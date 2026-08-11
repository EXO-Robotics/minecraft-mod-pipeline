#!/usr/bin/env python3
"""Bind the five native-PASS Whisperwood ordinary creatures into BP/RP runtime files."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "engineering/native-assets/whisperwood/evidence"

ASSETS = {
    "lantern_hare": {
        "class": "ambient",
        "idle": "idle_ear_flick",
        "move": "hop",
        "health": 8,
        "movement": 0.30,
        "collision": [0.55, 0.62],
        "spawn": {"brightness": [0, 7], "weight": 3, "herd": [1, 2]},
    },
    "mosskip_fawn": {
        "class": "ambient",
        "idle": "idle",
        "move": "hop",
        "health": 10,
        "movement": 0.27,
        "collision": [0.65, 0.72],
        "spawn": {"brightness": [7, 15], "weight": 2, "herd": [1, 2]},
    },
    "mosskip_doe": {
        "class": "ambient",
        "idle": "idle_graze",
        "move": "hop_bound",
        "health": 20,
        "movement": 0.25,
        "collision": [0.9, 1.2],
        "spawn": {"brightness": [7, 15], "weight": 3, "herd": [1, 2]},
    },
    "mosskip_buck": {
        "class": "neutral",
        "idle": "idle_graze",
        "move": "hop_bound",
        "health": 30,
        "movement": 0.27,
        "attack": 5,
        "collision": [1.05, 1.35],
        "spawn": {"brightness": [7, 15], "weight": 1, "herd": [1, 1]},
    },
    "rootback_boar": {
        "class": "neutral",
        "idle": "idle",
        "move": "walk_trundle",
        "health": 28,
        "movement": 0.22,
        "attack": 5,
        "collision": [1.2, 1.05],
        "spawn": {"brightness": [4, 15], "weight": 2, "herd": [1, 2]},
    },
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_ids(value: object) -> object:
    if isinstance(value, dict):
        return {normalize_ids(key): normalize_ids(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_ids(item) for item in value]
    if isinstance(value, str):
        return value.replace("geometry.aionforge_ww.", "geometry.aionbound.whisperwood.").replace(
            "animation.aionforge_ww.", "animation.aionbound.whisperwood."
        )
    return value


def behavior_entity(asset: str, spec: dict) -> dict:
    width, height = spec["collision"]
    components = {
        "minecraft:type_family": {"family": ["aionbound", "creature", spec["class"], "whisperwood"]},
        "minecraft:collision_box": {"width": width, "height": height},
        "minecraft:health": {"value": spec["health"], "max": spec["health"]},
        "minecraft:movement": {"value": spec["movement"]},
        "minecraft:movement.basic": {},
        "minecraft:navigation.walk": {
            "avoid_damage_blocks": True,
            "avoid_water": True,
            "can_path_over_water": False,
            "can_sink": True,
        },
        "minecraft:despawn": {
            "despawn_from_distance": {"min_distance": 32, "max_distance": 96},
            "despawn_from_chance": True,
            "despawn_from_inactivity": True,
            "despawn_from_simulation_edge": True,
            "min_range_inactivity_timer": 30,
            "min_range_random_chance": 800,
        },
        "minecraft:physics": {},
        "minecraft:behavior.random_stroll": {
            "priority": 6,
            "speed_multiplier": 0.75,
            "interval": 100 if spec["class"] == "neutral" else 140,
        },
        "minecraft:behavior.look_at_player": {
            "priority": 7,
            "look_distance": 7,
            "probability": 0.025,
        },
        "minecraft:behavior.random_look_around": {"priority": 8},
    }
    if spec["class"] == "ambient":
        # Damage-triggered panic provides readable flight without inventing a proactive target policy.
        components["minecraft:behavior.panic"] = {"priority": 1, "speed_multiplier": 1.35}
    else:
        components["minecraft:attack"] = {"damage": spec["attack"]}
        components["minecraft:behavior.hurt_by_target"] = {"priority": 1}
        components["minecraft:behavior.melee_attack"] = {
            "priority": 2,
            "speed_multiplier": 1.2,
            "track_target": True,
        }
    return {
        "format_version": "1.21.80",
        "minecraft:entity": {
            "description": {
                "identifier": f"aionbound:{asset}",
                "is_spawnable": True,
                "is_summonable": True,
            },
            "components": components,
        },
    }


def client_entity(asset: str, animation_names: list[str], spec: dict) -> dict:
    aliases = {name: f"animation.aionbound.whisperwood.{asset}.{name}" for name in animation_names}
    aliases["runtime"] = f"controller.animation.aionbound.whisperwood.{asset}.runtime"
    return {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": f"aionbound:{asset}",
                "materials": {"default": "entity_alphatest"},
                "textures": {"default": f"textures/aionbound/whisperwood/entity/{asset}"},
                "geometry": {"default": f"geometry.aionbound.whisperwood.{asset}"},
                "animations": aliases,
                "scripts": {"animate": ["runtime"]},
                "render_controllers": [f"controller.render.aionbound.whisperwood.{asset}"],
            }
        },
    }


def animation_controller(asset: str, spec: dict, animation_names: list[str]) -> dict:
    idle = spec["idle"]
    move = spec["move"]
    hurt = "hurt" if "hurt" in animation_names else idle
    death = "death" if "death" in animation_names else idle
    return {
        "format_version": "1.10.0",
        "animation_controllers": {
            f"controller.animation.aionbound.whisperwood.{asset}.runtime": {
                "initial_state": "idle",
                "states": {
                    "idle": {
                        "animations": [idle],
                        "transitions": [
                            {"dead": "query.health <= 0.0"},
                            {"hurt": "query.hurt_time > 0.0"},
                            {"moving": "query.modified_move_speed > 0.05"},
                        ],
                        "blend_transition": 0.12,
                    },
                    "moving": {
                        "animations": [move],
                        "transitions": [
                            {"dead": "query.health <= 0.0"},
                            {"hurt": "query.hurt_time > 0.0"},
                            {"idle": "query.modified_move_speed <= 0.05"},
                        ],
                        "blend_transition": 0.08,
                    },
                    "hurt": {
                        "animations": [hurt],
                        "transitions": [
                            {"dead": "query.health <= 0.0"},
                            {"moving": "query.hurt_time <= 0.0 && query.modified_move_speed > 0.05"},
                            {"idle": "query.hurt_time <= 0.0"},
                        ],
                        "blend_transition": 0.05,
                    },
                    "dead": {"animations": [death]},
                },
            }
        },
    }


def render_controller(asset: str) -> dict:
    return {
        "format_version": "1.8.0",
        "render_controllers": {
            f"controller.render.aionbound.whisperwood.{asset}": {
                "geometry": "Geometry.default",
                "materials": [{"*": "Material.default"}],
                "textures": ["Texture.default"],
            }
        },
    }


def spawn_rule(asset: str, spec: dict) -> dict:
    minimum, maximum = spec["spawn"]["brightness"]
    herd_min, herd_max = spec["spawn"]["herd"]
    return {
        "format_version": "1.8.0",
        "minecraft:spawn_rules": {
            "description": {"identifier": f"aionbound:{asset}", "population_control": "animal"},
            "conditions": [
                {
                    "minecraft:spawns_on_surface": {},
                    "minecraft:brightness_filter": {
                        "min": minimum,
                        "max": maximum,
                        "adjust_for_weather": True,
                    },
                    "minecraft:biome_filter": {
                        "all_of": [
                            {"test": "has_biome_tag", "operator": "==", "value": "overworld"},
                            {"test": "has_biome_tag", "operator": "==", "value": "forest"},
                        ]
                    },
                    "minecraft:weight": {"default": spec["spawn"]["weight"]},
                    "minecraft:herd": {"min_size": herd_min, "max_size": herd_max},
                    "minecraft:density_limit": {"surface": 2, "underground": 0},
                    "minecraft:distance_filter": {"min": 24, "max": 96},
                }
            ],
        },
    }


def main() -> None:
    for asset, spec in ASSETS.items():
        evidence = EVIDENCE / asset
        receipt = json.loads((evidence / "entity-animation-native-receipt.json").read_text(encoding="utf-8"))
        if receipt.get("status") != "PASS":
            raise SystemExit(f"{asset}: native receipt is not PASS")

        geometry = normalize_ids(json.loads((evidence / "native-exports/pass-2.geo.json").read_text(encoding="utf-8")))
        animations = normalize_ids(json.loads((evidence / "native-exports/pass-2.animation.json").read_text(encoding="utf-8")))
        animation_names = sorted(key.rsplit(".", 1)[-1] for key in animations["animations"])

        write_json(ROOT / f"behavior_pack/entities/{asset}.entity.json", behavior_entity(asset, spec))
        write_json(ROOT / f"behavior_pack/spawn_rules/{asset}.spawn_rules.json", spawn_rule(asset, spec))
        write_json(ROOT / f"resource_pack/entity/{asset}.entity.json", client_entity(asset, animation_names, spec))
        write_json(ROOT / f"resource_pack/models/aionbound/whisperwood/{asset}.geo.json", geometry)
        write_json(ROOT / f"resource_pack/animations/aionbound/whisperwood/{asset}.animation.json", animations)
        write_json(
            ROOT / f"resource_pack/animation_controllers/aionbound/whisperwood/{asset}.animation_controllers.json",
            animation_controller(asset, spec, animation_names),
        )
        write_json(
            ROOT / f"resource_pack/render_controllers/aionbound/whisperwood/{asset}.render_controllers.json",
            render_controller(asset),
        )
        texture_target = ROOT / f"resource_pack/textures/aionbound/whisperwood/entity/{asset}.png"
        texture_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(evidence / f"native-project/textures/{asset}.png", texture_target)


if __name__ == "__main__":
    main()
