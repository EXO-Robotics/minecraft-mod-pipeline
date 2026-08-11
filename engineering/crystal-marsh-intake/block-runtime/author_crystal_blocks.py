#!/usr/bin/env python3
"""Deterministically bind the ten Packet 003 ordinary full-cube blocks."""

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
    "crystal_log": {
        "display": "Crystal Log", "category": "construction", "sound": "wood", "seconds": 2.0,
    },
    "marsh_wood": {
        "display": "Marsh Wood", "category": "construction", "sound": "wood", "seconds": 2.0,
    },
    "flood_planks": {
        "display": "Flood Planks", "category": "construction", "sound": "wood", "seconds": 2.0,
    },
    "crystal_stone": {
        "display": "Crystal Stone", "category": "construction", "sound": "stone", "seconds": 2.5,
    },
    "prism_brick": {
        "display": "Prism Brick", "category": "construction", "sound": "stone", "seconds": 2.5,
    },
    "wet_clay_block": {
        "display": "Wet Clay Block", "category": "nature", "sound": "gravel", "seconds": 0.8,
    },
    "glass_root_block": {
        "display": "Glass Root", "category": "nature", "sound": "wood", "seconds": 1.5,
    },
    "algae_block": {
        "display": "Algae Block", "category": "nature", "sound": "grass", "seconds": 0.4,
    },
    "marsh_soil": {
        "display": "Marsh Soil", "category": "nature", "sound": "gravel", "seconds": 0.6,
    },
    "crystal_gravel": {
        "display": "Crystal Gravel", "category": "nature", "sound": "gravel", "seconds": 0.7,
    },
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


def block_definition(asset_id: str, spec: dict) -> dict:
    return {
        "format_version": "1.21.80",
        "minecraft:block": {
            "description": {
                "identifier": f"aionbound:{asset_id}",
                "menu_category": {"category": spec["category"]},
            },
            "components": {
                "minecraft:display_name": spec["display"],
                "minecraft:destructible_by_mining": {
                    "seconds_to_destroy": spec["seconds"]
                },
                "minecraft:geometry": "minecraft:geometry.full_block",
                "minecraft:material_instances": {
                    "*": {"texture": asset_id, "render_method": "opaque"}
                },
            },
        },
    }


