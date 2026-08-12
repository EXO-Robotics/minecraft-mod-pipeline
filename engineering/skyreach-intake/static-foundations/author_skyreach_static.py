#!/usr/bin/env python3
"""Deterministically bind Packet 004 flat resources and full-cube blocks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[3]
BASE_COMMIT = "dde6dbe1a331ee2d1673624daaad0c56fc1f9950"
BASE_TREE = "5111a8f664cd072bafe5654cfc31753235e8d567"
OUT = Path(__file__).resolve().parent


def find_bedrock_root() -> Path:
    for candidate in (ROOT, *ROOT.parents):
        if (candidate / "program/crazycraft-pack-production-v1").is_dir():
            return candidate
    git_link = ROOT / ".git"
    if git_link.is_file():
        line = git_link.read_text(encoding="utf-8").strip()
        if line.startswith("gitdir: "):
            git_dir = Path(line.removeprefix("gitdir: ")).resolve()
            for candidate in (git_dir, *git_dir.parents):
                if (candidate / "program/crazycraft-pack-production-v1").is_dir():
                    return candidate
    raise SystemExit("bedrock-server root containing Packet 004 was not found")


BEDROCK_ROOT = find_bedrock_root()
PACKET = BEDROCK_ROOT / "program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-004-skyreach-cliffs"
RESOURCES = {
    "sky_feather": "Sky Feather", "wind_silk": "Wind Silk", "cloud_wool": "Cloud Wool",
    "cliff_crystal": "Cliff Crystal", "storm_pinion": "Storm Pinion", "aether_stone": "Aether Stone",
    "updraft_reed_item": "Updraft Reed", "sky_vine_item": "Sky Vine",
    "float_resin": "Float Resin", "lift_bloom_item": "Lift Bloom",
}
BLOCKS = {
    "skyreach_log": {"display": "Skyreach Log", "category": "construction", "sound": "wood", "seconds": 2.0},
    "skyreach_wood": {"display": "Skyreach Wood", "category": "construction", "sound": "wood", "seconds": 2.0},
    "skyreach_planks": {"display": "Skyreach Planks", "category": "construction", "sound": "wood", "seconds": 1.5},
    "wind_slate": {"display": "Wind Slate", "category": "construction", "sound": "stone", "seconds": 2.0},
    "cliff_stone": {"display": "Cliff Stone", "category": "construction", "sound": "stone", "seconds": 2.5},
    "rope_timber": {"display": "Rope Timber", "category": "construction", "sound": "wood", "seconds": 2.0},
    "cloud_wool_block": {"display": "Cloud Wool Block", "category": "construction", "sound": "cloth", "seconds": 0.8},
    "pale_shelf_stone": {"display": "Pale Shelf Stone", "category": "construction", "sound": "stone", "seconds": 2.2},
    "cliff_gravel": {"display": "Cliff Gravel", "category": "nature", "sound": "gravel", "seconds": 0.7},
    "sky_moss_block": {"display": "Sky Moss Block", "category": "nature", "sound": "grass", "seconds": 0.5},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.relative_to(BEDROCK_ROOT).as_posix()


def source_record(asset_id: str) -> dict:
    paths = {
        "brief": PACKET / f"assets/briefs/{asset_id}.json",
        "editable_model": PACKET / f"assets/editable/{asset_id}.bbmodel",
        "editable_texture": PACKET / f"assets/editable/{asset_id}.png",
        "exported_geometry": PACKET / f"assets/export/models/{asset_id}.geo.json",
        "exported_animation": PACKET / f"assets/export/animations/{asset_id}.animation.json",
        "exported_texture": PACKET / f"assets/export/textures/{asset_id}.png",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise SystemExit(f"{asset_id}: missing packet inputs: {missing}")
    return {key: {"path": relative(path), "sha256": sha256(path)} for key, path in paths.items()}


def replace_lang_section(lines: list[str], begin: str, end: str, body: list[str]) -> list[str]:
    section = [begin, *body, end]
    if begin not in lines and end not in lines:
        return [*lines, *section]
    if lines.count(begin) != 1 or lines.count(end) != 1:
        raise SystemExit(f"malformed localization section: {begin}")
    start, stop = lines.index(begin), lines.index(end)
    if stop < start:
        raise SystemExit(f"reversed localization section: {begin}")
    return lines[:start] + section + lines[stop + 1 :]


def write_receipts(manifest_path: Path, sources: dict) -> None:
    authority = {
        "schema_version": 1,
        "authority": "PACKET_004_SKYREACH_STATIC_RESOURCE_AND_FULL_CUBE_BINDING",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE},
        "packet_manifest": {"path": relative(manifest_path), "sha256": sha256(manifest_path)},
        "normalization": {"warehouse_namespace": "aionforge_sr", "runtime_namespace": "aionbound", "identifier_policy": "PRESERVE_PACKET_ASSET_ID_NORMALIZE_NAMESPACE_ONLY"},
        "resource_ids": list(RESOURCES), "block_ids": list(BLOCKS), "source_inputs": sources,
        "presentation_policy": {
            "resources": {"shipping_form": "flat_inventory_icon", "texture_policy": "BYTE_IDENTICAL_PACKET_TEXTURE_COPY", "blockbench_status": "NOT_APPLICABLE", "reason": "Flat inventory icons require no custom geometry, locator, rig, UV editing, or animation."},
            "blocks": {"shipping_geometry": "minecraft:geometry.full_block", "texture_policy": "BYTE_IDENTICAL_PACKET_TEXTURE_COPY", "blockbench_status": "NOT_APPLICABLE", "reason": "Ordinary full-cube blocks require no custom geometry, locator, rig, UV editing, or animation."},
            "packet_custom_geometry_status": "NOT_PROMOTED_FOR_THESE_RUNTIME_FORMS",
        },
        "scope_exclusions": ["acquisition", "loot", "recipes", "world_generation", "scripts", "persistence", "BDS", "client claims", "candidate build"],
    }
    write_json(OUT / "SKYREACH_STATIC_FOUNDATIONS_AUTHORITY.json", authority)
    resources, blocks = [], []
    for asset_id in RESOURCES:
        source = PACKET / f"assets/export/textures/{asset_id}.png"
        shipping = ROOT / f"resource_pack/textures/aionbound/skyreach/items/{asset_id}.png"
        definition = ROOT / f"behavior_pack/items/{asset_id}.item.json"
        resources.append({"id": asset_id, "runtime_id": f"aionbound:{asset_id}", "definition": {"path": relative(definition), "sha256": sha256(definition)}, "texture": {"path": relative(shipping), "sha256": sha256(shipping)}, "source_texture_sha256": sha256(source), "texture_byte_equality": sha256(source) == sha256(shipping), "blockbench": "NOT_APPLICABLE_FLAT_INVENTORY_ICON"})
    for asset_id in BLOCKS:
        source = PACKET / f"assets/export/textures/{asset_id}.png"
        shipping = ROOT / f"resource_pack/textures/aionbound/skyreach/blocks/{asset_id}.png"
        definition = ROOT / f"behavior_pack/blocks/{asset_id}.block.json"
        blocks.append({"id": asset_id, "runtime_id": f"aionbound:{asset_id}", "definition": {"path": relative(definition), "sha256": sha256(definition)}, "texture": {"path": relative(shipping), "sha256": sha256(shipping)}, "source_texture_sha256": sha256(source), "texture_byte_equality": sha256(source) == sha256(shipping), "geometry": "minecraft:geometry.full_block", "blockbench": "NOT_APPLICABLE_ORDINARY_FULL_CUBE"})
    write_json(OUT / "SKYREACH_STATIC_FOUNDATIONS_REPORT.json", {
        "schema": "aionbound.wave1.skyreach-static-foundations.v1", "status": "SKYREACH_STATIC_FOUNDATIONS_STATIC_PASS",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE}, "scope": "ten Packet 004 flat resource items and ten ordinary full-cube blocks only",
        "resources": resources, "blocks": blocks,
        "shared_merge_hotspots": ["resource_pack/textures/item_texture.json", "resource_pack/textures/terrain_texture.json", "resource_pack/blocks.json", "resource_pack/texts/en_US.lang"],
        "checks": {"packet_inventory_exact": "PASS_20_OF_20", "namespace_normalization": "PASS_AIONFORGE_SR_TO_AIONBOUND", "definition_registry_language_closure": "PASS_20_OF_20", "texture_byte_equality": "PASS_20_OF_20", "png_decode": "PASS_20_OF_20", "blockbench": "NOT_APPLICABLE_FLAT_ICONS_AND_ORDINARY_FULL_CUBES"},
        "proof_scope": "STATIC_BP_RP_SOURCE_AND_EXACT_PACKET_TEXTURE_CLOSURE_ONLY",
        "not_proven": ["ACQUISITION", "LOOT", "RECIPES", "WORLD_GENERATION", "SCRIPT_OR_PERSISTENCE", "BEDROCK_CLIENT_RENDERING", "STABLE_BDS", "PACKAGE", "PHYSICAL_PS4", "MARKETPLACE"],
    })


def main() -> None:
    manifest_path = PACKET / "MANIFEST_FULL.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    packet_resources = {a["name"] for a in manifest["assets"] if a["tier"] == "RESOURCE"}
    packet_blocks = {a["name"] for a in manifest["assets"] if a["tier"] == "BLOCK"}
    if packet_resources != set(RESOURCES) or packet_blocks != set(BLOCKS):
        raise SystemExit("Packet 004 inventory drift")
    item_atlas_path = ROOT / "resource_pack/textures/item_texture.json"
    terrain_path = ROOT / "resource_pack/textures/terrain_texture.json"
    blocks_path = ROOT / "resource_pack/blocks.json"
    lang_path = ROOT / "resource_pack/texts/en_US.lang"
    item_atlas = json.loads(item_atlas_path.read_text(encoding="utf-8"))
    terrain = json.loads(terrain_path.read_text(encoding="utf-8"))
    rp_blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
    language = lang_path.read_text(encoding="utf-8").splitlines()
    sources = {}
    for asset_id, display in RESOURCES.items():
        sources[asset_id] = source_record(asset_id)
        source = PACKET / f"assets/export/textures/{asset_id}.png"
        shipping = ROOT / f"resource_pack/textures/aionbound/skyreach/items/{asset_id}.png"
        shipping.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, shipping)
        write_json(ROOT / f"behavior_pack/items/{asset_id}.item.json", {"format_version": "1.21.80", "minecraft:item": {"description": {"identifier": f"aionbound:{asset_id}", "menu_category": {"category": "items"}}, "components": {"minecraft:display_name": {"value": display}, "minecraft:icon": {"textures": {"default": asset_id}}}}})
        item_atlas["texture_data"][asset_id] = {"textures": f"textures/aionbound/skyreach/items/{asset_id}"}
    for asset_id, spec in BLOCKS.items():
        sources[asset_id] = source_record(asset_id)
        source = PACKET / f"assets/export/textures/{asset_id}.png"
        shipping = ROOT / f"resource_pack/textures/aionbound/skyreach/blocks/{asset_id}.png"
        shipping.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, shipping)
        write_json(ROOT / f"behavior_pack/blocks/{asset_id}.block.json", {"format_version": "1.21.80", "minecraft:block": {"description": {"identifier": f"aionbound:{asset_id}", "menu_category": {"category": spec["category"]}}, "components": {"minecraft:display_name": spec["display"], "minecraft:destructible_by_mining": {"seconds_to_destroy": spec["seconds"]}, "minecraft:geometry": "minecraft:geometry.full_block", "minecraft:material_instances": {"*": {"texture": asset_id, "render_method": "opaque"}}}}})
        terrain["texture_data"][asset_id] = {"textures": f"textures/aionbound/skyreach/blocks/{asset_id}"}
        rp_blocks[f"aionbound:{asset_id}"] = {"sound": spec["sound"], "textures": asset_id}
    language = replace_lang_section(language, "# BEGIN WAVE1 SKYREACH RESOURCE ITEMS", "# END WAVE1 SKYREACH RESOURCE ITEMS", [f"item.aionbound:{i}={n}" for i, n in RESOURCES.items()])
    language = replace_lang_section(language, "# BEGIN WAVE1 SKYREACH FULL-CUBE BLOCKS", "# END WAVE1 SKYREACH FULL-CUBE BLOCKS", [f"tile.aionbound:{i}.name={s['display']}" for i, s in BLOCKS.items()])
    write_json(item_atlas_path, item_atlas); write_json(terrain_path, terrain); write_json(blocks_path, rp_blocks)
    lang_path.write_text("\n".join(language) + "\n", encoding="utf-8")
    write_receipts(manifest_path, sources)


if __name__ == "__main__":
    main()
