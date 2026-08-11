#!/usr/bin/env python3
"""Deterministic, read-only static inventory of Wave 1 production packets."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
import struct
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PACKETS = {
    "001": ("001_whisperwood", "asset-sprint-001-whisperwood", "aionforge_ww"),
    "002": ("002_ashen_highlands", "asset-sprint-002-ashen-highlands", "aionforge_ah"),
    "003": ("003_crystal_marsh", "asset-sprint-003-crystal-marsh", "aionforge_cm"),
    "004": ("004_skyreach_cliffs", "asset-sprint-004-skyreach-cliffs", "aionforge_sr"),
    "006": ("006_equipment", "asset-sprint-006-equipment-progression", "aionforge_eq"),
}
CATEGORY_DIRS = {
    "creatures": "creatures", "resources": "resources", "blocks": "blocks",
    "plants": "plants", "structures": "props", "weapons": "weapons",
    "armor": "armor", "tools": "tools_items", "accessories": "accessories",
    "trophies": "trophies",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def parse_png(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    errors: list[str] = []
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return {"valid": False, "errors": ["PNG_SIGNATURE_INVALID"]}
    pos, chunks, idat = 8, [], bytearray()
    ihdr = None
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        crc = data[pos + 8 + length:pos + 12 + length]
        if len(body) != length or len(crc) != 4:
            errors.append("PNG_CHUNK_TRUNCATED")
            break
        if binascii.crc32(kind + body) & 0xFFFFFFFF != struct.unpack(">I", crc)[0]:
            errors.append(f"PNG_CRC_INVALID:{kind.decode('ascii', 'replace')}")
        chunks.append(kind.decode("ascii", "replace"))
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat.extend(body)
        pos += 12 + length
        if kind == b"IEND":
            break
    if not ihdr:
        errors.append("PNG_IHDR_MISSING")
        return {"valid": False, "errors": errors, "chunks": chunks}
    width, height, bit_depth, color_type, compression, filtering, interlace = ihdr
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if not width or not height or channels is None:
        errors.append("PNG_DIMENSION_OR_COLOR_INVALID")
    if compression != 0 or filtering != 0 or interlace != 0:
        errors.append("PNG_UNSUPPORTED_ENCODING")
    try:
        raw = zlib.decompress(bytes(idat))
        expected = height * (1 + ((width * channels * bit_depth + 7) // 8)) if channels else -1
        if len(raw) != expected:
            errors.append("PNG_SCANLINE_LENGTH_INVALID")
    except zlib.error:
        errors.append("PNG_IDAT_DECOMPRESSION_FAILED")
    return {
        "valid": not errors, "width": width, "height": height,
        "bit_depth": bit_depth, "color_type": color_type, "chunks": chunks,
        "errors": errors,
    }


def flatten_outliner(nodes: list[Any]) -> tuple[set[str], list[str], list[str]]:
    groups: set[str] = set()
    refs: list[str] = []
    problems: list[str] = []

    def visit(node: Any) -> None:
        if isinstance(node, str):
            refs.append(node)
            return
        if not isinstance(node, dict):
            problems.append("OUTLINER_NODE_INVALID")
            return
        uuid = node.get("uuid")
        if not isinstance(uuid, str):
            problems.append("OUTLINER_GROUP_UUID_MISSING")
        elif uuid in groups:
            problems.append("OUTLINER_GROUP_UUID_DUPLICATE")
        else:
            groups.add(uuid)
        for child in node.get("children", []):
            visit(child)

    for item in nodes:
        visit(item)
    return groups, refs, problems


def inspect_bbmodel(path: Path) -> dict[str, Any]:
    try:
        data = load_json(path)
    except Exception as exc:
        return {"valid": False, "errors": [f"BBMODEL_JSON_INVALID:{type(exc).__name__}"]}
    errors: list[str] = []
    elements = data.get("elements", [])
    uuids = [e.get("uuid") for e in elements if isinstance(e, dict)]
    if len(uuids) != len(set(uuids)):
        errors.append("ELEMENT_UUID_DUPLICATE")
    groups, refs, outline_errors = flatten_outliner(data.get("outliner", []))
    errors.extend(outline_errors)
    missing_refs = sorted(set(refs) - set(uuids))
    orphan_elements = sorted(set(uuids) - set(refs))
    if missing_refs:
        errors.append("OUTLINER_ELEMENT_REFERENCE_MISSING")
    if orphan_elements:
        errors.append("OUTLINER_ELEMENT_ORPHAN")
    locator_names = sorted(
        e.get("name") for e in elements
        if isinstance(e, dict) and e.get("type") == "locator" and isinstance(e.get("name"), str)
    )
    face_texture_errors = 0
    for element in elements:
        if not isinstance(element, dict) or element.get("type", "cube") != "cube":
            continue
        for face in element.get("faces", {}).values():
            if isinstance(face, dict) and face.get("texture") is None:
                face_texture_errors += 1
    if face_texture_errors:
        errors.append("FACE_TEXTURE_BINDING_MISSING")
    animation_names = sorted(
        a.get("name") for a in data.get("animations", [])
        if isinstance(a, dict) and isinstance(a.get("name"), str)
    )
    texture_metadata = []
    for texture in data.get("textures", []):
        source = texture.get("source", "") if isinstance(texture, dict) else ""
        embedded_sha = None
        if isinstance(source, str) and source.startswith("data:image/png;base64,"):
            try:
                embedded_sha = hashlib.sha256(base64.b64decode(source.split(",", 1)[1])).hexdigest()
            except (ValueError, binascii.Error):
                errors.append("EMBEDDED_TEXTURE_DATA_INVALID")
        texture_metadata.append({
            "name": texture.get("name"), "path": texture.get("path"),
            "relative_path": texture.get("relative_path"),
            "width": texture.get("width"), "height": texture.get("height"),
            "embedded_png_sha256": embedded_sha,
        })
    return {
        "valid": not errors,
        "errors": sorted(set(errors)),
        "model_format": data.get("meta", {}).get("model_format"),
        "model_identifier": data.get("model_identifier"),
        "resolution": data.get("resolution"),
        "element_count": len(elements),
        "cube_count": sum(1 for e in elements if isinstance(e, dict) and e.get("type", "cube") == "cube"),
        "group_count": len(groups),
        "locator_names": locator_names,
        "animation_names": animation_names,
        "texture_entries": len(data.get("textures", [])),
        "texture_metadata": texture_metadata,
        "missing_outliner_refs": missing_refs,
        "orphan_elements": orphan_elements,
    }


def inspect_geometry(path: Path) -> dict[str, Any]:
    try:
        data = load_json(path)
        geos = data.get("minecraft:geometry", [])
        if len(geos) != 1:
            return {"valid": False, "errors": ["GEOMETRY_RECORD_COUNT_NOT_ONE"]}
        geo = geos[0]
        bones = geo.get("bones", [])
        names = [b.get("name") for b in bones]
        errors: list[str] = []
        if len(names) != len(set(names)):
            errors.append("GEOMETRY_BONE_DUPLICATE")
        for bone in bones:
            if bone.get("parent") and bone["parent"] not in names:
                errors.append("GEOMETRY_PARENT_MISSING")
        return {
            "valid": not errors, "errors": sorted(set(errors)),
            "format_version": data.get("format_version"),
            "identifier": geo.get("description", {}).get("identifier"),
            "texture_width": geo.get("description", {}).get("texture_width"),
            "texture_height": geo.get("description", {}).get("texture_height"),
            "bone_count": len(bones),
            "cube_count": sum(len(b.get("cubes", [])) for b in bones),
            "locator_names": sorted({k for b in bones for k in b.get("locators", {})}),
        }
    except Exception as exc:
        return {"valid": False, "errors": [f"GEOMETRY_JSON_INVALID:{type(exc).__name__}"]}


def inspect_animation(path: Path) -> dict[str, Any]:
    try:
        data = load_json(path)
        animations = data.get("animations", {})
        return {
            "valid": isinstance(animations, dict),
            "errors": [] if isinstance(animations, dict) else ["ANIMATION_MAP_INVALID"],
            "format_version": data.get("format_version"),
            "animation_names": sorted(animations) if isinstance(animations, dict) else [],
        }
    except Exception as exc:
        return {"valid": False, "errors": [f"ANIMATION_JSON_INVALID:{type(exc).__name__}"]}


def expected_ids(contract: dict[str, Any], key: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for category, values in contract["packets"][key].items():
        if category not in CATEGORY_DIRS or not isinstance(values, list):
            continue
        for row in values:
            result[row["id"] if isinstance(row, dict) else row] = category
    return result


def resolution_from_brief(value: Any) -> tuple[int, int] | None:
    match = re.fullmatch(r"\s*(\d+)\s*[x×]\s*(\d+)\s*", str(value or ""))
    return (int(match.group(1)), int(match.group(2))) if match else None


def canonical_dependency(value: str) -> str:
    value = re.sub(r"\([^)]*\)", "", value).strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def audit_asset(
    packet_id: str, asset_id: str, category: str, packet_root: Path,
    all_ids: set[str], authority_root: Path, packet_namespace: str,
) -> dict[str, Any]:
    source = packet_root / "assets" / "editable" / f"{asset_id}.bbmodel"
    texture = packet_root / "assets" / "editable" / f"{asset_id}.png"
    brief_path = packet_root / "assets" / "briefs" / f"{asset_id}.json"
    geometry_path = packet_root / "assets" / "export" / "models" / f"{asset_id}.geo.json"
    animation_path = packet_root / "assets" / "export" / "animations" / f"{asset_id}.animation.json"
    export_texture = packet_root / "assets" / "export" / "textures" / f"{asset_id}.png"
    category_root = packet_root / CATEGORY_DIRS[category]
    mirror_paths = {
        "bbmodel": category_root / f"{asset_id}.bbmodel",
        "png": category_root / f"{asset_id}.png",
        "brief": category_root / f"{asset_id}.brief.json",
    }
    canonical_paths = {
        "bbmodel": source, "png": texture, "brief": brief_path,
        "geometry": geometry_path, "animation": animation_path,
        "export_texture": export_texture,
    }
    missing = sorted(k for k, p in canonical_paths.items() if not p.is_file())
    brief = load_json(brief_path) if brief_path.is_file() else {}
    bb = inspect_bbmodel(source) if source.is_file() else {"valid": False, "errors": ["MISSING"]}
    png = parse_png(texture) if texture.is_file() else {"valid": False, "errors": ["MISSING"]}
    geo = inspect_geometry(geometry_path) if geometry_path.is_file() else {"valid": False, "errors": ["MISSING"]}
    anim = inspect_animation(animation_path) if animation_path.is_file() else {"valid": False, "errors": ["MISSING"]}
    mirror = {}
    for kind, path in mirror_paths.items():
        canonical = {"bbmodel": source, "png": texture, "brief": brief_path}[kind]
        mirror[kind] = {
            "path": rel(path, authority_root), "present": path.is_file(),
            "hash_match": path.is_file() and canonical.is_file() and sha256(path) == sha256(canonical),
        }
    brief_locators = sorted(brief.get("locators", []))
    native_locator_gap = sorted(set(brief_locators) - set(bb.get("locator_names", [])))
    export_locator_gap = sorted(set(brief_locators) - set(geo.get("locator_names", [])))
    brief_clips = sorted(brief.get("animations", []))
    exported_suffixes = {name.rsplit(".", 1)[-1] for name in anim.get("animation_names", [])}
    animation_gap = sorted(set(brief_clips) - exported_suffixes)
    declared_resolution = resolution_from_brief(brief.get("texture_resolution"))
    actual_resolution = (png.get("width"), png.get("height")) if png.get("width") else None
    dependencies = []
    for raw in str(brief.get("related_assets", "")).split(","):
        dep = canonical_dependency(raw)
        if dep:
            embedded = sorted(asset for asset in all_ids if re.search(rf"(?:^|_){re.escape(asset)}(?:_|$)", dep))
            dependencies.append({
                "raw": raw.strip(), "canonicalized": dep,
                "resolved_warehouse_ids": embedded,
                "classification": "EXACT_WAREHOUSE_ID" if dep in all_ids else (
                    "PROSE_WITH_BOUND_WAREHOUSE_IDS" if embedded else "NON_CANONICAL_PROSE_UNBOUND"
                ),
            })
    issues: list[str] = []
    if missing:
        issues.append("CANONICAL_PATH_MISSING")
    if not all(m["present"] for m in mirror.values()):
        issues.append("CATEGORY_MIRROR_MISSING")
    if not all(m["hash_match"] for m in mirror.values() if m["present"]):
        issues.append("CATEGORY_MIRROR_HASH_MISMATCH")
    if any(not x.get("valid") for x in (bb, png, geo, anim)):
        issues.append("STATIC_FORMAT_INVALID")
    expected_old_identifier = f"geometry.{packet_namespace}.{asset_id}"
    identifiers = [brief.get("model_identifier"), bb.get("model_identifier"), geo.get("identifier")]
    if any(value != expected_old_identifier for value in identifiers):
        issues.append("PACKET_IDENTIFIER_INCONSISTENT")
    if packet_namespace != "aionbound":
        issues.append("RUNTIME_NAMESPACE_NORMALIZATION_REQUIRED")
    if native_locator_gap:
        issues.append("DECLARED_LOCATORS_ABSENT_FROM_NATIVE_EDITABLE")
    if export_locator_gap:
        issues.append("DECLARED_LOCATORS_ABSENT_FROM_STATIC_EXPORT")
    if animation_gap:
        issues.append("DECLARED_ANIMATION_COVERAGE_ABSENT")
    if declared_resolution and declared_resolution != actual_resolution:
        issues.append("BRIEF_TEXTURE_RESOLUTION_MISMATCH")
    if brief.get("editable") != f"assets/editable/{asset_id}.bbmodel":
        issues.append("BRIEF_EDITABLE_PATH_MISMATCH")
    if brief.get("cube_count") != bb.get("cube_count") or brief.get("cube_count") != geo.get("cube_count"):
        issues.append("BRIEF_CUBE_COUNT_MISMATCH")
    if brief.get("bone_count") != bb.get("group_count") or brief.get("bone_count") != geo.get("bone_count"):
        issues.append("BRIEF_BONE_COUNT_MISMATCH")
    if any(Path(str(t.get("path", ""))).is_absolute() for t in bb.get("texture_metadata", [])):
        issues.append("EDITABLE_ABSOLUTE_TEXTURE_PATH_REQUIRES_NORMALIZATION")
    if texture.is_file() and any(
        t.get("embedded_png_sha256") and t["embedded_png_sha256"] != sha256(texture)
        for t in bb.get("texture_metadata", [])
    ):
        issues.append("EDITABLE_EMBEDDED_TEXTURE_HASH_MISMATCH")
    if export_texture.is_file() and texture.is_file() and sha256(export_texture) != sha256(texture):
        issues.append("EXPORTED_TEXTURE_HASH_MISMATCH")
    if bb.get("cube_count") != geo.get("cube_count"):
        issues.append("EDITABLE_EXPORT_CUBE_COUNT_MISMATCH")
    if any(d["classification"] == "NON_CANONICAL_PROSE_UNBOUND" for d in dependencies):
        issues.append("RELATED_ASSET_PROSE_REQUIRES_ENGINEERING_BINDING")
    if native_locator_gap:
        native_risk = (
            "NATIVE_REPAIR_REQUIRED"
            if category in {"creatures", "weapons", "armor", "tools", "accessories", "trophies"}
            else "NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE"
        )
    elif category in {"creatures", "weapons", "armor", "tools", "accessories", "trophies"}:
        native_risk = "NATIVE_ROUNDTRIP_MANDATORY_OR_REPRESENTATIVE_CLASS_GATE"
    else:
        native_risk = "REPRESENTATIVE_NATIVE_GATE_OR_DOCUMENTED_NOT_APPLICABLE"
    return {
        "packet_id": packet_id, "warehouse_id": asset_id, "category": category,
        "runtime_id": f"aionbound:{asset_id}",
        "canonical": {
            key: {"path": rel(path, authority_root), "sha256": sha256(path) if path.is_file() else None}
            for key, path in canonical_paths.items()
        },
        "category_mirror": mirror,
        "brief": {
            "tier": brief.get("tier"), "profile": brief.get("profile"),
            "model_identifier": brief.get("model_identifier"),
            "declared_locators": brief_locators, "declared_animations": brief_clips,
            "declared_texture_resolution": list(declared_resolution) if declared_resolution else None,
            "dependencies": dependencies,
        },
        "static": {"bbmodel": bb, "png": png, "geometry": geo, "animation": anim},
        "normalization": {
            "source_namespace": packet_namespace, "shipping_namespace": "aionbound",
            "shipping_geometry_identifier": f"geometry.aionbound.{asset_id}",
            "native_locator_gap": native_locator_gap,
            "static_export_locator_gap": export_locator_gap,
            "animation_gap": animation_gap,
            "native_roundtrip_risk": native_risk,
        },
        "status": "STATIC_READY_FOR_NORMALIZATION" if not issues else "NORMALIZATION_OR_REPAIR_REQUIRED",
        "issues": sorted(set(issues)),
        "proof_boundary": {
            "static_inventory": "RUN", "native_blockbench_roundtrip": "NOT_RUN",
            "native_export_equivalence": "NOT_RUN", "bedrock_client": "NOT_RUN",
            "physical_ps4": "NOT_RUN",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Wave 1 Packet Normalization Inventory", "",
        f"Status: **{report['status']}**", "",
        "This is a deterministic static inventory. It does not prove a native Blockbench round-trip, native-export equivalence, Bedrock rendering, gameplay behavior, or physical-console readiness.", "",
        "## Authority binding", "",
        f"- Creative contract SHA-256: `{report['authority']['creative_contract_sha256']}`",
        f"- Engineering decision ledger SHA-256: `{report['authority']['decision_ledger_sha256']}`",
        "- Canonical editable source: each sprint's `assets/editable/<warehouse_id>.bbmodel` and sibling PNG.",
        "- Category copies are mirrors only and are compared byte-for-byte.",
        "- Shipping namespace decision: `aionbound:<warehouse_id>`; packet namespace identifiers require normalization in successor production files.", "",
        "## Result", "",
        f"- Warehouse IDs bound: **{summary['warehouse_ids_bound']} / 250**",
        f"- Canonical file sets complete: **{summary['canonical_file_sets_complete']} / 250**",
        f"- Category mirrors exact: **{summary['category_mirrors_exact']} / 250**",
        f"- Static format sets valid: **{summary['static_format_sets_valid']} / 250**",
        f"- Assets requiring normalization or repair: **{summary['normalization_or_repair_required']}**",
        f"- Native Blockbench/editor proof: **NOT RUN**", "",
        "## Packet rollup", "",
        "| Packet | IDs | Canonical complete | Mirrors exact | Static valid | Repair/normalize |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for packet in report["packets"]:
        lines.append(
            f"| {packet['id']} {packet['name']} | {packet['id_count']} | {packet['canonical_complete']} | "
            f"{packet['mirrors_exact']} | {packet['static_valid']} | {packet['repair_or_normalize']} |"
        )
    lines += ["", "## Evidence-derived findings", ""]
    for issue, count in report["issue_counts"].items():
        lines.append(f"- `{issue}`: {count}")
    lines += [
        "", "The two highest-risk findings are contractual rather than cosmetic:", "",
        "- Briefs declare locator names that are absent as native locator elements in editable projects. The static geometry exports contain those locators, which means they were injected outside the native editable hierarchy; native reopen/export drops them. Locator-dependent or hero shipping use therefore requires native repair. Ordinary native-JSON/block-assembly implementations may instead document Blockbench as `NOT_APPLICABLE` under the decision ledger.",
        "- Briefs declare role-specific animation sets, while exported animation files expose only the actually inventoried clips. Missing declared clips must be implemented or explicitly removed from the implementation contract.",
        "", "## Complete warehouse binding", "",
        "| Packet | Category | Warehouse ID | Runtime ID | Static status | Native risk |",
        "|---|---|---|---|---|---|",
    ]
    for asset in report["assets"]:
        lines.append(
            f"| {asset['packet_id']} | {asset['category']} | `{asset['warehouse_id']}` | `{asset['runtime_id']}` | "
            f"{asset['status']} | {asset['normalization']['native_roundtrip_risk']} |"
        )
    lines += [
        "", "## Proof boundary", "",
        "Static JSON/PNG/path/hash inspection was run. Blockbench GUI open/save/reopen, native codec export, Creator Tools, Stable BDS, Bedrock client, controller, multiplayer, Realm, split-screen, and physical PS4 gates were not run by this lane.", "",
        "Regenerate with:", "",
        "```sh", "python3 engineering/normalization/tools/inventory_packets.py", "```", "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--studio-prep", type=Path, default=Path("/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/studio-prep"))
    parser.add_argument("--decision-ledger", type=Path, default=Path("engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("engineering/normalization"))
    args = parser.parse_args()
    studio = args.studio_prep.resolve()
    contract_path = studio / "creative" / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json"
    contract = load_json(contract_path)
    decision_path = args.decision_ledger.resolve()
    authority_root = studio.parent.parent
    expected_by_packet = {pid: expected_ids(contract, key) for pid, (key, _, _) in PACKETS.items()}
    all_ids = {asset_id for ids in expected_by_packet.values() for asset_id in ids}
    assets: list[dict[str, Any]] = []
    packet_reports = []
    for pid, (key, dirname, namespace) in PACKETS.items():
        root = studio / "sprints" / dirname
        packet_assets = [
            audit_asset(pid, asset_id, category, root, all_ids, authority_root, namespace)
            for asset_id, category in sorted(expected_by_packet[pid].items())
        ]
        assets.extend(packet_assets)
        packet_reports.append({
            "id": pid, "name": key, "path": rel(root, authority_root), "namespace_intent": namespace,
            "id_count": len(packet_assets),
            "canonical_complete": sum(all(v["sha256"] for v in a["canonical"].values()) for a in packet_assets),
            "mirrors_exact": sum(all(v["present"] and v["hash_match"] for v in a["category_mirror"].values()) for a in packet_assets),
            "static_valid": sum(all(a["static"][k]["valid"] for k in ("bbmodel", "png", "geometry", "animation")) for a in packet_assets),
            "repair_or_normalize": sum(a["status"] != "STATIC_READY_FOR_NORMALIZATION" for a in packet_assets),
        })
    issue_counts = Counter(issue for asset in assets for issue in asset["issues"])
    summary = {
        "warehouse_ids_bound": len(assets),
        "warehouse_ids_unique": len({a["warehouse_id"] for a in assets}),
        "canonical_file_sets_complete": sum(all(v["sha256"] for v in a["canonical"].values()) for a in assets),
        "category_mirrors_exact": sum(all(v["present"] and v["hash_match"] for v in a["category_mirror"].values()) for a in assets),
        "static_format_sets_valid": sum(all(a["static"][k]["valid"] for k in ("bbmodel", "png", "geometry", "animation")) for a in assets),
        "normalization_or_repair_required": sum(a["status"] != "STATIC_READY_FOR_NORMALIZATION" for a in assets),
    }
    status = "STATIC_INVENTORY_COMPLETE_NORMALIZATION_AND_NATIVE_REPAIR_REQUIRED"
    if len(assets) != 250 or summary["warehouse_ids_unique"] != 250:
        status = "STATIC_INVENTORY_FAILED_WAREHOUSE_BINDING"
    report = {
        "schema": "aionbound.wave1.packet_normalization_inventory.v1",
        "status": status,
        "scope": "packets_001_002_003_004_006_static_only",
        "authority": {
            "creative_contract_path": rel(contract_path, authority_root),
            "creative_contract_sha256": sha256(contract_path),
            "decision_ledger_path": args.decision_ledger.as_posix(),
            "decision_ledger_sha256": sha256(decision_path),
            "shipping_namespace": "aionbound",
        },
        "summary": summary,
        "issue_counts": dict(sorted(issue_counts.items())),
        "packets": packet_reports,
        "assets": assets,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "PACKET_NORMALIZATION_INVENTORY.json"
    md_path = args.output_dir / "PACKET_NORMALIZATION_INVENTORY.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": status, "summary": summary, "issue_counts": report["issue_counts"]}, indent=2, sort_keys=True))
    return 0 if len(assets) == 250 and summary["warehouse_ids_unique"] == 250 else 1


if __name__ == "__main__":
    raise SystemExit(main())