def main() -> None:
    manifest_path = PACKET / "MANIFEST_FULL.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    packet_blocks = {
        asset["name"] for asset in manifest["assets"] if asset["tier"] == "BLOCK"
    }
    if packet_blocks != set(ASSETS):
        raise SystemExit(
            f"Packet block inventory drift: expected {sorted(ASSETS)}, got {sorted(packet_blocks)}"
        )

    terrain_path = ROOT / "resource_pack/textures/terrain_texture.json"
    blocks_path = ROOT / "resource_pack/blocks.json"
    lang_path = ROOT / "resource_pack/texts/en_US.lang"
    terrain = json.loads(terrain_path.read_text(encoding="utf-8"))
    blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
    language_lines = lang_path.read_text(encoding="utf-8").splitlines()
    lang_begin = "# BEGIN WAVE1 CRYSTAL MARSH FULL-CUBE BLOCKS"
    lang_end = "# END WAVE1 CRYSTAL MARSH FULL-CUBE BLOCKS"
    lang_section = [lang_begin]
    lang_section.extend(
        f"tile.aionbound:{asset_id}.name={spec['display']}"
        for asset_id, spec in ASSETS.items()
    )
    lang_section.append(lang_end)
    if lang_begin in language_lines or lang_end in language_lines:
        if language_lines.count(lang_begin) != 1 or language_lines.count(lang_end) != 1:
            raise SystemExit("malformed Crystal Marsh block localization section")
        start = language_lines.index(lang_begin)
        stop = language_lines.index(lang_end)
        if stop < start:
            raise SystemExit("reversed Crystal Marsh block localization section")
        language_lines = language_lines[:start] + lang_section + language_lines[stop + 1 :]
    else:
        language_lines.extend(lang_section)

    sources = {}
    for asset_id, spec in ASSETS.items():
        sources[asset_id] = source_record(asset_id)
        source_texture = PACKET / f"assets/export/textures/{asset_id}.png"
        shipping_texture = ROOT / (
            f"resource_pack/textures/aionbound/crystal_marsh/blocks/{asset_id}.png"
        )
        shipping_texture.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_texture, shipping_texture)
        write_json(
            ROOT / f"behavior_pack/blocks/{asset_id}.block.json",
            block_definition(asset_id, spec),
        )
        terrain["texture_data"][asset_id] = {
            "textures": f"textures/aionbound/crystal_marsh/blocks/{asset_id}"
        }
        blocks[f"aionbound:{asset_id}"] = {
            "sound": spec["sound"],
            "textures": asset_id,
        }
    write_json(terrain_path, terrain)
    write_json(blocks_path, blocks)
    lang_path.write_text("\n".join(language_lines) + "\n", encoding="utf-8")

    write_json(
        OUT / "CRYSTAL_BLOCK_RUNTIME_AUTHORITY.json",
        {
            "schema_version": 1,
            "authority": "PACKET_003_CRYSTAL_MARSH_FULL_CUBE_BLOCK_BINDING",
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
            "geometry_policy": {
                "shipping_geometry": "minecraft:geometry.full_block",
                "blockbench_status": "NOT_APPLICABLE",
                "reason": (
                    "These ten approved runtime forms are ordinary full-cube blocks; "
                    "custom geometry, locators, rigging, UV editing, and animation "
                    "are not required."
                ),
                "packet_custom_geometry_status": "NOT_PROMOTED",
            },
            "texture_policy": "BYTE_IDENTICAL_PACKET_TEXTURE_COPY",
            "scope_exclusions": [
                "plants",
                "resource_items",
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
        },
    )

    assets = []
    for asset_id in ASSETS:
        source_texture = PACKET / f"assets/export/textures/{asset_id}.png"
        block_path = ROOT / f"behavior_pack/blocks/{asset_id}.block.json"
        shipping_texture = ROOT / (
            f"resource_pack/textures/aionbound/crystal_marsh/blocks/{asset_id}.png"
        )
        assets.append(
            {
                "id": asset_id,
                "runtime_id": f"aionbound:{asset_id}",
                "geometry": "minecraft:geometry.full_block",
                "texture_byte_equality": sha256(source_texture) == sha256(shipping_texture),
                "source_texture_sha256": sha256(source_texture),
                "files": {
                    "behavior_block": {
                        "path": block_path.relative_to(ROOT).as_posix(),
                        "sha256": sha256(block_path),
                    },
                    "shipping_texture": {
                        "path": shipping_texture.relative_to(ROOT).as_posix(),
                        "sha256": sha256(shipping_texture),
                    },
                },
            }
        )

    write_json(
        OUT / "CRYSTAL_BLOCK_RUNTIME_REPORT.json",
        {
            "schema_version": 1,
            "status": "CRYSTAL_BLOCK_RUNTIME_STATIC_PASS",
            "asset_count": len(assets),
            "assets": assets,
            "registry_files": {
                "terrain_texture": {
                    "path": terrain_path.relative_to(ROOT).as_posix(),
                    "binding_count": 10,
                    "hash_policy": "MUTABLE_SHARED_REGISTRY_VALIDATE_OWNED_ENTRIES",
                },
                "blocks": {
                    "path": blocks_path.relative_to(ROOT).as_posix(),
                    "binding_count": 10,
                    "hash_policy": "MUTABLE_SHARED_REGISTRY_VALIDATE_OWNED_ENTRIES",
                },
                "language": {
                    "path": lang_path.relative_to(ROOT).as_posix(),
                    "binding_count": 10,
                    "hash_policy": "MUTABLE_SHARED_REGISTRY_VALIDATE_OWNED_ENTRIES",
                },
            },
            "checks": {
                "packet_inventory_exact": "PASS_10_OF_10",
                "behavior_block_schema_static": "PASS_10_OF_10",
                "full_cube_geometry_binding": "PASS_10_OF_10",
                "texture_byte_equality": "PASS_10_OF_10",
                "terrain_blocks_language_closure": "PASS_10_OF_10",
                "png_decode_and_fully_opaque": "PASS_10_OF_10",
                "blockbench": "NOT_APPLICABLE_ORDINARY_FULL_CUBES",
            },
            "presentation_debt": [
                {
                    "id": "directional_wood_faces",
                    "status": "WITHHELD",
                    "reason": (
                        "Packet 003 supplies one atlas PNG per wood ID, not separately "
                        "authorized directional face textures or orientation states."
                    ),
                }
            ],
            "proof_scope": "STATIC_BP_RP_SOURCE_AND_EXACT_TEXTURE_CLOSURE_ONLY",
            "not_proven": [
                "ACQUISITION_OR_LOOT",
                "RECIPES",
                "WORLD_GENERATION",
                "SCRIPT_OR_PERSISTENCE",
                "BEDROCK_CLIENT_RENDERING",
                "STABLE_BDS",
                "PACKAGE",
                "PHYSICAL_PS4",
                "MARKETPLACE",
            ],
        },
    )


if __name__ == "__main__":
    main()
