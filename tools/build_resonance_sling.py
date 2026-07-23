#!/usr/bin/env python3
"""Deterministically build the original Bedrock-native Resonance Sling test slice."""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
import zipfile
import zlib
from pathlib import Path
from typing import Any

from mccompiler.world import generate_test_world
from mccompiler.runtime.gametest import augment_mcworld_with_gametest_pack

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "production/features/resonance-sling"
SOURCE = FEATURE / "source"
BEDROCK = FEATURE / "bedrock"
DIST = FEATURE / "dist"
REPORTS = FEATURE / "reports"
ASSETS = ROOT / "prototypes/blockbench/resonance_sling"
MANIFEST = ROOT / "production/reconstruction-waves/forest-wave-1/resonance_sling/original-production-manifest.json"
EPOCH = (1980, 1, 1, 0, 0, 0)


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((json.dumps(value, indent=2, sort_keys=True) + "\n") if not isinstance(value, str) else value, encoding="utf-8")


def png(width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> bytes:
    raw = b"".join(b"\0" + b"".join(bytes(px) for px in pixels[y * width:(y + 1) * width]) for y in range(height))
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def icon(size: int = 32) -> bytes:
    px = [(28, 34, 31, 0)] * (size * size)
    def fill(x0: int, y0: int, x1: int, y1: int, c: tuple[int, int, int, int]) -> None:
        for y in range(y0, y1):
            for x in range(x0, x1): px[y * size + x] = c
    wood, cord, glow = (92, 58, 36, 255), (197, 206, 181, 255), (105, 240, 211, 255)
    fill(13, 12, 18, 29, wood); fill(7, 4, 12, 17, wood); fill(19, 4, 24, 17, wood)
    for i in range(9): fill(11 + i, 6 + i // 2, 12 + i, 7 + i // 2, cord)
    fill(13, 12, 19, 17, glow)
    return png(size, size, px)


def solid(size: int, color: tuple[int, int, int, int]) -> bytes:
    return png(size, size, [color] * size * size)


def zip_tree(path: Path, roots: list[tuple[Path, str]]) -> dict[str, Any]:
    entries: list[tuple[str, bytes]] = []
    for root, prefix in roots:
        for item in sorted(p for p in root.rglob("*") if p.is_file()):
            entries.append((prefix + item.relative_to(root).as_posix(), item.read_bytes()))
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in entries:
            info = zipfile.ZipInfo(name, EPOCH); info.create_system = 3; info.external_attr = 0o100644 << 16
            archive.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "files": len(entries)}


SCRIPT = r'''import { system, world } from "@minecraft/server";
const NS="ccoriginal_cc", SLING=`${NS}:resonance_sling`, AMMO=`${NS}:resonance_pebble`, PULSE=`${NS}:resonance_pulse`;
const activeByOwner=new Map(), ownerByProjectile=new Map(); let activeGlobal=0;
function releaseId(projectileId){
  if(!ownerByProjectile.has(projectileId))return;const ownerId=ownerByProjectile.get(projectileId);ownerByProjectile.delete(projectileId);activeGlobal=Math.max(0,activeGlobal-1);
  if(ownerId)activeByOwner.set(ownerId,Math.max(0,(activeByOwner.get(ownerId)||1)-1));
}
function removeProjectile(projectile){if(!projectile)return;let id;try{id=projectile.id;}catch{}if(id)releaseId(id);try{if(projectile.isValid)projectile.remove();}catch{}}
world.afterEvents.entitySpawn.subscribe(e=>{if(e.entity.typeId!==PULSE)return;const p=e.entity;system.run(()=>{
  if(!p?.isValid)return;const owner=p.getComponent("minecraft:projectile")?.owner,ownerId=owner?.id,own=ownerId?(activeByOwner.get(ownerId)||0):0;
  if((ownerId&&own>=4)||activeGlobal>=16){try{owner?.sendMessage("§cToo many resonance pulses are active.");}catch{}removeProjectile(p);return;}
  if(ownerId)activeByOwner.set(ownerId,own+1);activeGlobal++;ownerByProjectile.set(p.id,ownerId);system.runTimeout(()=>removeProjectile(p),60);
});});
world.afterEvents.entityRemove.subscribe(e=>{if(e.removedEntityTypeId===PULSE)releaseId(e.removedEntityId);});
world.afterEvents.playerSpawn.subscribe(e=>{const p=e.player;if(e.initialSpawn&&p)system.runTimeout(()=>{if(p?.isValid)p.sendMessage("§a[Resonance Sling] ORIGINAL INTERNAL TEST BUILD initialized");},20);});
console.warn("[resonance-sling] script runtime initialized stable_api=2.0.0 persistent_records=0 global_scan_per_tick=0 cap=16");
'''


def build() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text())
    if BEDROCK.exists(): shutil.rmtree(BEDROCK)
    bp, rp = BEDROCK / "behavior_pack", BEDROCK / "resource_pack"
    bp_uuid, rp_uuid = "61e0bbf4-0051-4bb0-a5bb-19e1cd68db0f", "ae5d1908-8fbe-4282-83a4-8509606aceda"
    write(bp/"manifest.json",{"format_version":2,"header":{"name":"Resonance Sling INTERNAL TEST BP","description":"NOT MARKETPLACE APPROVED; NOT PHYSICAL PS4 CERTIFIED; NOT FOR PUBLIC RELEASE","uuid":bp_uuid,"version":[1,0,0],"min_engine_version":[1,21,90]},"modules":[{"type":"data","uuid":"45ae61d5-f378-49bb-9140-1912384c3241","version":[1,0,0]},{"type":"script","language":"javascript","entry":"scripts/main.js","uuid":"1d5f9d5e-eb11-46da-8cab-d6f1387bd850","version":[1,0,0]}],"dependencies":[{"module_name":"@minecraft/server","version":"2.0.0"},{"uuid":rp_uuid,"version":[1,0,0]}]})
    write(rp/"manifest.json",{"format_version":2,"header":{"name":"Resonance Sling INTERNAL TEST RP","description":"NOT MARKETPLACE APPROVED; NOT PHYSICAL PS4 CERTIFIED; NOT FOR PUBLIC RELEASE","uuid":rp_uuid,"version":[1,0,0],"min_engine_version":[1,21,90],"pack_scope":"world"},"modules":[{"type":"resources","uuid":"e509f362-1976-4ae9-b536-fd4b9b7deafe","version":[1,0,0]}],"dependencies":[{"uuid":bp_uuid,"version":[1,0,0]}]})
    write(bp/"scripts/main.js",SCRIPT)
    common={"minecraft:display_name":{"value":"item.ccoriginal_cc"},"minecraft:icon":"resonance_sling","minecraft:max_stack_size":1}
    write(bp/"items/resonance_sling.json",{"format_version":"1.21.90","minecraft:item":{"description":{"identifier":"ccoriginal_cc:resonance_sling","menu_category":{"category":"equipment"}},"components":{**common,"minecraft:display_name":{"value":"item.ccoriginal_cc:resonance_sling.name"},"minecraft:durability":{"max_durability":256},"minecraft:cooldown":{"category":"resonance_sling","duration":0.8},"minecraft:hand_equipped":True,"minecraft:use_modifiers":{"use_duration":72000.0,"movement_modifier":0.6},"minecraft:shooter":{"ammunition":[{"item":"ccoriginal_cc:resonance_pebble","use_offhand":True,"search_inventory":True,"use_in_creative":False}],"max_draw_duration":0.7,"scale_power_by_draw_duration":True,"charge_on_draw":False}}}})
    write(bp/"items/resonance_pebble.json",{"format_version":"1.21.90","minecraft:item":{"description":{"identifier":"ccoriginal_cc:resonance_pebble","menu_category":{"category":"items"}},"components":{"minecraft:display_name":{"value":"item.ccoriginal_cc:resonance_pebble.name"},"minecraft:icon":"resonance_pebble","minecraft:max_stack_size":64,"minecraft:projectile":{"minimum_critical_power":1.0,"projectile_entity":"ccoriginal_cc:resonance_pulse"}}}})
    write(bp/"entities/resonance_pulse.json",{"format_version":"1.21.90","minecraft:entity":{"description":{"identifier":"ccoriginal_cc:resonance_pulse","is_spawnable":False,"is_summonable":True},"components":{"minecraft:type_family":{"family":["resonance_projectile"]},"minecraft:collision_box":{"width":0.2,"height":0.2},"minecraft:physics":{},"minecraft:projectile":{"power":1.0,"gravity":0.045,"anchor":1,"on_hit":{"impact_damage":{"damage":4,"knockback":True,"power_multiplier":0.23,"semi_random_diff_damage":False},"particle_on_hit":{"particle_type":"ccoriginal_cc:resonance_impact","num_particles":6,"on_entity_hit":True,"on_other_hit":True},"remove_on_hit":{}}},"minecraft:timer":{"time":3.0,"looping":False,"time_down_event":{"event":"ccoriginal_cc:expire","target":"self"}}},"events":{"ccoriginal_cc:expire":{"remove":{}}}}})
    write(bp/"recipes/resonance_sling.json",{"format_version":"1.20.10","minecraft:recipe_shaped":{"description":{"identifier":"ccoriginal_cc:resonance_sling"},"tags":["crafting_table"],"pattern":["SSS","TAT"," T "],"key":{"S":{"item":"minecraft:string"},"T":{"item":"minecraft:stick"},"A":{"item":"minecraft:amethyst_shard"}},"result":{"item":"ccoriginal_cc:resonance_sling","count":1},"unlock":[{"item":"minecraft:amethyst_shard"}]}})
    write(bp/"recipes/resonance_pebbles.json",{"format_version":"1.20.10","minecraft:recipe_shapeless":{"description":{"identifier":"ccoriginal_cc:resonance_pebbles"},"tags":["crafting_table"],"ingredients":[{"item":"minecraft:amethyst_shard"},{"item":"minecraft:cobblestone"}],"result":{"item":"ccoriginal_cc:resonance_pebble","count":8},"unlock":[{"item":"minecraft:amethyst_shard"}]}})
    write(bp/"functions/resonance_sling_kit.mcfunction","give @s ccoriginal_cc:resonance_sling 1\ngive @s ccoriginal_cc:resonance_pebble 64\n")
    write(rp/"textures/item_texture.json",{"resource_pack_name":"ccoriginal_cc","texture_name":"atlas.items","texture_data":{"resonance_sling":{"textures":"textures/items/resonance_sling"},"resonance_pebble":{"textures":"textures/items/resonance_pebble"}}})
    (rp/"textures/items").mkdir(parents=True,exist_ok=True); (rp/"textures/items/resonance_sling.png").write_bytes(icon()); (rp/"textures/items/resonance_pebble.png").write_bytes(solid(16,(105,240,211,255)))
    geo={"format_version":"1.12.0","minecraft:geometry":[{"description":{"identifier":"geometry.ccoriginal_cc.resonance_pulse","texture_width":16,"texture_height":16,"visible_bounds_width":1,"visible_bounds_height":1,"visible_bounds_offset":[0,0,0]},"bones":[{"name":"root","pivot":[0,0,0]},{"name":"core","parent":"root","pivot":[0,0,0],"cubes":[{"origin":[-2,-2,-2],"size":[4,4,4],"uv":[0,0]}]}]}]}
    write(rp/"models/entity/resonance_pulse.geo.json",geo)
    native_pulse_geo=ASSETS/"resonance_pulse.geo.json"
    if native_pulse_geo.is_file(): shutil.copyfile(native_pulse_geo,rp/"models/entity/resonance_pulse.geo.json")
    (rp/"textures/entity").mkdir(parents=True,exist_ok=True); (rp/"textures/entity/resonance_pulse.png").write_bytes(solid(16,(105,240,211,255)))
    write(rp/"entity/resonance_pulse.entity.json",{"format_version":"1.10.0","minecraft:client_entity":{"description":{"identifier":"ccoriginal_cc:resonance_pulse","materials":{"default":"entity_emissive_alpha"},"textures":{"default":"textures/entity/resonance_pulse"},"geometry":{"default":"geometry.ccoriginal_cc.resonance_pulse"},"render_controllers":["controller.render.default"]}}})
    native_sling_geo=ASSETS/"resonance_sling.geo.json"
    shutil.copyfile(native_sling_geo,rp/"models/entity/resonance_sling.geo.json")
    write(rp/"attachables/resonance_sling.entity.json",{"format_version":"1.10.0","minecraft:attachable":{"description":{"identifier":"ccoriginal_cc:resonance_sling","materials":{"default":"entity_alphatest"},"textures":{"default":"textures/entity/resonance_sling"},"geometry":{"default":"geometry.ccoriginal_cc.resonance_sling"},"animations":{"idle":"animation.ccoriginal_cc.resonance_sling.idle","release":"animation.ccoriginal_cc.resonance_sling.release","controller":"controller.animation.ccoriginal_cc.resonance_sling"},"scripts":{"animate":["controller"]},"render_controllers":["controller.render.default"]}}})
    write(rp/"animations/resonance_sling.animation.json",{"format_version":"1.8.0","animations":{"animation.ccoriginal_cc.resonance_sling.idle":{"loop":True,"animation_length":1.0,"bones":{"pouch":{"rotation":[0,0,"math.sin(query.life_time * 120.0) * 1.5"]}}},"animation.ccoriginal_cc.resonance_sling.release":{"loop":False,"animation_length":0.2,"bones":{"pouch":{"position":{"0.0":[0,0,0],"0.08":[0,0,1.5],"0.2":[0,0,0]}}}}}})
    write(rp/"animation_controllers/resonance_sling.controller.json",{"format_version":"1.10.0","animation_controllers":{"controller.animation.ccoriginal_cc.resonance_sling":{"initial_state":"idle","states":{"idle":{"animations":["idle"],"transitions":[{"release":"query.is_using_item"}]},"release":{"animations":["release"],"transitions":[{"idle":"!query.is_using_item"}],"blend_transition":0.05}}}}})
    (rp/"textures/entity/resonance_sling.png").write_bytes(icon())
    write(rp/"particles/resonance_impact.json",{"format_version":"1.10.0","particle_effect":{"description":{"identifier":"ccoriginal_cc:resonance_impact","basic_render_parameters":{"material":"particles_alpha","texture":"textures/particle/particles"}},"components":{"minecraft:emitter_lifetime_once":{"active_time":0.1},"minecraft:emitter_rate_instant":{"num_particles":6},"minecraft:emitter_shape_sphere":{"radius":0.15,"direction":"outwards"},"minecraft:particle_lifetime_expression":{"max_lifetime":0.3},"minecraft:particle_initial_speed":1.2,"minecraft:particle_appearance_billboard":{"size":[0.08,0.08],"facing_camera_mode":"rotate_xyz","uv":{"texture_width":128,"texture_height":128,"uv":[0,0],"uv_size":[8,8]}}}}})
    write(rp/"texts/languages.json",["en_US"]); write(rp/"texts/en_US.lang","item.ccoriginal_cc:resonance_sling.name=Resonance Sling\nitem.ccoriginal_cc:resonance_pebble.name=Resonance Pebble\n")
    ASSETS.mkdir(parents=True,exist_ok=True)
    bb={"meta":{"format_version":"4.10","model_format":"bedrock","box_uv":True},"name":"resonance_sling","model_identifier":"ccoriginal_cc.resonance_sling","resolution":{"width":32,"height":32},"elements":[],"outliner":[{"name":"root","origin":[0,0,0],"children":[]},{"name":"grip","origin":[0,0,0],"children":[]},{"name":"fork","origin":[0,8,0],"children":[]},{"name":"pouch","origin":[0,12,0],"children":[]}],"animations":[]}
    if not (ASSETS/"resonance_sling.bbmodel").exists(): write(ASSETS/"resonance_sling.bbmodel",bb)
    if not (ASSETS/"resonance_pulse.bbmodel").exists(): write(ASSETS/"resonance_pulse.bbmodel",{"meta":{"format_version":"4.10","model_format":"bedrock","box_uv":True},"name":"resonance_pulse","model_identifier":"ccoriginal_cc.resonance_pulse","resolution":{"width":16,"height":16},"elements":[],"outliner":[]})
    write(ASSETS/"originality-and-authoring.json",{"authorship":"ORIGINAL_AUTHORSHIP","third_party_materials":[],"editable_sources":["resonance_sling.bbmodel","resonance_pulse.bbmodel"],"native_exports":["resonance_sling.geo.json","resonance_pulse.geo.json"],"native_round_trip":"BLOCKBENCH_5_1_5_VERIFIED","observations":{"sling_elements":8,"sling_cubes":6,"sling_true_locators":["locator.pouch","locator.release"],"projectile_cubes":1,"projectile_warnings":0},"note":"Both sources were reopened and saved in Blockbench 5.1.5; both Bedrock geometry files were exported through Blockbench. Sling export preserves both locators on the pouch bone."})
    addon=zip_tree(DIST/"resonance-sling-INTERNAL-TEST.mcaddon",[(bp,"behavior_pack/"),(rp,"resource_pack/")])
    world_path=DIST/"resonance-sling-INTERNAL-TEST.mcworld"; generate_test_world(bp,rp,world_path,world_name="Resonance Sling INTERNAL TEST")
    world={"path":world_path.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(world_path.read_bytes()).hexdigest(),"bytes":world_path.stat().st_size}
    diagnostic_pack=FEATURE/"diagnostic/preview-simulated-player"
    preview_world=FEATURE/"runtime/preview-simulated-player.mcworld"
    preview=augment_mcworld_with_gametest_pack(world_path,diagnostic_pack,preview_world,diagnostic_server_version="2.10.0")
    receipt={"schema_version":"1.0.0","labels":["INTERNAL TEST BUILD","NOT MARKETPLACE APPROVED","NOT PHYSICAL PS4 CERTIFIED","NOT FOR PUBLIC RELEASE"],"manifest_revision":manifest["manifest_revision"],"pack_uuids":{"behavior":bp_uuid,"resource":rp_uuid},"artifacts":{"mcaddon":addon,"mcworld":world},"preview_diagnostic":{"path":str(preview_world.relative_to(ROOT)),"sha256":preview["diagnostic_world"]["sha256"],"never_ship":True}}
    write(REPORTS/"artifact-manifest.json",receipt)
    return receipt


if __name__=="__main__":
    print(json.dumps(build(),indent=2,sort_keys=True))
