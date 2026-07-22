from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from .io import read_json


def validate_output(path: str | Path) -> dict[str, Any]:
    root = Path(path).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifests = sorted(root.rglob("manifest.json")) if root.exists() else []
    uuids: dict[str, Path] = {}
    modules = []
    parsed_manifests: list[tuple[Path, dict[str, Any]]] = []
    for manifest in manifests:
        data = read_json(manifest)
        if not isinstance(data, dict):
            errors.append(f"Invalid JSON manifest: {manifest}")
            continue
        parsed_manifests.append((manifest, data))
        header = data.get("header")
        if not isinstance(header, dict) or not header.get("uuid") or not header.get("version"):
            errors.append(f"Manifest missing header identity/version: {manifest}")
        elif header["uuid"] in uuids:
            errors.append(f"Duplicate pack UUID {header['uuid']}: {manifest} and {uuids[header['uuid']]}")
        else:
            uuids[header["uuid"]] = manifest
        for module in data.get("modules", []) or []:
            if not isinstance(module, dict) or module.get("type") not in {"data", "resources", "script"}:
                errors.append(f"Unknown module in {manifest}")
            else:
                modules.append(module)
    # Resolve pack UUID dependencies after collecting every manifest, so a
    # behavior pack can depend on a resource pack that sorts later on disk.
    known_uuids = set(uuids)
    for manifest, data in parsed_manifests:
        for dependency in data.get("dependencies", []) or []:
            if isinstance(dependency, dict) and dependency.get("uuid") and dependency["uuid"] not in uuids:
                if dependency["uuid"] not in known_uuids:
                    warnings.append(f"Pack dependency may be unresolved: {dependency['uuid']}")
    archive = root / "generated.mcaddon"
    if archive.exists():
        try:
            with zipfile.ZipFile(archive) as bundle:
                names = set(bundle.namelist())
                if not any(name.endswith("/behavior_pack/manifest.json") or name == "behavior_pack/manifest.json" for name in names):
                    warnings.append("Archive does not contain a conventional behavior_pack/manifest.json path")
                if bundle.testzip() is not None:
                    errors.append("Archive contains a corrupt member")
        except zipfile.BadZipFile:
            errors.append(f"Invalid mcaddon archive: {archive}")
    if not root.exists():
        errors.append(f"Output does not exist: {root}")
    return {"path": str(root), "manifest_count": len(manifests), "module_count": len(modules), "errors": errors, "warnings": warnings, "valid": not errors}
