#!/usr/bin/env python3
"""Deterministically build the original Gloamwing Stalker internal test slice."""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
import zlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "production/features/gloamwing-stalker"
ASSET = ROOT / "prototypes/blockbench/gloamwing_stalker"
RP = FEATURE / "resource_pack"
BP = FEATURE / "behavior_pack"
PACKAGES = FEATURE / "packages"
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_texture(path: Path) -> None:
    width = height = 64
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            if 20 <= x < 44 and 20 <= y < 42:
                color = (35, 81, 88, 255) if (x + y) % 5 else (68, 121, 119, 255)
            elif 25 <= x < 39 and 42 <= y < 56:
                color = (224, 152, 54, 255) if (x + y) % 3 else (255, 193, 75, 255)
            elif (x // 8 + y // 8) % 2:
                color = (31, 29, 62, 255)
            else:
                color = (45, 42, 82, 255)
            rows.extend(color)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def cube(origin: list[float], size: list[float], uv: list[int]) -> dict:
    return {"origin": origin, "size": size, "uv": uv}


def geometry() -> dict:
    bones = [
        {"name": "root", "pivot": [0, 8, 0]},
        {"name": "body", "parent": "root", "pivot": [0, 9, 0], "cubes": [
            cube([-4, 6, -6], [8, 6, 12], [0, 0]), cube([-3, 11, -4], [6, 2, 7], [0, 20])]},
        {"name": "head", "parent": "body", "pivot": [0, 10, -6], "cubes": [
            cube([-3, 7, -10], [6, 5, 5], [24, 0]), cube([-2, 6, -10.5], [4, 2, 2], [24, 12])]},
        {"name": "throat", "parent": "head", "pivot": [0, 7, -7], "cubes": [
            cube([-2, 4.5, -9], [4, 3, 3], [36, 0])]},
        {"name": "fin_left", "parent": "body", "pivot": [4, 11, -1], "cubes": [
            cube([4, 10, -4], [8, 1, 8], [0, 30]), cube([7, 9.5, 2], [5, 1, 4], [0, 40])]},
        {"name": "fin_right", "parent": "body", "pivot": [-4, 11, -1], "cubes": [
            cube([-12, 10, -4], [8, 1, 8], [0, 30]), cube([-12, 9.5, 2], [5, 1, 4], [0, 40])]},
        {"name": "legs_front", "parent": "body", "pivot": [0, 7, -4], "cubes": [
            cube([2, 1, -6], [2, 6, 2], [32, 20]), cube([-4, 1, -6], [2, 6, 2], [32, 20]),
            cube([1.5, 0, -7], [3, 1, 3], [40, 20]), cube([-4.5, 0, -7], [3, 1, 3], [40, 20])]},
        {"name": "legs_mid", "parent": "body", "pivot": [0, 7, 0], "cubes": [
            cube([3, 1, -1], [2, 6, 2], [32, 20]), cube([-5, 1, -1], [2, 6, 2], [32, 20]),
            cube([2.5, 0, -2], [3, 1, 3], [40, 20]), cube([-5.5, 0, -2], [3, 1, 3], [40, 20])]},
        {"name": "legs_rear", "parent": "body", "pivot": [0, 7, 4], "cubes": [
            cube([2, 1, 3], [2, 6, 2], [32, 20]), cube([-4, 1, 3], [2, 6, 2], [32, 20]),
            cube([1.5, 0, 3], [3, 1, 3], [40, 20]), cube([-4.5, 0, 3], [3, 1, 3], [40, 20])]},
        {"name": "tail", "parent": "body", "pivot": [0, 9, 6], "cubes": [
            cube([-1.5, 7.5, 5], [3, 3, 7], [48, 0]), cube([-1, 8, 12], [2, 2, 5], [48, 12])]},
    ]
    return {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry.ccoriginal_cc.gloamwing_stalker",
                        "texture_width": 64, "texture_height": 64,
                        "visible_bounds_width": 3.0, "visible_bounds_height": 2.0,
                        "visible_bounds_offset": [0, 1, 0]},
        "bones": bones,
    }]}


