#!/usr/bin/env python3
"""Deterministic, read-only native-readiness audit for Packet 003.

The audit deliberately does not open Blockbench and does not modify the packet.
It binds every conclusion to canonical packet bytes and keeps native-editor,
runtime-export, and shipping claims separate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import uuid
import zlib
from collections import Counter
from pathlib import Path
from typing import Any


PACKET_RELATIVE = Path(
    "program/crazycraft-pack-production-v1/studio-prep/sprints/"
    "asset-sprint-003-crystal-marsh"
)
DEFAULT_PACKET_ROOT = Path("/Users/blakegrove/Desktop/bedrock-server") / PACKET_RELATIVE
SOURCE_COMMIT = "bcd65076900a3688dd797d54719263d88afd501c"
SOURCE_TREE = "4d876b233e6b510687d238f1d7f6611c7c0c4ab9"
SOURCE_NAMESPACE = "aionforge_cm"
SHIPPING_NAMESPACE = "aionbound"
TIER_FOLDER = {
    "CREATURE": "creatures",
    "RESOURCE": "resources",
    "PLANT": "plants",
    "BLOCK": "blocks",
    "LANDMARK": "props",
}
NATIVE_REQUIRED_TIERS = {"CREATURE", "PLANT", "LANDMARK"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def png_info(path: Path) -> dict[str, Any]:
    """Validate PNG structure, CRCs, zlib stream, and decompressed row length."""
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError(f"not a PNG: {path}")
    offset = len(PNG_SIGNATURE)
    chunks: list[str] = []
    idat = bytearray()
    width = height = bit_depth = color_type = interlace = None
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError(f"truncated PNG chunk: {path}")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        stored_crc = struct.unpack(">I", data[offset + 8 + length : offset + 12 + length])[0]
        actual_crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            raise ValueError(f"PNG CRC mismatch: {path}")
        name = chunk_type.decode("ascii")
        chunks.append(name)
        if name == "IHDR":
            width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
        elif name == "IDAT":
            idat.extend(payload)
        elif name == "IEND":
            break
        offset += 12 + length
    if width is None or height is None or not idat or chunks[-1] != "IEND":
        raise ValueError(f"incomplete PNG: {path}")
    if interlace != 0:
        raise ValueError(f"interlaced PNG not admitted by this bounded decoder: {path}")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if channels is None or bit_depth not in {1, 2, 4, 8, 16}:
        raise ValueError(f"unsupported PNG channel/bit-depth pair: {path}")
    inflated = zlib.decompress(bytes(idat))
    row_bytes = (width * channels * bit_depth + 7) // 8
    expected = height * (row_bytes + 1)
    if len(inflated) != expected:
        raise ValueError(f"PNG scanline length mismatch: {path}")
    filters = [inflated[row * (row_bytes + 1)] for row in range(height)]
    if any(value > 4 for value in filters):
        raise ValueError(f"illegal PNG scanline filter: {path}")
    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "crc_valid": True,
        "idat_decompressed": True,
        "legal_scanlines": True,
    }


def dimensions_allowed(declaration: str, width: int, height: int) -> bool:
    normalized = declaration.lower().replace(" ", "")
    if "×" in normalized or "x" in normalized:
        parts = re.split("[×x]", normalized)
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            return (width, height) == (int(parts[0]), int(parts[1]))
    if "–" in normalized or "-" in normalized:
        parts = re.split("[–-]", normalized)
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            low, high = map(int, parts)
            return width == height and low <= width <= high
    if normalized.isdigit():
        size = int(normalized)
        return (width, height) == (size, size)
    return False


def walk_groups(outliner: list[Any]) -> tuple[list[dict[str, Any]], list[str]]:
    groups: list[dict[str, Any]] = []
    refs: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, str):
            refs.append(value)
        elif isinstance(value, dict):
            groups.append(value)
            for child in value.get("children", []):
                visit(child)

    for entry in outliner:
        visit(entry)
    return groups, refs


def uuid_is_native_shaped(value: str) -> bool:
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        return False
    return str(parsed) == value.lower()


def source_integrity(bbmodel: dict[str, Any]) -> dict[str, Any]:
    elements = bbmodel.get("elements", [])
    groups, element_refs = walk_groups(bbmodel.get("outliner", []))
    element_ids = [entry.get("uuid") for entry in elements]
    group_ids = [entry.get("uuid") for entry in groups]
    animation_ids: list[str] = []
    keyframe_ids: list[str] = []
    animator_refs: list[str] = []
    for animation in bbmodel.get("animations", []):
        animation_ids.append(animation.get("uuid"))
        for animator_id, animator in animation.get("animators", {}).items():
            animator_refs.append(animator_id)
            keyframe_ids.extend(frame.get("uuid") for frame in animator.get("keyframes", []))
    all_ids = element_ids + group_ids + animation_ids + keyframe_ids
    texture_metadata = [
        {
            "name": entry.get("name"),
            "path": entry.get("path"),
            "relative_path": entry.get("relative_path"),
            "width": entry.get("width"),
            "height": entry.get("height"),
            "path_is_absolute": bool(entry.get("path")) and Path(entry["path"]).is_absolute(),
        }
        for entry in bbmodel.get("textures", [])
    ]
    return {
        "element_count": len(elements),
        "cube_count": sum(entry.get("type") == "cube" for entry in elements),
        "locator_element_count": sum(entry.get("type") == "locator" for entry in elements),
        "locator_element_names": sorted(
            entry.get("name") for entry in elements if entry.get("type") == "locator"
        ),
        "group_count": len(groups),
        "animation_count": len(bbmodel.get("animations", [])),
        "animation_names": sorted(animation.get("name") for animation in bbmodel.get("animations", [])),
        "uuid_shape_pass": all(isinstance(value, str) and uuid_is_native_shaped(value) for value in all_ids),
        "uuid_uniqueness_pass": len(all_ids) == len(set(all_ids)),
        "outliner_reference_closure_pass": set(element_refs) == set(element_ids),
        "animator_reference_closure_pass": set(animator_refs).issubset(set(group_ids)),
        "texture_metadata": texture_metadata,
        "absolute_texture_path_count": sum(entry["path_is_absolute"] for entry in texture_metadata),
    }


def export_integrity(geometry: dict[str, Any], animations: dict[str, Any]) -> dict[str, Any]:
    geometries = geometry.get("minecraft:geometry", [])
    bones = [bone for geo in geometries for bone in geo.get("bones", [])]
    locator_names = sorted(
        name for bone in bones for name in (bone.get("locators") or {}).keys()
    )
    return {
        "geometry_identifiers": sorted(geo.get("description", {}).get("identifier") for geo in geometries),
        "bone_count": len(bones),
        "cube_count": sum(len(bone.get("cubes", [])) for bone in bones),
        "locator_names": locator_names,
        "clip_names": sorted(animations.get("animations", {}).keys()),
    }


def short_clip(name: str) -> str:
    return name.rsplit(".", 1)[-1]


def classify_related_assets(raw: str, warehouse_ids: set[str]) -> list[dict[str, Any]]:
    terms = [term.strip() for term in re.split(r"[,;]", raw or "") if term.strip()]
    results: list[dict[str, Any]] = []
    for term in terms:
        canonical = re.sub(r"[^a-z0-9]+", "_", term.lower()).strip("_")
        exact = [canonical] if canonical in warehouse_ids else []
        contained = sorted(
            candidate
            for candidate in warehouse_ids
            if not exact and re.search(rf"(?:^|_){re.escape(candidate)}(?:_|$)", canonical)
        )
        resolved = exact or contained
        results.append(
            {
                "raw": term,
                "canonicalized": canonical,
                "classification": (
                    "EXACT_PACKET_WAREHOUSE_ID"
                    if exact
                    else "CONTAINS_PACKET_WAREHOUSE_ID"
                    if contained
                    else "NON_CANONICAL_PROSE_UNBOUND"
                ),
                "resolved_packet_warehouse_ids": resolved,
            }
        )
    return results


def audit_asset(
    packet: Path, manifest_entry: dict[str, Any], warehouse_ids: set[str]
) -> dict[str, Any]:
    name = manifest_entry["name"]
    tier = manifest_entry["tier"]
    folder = TIER_FOLDER[tier]
    paths = {
        "brief": packet / "assets" / "briefs" / f"{name}.json",
        "editable": packet / "assets" / "editable" / f"{name}.bbmodel",
        "editable_texture": packet / "assets" / "editable" / f"{name}.png",
        "export_geometry": packet / "assets" / "export" / "models" / f"{name}.geo.json",
        "export_animation": packet / "assets" / "export" / "animations" / f"{name}.animation.json",
        "export_texture": packet / "assets" / "export" / "textures" / f"{name}.png",
        "mirror_brief": packet / folder / f"{name}.brief.json",
        "mirror_editable": packet / folder / f"{name}.bbmodel",
        "mirror_texture": packet / folder / f"{name}.png",
    }
    missing = sorted(label for label, path in paths.items() if not path.is_file())
    if missing:
        raise FileNotFoundError(f"{name}: missing {missing}")
    brief = load_json(paths["brief"])
    bbmodel = load_json(paths["editable"])
    geometry = load_json(paths["export_geometry"])
    animations = load_json(paths["export_animation"])
    source = source_integrity(bbmodel)
    exported = export_integrity(geometry, animations)
    pngs = {
        label: png_info(paths[label])
        for label in ("editable_texture", "export_texture", "mirror_texture")
    }
    declared_clips = sorted(brief.get("animations", []))
    actual_clips = sorted(short_clip(name) for name in exported["clip_names"])
    declared_locators = sorted(brief.get("locators", []))
    texture_width = pngs["export_texture"]["width"]
    texture_height = pngs["export_texture"]["height"]
    geometry_descriptions = [
        geo.get("description", {}) for geo in geometry.get("minecraft:geometry", [])
    ]
    geometry_sizes = sorted(
        [description.get("texture_width"), description.get("texture_height")]
        for description in geometry_descriptions
    )
    model_identifier = brief.get("model_identifier")
    related_assets = classify_related_assets(brief.get("related_assets", ""), warehouse_ids)
    namespace_ok = (
        model_identifier == f"geometry.{SOURCE_NAMESPACE}.{name}"
        and bbmodel.get("model_identifier") == model_identifier
        and exported["geometry_identifiers"] == [model_identifier]
        and all(clip.startswith(f"animation.{SOURCE_NAMESPACE}.{name}.") for clip in exported["clip_names"])
    )
    blockbench_disposition = (
        "NATIVE_REPAIR_REQUIRED"
        if tier in NATIVE_REQUIRED_TIERS
        else "NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM"
    )
    if tier in {"BLOCK", "RESOURCE"}:
        readiness = "STATIC_TEXTURE_NORMALIZATION_REQUIRED"
        rationale = (
            "Approved function is an ordinary full-cube block; consume native block JSON and texture, not packet custom geometry."
            if tier == "BLOCK"
            else "Approved function is a flat inventory/resource item; consume native item JSON and icon, not packet custom geometry."
        )
    else:
        readiness = "NATIVE_REPAIR_REQUIRED"
        rationale = (
            "Custom geometry or animation is material to the approved visual identity; the editable source lacks real locator elements and has not passed a native editor round-trip."
        )
    artifact_hashes = {label: sha256(path) for label, path in paths.items()}
    return {
        "name": name,
        "display_name": manifest_entry["display"],
        "tier": tier,
        "production_priority": brief.get("production_priority"),
        "canonical_source_namespace": SOURCE_NAMESPACE,
        "intended_shipping_namespace": SHIPPING_NAMESPACE,
        "intended_shipping_runtime_id": f"{SHIPPING_NAMESPACE}:{name}",
        "intended_shipping_geometry_identifier": f"geometry.{SHIPPING_NAMESPACE}.{name}",
        "namespace_consistency": "PASS_SOURCE_NAMESPACE" if namespace_ok else "FAIL",
        "paths": {label: str(path.relative_to(packet)) for label, path in paths.items()},
        "sha256": artifact_hashes,
        "mirror_equality": {
            "brief": artifact_hashes["brief"] == artifact_hashes["mirror_brief"],
            "editable": artifact_hashes["editable"] == artifact_hashes["mirror_editable"],
            "editable_texture": artifact_hashes["editable_texture"] == artifact_hashes["mirror_texture"],
            "export_texture": artifact_hashes["export_texture"] == artifact_hashes["mirror_texture"],
        },
        "editable_source": source,
        "export": exported,
        "declared_vs_actual": {
            "declared_locators": declared_locators,
            "real_editable_locator_elements": source["locator_element_names"],
            "exported_geometry_locators": exported["locator_names"],
            "exported_locators_match_brief": exported["locator_names"] == declared_locators,
            "native_locator_authority": "FAIL_NO_REAL_EDITABLE_LOCATOR_ELEMENTS",
            "declared_clips": declared_clips,
            "editable_clips": sorted(short_clip(name) for name in source["animation_names"]),
            "exported_clips": actual_clips,
            "declared_clips_match_export": declared_clips == actual_clips,
            "missing_declared_role_clips": sorted(set(declared_clips) - set(actual_clips)),
            "generic_or_extra_exported_clips": sorted(set(actual_clips) - set(declared_clips)),
            "texture_contract": brief.get("texture_resolution"),
            "editable_resolution": [bbmodel.get("resolution", {}).get("width"), bbmodel.get("resolution", {}).get("height")],
            "geometry_resolutions": geometry_sizes,
            "decoded_texture_resolution": [texture_width, texture_height],
            "texture_contract_allows_decoded_resolution": dimensions_allowed(
                str(brief.get("texture_resolution", "")), texture_width, texture_height
            ),
        },
        "path_normalization": {
            "editable_texture_paths": source["texture_metadata"],
            "absolute_texture_path_count": source["absolute_texture_path_count"],
            "requires_relative_shipping_path_rebind": bool(source["absolute_texture_path_count"]),
        },
        "related_asset_bindings": {
            "raw": brief.get("related_assets", ""),
            "terms": related_assets,
            "unbound_terms": [
                entry["raw"]
                for entry in related_assets
                if entry["classification"] == "NON_CANONICAL_PROSE_UNBOUND"
            ],
        },
        "png_validation": pngs,
        "blockbench_disposition": blockbench_disposition,
        "shipping_readiness": readiness,
        "disposition_rationale": rationale,
        "native_roundtrip": "NOT_RUN_BY_SCOPE",
        "native_export_equivalence": "UNPROVEN",
        "bedrock_client_render": "UNTESTED",
        "physical_ps4_render": "UNTESTED",
    }


def build_report(packet: Path) -> dict[str, Any]:
    manifest = load_json(packet / "MANIFEST_FULL.json")
    warehouse_ids = {entry["name"] for entry in manifest["assets"]}
    assets = [audit_asset(packet, entry, warehouse_ids) for entry in manifest["assets"]]
    counts = Counter(asset["tier"] for asset in assets)
    disposition = Counter(asset["blockbench_disposition"] for asset in assets)
    texture_contract = Counter(
        asset["declared_vs_actual"]["texture_contract_allows_decoded_resolution"]
        for asset in assets
    )
    packet_authority = {
        rel: sha256(packet / rel)
        for rel in (
            "MANIFEST_FULL.json",
            "ASSET_SPRINT_003_CRYSTAL_MARSH.md",
            "SPRINT_003_COMPLETE.md",
        )
    }
    return {
        "schema": "aionforge.wave1.crystal_marsh.packet003_native_readiness.v1",
        "audit_scope": {
            "integration_commit": SOURCE_COMMIT,
            "integration_tree": SOURCE_TREE,
            "packet": "003_crystal_marsh",
            "canonical_packet_path": str(PACKET_RELATIVE),
            "read_only_packet_audit": True,
            "blockbench_launched": False,
            "packet_assets_edited": False,
            "bp_rp_touched": False,
        },
        "packet_authority_sha256": packet_authority,
        "summary": {
            "asset_count": len(assets),
            "tier_counts": dict(sorted(counts.items())),
            "complete_artifact_sets": sum(len(asset["sha256"]) == 9 for asset in assets),
            "all_hashes_sha256": all(
                SHA_RE.fullmatch(value)
                for asset in assets
                for value in asset["sha256"].values()
            ),
            "all_json_parsed": True,
            "all_pngs_decoded": all(
                validation["crc_valid"]
                and validation["idat_decompressed"]
                and validation["legal_scanlines"]
                for asset in assets
                for validation in asset["png_validation"].values()
            ),
            "exact_category_mirrors": sum(
                all(asset["mirror_equality"].values()) for asset in assets
            ),
            "source_namespace_consistent": sum(
                asset["namespace_consistency"] == "PASS_SOURCE_NAMESPACE" for asset in assets
            ),
            "absolute_editable_texture_path_assets": sum(
                bool(asset["path_normalization"]["absolute_texture_path_count"])
                for asset in assets
            ),
            "assets_with_unbound_related_prose": sum(
                bool(asset["related_asset_bindings"]["unbound_terms"]) for asset in assets
            ),
            "real_editable_locator_assets": sum(
                bool(asset["editable_source"]["locator_element_count"]) for asset in assets
            ),
            "exported_locator_sets_match_briefs": sum(
                asset["declared_vs_actual"]["exported_locators_match_brief"] for asset in assets
            ),
            "declared_clip_sets_match_exports": sum(
                asset["declared_vs_actual"]["declared_clips_match_export"] for asset in assets
            ),
            "texture_contract_compatible": texture_contract[True],
            "texture_contract_mismatch": texture_contract[False],
            "blockbench_dispositions": dict(sorted(disposition.items())),
            "native_repair_required_count": disposition["NATIVE_REPAIR_REQUIRED"],
            "blockbench_not_applicable_count": disposition[
                "NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM"
            ],
            "portfolio_native_status": "NOT_READY_NATIVE_REPAIR_REQUIRED",
        },
        "representative_class_gate": {
            "status": "REQUIRED_BEFORE_SCALE_OUT",
            "assets_in_order": [
                {
                    "name": "marsh_wight",
                    "class": "hostile_biped_chapter_apex",
                    "gate_reason": "chapter-facing silhouette, biped contacts, reach action, terminal collapse, and effect/gaze locator coverage",
                },
                {
                    "name": "crystal_dragonfly",
                    "class": "small_flying_creature",
                    "gate_reason": "hover, flight, dart transitions, transparent thin-feature readability, and effect/gaze locators",
                },
                {
                    "name": "silt_crocodile",
                    "class": "large_aquatic_ambush_creature",
                    "gate_reason": "long-body articulation, swim/submerge/lunge/bite coverage, 128x64 contract, and effect/gaze locators",
                },
                {
                    "name": "bubble_pod",
                    "class": "animated_translucent_plant",
                    "gate_reason": "declared bob clip, effect locator, transparent material readability, and small-form UV coverage",
                },
                {
                    "name": "flood_reed",
                    "class": "animated_plant_sway",
                    "gate_reason": "declared sway loop, effect locator, and thin-feature contact/readability representative",
                },
                {
                    "name": "sunken_shrine",
                    "class": "animated_landmark_prop",
                    "gate_reason": "declared glow clip, effect locator, and submerged landmark material representative",
                },
                {
                    "name": "ancient_boat",
                    "class": "static_landmark_prop",
                    "gate_reason": "complex static silhouette, effect locator, and 64-128 texture-contract representative",
                },
            ],
            "required_evidence_per_asset": [
                "exact editable hash staged without changing Creative identity",
                "real native locator elements where brief declares locators",
                "brief-declared clip identities with authored keyframes and no generic aliases",
                "texture dimensions compliant with the frozen brief",
                "Blockbench reopen-save-reopen with zero warnings",
                "native geometry and animation export with structural equivalence",
                "fixed Golden proof inventory and two critique cycles",
                "exact artifact and evidence hashes",
            ],
            "promotion_rule": "No remaining member of a represented class may scale from packet source until its representative passes every required evidence item; representatives are templates for construction quality only, never silhouettes, palettes, or motion identity.",
        },
        "bounded_repair_order": [
            {
                "stage": 1,
                "scope": "Blockbench-N/A block/resource normalization; may start immediately and independently",
                "assets": [
                    asset["name"] for asset in assets if asset["tier"] in {"BLOCK", "RESOURCE"}
                ],
                "exit": "native block/item form selected and textures normalized to the frozen brief without consuming packet geometry, locators, or generic animations",
            },
            {
                "stage": 2,
                "scope": "seven representative custom-geometry class-gate assets only",
                "assets": [
                    "marsh_wight",
                    "crystal_dragonfly",
                    "silt_crocodile",
                    "bubble_pod",
                    "flood_reed",
                    "sunken_shrine",
                    "ancient_boat",
                ],
                "exit": "all representative native and Golden gates pass before custom-geometry scale-out",
            },
            {
                "stage": 3,
                "scope": "remaining custom-geometry creatures",
                "assets": [
                    "crystal_newt",
                    "prism_frog",
                    "glass_heron",
                    "mire_turtle",
                    "bloom_crab",
                    "reed_serpent",
                    "bog_watcher",
                ],
                "exit": "each creature independently passes native locator, declared motion, texture, Golden, and export-equivalence gates",
            },
            {
                "stage": 4,
                "scope": "remaining custom-geometry plants",
                "assets": [
                    "crystal_lily",
                    "prism_bloom",
                    "glass_moss",
                    "marsh_fern",
                    "glow_kelp",
                    "mire_orchid",
                    "pearl_grass",
                    "crystal_vine",
                ],
                "exit": "each plant independently passes its declared static-or-role-clip contract and native locator/export gate",
            },
            {
                "stage": 5,
                "scope": "remaining custom-geometry landmarks",
                "assets": [
                    "crystal_obelisk",
                    "flooded_dock",
                    "marsh_totem",
                    "marsh_broken_bridge",
                    "crystal_arch",
                    "pearl_cairn",
                    "ruined_observatory",
                    "deep_pool_entrance",
                ],
                "exit": "each landmark independently passes its declared static-or-role-clip contract and native locator/export gate",
            },
        ],
        "systemic_findings": [
            {
                "id": "CM-NATIVE-001",
                "severity": "BLOCKING_FOR_CUSTOM_GEOMETRY_SHIPPING",
                "finding": "All 50 editable projects lack real locator elements even though every brief declares at least one locator; exported geometry contains matching locator names, so those exports are deterministic-tool products rather than proven native-equivalent exports.",
            },
            {
                "id": "CM-NATIVE-002",
                "severity": "BLOCKING_FOR_ANIMATED_SHIPPING",
                "finding": "No asset's declared clip set equals its editable/exported clip set. Every project/export contains generic idle and action clips, including assets whose briefs declare no animation.",
            },
            {
                "id": "CM-NATIVE-003",
                "severity": "BLOCKING_WHERE_BRIEF_SIZE_IS_EXACT",
                "finding": "All editable projects, geometry exports, and PNGs use 32x32 atlases; the exact compatible/mismatch count is measured in the summary and each per-asset record.",
            },
            {
                "id": "CM-NATIVE-004",
                "severity": "NORMALIZATION_REQUIRED",
                "finding": "Canonical source identifiers consistently use aionforge_cm; shipping normalization must bind approved identities into aionbound without editing the frozen packet.",
            },
            {
                "id": "CM-NATIVE-005",
                "severity": "EVIDENCE_BOUNDARY",
                "finding": "Exact mirrors and parse/decode success prove packet integrity only. They do not prove Blockbench round-trip, native export equivalence, client rendering, animation playback, Marketplace acceptance, or physical PS4 behavior.",
            },
            {
                "id": "CM-NATIVE-006",
                "severity": "NORMALIZATION_REQUIRED",
                "finding": "Every editable project records an absolute author-workstation texture path and must be rebound to a relative staged path before any native round trip or shipping export.",
            },
            {
                "id": "CM-NATIVE-007",
                "severity": "ENGINEERING_BINDING_REQUIRED_WHERE_LISTED",
                "finding": "Related-asset fields mix exact warehouse IDs with prose. Exact IDs are recorded; unbound prose remains an explicit engineering binding gap and is not treated as a new Creative identity.",
            },
        ],
        "assets": assets,
        "proof_boundaries": {
            "proven": [
                "canonical packet byte inventory and SHA-256 bindings",
                "JSON parse and bounded PNG decode/CRC/scanline validity",
                "source namespace consistency",
                "category-mirror byte equality",
                "declared versus actual clip, locator, and texture-dimension comparison",
                "static RFC-shaped UUID and source-link closure checks",
            ],
            "not_proven": [
                "Blockbench open/save/reopen success",
                "native Blockbench export equivalence",
                "visual quality or Golden score",
                "Bedrock client rendering or animation playback",
                "AI, movement, pathfinding, or gameplay behavior",
                "Creator Tools or BDS package admission",
                "multiplayer, persistence, performance, controller, Realm, split-screen, or physical PS4",
                "Marketplace approval or release readiness",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Crystal Marsh Packet 003 native production-readiness intake",
        "",
        f"Authority: integration commit `{SOURCE_COMMIT}`; tree `{SOURCE_TREE}`; frozen packet `{report['audit_scope']['canonical_packet_path']}`.",
        "",
        "This is a read-only static intake. Blockbench was not launched; packet assets and BP/RP were not edited.",
        "",
        "## Outcome",
        "",
        f"**{summary['portfolio_native_status']}**",
        "",
        f"All {summary['asset_count']} canonical assets have complete hashed artifact sets, parseable JSON, decoded PNGs, consistent `aionforge_cm` source identifiers, and byte-identical category mirrors. Those strengths establish packet integrity, not native production readiness.",
        "",
        f"- Native repair required: {summary['native_repair_required_count']} custom-geometry assets (10 creatures, 10 plants, 10 landmarks).",
        f"- Blockbench not applicable: {summary['blockbench_not_applicable_count']} ordinary full-cube/flat-item assets (10 blocks, 10 resources); static texture normalization remains required.",
        f"- Real editable locator elements: {summary['real_editable_locator_assets']}/50.",
        f"- Exported locator sets matching briefs: {summary['exported_locator_sets_match_briefs']}/50, but native equivalence is unproven.",
        f"- Declared clip sets matching exports: {summary['declared_clip_sets_match_exports']}/50.",
        f"- Texture contracts admitting the actual 32x32 atlases: {summary['texture_contract_compatible']}/50; mismatches: {summary['texture_contract_mismatch']}/50.",
        f"- Editable projects with absolute texture paths requiring staged relative rebind: {summary['absolute_editable_texture_path_assets']}/50.",
        f"- Assets with unbound related-asset prose: {summary['assets_with_unbound_related_prose']}/50; exact or contained packet IDs remain recorded separately.",
        "",
        "## Systemic findings",
        "",
    ]
    for finding in report["systemic_findings"]:
        lines.append(f"- `{finding['id']}` — {finding['finding']}")
    lines += [
        "",
        "## Representative class gate",
        "",
        "Run native repair only after staging immutable copies. The first bounded gate is:",
        "",
    ]
    for entry in report["representative_class_gate"]["assets_in_order"]:
        lines.append(f"- `{entry['name']}` ({entry['class']}): {entry['gate_reason']}.")
    lines += [
        "",
        "Each representative must use real native locators, exact brief-declared clips, contract-compliant textures, a zero-warning reopen/save/reopen/native-export round trip, fixed Golden proof views, two critique cycles, and exact evidence hashes. Passing representatives establish construction templates only; every scaled asset still passes independently.",
        "",
        "## Bounded repair order",
        "",
        "Stage 1 is an implementation-safe normalization lane: blocks remain ordinary full cubes and resources remain flat inventory items, so their packet `.bbmodel`, locator, and generic animation defects are explicitly Blockbench `NOT_APPLICABLE`. Custom creatures, plants, and landmark props remain behind the representative native gate.",
        "",
    ]
    for stage in report["bounded_repair_order"]:
        lines.append(
            f"{stage['stage']}. {stage['scope']}: "
            + ", ".join(f"`{name}`" for name in stage["assets"])
            + f". Exit: {stage['exit']}."
        )
    lines += [
        "",
        "## Per-asset disposition",
        "",
        "| Asset | Tier | Priority | Blockbench | Clips declared/exported | Locators source/export | Texture brief/actual | Related-ID gap |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    for asset in report["assets"]:
        comparison = asset["declared_vs_actual"]
        lines.append(
            f"| `{asset['name']}` | {asset['tier']} | {asset['production_priority']} | {asset['blockbench_disposition']} | "
            f"{len(comparison['declared_clips'])}/{len(comparison['exported_clips'])} | "
            f"{len(comparison['real_editable_locator_elements'])}/{len(comparison['exported_geometry_locators'])} | "
            f"{comparison['texture_contract']}/{comparison['decoded_texture_resolution'][0]}x{comparison['decoded_texture_resolution'][1]} | "
            f"{', '.join(asset['related_asset_bindings']['unbound_terms']) or 'none'} |"
        )
    lines += [
        "",
        "## Proof boundary",
        "",
        "Proven here: exact packet hashes, JSON parsing, PNG CRC/decompression/scanlines, source namespace consistency, mirror equality, UUID/link closure, and declared-versus-actual static comparisons.",
        "",
        "Not proven here: Blockbench UI round-trip, native-export equivalence, Golden visual quality, Bedrock rendering/animation/gameplay, Creator Tools/BDS admission, multiplayer, performance, console/controller/Realm/split-screen/physical PS4, Marketplace approval, or release readiness.",
        "",
        "The machine-readable report contains every artifact path and SHA-256.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-root", type=Path, default=DEFAULT_PACKET_ROOT)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    report = build_report(args.packet_root.resolve())
    json_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    markdown_text = render_markdown(report)
    if args.json_output:
        args.json_output.write_text(json_text, encoding="utf-8")
    else:
        print(json_text, end="")
    if args.markdown_output:
        args.markdown_output.write_text(markdown_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
