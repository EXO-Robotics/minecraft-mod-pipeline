#!/usr/bin/env python3
"""Bind Packet 003 native-repaired plants as stable custom blocks.

Native Blockbench evidence is authoritative for geometry and texture bytes.
Custom-block skeletal playback has no clean Stable binding, so authored clips
remain evidence only and are not replaced with entity surrogates or scripts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPRESENTATIVE = {"bubble_pod", "flood_reed"}

MARSH_GROUND = [
    "aionbound:marsh_soil",
    "aionbound:wet_clay_block",
    "aionbound:crystal_gravel",
    "minecraft:mud",
    "minecraft:clay",
]
CRYSTAL_SHADE = [
    "aionbound:marsh_soil",
    "aionbound:glass_root_block",
    "aionbound:crystal_stone",
    "aionbound:crystal_gravel",
]
CHANNEL_ATTACHMENTS = [
    "aionbound:crystal_log",
    "aionbound:marsh_wood",
    "aionbound:glass_root_block",
    "aionbound:crystal_stone",
    "aionbound:prism_brick",
]


@dataclass(frozen=True)
class Plant:
    display: str
    faces: tuple[str, ...]
    supports: tuple[str, ...]
    selection: tuple[int, int, int, int, int, int]
    waterloggable: bool = False
    light: int = 0


PLANTS = {
    "crystal_lily": Plant("Crystal Lily", ("up",), tuple(MARSH_GROUND), (-7, 0, -7, 14, 8, 14), True, 3),
    "flood_reed": Plant("Flood Reed", ("up",), tuple(MARSH_GROUND), (-4, 0, -4, 8, 16, 8), True),
    "prism_bloom": Plant("Prism Bloom", ("up",), tuple(CRYSTAL_SHADE), (-6, 0, -6, 12, 12, 12), False, 3),
    "glass_moss": Plant("Glass Moss", ("up",), tuple(CRYSTAL_SHADE), (-8, 0, -8, 16, 3, 16), False, 2),
    "marsh_fern": Plant("Marsh Fern", ("up",), tuple(MARSH_GROUND), (-7, 0, -7, 14, 13, 14)),
    "glow_kelp": Plant("Glow Kelp", ("up",), tuple(MARSH_GROUND), (-5, 0, -5, 10, 16, 10), True, 6),
    "mire_orchid": Plant("Mire Orchid", ("up",), tuple(MARSH_GROUND), (-5, 0, -5, 10, 12, 10)),
    "bubble_pod": Plant("Bubble Pod", ("up",), tuple(MARSH_GROUND), (-6, 0, -6, 12, 14, 12), True),
    "pearl_grass": Plant("Pearl Grass", ("up",), tuple(MARSH_GROUND), (-7, 0, -7, 14, 14, 14)),
    "crystal_vine": Plant("Crystal Vine", ("down", "side"), tuple(CHANNEL_ATTACHMENTS), (-4, 0, -4, 8, 16, 8), True),
}


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def evidence_root(repo: Path, asset: str) -> Path:
    lane = "representative" if asset in REPRESENTATIVE else "plants"
    return repo / f"engineering/native-assets/crystal-marsh/{lane}/evidence/{asset}"


def block_definition(asset: str, spec: Plant) -> dict:
    origin = list(spec.selection[:3])
    size = list(spec.selection[3:])
    components: dict[str, object] = {
        "minecraft:display_name": spec.display,
        "minecraft:collision_box": False,
        "minecraft:selection_box": {"origin": origin, "size": size},
        "minecraft:destructible_by_mining": {"seconds_to_destroy": 0.1},
        "minecraft:geometry": f"geometry.aionbound.{asset}",
        "minecraft:material_instances": {
            "*": {
                "texture": asset,
                "render_method": "alpha_test",
                "ambient_occlusion": False,
                "face_dimming": False,
            }
        },
        "minecraft:placement_filter": {
            "conditions": [{"allowed_faces": list(spec.faces), "block_filter": list(spec.supports)}]
        },
        "minecraft:loot": f"loot_tables/blocks/{asset}.json",
    }
    if spec.waterloggable:
        components["minecraft:liquid_detection"] = {
            "detection_rules": [
                {"liquid_type": "water", "can_contain_liquid": True, "on_liquid_touches": "blocking"}
            ]
        }
    if spec.light:
        components["minecraft:light_emission"] = spec.light
    return {
        "format_version": "1.21.80",
        "minecraft:block": {
            "description": {"identifier": f"aionbound:{asset}", "menu_category": {"category": "nature"}},
            "components": components,
        },
    }


def build(repo: Path) -> tuple[dict[Path, bytes], dict]:
    files: dict[Path, bytes] = {}
    blocks_path = repo / "resource_pack/blocks.json"
    terrain_path = repo / "resource_pack/textures/terrain_texture.json"
    lang_path = repo / "resource_pack/texts/en_US.lang"
    blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
    terrain = json.loads(terrain_path.read_text(encoding="utf-8"))
    lang_lines = lang_path.read_text(encoding="utf-8").splitlines()
    prefixes = tuple(f"tile.aionbound:{asset}.name=" for asset in PLANTS)
    lang_lines = [line for line in lang_lines if not line.startswith(prefixes)]
    rows = []

    for asset, spec in PLANTS.items():
        evidence = evidence_root(repo, asset)
        geometry_source = evidence / "native-exports/pass-2.geo.json"
        texture_source = evidence / f"inputs/{asset}.source.png"
        geometry = json.loads(geometry_source.read_text(encoding="utf-8"))
        geometry["minecraft:geometry"][0]["description"]["identifier"] = f"geometry.aionbound.{asset}"

        geometry_path = repo / f"resource_pack/models/aionbound/crystal_marsh/{asset}.geo.json"
        texture_path = repo / f"resource_pack/textures/aionbound/crystal_marsh/plants/{asset}.png"
        block_path = repo / f"behavior_pack/blocks/{asset}.block.json"
        files[geometry_path] = encoded(geometry)
        files[texture_path] = texture_source.read_bytes()
        files[block_path] = encoded(block_definition(asset, spec))

        blocks[f"aionbound:{asset}"] = {"sound": "grass", "textures": asset}
        terrain["texture_data"][asset] = {
            "textures": f"textures/aionbound/crystal_marsh/plants/{asset}"
        }
        lang_lines.append(f"tile.aionbound:{asset}.name={spec.display}")
        rows.append({
            "asset": asset,
            "native_lane": "representative" if asset in REPRESENTATIVE else "plants",
            "geometry_source_sha256": hashlib.sha256(geometry_source.read_bytes()).hexdigest(),
            "runtime_geometry_sha256": hashlib.sha256(files[geometry_path]).hexdigest(),
            "texture_sha256": hashlib.sha256(texture_source.read_bytes()).hexdigest(),
            "waterloggable": spec.waterloggable,
            "light_emission": spec.light,
            "loot_binding": f"loot_tables/blocks/{asset}.json",
        })

    files[blocks_path] = encoded(blocks)
    files[terrain_path] = encoded(terrain)
    files[lang_path] = ("\n".join(lang_lines) + "\n").encode()
    report = {
        "schema": "aionbound.wave1.crystal-marsh-plant-runtime.v1",
        "status": "PASS_SOURCE_STATIC_PLANT_BINDING",
        "base_commit": "6a10cd8a82635299ae62ab8f6b9095c9b793c7a3",
        "base_tree": "689fa214ae21ab9739a8b6710fdbb5bb00ebeaeb",
        "assets": rows,
        "implementation": {
            "format_version": "1.21.80",
            "runtime_form": "custom_block_with_native_geometry_and_alpha_test_material",
            "collision": False,
            "waterloggable_assets": sorted(a for a, s in PLANTS.items() if s.waterloggable),
            "native_texture_bytes_preserved": True,
            "native_animation_playback": "WITHHELD_NO_CLEAN_STABLE_CUSTOM_BLOCK_SKELETAL_BINDING",
            "entity_surrogate": False,
            "script_component": False,
        },
        "economy_dependency": {
            "owner": "crystal_economy_equipment",
            "state": "BOUND_PATHS_TABLE_BYTES_OWNED_BY_ECONOMY_LANE",
            "paths": [f"behavior_pack/loot_tables/blocks/{a}.json" for a in PLANTS],
        },
        "proof_boundary": [
            "source_tree_static_only",
            "not_live_placement_harvest_waterlogging_or_light_proof",
            "not_client_geometry_alpha_or_water_render_proof",
            "not_creator_tools_bds_console_marketplace_or_release_proof",
        ],
    }
    files[OUT / "CRYSTAL_PLANT_RUNTIME_REPORT.json"] = encoded(report)
    return files, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    files, _ = build(repo)
    mismatches = []
    for path, data in files.items():
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                mismatches.append(str(path.relative_to(repo)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".png":
                shutil.copyfile(evidence_root(repo, path.stem) / f"inputs/{path.stem}.source.png", path)
            else:
                path.write_bytes(data)
    if mismatches:
        print(json.dumps({"status": "FAIL", "mismatches": mismatches}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "outputs": len(files), "mode": "check" if args.check else "write"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