def animations() -> dict:
    prefix = "animation.ccoriginal_cc.gloamwing_stalker"
    return {"format_version": "1.8.0", "animations": {
        f"{prefix}.idle": {"loop": True, "animation_length": 4.0, "bones": {"throat": {"scale": {"0.0": [1, 1, 1], "2.0": [1.05, 1.05, 1.05], "4.0": [1, 1, 1]}}, "tail": {"rotation": {"0.0": [0, -5, 0], "2.0": [0, 5, 0], "4.0": [0, -5, 0]}}}},
        f"{prefix}.stalk": {"loop": True, "animation_length": 1.0, "bones": {"legs_front": {"rotation": {"0.0": [12, 0, 0], "0.5": [-12, 0, 0], "1.0": [12, 0, 0]}}, "legs_rear": {"rotation": {"0.0": [-12, 0, 0], "0.5": [12, 0, 0], "1.0": [-12, 0, 0]}}}},
        f"{prefix}.telegraph": {"animation_length": 0.5, "bones": {"throat": {"scale": {"0.0": [1, 1, 1], "0.5": [1.25, 1.25, 1.25]}}, "fin_left": {"rotation": [0, 0, -22]}, "fin_right": {"rotation": [0, 0, 22]}}},
        f"{prefix}.pounce": {"animation_length": 0.4, "bones": {"body": {"rotation": {"0.0": [15, 0, 0], "0.4": [-8, 0, 0]}}, "legs_front": {"rotation": [-35, 0, 0]}, "legs_rear": {"rotation": [30, 0, 0]}}},
        f"{prefix}.landing": {"animation_length": 0.7, "bones": {"body": {"position": {"0.0": [0, 0, 0], "0.15": [0, -1, 0], "0.7": [0, 0, 0]}}, "fin_left": {"rotation": {"0.0": [0, 0, -14], "0.7": [0, 0, 0]}}, "fin_right": {"rotation": {"0.0": [0, 0, 14], "0.7": [0, 0, 0]}}}},
    }}


def controller() -> dict:
    p = "animation.ccoriginal_cc.gloamwing_stalker"
    return {"format_version": "1.10.0", "animation_controllers": {
        "controller.animation.ccoriginal_cc.gloamwing_stalker": {"initial_state": "idle", "states": {
            "idle": {"animations": ["idle"], "transitions": [{"stalk": "query.modified_move_speed > 0.05"}], "blend_transition": 0.15},
            "stalk": {"animations": ["stalk"], "transitions": [{"telegraph": "query.property('ccoriginal_cc:attack_phase') == 1"}, {"idle": "query.modified_move_speed <= 0.05"}], "blend_transition": 0.1},
            "telegraph": {"animations": ["telegraph"], "transitions": [{"pounce": "query.property('ccoriginal_cc:attack_phase') == 2"}]},
            "pounce": {"animations": ["pounce"], "transitions": [{"landing": "query.property('ccoriginal_cc:attack_phase') == 3"}]},
            "landing": {"animations": ["landing"], "transitions": [{"idle": "query.property('ccoriginal_cc:attack_phase') == 0"}]},
        }}
    }}


