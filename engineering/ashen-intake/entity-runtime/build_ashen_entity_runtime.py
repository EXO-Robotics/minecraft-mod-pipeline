#!/usr/bin/env python3
"""Build deterministic Packet 002 Ashen entity BP/RP runtime shells."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE_COMMIT = "d3f162db41b06ce502dd8fc6995288d2fe546fa0"
BASE_TREE = "4843a3ad877cec4ecdd238d01867218ef9687741"

AUDIO_INTERVALS = {
    "ash_mite": (6, 8), "ember_crow": (12, 10), "magma_lizard": (10, 9),
    "furnace_beetle": (14, 10), "char_wolf": (8, 12), "cinder_lynx": (11, 12),
    "ash_ram": (12, 12), "soot_stag": (15, 14), "basalt_tortoise": (18, 10),
    "ash_drake": (8, 16),
}

ASSETS = {
    "ash_mite": dict(source="creatures", role="swarm_hostile", health=8, attack=2, speed=.27, width=.45, height=.3, movement="skitter", action="skitter", secondary=None, hostile=True, neutral=False, flying=False, weight=6, herd=(1, 2), density=2, light=(0, 10), biomes=("mountain", "mesa")),
    "ember_crow": dict(source="representative", role="ambient_air", health=10, attack=0, speed=.25, width=.55, height=.5, movement="fly", action="peck", secondary="glide", hostile=False, neutral=False, flying=True, weight=4, herd=(1, 2), density=1, light=(7, 15), biomes=("mountain",)),
    "magma_lizard": dict(source="creatures", role="small_hostile", health=14, attack=3, speed=.24, width=1.2, height=.5, movement="walk", action="lunge_bite", secondary=None, hostile=True, neutral=False, flying=False, weight=3, herd=(1, 1), density=1, light=(0, 12), biomes=("mesa", "mountain")),
    "furnace_beetle": dict(source="creatures", role="hostile", health=24, attack=5, speed=.22, width=.9, height=.7, movement="walk", action="mandible_clamp", secondary="charge", hostile=True, neutral=False, flying=False, weight=2, herd=(1, 1), density=1, light=(0, 8), biomes=("mesa",)),
    "char_wolf": dict(source="creatures", role="hostile_pack", health=28, attack=6, speed=.30, width=.85, height=.9, movement="walk", action="snarl_attack", secondary="run", hostile=True, neutral=False, flying=False, weight=2, herd=(1, 2), density=2, light=(0, 7), biomes=("mountain", "mesa")),
    "cinder_lynx": dict(source="creatures", role="elite_hunter", health=30, attack=7, speed=.31, width=.75, height=.7, movement="stalk", action="pounce_pose", secondary=None, hostile=True, neutral=False, flying=False, weight=1, herd=(1, 1), density=1, light=(0, 8), biomes=("mountain",)),
    "ash_ram": dict(source="representative", role="neutral_territorial", health=32, attack=5, speed=.24, width=1.0, height=1.2, movement="walk", action="headbutt_pose", secondary=None, hostile=False, neutral=True, flying=False, weight=2, herd=(1, 2), density=2, light=(7, 15), biomes=("mountain",)),
    "soot_stag": dict(source="creatures", role="neutral_rare", health=38, attack=6, speed=.25, width=1.0, height=1.8, movement="walk", action="antler_shake", secondary="trot", hostile=False, neutral=True, flying=False, weight=1, herd=(1, 1), density=1, light=(7, 15), biomes=("mountain", "mesa")),
    "basalt_tortoise": dict(source="creatures", role="tank_neutral", health=50, attack=7, speed=.14, width=1.2, height=.9, movement="slow_walk", action="withdraw_pose", secondary=None, hostile=False, neutral=True, flying=False, weight=1, herd=(1, 1), density=1, light=(0, 15), biomes=("mesa", "mountain")),
    "ash_drake": dict(source="representative", role="arena_only_shell", health=80, attack=8, speed=.24, width=1.4, height=1.6, movement="walk", action="bite", secondary="wing_flap_hop", hostile=True, neutral=False, flying=False, weight=None, herd=None, density=None, light=None, biomes=()),
}


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence(asset: str, cfg: dict) -> Path:
    return ROOT / "engineering/native-assets/ashen" / cfg["source"] / "evidence" / asset


def behavior_entity(asset: str, cfg: dict) -> dict:
    family = ["aionbound", "ashen", asset]
    if asset == "ash_drake":
        family += ["apex", "arena_only_shell"]
    elif cfg["hostile"]:
        family += ["monster", "hostile"]
    elif cfg["neutral"]:
        family += ["creature", "neutral"]
    else:
        family += ["creature", "ambient"]
    components = {
        "minecraft:type_family": {"family": family},
        "minecraft:health": {"value": cfg["health"], "max": cfg["health"]},
        "minecraft:loot": {"table": f"loot_tables/entities/ashen/{asset if asset != 'ash_drake' else 'ash_drake_ecology'}.json"},
        "minecraft:ambient_sound_interval": {
            "event_name": "ambient", "value": AUDIO_INTERVALS[asset][0], "range": AUDIO_INTERVALS[asset][1]
        },
        "minecraft:collision_box": {"width": cfg["width"], "height": cfg["height"]},
        "minecraft:movement": {"value": cfg["speed"]},
        "minecraft:physics": {},
        "minecraft:despawn": {"despawn_from_distance": {"min_distance": 40, "max_distance": 96}},
    }
    if cfg["flying"]:
        components.update({
            "minecraft:can_fly": {}, "minecraft:movement.fly": {},
            "minecraft:navigation.fly": {"avoid_water": True, "can_path_from_air": True},
            "minecraft:behavior.random_fly": {"priority": 5, "xz_dist": 8, "y_dist": 4, "y_offset": 1},
            "minecraft:behavior.look_at_player": {"priority": 6, "look_distance": 8, "probability": .04},
            "minecraft:behavior.random_look_around": {"priority": 7},
        })
    else:
        components.update({
            "minecraft:movement.basic": {},
            "minecraft:navigation.walk": {"avoid_damage_blocks": True, "can_path_over_water": False, "can_sink": True},
            "minecraft:behavior.float": {"priority": 0},
            "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": .75 if cfg["neutral"] else .85, "interval": 90 if cfg["neutral"] else 70},
            "minecraft:behavior.look_at_player": {"priority": 7, "look_distance": 9, "probability": .06},
            "minecraft:behavior.random_look_around": {"priority": 8},
        })
    if cfg["hostile"] or cfg["neutral"]:
        components["minecraft:attack"] = {"damage": cfg["attack"]}
        components["minecraft:behavior.hurt_by_target"] = {"priority": 1, **({"alert_same_type": True} if asset in {"ash_mite", "char_wolf"} else {})}
        components["minecraft:behavior.melee_attack"] = {"priority": 2, "speed_multiplier": 1.18 if cfg["neutral"] else 1.28, "track_target": True}
    if cfg["hostile"]:
        components["minecraft:behavior.nearest_attackable_target"] = {"priority": 3, "must_see": True, "reselect_targets": True, "within_radius": 16 if asset != "ash_drake" else 24, "entity_types": [{"filters": {"test": "is_family", "subject": "other", "value": "player"}, "max_dist": 16 if asset != "ash_drake" else 24}]}
    return {"format_version": "1.21.80", "minecraft:entity": {"description": {"identifier": f"aionbound:{asset}", "is_spawnable": asset != "ash_drake", "is_summonable": True}, "components": components}}


def spawn_rule(asset: str, cfg: dict) -> dict:
    biome_any = [{"test": "has_biome_tag", "operator": "==", "value": tag} for tag in cfg["biomes"]]
    biome_filter = {"all_of": [{"test": "has_biome_tag", "operator": "==", "value": "overworld"}, {"any_of": biome_any}]}
    condition = {
        "minecraft:biome_filter": biome_filter,
        "minecraft:brightness_filter": {"min": cfg["light"][0], "max": cfg["light"][1], "adjust_for_weather": True},
        "minecraft:density_limit": {"surface": cfg["density"], "underground": 0},
        "minecraft:distance_filter": {"min": 28, "max": 96},
        "minecraft:herd": {"min_size": cfg["herd"][0], "max_size": cfg["herd"][1]},
        "minecraft:spawns_on_surface": {},
        "minecraft:weight": {"default": cfg["weight"]},
    }
    population = "monster" if cfg["hostile"] else "animal"
    return {"format_version": "1.8.0", "minecraft:spawn_rules": {"description": {"identifier": f"aionbound:{asset}", "population_control": population}, "conditions": [condition]}}


def client_entity(asset: str, clips: list[str]) -> dict:
    aliases = {clip.rsplit(".", 1)[-1]: clip for clip in clips}
    aliases["runtime"] = f"controller.animation.aionbound.ashen.{asset}.runtime"
    return {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
        "identifier": f"aionbound:{asset}", "materials": {"default": "entity_alphatest"},
        "textures": {"default": f"textures/aionbound/ashen/entity/{asset}"},
        "geometry": {"default": f"geometry.aionbound.{asset}"}, "animations": aliases,
        "scripts": {"animate": ["runtime"]}, "render_controllers": [f"controller.render.aionbound.ashen.{asset}"]
    }}}


def animation_controller(asset: str, cfg: dict) -> dict:
    idle = "idle_perch" if asset == "ember_crow" else "idle"
    move, action, secondary = cfg["movement"], cfg["action"], cfg["secondary"]
    states = {
        "idle": {"animations": [idle], "transitions": [{"death": "!query.is_alive"}, {"hurt": "query.hurt_time > 0.0"}, {"move": "query.is_moving"}]},
        "move": {"animations": [move], "transitions": [{"death": "!query.is_alive"}, {"hurt": "query.hurt_time > 0.0"}, {"idle": "!query.is_moving"}]},
        "hurt": {"animations": ["hurt"], "transitions": [{"death": "!query.is_alive"}, {"move": "query.hurt_time <= 0.0 && query.is_moving"}, {"idle": "query.hurt_time <= 0.0 && !query.is_moving"}]},
        "death": {"animations": ["death"]},
    }
    if not cfg["flying"]:
        states["idle"]["transitions"].insert(2, {"action": "query.has_target && !query.is_moving"})
        states["move"]["transitions"].insert(2, {"action": "query.has_target && !query.is_moving"})
        states["action"] = {"animations": [action], "transitions": [{"death": "!query.is_alive"}, {"hurt": "query.hurt_time > 0.0"}, {"move": "query.any_animation_finished && query.is_moving"}, {"idle": "query.any_animation_finished && !query.is_moving"}]}
    if secondary:
        states["move"]["animations"] = [{move: "!query.has_target"}, {secondary: "query.has_target"}]
    return {"format_version": "1.10.0", "animation_controllers": {f"controller.animation.aionbound.ashen.{asset}.runtime": {"initial_state": "idle", "states": states}}}


def render_controller(asset: str) -> dict:
    return {"format_version": "1.8.0", "render_controllers": {f"controller.render.aionbound.ashen.{asset}": {"geometry": "Geometry.default", "materials": [{"*": "Material.default"}], "textures": ["Texture.default"]}}}


def build() -> dict:
    outputs: list[dict] = []
    source_evidence: list[dict] = []
    for asset, cfg in ASSETS.items():
        src = evidence(asset, cfg)
        geometry_src = src / "native-exports/pass-2.geo.json"
        animation_src = src / "native-exports/pass-2.animation.json"
        texture_src = src / f"native-project/textures/{asset}.png"
        geometry_dst = ROOT / f"resource_pack/models/aionbound/ashen/entities/{asset}.geo.json"
        animation_dst = ROOT / f"resource_pack/animations/aionbound/ashen/entities/{asset}.animation.json"
        texture_dst = ROOT / f"resource_pack/textures/aionbound/ashen/entity/{asset}.png"
        for source, destination in ((geometry_src, geometry_dst), (animation_src, animation_dst), (texture_src, texture_dst)):
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        clips = list(json.loads(animation_src.read_text())["animations"])
        authored = {
            ROOT / f"behavior_pack/entities/aionbound/ashen/{asset}.entity.json": behavior_entity(asset, cfg),
            ROOT / f"resource_pack/entity/aionbound/ashen/{asset}.entity.json": client_entity(asset, clips),
            ROOT / f"resource_pack/animation_controllers/aionbound/ashen/{asset}.animation_controller.json": animation_controller(asset, cfg),
            ROOT / f"resource_pack/render_controllers/aionbound/ashen/{asset}.render_controller.json": render_controller(asset),
        }
        if asset != "ash_drake":
            authored[ROOT / f"behavior_pack/spawn_rules/aionbound/ashen/{asset}.spawn_rules.json"] = spawn_rule(asset, cfg)
        for path, value in authored.items():
            dump(path, value)
        source_evidence.append({"asset": asset, "source_class": cfg["source"], "geometry_path": str(geometry_src.relative_to(ROOT)), "geometry_sha256": sha(geometry_src), "animation_path": str(animation_src.relative_to(ROOT)), "animation_sha256": sha(animation_src), "texture_path": str(texture_src.relative_to(ROOT)), "texture_sha256": sha(texture_src), "clip_ids": clips})
        for path in (geometry_dst, animation_dst, texture_dst, *authored):
            outputs.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path)})
    return {
        "schema": "aionbound.wave1.ashen_entity_runtime_report.v1", "status": "STATIC_RUNTIME_SHELLS_COMPLETE_UNQUALIFIED",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE},
        "scope": {"entities": sorted(ASSETS), "natural_spawn_entities": sorted(a for a in ASSETS if a != "ash_drake"), "arena_only_shell": "aionbound:ash_drake", "loot_binding": "RATIFIED_ECOLOGY_TABLES_BOUND", "boss_session_completion_rewards": "OUT_OF_SCOPE"},
        "native_binding": source_evidence,
        "ecology": {"rule_count": 9, "biome_tags": ["overworld", "mountain", "mesa"], "max_group_size": 2, "max_per_type_surface_density": 2, "max_weight": 6, "whisperwood_numbers_copied": False, "ash_drake_natural_spawn": False},
        "outputs": sorted(outputs, key=lambda x: x["path"]),
        "proof_boundary": {"json_and_reference_validation": "RUN_BY_TEST_LANE", "native_source_evidence": "PREEXISTING_PASS", "bp_rp_integration": "STATIC_FILES_ONLY", "build": "NOT_RUN", "bds": "NOT_RUN", "bedrock_client": "NOT_RUN", "multiplayer": "NOT_RUN", "console_ps4": "NOT_RUN", "marketplace_release": "NOT_RUN"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=Path(__file__).with_name("ASHEN_ENTITY_RUNTIME_REPORT.json"))
    args = parser.parse_args()
    report = build()
    dump(args.report, report)
    print(hashlib.sha256(args.report.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
