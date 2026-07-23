#!/usr/bin/env python3
"""Build the original Barkguard Charm Bedrock internal-test package deterministically."""
from __future__ import annotations

import hashlib
import json
import struct
import zipfile
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "production/features/barkguard-charm"
BP = FEATURE / "bedrock/behavior_pack"
RP = FEATURE / "bedrock/resource_pack"
ASSETS = ROOT / "prototypes/blockbench/barkguard_charm"
DIST = FEATURE / "dist"
REPORTS = FEATURE / "reports"
EPOCH = (1980, 1, 1, 0, 0, 0)
IMPLEMENTATION_COMMIT = "c88d4d025c00ab474a951cd71ff28745dbdf40a8"
ASSIGNED_WORKTREE = "/Users/blakegrove/Desktop/bedrock-server/.derivedData/worktrees/parallel-batch-1/barkguard-charm"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def png(width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> bytes:
    rows = b"".join(b"\0" + b"".join(bytes(p) for p in pixels[y * width:(y + 1) * width]) for y in range(height))

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")


def charm_texture() -> bytes:
    size = 32
    px = [(0, 0, 0, 0)] * (size * size)

    def fill(x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int, int]) -> None:
        for y in range(y0, y1):
            for x in range(x0, x1):
                px[y * size + x] = color

    bark, wood, honey, fern, rim = (55, 35, 25, 255), (105, 66, 38, 255), (190, 126, 54, 255), (58, 117, 69, 255), (225, 206, 155, 255)
    fill(9, 4, 23, 27, bark)
    fill(11, 6, 21, 25, wood)
    fill(13, 8, 20, 22, honey)
    fill(14, 10, 19, 19, fern)
    fill(15, 8, 16, 22, rim)
    fill(7, 9, 10, 12, rim)
    fill(22, 14, 25, 17, rim)
    fill(9, 22, 12, 25, rim)
    return png(size, size, px)


SCRIPT = r'''import { EquipmentSlot, EntityComponentTypes, system, world } from "@minecraft/server";

const ITEM = "ccoriginal_cc:barkguard_charm";
const COOLDOWN = "barkguard_charm";
const DAMAGE_THRESHOLD = 2;
const EFFECT_TICKS = 60;
const COOLDOWN_TICKS = 240;
const lastHandledTick = new Map();

function tryActivate(player, damage) {
  if (damage < DAMAGE_THRESHOLD || player.getItemCooldown(COOLDOWN) > 0) return false;
  const equippable = player.getComponent(EntityComponentTypes.Equippable);
  const charm = equippable?.getEquipment(EquipmentSlot.Offhand);
  if (!charm || charm.typeId !== ITEM) return false;

  const tick = system.currentTick;
  if (lastHandledTick.get(player.id) === tick) return false;
  lastHandledTick.set(player.id, tick);

  const durability = charm.getComponent("minecraft:durability");
  if (!durability) return false;
  player.addEffect("resistance", EFFECT_TICKS, { amplifier: 0, showParticles: true });
  player.startItemCooldown(COOLDOWN, COOLDOWN_TICKS);
  const nextDamage = durability.damage + 1;
  if (nextDamage >= durability.maxDurability) {
    equippable.setEquipment(EquipmentSlot.Offhand, undefined);
    player.sendMessage("§6Your Barkguard Charm returns to the forest.");
  } else {
    durability.damage = nextDamage;
    equippable.setEquipment(EquipmentSlot.Offhand, charm);
  }
  return true;
}

world.afterEvents.entityHurt.subscribe((event) => {
  const player = event.hurtEntity;
  if (player.typeId !== "minecraft:player") return;
  tryActivate(player, event.damage);
});

world.afterEvents.playerLeave.subscribe((event) => lastHandledTick.delete(event.playerId));
console.warn("[barkguard-charm] stable_api=2.0.0 event_driven=true global_scans_per_tick=0 persistent_records=0");
'''


