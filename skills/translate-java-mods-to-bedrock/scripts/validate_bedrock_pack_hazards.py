#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dependency_uuids(manifest: dict[str, Any]) -> set[str]:
    return {
        row["uuid"]
        for row in manifest.get("dependencies", [])
        if isinstance(row, dict) and isinstance(row.get("uuid"), str)
    }


def material_groups(block: dict[str, Any]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    root = block.get("components", {}).get("minecraft:material_instances")
    if isinstance(root, dict):
        groups.append(root)
    for row in block.get("permutations", []):
        group = row.get("components", {}).get("minecraft:material_instances")
        if isinstance(group, dict):
            groups.append(group)
    return groups


def stable_server_major(manifest: dict[str, Any]) -> int | None:
    for row in manifest.get("dependencies", []):
        if not isinstance(row, dict) or row.get("module_name") != "@minecraft/server":
            continue
        version = row.get("version")
        if isinstance(version, str):
            try:
                return int(version.split(".", 1)[0])
            except ValueError:
                return None
    return None


def validate(
    bp: Path,
    rp: Path,
    cooperative: bool,
    require_pack_icons: bool = False,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    parsed = 0
    for path in sorted((*bp.rglob("*.json"), *rp.rglob("*.json"))):
        try:
            read_json(path)
            parsed += 1
        except (OSError, json.JSONDecodeError) as error:
            findings.append({"code": "JSON_INVALID", "path": str(path), "detail": str(error)})

    for path in sorted((bp / "blocks").glob("*.json")):
        try:
            block = read_json(path).get("minecraft:block", {})
        except (OSError, json.JSONDecodeError):
            continue
        for index, group in enumerate(material_groups(block)):
            methods = {
                value.get("render_method")
                for value in group.values()
                if isinstance(value, dict) and isinstance(value.get("render_method"), str)
            }
            if len(methods) > 1:
                findings.append({
                    "code": "MIXED_MATERIAL_RENDER_METHODS",
                    "path": str(path),
                    "detail": f"group {index} mixes {sorted(methods)}",
                })

    try:
        bp_manifest = read_json(bp / "manifest.json")
        rp_manifest = read_json(rp / "manifest.json")
        bp_uuid = bp_manifest["header"]["uuid"]
        rp_uuid = rp_manifest["header"]["uuid"]
        if rp_manifest.get("header", {}).get("pack_scope") != "world":
            findings.append({
                "code": "RESOURCE_PACK_SCOPE",
                "path": str(rp / "manifest.json"),
                "detail": "header.pack_scope must be world for this cooperative profile",
            })
        if rp_uuid not in dependency_uuids(bp_manifest):
            findings.append({
                "code": "BP_MISSING_RP_DEPENDENCY",
                "path": str(bp / "manifest.json"),
                "detail": "behavior pack does not depend on resource pack UUID",
            })
        if bp_uuid not in dependency_uuids(rp_manifest):
            findings.append({
                "code": "RP_MISSING_BP_DEPENDENCY",
                "path": str(rp / "manifest.json"),
                "detail": "resource pack does not depend on behavior pack UUID",
            })

        if stable_server_major(bp_manifest) is not None and stable_server_major(bp_manifest) >= 2:
            for path in sorted((*bp.rglob("*.js"), *bp.rglob("*.ts"))):
                try:
                    source = path.read_text(encoding="utf-8")
                except OSError as error:
                    findings.append({
                        "code": "SCRIPT_READ_FAILED",
                        "path": str(path),
                        "detail": str(error),
                    })
                    continue
                if "world.beforeEvents.itemUseOn" in source:
                    findings.append({
                        "code": "REMOVED_SCRIPT_EVENT_MEMBER",
                        "path": str(path),
                        "detail": (
                            "world.beforeEvents.itemUseOn is not supported by "
                            "@minecraft/server 2.x"
                        ),
                    })
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        findings.append({"code": "MANIFEST_INVALID", "path": "manifest.json", "detail": str(error)})

    if require_pack_icons:
        for root, label in ((bp, "behavior"), (rp, "resource")):
            if not (root / "pack_icon.png").is_file():
                findings.append({
                    "code": "PACK_ICON_MISSING",
                    "path": str(root / "pack_icon.png"),
                    "detail": f"{label} pack icon is required by this profile",
                })

    if cooperative:
        for name in ("blocks", "items"):
            path = rp / "textures" / name
            if path.exists():
                findings.append({
                    "code": "LOOSE_TEXTURE_ROOT",
                    "path": str(path),
                    "detail": "place textures below textures/<creator>/<game>/ instead",
                })

    return {
        "schema_version": "1.0.0",
        "status": "PASS" if not findings else "FAIL",
        "json_files_parsed": parsed,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--behavior-pack", type=Path, required=True)
    parser.add_argument("--resource-pack", type=Path, required=True)
    parser.add_argument("--cooperative", action="store_true")
    parser.add_argument("--require-pack-icons", action="store_true")
    args = parser.parse_args()
    result = validate(
        args.behavior_pack,
        args.resource_pack,
        args.cooperative,
        args.require_pack_icons,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
