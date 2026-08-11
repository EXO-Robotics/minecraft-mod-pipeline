#!/usr/bin/env python3
"""Deterministically bind the ten Packet 003 resource items into G8."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[3]
BASE_COMMIT = "466a061cbe22a01a4e561169df31e4f351edea71"
BASE_TREE = "1aadcfab635991f6d0fb4647f6ed2a3bb615a7af"


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
    raise SystemExit("bedrock-server root containing Packet 003 was not found")


BEDROCK_ROOT = find_bedrock_root()
PACKET = BEDROCK_ROOT / (
    "program/crazycraft-pack-production-v1/studio-prep/sprints/"
    "asset-sprint-003-crystal-marsh"
)
OUT = Path(__file__).resolve().parent
ASSETS = {
    "prism_pearl": "Prism Pearl",
    "crystal_reed_item": "Crystal Reed",
    "marsh_resin": "Marsh Resin",
    "glass_algae": "Glass Algae",
    "silt_core": "Silt Core",
    "flood_crystal": "Flood Crystal",
    "moon_pearl": "Moon Pearl",
    "wet_chitin": "Wet Chitin",
    "mire_bloom_item": "Mire Bloom",
    "crystal_root_item": "Crystal Root",
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
    return {
        key: {"path": relative(path), "sha256": sha256(path)}
        for key, path in paths.items()
    }


def update_lang() -> None:
    path = ROOT / "resource_pack/texts/en_US.lang"
    begin = "# BEGIN WAVE1 CRYSTAL MARSH RESOURCE ITEMS"
    end = "# END WAVE1 CRYSTAL MARSH RESOURCE ITEMS"
    lines = path.read_text(encoding="utf-8").splitlines()
    section = [begin]
    section.extend(
        f"item.aionbound:{asset_id}={display}"
        for asset_id, display in ASSETS.items()
    )
    section.append(end)
    if begin in lines or end in lines:
        if lines.count(begin) != 1 or lines.count(end) != 1:
            raise SystemExit("malformed Crystal Marsh resource localization section")
        start = lines.index(begin)
        stop = lines.index(end)
        if stop < start:
            raise SystemExit("reversed Crystal Marsh resource localization section")
        lines = lines[:start] + section + lines[stop + 1 :]
    else:
        lines.extend(section)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    manifest_path = PACKET / "MANIFEST_FULL.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    packet_resources = {
        asset["name"] for asset in manifest["assets"] if asset["tier"] == "RESOURCE"
    }
    if packet_resources != set(ASSETS):
        raise SystemExit(
            "Packet resource inventory drift: "
            f"expected {sorted(ASSETS)}, got {sorted(packet_resources)}"
        )

    atlas_path = ROOT / "resource_pack/textures/item_texture.json"
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    sources = {}
    for asset_id, display in ASSETS.items():
        sources[asset_id] = source_record(asset_id)
        source_texture = PACKET / f"assets/export/textures/{asset_id}.png"
        shipping_texture = ROOT / (
            f"resource_pack/textures/aionbound/crystal_marsh/items/{asset_id}.png"
        )
        shipping_texture.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_texture, shipping_texture)

        write_json(
            ROOT / f"behavior_pack/items/{asset_id}.item.json",
            {
                "format_version": "1.21.80",
                "minecraft:item": {
                    "description": {
                        "identifier": f"aionbound:{asset_id}",
                        "menu_category": {"category": "items"},
                    },
                    "components": {
                        "minecraft:display_name": {"value": display},
                        "minecraft:icon": {"textures": {"default": asset_id}},
                    },
                },
            },
        )
        atlas["texture_data"][asset_id] = {
            "textures": f"textures/aionbound/crystal_marsh/items/{asset_id}"
        }

    write_json(atlas_path, atlas)
    update_lang()

    authority = {
        "schema_version": 1,
        "authority": "PACKET_003_CRYSTAL_MARSH_RESOURCE_ITEM_BINDING",
        "base_commit": BASE_COMMIT,
        "base_tree": BASE_TREE,
        "packet_manifest": {
            "path": relative(manifest_path),
            "sha256": sha256(manifest_path),
        },
        "asset_count": len(ASSETS),
        "asset_ids": list(ASSETS),
        "source_inputs": sources,
        "runtime_namespace": "aionbound",
        "presentation_policy": {
            "shipping_form": "flat_inventory_icon",
            "texture_policy": "BYTE_IDENTICAL_PACKET_TEXTURE_COPY",
            "blockbench_status": "NOT_APPLICABLE",
            "reason": (
                "Flat inventory icons require no custom geometry, locator, rig, "
                "UV editing, or animation."
            ),
            "packet_custom_geometry_status": "NOT_PROMOTED",
        },
        "scope_exclusions": [
            "acquisition",
            "loot",
            "recipes",
            "world_generation",
            "scripts",
            "persistence",
            "BDS",
            "client claims",
            "candidate build",
        ],
    }
    write_json(OUT / "CRYSTAL_RESOURCE_RUNTIME_AUTHORITY.json", authority)

    resources = []
    for asset_id, display in ASSETS.items():
        source_texture = PACKET / f"assets/export/textures/{asset_id}.png"
        item_path = ROOT / f"behavior_pack/items/{asset_id}.item.json"
        icon_path = ROOT / (
            f"resource_pack/textures/aionbound/crystal_marsh/items/{asset_id}.png"
        )
        resources.append(
            {
                "warehouse_id": asset_id,
                "runtime_id": f"aionbound:{asset_id}",
                "display_name": display,
                "item_path": item_path.relative_to(ROOT).as_posix(),
                "item_sha256": sha256(item_path),
                "atlas_key": asset_id,
                "texture_path": f"textures/aionbound/crystal_marsh/items/{asset_id}",
                "icon_path": icon_path.relative_to(ROOT).as_posix(),
                "icon_sha256": sha256(icon_path),
                "source_icon_sha256": sha256(source_texture),
                "icon_byte_equality": sha256(icon_path) == sha256(source_texture),
                "blockbench": {
                    "status": "NOT_APPLICABLE",
                    "reason": "flat inventory icon; no custom geometry or animation",
                },
            }
        )

    write_json(
        OUT / "CRYSTAL_RESOURCE_RUNTIME_REPORT.json",
        {
            "schema": "aionbound.wave1.crystal-marsh-resource-runtime.v1",
            "status": "CRYSTAL_RESOURCE_RUNTIME_STATIC_PASS",
            "base": {"commit": BASE_COMMIT, "tree": BASE_TREE},
            "scope": "ten Packet 003 warehouse resource items only",
            "resources": resources,
            "shared_files": [
                {
                    "path": atlas_path.relative_to(ROOT).as_posix(),
                    "change": "ten aionbound item-atlas bindings",
                    "binding_count": 10,
                    "hash_policy": "MUTABLE_SHARED_REGISTRY_VALIDATE_OWNED_ENTRIES",
                },
                {
                    "path": "resource_pack/texts/en_US.lang",
                    "change": "ten English item localization bindings",
                    "binding_count": 10,
                    "hash_policy": "MUTABLE_SHARED_REGISTRY_VALIDATE_OWNED_ENTRIES",
                },
            ],
            "checks": {
                "packet_inventory_exact": "PASS_10_OF_10",
                "item_definition_closure": "PASS_10_OF_10",
                "icon_byte_equality": "PASS_10_OF_10",
                "atlas_language_closure": "PASS_10_OF_10",
                "blockbench": "NOT_APPLICABLE_FLAT_INVENTORY_ICONS",
            },
            "proof_scope": "STATIC_BP_RP_SOURCE_AND_EXACT_PACKET_ICON_CLOSURE_ONLY",
            "not_proven": [
                "ACQUISITION",
                "LOOT",
                "RECIPES",
                "WORLD_GENERATION",
                "SCRIPT_OR_PERSISTENCE",
                "BEDROCK_CLIENT_RENDERING_OR_UI_READABILITY",
                "STABLE_BDS",
                "PACKAGE",
                "PHYSICAL_PS4",
                "MARKETPLACE",
            ],
        },
    )


if __name__ == "__main__":
    main()