def model_files() -> None:
    elements = [
        ("back_plate", [-4, 6, -1], [4, 14, 0], "medallion"),
        ("heartwood", [-3, 7, -2], [3, 13, -1], "medallion"),
        ("leaf", [-1, 8, -3], [2, 12, -2], "leaf_inlay"),
        ("rim_top", [-3, 13, -2], [3, 14, -1], "medallion"),
        ("notch_left", [-5, 8, -1.5], [-4, 10, -0.5], "bindings"),
        ("notch_right", [4, 10, -1.5], [5, 12, -0.5], "bindings"),
        ("notch_base", [-1, 5, -1.5], [1, 6, -0.5], "bindings"),
    ]
    cubes = []
    bb_elements = []
    children: dict[str, list[str]] = {"medallion": [], "leaf_inlay": [], "bindings": []}
    for index, (name, frm, to, bone) in enumerate(elements):
        uuid = f"00000000-0000-4000-8000-{index + 1:012d}"
        size = [to[i] - frm[i] for i in range(3)]
        cubes.append({"origin": frm, "size": size, "uv": [index * 4 % 24, (index // 6) * 8]})
        bb_elements.append({"name": name, "from": frm, "to": to, "autouv": 0, "color": index % 8, "uuid": uuid, "faces": {face: {"uv": [0, 0, 4, 4], "texture": 0} for face in ["north", "east", "south", "west", "up", "down"]}})
        children[bone].append(uuid)
    geo = {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {"identifier": "geometry.ccoriginal_cc.barkguard_charm", "texture_width": 32, "texture_height": 32, "visible_bounds_width": 1, "visible_bounds_height": 1, "visible_bounds_offset": [0, 0.6, 0]},
            "bones": [
                {"name": "root", "pivot": [0, 8, 0]},
                {"name": "medallion", "parent": "root", "pivot": [0, 10, 0], "cubes": [cubes[0], cubes[1], cubes[3]]},
                {"name": "leaf_inlay", "parent": "medallion", "pivot": [0, 10, -1], "cubes": [cubes[2]]},
                {"name": "bindings", "parent": "root", "pivot": [0, 10, 0], "cubes": cubes[4:]},
            ],
        }],
    }
    bb = {
        "meta": {"format_version": "4.10", "model_format": "bedrock", "box_uv": True},
        "name": "barkguard_charm",
        "model_identifier": "ccoriginal_cc.barkguard_charm",
        "resolution": {"width": 32, "height": 32},
        "elements": bb_elements,
        "outliner": [
            {"name": "root", "origin": [0, 8, 0], "uuid": "10000000-0000-4000-8000-000000000001", "children": [
                {"name": "medallion", "origin": [0, 10, 0], "uuid": "10000000-0000-4000-8000-000000000002", "children": children["medallion"] + [
                    {"name": "leaf_inlay", "origin": [0, 10, -1], "uuid": "10000000-0000-4000-8000-000000000003", "children": children["leaf_inlay"]}
                ]},
                {"name": "bindings", "origin": [0, 10, 0], "uuid": "10000000-0000-4000-8000-000000000004", "children": children["bindings"]},
            ]}
        ],
        "textures": [{"path": "barkguard_charm.png", "name": "barkguard_charm.png", "folder": "", "namespace": "", "id": "0", "particle": False, "render_mode": "default", "render_sides": "auto", "frame_time": 1, "frame_order_type": "loop"}],
        "animations": [{"uuid": "20000000-0000-4000-8000-000000000001", "name": "animation.ccoriginal_cc.barkguard_charm.activate", "loop": "once", "length": 0.35, "snapping": 20, "animators": {}}],
    }
    write_json(ASSETS / "barkguard_charm.bbmodel", bb)
    write_json(ASSETS / "barkguard_charm.geo.json", geo)
    (ASSETS / "barkguard_charm.png").parent.mkdir(parents=True, exist_ok=True)
    (ASSETS / "barkguard_charm.png").write_bytes(charm_texture())
    write_json(ASSETS / "originality-and-authoring.json", {
        "asset_class": "attachable/item",
        "authorship": "ORIGINAL_AUTHORSHIP",
        "shape_grammar": "Layered asymmetrical wooden medallion, offset leaf inlay, and three binding notches.",
        "palette": ["dark bark", "honey wood", "fern green", "pale rim"],
        "third_party_materials": [],
        "source_expression_used": False,
        "editable_source": "barkguard_charm.bbmodel",
        "native_export": "barkguard_charm.geo.json",
        "authoring_method": "Deterministic original source generation; Blockbench GUI round-trip remains assigned to MAIN_CODEX.",
    })


def pack_files() -> None:
    description = "ORIGINAL INTERNAL TEST BUILD; NOT MARKETPLACE APPROVED; NOT PHYSICAL PS4 CERTIFIED; NOT FOR PUBLIC RELEASE"
    bp_header, bp_data, bp_script = "2985974d-139b-4142-9c25-ae1aba1f95bf", "1ace8116-c3de-4fa4-b083-c6a3b2c79d39", "a8cbf915-0ec4-4c20-95c0-5905667428fd"
    rp_header, rp_module = "29eb411e-8ad2-4666-bb55-756efbd4944c", "5580dd51-6b31-414b-b15e-0160f5f5b34f"
    write_json(BP / "manifest.json", {"format_version": 2, "header": {"name": "Barkguard Charm INTERNAL TEST BP", "description": description, "uuid": bp_header, "version": [1, 0, 0], "min_engine_version": [1, 21, 90]}, "modules": [{"type": "data", "uuid": bp_data, "version": [1, 0, 0]}, {"type": "script", "language": "javascript", "entry": "scripts/main.js", "uuid": bp_script, "version": [1, 0, 0]}], "dependencies": [{"module_name": "@minecraft/server", "version": "2.0.0"}, {"uuid": rp_header, "version": [1, 0, 0]}]})
    write_json(RP / "manifest.json", {"format_version": 2, "header": {"name": "Barkguard Charm INTERNAL TEST RP", "description": description, "uuid": rp_header, "version": [1, 0, 0], "min_engine_version": [1, 21, 90], "pack_scope": "world"}, "modules": [{"type": "resources", "uuid": rp_module, "version": [1, 0, 0]}], "dependencies": [{"uuid": bp_header, "version": [1, 0, 0]}]})
    write_text(BP / "scripts/main.js", SCRIPT)
    write_json(BP / "items/barkguard_charm.json", {"format_version": "1.21.90", "minecraft:item": {"description": {"identifier": "ccoriginal_cc:barkguard_charm", "menu_category": {"category": "equipment"}}, "components": {"minecraft:display_name": {"value": "item.ccoriginal_cc:barkguard_charm.name"}, "minecraft:icon": "barkguard_charm", "minecraft:max_stack_size": 1, "minecraft:allow_off_hand": True, "minecraft:durability": {"max_durability": 96}, "minecraft:cooldown": {"category": "barkguard_charm", "duration": 12.0}}}})
    write_json(BP / "recipes/barkguard_charm.json", {"format_version": "1.20.10", "minecraft:recipe_shaped": {"description": {"identifier": "ccoriginal_cc:barkguard_charm"}, "tags": ["crafting_table"], "pattern": ["LAL", "WWW", " L "], "key": {"L": {"item": "minecraft:leather"}, "A": {"item": "minecraft:amethyst_shard"}, "W": {"item": "minecraft:oak_planks"}}, "result": {"item": "ccoriginal_cc:barkguard_charm", "count": 1}, "unlock": [{"item": "minecraft:amethyst_shard"}]}})
    write_text(BP / "functions/barkguard_test.mcfunction", "give @s ccoriginal_cc:barkguard_charm 1\n")
    write_json(RP / "textures/item_texture.json", {"resource_pack_name": "ccoriginal_cc", "texture_name": "atlas.items", "texture_data": {"barkguard_charm": {"textures": "textures/items/barkguard_charm"}}})
    (RP / "textures/items").mkdir(parents=True, exist_ok=True)
    (RP / "textures/items/barkguard_charm.png").write_bytes(charm_texture())
    (RP / "textures/entity").mkdir(parents=True, exist_ok=True)
    (RP / "textures/entity/barkguard_charm.png").write_bytes(charm_texture())
    geo = json.loads((ASSETS / "barkguard_charm.geo.json").read_text())
    write_json(RP / "models/entity/barkguard_charm.geo.json", geo)
    write_json(RP / "animations/barkguard_charm.animation.json", {"format_version": "1.8.0", "animations": {"animation.ccoriginal_cc.barkguard_charm.idle": {"loop": True, "animation_length": 2.0, "bones": {"leaf_inlay": {"rotation": [0, 0, "math.sin(query.life_time * 90.0) * 1.0"]}}}, "animation.ccoriginal_cc.barkguard_charm.activate": {"loop": False, "animation_length": 0.35, "bones": {"medallion": {"scale": {"0.0": [1, 1, 1], "0.12": [1.12, 1.12, 1.12], "0.35": [1, 1, 1]}, "rotation": {"0.0": [0, 0, 0], "0.12": [0, 0, -8], "0.35": [0, 0, 0]}}}}}})
    write_json(RP / "animation_controllers/barkguard_charm.controller.json", {"format_version": "1.10.0", "animation_controllers": {"controller.animation.ccoriginal_cc.barkguard_charm": {"initial_state": "idle", "states": {"idle": {"animations": ["idle"], "transitions": [{"activate": "query.is_item_name_any('slot.weapon.offhand', 0, 'ccoriginal_cc:barkguard_charm') && query.is_on_fire"}]}, "activate": {"animations": ["activate"], "transitions": [{"idle": "!query.is_on_fire"}], "blend_transition": 0.08}}}}})
    write_json(RP / "attachables/barkguard_charm.entity.json", {"format_version": "1.10.0", "minecraft:attachable": {"description": {"identifier": "ccoriginal_cc:barkguard_charm", "materials": {"default": "entity_alphatest"}, "textures": {"default": "textures/entity/barkguard_charm"}, "geometry": {"default": "geometry.ccoriginal_cc.barkguard_charm"}, "animations": {"idle": "animation.ccoriginal_cc.barkguard_charm.idle", "activate": "animation.ccoriginal_cc.barkguard_charm.activate", "controller": "controller.animation.ccoriginal_cc.barkguard_charm"}, "scripts": {"animate": ["controller"]}, "render_controllers": ["controller.render.default"]}}})
    write_json(RP / "texts/languages.json", ["en_US"])
    write_text(RP / "texts/en_US.lang", "item.ccoriginal_cc:barkguard_charm.name=Barkguard Charm\n")


def zip_pack() -> dict[str, Any]:
    path = DIST / "barkguard-charm-INTERNAL-TEST.mcaddon"
    entries: list[tuple[str, bytes]] = []
    for root, prefix in [(BP, "behavior_pack/"), (RP, "resource_pack/")]:
        for item in sorted(p for p in root.rglob("*") if p.is_file()):
            entries.append((prefix + item.relative_to(root).as_posix(), item.read_bytes()))
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in entries:
            info = zipfile.ZipInfo(name, EPOCH)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    payload = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload), "files": len(entries)}


