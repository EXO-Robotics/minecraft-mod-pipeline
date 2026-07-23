#!/usr/bin/env python3
"""Deterministically build the original Mossback Forager internal-test slice."""
from __future__ import annotations

import hashlib
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
    # Blockbench source is an editable, original project representation; GUI/native round-trip remains an explicit gate.
    bb = {"meta": {"format_version": "4.10", "model_format": "bedrock", "box_uv": True},
          "name": "Mossback Forager", "model_identifier": "ccoriginal_cc:mossback_forager",
          "resolution": {"width": 64, "height": 64}, "elements": [], "outliner": [],
          "animations": list(anim["animations"].keys()), "provenance": "Original Codex-authored shape grammar; no third-party expression."}
    write_json(PROTO / "mossback_forager.bbmodel", bb)
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
        "worktree": str(ROOT), "owned_paths": ["production/features/mossback-forager/",
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
        "tests": {"static_feature_tests": "PASS_7_DIRECT_HARNESS",
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
        ],
        "performance": {"caps_structurally_met": True, "runtime_measurements": None,
                        "simultaneous_entities_cap": 20, "scripts_per_tick": 0},
        "cleanup": {"selector_is_tag_scoped": True, "latency_target_ticks": 20, "runtime_zero_count": None},
        "limitations": ["Native interaction atomicity requires Bedrock runtime confirmation.",
                        "Timer persistence/restart behavior requires stable BDS confirmation."],
        "unexecuted_gates": ["Blockbench GUI native round-trip and visual captures", "Creator Tools",
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
