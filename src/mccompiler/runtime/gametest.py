from __future__ import annotations

import hashlib
import json
import struct
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class GameTestDiagnosticError(RuntimeError):
    pass


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _nbt_byte(name: str, value: int) -> bytes:
    encoded = name.encode("utf-8")
    return b"\x01" + struct.pack("<H", len(encoded)) + encoded + struct.pack("<b", value)


def enable_gametest_experiment(level_dat: bytes) -> bytes:
    if len(level_dat) < 12:
        raise GameTestDiagnosticError("level.dat is too short")
    version, declared = struct.unpack("<II", level_dat[:8])
    payload = level_dat[8:]
    if declared != len(payload) or payload[:3] != b"\x0a\x00\x00" or payload[-1:] != b"\x00":
        raise GameTestDiagnosticError("level.dat is not a supported little-endian root compound")
    if b"\x0b\x00experiments" in payload:
        raise GameTestDiagnosticError("level.dat already contains an experiments compound")
    name = b"experiments"
    experiments = b"\x0a" + struct.pack("<H", len(name)) + name
    experiments += _nbt_byte("experiments_ever_used", 1)
    experiments += _nbt_byte("gametest", 1)
    experiments += _nbt_byte("saved_with_toggled_experiments", 1)
    experiments += b"\x00"
    updated = payload[:-1] + experiments + b"\x00"
    return struct.pack("<II", version, len(updated)) + updated


def _safe_archive_files(path: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                relative = PurePosixPath(member.filename)
                if relative.is_absolute() or ".." in relative.parts:
                    raise GameTestDiagnosticError(f"unsafe archive path: {member.filename}")
                if member.is_dir():
                    continue
                files[relative.as_posix()] = archive.read(member)
    except (OSError, zipfile.BadZipFile) as exc:
        raise GameTestDiagnosticError(f"invalid .mcworld: {path}") from exc
    return files


def _load_diagnostic_pack(pack_root: Path) -> tuple[dict[str, bytes], str, list[int], str]:
    if not pack_root.is_dir():
        raise GameTestDiagnosticError(f"diagnostic behavior pack does not exist: {pack_root}")
    try:
        manifest = json.loads((pack_root / "manifest.json").read_text(encoding="utf-8"))
        header = manifest["header"]
        pack_id = str(header["uuid"])
        version = [int(part) for part in header["version"]]
        name = str(header["name"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise GameTestDiagnosticError("diagnostic behavior pack has an invalid manifest") from exc
    try:
        uuid.UUID(pack_id)
    except ValueError as exc:
        raise GameTestDiagnosticError("diagnostic behavior pack UUID is invalid") from exc
    if len(version) != 3 or any(part < 0 for part in version):
        raise GameTestDiagnosticError("diagnostic behavior pack version is invalid")
    dependencies = manifest.get("dependencies", [])
    if not any(
        isinstance(row, dict) and row.get("module_name") == "@minecraft/server-gametest"
        and "beta" in str(row.get("version", ""))
        for row in dependencies
    ):
        raise GameTestDiagnosticError("diagnostic pack must declare a beta @minecraft/server-gametest dependency")
    files: dict[str, bytes] = {}
    for source in sorted(pack_root.rglob("*"), key=lambda item: item.as_posix()):
        if source.is_symlink():
            raise GameTestDiagnosticError(f"diagnostic behavior pack contains a symlink: {source}")
        if source.is_file():
            files[source.relative_to(pack_root).as_posix()] = source.read_bytes()
    if "manifest.json" not in files or not any(path.startswith("scripts/") for path in files):
        raise GameTestDiagnosticError("diagnostic behavior pack must contain a manifest and scripts")
    folder = "".join(character if character.isalnum() or character in "._-" else "_" for character in name)
    return files, pack_id, version, f"{folder.strip('._') or 'diagnostic'}-{pack_id[:8]}"


def augment_mcworld_with_gametest_pack(
    source_world: str | Path,
    diagnostic_pack: str | Path,
    destination: str | Path,
    *,
    diagnostic_server_version: str | None = None,
) -> dict[str, Any]:
    source = Path(source_world).resolve()
    pack_root = Path(diagnostic_pack).resolve()
    output = Path(destination).resolve()
    if source == output:
        raise GameTestDiagnosticError("diagnostic output must not overwrite the source world")
    if source.suffix.lower() != ".mcworld" or output.suffix.lower() != ".mcworld":
        raise GameTestDiagnosticError("source and destination must use the .mcworld extension")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    files = _safe_archive_files(source)
    try:
        bindings = json.loads(files["world_behavior_packs.json"])
        level_dat = files["level.dat"]
    except (KeyError, json.JSONDecodeError) as exc:
        raise GameTestDiagnosticError("source world is missing valid pack bindings or level.dat") from exc
    if not isinstance(bindings, list):
        raise GameTestDiagnosticError("world_behavior_packs.json must be an array")
    module_overrides: list[dict[str, str]] = []
    if diagnostic_server_version is not None:
        parts = diagnostic_server_version.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise GameTestDiagnosticError("diagnostic server version must be a three-part numeric version")
        for relative in sorted(files):
            if not relative.startswith("behavior_packs/") or not relative.endswith("/manifest.json"):
                continue
            try:
                manifest = json.loads(files[relative])
            except json.JSONDecodeError as exc:
                raise GameTestDiagnosticError(f"embedded behavior-pack manifest is invalid: {relative}") from exc
            changed = False
            for dependency in manifest.get("dependencies", []):
                if not isinstance(dependency, dict) or dependency.get("module_name") != "@minecraft/server":
                    continue
                previous = str(dependency.get("version", ""))
                if previous == diagnostic_server_version:
                    continue
                dependency["version"] = diagnostic_server_version
                module_overrides.append({
                    "manifest": relative,
                    "module": "@minecraft/server",
                    "from": previous,
                    "to": diagnostic_server_version,
                })
                changed = True
            if changed:
                files[relative] = _canonical_json(manifest)
        if not module_overrides:
            raise GameTestDiagnosticError("diagnostic server version requested but no embedded @minecraft/server dependency was found")
    pack_files, pack_id, version, folder = _load_diagnostic_pack(pack_root)
    if any(isinstance(row, dict) and row.get("pack_id") == pack_id for row in bindings):
        raise GameTestDiagnosticError("diagnostic behavior pack is already bound")
    prefix = f"behavior_packs/{folder}/"
    if any(path.startswith(prefix) for path in files):
        raise GameTestDiagnosticError("diagnostic behavior pack path collides with the source world")
    files.update({prefix + relative: payload for relative, payload in pack_files.items()})
    files["world_behavior_packs.json"] = _canonical_json([*bindings, {"pack_id": pack_id, "version": version}])
    files["level.dat"] = enable_gametest_experiment(level_dat)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, payload in sorted(files.items()):
            info = zipfile.ZipInfo(relative, _ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0
            archive.writestr(info, payload)
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise GameTestDiagnosticError("source world changed while building diagnostic world")
    payload = output.read_bytes()
    return {
        "schema_version": "1.0.0",
        "classification": "simulated_player_diagnostic",
        "source_world": {"path": str(source), "sha256": source_hash, "unchanged": True},
        "diagnostic_world": {"path": str(output), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)},
        "diagnostic_pack": {"uuid": pack_id, "version": version, "folder": folder},
        "experiments": ["gametest"],
        "production_pack_module_overrides": module_overrides,
        "production_pack_modified_for_preview_diagnostic": bool(module_overrides),
        "marketplace_or_console_evidence": False,
    }
