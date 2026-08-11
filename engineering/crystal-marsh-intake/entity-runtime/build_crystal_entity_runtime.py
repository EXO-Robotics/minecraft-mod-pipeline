#!/usr/bin/env python3
"""Build deterministic Packet 003 Crystal Marsh creature BP/RP runtime shells."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE_COMMIT = "6a10cd8a82635299ae62ab8f6b9095c9b793c7a3"
BASE_TREE = "689fa214ae21ab9739a8b6710fdbb5bb00ebeaeb"

# Creature numbers are Crystal-specific implementation tuning. They intentionally
# do not inherit Whisperwood or Ashen ecology values.
ASSETS = {
    "prism_frog": dict(source="creatures", role="ambient_shallows", health=6, attack=0, speed=.20, width=.65, height=.45, locomotion="amphibious", idle="idle", move="hop", water_move="swim_pose", action=None, hostile=False, neutral=False, weight=5, herd=(1, 2), density=2, light=(0, 15), biomes=("swamp", "river"), placement="surface"),
    "crystal_newt": dict(source="creatures", role="ambient_bank", health=10, attack=0, speed=.18, width=.8, height=.45, locomotion="amphibious", idle="idle", move="walk", water_move=None, action=None, hostile=False, neutral=False, weight=4, herd=(1, 2), density=2, light=(0, 12), biomes=("swamp", "river"), placement="surface"),
    "crystal_dragonfly": dict(source="representative", role="ambient_air", health=6, attack=0, speed=.22, width=.55, height=.45, locomotion="flying", idle="idle_hover", move="fly", water_move=None, action=None, hostile=False, neutral=False, weight=3, herd=(1, 2), density=1, light=(7, 15), biomes=("swamp", "river"), placement="surface"),
    "bloom_crab": dict(source="creatures", role="neutral_shore", health=16, attack=3, speed=.17, width=.9, height=.5, locomotion="amphibious", idle="idle", move="scuttle", water_move=None, action="claw_snap", hostile=False, neutral=True, weight=3, herd=(1, 1), density=1, light=(0, 15), biomes=("swamp",), placement="surface"),
    "mire_turtle": dict(source="creatures", role="neutral_channel_tank", health=34, attack=4, speed=.12, width=1.1, height=.7, locomotion="amphibious", idle="idle", move="walk", water_move="swim", action="withdraw", hostile=False, neutral=True, weight=2, herd=(1, 1), density=1, light=(4, 15), biomes=("swamp", "river"), placement="surface"),
    "glass_heron": dict(source="creatures", role="neutral_rare_wader", health=24, attack=4, speed=.18, width=.75, height=2.1, locomotion="wader", idle="idle", move="walk_wade", water_move=None, action="spear_strike", hostile=False, neutral=True, weight=1, herd=(1, 1), density=1, light=(7, 15), biomes=("swamp", "river"), placement="surface"),
    "reed_serpent": dict(source="creatures", role="hostile_reed_water", health=20, attack=5, speed=.21, width=.9, height=.55, locomotion="aquatic", idle="idle_undulate", move="swim", water_move=None, action="lunge", hostile=True, neutral=False, weight=2, herd=(1, 2), density=2, light=(0, 7), biomes=("swamp", "river"), placement="underwater"),
    "silt_crocodile": dict(source="representative", role="hostile_deep_channel_elite", health=36, attack=8, speed=.19, width=1.4, height=.65, locomotion="aquatic", idle="idle_submerge", move="swim", water_move=None, action="bite", hostile=True, neutral=False, weight=1, herd=(1, 1), density=1, light=(0, 7), biomes=("swamp", "river"), placement="underwater"),
    "bog_watcher": dict(source="creatures", role="hostile_fog_ambush_elite", health=42, attack=9, speed=.16, width=1.0, height=1.25, locomotion="ground", idle="idle", move="crawl", water_move=None, action="lunge", hostile=True, neutral=False, weight=1, herd=(1, 1), density=1, light=(0, 5), biomes=("swamp",), placement="surface"),
    "marsh_wight": dict(source="representative", role="arena_only_base_shell", health=80, attack=10, speed=.18, width=.9, height=2.0, locomotion="ground", idle="idle_sway", move="drift_walk", water_move=None, action="reach_attack", hostile=True, neutral=False, weight=None, herd=None, density=None, light=None, biomes=(), placement=None),
}

AUDIO = {
    "prism_frog": dict(ambient="mob.rabbit.idle", hurt="mob.rabbit.hurt", death="mob.rabbit.death", pitch=[1.1, 1.25], volume=.45, interval=(12, 10)),
    "crystal_newt": dict(ambient="mob.rabbit.idle", hurt="mob.rabbit.hurt", death="mob.rabbit.death", pitch=[.85, 1.0], volume=.4, interval=(15, 10)),
    "crystal_dragonfly": dict(ambient="mob.spider.say", hurt="mob.spider.say", death="mob.spider.death", pitch=[1.35, 1.5], volume=.25, interval=(16, 8)),
    "bloom_crab": dict(ambient="mob.spider.say", hurt="mob.spider.say", death="mob.spider.death", pitch=[.8, .95], volume=.45, interval=(16, 10)),
    "mire_turtle": dict(ambient="mob.pig.say", hurt="mob.pig.say", death="mob.pig.death", pitch=[.55, .7], volume=.55, interval=(20, 12)),
    "glass_heron": dict(ambient="mob.rabbit.idle", hurt="mob.rabbit.hurt", death="mob.rabbit.death", pitch=[.75, .9], volume=.5, interval=(18, 12)),
    "reed_serpent": dict(ambient="mob.spider.say", hurt="mob.spider.say", death="mob.spider.death", pitch=[.65, .8], volume=.65, interval=(12, 10)),
    "silt_crocodile": dict(ambient="mob.ravager.ambient", hurt="mob.ravager.hurt", death="mob.ravager.death", pitch=[.45, .6], volume=.8, interval=(18, 12)),
    "bog_watcher": dict(ambient="mob.vex.ambient", hurt="mob.vex.hurt", death="mob.vex.death", pitch=[.55, .7], volume=.7, interval=(14, 12)),
    "marsh_wight": dict(ambient="mob.vex.ambient", hurt="mob.vex.hurt", death="mob.vex.death", pitch=[.45, .6], volume=.9, interval=(10, 14)),
}

LOOT_DEPENDENCIES = {
    "prism_frog": ["aionbound:marsh_resin", "aionbound:flood_crystal", "codex:Frog Song Stone"],
    "crystal_newt": ["aionbound:wet_chitin", "aionbound:glass_algae", "codex:Newt Tail Crystal"],
    "crystal_dragonfly": ["aionbound:prism_wing", "aionbound:flood_crystal", "codex:Dragonfly Pin"],
    "bloom_crab": ["aionbound:wet_chitin", "aionbound:prism_pearl", "aionbound:marsh_resin"],
    "mire_turtle": ["aionbound:wet_chitin", "aionbound:silt_core", "aionbound:glass_algae", "codex:Turtle Breath Stone"],
    "glass_heron": ["aionbound:flood_crystal", "codex:Heron Nest Token"],
    "reed_serpent": ["aionbound:crystal_reed_item", "aionbound:wet_chitin", "aionbound:flood_crystal"],
    "silt_crocodile": ["aionbound:wet_chitin", "aionbound:silt_core", "aionbound:prism_pearl"],
    "bog_watcher": ["aionbound:watcher_lens", "aionbound:flood_crystal", "aionbound:marsh_resin", "codex:Watcher Journal Scrap"],
    "marsh_wight": ["aionbound:wight_shroud", "aionbound:prism_pearl", "aionbound:moon_pearl", "aionbound:flood_crystal", "aionbound:crystal_root_item"],
}


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence(asset: str, cfg: dict) -> Path:
    return ROOT / "engineering/native-assets/crystal-marsh" / cfg["source"] / "evidence" / asset


def add_navigation(components: dict, cfg: dict) -> None:
    mode = cfg["locomotion"]
    if mode == "flying":
        components.update({
            "minecraft:can_fly": {},
            "minecraft:movement.fly": {},
            "minecraft:navigation.fly": {"avoid_water": False, "can_path_from_air": True},
            "minecraft:behavior.random_fly": {"priority": 5, "xz_dist": 7, "y_dist": 3, "y_offset": 1},
        })
    elif mode == "aquatic":
        components.update({
            "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0, "breathes_air": True, "breathes_water": True},
            "minecraft:movement.basic": {},
            "minecraft:navigation.swim": {"avoid_damage_blocks": True, "can_path_over_water": False, "can_sink": False, "can_swim": True, "can_walk": False},
            "minecraft:behavior.random_swim": {"priority": 5, "speed_multiplier": .75, "xz_dist": 8, "y_dist": 3, "interval": 80},
        })
    elif mode == "amphibious":
        components.update({
            "minecraft:movement.amphibious": {},
            "minecraft:navigation.generic": {"avoid_damage_blocks": True, "can_path_over_water": True, "can_sink": False, "can_swim": True, "can_walk": True, "is_amphibious": True},
            "minecraft:behavior.float": {"priority": 0},
            "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": .72, "interval": 100},
        })
    else:
        components.update({
            "minecraft:movement.basic": {},
            "minecraft:navigation.walk": {"avoid_damage_blocks": True, "can_path_over_water": False, "can_sink": mode == "wader", "can_swim": mode == "wader"},
            "minecraft:behavior.float": {"priority": 0},
            "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": .68 if mode == "wader" else .76, "interval": 110 if mode == "wader" else 90},
        })


def behavior_entity(asset: str, cfg: dict) -> dict:
    arena = asset == "marsh_wight"
    if arena:
        family = ["aionbound", "crystal_marsh", asset, "apex", "arena_only_shell", "monster", "hostile"]
    elif cfg["hostile"]:
        family = ["aionbound", "crystal_marsh", asset, "monster", "hostile"]
    elif cfg["neutral"]:
        family = ["aionbound", "crystal_marsh", asset, "creature", "neutral"]
    else:
        family = ["aionbound", "crystal_marsh", asset, "creature", "ambient"]
    sound = AUDIO[asset]
    components = {
        "minecraft:type_family": {"family": family},
        "minecraft:health": {"value": cfg["health"], "max": cfg["health"]},
        "minecraft:ambient_sound_interval": {"event_name": "ambient", "value": sound["interval"][0], "range": sound["interval"][1]},
        "minecraft:collision_box": {"width": cfg["width"], "height": cfg["height"]},
        "minecraft:movement": {"value": cfg["speed"]},
        "minecraft:physics": {"has_gravity": cfg["locomotion"] not in {"flying", "aquatic"}},
        "minecraft:despawn": {"despawn_from_distance": {"min_distance": 44, "max_distance": 96}},
        "minecraft:behavior.look_at_player": {"priority": 7, "look_distance": 8, "probability": .05},
        "minecraft:behavior.random_look_around": {"priority": 8},
    }
    add_navigation(components, cfg)
    if not cfg["hostile"] and not cfg["neutral"]:
        components["minecraft:behavior.panic"] = {"priority": 1, "speed_multiplier": 1.25}
    if cfg["hostile"] or cfg["neutral"]:
        components["minecraft:attack"] = {"damage": cfg["attack"]}
        components["minecraft:behavior.hurt_by_target"] = {"priority": 1}
        components["minecraft:behavior.melee_attack"] = {"priority": 2, "speed_multiplier": 1.12 if cfg["neutral"] else 1.22, "track_target": True}
    if cfg["hostile"]:
        radius = 24 if arena else (18 if "elite" in cfg["role"] else 14)
        components["minecraft:behavior.nearest_attackable_target"] = {
            "priority": 3,
            "must_see": asset not in {"silt_crocodile", "bog_watcher"},
            "reselect_targets": True,
            "within_radius": radius,
            "entity_types": [{"filters": {"test": "is_family", "subject": "other", "value": "player"}, "max_dist": radius}],
        }
    return {"format_version": "1.21.80", "minecraft:entity": {"description": {"identifier": f"aionbound:{asset}", "is_spawnable": not arena, "is_summonable": True}, "components": components}}


def spawn_rule(asset: str, cfg: dict) -> dict:
    biome_filter = {
        "all_of": [
            {"test": "has_biome_tag", "operator": "==", "value": "overworld"},
            {"any_of": [{"test": "has_biome_tag", "operator": "==", "value": tag} for tag in cfg["biomes"]]},
        ]
    }
    condition = {
        "minecraft:biome_filter": biome_filter,
        "minecraft:brightness_filter": {"min": cfg["light"][0], "max": cfg["light"][1], "adjust_for_weather": True},
        "minecraft:density_limit": {"surface": cfg["density"], "underground": 0},
        "minecraft:distance_filter": {"min": 32, "max": 88},
        "minecraft:herd": {"min_size": cfg["herd"][0], "max_size": cfg["herd"][1]},
        "minecraft:weight": {"default": cfg["weight"]},
        f"minecraft:spawns_{'underwater' if cfg['placement'] == 'underwater' else 'on_surface'}": {},
    }
    population = "monster" if cfg["hostile"] else ("water_animal" if cfg["placement"] == "underwater" else "animal")
    return {"format_version": "1.8.0", "minecraft:spawn_rules": {"description": {"identifier": f"aionbound:{asset}", "population_control": population}, "conditions": [condition]}}


def client_entity(asset: str, clips: list[str]) -> dict:
    aliases = {clip.rsplit(".", 1)[-1]: clip for clip in clips}
    aliases["runtime"] = f"controller.animation.aionbound.crystal_marsh.{asset}.runtime"
    return {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
        "identifier": f"aionbound:{asset}",
        "materials": {"default": "entity_alphatest"},
        "textures": {"default": f"textures/aionbound/crystal_marsh/entity/{asset}"},
        "geometry": {"default": f"geometry.aionbound.{asset}"},
        "animations": aliases,
        "scripts": {"animate": ["runtime"]},
        "render_controllers": [f"controller.render.aionbound.crystal_marsh.{asset}"],
    }}}


def animation_controller(asset: str, cfg: dict) -> dict:
    idle, move, water_move, action = cfg["idle"], cfg["move"], cfg["water_move"], cfg["action"]
    death = "death_collapse" if asset == "marsh_wight" else "death"
    move_animation = [{move: "!query.is_in_water"}, {water_move: "query.is_in_water"}] if water_move else [move]
    transitions = [{"death": "!query.is_alive"}, {"hurt": "query.hurt_time > 0.0"}]
    if action:
        transitions.append({"action": "query.has_target && !query.is_moving"})
    idle_transitions = transitions + [{"move": "query.is_moving"}]
    move_transitions = transitions + [{"idle": "!query.is_moving"}]
    states = {
        "idle": {"animations": [idle], "transitions": idle_transitions},
        "move": {"animations": move_animation, "transitions": move_transitions},
        "hurt": {"animations": ["hurt"], "transitions": [{"death": "!query.is_alive"}, {"move": "query.hurt_time <= 0.0 && query.is_moving"}, {"idle": "query.hurt_time <= 0.0 && !query.is_moving"}]},
        "death": {"animations": [death]},
    }
    if action:
        states["action"] = {"animations": [action], "transitions": [{"death": "!query.is_alive"}, {"hurt": "query.hurt_time > 0.0"}, {"move": "query.any_animation_finished && query.is_moving"}, {"idle": "query.any_animation_finished && !query.is_moving"}]}
    return {"format_version": "1.10.0", "animation_controllers": {f"controller.animation.aionbound.crystal_marsh.{asset}.runtime": {"initial_state": "idle", "states": states}}}


def render_controller(asset: str) -> dict:
    return {"format_version": "1.8.0", "render_controllers": {f"controller.render.aionbound.crystal_marsh.{asset}": {"geometry": "Geometry.default", "materials": [{"*": "Material.default"}], "textures": ["Texture.default"]}}}


def update_sounds() -> Path:
    path = ROOT / "resource_pack/sounds.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    entities = document.setdefault("entity_sounds", {}).setdefault("entities", {})
    for asset, sound in AUDIO.items():
        entities[f"aionbound:{asset}"] = {"events": {key: sound[key] for key in ("ambient", "death", "hurt")}, "pitch": sound["pitch"], "volume": sound["volume"]}
    dump(path, document)
    return path


def build() -> dict:
    outputs: list[dict] = []
    source_evidence: list[dict] = []
    for asset, cfg in ASSETS.items():
        src = evidence(asset, cfg)
        geometry_src = src / "native-exports/pass-2.geo.json"
        animation_src = src / "native-exports/pass-2.animation.json"
        texture_src = src / f"native-project/textures/{asset}.png"
        geometry_dst = ROOT / f"resource_pack/models/aionbound/crystal_marsh/entities/{asset}.geo.json"
        animation_dst = ROOT / f"resource_pack/animations/aionbound/crystal_marsh/entities/{asset}.animation.json"
        texture_dst = ROOT / f"resource_pack/textures/aionbound/crystal_marsh/entity/{asset}.png"
        for source, destination in ((geometry_src, geometry_dst), (animation_src, animation_dst), (texture_src, texture_dst)):
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        clips = list(json.loads(animation_src.read_text(encoding="utf-8"))["animations"])
        authored = {
            ROOT / f"behavior_pack/entities/aionbound/crystal_marsh/{asset}.entity.json": behavior_entity(asset, cfg),
            ROOT / f"resource_pack/entity/aionbound/crystal_marsh/{asset}.entity.json": client_entity(asset, clips),
            ROOT / f"resource_pack/animation_controllers/aionbound/crystal_marsh/{asset}.animation_controller.json": animation_controller(asset, cfg),
            ROOT / f"resource_pack/render_controllers/aionbound/crystal_marsh/{asset}.render_controller.json": render_controller(asset),
        }
        if asset != "marsh_wight":
            authored[ROOT / f"behavior_pack/spawn_rules/aionbound/crystal_marsh/{asset}.spawn_rules.json"] = spawn_rule(asset, cfg)
        for path, value in authored.items():
            dump(path, value)
        receipt = next(src.glob("*receipt.json"))
        source_evidence.append({
            "asset": asset,
            "source_class": cfg["source"],
            "receipt_path": str(receipt.relative_to(ROOT)),
            "receipt_status": json.loads(receipt.read_text(encoding="utf-8"))["status"],
            "geometry_path": str(geometry_src.relative_to(ROOT)), "geometry_sha256": sha(geometry_src),
            "animation_path": str(animation_src.relative_to(ROOT)), "animation_sha256": sha(animation_src),
            "texture_path": str(texture_src.relative_to(ROOT)), "texture_sha256": sha(texture_src),
            "clip_ids": clips,
        })
        for path in (geometry_dst, animation_dst, texture_dst, *authored):
            outputs.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path)})
    sound_path = update_sounds()
    outputs.append({"path": str(sound_path.relative_to(ROOT)), "sha256": sha(sound_path)})
    return {
        "schema": "aionbound.wave1.crystal_marsh_entity_runtime_report.v1",
        "status": "STATIC_CREATURE_RUNTIME_COMPLETE_LOOT_BINDING_PENDING_UNQUALIFIED",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE},
        "authority": {"W1-001-CM": "DIRECT_USER_APPROVAL_2026-08-11", "W1-004-CM": "DIRECT_USER_APPROVAL_2026-08-11", "W1-CREATIVE-005": "DEFERRED_UNCHANGED"},
        "scope": {
            "entities": sorted(ASSETS),
            "natural_spawn_entities": sorted(asset for asset in ASSETS if asset != "marsh_wight"),
            "arena_only_shell": "aionbound:marsh_wight",
            "marsh_wight_natural_spawn": False,
            "marsh_wight_seal_drop": False,
            "pearl_depths_session_completion_rewards": "OUT_OF_SCOPE",
            "shared_runtime_scripts": "NOT_TOUCHED",
        },
        "native_binding": source_evidence,
        "loot_binding": {
            "status": "PENDING_SEPARATE_RATIFIED_ECONOMY_TABLES",
            "minecraft_loot_components_authored": 0,
            "expected_table_paths": {asset: f"behavior_pack/loot_tables/entities/crystal/{asset}.json" for asset in sorted(ASSETS)},
            "dependencies": LOOT_DEPENDENCIES,
        },
        "audio": {"kind": "STABLE_VANILLA_PLACEHOLDER_MAPPINGS", "custom_audio_bytes": False, "entities": sorted(ASSETS)},
        "ecology": {
            "rule_count": 9,
            "biome_tags": ["overworld", "river", "swamp"],
            "water_placement_entities": ["reed_serpent", "silt_crocodile"],
            "max_group_size": 2,
            "max_per_type_surface_density": 2,
            "max_weight": 5,
            "whisperwood_numbers_copied": False,
            "ashen_numbers_copied": False,
        },
        "outputs": sorted(outputs, key=lambda row: row["path"]),
        "proof_boundary": {
            "json_and_reference_validation": "RUN_BY_TARGETED_TEST_LANE",
            "native_source_evidence": "PREEXISTING_PASS_NATIVE_REPAIR_GATE",
            "bp_rp_integration": "STATIC_FILES_ONLY",
            "loot_tables": "PENDING_SEPARATE_OWNER",
            "boss_terminal_semantics": "NOT_IMPLEMENTED",
            "build": "NOT_RUN", "bds": "NOT_RUN", "bedrock_client": "NOT_RUN", "multiplayer": "NOT_RUN", "console_ps4": "NOT_RUN", "marketplace_release": "NOT_RUN",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=Path(__file__).with_name("CRYSTAL_MARSH_ENTITY_RUNTIME_REPORT.json"))
    args = parser.parse_args()
    report = build()
    dump(args.report, report)
    print(hashlib.sha256(args.report.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
