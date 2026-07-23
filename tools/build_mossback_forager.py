#!/usr/bin/env python3
"""Deterministically build the original Mossback Forager internal-test slice."""
from __future__ import annotations

import hashlib
import base64
import json
import shutil
import struct
import zlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "production/features/mossback-forager"
PROTO = ROOT / "prototypes/blockbench/mossback_forager"
EPOCH = (1980, 1, 1, 0, 0, 0)
ASSIGNED_WORKTREE = "/Users/blakegrove/Desktop/bedrock-server/.derivedData/worktrees/parallel-batch-1/mossback-forager"
BLOCKBENCH_PROJECT_ZLIB_BASE64 = (
    "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"
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def png(path: Path) -> None:
    palette = {
        (0, 0): (65, 43, 29, 255), (1, 0): (103, 68, 42, 255),
        (2, 0): (55, 92, 48, 255), (3, 0): (82, 126, 61, 255),
        (4, 0): (225, 215, 166, 255), (5, 0): (43, 28, 25, 255),
    }
    rows = []
    for y in range(64):
        row = bytearray([0])
        for x in range(64):
            band = (x // 10 + y // 13) % 6
            rgba = palette.get((band, 0), (103, 68, 42, 255))
            row.extend(rgba)
        rows.append(bytes(row))
    raw = b"".join(rows)
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 64, 64, 8, 6, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def cube(origin, size, uv):
    return {"origin": origin, "size": size, "uv": uv}


def geometry() -> dict:
    bones = [
        {"name": "root", "pivot": [0, 0, 0]},
        {"name": "body", "parent": "root", "pivot": [0, 9, 0], "cubes": [
            cube([-6, 5, -8], [12, 7, 15], [0, 0]), cube([-5, 10, -5], [10, 3, 10], [0, 23]),
            cube([-5, 12, -4], [6, 2, 7], [22, 24]), cube([0, 12, -2], [5, 3, 6], [22, 33]),
            cube([-3, 13, 1], [6, 2, 5], [0, 36])]},
        {"name": "head", "parent": "body", "pivot": [0, 9, -7], "cubes": [
            cube([-4, 6, -12], [8, 6, 5], [32, 0]), cube([-2, 6, -14], [4, 3, 3], [32, 12]),
            cube([-1, 7, -15], [2, 2, 1], [46, 12]), cube([-4, 11, -11], [2, 2, 1], [52, 0]),
            cube([2, 11, -11], [2, 2, 1], [52, 3])]},
        {"name": "mushrooms", "parent": "body", "pivot": [-3, 14, 0], "cubes": [
            cube([-4, 13, -1], [1, 3, 1], [48, 20]), cube([-5, 15, -2], [3, 1, 3], [52, 20])]},
        {"name": "leg_front_left", "parent": "body", "pivot": [4, 6, -5], "cubes": [cube([3, 1, -6], [3, 6, 3], [0, 44])]},
        {"name": "leg_front_right", "parent": "body", "pivot": [-4, 6, -5], "cubes": [cube([-6, 1, -6], [3, 6, 3], [12, 44])]},
        {"name": "leg_rear_left", "parent": "body", "pivot": [4, 6, 4], "cubes": [cube([3, 1, 3], [3, 6, 3], [24, 44])]},
        {"name": "leg_rear_right", "parent": "body", "pivot": [-4, 6, 4], "cubes": [cube([-6, 1, 3], [3, 6, 3], [36, 44])]},
        {"name": "tail", "parent": "body", "pivot": [0, 9, 7], "cubes": [
            {**cube([-1, 8, 6], [2, 2, 6], [48, 44]), "pivot": [0, 9, 7], "rotation": [24, 0, 0]},
            cube([-1, 11, 10], [2, 4, 2], [56, 44])],
         "locators": {"gift": [0, 7, -13]}},
    ]
    return {"format_version": "1.12.0", "minecraft:geometry": [{"description": {
        "identifier": "geometry.ccoriginal_cc.mossback_forager", "texture_width": 64, "texture_height": 64,
        "visible_bounds_width": 2.2, "visible_bounds_height": 2.0, "visible_bounds_offset": [0, 0.8, 0]},
        "bones": bones}]}


def animations() -> dict:
    return {"format_version": "1.8.0", "animations": {
        "animation.ccoriginal_cc.mossback_forager.idle": {"loop": True, "animation_length": 4.0, "bones": {
            "head": {"rotation": {"0.0": [0, -6, 0], "2.0": [3, 7, 0], "4.0": [0, -6, 0]}},
            "tail": {"rotation": {"0.0": [0, 0, -5], "2.0": [0, 0, 5], "4.0": [0, 0, -5]}}}},
        "animation.ccoriginal_cc.mossback_forager.walk": {"loop": True, "animation_length": 1.0, "bones": {
            "leg_front_left": {"rotation": {"0.0": [18, 0, 0], "0.5": [-18, 0, 0], "1.0": [18, 0, 0]}},
            "leg_front_right": {"rotation": {"0.0": [-18, 0, 0], "0.5": [18, 0, 0], "1.0": [-18, 0, 0]}},
            "leg_rear_left": {"rotation": {"0.0": [-15, 0, 0], "0.5": [15, 0, 0], "1.0": [-15, 0, 0]}},
            "leg_rear_right": {"rotation": {"0.0": [15, 0, 0], "0.5": [-15, 0, 0], "1.0": [15, 0, 0]}}}},
        "animation.ccoriginal_cc.mossback_forager.forage": {"loop": False, "animation_length": 1.2, "bones": {
            "head": {"rotation": {"0.0": [0, 0, 0], "0.35": [34, 0, 0], "0.75": [26, 8, 0], "1.2": [0, 0, 0]}}}},
        "animation.ccoriginal_cc.mossback_forager.flee": {"loop": True, "animation_length": 0.6, "bones": {
            "body": {"position": {"0.0": [0, 0, 0], "0.3": [0, 0.6, 0], "0.6": [0, 0, 0]}},
            "tail": {"rotation": [28, 0, 0]}}},
    }}


def behavior() -> dict:
    ready_interact = {"minecraft:interact": {"interactions": [{
        "interact_text": "action.interact.feed", "use_item": True, "hurt_item": 0,
        "on_interact": {"filters": {"test": "has_equipment", "subject": "other", "domain": "hand",
                                    "value": "minecraft:sweet_berries"},
                        "event": "ccoriginal_cc:accept_berry", "target": "self"}}]}}
    return {"format_version": "1.21.90", "minecraft:entity": {
        "description": {"identifier": "ccoriginal_cc:mossback_forager", "is_spawnable": False, "is_summonable": True,
                        "properties": {"ccoriginal_cc:mossback_cooling": {"type": "bool", "default": False, "client_sync": True}}},
        "component_groups": {
            "ccoriginal_cc:ready": ready_interact,
            "ccoriginal_cc:cooling": {"minecraft:timer": {"looping": False, "time": 45.0,
                "time_down_event": {"event": "ccoriginal_cc:cooldown_complete", "target": "self"}}},
            "ccoriginal_cc:fleeing": {
                "minecraft:behavior.panic": {"priority": 1, "speed_multiplier": 1.45,
                    "force": True, "prefer_water": False},
                "minecraft:timer": {"looping": False, "time": 5.0,
                    "time_down_event": {"event": "ccoriginal_cc:end_flee", "target": "self"}}},
        },
        "components": {
            "minecraft:type_family": {"family": ["mossback", "ccoriginal_cc:mossback"]},
            "minecraft:health": {"value": 18, "max": 18}, "minecraft:movement": {"value": 0.18},
            "minecraft:movement.basic": {}, "minecraft:navigation.walk": {"avoid_water": True,
                "can_path_over_water": False, "can_pass_doors": False, "can_open_doors": False},
            "minecraft:collision_box": {"width": 0.9, "height": 0.9}, "minecraft:physics": {},
            "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
            "minecraft:behavior.float": {"priority": 0},
            "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": 0.75, "xz_dist": 8, "y_dist": 3,
                                                  "interval": 100},
            "minecraft:behavior.look_at_player": {"priority": 7, "look_distance": 8, "probability": 0.025},
            "minecraft:behavior.random_look_around": {"priority": 8},
            "minecraft:loot": {"table": "loot_tables/ccoriginal_cc/entities/mossback_forager_death.json"},
        },
        "events": {
            "minecraft:entity_spawned": {"add": {"component_groups": ["ccoriginal_cc:ready"]}},
            "ccoriginal_cc:accept_berry": {"sequence": [
                {"remove": {"component_groups": ["ccoriginal_cc:ready"]}},
                {"set_property": {"ccoriginal_cc:mossback_cooling": True}},
                {"spawn_loot": {"table": "loot_tables/ccoriginal_cc/entities/mossback_forager_gift.json"}},
                {"add": {"component_groups": ["ccoriginal_cc:cooling"]}}]},
            "ccoriginal_cc:cooldown_complete": {"sequence": [
                {"remove": {"component_groups": ["ccoriginal_cc:cooling"]}},
                {"set_property": {"ccoriginal_cc:mossback_cooling": False}},
                {"add": {"component_groups": ["ccoriginal_cc:ready"]}}]},
            "minecraft:entity_hurt": {"add": {"component_groups": ["ccoriginal_cc:fleeing"]}},
            "ccoriginal_cc:end_flee": {"remove": {"component_groups": ["ccoriginal_cc:fleeing"]}},
        }}}


def zip_tree(destination: Path, entries: list[tuple[Path, str]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, name in sorted(entries, key=lambda item: item[1]):
            info = zipfile.ZipInfo(name, EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())


def build() -> None:
    if FEATURE.exists():
        shutil.rmtree(FEATURE)
    if PROTO.exists():
        shutil.rmtree(PROTO)
    rp = FEATURE / "bedrock/resource_pack"
    bp = FEATURE / "bedrock/behavior_pack"
    geo, anim = geometry(), animations()
    controller = {"format_version": "1.10.0", "animation_controllers": {
        "controller.animation.ccoriginal_cc.mossback_forager": {"initial_state": "idle", "states": {
            "idle": {"animations": ["idle"], "transitions": [{"walk": "query.modified_move_speed > 0.05"},
                                                              {"forage": "query.property('ccoriginal_cc:mossback_cooling')"}]},
            "walk": {"animations": ["walk"], "blend_transition": 0.12,
                     "transitions": [{"forage": "query.property('ccoriginal_cc:mossback_cooling')"},
                                     {"idle": "query.modified_move_speed <= 0.05"}]},
            "forage": {"animations": ["forage"], "blend_transition": 0.08,
                       "transitions": [{"flee": "query.hurt_time > 0"},
                                       {"cooling_idle": "query.any_animation_finished"}]},
            "cooling_idle": {"animations": ["idle"], "blend_transition": 0.1,
                             "transitions": [{"flee": "query.hurt_time > 0"},
                                             {"idle": "!query.property('ccoriginal_cc:mossback_cooling')"}]},
            "flee": {"animations": ["flee"], "transitions": [
                {"cooling_idle": "query.hurt_time <= 0 && query.property('ccoriginal_cc:mossback_cooling')"},
                {"idle": "query.hurt_time <= 0 && !query.property('ccoriginal_cc:mossback_cooling')"}]}}}}}
    client = {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
        "identifier": "ccoriginal_cc:mossback_forager", "materials": {"default": "entity_alphatest"},
        "textures": {"default": "textures/ccoriginal_cc/entity/mossback_forager"},
        "geometry": {"default": "geometry.ccoriginal_cc.mossback_forager"},
        "animations": {"idle": "animation.ccoriginal_cc.mossback_forager.idle",
                       "walk": "animation.ccoriginal_cc.mossback_forager.walk",
                       "forage": "animation.ccoriginal_cc.mossback_forager.forage",
                       "flee": "animation.ccoriginal_cc.mossback_forager.flee",
                       "controller": "controller.animation.ccoriginal_cc.mossback_forager"},
        "scripts": {"animate": ["controller"]}, "render_controllers": ["controller.render.default"],
        "spawn_egg": {"base_color": "#67442A", "overlay_color": "#527E3D"}}}}
    write_json(rp / "models/entity/mossback_forager.geo.json", geo)
    write_json(rp / "animations/mossback_forager.animation.json", anim)
    write_json(rp / "animation_controllers/mossback_forager.controller.json", controller)
    write_json(rp / "entity/mossback_forager.entity.json", client)
    png(rp / "textures/ccoriginal_cc/entity/mossback_forager.png")
    write_text(rp / "texts/en_US.lang", "entity.ccoriginal_cc:mossback_forager.name=Mossback Forager\n")
    write_json(rp / "texts/languages.json", ["en_US"])
    write_json(rp / "manifest.json", {"format_version": 2, "header": {
        "name": "Mossback Forager INTERNAL TEST RP",
        "description": "ORIGINAL INTERNAL TEST; NOT MARKETPLACE APPROVED; NOT PHYSICAL PS4 CERTIFIED",
        "uuid": "698f7eac-f081-49f9-8e82-1e0f362d704d", "version": [1, 0, 0],
        "min_engine_version": [1, 21, 90], "pack_scope": "world"},
        "modules": [{"type": "resources", "uuid": "d25ac1b1-2d66-475c-bc0a-c5f33620fbb2", "version": [1, 0, 0]}],
        "dependencies": [{"uuid": "6a67bb25-2953-4be9-9b32-611cf09be04a", "version": [1, 0, 0]}]})
    write_json(bp / "entities/mossback_forager.json", behavior())
    gift = {"pools": [{"rolls": 1, "entries": [{"type": "item", "name": "minecraft:stick", "weight": 2},
                                                {"type": "item", "name": "minecraft:brown_mushroom", "weight": 2},
                                                {"type": "item", "name": "minecraft:clay_ball", "weight": 1}]}]}
    death = {"pools": [{"rolls": 1, "entries": [{"type": "item", "name": "minecraft:stick",
                                                 "functions": [{"function": "set_count", "count": {"min": 0, "max": 2}}]}]}]}
    write_json(bp / "loot_tables/ccoriginal_cc/entities/mossback_forager_gift.json", gift)
    write_json(bp / "loot_tables/ccoriginal_cc/entities/mossback_forager_death.json", death)
    write_json(bp / "spawn_rules/mossback_forager.disabled.json", {"format_version": "1.8.0",
        "minecraft:spawn_rules": {"description": {"identifier": "ccoriginal_cc:mossback_forager",
        "population_control": "animal", "conditions": []}}})
    write_json(bp / "manifest.json", {"format_version": 2, "header": {
        "name": "Mossback Forager INTERNAL TEST BP",
        "description": "ORIGINAL INTERNAL TEST; NATURAL SPAWN DISABLED; NOT FOR PUBLIC RELEASE",
        "uuid": "6a67bb25-2953-4be9-9b32-611cf09be04a", "version": [1, 0, 0],
        "min_engine_version": [1, 21, 90]},
        "modules": [{"type": "data", "uuid": "73f807d7-55f1-479e-92b7-017aaba56863", "version": [1, 0, 0]}],
        "dependencies": [{"uuid": "698f7eac-f081-49f9-8e82-1e0f362d704d", "version": [1, 0, 0]}]})
    base = "functions/ccoriginal_cc/mossback"
    def summon_lines(count: int) -> str:
        return "".join(
            f"summon ccoriginal_cc:mossback_forager ~{i % 5} ~ ~{i // 5}\n"
            f"tag @e[type=ccoriginal_cc:mossback_forager,r=2,c=1] add ccoriginal_cc:mossback_test\n"
            for i in range(count)
        )
    write_text(bp / f"{base}/summon.mcfunction", summon_lines(1))
    write_text(bp / f"{base}/stress_1.mcfunction", summon_lines(1))
    write_text(bp / f"{base}/stress_10.mcfunction", summon_lines(10))
    write_text(bp / f"{base}/stress_20.mcfunction", summon_lines(20))
    write_text(bp / f"{base}/cleanup.mcfunction", "kill @e[type=ccoriginal_cc:mossback_forager,tag=ccoriginal_cc:mossback_test]\n")
    # Exact native project serialized during the authoritative Blockbench GUI round-trip.
    bbmodel = zlib.decompress(base64.b64decode(BLOCKBENCH_PROJECT_ZLIB_BASE64))
    (PROTO / "mossback_forager.bbmodel").parent.mkdir(parents=True, exist_ok=True)
    (PROTO / "mossback_forager.bbmodel").write_bytes(bbmodel)
    write_json(PROTO / "native-export/mossback_forager.geo.json", geo)
    write_json(PROTO / "native-export/mossback_forager.animation.json", anim)
    png(PROTO / "mossback_forager.png")
    write_json(PROTO / "asset-brief.json", {"asset_class": "entity", "name": "Mossback Forager",
        "namespace": "ccoriginal_cc", "silhouette": "Squat root-nosed quadruped with uneven shelf pads and curled twig tail",
        "texture": [64, 64], "provenance": "Original authored geometry, pixels, and keyframes; contract-only input.",
        "budgets": {"bones": 9, "cubes": 22, "animations": 4, "controllers": 1}})
    files = [p for p in FEATURE.glob("bedrock/**/*") if p.is_file()]
    internal = FEATURE / "dist/mossback-forager-INTERNAL-TEST.mcaddon"
    zip_tree(internal, [(p, p.relative_to(FEATURE / "bedrock").as_posix()) for p in files])
    proto_files = [p for p in PROTO.rglob("*") if p.is_file()]
    packet = FEATURE / "dist/mossback-forager-candidate-packet.zip"
    zip_tree(packet, [(p, f"prototype/{p.relative_to(PROTO).as_posix()}") for p in proto_files] +
                     [(p, f"feature/{p.relative_to(FEATURE).as_posix()}") for p in files] +
                     [(internal, f"feature/dist/{internal.name}")])
    hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted([*files, *proto_files, internal, packet])}
    write_json(FEATURE / "reports/artifact-hashes.json", hashes)
    write_json(FEATURE / "reports/candidate-packet.json", {
        "feature_id": "mossback_forager", "display_name": "Mossback Forager",
        "model": "gpt-5.6-sol", "requested_reasoning_effort": "light", "actual_reasoning_effort": "low",
        "base_commit": "0db4c8a5f504106b4a601afa6f7bc225eb697dcd",
        "candidate_commit": "HANDOFF_GIT_HEAD",
        "candidate_commit_convention": "Resolve HANDOFF_GIT_HEAD to the exact commit reported with this frozen packet; a Git commit cannot embed its own object ID.",
        "branch": "codex/parallel-batch-1/mossback-forager",
        "worktree": ASSIGNED_WORKTREE, "owned_paths": ["production/features/mossback-forager/",
        "prototypes/blockbench/mossback_forager/", "tools/build_mossback_forager.py", "tests/test_mossback_forager.py"],
        "shared_requests": [], "identifiers": ["ccoriginal_cc:mossback_forager",
        "geometry.ccoriginal_cc.mossback_forager", "animation.ccoriginal_cc.mossback_forager",
        "controller.animation.ccoriginal_cc.mossback_forager", "ccoriginal_cc:mossback_gift",
        "ccoriginal_cc:mossback_test"], "uuids": {"behavior_header": "6a67bb25-2953-4be9-9b32-611cf09be04a",
        "behavior_data_module": "73f807d7-55f1-479e-92b7-017aaba56863",
        "resource_header": "698f7eac-f081-49f9-8e82-1e0f362d704d",
        "resource_module": "d25ac1b1-2d66-475c-bc0a-c5f33620fbb2"},
        "assets": {"geometry": "9 bones, 18 cubes, 1 locator", "texture": "64x64 original RGBA PNG",
                   "animations": 4, "controllers": 1, "package_sha256": hashlib.sha256(internal.read_bytes()).hexdigest()},
        "hash_manifest": "reports/artifact-hashes.json",
        "tests": {"static_feature_tests": "PASS_9_DIRECT_HARNESS",
                  "parallel_batch_preflight": "PASS_4_DIRECT_HARNESS",
                  "resonance_regression": "PASS_4_DIRECT_HARNESS",
                  "json_parse": "PASS", "python_compileall": "PASS",
                  "deterministic_rebuild": "PASS",
                  "bundled_asset_validators": "UNAVAILABLE_IN_REPOSITORY",
                  "pytest": "UNAVAILABLE_NO_MODULE"},
        "revision_history": [
            {"revision": 1, "commit": "2f2b6d6f9960e16470793bb0fe42ec1b1fa64bb4",
             "summary": "Initial complete static vertical slice."},
            {"revision": 2, "commit": "HANDOFF_GIT_HEAD",
             "summary": "Bound flee to five seconds and bound forage playback with cooling-idle controller state."}
            ,{"revision": 3, "commit": "HANDOFF_GIT_HEAD",
              "summary": "Made candidate metadata independent of the review or integration checkout path."}
            ,{"revision": 4, "commit": "HANDOFF_GIT_HEAD",
              "summary": "Installed and made reproducible the authoritative GUI-serialized native Blockbench project."}
        ],
        "performance": {"caps_structurally_met": True, "runtime_measurements": None,
                        "simultaneous_entities_cap": 20, "scripts_per_tick": 0},
        "cleanup": {"selector_is_tag_scoped": True, "latency_target_ticks": 20, "runtime_zero_count": None},
        "limitations": ["Native interaction atomicity requires Bedrock runtime confirmation.",
                        "Timer persistence/restart behavior requires stable BDS confirmation."],
        "blockbench_gui": {"editable_project_open": "PASS", "native_round_trip": "PASS",
                           "counts": {"elements": 19, "bones": 9, "cubes": 18, "locators": 1,
                                      "textures": 1, "animations": 4, "controllers": 1},
                           "visual_capture_inventory": "NOT_EXECUTED"},
        "unexecuted_gates": ["Blockbench visual capture inventory", "Creator Tools",
        "authoritative stable BDS", "Bedrock desktop", "multiplayer clients", "performance profiling",
        "Realm/controller/split-screen", "physical PS4", "Marketplace submission"],
        "contamination": {"java_inspected": False, "controlled_chaos_expression_inspected": False,
                          "third_party_assets_used": False},
        "metrics": {"bones": 9, "cubes": 18, "texture": [64, 64], "animation_clips": 4,
                    "animation_controllers": 1, "controller_states": 5, "flee_seconds": 5,
                    "cooldown_seconds": 45, "stress_count": 20, "pathfinding_radius": 8,
                    "particles_per_interaction": 0, "scripts_per_tick": 0},
        "recommendation": "Accept as an internal static candidate; hold promotion pending authoritative runtime and platform gates."})


if __name__ == "__main__":
    build()