def file_hashes() -> dict[str, str]:
    roots = [BP, RP, ASSETS]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for root in roots for p in sorted(root.rglob("*")) if p.is_file()}


def build() -> dict[str, Any]:
    model_files()
    pack_files()
    package = zip_pack()
    packet = {
        "schema_version": "1.0.0",
        "feature": "Barkguard Charm",
        "feature_id": "barkguard_charm",
        "recommendation": "ACCEPT_FOR_MAIN_CODEX_QUALIFICATION",
        "reasoning_allocation": {"requested": "light", "actual": "low", "honest_note": "Requested allocation was unavailable."},
        "authorship": {"lane": "ORIGINAL_BEDROCK_NATIVE", "source_expression_used": False, "third_party_materials": [], "model_reasoning": "Seven-cube layered medallion uses an asymmetric leaf and three protruding binding notches to remain readable at offhand scale."},
        "worktree": ASSIGNED_WORKTREE,
        "branch": "codex/parallel-batch-1/barkguard-charm",
        "base_commit": "0db4c8a5f504106b4a601afa6f7bc225eb697dcd",
        "implementation_head_at_build": IMPLEMENTATION_COMMIT,
        "owned_paths": ["production/features/barkguard-charm/", "prototypes/blockbench/barkguard_charm/", "tools/build_barkguard_charm.py", "tests/test_barkguard_charm.py"],
        "identifiers": ["ccoriginal_cc:barkguard_charm", "geometry.ccoriginal_cc.barkguard_charm", "animation.ccoriginal_cc.barkguard_charm", "controller.animation.ccoriginal_cc.barkguard_charm", "ccoriginal_cc:barkguard_test"],
        "uuids": {"behavior_header": "2985974d-139b-4142-9c25-ae1aba1f95bf", "behavior_data_module": "1ace8116-c3de-4fa4-b083-c6a3b2c79d39", "behavior_script_module": "a8cbf915-0ec4-4c20-95c0-5905667428fd", "resource_header": "29eb411e-8ad2-4666-bb55-756efbd4944c", "resource_module": "5580dd51-6b31-414b-b15e-0160f5f5b34f"},
        "assets": {"editable_model": "prototypes/blockbench/barkguard_charm/barkguard_charm.bbmodel", "native_geometry": "prototypes/blockbench/barkguard_charm/barkguard_charm.geo.json", "texture_size": [32, 32], "cube_count": 7, "animation_clips": 2, "animation_controllers": 1, "hashes": file_hashes()},
        "package": package,
        "tests": {"command": "python3 -m unittest tests.test_barkguard_charm", "coverage": ["offhand detection", "damage threshold", "effect/cooldown", "exact durability and break", "duplicate event path", "2/4-player isolation", "death/reconnect/restart model", "no per-tick scan/custom persistence", "deterministic hashes and labels"]},
        "performance": {"global_scans_per_tick": 0, "persistent_records": 0, "scheduled_callbacks": 0, "callbacks_per_damage_event_max": 1, "simultaneous_players_design_cap": 4},
        "cleanup": {"disconnect": "delete one ephemeral duplicate guard entry", "restart": "ephemeral cooldown and duplicate guard reset safely; inventory durability remains native", "persistent_cleanup_required": False},
        "labels": ["INTERNAL TEST BUILD", "NOT MARKETPLACE APPROVED", "NOT PHYSICAL PS4 CERTIFIED", "NOT FOR PUBLIC RELEASE"],
        "unexecuted_gates": ["Blockbench GUI native round-trip and visual evidence (MAIN_CODEX owner)", "Creator Tools", "stable BDS (MAIN_CODEX owner)", "Bedrock desktop", "multiplayer clients", "physical PS4", "Marketplace review"],
        "limitations": ["Activation animation uses a conservative visual query proxy because stable script state is not exported to Molang.", "Cooldown may safely reset after restart as explicitly allowed by the contract.", "Static and model tests are not runtime evidence."],
        "contamination": {"java_material_used": False, "controlled_chaos_expression_used": False, "shared_paths_modified": False},
        "metrics": {"durability": 96, "damage_threshold": 2, "effect": "resistance I", "effect_ticks": 60, "cooldown_ticks": 240, "durability_cost": 1},
    }
    write_json(REPORTS / "candidate-packet.json", packet)
    return packet


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
