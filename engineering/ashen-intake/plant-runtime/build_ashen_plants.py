#!/usr/bin/env python3
"""Bind ten native-repaired Packet 002 plants as stable custom blocks.

The native projects prove geometry, texture, and locator preservation. Bedrock
custom blocks do not expose the entity animation-controller surface, so plant
clips remain native evidence and are not silently rebound through surrogates.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


PLANTS = {
    "cinder_grass": ("Cinder Grass", ["up"], ["aionbound:ash_soil", "aionbound:cinder_gravel"], [-6, 0, -6, 12, 8, 12]),
    "ash_fern": ("Ash Fern", ["up"], ["aionbound:ash_soil", "aionbound:cinder_gravel"], [-7, 0, -7, 14, 11, 14]),
    "smoke_reed": ("Smoke Reed", ["up"], ["aionbound:ash_soil", "aionbound:smolder_stone", "aionbound:ember_moss"], [-4, 0, -4, 8, 16, 8]),
    "char_shrub": ("Char Shrub", ["up"], ["aionbound:ash_soil", "aionbound:cinder_gravel"], [-7, 0, -7, 14, 13, 14]),
    "soot_mushroom": ("Soot Mushroom", ["up"], ["aionbound:ash_soil", "aionbound:smolder_stone", "aionbound:basalt_brick"], [-5, 0, -5, 10, 8, 10]),
    "magma_moss": ("Magma Moss", ["up"], ["aionbound:smolder_stone", "aionbound:basalt_brick", "aionbound:basalt_pillar"], [-8, 0, -8, 16, 4, 16]),
    "glow_root": ("Glow Root", ["down", "side"], ["aionbound:smolder_stone", "aionbound:basalt_brick", "minecraft:stone", "minecraft:deepslate"], [-5, 0, -5, 10, 16, 10]),
    "basalt_flower": ("Basalt Flower", ["up"], ["aionbound:smolder_stone", "aionbound:basalt_brick", "aionbound:cinder_gravel"], [-5, 0, -5, 10, 10, 10]),
    "ember_vine": ("Ember Vine", ["down", "side"], ["aionbound:ash_log", "aionbound:heat_bark", "aionbound:smolder_stone", "aionbound:basalt_pillar"], [-4, 0, -4, 8, 16, 8]),
    "fire_bloom": ("Fire Bloom", ["up"], ["aionbound:ash_soil", "aionbound:ember_moss", "aionbound:cinder_gravel"], [-5, 0, -5, 10, 11, 10]),
}

REPRESENTATIVE = {"smoke_reed", "fire_bloom"}


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def evidence_root(repo: Path, asset: str) -> Path:
    lane = "representative" if asset in REPRESENTATIVE else "plants"
    return repo / f"engineering/native-assets/ashen/{lane}/evidence/{asset}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    repo = args.repo.resolve()

    blocks_path = repo / "resource_pack/blocks.json"
    terrain_path = repo / "resource_pack/textures/terrain_texture.json"
    lang_path = repo / "resource_pack/texts/en_US.lang"
    blocks_registry = json.loads(blocks_path.read_text(encoding="utf-8"))
    terrain_registry = json.loads(terrain_path.read_text(encoding="utf-8"))
    lang_lines = lang_path.read_text(encoding="utf-8").splitlines()
    prefixes = tuple(f"tile.aionbound:{asset}.name=" for asset in PLANTS)
    lang_lines = [line for line in lang_lines if not line.startswith(prefixes)]

    for asset, (display, faces, supports, bounds) in PLANTS.items():
        evidence = evidence_root(repo, asset)
        geometry = json.loads((evidence / "native-exports/pass-2.geo.json").read_text(encoding="utf-8"))
        description = geometry["minecraft:geometry"][0]["description"]
        description["identifier"] = f"geometry.aionbound.{asset}"
        dump(repo / f"resource_pack/models/aionbound/ashen/{asset}.geo.json", geometry)

        texture_target = repo / f"resource_pack/textures/aionbound/ashen/plants/{asset}.png"
        texture_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(evidence / f"inputs/{asset}.source.png", texture_target)

        origin = bounds[:3]
        size = bounds[3:]
        block = {
            "format_version": "1.21.80",
            "minecraft:block": {
                "description": {"identifier": f"aionbound:{asset}", "menu_category": {"category": "nature"}},
                "components": {
                    "minecraft:display_name": display,
                    "minecraft:collision_box": False,
                    "minecraft:selection_box": {"origin": origin, "size": size},
                    "minecraft:destructible_by_mining": {"seconds_to_destroy": 0.1},
                    "minecraft:geometry": f"geometry.aionbound.{asset}",
                    "minecraft:material_instances": {
                        "*": {"texture": asset, "render_method": "alpha_test", "ambient_occlusion": False, "face_dimming": False}
                    },
                    "minecraft:placement_filter": {"conditions": [{"allowed_faces": faces, "block_filter": supports}]},
                },
            },
        }
        dump(repo / f"behavior_pack/blocks/{asset}.block.json", block)
        blocks_registry[f"aionbound:{asset}"] = {"sound": "grass", "textures": asset}
        terrain_registry["texture_data"][asset] = {"textures": f"textures/aionbound/ashen/plants/{asset}"}
        lang_lines.append(f"tile.aionbound:{asset}.name={display}")

    dump(blocks_path, blocks_registry)
    dump(terrain_path, terrain_registry)
    lang_path.write_text("\n".join(lang_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
