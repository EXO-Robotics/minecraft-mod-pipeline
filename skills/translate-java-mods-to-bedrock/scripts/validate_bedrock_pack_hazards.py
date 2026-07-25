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


def validate(bp: Path, rp: Path, cooperative: bool) -> dict[str, Any]:
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
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        findings.append({"code": "MANIFEST_INVALID", "path": "manifest.json", "detail": str(error)})

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
    args = parser.parse_args()
    result = validate(args.behavior_pack, args.resource_pack, args.cooperative)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