def behavior_entity() -> dict:
    return {"format_version": "1.20.50", "minecraft:entity": {
        "description": {"identifier": "ccoriginal_cc:gloamwing_stalker", "is_spawnable": True,
                        "is_summonable": True, "is_experimental": False,
                        "properties": {"ccoriginal_cc:attack_phase": {"type": "int", "range": [0, 3], "default": 0, "client_sync": True}}},
        "component_groups": {
            "ccoriginal_cc:ready": {
                "minecraft:environment_sensor": {
                    "triggers": [{
                        "filters": {
                            "all_of": [
                                {"test": "has_target", "subject": "self", "value": True},
                                {"test": "distance_to_nearest_player", "subject": "self", "operator": "<=", "value": 16}
                            ]
                        },
                        "event": "ccoriginal_cc:begin_telegraph"
                    }]
                }
            },
            "ccoriginal_cc:telegraph": {"minecraft:movement": {"value": 0.0}, "minecraft:timer": {"time": 0.5, "looping": False, "time_down_event": {"event": "ccoriginal_cc:pounce"}}},
            "ccoriginal_cc:pounce": {"minecraft:movement": {"value": 0.42}, "minecraft:behavior.leap_at_target": {"priority": 1, "yd": 0.35, "must_be_on_ground": True}, "minecraft:timer": {"time": 0.4, "looping": False, "time_down_event": {"event": "ccoriginal_cc:land"}}},
            "ccoriginal_cc:recovery": {"minecraft:movement": {"value": 0.08}, "minecraft:timer": {"time": 0.7, "looping": False, "time_down_event": {"event": "ccoriginal_cc:begin_cooldown"}}},
            "ccoriginal_cc:cooldown": {"minecraft:movement": {"value": 0.14}, "minecraft:timer": {"time": [4.0, 7.0], "looping": False, "time_down_event": {"event": "ccoriginal_cc:arm"}}},
            "ccoriginal_cc:damage_reaction": {"minecraft:timer": {"time": 0.2, "looping": False, "time_down_event": {"event": "ccoriginal_cc:reset"}}},
            "ccoriginal_cc:death_state": {"minecraft:movement": {"value": 0.0}},
        },
        "components": {
            "minecraft:type_family": {"family": ["ccoriginal_cc:gloamwing", "monster", "mob"]},
            "minecraft:health": {"value": 24, "max": 24}, "minecraft:attack": {"damage": 4},
            "minecraft:collision_box": {"width": 1.2, "height": 0.9}, "minecraft:physics": {},
            "minecraft:movement": {"value": 0.18}, "minecraft:movement.basic": {},
            "minecraft:navigation.walk": {"can_path_over_water": False, "avoid_water": True, "can_open_doors": False},
            "minecraft:follow_range": {"value": 16, "max": 16},
            "minecraft:loot": {"table": "loot_tables/ccoriginal_cc/entities/gloamwing_stalker.json"},
            "minecraft:behavior.nearest_attackable_target": {"priority": 2, "must_see": True, "reselect_targets": True, "within_radius": 16, "entity_types": [{"filters": {"test": "is_family", "subject": "other", "value": "player"}, "max_dist": 16}]},
            "minecraft:behavior.melee_attack": {"priority": 3, "speed_multiplier": 1.0, "track_target": True, "reach_multiplier": 1.4, "cooldown_time": 1.2},
            "minecraft:behavior.random_stroll": {"priority": 8, "speed_multiplier": 0.6, "interval": 80},
            "minecraft:behavior.look_at_player": {"priority": 9, "look_distance": 8, "probability": 0.05},
            "minecraft:behavior.random_look_around": {"priority": 10},
        },
        "events": {
            "minecraft:entity_spawned": {"set_property": {"ccoriginal_cc:attack_phase": 0}, "add": {"component_groups": ["ccoriginal_cc:ready"]}},
            "ccoriginal_cc:begin_telegraph": {"set_property": {"ccoriginal_cc:attack_phase": 1}, "remove": {"component_groups": ["ccoriginal_cc:ready", "ccoriginal_cc:cooldown"]}, "add": {"component_groups": ["ccoriginal_cc:telegraph"]}},
            "ccoriginal_cc:pounce": {"set_property": {"ccoriginal_cc:attack_phase": 2}, "remove": {"component_groups": ["ccoriginal_cc:telegraph"]}, "add": {"component_groups": ["ccoriginal_cc:pounce"]}},
            "ccoriginal_cc:land": {"set_property": {"ccoriginal_cc:attack_phase": 3}, "remove": {"component_groups": ["ccoriginal_cc:pounce"]}, "add": {"component_groups": ["ccoriginal_cc:recovery"]}},
            "ccoriginal_cc:begin_cooldown": {"set_property": {"ccoriginal_cc:attack_phase": 0}, "remove": {"component_groups": ["ccoriginal_cc:ready", "ccoriginal_cc:telegraph", "ccoriginal_cc:pounce", "ccoriginal_cc:recovery", "ccoriginal_cc:damage_reaction"]}, "add": {"component_groups": ["ccoriginal_cc:cooldown"]}},
            "ccoriginal_cc:arm": {"set_property": {"ccoriginal_cc:attack_phase": 0}, "remove": {"component_groups": ["ccoriginal_cc:cooldown"]}, "add": {"component_groups": ["ccoriginal_cc:ready"]}},
            "ccoriginal_cc:reset": {"set_property": {"ccoriginal_cc:attack_phase": 0}, "remove": {"component_groups": ["ccoriginal_cc:ready", "ccoriginal_cc:telegraph", "ccoriginal_cc:pounce", "ccoriginal_cc:recovery", "ccoriginal_cc:damage_reaction"]}, "add": {"component_groups": ["ccoriginal_cc:cooldown"]}},
            "ccoriginal_cc:on_damage": {"add": {"component_groups": ["ccoriginal_cc:damage_reaction"]}},
            "ccoriginal_cc:on_death": {"add": {"component_groups": ["ccoriginal_cc:death_state"]}},
        },
    }}


