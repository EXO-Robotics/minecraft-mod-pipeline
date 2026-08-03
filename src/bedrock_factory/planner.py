"""Deterministic, non-executing intake and task separation for modpacks.

This module deliberately stops at planning.  It reads an explicitly authorized
local source, hashes the exact bytes, inspects a small allow-list of archive
metadata files, and returns a machine-readable factory plan.  It never imports
or executes archive content, uses the network, or creates production lanes.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import stat
import tomllib
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


PLAN_SCHEMA_VERSION = "1.0.0"
PLAN_RECORD_TYPE = "JAVA_TO_BEDROCK_FACTORY_PLAN"
ARCHIVE_SUFFIXES = {".jar", ".zip"}
MAX_METADATA_BYTES = 1_048_576
MAX_NESTED_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 250_000
OPAQUE_ID_PREFIX_BYTES = 32

AUTHORIZATION_IDS = (
    "SOURCE_METADATA_INSPECTION_AUTHORIZED",
    "STATIC_ANALYSIS_AUTHORIZED",
    "ABSTRACT_BEHAVIOR_EXTRACTION_AUTHORIZED",
    "PRIVATE_REIMPLEMENTATION_AUTHORIZED",
    "SOURCE_ASSET_REUSE_AUTHORIZED",
    "BRANDING_REUSE_AUTHORIZED",
    "COMMERCIAL_DISTRIBUTION_AUTHORIZED",
    "MARKETPLACE_SUBMISSION_AUTHORIZED",
    "PRODUCTION_AUTHORIZED",
    "PUBLICATION_AUTHORIZED",
    "RELEASE_AUTHORIZED",
)

AUTHORIZATION_STATUSES = {
    "AUTHORIZED",
    "EXPLICITLY_PERMITTED",
    "PERMITTED_BY_APPLICABLE_LICENSE",
    "PERMITTED_FOR_PRIVATE_TECHNICAL_EVALUATION",
    "NOT_NEEDED_FOR_PILOT",
    "PENDING",
    "PROHIBITED",
    "UNRESOLVED",
    "CONFLICTING_TERMS",
    "LEGAL_REVIEW_REQUIRED",
}

INSPECTION_PERMITTED_STATUSES = {
    "AUTHORIZED",
    "EXPLICITLY_PERMITTED",
    "PERMITTED_BY_APPLICABLE_LICENSE",
    "PERMITTED_FOR_PRIVATE_TECHNICAL_EVALUATION",
}

_SAFE_OUTPUT_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$")


class FactoryPlanningError(ValueError):
    """Raised when intake cannot be completed without ambiguity or mutation."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_regular_file(path: Path, *, retain_bytes: bool) -> tuple[str, int, bytes | None]:
    """Read a stable regular file without following a last-component symlink."""

    digest = hashlib.sha256()
    chunks: list[bytes] | None = [] if retain_bytes else None
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise FactoryPlanningError(f"cannot safely open regular file: {path}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise FactoryPlanningError(f"source entry is not a regular file: {path}")
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            if chunks is not None:
                chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after:
        raise FactoryPlanningError(f"source changed during intake: {path}")
    return digest.hexdigest(), before.st_size, b"".join(chunks) if chunks is not None else None


def _sha256_path(path: Path) -> tuple[str, int]:
    sha256, size, _ = _read_regular_file(path, retain_bytes=False)
    return sha256, size


def _frame(digest: "hashlib._Hash", kind: str, name: str, size: int, sha256: str) -> None:
    """Add an unambiguous tree entry to a digest."""

    fields = (kind.encode("ascii"), name.encode("utf-8"), str(size).encode("ascii"), sha256.encode("ascii"))
    for field in fields:
        digest.update(len(field).to_bytes(8, "big"))
        digest.update(field)


def _lexical_absolute(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    return Path(os.path.abspath(os.fspath(candidate)))


def _assert_no_symlink_components(path: Path, *, allow_missing_tail: bool) -> None:
    current = Path(path.anchor)
    parts = path.parts[1:] if path.is_absolute() else path.parts
    missing = False
    for part in parts:
        current /= part
        if missing:
            continue
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            if allow_missing_tail:
                missing = True
                continue
            raise FactoryPlanningError(f"path does not exist: {path}") from None
        if stat.S_ISLNK(mode):
            raise FactoryPlanningError(f"symlink path components are forbidden: {current}")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate_source_path(source_path: str | Path) -> Path:
    """Return an absolute local source path after fail-closed path validation."""

    source = _lexical_absolute(source_path)
    _assert_no_symlink_components(source, allow_missing_tail=False)
    mode = source.lstat().st_mode
    if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
        raise FactoryPlanningError("source must be a regular local file or directory")
    if stat.S_ISREG(mode) and source.suffix.lower() not in ARCHIVE_SUFFIXES:
        raise FactoryPlanningError("a file source must be a .jar or .zip archive")
    return source


def validate_output_root(source: Path, output_root: str | Path) -> Path:
    """Validate a non-overlapping, non-symlink caller-owned output boundary."""

    output = _lexical_absolute(output_root)
    _assert_no_symlink_components(output, allow_missing_tail=True)
    if output.exists() and not output.is_dir():
        raise FactoryPlanningError("output_root must be a directory")
    overlaps_source = source.is_dir() and _is_within(output, source)
    contains_source = _is_within(source, output)
    if overlaps_source or contains_source:
        raise FactoryPlanningError("source and output_root must not overlap")
    return output


def _walk_source(source: Path) -> tuple[list[dict[str, Any]], str]:
    """Hash exact file bytes and a canonical, path-sensitive tree."""

    records: list[dict[str, Any]] = []
    directories: list[str] = []
    if source.is_file():
        artifact_sha256, size = _sha256_path(source)
        records.append(
            {
                "path": source.name,
                "size": size,
                "artifact_sha256": artifact_sha256,
            }
        )
    else:
        stack = [(source, Path("."))]
        while stack:
            directory, relative_directory = stack.pop()
            children = sorted(os.scandir(directory), key=lambda item: item.name)
            pending_directories: list[tuple[Path, Path]] = []
            for child in children:
                child_path = Path(child.path)
                relative = relative_directory / child.name
                mode = child.stat(follow_symlinks=False).st_mode
                if stat.S_ISLNK(mode):
                    raise FactoryPlanningError(f"symlinks are forbidden in source trees: {relative}")
                if stat.S_ISDIR(mode):
                    directories.append(relative.as_posix())
                    pending_directories.append((child_path, relative))
                    continue
                if not stat.S_ISREG(mode):
                    raise FactoryPlanningError(f"special files are forbidden in source trees: {relative}")
                artifact_sha256, size = _sha256_path(child_path)
                records.append(
                    {
                        "path": relative.as_posix(),
                        "size": size,
                        "artifact_sha256": artifact_sha256,
                    }
                )
            stack.extend(reversed(pending_directories))

    records.sort(key=lambda row: row["path"])
    directories.sort()
    digest = hashlib.sha256()
    digest.update(b"mccompiler-exact-tree-v1\0")
    for directory in directories:
        _frame(digest, "directory", directory, 0, "0" * 64)
    for record in records:
        _frame(
            digest,
            "file",
            record["path"],
            record["size"],
            record["artifact_sha256"],
        )
    return records, digest.hexdigest()


def _safe_archive_name(name: str) -> bool:
    if not name or "\x00" in name or "\\" in name or name.startswith("/"):
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def _validate_archive_directory(archive: zipfile.ZipFile, locator: str) -> list[zipfile.ZipInfo]:
    infos = archive.infolist()
    if len(infos) > MAX_ARCHIVE_ENTRIES:
        raise FactoryPlanningError(f"archive entry limit exceeded: {locator}")
    seen: set[str] = set()
    portable_seen: set[str] = set()
    for info in infos:
        name = info.filename
        if not _safe_archive_name(name):
            raise FactoryPlanningError(f"unsafe archive member in {locator}: {name!r}")
        mode = info.external_attr >> 16
        if mode and stat.S_ISLNK(mode):
            raise FactoryPlanningError(f"archive symlinks are forbidden in {locator}: {name}")
        if name in seen:
            raise FactoryPlanningError(f"duplicate archive member in {locator}: {name}")
        seen.add(name)
        portable = unicodedata.normalize("NFC", name).casefold()
        if portable in portable_seen:
            raise FactoryPlanningError(f"portable-name collision in {locator}: {name}")
        portable_seen.add(portable)
    return infos


def _bounded_read(archive: zipfile.ZipFile, info: zipfile.ZipInfo, *, limit: int) -> bytes:
    if info.file_size > limit:
        raise FactoryPlanningError(f"archive member exceeds read limit: {info.filename}")
    try:
        with archive.open(info, "r") as stream:
            data = stream.read(limit + 1)
    except (RuntimeError, zipfile.BadZipFile, OSError) as exc:
        raise FactoryPlanningError(f"cannot safely read archive member: {info.filename}") from exc
    if len(data) > limit:
        raise FactoryPlanningError(f"archive member exceeds read limit: {info.filename}")
    return data


def _safe_declared_name(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = unicodedata.normalize("NFC", " ".join(value.split())).strip()
    if not normalized or len(normalized) > 160:
        return None
    if any(unicodedata.category(character).startswith("C") for character in normalized):
        return None
    if "://" in normalized or normalized.startswith(("/", "~")):
        return None
    return normalized


def _json_object(data: bytes) -> Any | None:
    try:
        return json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _metadata_names(
    archive: zipfile.ZipFile,
    infos_by_name: Mapping[str, zipfile.ZipInfo],
) -> tuple[list[str], list[str], bool]:
    """Read display names only from a fixed metadata allow-list."""

    names: set[str] = set()
    sources: list[str] = []
    pack_manifest = False

    def add(value: Any) -> None:
        safe = _safe_declared_name(value)
        if safe is not None:
            names.add(safe)

    for filename in ("fabric.mod.json", "quilt.mod.json", "manifest.json", "modrinth.index.json"):
        info = infos_by_name.get(filename)
        if info is None or info.is_dir():
            continue
        data = _json_object(_bounded_read(archive, info, limit=MAX_METADATA_BYTES))
        if not isinstance(data, dict):
            continue
        sources.append(filename)
        if filename == "fabric.mod.json":
            add(data.get("name"))
        elif filename == "quilt.mod.json":
            loader = data.get("quilt_loader")
            if isinstance(loader, dict):
                metadata = loader.get("metadata")
                if isinstance(metadata, dict):
                    add(metadata.get("name"))
        else:
            add(data.get("name"))
            pack_manifest = True

    for filename in ("META-INF/mods.toml", "META-INF/neoforge.mods.toml"):
        info = infos_by_name.get(filename)
        if info is None or info.is_dir():
            continue
        try:
            data = tomllib.loads(_bounded_read(archive, info, limit=MAX_METADATA_BYTES).decode("utf-8-sig"))
        except (UnicodeDecodeError, tomllib.TOMLDecodeError):
            continue
        sources.append(filename)
        mods = data.get("mods", [])
        if isinstance(mods, list):
            for mod in mods:
                if isinstance(mod, dict):
                    add(mod.get("displayName"))

    info = infos_by_name.get("mcmod.info")
    if info is not None and not info.is_dir():
        data = _json_object(_bounded_read(archive, info, limit=MAX_METADATA_BYTES))
        rows = data if isinstance(data, list) else [data]
        for row in rows:
            if isinstance(row, dict):
                add(row.get("name"))
        if isinstance(data, (dict, list)):
            sources.append("mcmod.info")

    manifest = infos_by_name.get("META-INF/MANIFEST.MF")
    if manifest is not None and not manifest.is_dir():
        try:
            text = _bounded_read(archive, manifest, limit=MAX_METADATA_BYTES).decode("utf-8-sig")
        except UnicodeDecodeError:
            text = ""
        found = False
        for line in text.splitlines():
            key, separator, value = line.partition(":")
            if separator and key.casefold() in {"implementation-title", "specification-title"}:
                add(value)
                found = True
        if found:
            sources.append("META-INF/MANIFEST.MF")

    return sorted(names), sorted(set(sources)), pack_manifest


def _inspect_archive_bytes(data: bytes, locator: str, suffix: str) -> tuple[dict[str, Any], list[tuple[str, bytes]]]:
    artifact_sha256 = _sha256_bytes(data)
    opaque_digest = hashlib.sha256(
        b"mccompiler-opaque-unit-v1\0" + bytes.fromhex(artifact_sha256)
    ).hexdigest()
    try:
        archive = zipfile.ZipFile(io.BytesIO(data), "r")
    except zipfile.BadZipFile as exc:
        raise FactoryPlanningError(f"invalid archive: {locator}") from exc
    with archive:
        infos = _validate_archive_directory(archive, locator)
        by_name = {info.filename: info for info in infos}
        declared_names, metadata_sources, pack_manifest = _metadata_names(archive, by_name)
        nested: list[tuple[str, bytes]] = []
        if suffix == ".zip":
            for info in infos:
                member_suffix = PurePosixPath(info.filename).suffix.lower()
                if info.is_dir() or member_suffix not in ARCHIVE_SUFFIXES:
                    continue
                nested.append(
                    (
                        f"{locator}!/{info.filename}",
                        _bounded_read(archive, info, limit=MAX_NESTED_ARCHIVE_BYTES),
                    )
                )
        if suffix == ".jar" or metadata_sources and not pack_manifest:
            unit_kind = "MOD_ARCHIVE"
        elif nested or pack_manifest:
            unit_kind = "PACK_CONTAINER"
        else:
            unit_kind = "ARCHIVE_REVIEW_REQUIRED"
        return (
            {
                "unit_id": f"unit-{opaque_digest}",
                "unit_kind": unit_kind,
                "artifact_sha256": artifact_sha256,
                "size": len(data),
                "source_locators": [locator],
                "evidence_metadata": {
                    "declared_names": declared_names,
                    "metadata_sources": metadata_sources,
                },
                "archive_safety": {
                    "entry_count": len(infos),
                    "path_validation": "PASSED",
                    "symlink_validation": "PASSED",
                    "content_executed": False,
                    "content_extracted": False,
                },
            },
            nested,
        )


def _discover_units(source: Path, files: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[tuple[str, Path]] = []
    if source.is_file():
        candidates.append((source.name, source))
    else:
        for record in files:
            relative = str(record["path"])
            if PurePosixPath(relative).suffix.lower() in ARCHIVE_SUFFIXES:
                candidates.append((relative, source / relative))

    units_by_id: dict[str, dict[str, Any]] = {}
    records_by_path = {str(record["path"]): record for record in files}
    for locator, path in candidates:
        artifact_sha256, size, data = _read_regular_file(path, retain_bytes=True)
        assert data is not None
        expected = records_by_path[locator]
        if artifact_sha256 != expected["artifact_sha256"] or size != expected["size"]:
            raise FactoryPlanningError(f"source changed between tree hash and archive intake: {locator}")
        unit, nested = _inspect_archive_bytes(data, locator, path.suffix.lower())
        existing = units_by_id.get(unit["unit_id"])
        if existing is None:
            units_by_id[unit["unit_id"]] = unit
        else:
            existing["source_locators"] = sorted(set(existing["source_locators"] + [locator]))
        for nested_locator, nested_data in nested:
            nested_suffix = PurePosixPath(nested_locator).suffix.lower()
            nested_unit, _ = _inspect_archive_bytes(nested_data, nested_locator, nested_suffix)
            existing_nested = units_by_id.get(nested_unit["unit_id"])
            if existing_nested is None:
                units_by_id[nested_unit["unit_id"]] = nested_unit
            else:
                existing_nested["source_locators"] = sorted(
                    set(existing_nested["source_locators"] + [nested_locator])
                )
    return [units_by_id[key] for key in sorted(units_by_id)]


def _authorization_records(
    inspection_authority: str,
    overrides: Mapping[str, Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not isinstance(inspection_authority, str) or not inspection_authority.strip():
        raise FactoryPlanningError("inspection_authority must identify the caller authorization")
    overrides = overrides or {}
    unknown = sorted(set(overrides) - set(AUTHORIZATION_IDS))
    if unknown:
        raise FactoryPlanningError(f"unknown authorization ids: {', '.join(unknown)}")
    records: list[dict[str, Any]] = []
    for authorization_id in AUTHORIZATION_IDS:
        supplied = overrides.get(authorization_id, {})
        status = supplied.get("status", "PENDING")
        if status not in AUTHORIZATION_STATUSES:
            raise FactoryPlanningError(f"invalid authorization status for {authorization_id}: {status}")
        evidence_sha256 = supplied.get("evidence_sha256")
        if evidence_sha256 is not None and (
            not isinstance(evidence_sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", evidence_sha256)
        ):
            raise FactoryPlanningError(
                f"evidence_sha256 for {authorization_id} must be lowercase SHA-256"
            )
        authority = supplied.get("authority")
        if status in INSPECTION_PERMITTED_STATUSES and (
            authority is not None and (not isinstance(authority, str) or not authority.strip())
        ):
            raise FactoryPlanningError(f"authority for {authorization_id} must be a non-empty string")
        record = {
            "authorization_id": authorization_id,
            "status": status,
            "authority": authority,
            "evidence_ref": supplied.get("evidence_ref"),
            "evidence_sha256": evidence_sha256,
            "required_before": supplied.get("required_before", _authorization_boundary(authorization_id)),
        }
        records.append(record)

    inspection = next(
        record for record in records
        if record["authorization_id"] == "SOURCE_METADATA_INSPECTION_AUTHORIZED"
    )
    if inspection["status"] == "PENDING":
        inspection.update({"status": "AUTHORIZED", "authority": inspection_authority})
    if inspection["status"] not in INSPECTION_PERMITTED_STATUSES:
        raise FactoryPlanningError("source metadata inspection is not authorized")
    if not inspection["authority"]:
        inspection["authority"] = inspection_authority
    return records


def _authorization_boundary(authorization_id: str) -> str:
    if authorization_id == "SOURCE_METADATA_INSPECTION_AUTHORIZED":
        return "INTAKE"
    if authorization_id in {"STATIC_ANALYSIS_AUTHORIZED", "ABSTRACT_BEHAVIOR_EXTRACTION_AUTHORIZED"}:
        return "EVIDENCE_ANALYSIS"
    if authorization_id in {
        "PRIVATE_REIMPLEMENTATION_AUTHORIZED",
        "PRODUCTION_AUTHORIZED",
    }:
        return "PRODUCTION_LANE_CREATION"
    if authorization_id in {
        "SOURCE_ASSET_REUSE_AUTHORIZED",
        "BRANDING_REUSE_AUTHORIZED",
    }:
        return "ANY_SOURCE_MATERIAL_REUSE"
    if authorization_id in {"COMMERCIAL_DISTRIBUTION_AUTHORIZED", "PUBLICATION_AUTHORIZED"}:
        return "PUBLICATION"
    if authorization_id in {"MARKETPLACE_SUBMISSION_AUTHORIZED", "RELEASE_AUTHORIZED"}:
        return "RELEASE"
    raise AssertionError(authorization_id)


def inspect_modpack(
    source_path: str | Path,
    *,
    inspection_authority: str,
    authorization_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Inspect an authorized local source without executing or extracting it."""

    source = validate_source_path(source_path)
    authorizations = _authorization_records(inspection_authority, authorization_overrides)
    files, tree_sha256 = _walk_source(source)
    units = _discover_units(source, files)
    inventory = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "record_type": "MODPACK_INTAKE",
        "source": {
            "path": str(source),
            "kind": "ARCHIVE" if source.is_file() else "DIRECTORY",
            "tree_sha256": tree_sha256,
            "file_count": len(files),
            "files": files,
            "read_only": True,
            "symlink_policy": "REJECT",
        },
        "authorizations": authorizations,
        "units": units,
        "execution": {
            "archive_content_executed": False,
            "archive_content_extracted": False,
            "network_used": False,
        },
    }
    inventory["intake_sha256"] = _sha256_bytes(_canonical_bytes(inventory))
    return inventory


def _role_boundaries(output: Path) -> list[dict[str, Any]]:
    lanes = output / "lanes"
    return [
        {
            "role": "overseer",
            "lane": "CONTROL",
            "interface": "THREAD_CONVERSATION",
            "write_root": str(lanes / "control"),
            "may": ["select_local_source", "record_authorizations", "approve_scope", "route_structured_messages"],
            "must_not": ["perform_evidence_analysis", "author_production", "self-certify_downstream_gates"],
        },
        {
            "role": "task_maker",
            "lane": "CONTROL",
            "write_root": str(lanes / "control" / "tasks"),
            "may": ["separate_opaque_units", "materialize_hash_bound_assignments", "schedule_ready_tasks"],
            "must_not": ["execute_archive_content", "grant_authority", "copy_source_identity_into_production"],
        },
        {
            "role": "evidence_analyst",
            "lane": "EVIDENCE",
            "write_root": str(lanes / "evidence"),
            "may": ["read_authorized_source", "record_source_observations", "build_private_feature_graph"],
            "must_not": ["read_or_write_production", "grant_production_or_release_authority"],
        },
        {
            "role": "contract_steward",
            "lane": "CONTROL",
            "write_root": str(lanes / "control" / "contracts"),
            "may": ["read_evidence_claims", "select_product_requirements", "publish_sanitized_contracts"],
            "must_not": ["author_production", "transfer_source_names_paths_hashes_or_private_oracles"],
        },
        {
            "role": "feature_producer",
            "lane": "PRODUCTION",
            "write_root": str(lanes / "production"),
            "may": ["read_sanitized_contract", "author_original_bedrock_output", "build_candidate", "freeze_candidate"],
            "must_not": ["read_evidence_or_private_oracle", "edit_frozen_candidates", "run_or_claim_downstream_gates"],
        },
        {
            "role": "pre_bds_milestone_owner",
            "lane": "QUALIFICATION",
            "write_root": str(lanes / "qualification" / "pre-bds"),
            "may": ["run_pre_bds_milestone_once", "publish_hash_bound_milestone_receipt"],
            "must_not": ["repair_candidate", "repeat_worker_validation", "claim_bds_or_semantic_results"],
        },
        {
            "role": "bds_tester",
            "lane": "QUALIFICATION",
            "write_root": str(lanes / "qualification" / "bds"),
            "may": ["run_exact_package_stable_bds", "publish_hash_bound_receipt"],
            "must_not": ["edit_candidate", "claim_client_realms_controller_split_screen_or_console_results"],
        },
        {
            "role": "final_mod_milestone_owner",
            "lane": "AUDIT",
            "write_root": str(lanes / "audit"),
            "may": ["run_final_mod_milestone_once", "read_frozen_candidate_and_authorized_oracle", "publish_opaque_findings"],
            "must_not": ["edit_candidate", "reveal_private_cases_to_production", "rerun_unchanged_milestones"],
        },
        {
            "role": "t2_adapter_owner",
            "lane": "INTEGRATION",
            "write_root": str(lanes / "integration" / "adapters"),
            "may": ["implement_admitted_shared_adapter", "publish_adapter_receipt"],
            "must_not": ["read_java_evidence", "silently_expand_pack_scope"],
        },
        {
            "role": "segment_integrator",
            "lane": "INTEGRATION",
            "write_root": str(lanes / "integration"),
            "may": ["combine_frozen_candidates", "run_integration_local_checks", "freeze_integrated_candidate"],
            "must_not": ["read_java_evidence", "rewrite_pack_candidate_history"],
        },
    ]


def _task_id(prefix: str, unit_id: str) -> str:
    digest = unit_id.removeprefix("unit-")
    return f"{prefix}-{digest[:OPAQUE_ID_PREFIX_BYTES]}"


def _unit_tasks(unit: Mapping[str, Any]) -> list[dict[str, Any]]:
    unit_id = str(unit["unit_id"])
    evidence = _task_id("evidence", unit_id)
    contract = _task_id("contract", unit_id)
    production = _task_id("production", unit_id)
    pre_bds = _task_id("pre-bds", unit_id)
    bds = _task_id("bds", unit_id)
    final_mod = _task_id("final-mod", unit_id)
    common = {"unit_id": unit_id, "source_identity_exposure": "OPAQUE_ID_ONLY_OUTSIDE_EVIDENCE"}
    tasks = [
        {
            **common,
            "task_id": evidence,
            "role": "evidence_analyst",
            "lane": "EVIDENCE",
            "action": "BUILD_AUTHORIZED_SOURCE_OBSERVATIONS",
            "depends_on": [],
            "required_authorizations": ["STATIC_ANALYSIS_AUTHORIZED", "ABSTRACT_BEHAVIOR_EXTRACTION_AUTHORIZED"],
            "completion": "HASH_BOUND_EVIDENCE_CLAIMS_PUBLISHED",
        },
        {
            **common,
            "task_id": contract,
            "role": "contract_steward",
            "lane": "CONTROL",
            "action": "PUBLISH_SANITIZED_PRODUCT_CONTRACT",
            "depends_on": [evidence],
            "required_authorizations": [],
            "completion": "CONTRACT_SANITIZED",
        },
        {
            **common,
            "task_id": production,
            "role": "feature_producer",
            "lane": "PRODUCTION",
            "action": "AUTHOR_FREEZE_AND_SUBMIT_ONE_IMMUTABLE_CANDIDATE",
            "depends_on": [contract],
            "required_authorizations": ["PRIVATE_REIMPLEMENTATION_AUTHORIZED", "PRODUCTION_AUTHORIZED"],
            "input_policy": "SANITIZED_CONTRACT_AND_PRODUCTION_ORACLE_INTERFACE_ONLY",
            "always_on_invariants": [
                "identity_syntax",
                "referenced_hash_equality",
                "path_containment",
                "exclusive_write_scope",
            ],
            "activation_record": "MINIMAL_ACTIVATION_ATTESTATION",
            "validation_jobs": "NONE_UNTIL_PRE_BDS_MILESTONE",
            "completion": "CANDIDATE_SUBMITTED",
        },
        {
            **common,
            "task_id": pre_bds,
            "role": "pre_bds_milestone_owner",
            "lane": "QUALIFICATION",
            "action": "VALIDATE_PRE_BDS_MILESTONE",
            "depends_on": [production],
            "required_authorizations": [],
            "validation_scope": [
                "exact_candidate_binding",
                "deterministic_build_twice",
                "package_structure_manifest_icons_entrypoint",
                "archive_media_reference_integrity",
                "restricted_identifier_and_object_scans",
                "t1_and_mctools_mechanical_admission",
            ],
            "completion": "PRE_BDS_MILESTONE_PASS",
        },
        {
            **common,
            "task_id": bds,
            "role": "bds_tester",
            "lane": "QUALIFICATION",
            "action": "RUN_EXACT_PACKAGE_STABLE_BDS",
            "depends_on": [pre_bds],
            "required_authorizations": [],
            "completion": "BDS_RESULT_PUBLISHED",
        },
        {
            **common,
            "task_id": final_mod,
            "role": "final_mod_milestone_owner",
            "lane": "AUDIT",
            "action": "VALIDATE_FINAL_MOD_MILESTONE",
            "depends_on": [bds],
            "required_authorizations": [],
            "validation_scope": [
                "exact_final_package_binding",
                "required_bds_runtime_receipts",
                "calibrated_observation_and_independent_t10",
                "integration_and_persistence",
                "lineage_originality_and_claim_boundaries",
                "final_bundle_manifest_coverage",
            ],
            "completion": "FINAL_MOD_MILESTONE_PASS",
        },
    ]
    if unit["unit_kind"] != "MOD_ARCHIVE":
        for task in tasks[1:]:
            task["dispatch_condition"] = "EVIDENCE_ANALYST_CLASSIFIES_AS_CONVERTIBLE_UNIT"
    return tasks


def build_factory_plan(
    source_path: str | Path,
    output_root: str | Path,
    *,
    inspection_authority: str,
    authorization_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic plan; do not create files or directories."""

    source = validate_source_path(source_path)
    output = validate_output_root(source, output_root)
    intake = inspect_modpack(
        source,
        inspection_authority=inspection_authority,
        authorization_overrides=authorization_overrides,
    )
    tasks = [task for unit in intake["units"] for task in _unit_tasks(unit)]
    plan: dict[str, Any] = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "record_type": PLAN_RECORD_TYPE,
        "intake": intake,
        "output_boundary": {
            "root": str(output),
            "writes_outside_root": "FORBIDDEN",
            "network": "FORBIDDEN",
            "ui": "NONE_THREAD_CONVERSATION_IS_THE_INTERFACE",
        },
        "roles": _role_boundaries(output),
        "tasks": tasks,
        "mailbox_policy": {
            "history": "APPEND_ONLY",
            "delivery": "IDEMPOTENT_BY_MESSAGE_HASH_AND_PARENT",
            "repair": "ONE_CONSOLIDATED_MESSAGE_BOUND_TO_ONE_REJECTED_GENERATION",
            "candidate_generations": "IMMUTABLE_REPLACEMENT_IS_EXACTLY_PLUS_ONE",
            "wake_payload": "TASK_PACKET_PATH_AND_SHA256_ONLY",
        },
        "repair_loop": {
            "maximum_candidates_per_activation": 1,
            "preserve_rejected_candidate": True,
            "required_inputs": ["consolidated_finding_message", "rejected_generation", "next_generation"],
            "worker_completion": "REPLACEMENT_CANDIDATE_SUBMITTED",
            "downstream_retest_owner": "ORIGINAL_GATE_OWNER",
        },
        "validation_policy": {
            "mode": "MILESTONE_ONLY",
            "milestones": ["PRE_BDS_MILESTONE", "FINAL_MOD_MILESTONE"],
            "rule": "RUN_ONLY_ON_MILESTONE_ENTRY_OR_BOUND_HASH_CHANGE_OR_MISSING_INVALID_RECEIPT",
            "unchanged_valid_receipt": "REUSE",
            "per_activation_validation_jobs": "FORBIDDEN",
        },
        "external_gates": [
            {"gate": "PRE_BDS_MILESTONE", "owner": "pre_bds_milestone_owner", "worker_publication_prerequisite": False},
            {"gate": "STABLE_BDS", "owner": "bds_tester", "worker_publication_prerequisite": False},
            {"gate": "FINAL_MOD_MILESTONE", "owner": "final_mod_milestone_owner", "worker_publication_prerequisite": False},
        ],
        "optional_claim_extensions": {
            "dispatch": "ONLY_AFTER_EXPLICIT_USER_AUTHORITY_AND_OUTSIDE_RECONSTRUCTION_COMPLETION",
            "claims": ["DESKTOP_CLIENT", "REALMS", "CONTROLLER", "SPLIT_SCREEN", "PHYSICAL_PS4", "PUBLIC_RELEASE"],
        },
        "release_authorizations": [
            "PUBLICATION_AUTHORIZED",
            "COMMERCIAL_DISTRIBUTION_AUTHORIZED",
            "MARKETPLACE_SUBMISSION_AUTHORIZED",
            "RELEASE_AUTHORIZED",
        ],
    }
    plan["plan_id"] = f"plan-sha256-{_sha256_bytes(_canonical_bytes(plan))}"
    return plan


def write_factory_plan(
    source_path: str | Path,
    output_root: str | Path,
    *,
    inspection_authority: str,
    authorization_overrides: Mapping[str, Mapping[str, Any]] | None = None,
    filename: str = "factory-plan.json",
) -> Path:
    """Write the canonical plan inside ``output_root`` and nowhere else.

    Existing identical output is accepted idempotently.  Existing different
    output is never overwritten.
    """

    if not _SAFE_OUTPUT_NAME.fullmatch(filename) or filename in {".", ".."}:
        raise FactoryPlanningError("filename must be one portable basename")
    source = validate_source_path(source_path)
    output = validate_output_root(source, output_root)
    plan = build_factory_plan(
        source,
        output,
        inspection_authority=inspection_authority,
        authorization_overrides=authorization_overrides,
    )
    encoded = json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    output.mkdir(parents=True, exist_ok=True)
    target = output / filename
    _assert_no_symlink_components(target, allow_missing_tail=True)
    if target.exists():
        if target.is_file() and target.read_bytes() == encoded:
            return target
        raise FactoryPlanningError(f"refusing to overwrite existing output: {target}")
    try:
        with target.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if target.is_file() and target.read_bytes() == encoded:
            return target
        raise FactoryPlanningError(f"refusing to overwrite existing output: {target}") from None
    return target


__all__ = [
    "FactoryPlanningError",
    "PLAN_RECORD_TYPE",
    "PLAN_SCHEMA_VERSION",
    "build_factory_plan",
    "inspect_modpack",
    "validate_output_root",
    "validate_source_path",
    "write_factory_plan",
]
