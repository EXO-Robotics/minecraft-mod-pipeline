#!/usr/bin/env python3
"""Bind the ten Packet 001 plants into the Wave 1 BP/RP.

This is intentionally a static custom-block binding. Bedrock custom blocks do
not expose the entity animation-controller surface required to play the four
native skeletal clips, so those clips remain provenance evidence only.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


PLANTS = {
    "briar_vine": {
        "display": "Briar Vine",
        "faces": ["side"],
        "supports": [
            "minecraft:oak_log",
            "minecraft:dark_oak_log",
            "minecraft:mangrove_log",
            "aionbound:whisperwood_log",
            "aionbound:whisperwood_wood",
            "aionbound:moss_bark",
        ],
        "selection": {"origin": [-4, 0, -4], "size": [8, 16, 8]},
    },
    "ember_thistle": {
        "display": "Ember Thistle",
        "faces": ["up"],
        "supports": ["minecraft:grass_block", "minecraft:dirt", "minecraft:coarse_dirt", "minecraft:podzol"],
        "selection": {"origin": [-4, 0, -4], "size": [8, 14, 8]},
    },
    "glow_moss": {
        "display": "Glow Moss",
        "faces": ["up"],
        "supports": ["minecraft:stone", "minecraft:moss_block", "minecraft:grass_block", "minecraft:dirt"],
        "selection": {"origin": [-8, 0, -8], "size": [16, 5, 16]},
    },
    "hollow_lily": {
        "display": "Hollow Lily",
        "faces": ["up"],
        "supports": ["minecraft:mud", "minecraft:clay", "minecraft:dirt", "minecraft:grass_block"],
        "selection": {"origin": [-5, 0, -5], "size": [10, 7, 10]},
    },
    "lantern_bloom": {
        "display": "Lantern Bloom",
        "faces": ["up"],
        "supports": ["minecraft:grass_block", "minecraft:dirt", "minecraft:coarse_dirt", "minecraft:podzol"],
        "selection": {"origin": [-4, 0, -4], "size": [8, 8, 8]},
    },
    "mooncap_mushroom": {
        "display": "Mooncap Mushroom",
        "faces": ["up"],
        "supports": ["minecraft:grass_block", "minecraft:dirt", "minecraft:podzol", "minecraft:moss_block", "minecraft:mycelium"],
        "selection": {"origin": [-5, 0, -5], "size": [10, 11, 10]},
    },
    "pale_reed": {
        "display": "Pale Reed",
        "faces": ["up"],
        "supports": ["minecraft:mud", "minecraft:clay", "minecraft:sand", "minecraft:dirt", "minecraft:grass_block"],
        "selection": {"origin": [-4, 0, -4], "size": [8, 16, 8]},
    },
    "root_flower": {
        "display": "Root Flower",
        "faces": ["up"],
        "supports": ["minecraft:grass_block", "minecraft:dirt", "minecraft:coarse_dirt", "minecraft:podzol"],
        "selection": {"origin": [-5, 0, -4], "size": [10, 9, 9]},
    },
    "star_grass": {
        "display": "Star Grass",
        "faces": ["up"],
        "supports": ["minecraft:grass_block", "minecraft:dirt", "minecraft:coarse_dirt", "minecraft:podzol", "minecraft:moss_block"],
        "selection": {"origin": [-3, 0, -3], "size": [6, 11, 6]},
    },
    "whisper_fern": {
        "display": "Whisper Fern",
        "faces": ["up"],
        "supports": ["minecraft:grass_block", "minecraft:dirt", "minecraft:coarse_dirt", "minecraft:podzol", "minecraft:moss_block"],
        "selection": {"origin": [-7, 0, -7], "size": [14, 8, 14]},
    },
}


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--packet-assets", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    packet = args.packet_assets.resolve()
    evidence = repo / "engineering/native-assets/whisperwood/evidence"

    blocks_path = repo / "resource_pack/blocks.json"
    terrain_path = repo / "resource_pack/textures/terrain_texture.json"
    blocks_registry = json.loads(blocks_path.read_text(encoding="utf-8"))
    terrain_registry = json.loads(terrain_path.read_text(encoding="utf-8"))

    lang_path = repo / "resource_pack/texts/en_US.lang"
    lang_lines = lang_path.read_text(encoding="utf-8").splitlines()
    lang_prefixes = tuple(f"tile.aionbound:{asset}.name=" for asset in PLANTS)
    lang_lines = [line for line in lang_lines if not line.startswith(lang_prefixes)]

    for asset, spec in PLANTS.items():
        source_geometry = evidence / asset / "native-exports/pass-2.geo.json"
        geometry = json.loads(source_geometry.read_text(encoding="utf-8"))
        description = geometry["minecraft:geometry"][0]["description"]
        description["identifier"] = f"geometry.aionbound.{asset}"
        geometry_path = repo / f"resource_pack/models/aionbound/whisperwood/{asset}.geo.json"
        dump(geometry_path, geometry)

        texture_source = packet / f"export/textures/{asset}.png"
        texture_target = repo / f"resource_pack/textures/aionbound/whisperwood/plants/{asset}.png"
        texture_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(texture_source, texture_target)

        block = {
            "format_version": "1.21.80",
            "minecraft:block": {
                "description": {
                    "identifier": f"aionbound:{asset}",
                    "menu_category": {"category": "nature"},
                },
                "components": {
                    "minecraft:display_name": spec["display"],
                    "minecraft:collision_box": False,
                    "minecraft:selection_box": spec["selection"],
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
                        "conditions": [
                            {
                                "allowed_faces": spec["faces"],
                                "block_filter": spec["supports"],
                            }
                        ]
                    },
                },
            },
        }
        dump(repo / f"behavior_pack/blocks/{asset}.block.json", block)

        blocks_registry[f"aionbound:{asset}"] = {"sound": "grass", "textures": asset}
        terrain_registry["texture_data"][asset] = {
            "textures": f"textures/aionbound/whisperwood/plants/{asset}"
        }
        lang_lines.append(f"tile.aionbound:{asset}.name={spec['display']}")

    dump(blocks_path, blocks_registry)
    dump(terrain_path, terrain_registry)
    lang_path.write_text("\n".join(lang_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
