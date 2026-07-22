from __future__ import annotations

import hashlib
import json
import struct
import uuid as uuid_module
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class PackBinding:
    kind: str
    uuid: str
    version: tuple[int, int, int]
    source: Path
    folder: str

    def world_record(self) -> dict[str, Any]:
        return {"pack_id": self.uuid, "version": list(self.version)}


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _safe_folder(value: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in "._-" else "_" for character in value)
    return cleaned.strip("._") or "pack"


def _load_binding(root: Path, kind: str) -> PackBinding:
    manifest_path = root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        header = manifest["header"]
        uuid = str(header["uuid"])
        version = tuple(int(part) for part in header["version"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {kind} pack manifest: {manifest_path}") from exc
    if len(version) != 3 or any(part < 0 for part in version):
        raise ValueError(f"Invalid {kind} pack version: {version}")
    if not uuid:
        raise ValueError(f"Invalid {kind} pack UUID")
    try:
        uuid_module.UUID(uuid)
    except ValueError as exc:
        raise ValueError(f"Invalid {kind} pack UUID") from exc
    name = _safe_folder(str(header.get("name") or root.name))
    return PackBinding(kind, uuid, version, root.resolve(), f"{name}-{uuid[:8]}")


def _pack_inventory(bindings: Iterable[PackBinding]) -> list[tuple[str, bytes]]:
    bindings = tuple(bindings)
    files: list[tuple[str, bytes]] = []
    roots = {binding.source for binding in bindings}
    if len(roots) != len(bindings):
        raise ValueError("Behavior and resource packs must use different roots")
    for binding in bindings:
        if not binding.source.is_dir():
            raise ValueError(f"Pack root does not exist: {binding.source}")
        prefix = "behavior_packs" if binding.kind == "behavior" else "resource_packs"
        for path in sorted(binding.source.rglob("*"), key=lambda item: item.as_posix()):
            if path.is_symlink():
                raise ValueError(f"Pack contains a symlink: {path}")
            if path.is_file():
                relative = path.relative_to(binding.source).as_posix()
                files.append((f"{prefix}/{binding.folder}/{relative}", path.read_bytes()))
    return files


def compute_pack_hash(behavior_pack: str | Path, resource_pack: str | Path) -> str:
    bindings = (_load_binding(Path(behavior_pack), "behavior"), _load_binding(Path(resource_pack), "resource"))
    digest = hashlib.sha256()
    for relative, payload in _pack_inventory(bindings):
        encoded = relative.encode("utf-8")
        digest.update(struct.pack("<I", len(encoded)))
        digest.update(encoded)
        digest.update(struct.pack("<Q", len(payload)))
        digest.update(payload)
    return digest.hexdigest()


def _nbt_string(name: str, value: str) -> bytes:
    name_bytes = name.encode("utf-8")
    value_bytes = value.encode("utf-8")
    return b"\x08" + struct.pack("<H", len(name_bytes)) + name_bytes + struct.pack("<H", len(value_bytes)) + value_bytes


def _nbt_int(name: str, value: int) -> bytes:
    encoded = name.encode("utf-8")
    return b"\x03" + struct.pack("<H", len(encoded)) + encoded + struct.pack("<i", value)


def _nbt_long(name: str, value: int) -> bytes:
    encoded = name.encode("utf-8")
    return b"\x04" + struct.pack("<H", len(encoded)) + encoded + struct.pack("<q", value)


def _minimal_level_dat(world_name: str) -> bytes:
    root_name = b""
    payload = b"\x0a" + struct.pack("<H", len(root_name)) + root_name
    payload += _nbt_string("LevelName", world_name)
    payload += _nbt_int("StorageVersion", 10)
    payload += _nbt_int("NetworkVersion", 0)
    payload += _nbt_int("Generator", 1)
    payload += _nbt_int("GameType", 1)
    payload += _nbt_int("SpawnX", 0) + _nbt_int("SpawnY", 64) + _nbt_int("SpawnZ", 0)
    payload += _nbt_long("LastPlayed", 0)
    payload += b"\x00"
    return struct.pack("<II", 8, len(payload)) + payload


def _write_zip(path: Path, files: Iterable[tuple[str, bytes]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, payload in sorted(files, key=lambda item: item[0]):
            info = zipfile.ZipInfo(relative, _ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0
            archive.writestr(info, payload)


def generate_test_world(
    behavior_pack: str | Path,
    resource_pack: str | Path,
    output: str | Path,
    *,
    world_name: str = "MCCompiler Test World",
) -> dict[str, Any]:
    """Create a deterministic minimal .mcworld with embedded and bound BP/RP packs."""
    bp = _load_binding(Path(behavior_pack), "behavior")
    rp = _load_binding(Path(resource_pack), "resource")
    bindings = (bp, rp)
    inventory = _pack_inventory(bindings)
    pack_hash = compute_pack_hash(bp.source, rp.source)
    world_files = [
        ("level.dat", _minimal_level_dat(world_name)),
        ("levelname.txt", (world_name + "\n").encode("utf-8")),
        ("world_behavior_packs.json", _canonical_json([bp.world_record()])),
        ("world_resource_packs.json", _canonical_json([rp.world_record()])),
    ]
    destination = Path(output)
    if destination.suffix.lower() != ".mcworld":
        raise ValueError("Test-world output must use the .mcworld extension")
    _write_zip(destination, [*world_files, *inventory])
    world_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
    return {
        "schema_version": "1.0.0",
        "path": str(destination.resolve()),
        "world_name": world_name,
        "pack_hash": pack_hash,
        "world_hash": world_hash,
        "behavior_pack": bp.world_record(),
        "resource_pack": rp.world_record(),
    }
