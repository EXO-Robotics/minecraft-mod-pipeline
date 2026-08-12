#!/usr/bin/env python3
"""Build the three native-qualified Skyreach creature runtime surfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE_COMMIT = "10e60dfb4ae95996286d455473612b58c234ec9b"
BASE_TREE = "57088d0df2e3ccdf4a8e463ee09d3d6fbe7bd4bf"
NATIVE_REPORT = ROOT / "engineering/native-assets/skyreach/representative/SKYREACH_REPRESENTATIVE_NATIVE_REPORT.json"

WITHHELD = [
    "cliff_ram", "glide_drake", "ropewing", "ruin_harpy", "sky_fox",
    "stone_vulture", "storm_gull",
]

ASSETS = {
    "cloud_goat": {
        "display": "Cloud Goat", "role": "neutral_ledge_grazer", "health": 24,
        "attack": 4, "speed": 0.22, "width": 0.9, "height": 1.15,
        "flying": False, "hostile": False, "natural": True,
        "weight": 2, "herd": (1, 2), "density": 2, "light": (7, 15),
        "audio": ("mob.goat.ambient", "mob.goat.hurt", "mob.goat.death", [0.9, 1.05], 0.72),
    },
    "gale_hawk": {
        "display": "Gale Hawk", "role": "hostile_aerial_patrol", "health": 18,
        "attack": 4, "speed": 0.27, "width": 0.7, "height": 0.55,
        "flying": True, "hostile": True, "natural": True,
        "weight": 1, "herd": (1, 1), "density": 1, "light": (7, 15),
        "audio": ("mob.parrot.idle", "mob.parrot.hurt", "mob.parrot.death", [0.85, 1.0], 0.55),
    },
    "wind_roc": {
        "display": "Wind Roc", "role": "arena_only_apex_soaring_shell", "health": 96,
        "attack": 9, "speed": 0.25, "width": 2.0, "height": 1.65,
        "flying": True, "hostile": True, "natural": False,
        "weight": None, "herd": None, "density": None, "light": None,
        "audio": ("mob.phantom.idle", "mob.phantom.hurt", "mob.phantom.death", [0.65, 0.78], 1.0),
    },
}


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence(asset: str) -> Path:
    return ROOT / "engineering/native-assets/skyreach/representative/evidence" / asset


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
                "priority": 6, "xz_dist": 10 if asset == "gale_hawk" else 14,
                "y_dist": 5 if asset == "gale_hawk" else 7, "y_offset": 1,
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
        radius = 18 if asset == "gale_hawk" else 28
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
            {"test": "has_biome_tag", "operator": "==", "value": "mountain"},
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
    if asset == "cloud_goat":
        idle, move, action = "idle", "walk", "hop_ledge"
    elif asset == "gale_hawk":
        idle, move, action = "idle", "fly", "stoop"
    else:
        idle, move, action = "idle_perch", "soar", "dive"
    states = {
        "idle": {"animations": [idle], "transitions": [
            {"death": "!query.is_alive"}, {"hurt": "query.hurt_time > 0.0"},
            {"action": "query.has_target"}, {"move": "query.is_moving"},
        ]},
        "move": {"animations": [move], "transitions": [
            {"death": "!query.is_alive"}, {"hurt": "query.hurt_time > 0.0"},
            {"action": "query.has_target"}, {"idle": "!query.is_moving"},
        ]},
        "action": {"animations": [action], "transitions": [
            {"death": "!query.is_alive"}, {"hurt": "query.hurt_time > 0.0"},
            {"move": "!query.has_target && query.is_moving"},
            {"idle": "!query.has_target && !query.is_moving"},
        ]},
        "hurt": {"animations": ["hurt"], "transitions": [
            {"death": "!query.is_alive"},
            {"move": "query.hurt_time <= 0.0 && query.is_moving"},
            {"idle": "query.hurt_time <= 0.0 && !query.is_moving"},
        ]},
        "death": {"animations": ["death"]},
    }
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
    native = json.loads(NATIVE_REPORT.read_text(encoding="utf-8"))
    qualified = {row["asset"]: row for row in native["assets"] if row["asset"] in ASSETS}
    if set(qualified) != set(ASSETS) or any(row["status"] != "PASS_NATIVE_REPAIR_GATE" for row in qualified.values()):
        raise RuntimeError("exact three representative native PASS rows are required")
    outputs: list[dict] = []
    bindings: list[dict] = []
    for asset, cfg in ASSETS.items():
        src = evidence(asset)
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
        "schema": "aionbound.wave1.skyreach_entity_runtime.v1",
        "status": "SKYREACH_THREE_NATIVE_CREATURES_STATIC_RUNTIME_COMPLETE",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE},
        "completed": sorted(ASSETS),
        "natural_spawn_entities": ["cloud_goat", "gale_hawk"],
        "arena_only_shell": "wind_roc",
        "withheld": [{
            "asset": asset,
            "reason": "NATIVE_REPAIR_NOT_PROVEN_ON_EXACT_BASE",
            "runtime_created": False,
        } for asset in WITHHELD],
        "native_bindings": bindings,
        "loot_binding": "OMITTED_NO_SKYREACH_CREATURE_LOOT_TABLES_ON_EXACT_BASE",
        "localization_binding": "DEFERRED_TO_SHARED_CLOSURE_REFRESH",
        "ecology": {
            "rule_count": 2, "biome_tags": ["overworld", "mountain"],
            "max_group_size": 2, "max_surface_density_per_type": 2,
            "max_weight": 2, "distance_min": 40, "distance_max": 96,
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
