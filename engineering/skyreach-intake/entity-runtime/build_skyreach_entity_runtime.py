#!/usr/bin/env python3
"""Build the ten native-qualified Skyreach creature runtime surfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE_COMMIT = "654d20ff9fd45d8bc7f2400ea35248e84d82b07b"
BASE_TREE = "69ac4899f44d598da0bb939b710c4453c947ce37"
REPRESENTATIVE_REPORT = ROOT / "engineering/native-assets/skyreach/representative/SKYREACH_REPRESENTATIVE_NATIVE_REPORT.json"
CREATURE_REPORT = ROOT / "engineering/native-assets/skyreach/creatures/SKYREACH_CREATURE_NATIVE_REPORT.json"

ASSETS = {
    "cloud_goat": {
        "display": "Cloud Goat", "role": "neutral_ledge_grazer", "health": 24,
        "attack": 4, "speed": 0.22, "width": 0.9, "height": 1.15,
        "flying": False, "hostile": False, "natural": True,
        "weight": 2, "herd": (1, 2), "density": 2, "light": (7, 15),
        "audio": ("mob.goat.ambient", "mob.goat.hurt", "mob.goat.death", [0.9, 1.05], 0.72),
        "clips": ("idle", "walk", "hop_ledge"), "native_lane": "representative",
    },
    "gale_hawk": {
        "display": "Gale Hawk", "role": "hostile_aerial_patrol", "health": 18,
        "attack": 4, "speed": 0.27, "width": 0.7, "height": 0.55,
        "flying": True, "hostile": True, "natural": True,
        "weight": 1, "herd": (1, 1), "density": 1, "light": (7, 15),
        "audio": ("mob.parrot.idle", "mob.parrot.hurt", "mob.parrot.death", [0.85, 1.0], 0.55),
        "clips": ("idle", "fly", "stoop"), "native_lane": "representative",
    },
    "wind_roc": {
        "display": "Wind Roc", "role": "arena_only_apex_soaring_shell", "health": 96,
        "attack": 9, "speed": 0.25, "width": 2.0, "height": 1.65,
        "flying": True, "hostile": True, "natural": False,
        "weight": None, "herd": None, "density": None, "light": None,
        "audio": ("mob.phantom.idle", "mob.phantom.hurt", "mob.phantom.death", [0.65, 0.78], 1.0),
        "clips": ("idle_perch", "soar", "dive"), "native_lane": "representative",
    },
    "cliff_ram": {
        "display": "Cliff Ram", "role": "neutral_heavy_ledge_charger", "health": 30,
        "attack": 6, "speed": 0.21, "width": 1.0, "height": 1.2,
        "flying": False, "hostile": False, "natural": True,
        "weight": 2, "herd": (1, 2), "density": 2, "light": (7, 15),
        "audio": ("mob.goat.ambient", "mob.goat.hurt", "mob.goat.death", [0.78, 0.92], 0.82),
        "clips": ("idle", "walk", "charge_pose"), "native_lane": "creatures",
    },
    "glide_drake": {
        "display": "Glide Drake", "role": "hostile_ridge_glider", "health": 26,
        "attack": 6, "speed": 0.26, "width": 1.15, "height": 0.65,
        "flying": True, "hostile": True, "natural": True,
        "weight": 1, "herd": (1, 1), "density": 1, "light": (7, 15),
        "audio": ("mob.phantom.idle", "mob.phantom.hurt", "mob.phantom.death", [0.88, 1.0], 0.62),
        "clips": ("idle", "glide", "dive_attack"), "native_lane": "creatures",
    },
    "ropewing": {
        "display": "Ropewing", "role": "neutral_membrane_shelf_glider", "health": 16,
        "attack": 3, "speed": 0.24, "width": 0.85, "height": 0.45,
        "flying": True, "hostile": False, "natural": True,
        "weight": 1, "herd": (1, 1), "density": 1, "light": (7, 15),
        "audio": ("mob.bat.idle", "mob.bat.hurt", "mob.bat.death", [0.82, 0.98], 0.48),
        "clips": ("idle_perch", "glide", "bank"), "native_lane": "creatures",
    },
    "ruin_harpy": {
        "display": "Ruin Harpy", "role": "hostile_biped_ruin_flyer", "health": 28,
        "attack": 7, "speed": 0.25, "width": 0.85, "height": 1.35,
        "flying": True, "hostile": True, "natural": True,
        "weight": 1, "herd": (1, 1), "density": 1, "light": (0, 12),
        "audio": ("mob.phantom.idle", "mob.phantom.hurt", "mob.phantom.death", [1.02, 1.16], 0.68),
        "clips": ("idle_perch", "fly", "dive_slash"), "native_lane": "creatures",
    },
    "sky_fox": {
        "display": "Sky Fox", "role": "neutral_agile_cliff_runner", "health": 20,
        "attack": 4, "speed": 0.28, "width": 0.7, "height": 0.75,
        "flying": False, "hostile": False, "natural": True,
        "weight": 2, "herd": (1, 2), "density": 2, "light": (7, 15),
        "audio": ("mob.fox.ambient", "mob.fox.hurt", "mob.fox.death", [0.92, 1.08], 0.62),
        "clips": ("idle", "trot", "leap"), "native_lane": "creatures",
    },
    "stone_vulture": {
        "display": "Stone Vulture", "role": "neutral_ruin_scavenger_flyer", "health": 22,
        "attack": 4, "speed": 0.22, "width": 0.9, "height": 0.7,
        "flying": True, "hostile": False, "natural": True,
        "weight": 1, "herd": (1, 1), "density": 1, "light": (7, 15),
        "audio": ("mob.parrot.idle", "mob.parrot.hurt", "mob.parrot.death", [0.65, 0.78], 0.55),
        "clips": ("idle_perch", "fly", None), "native_lane": "creatures",
    },
    "storm_gull": {
        "display": "Storm Gull", "role": "ambient_shelf_scavenger_flyer", "health": 14,
        "attack": 2, "speed": 0.25, "width": 0.65, "height": 0.45,
        "flying": True, "hostile": False, "natural": True,
        "weight": 1, "herd": (1, 2), "density": 1, "light": (7, 15),
        "audio": ("mob.parrot.idle", "mob.parrot.hurt", "mob.parrot.death", [1.08, 1.22], 0.45),
        "clips": ("idle_perch", "fly", None), "native_lane": "creatures",
    },
}


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence(asset: str, cfg: dict) -> Path:
    return ROOT / f"engineering/native-assets/skyreach/{cfg['native_lane']}/evidence" / asset


def behavior_entity(asset: str, cfg: dict) -> dict:
    family = ["aionbound", "skyreach", asset, "creature"]
    if cfg["natural"]:
        family.append("hostile" if cfg["hostile"] else "neutral")
    else:
        family += ["apex", "arena_only_shell"]
    components = {
        "minecraft:type_family": {"family": family},
        "minecraft:health": {"value": cfg["health"], "max": cfg["health"]},
        "minecraft:collision_box": {"width": cfg["width"], "height": cfg["height"]},
        "minecraft:movement": {"value": cfg["speed"]},
        "minecraft:physics": {"has_gravity": not cfg["flying"]},
        "minecraft:despawn": {"despawn_from_distance": {"min_distance": 48, "max_distance": 96}},
        "minecraft:ambient_sound_interval": {"event_name": "ambient", "value": 12 if cfg["flying"] else 16, "range": 10},
        "minecraft:behavior.look_at_player": {"priority": 7, "look_distance": 10, "probability": 0.04},
        "minecraft:behavior.random_look_around": {"priority": 8},
    }
    if cfg["flying"]:
        components.update({
            "minecraft:can_fly": {},
            "minecraft:movement.fly": {},
            "minecraft:navigation.fly": {"avoid_water": True, "can_path_from_air": True},
            "minecraft:behavior.random_fly": {
                "priority": 6, "xz_dist": 10 if cfg["natural"] else 14,
                "y_dist": 5 if cfg["natural"] else 7, "y_offset": 1,
            },
        })
    else:
        components.update({
            "minecraft:movement.basic": {},
            "minecraft:navigation.walk": {
                "avoid_damage_blocks": True, "avoid_water": True,
                "can_path_over_water": False, "can_sink": True,
            },
            "minecraft:behavior.float": {"priority": 0},
            "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": 0.72, "interval": 100},
        })
    if cfg["hostile"]:
        radius = 18 if cfg["natural"] else 28
        components.update({
            "minecraft:attack": {"damage": cfg["attack"]},
            "minecraft:behavior.hurt_by_target": {"priority": 1},
            "minecraft:behavior.melee_attack": {"priority": 2, "speed_multiplier": 1.22, "track_target": True},
            "minecraft:behavior.nearest_attackable_target": {
                "priority": 3, "must_see": True, "reselect_targets": True, "within_radius": radius,
                "entity_types": [{
                    "filters": {"test": "is_family", "subject": "other", "value": "player"},
                    "max_dist": radius,
                }],
            },
        })
    else:
        components.update({
            "minecraft:attack": {"damage": cfg["attack"]},
            "minecraft:behavior.hurt_by_target": {"priority": 1},
            "minecraft:behavior.melee_attack": {"priority": 2, "speed_multiplier": 1.12, "track_target": True},
        })
    return {
        "format_version": "1.21.80",
        "minecraft:entity": {
            "description": {
                "identifier": f"aionbound:{asset}",
                "is_spawnable": cfg["natural"],
                "is_summonable": True,
            },
            "components": components,
        },
    }


def spawn_rule(asset: str, cfg: dict) -> dict:
    condition = {
        "minecraft:biome_filter": {"all_of": [
            {"test": "has_biome_tag", "operator": "==", "value": "overworld"},
            {"any_of": [
                {"test": "has_biome_tag", "operator": "==", "value": "mountain"},
                {"test": "has_biome_tag", "operator": "==", "value": "hills"},
            ]},
        ]},
        "minecraft:brightness_filter": {"min": cfg["light"][0], "max": cfg["light"][1], "adjust_for_weather": True},
        "minecraft:density_limit": {"surface": cfg["density"], "underground": 0},
        "minecraft:distance_filter": {"min": 40, "max": 96},
        "minecraft:herd": {"min_size": cfg["herd"][0], "max_size": cfg["herd"][1]},
        "minecraft:spawns_on_surface": {},
        "minecraft:weight": {"default": cfg["weight"]},
    }
    return {
        "format_version": "1.8.0",
        "minecraft:spawn_rules": {
            "description": {
                "identifier": f"aionbound:{asset}",
                "population_control": "monster" if cfg["hostile"] else "animal",
            },
            "conditions": [condition],
        },
    }


def client_entity(asset: str, clip_ids: list[str]) -> dict:
    aliases = {clip.rsplit(".", 1)[-1]: clip for clip in clip_ids}
    aliases["runtime"] = f"controller.animation.aionbound.skyreach.{asset}.runtime"
    return {
        "format_version": "1.10.0",
        "minecraft:client_entity": {"description": {
            "identifier": f"aionbound:{asset}",
            "materials": {"default": "entity_alphatest"},
            "textures": {"default": f"textures/aionbound/skyreach/entity/{asset}"},
            "geometry": {"default": f"geometry.aionbound.{asset}"},
            "animations": aliases,
            "scripts": {"animate": ["runtime"]},
            "render_controllers": [f"controller.render.aionbound.skyreach.{asset}"],
        }},
    }


def animation_controller(asset: str) -> dict:
    idle, move, action = ASSETS[asset]["clips"]
    active_transitions = [
        {"death": "!query.is_alive"}, {"hurt": "query.hurt_time > 0.0"},
    ]
    if action:
        active_transitions.append({"action": "query.has_target"})
    states = {
        "idle": {"animations": [idle], "transitions": active_transitions + [{"move": "query.is_moving"}]},
        "move": {"animations": [move], "transitions": active_transitions + [{"idle": "!query.is_moving"}]},
        "hurt": {"animations": ["hurt"], "transitions": [
            {"death": "!query.is_alive"},
            {"move": "query.hurt_time <= 0.0 && query.is_moving"},
            {"idle": "query.hurt_time <= 0.0 && !query.is_moving"},
        ]},
        "death": {"animations": ["death"]},
    }
    if action:
        states["action"] = {"animations": [action], "transitions": [
            {"death": "!query.is_alive"}, {"hurt": "query.hurt_time > 0.0"},
            {"move": "!query.has_target && query.is_moving"},
            {"idle": "!query.has_target && !query.is_moving"},
        ]}
    return {
        "format_version": "1.10.0",
        "animation_controllers": {
            f"controller.animation.aionbound.skyreach.{asset}.runtime": {
                "initial_state": "idle", "states": states,
            }
        },
    }


def render_controller(asset: str) -> dict:
    return {
        "format_version": "1.8.0",
        "render_controllers": {
            f"controller.render.aionbound.skyreach.{asset}": {
                "geometry": "Geometry.default",
                "materials": [{"*": "Material.default"}],
                "textures": ["Texture.default"],
            }
        },
    }


def update_sounds() -> None:
    path = ROOT / "resource_pack/sounds.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    entities = document.setdefault("entity_sounds", {}).setdefault("entities", {})
    for asset, cfg in ASSETS.items():
        ambient, hurt, death, pitch, volume = cfg["audio"]
        entities[f"aionbound:{asset}"] = {
            "events": {"ambient": ambient, "death": death, "hurt": hurt},
            "pitch": pitch, "volume": volume,
        }
    dump(path, document)


def build() -> dict:
    representative = json.loads(REPRESENTATIVE_REPORT.read_text(encoding="utf-8"))
    creatures = json.loads(CREATURE_REPORT.read_text(encoding="utf-8"))
    qualified = {row["asset"]: row for report in (representative, creatures) for row in report["assets"] if row["asset"] in ASSETS}
    if set(qualified) != set(ASSETS) or any(row["status"] != "PASS_NATIVE_REPAIR_GATE" for row in qualified.values()):
        raise RuntimeError("exact ten Skyreach native PASS rows are required")
    outputs: list[dict] = []
    bindings: list[dict] = []
    for asset, cfg in ASSETS.items():
        src = evidence(asset, cfg)
        sources = {
            "geometry": src / "native-exports/pass-2.geo.json",
            "animation": src / "native-exports/pass-2.animation.json",
            "texture": src / f"native-project/textures/{asset}.png",
        }
        destinations = {
            "geometry": ROOT / f"resource_pack/models/aionbound/skyreach/{asset}.geo.json",
            "animation": ROOT / f"resource_pack/animations/aionbound/skyreach/{asset}.animation.json",
            "texture": ROOT / f"resource_pack/textures/aionbound/skyreach/entity/{asset}.png",
        }
        for kind in sources:
            destinations[kind].parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(sources[kind], destinations[kind])
        clips = list(json.loads(sources["animation"].read_text(encoding="utf-8"))["animations"])
        authored = {
            ROOT / f"behavior_pack/entities/aionbound/skyreach/{asset}.entity.json": behavior_entity(asset, cfg),
            ROOT / f"resource_pack/entity/aionbound/skyreach/{asset}.entity.json": client_entity(asset, clips),
            ROOT / f"resource_pack/animation_controllers/aionbound/skyreach/{asset}.animation_controller.json": animation_controller(asset),
            ROOT / f"resource_pack/render_controllers/aionbound/skyreach/{asset}.render_controller.json": render_controller(asset),
        }
        if cfg["natural"]:
            authored[ROOT / f"behavior_pack/spawn_rules/aionbound/skyreach/{asset}.spawn_rules.json"] = spawn_rule(asset, cfg)
        for path, value in authored.items():
            dump(path, value)
        bindings.append({
            "asset": asset, "role": cfg["role"], "native_status": qualified[asset]["status"],
            "native_receipt_sha256": qualified[asset]["receipt_sha256"],
            **{f"{kind}_source_path": str(path.relative_to(ROOT)) for kind, path in sources.items()},
            **{f"{kind}_sha256": sha256(path) for kind, path in sources.items()},
            "clip_ids": clips,
        })
        for path in (*destinations.values(), *authored):
            outputs.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(path)})
    update_sounds()
    for path in (ROOT / "resource_pack/sounds.json",):
        outputs.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(path)})
    return {
        "schema": "aionbound.wave1.skyreach_entity_runtime.v2",
        "status": "SKYREACH_TEN_NATIVE_CREATURES_STATIC_RUNTIME_COMPLETE",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE},
        "completed": sorted(ASSETS),
        "natural_spawn_entities": [asset for asset, cfg in ASSETS.items() if cfg["natural"]],
        "arena_only_shell": "wind_roc",
        "withheld": [],
        "native_bindings": bindings,
        "loot_binding": "OMITTED_NO_SKYREACH_CREATURE_LOOT_TABLES_ON_EXACT_BASE",
        "localization_binding": "DEFERRED_TO_SHARED_CLOSURE_REFRESH",
        "ecology": {
            "rule_count": 9, "biome_tags": ["overworld", "mountain", "hills"],
            "max_group_size": 2, "max_surface_density_per_type": 2,
            "max_weight": 2, "distance_min": 40, "distance_max": 96,
            "aggregate_surface_density_ceiling": sum(cfg["density"] for cfg in ASSETS.values() if cfg["natural"]),
            "wind_roc_natural_spawn": False,
        },
        "outputs": sorted(outputs, key=lambda row: row["path"]),
        "proof_boundary": {
            "native_sources": "PREEXISTING_PASS_NATIVE_REPAIR_GATE",
            "bp_rp_integration": "STATIC_SOURCE_FILES_ONLY",
            "loot_economy": "DEFERRED_TO_ECONOMY_LANE",
            "storm_nest_terminal_reward_seal": "NOT_IMPLEMENTED_DEFERRED_AUTHORITY",
            "build": "NOT_RUN", "bds": "NOT_RUN", "client": "NOT_RUN",
            "multiplayer": "NOT_RUN", "console_ps4": "NOT_RUN", "release": "NOT_RUN",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=Path(__file__).with_name("SKYREACH_ENTITY_RUNTIME_REPORT.json"))
    args = parser.parse_args()
    report = build()
    dump(args.report, report)
    print(sha256(args.report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
