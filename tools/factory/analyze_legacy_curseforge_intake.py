#!/usr/bin/env python3
"""Deterministically inventory an already-frozen legacy CurseForge intake.

This analyzer is intentionally an evidence-side tool.  It never imports or
executes a mod, launches Forge, decompiles bytecode, or recursively opens an
archive found inside a mod JAR.  Paths and source-expression evidence emitted
by this tool belong under the private analysis root and must not be forwarded
to production workers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import stat
import tempfile
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "legacy-curseforge-intake-analysis-v1"
MAX_METADATA_BYTES = 4 * 1024 * 1024
TEXT_EVIDENCE_BYTES = 2 * 1024 * 1024
ARCHIVE_SUFFIXES = {".jar", ".zip"}


class IntakeAnalysisError(ValueError):
    """Raised when an intake cannot be inspected without weakening safety."""


def _portable(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_json_bytes(value))
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path, *, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntakeAnalysisError(f"invalid {label}: {path}: {exc}") from exc


def _under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _validate_roots(
    release_lock: Path,
    server_root: Path,
    client_root: Path,
    analysis_root: Path,
    metadata_cache: Path | None,
) -> tuple[Path, Path, Path, Path, Path | None]:
    release_lock = release_lock.expanduser().resolve()
    server_root = server_root.expanduser().resolve()
    client_root = client_root.expanduser().resolve()
    analysis_root = analysis_root.expanduser().resolve()
    metadata_cache = metadata_cache.expanduser().resolve() if metadata_cache else None
    if not release_lock.is_file():
        raise IntakeAnalysisError(f"release lock is not a regular file: {release_lock}")
    for label, root in (("server oracle", server_root), ("client oracle", client_root)):
        if not root.is_dir():
            raise IntakeAnalysisError(f"{label} root is not a directory: {root}")
        if root.is_symlink():
            raise IntakeAnalysisError(f"{label} root may not be a symlink: {root}")
    if server_root == client_root or _under(server_root, client_root) or _under(client_root, server_root):
        raise IntakeAnalysisError("server and client oracle roots must be disjoint")
    if _under(analysis_root, server_root) or _under(analysis_root, client_root):
        raise IntakeAnalysisError("analysis root must be outside both immutable oracle roots")
    if metadata_cache is not None and not metadata_cache.is_file():
        raise IntakeAnalysisError(f"metadata cache is not a regular file: {metadata_cache}")
    return release_lock, server_root, client_root, analysis_root, metadata_cache


def _classify_path(path: str) -> list[str]:
    portable = _portable(path)
    name = PurePosixPath(path).name.casefold()
    suffix = PurePosixPath(path).suffix.casefold()
    categories: list[str] = []
    tests: tuple[tuple[str, bool], ...] = (
        ("FORGE_RUNTIME", name.startswith("forge-") or name in {"launchwrapper.jar", "minecraft_server.jar"}),
        ("MOD_JAR", suffix == ".jar" and "/mods/" in f"/{portable}"),
        ("LIBRARY", "/libraries/" in f"/{portable}"),
        ("COREMOD", "coremod" in portable),
        ("CONFIG", suffix in {".cfg", ".conf", ".properties", ".toml"} or "/config/" in f"/{portable}"),
        ("SCRIPT", suffix in {".zs", ".js", ".lua", ".groovy"} or "/scripts/" in f"/{portable}"),
        ("RECIPE", "recipe" in portable),
        ("PROGRESSION", any(token in portable for token in ("prestige", "advancement", "achievement", "quest"))),
        ("WORLD", any(token in portable for token in ("world", "dimension", "structure", "template"))),
        ("RESOURCE_PACK", "resourcepack" in portable or "resources.zip" in portable),
        ("ASSET", "/assets/" in f"/{portable}" or suffix in {".png", ".ogg", ".wav", ".obj"}),
        ("LICENSE", any(token in name for token in ("license", "licence", "copying", "notice", "credits"))),
        ("DOCUMENTATION", suffix in {".md", ".txt", ".pdf"}),
    )
    categories.extend(label for label, present in tests if present)
    return categories or ["OTHER"]


def _walk_oracle(root: Path, side: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    files: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    portable_seen: dict[str, str] = {}
    for path in sorted(
        root.rglob("*"),
        key=lambda item: (
            _portable(item.relative_to(root).as_posix()),
            item.relative_to(root).as_posix(),
        ),
    ):
        relative = path.relative_to(root).as_posix()
        try:
            mode = path.lstat().st_mode
        except OSError as exc:
            raise IntakeAnalysisError(f"cannot stat oracle path: {path}: {exc}") from exc
        if stat.S_ISLNK(mode):
            anomalies.append(
                {
                    "scope": side,
                    "kind": "LOOSE_SYMLINK_NOT_FOLLOWED",
                    "path": relative,
                }
            )
            continue
        if not stat.S_ISREG(mode):
            continue
        portable = _portable(relative)
        if portable in portable_seen and portable_seen[portable] != relative:
            anomalies.append(
                {
                    "scope": side,
                    "kind": "LOOSE_PORTABLE_PATH_COLLISION",
                    "paths": sorted([portable_seen[portable], relative]),
                }
            )
        else:
            portable_seen[portable] = relative
        try:
            byte_length = path.stat().st_size
            digest = _sha256(path)
        except OSError as exc:
            raise IntakeAnalysisError(f"cannot hash oracle file: {path}: {exc}") from exc
        files.append(
            {
                "side": side,
                "path": relative,
                "byte_length": byte_length,
                "sha256": digest,
                "categories": _classify_path(relative),
            }
        )
    files.sort(key=lambda row: (row["side"], _portable(row["path"]), row["path"]))
    anomalies.sort(key=lambda row: json.dumps(row, sort_keys=True))
    return files, anomalies


def _parse_manifest(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    current: str | None = None
    for raw_line in text.replace("\r\n", "\n").split("\n"):
        if raw_line.startswith(" ") and current is not None:
            result[current] += raw_line[1:]
            continue
        if ":" not in raw_line:
            current = None
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        if not key:
            continue
        result[key] = value.lstrip()
        current = key
    return dict(sorted(result.items(), key=lambda item: _portable(item[0])))


def _mcmod_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, Mapping)]
    if not isinstance(value, Mapping):
        return []
    if isinstance(value.get("modList"), list):
        return [dict(item) for item in value["modList"] if isinstance(item, Mapping)]
    return [dict(value)] if any(key in value for key in ("modid", "modId", "name")) else []


def _read_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> bytes:
    if info.file_size > MAX_METADATA_BYTES:
        raise IntakeAnalysisError(
            f"metadata member exceeds {MAX_METADATA_BYTES} bytes: {info.filename}"
        )
    with archive.open(info, "r") as stream:
        value = stream.read(MAX_METADATA_BYTES + 1)
    if len(value) > MAX_METADATA_BYTES:
        raise IntakeAnalysisError(f"metadata member expanded beyond limit: {info.filename}")
    return value


def _metadata_members(
    infos: list[zipfile.ZipInfo], suffix: str
) -> list[zipfile.ZipInfo]:
    portable_name = _portable(suffix)
    return [
        info
        for info in infos
        if not info.is_dir()
        and _portable(PurePosixPath(info.filename).name) == portable_name
    ]


def _archive_anomalies(
    infos: list[zipfile.ZipInfo], *, side: str, jar_path: str
) -> list[dict[str, Any]]:
    exact = Counter(info.filename for info in infos)
    portable: dict[str, set[str]] = defaultdict(set)
    for info in infos:
        portable[_portable(info.filename)].add(info.filename)
    rows: list[dict[str, Any]] = []
    for name, count in sorted(exact.items(), key=lambda item: _portable(item[0])):
        if count > 1:
            rows.append(
                {
                    "scope": side,
                    "jar_path": jar_path,
                    "kind": "NESTED_EXACT_DUPLICATE_MEMBER",
                    "member": name,
                    "count": count,
                }
            )
    for names in portable.values():
        if len(names) > 1:
            rows.append(
                {
                    "scope": side,
                    "jar_path": jar_path,
                    "kind": "NESTED_PORTABLE_MEMBER_COLLISION",
                    "members": sorted(names),
                }
            )
    return sorted(rows, key=lambda row: json.dumps(row, sort_keys=True))


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


DEPENDENCY_TOKEN = re.compile(
    r"(?:(?P<relation>required-after|required-before|after|before):)?"
    r"(?P<modid>[A-Za-z0-9_.-]+)(?:@[^,;\s]+)?",
    re.IGNORECASE,
)


def _declared_dependencies(row: Mapping[str, Any], manifest: Mapping[str, str]) -> list[dict[str, Any]]:
    sources: list[tuple[str, str]] = []
    for key in ("dependencies", "requiredMods", "dependants"):
        for value in _coerce_list(row.get(key)):
            sources.append((f"mcmod.info:{key}", value))
    for key in ("FMLAT", "FMLCorePluginContainsFMLMod", "ModDependencies"):
        if key in manifest:
            sources.append((f"MANIFEST.MF:{key}", manifest[key]))
    dependencies: list[dict[str, Any]] = []
    seen: set[tuple[str, str, bool, str]] = set()
    for source, declaration in sources:
        for match in DEPENDENCY_TOKEN.finditer(declaration):
            modid = match.group("modid")
            if modid.casefold() in {"minecraft", "forge"}:
                continue
            relation = (match.group("relation") or "unspecified").lower()
            required = relation.startswith("required-")
            key = (modid.casefold(), relation, required, source)
            if key in seen:
                continue
            seen.add(key)
            dependencies.append(
                {
                    "mod_id": modid,
                    "relation": relation,
                    "required": required,
                    "evidence_field": source,
                    "raw_declaration": declaration,
                }
            )
    return sorted(dependencies, key=lambda row: (_portable(row["mod_id"]), row["relation"], row["evidence_field"]))


def _distribution(row: Mapping[str, Any]) -> tuple[str, str, list[str]]:
    client_only = row.get("clientSideOnly") is True
    server_only = row.get("serverSideOnly") is True
    if client_only and server_only:
        return "CONFLICTING_DECLARATION", "HIGH", ["mcmod.info declares both clientSideOnly and serverSideOnly"]
    if client_only:
        return "CLIENT_ONLY", "HIGH", ["mcmod.info clientSideOnly=true"]
    if server_only:
        return "SERVER_ONLY", "HIGH", ["mcmod.info serverSideOnly=true"]
    return "SERVER_PRESENT_CLIENT_UNRESOLVED", "LOW", ["server JAR presence does not prove client distribution"]


def _asset_family(member: str) -> str | None:
    portable = _portable(member)
    if "/textures/block" in portable or "/textures/blocks" in portable:
        return "BLOCK_TEXTURES"
    if "/textures/item" in portable or "/textures/items" in portable:
        return "ITEM_TEXTURES"
    if "/textures/gui" in portable:
        return "INTERFACE_TEXTURES"
    if "/textures/entity" in portable:
        return "CREATURE_TEXTURES"
    if "/models/" in portable:
        return "MODELS"
    if "/blockstates/" in portable:
        return "BLOCKSTATES"
    if portable.endswith("sounds.json") or portable.endswith(".ogg") or portable.endswith(".wav"):
        return "SOUNDS"
    if "/lang/" in portable:
        return "LOCALIZATION"
    if "/assets/" in f"/{portable}":
        return "OTHER_ASSETS"
    return None


def _inspect_server_jars(
    server_root: Path, file_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    mods: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    member_evidence: list[dict[str, Any]] = []
    jar_rows = [row for row in file_rows if "MOD_JAR" in row["categories"] and row["side"] == "server"]
    for file_row in jar_rows:
        jar_path = str(file_row["path"])
        absolute = server_root / PurePosixPath(jar_path)
        base: dict[str, Any] = {
            "server_jar_path": jar_path,
            "filename": PurePosixPath(jar_path).name,
            "byte_length": file_row["byte_length"],
            "sha256": file_row["sha256"],
            "archive_status": "OK",
            "metadata_status": "UNKNOWN_NO_UNIQUE_MCMOD_INFO",
            "manifest_status": "UNKNOWN_NO_UNIQUE_MANIFEST",
            "archive_opened": True,
            "nested_archives_opened": False,
        }
        try:
            with zipfile.ZipFile(absolute, "r") as archive:
                infos = archive.infolist()
                anomalies.extend(_archive_anomalies(infos, side="server", jar_path=jar_path))
                nested_archives = sorted(
                    info.filename
                    for info in infos
                    if not info.is_dir()
                    and PurePosixPath(info.filename).suffix.casefold() in ARCHIVE_SUFFIXES
                )
                base["archive_member_count"] = len(infos)
                base["nested_archive_members_not_opened"] = nested_archives
                mcmod_infos = _metadata_members(infos, "mcmod.info")
                manifest_infos = [
                    info
                    for info in infos
                    if not info.is_dir() and _portable(info.filename) == "meta-inf/manifest.mf"
                ]
                mcmod_rows: list[dict[str, Any]] = []
                manifest: dict[str, str] = {}
                if len(mcmod_infos) == 1:
                    try:
                        mcmod_value = json.loads(_read_member(archive, mcmod_infos[0]).decode("utf-8-sig"))
                        mcmod_rows = _mcmod_rows(mcmod_value)
                        base["metadata_status"] = "PARSED" if mcmod_rows else "PARSED_NO_MOD_ROWS"
                        base["mcmod_info_member"] = mcmod_infos[0].filename
                    except (UnicodeDecodeError, json.JSONDecodeError, IntakeAnalysisError) as exc:
                        base["metadata_status"] = "UNPARSEABLE"
                        base["mcmod_info_error"] = str(exc)
                elif len(mcmod_infos) > 1:
                    base["metadata_status"] = "AMBIGUOUS_MULTIPLE_MCMOD_INFO"
                    base["mcmod_info_members"] = sorted(info.filename for info in mcmod_infos)
                if len(manifest_infos) == 1:
                    try:
                        manifest = _parse_manifest(_read_member(archive, manifest_infos[0]).decode("utf-8", errors="replace"))
                        base["manifest_status"] = "PARSED"
                    except IntakeAnalysisError as exc:
                        base["manifest_status"] = "UNPARSEABLE"
                        base["manifest_error"] = str(exc)
                elif len(manifest_infos) > 1:
                    base["manifest_status"] = "AMBIGUOUS_MULTIPLE_MANIFEST"
                family_counts: Counter[str] = Counter()
                family_examples: dict[str, list[str]] = defaultdict(list)
                for info in infos:
                    if info.is_dir():
                        continue
                    family = _asset_family(info.filename)
                    if family:
                        family_counts[family] += 1
                        if len(family_examples[family]) < 5:
                            family_examples[family].append(info.filename)
                    categories = _classify_path(info.filename)
                    relevant = sorted(set(categories) & {"CONFIG", "SCRIPT", "RECIPE", "PROGRESSION", "WORLD", "LICENSE"})
                    if relevant:
                        member_evidence.append(
                            {
                                "server_jar_path": jar_path,
                                "member": info.filename,
                                "categories": relevant,
                            }
                        )
                for family in sorted(family_counts):
                    assets.append(
                        {
                            "source_side": "server",
                            "server_jar_path": jar_path,
                            "family": family,
                            "member_count": family_counts[family],
                            "evidence_members": sorted(family_examples[family]),
                            "production_copying_allowed": False,
                        }
                    )
                contribution_kinds: list[dict[str, Any]] = []
                relevant_members = [
                    row for row in member_evidence if row["server_jar_path"] == jar_path
                ]
                behavior_categories = sorted(
                    {
                        category
                        for row in relevant_members
                        for category in row["categories"]
                        if category in {"SCRIPT", "RECIPE", "PROGRESSION", "WORLD"}
                    }
                )
                if behavior_categories:
                    contribution_kinds.append(
                        {
                            "kind": "BEHAVIOR_OR_DATA_DECLARATIONS",
                            "evidence_categories": behavior_categories,
                        }
                    )
                if family_counts:
                    contribution_kinds.append(
                        {
                            "kind": "ASSETS_OR_PRESENTATION",
                            "evidence_families": sorted(family_counts),
                        }
                    )
                if any(_declared_dependencies(row, manifest) for row in mcmod_rows):
                    contribution_kinds.append(
                        {
                            "kind": "DECLARED_INTEGRATION",
                            "evidence": "declared dependency metadata",
                        }
                    )
                if not contribution_kinds:
                    contribution_kinds.append(
                        {
                            "kind": "UNKNOWN",
                            "evidence": "metadata and archive member names do not establish a functional contribution",
                        }
                    )
                base["evidence_grounded_contributions"] = contribution_kinds
                if not mcmod_rows:
                    mods.append(
                        {
                            **base,
                            "mod_id": None,
                            "display_name": None,
                            "version": manifest.get("Implementation-Version"),
                            "declared_dependencies": [],
                            "distribution": "UNKNOWN",
                            "distribution_confidence": "NONE",
                            "distribution_evidence": [base["metadata_status"]],
                            "license": None,
                            "gameplay_domain": "UNKNOWN_REQUIRES_ORACLE",
                            "progression_essentiality": "UNKNOWN_REQUIRES_ORACLE",
                            "bedrock_reconstruction_difficulty": "UNKNOWN_REQUIRES_ANALYSIS",
                            "shared_runtime_requirements": ["UNKNOWN_REQUIRES_ANALYSIS"],
                        }
                    )
                else:
                    for index, row in enumerate(mcmod_rows):
                        distribution, confidence, evidence = _distribution(row)
                        mod_id = row.get("modid", row.get("modId"))
                        mods.append(
                            {
                                **base,
                                "metadata_row_index": index,
                                "mod_id": str(mod_id) if mod_id is not None else None,
                                "display_name": row.get("name"),
                                "version": row.get("version") or manifest.get("Implementation-Version"),
                                "description_present": bool(row.get("description")),
                                "declared_dependencies": _declared_dependencies(row, manifest),
                                "distribution": distribution,
                                "distribution_confidence": confidence,
                                "distribution_evidence": evidence,
                                "license": row.get("license") or manifest.get("Bundle-License"),
                                "gameplay_domain": "UNKNOWN_REQUIRES_ORACLE",
                                "progression_essentiality": "UNKNOWN_REQUIRES_ORACLE",
                                "bedrock_reconstruction_difficulty": "UNKNOWN_REQUIRES_ANALYSIS",
                                "shared_runtime_requirements": ["UNKNOWN_REQUIRES_ANALYSIS"],
                            }
                        )
        except (OSError, zipfile.BadZipFile) as exc:
            base["archive_status"] = "INVALID_OR_UNREADABLE_ZIP"
            base["archive_error"] = str(exc)
            mods.append(
                {
                    **base,
                    "mod_id": None,
                    "display_name": None,
                    "version": None,
                    "declared_dependencies": [],
                    "distribution": "UNKNOWN",
                    "distribution_confidence": "NONE",
                    "distribution_evidence": ["JAR could not be inspected"],
                    "license": None,
                    "gameplay_domain": "UNKNOWN_REQUIRES_ORACLE",
                    "progression_essentiality": "UNKNOWN_REQUIRES_ORACLE",
                    "bedrock_reconstruction_difficulty": "UNKNOWN_REQUIRES_ANALYSIS",
                    "shared_runtime_requirements": ["UNKNOWN_REQUIRES_ANALYSIS"],
                }
            )
    mods.sort(
        key=lambda row: (
            _portable(row["server_jar_path"]),
            row["server_jar_path"],
            _portable(str(row.get("mod_id") or "")),
            str(row.get("mod_id") or ""),
            row.get("metadata_row_index", -1),
        )
    )
    assets.sort(
        key=lambda row: (
            _portable(row["server_jar_path"]),
            row["server_jar_path"],
            row["family"],
        )
    )
    member_evidence.sort(
        key=lambda row: (
            _portable(row["server_jar_path"]),
            row["server_jar_path"],
            _portable(row["member"]),
            row["member"],
        )
    )
    return mods, anomalies, assets, member_evidence


def _find_client_manifest(client_root: Path) -> tuple[str | None, dict[str, Any] | None]:
    matches = sorted(
        [
            path
            for path in client_root.rglob("*")
            if path.is_file()
            and not path.is_symlink()
            and path.name.casefold() == "manifest.json"
        ],
        key=lambda path: (
            _portable(path.relative_to(client_root).as_posix()),
            path.relative_to(client_root).as_posix(),
        ),
    )
    if len(matches) != 1:
        return None, None
    path = matches[0]
    value = _load_json(path, label="client CurseForge manifest")
    if not isinstance(value, dict):
        raise IntakeAnalysisError("client manifest.json must contain a JSON object")
    return path.relative_to(client_root).as_posix(), value


def _cache_records(cache: Any) -> list[dict[str, Any]]:
    if cache is None:
        return []
    if isinstance(cache, list):
        return [dict(row) for row in cache if isinstance(row, Mapping)]
    if isinstance(cache, Mapping):
        for key in ("files", "rows", "records", "data"):
            if isinstance(cache.get(key), list):
                return [dict(row) for row in cache[key] if isinstance(row, Mapping)]
        result: list[dict[str, Any]] = []
        for key, value in cache.items():
            if isinstance(value, Mapping):
                row = dict(value)
                row.setdefault("cache_key", key)
                result.append(row)
        return result
    return []


def _integer_field(row: Mapping[str, Any], *names: str) -> int | None:
    for name in names:
        value = row.get(name)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def _manifest_rows(
    manifest: dict[str, Any] | None, cache: Any
) -> tuple[list[dict[str, Any]], dict[tuple[int, int], dict[str, Any]]]:
    rows = [] if manifest is None else manifest.get("files", [])
    if not isinstance(rows, list):
        raise IntakeAnalysisError("client manifest files field must be a list")
    cache_index: dict[tuple[int, int], dict[str, Any]] = {}
    for row in _cache_records(cache):
        project_id = _integer_field(row, "projectID", "projectId", "project_id")
        file_id = _integer_field(row, "fileID", "fileId", "file_id", "id")
        if project_id is not None and file_id is not None:
            cache_index[(project_id, file_id)] = row
    preserved: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            preserved.append({"row_index": index, "manifest_row": raw, "metadata_resolution": "INVALID_NON_OBJECT_ROW"})
            continue
        row = dict(raw)
        project_id = _integer_field(row, "projectID", "projectId", "project_id")
        file_id = _integer_field(row, "fileID", "fileId", "file_id")
        metadata = cache_index.get((project_id, file_id)) if project_id is not None and file_id is not None else None
        preserved.append(
            {
                "row_index": index,
                "manifest_row": row,
                "metadata_resolution": "RESOLVED_OFFICIAL_CACHE" if metadata is not None else "UNRESOLVED_NO_OFFICIAL_CACHE_ROW",
                "official_metadata": metadata,
                "distribution": "CLIENT_MANIFEST_PRESENT_SERVER_UNRESOLVED",
                "distribution_confidence": "LOW",
                "distribution_evidence": [
                    "client manifest membership does not by itself prove a client-only mod"
                ],
            }
        )
    return preserved, cache_index


def _match_client_distribution(
    mods: list[dict[str, Any]], manifest_rows: list[dict[str, Any]]
) -> None:
    resolved_names: dict[str, list[int]] = defaultdict(list)
    for row in manifest_rows:
        metadata = row.get("official_metadata")
        if not isinstance(metadata, Mapping):
            continue
        candidates = [
            metadata.get("fileName"),
            metadata.get("filename"),
            metadata.get("downloadUrl", "").rsplit("/", 1)[-1] if isinstance(metadata.get("downloadUrl"), str) else None,
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate:
                resolved_names[_portable(candidate)].append(int(row["row_index"]))
    for mod in mods:
        matches = resolved_names.get(_portable(str(mod["filename"])), [])
        if not matches:
            continue
        mod["client_manifest_row_indices"] = sorted(set(matches))
        for index in sorted(set(matches)):
            manifest_rows[index]["distribution"] = "SHARED"
            manifest_rows[index]["distribution_confidence"] = "HIGH"
            manifest_rows[index]["distribution_evidence"] = [
                "exact official-cache filename matched a server mod JAR"
            ]
        if mod["distribution"] == "SERVER_PRESENT_CLIENT_UNRESOLVED":
            mod["distribution"] = "SHARED"
            mod["distribution_confidence"] = "HIGH"
            mod["distribution_evidence"] = ["exact server JAR filename matched official client file metadata"]


def _dependency_graph(mods: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    for mod in mods:
        node_id = mod.get("mod_id") or f"unknown:{mod['sha256'][:16]}"
        nodes.setdefault(
            str(node_id),
            {
                "mod_id": mod.get("mod_id"),
                "node_id": str(node_id),
                "display_name": mod.get("display_name"),
                "evidence_jar": mod["server_jar_path"],
                "metadata_status": mod["metadata_status"],
            },
        )
        for dependency in mod["declared_dependencies"]:
            edges.append(
                {
                    "from": str(node_id),
                    "to": dependency["mod_id"],
                    "relation": dependency["relation"],
                    "required": dependency["required"],
                    "evidence_jar": mod["server_jar_path"],
                    "evidence_field": dependency["evidence_field"],
                    "raw_declaration": dependency["raw_declaration"],
                }
            )
    edges.sort(key=lambda row: (_portable(row["from"]), _portable(row["to"]), row["relation"], row["evidence_field"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "graph_kind": "DECLARED_MOD_DEPENDENCIES",
        "nodes": [nodes[key] for key in sorted(nodes, key=_portable)],
        "edges": edges,
        "limitations": [
            "Only dependencies declared in uniquely parsed metadata are edges.",
            "Runtime, reflection, script, and undocumented integration dependencies remain UNKNOWN.",
        ],
    }


def _evidence_graph(
    *, kind: str, file_rows: list[dict[str, Any]], member_rows: list[dict[str, Any]], categories: set[str]
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    for row in file_rows:
        matched = sorted(categories.intersection(row["categories"]))
        if matched:
            nodes.append(
                {
                    "node_id": f"{row['side']}:{row['path']}",
                    "source_kind": "LOOSE_FILE",
                    "side": row["side"],
                    "path": row["path"],
                    "evidence_categories": matched,
                    "semantic_status": "UNKNOWN_REQUIRES_ORACLE_ANALYSIS",
                }
            )
    for row in member_rows:
        matched = sorted(categories.intersection(row["categories"]))
        if matched:
            nodes.append(
                {
                    "node_id": f"server:{row['server_jar_path']}!/{row['member']}",
                    "source_kind": "JAR_MEMBER_NAME_ONLY",
                    "side": "server",
                    "jar_path": row["server_jar_path"],
                    "member": row["member"],
                    "evidence_categories": matched,
                    "semantic_status": "UNKNOWN_REQUIRES_ORACLE_ANALYSIS",
                }
            )
    nodes.sort(key=lambda row: _portable(row["node_id"]))
    category_nodes = sorted(
        {
            category
            for row in nodes
            for category in row["evidence_categories"]
        }
    )
    edges = [
        {
            "from": row["node_id"],
            "to": f"evidence-category:{category}",
            "relation": "PATH_CLASSIFIED_AS",
            "evidence": "deterministic path classification",
        }
        for row in nodes
        for category in row["evidence_categories"]
    ]
    edges.sort(key=lambda row: (_portable(row["from"]), row["to"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "graph_kind": kind,
        "nodes": nodes
        + [
            {
                "node_id": f"evidence-category:{category}",
                "source_kind": "COARSE_EVIDENCE_CATEGORY",
                "semantic_status": "CATEGORY_ONLY_NOT_GAMEPLAY_SEMANTICS",
            }
            for category in category_nodes
        ],
        "edges": edges,
        "reachability_status": "UNKNOWN_NOT_INFERRED_FROM_FILENAMES",
        "limitations": [
            "File and archive-member names establish evidence locations, not gameplay meaning.",
            "No progression or recipe edge is invented without a separately parsed semantic source.",
        ],
    }


def _rights_ledger(
    mods: list[dict[str, Any]], file_rows: list[dict[str, Any]], member_rows: list[dict[str, Any]], release_lock: Any
) -> dict[str, Any]:
    records = []
    for mod in mods:
        license_value = mod.get("license")
        records.append(
            {
                "subject_type": "MOD_METADATA_ROW",
                "subject_id": mod.get("mod_id") or f"unknown:{mod['sha256'][:16]}",
                "evidence_jar": mod["server_jar_path"],
                "license_metadata": license_value,
                "license_identification": "DECLARED_UNREVIEWED" if license_value else "UNKNOWN",
                "code_redistribution": "UNKNOWN_REQUIRES_RIGHTS_REVIEW",
                "modification_permission": "UNKNOWN_REQUIRES_RIGHTS_REVIEW",
                "asset_rights": "UNKNOWN_SEPARATE_REVIEW_REQUIRED",
                "branding_rights": "UNKNOWN_SEPARATE_REVIEW_REQUIRED",
                "production_copying_allowed": False,
                "private_oracle_only": True,
            }
        )
    pack_sources = [
        {"side": row["side"], "path": row["path"]}
        for row in file_rows
        if "LICENSE" in row["categories"]
    ] + [
        {"side": "server", "jar_path": row["server_jar_path"], "member": row["member"]}
        for row in member_rows
        if "LICENSE" in row["categories"]
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "default_policy": {
            "status": "PRIVATE_ORACLE_ONLY_UNTIL_REVIEWED",
            "production_copying_allowed": False,
            "functional_observation_allowed": True,
            "code_assets_configuration_branding_copying_allowed": False,
        },
        "release_lock_rights_fields": {
            key: value
            for key, value in release_lock.items()
            if isinstance(release_lock, Mapping) and any(token in key.casefold() for token in ("license", "rights", "author", "owner"))
        },
        "license_evidence_locations": sorted(pack_sources, key=lambda row: json.dumps(row, sort_keys=True)),
        "records": sorted(records, key=lambda row: (_portable(row["subject_id"]), _portable(row["evidence_jar"]))),
        "warning": "A declared software license is not evidence that art, sound, trademarks, branding, or pack-owned configuration share that license.",
    }


def _write_sqlite(
    path: Path,
    file_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    mods: list[dict[str, Any]],
    anomalies: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        temporary.unlink()
    connection = sqlite3.connect(temporary)
    try:
        connection.executescript(
            """
            PRAGMA journal_mode=DELETE;
            PRAGMA synchronous=FULL;
            CREATE TABLE files (
                side TEXT NOT NULL, path TEXT NOT NULL, byte_length INTEGER NOT NULL,
                sha256 TEXT NOT NULL, categories_json TEXT NOT NULL,
                PRIMARY KEY (side, path)
            ) WITHOUT ROWID;
            CREATE TABLE client_manifest_rows (
                row_index INTEGER PRIMARY KEY, manifest_row_json TEXT NOT NULL,
                metadata_resolution TEXT NOT NULL, official_metadata_json TEXT
            );
            CREATE TABLE mods (
                row_index INTEGER PRIMARY KEY, server_jar_path TEXT NOT NULL,
                mod_id TEXT, display_name TEXT, version TEXT, distribution TEXT NOT NULL,
                metadata_status TEXT NOT NULL, record_json TEXT NOT NULL
            );
            CREATE TABLE anomalies (
                row_index INTEGER PRIMARY KEY, kind TEXT NOT NULL, record_json TEXT NOT NULL
            );
            """
        )
        connection.executemany(
            "INSERT INTO files VALUES (?, ?, ?, ?, ?)",
            [
                (
                    row["side"], row["path"], row["byte_length"], row["sha256"],
                    json.dumps(row["categories"], sort_keys=True, separators=(",", ":")),
                )
                for row in file_rows
            ],
        )
        connection.executemany(
            "INSERT INTO client_manifest_rows VALUES (?, ?, ?, ?)",
            [
                (
                    row["row_index"],
                    json.dumps(row["manifest_row"], sort_keys=True, separators=(",", ":")),
                    row["metadata_resolution"],
                    None if row.get("official_metadata") is None else json.dumps(row["official_metadata"], sort_keys=True, separators=(",", ":")),
                )
                for row in manifest_rows
            ],
        )
        connection.executemany(
            "INSERT INTO mods VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    index, row["server_jar_path"], row.get("mod_id"), row.get("display_name"),
                    row.get("version"), row["distribution"], row["metadata_status"],
                    json.dumps(row, sort_keys=True, separators=(",", ":")),
                )
                for index, row in enumerate(mods)
            ],
        )
        connection.executemany(
            "INSERT INTO anomalies VALUES (?, ?, ?)",
            [
                (index, row["kind"], json.dumps(row, sort_keys=True, separators=(",", ":")))
                for index, row in enumerate(anomalies)
            ],
        )
        connection.commit()
    finally:
        connection.close()
    os.replace(temporary, path)


def analyze_intake(
    release_lock: Path,
    server_oracle_root: Path,
    client_oracle_root: Path,
    analysis_root: Path,
    official_metadata_cache: Path | None = None,
) -> dict[str, Any]:
    """Inspect frozen roots and write deterministic evidence-side deliverables."""

    release_lock, server_root, client_root, analysis_root, metadata_cache = _validate_roots(
        release_lock, server_oracle_root, client_oracle_root, analysis_root, official_metadata_cache
    )
    lock_value = _load_json(release_lock, label="release lock")
    if not isinstance(lock_value, Mapping):
        raise IntakeAnalysisError("release lock must contain a JSON object")
    cache_value = _load_json(metadata_cache, label="official metadata cache") if metadata_cache else None
    server_files, server_anomalies = _walk_oracle(server_root, "server")
    client_files, client_anomalies = _walk_oracle(client_root, "client")
    file_rows = sorted(server_files + client_files, key=lambda row: (row["side"], _portable(row["path"]), row["path"]))
    mods, archive_anomalies, assets, member_evidence = _inspect_server_jars(server_root, file_rows)
    manifest_path, manifest = _find_client_manifest(client_root)
    manifest_rows, _ = _manifest_rows(manifest, cache_value)
    _match_client_distribution(mods, manifest_rows)
    anomalies = sorted(server_anomalies + client_anomalies + archive_anomalies, key=lambda row: json.dumps(row, sort_keys=True))

    full_inventory = {
        "schema_version": SCHEMA_VERSION,
        "inventory_scope": "PRIVATE_EVIDENCE_ONLY",
        "server_oracle_root": str(server_root),
        "client_oracle_root": str(client_root),
        "file_count": len(file_rows),
        "total_byte_length": sum(row["byte_length"] for row in file_rows),
        "files": file_rows,
        "anomalies": anomalies,
    }
    mod_inventory = {
        "schema_version": SCHEMA_VERSION,
        "server_mod_jar_count": len({row["server_jar_path"] for row in mods}),
        "metadata_mod_row_count": len(mods),
        "client_manifest": {
            "path": manifest_path,
            "status": "PARSED" if manifest is not None else "UNKNOWN_NOT_EXACTLY_ONE_MANIFEST",
            "package_metadata": None if manifest is None else {key: value for key, value in manifest.items() if key != "files"},
            "rows": manifest_rows,
        },
        "mods": mods,
        "relevant_jar_member_evidence": member_evidence,
        "classification_policy": "Distribution claims require explicit metadata or an exact official-cache filename match; unmatched presence is unresolved.",
    }
    dependency_graph = _dependency_graph(mods)
    progression_graph = _evidence_graph(
        kind="COARSE_PROGRESSION_EVIDENCE",
        file_rows=file_rows,
        member_rows=member_evidence,
        categories={"PROGRESSION", "SCRIPT", "WORLD"},
    )
    recipe_graph = _evidence_graph(
        kind="COARSE_RECIPE_REACHABILITY_EVIDENCE",
        file_rows=file_rows,
        member_rows=member_evidence,
        categories={"RECIPE", "SCRIPT"},
    )
    asset_inventory = {
        "schema_version": SCHEMA_VERSION,
        "families": assets,
        "policy": "Counts and evidence member names are private analysis facts; source asset bytes are not copied.",
    }
    rights = _rights_ledger(mods, file_rows, member_evidence, lock_value)
    category_counts = Counter(category for row in file_rows for category in row["categories"])
    member_category_counts = Counter(category for row in member_evidence for category in row["categories"])
    summary = {
        "schema_version": SCHEMA_VERSION,
        "release_lock_path": str(release_lock),
        "release_lock_sha256": _sha256(release_lock),
        "official_metadata_cache": None if metadata_cache is None else {"path": str(metadata_cache), "sha256": _sha256(metadata_cache)},
        "server_oracle_root": str(server_root),
        "client_oracle_root": str(client_root),
        "analysis_root": str(analysis_root),
        "file_count": len(file_rows),
        "server_mod_jar_count": mod_inventory["server_mod_jar_count"],
        "metadata_mod_row_count": len(mods),
        "client_manifest_row_count": len(manifest_rows),
        "loose_category_counts": dict(sorted(category_counts.items())),
        "jar_member_evidence_category_counts": dict(sorted(member_category_counts.items())),
        "anomaly_count": len(anomalies),
        "unknown_mod_metadata_count": sum(row["metadata_status"] != "PARSED" for row in mods),
        "unknown_distribution_count": sum("UNKNOWN" in row["distribution"] or "UNRESOLVED" in row["distribution"] for row in mods),
        "source_content_executed": False,
        "bytecode_decompiled": False,
        "nested_archives_opened": False,
        "production_packets_generated": False,
        "analysis_status": "COMPLETE_WITH_UNKNOWNS",
        "deliverables": [
            "FULL_FILE_INVENTORY.json",
            "FULL_FILE_INVENTORY.sqlite3",
            "MOD_INVENTORY.json",
            "MOD_DEPENDENCY_GRAPH.json",
            "PROGRESSION_GRAPH.json",
            "RECIPE_REACHABILITY_GRAPH.json",
            "ASSET_FAMILY_INVENTORY.json",
            "RIGHTS_LEDGER.json",
            "EVIDENCE_ANALYSIS_SUMMARY.json",
        ],
    }

    analysis_root.mkdir(parents=True, exist_ok=True)
    outputs = {
        "FULL_FILE_INVENTORY.json": full_inventory,
        "MOD_INVENTORY.json": mod_inventory,
        "MOD_DEPENDENCY_GRAPH.json": dependency_graph,
        "PROGRESSION_GRAPH.json": progression_graph,
        "RECIPE_REACHABILITY_GRAPH.json": recipe_graph,
        "ASSET_FAMILY_INVENTORY.json": asset_inventory,
        "RIGHTS_LEDGER.json": rights,
        "EVIDENCE_ANALYSIS_SUMMARY.json": summary,
    }
    for name, value in outputs.items():
        _atomic_json(analysis_root / name, value)
    _write_sqlite(analysis_root / "FULL_FILE_INVENTORY.sqlite3", file_rows, manifest_rows, mods, anomalies)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-lock", type=Path, required=True)
    parser.add_argument("--server-oracle-root", type=Path, required=True)
    parser.add_argument("--client-oracle-root", type=Path, required=True)
    parser.add_argument("--official-metadata-cache", type=Path)
    parser.add_argument("--analysis-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        summary = analyze_intake(
            args.release_lock,
            args.server_oracle_root,
            args.client_oracle_root,
            args.analysis_root,
            args.official_metadata_cache,
        )
    except (IntakeAnalysisError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, **summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