def bbmodel(geo: dict, anim: dict) -> dict:
    # Controlled editable source mirroring the native export; GUI round-trip remains an explicit owner gate.
    return {"meta": {"format_version": "4.10", "model_format": "bedrock", "box_uv": True},
            "name": "Gloamwing Stalker", "model_identifier": "ccoriginal_cc:gloamwing_stalker",
            "resolution": {"width": 64, "height": 64},
            "bedrock_geometry_source": geo, "animations": anim["animations"],
            "provenance": "Original deterministic production authored for this repository; no third-party expression."}


def zip_tree(output: Path, roots: list[tuple[Path, str]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        files = [(p, f"{prefix}/{p.relative_to(root).as_posix()}") for root, prefix in roots for p in root.rglob("*") if p.is_file()]
        for source, name in sorted(files, key=lambda item: item[1]):
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    geo, anim, ctrl = geometry(), animations(), controller()
    write_json(ASSET / "gloamwing_stalker.geo.json", geo)
    write_json(ASSET / "gloamwing_stalker.bbmodel", bbmodel(geo, anim))
    write_texture(ASSET / "gloamwing_stalker.png")
    write_json(RP / "models/entity/gloamwing_stalker.geo.json", geo)
    write_json(RP / "animations/gloamwing_stalker.animation.json", anim)
    write_json(RP / "animation_controllers/gloamwing_stalker.animation_controllers.json", ctrl)
    write_texture(RP / "textures/ccoriginal_cc/entity/gloamwing_stalker.png")
    write_json(RP / "render_controllers/gloamwing_stalker.render_controllers.json", {"format_version": "1.8.0", "render_controllers": {"controller.render.ccoriginal_cc.gloamwing_stalker": {"geometry": "Geometry.default", "materials": [{"*": "Material.default"}], "textures": ["Texture.default"]}}})
    write_json(RP / "entity/gloamwing_stalker.entity.json", {"format_version": "1.10.0", "minecraft:client_entity": {"description": {"identifier": "ccoriginal_cc:gloamwing_stalker", "materials": {"default": "entity_alphatest"}, "textures": {"default": "textures/ccoriginal_cc/entity/gloamwing_stalker"}, "geometry": {"default": "geometry.ccoriginal_cc.gloamwing_stalker"}, "animations": {"idle": "animation.ccoriginal_cc.gloamwing_stalker.idle", "stalk": "animation.ccoriginal_cc.gloamwing_stalker.stalk", "telegraph": "animation.ccoriginal_cc.gloamwing_stalker.telegraph", "pounce": "animation.ccoriginal_cc.gloamwing_stalker.pounce", "landing": "animation.ccoriginal_cc.gloamwing_stalker.landing", "controller": "controller.animation.ccoriginal_cc.gloamwing_stalker"}, "scripts": {"animate": ["controller"]}, "render_controllers": ["controller.render.ccoriginal_cc.gloamwing_stalker"], "spawn_egg": {"base_color": "#23213F", "overlay_color": "#E09836"}}}})
    write_json(RP / "manifest.json", {"format_version": 2, "header": {"name": "Gloamwing Stalker RP (Internal)", "description": "Original internal-test resource pack", "uuid": "3a750a45-d232-4a26-aef0-4844df456d74", "version": [1, 0, 0], "min_engine_version": [1, 20, 50], "pack_scope": "world"}, "modules": [{"type": "resources", "uuid": "b503a43d-5d18-4147-8958-bd948d2d73b4", "version": [1, 0, 0]}]})
    write_json(BP / "entities/gloamwing_stalker.json", behavior_entity())
    write_json(BP / "loot_tables/ccoriginal_cc/entities/gloamwing_stalker.json", {"pools": [{"rolls": 1, "entries": [{"type": "item", "name": "minecraft:phantom_membrane", "weight": 1, "functions": [{"function": "set_count", "count": {"min": 0, "max": 1}}]}, {"type": "item", "name": "minecraft:string", "weight": 3, "functions": [{"function": "set_count", "count": {"min": 0, "max": 2}}]}]}]})
    write_json(BP / "spawn_rules/gloamwing_stalker.json", {"format_version": "1.8.0", "minecraft:spawn_rules": {"description": {"identifier": "ccoriginal_cc:gloamwing_stalker", "population_control": "monster"}, "conditions": []}, "_ccoriginal_cc": {"natural_spawn_enabled": False, "qualification_required": "server_stress_20"}})
    function_dir = BP / "functions/ccoriginal_cc/gloamwing"
    function_dir.mkdir(parents=True, exist_ok=True)
    (function_dir / "summon.mcfunction").write_text("summon ccoriginal_cc:gloamwing_stalker ~ ~1 ~ ccoriginal_cc:gloamwing_test\n", encoding="utf-8")
    summons = [f"summon ccoriginal_cc:gloamwing_stalker ~{(i % 5) * 2} ~1 ~{(i // 5) * 2} ccoriginal_cc:gloamwing_test" for i in range(20)]
    (function_dir / "stress_20.mcfunction").write_text("\n".join(summons) + "\n", encoding="utf-8")
    (function_dir / "cleanup.mcfunction").write_text("kill @e[type=ccoriginal_cc:gloamwing_stalker,tag=ccoriginal_cc:gloamwing_test]\n", encoding="utf-8")
    write_json(BP / "manifest.json", {"format_version": 2, "header": {"name": "Gloamwing Stalker BP (Internal)", "description": "Original internal-test behavior pack", "uuid": "e2b0816e-74ed-4457-a8af-a9eb889ecbcb", "version": [1, 0, 0], "min_engine_version": [1, 20, 50]}, "modules": [{"type": "data", "uuid": "00f4fc42-7b63-4860-bcd2-06d31724130c", "version": [1, 0, 0]}], "dependencies": [{"uuid": "3a750a45-d232-4a26-aef0-4844df456d74", "version": [1, 0, 0]}]})
    write_json(FEATURE / "asset-brief.json", {"asset_class": "entity", "asset_id": "ccoriginal_cc:gloamwing_stalker", "role": "Escalating nocturnal regional threat", "shape_grammar": "Low six-limbed glider, leaf-shaped shoulder fins, lantern throat, short tail", "palette": ["deep indigo", "desaturated teal", "warm amber", "pale claws"], "budgets": {"bones": 10, "cubes": 23, "texture": [64, 64], "clips": 5, "controllers": 1, "entities": 20}, "provenance": "Original repository authorship from consumer-safe production contract only."})
    write_json(FEATURE / "reports/readiness-matrix.json", {"STATIC": "PASSED", "BLOCKBENCH_NATIVE_ROUNDTRIP": "PENDING_MAIN_CODEX_GUI", "CREATOR_TOOLS": "PENDING", "STABLE_BDS": "PENDING_MAIN_CODEX", "BEDROCK_DESKTOP": "PENDING", "MULTIPLAYER": "PENDING", "PHYSICAL_PS4": "PENDING", "MARKETPLACE": "NOT_SUBMITTED"})
    zip_tree(PACKAGES / "gloamwing_stalker.mcaddon", [(BP, "behavior_pack"), (RP, "resource_pack")])
    hashes = {"mcaddon": sha(PACKAGES / "gloamwing_stalker.mcaddon"), "bbmodel": sha(ASSET / "gloamwing_stalker.bbmodel"), "geometry": sha(ASSET / "gloamwing_stalker.geo.json"), "texture": sha(ASSET / "gloamwing_stalker.png")}
    write_json(FEATURE / "reports/build-report.json", {"status": "STATIC_CANDIDATE", "hashes": hashes, "counts": {"bones": 10, "cubes": 23, "clips": 5, "controllers": 1, "stress_entities": 20, "attack_state_groups": 5}, "attack_cycle": {"initial_trigger": "minecraft:entity_spawned -> ready environment sensor", "telegraph_seconds": 0.5, "pounce_seconds": 0.4, "recovery_seconds": 0.7, "cooldown_seconds": [4.0, 7.0], "timer_stacking_prevented": True}, "labels": {"ps4_verified": False, "marketplace_approved": False}})
    write_json(FEATURE / "reports/revision-history.json", {
        "schema_version": "1.0.0",
        "revisions": [
            {
                "revision": 1,
                "implementation_commit": "e86d4ed1f99676a5bf8660a9bd2864f3aa0d46a9",
                "package_sha256": "385de156c907dcc9f225103d7262c21bf1bea791e2510ed60d5cc5104060035e",
                "disposition": "REVISE",
                "finding": "Telegraph entry event was unreachable and no 4-7 second cooldown existed."
            },
            {
                "revision": 2,
                "package_sha256": hashes["mcaddon"],
                "disposition": "READY_FOR_MAIN_CODEX_REVIEW",
                "changes": [
                    "Added spawn-armed target sensor",
                    "Made all attack-cycle groups mutually exclusive through explicit remove/add transitions",
                    "Added randomized non-looping 4-7 second cooldown before re-arm",
                    "Added structural event and component-group reachability test"
                ]
            }
        ]
    })
    return hashes


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
