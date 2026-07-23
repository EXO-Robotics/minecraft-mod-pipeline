#!/usr/bin/env python3
"""Build the original Signal Ruin internal-test vertical slice deterministically."""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "production/features/signal-ruin"
PROTO = ROOT / "prototypes/blockbench/signal_ruin"
LABEL = "INTERNAL TEST BUILD / NOT MARKETPLACE APPROVED / NOT PHYSICAL PS4 CERTIFIED / NOT FOR PUBLIC RELEASE"
BP = FEATURE / "bedrock/behavior_pack"
RP = FEATURE / "bedrock/resource_pack"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def nbt_string(value: str) -> bytes:
    raw = value.encode()
    return struct.pack("<H", len(raw)) + raw


def named(tag: int, name: str, payload: bytes) -> bytes:
    return bytes([tag]) + nbt_string(name) + payload


def compound(items: list[bytes]) -> bytes:
    return b"".join(items) + b"\x00"


def int_list(values: list[int]) -> bytes:
    return struct.pack("<i", len(values)) + b"".join(struct.pack("<i", x) for x in values)


def structure_nbt(spec: dict) -> bytes:
    sx, sy, sz = spec["size"]
    blocks = spec["blocks"]
    palette_names = sorted({row["block"] for row in blocks} | {"minecraft:air"})
    indexes = {name: i for i, name in enumerate(palette_names)}
    volume = sx * sy * sz
    layer = [-1] * volume
    for row in blocks:
        x, y, z = row["pos"]
        layer[x * sy * sz + y * sz + z] = indexes[row["block"]]
    palette = b"".join(
        bytes([10]) + compound([
            named(8, "name", nbt_string(name)),
            named(10, "states", compound([])),
            named(3, "version", struct.pack("<i", 18168865)),
        ])
        for name in palette_names
    )
    root = compound([
        named(3, "format_version", struct.pack("<i", 1)),
        named(9, "size", bytes([3]) + int_list([sx, sy, sz])),
        named(9, "structure_world_origin", bytes([3]) + int_list([0, 0, 0])),
        named(10, "structure", compound([
            named(9, "block_indices", bytes([9]) + struct.pack("<i", 2)
                  + bytes([3]) + int_list(layer)
                  + bytes([3]) + int_list([-1] * volume)),
            named(9, "entities", bytes([10]) + struct.pack("<i", 0)),
            named(10, "palette", compound([
                named(10, "default", compound([
                    named(9, "block_palette", bytes([10]) + struct.pack("<i", len(palette_names)) + palette),
                    named(10, "block_position_data", compound([])),
                ]))
            ])),
        ])),
    ])
    return root


def stable_zip(output: Path, roots: list[tuple[Path, str]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        files = sorted(
            (path, "/".join(filter(None, (prefix, path.relative_to(root).as_posix()))))
            for root, prefix in roots for path in root.rglob("*") if path.is_file()
        )
        for path, arcname in files:
            info = zipfile.ZipInfo(arcname, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    # Runtime outputs are wholly generated. Reports and the prototype directory
    # can also contain Main-Codex review/qualification evidence, so never delete
    # either tree during a feature-local rebuild.
    for path in (BP, RP, FEATURE / "dist"):
        if path.exists():
            shutil.rmtree(path)
    spec = {
        "schema_version": 1,
        "label": LABEL,
        "identifier": "ccoriginal_cc:signal_ruin",
        "size": [11, 9, 11],
        "origin": [5, 0, 5],
        "shape_grammar": "Asymmetrical broken stone ring surrounding a forked cedar signal mast, three rune plates, and an east-facing interaction plinth.",
        "palette": ["minecraft:mossy_cobblestone", "minecraft:cobblestone", "minecraft:stripped_spruce_log", "minecraft:chiseled_stone_bricks", "minecraft:ochre_froglight"],
        "blocks": [],
    }
    # Broken, deliberately asymmetric ring.
    ring = [(x, z) for x in range(1, 10) for z in range(1, 10)
            if (x in (1, 9) or z in (1, 9)) and (x, z) not in {(1, 4), (1, 5), (4, 9), (5, 9), (9, 7)}]
    for i, (x, z) in enumerate(ring):
        spec["blocks"].append({"pos": [x, 0, z], "block": "minecraft:mossy_cobblestone" if i % 3 else "minecraft:cobblestone"})
    # Split mast and diagonal branch tips, within 9 blocks tall.
    for y in range(1, 8):
        spec["blocks"].append({"pos": [5, y, 5], "block": "minecraft:stripped_spruce_log"})
    for pos in ([4, 7, 5], [3, 8, 5], [6, 7, 5], [7, 8, 5]):
        spec["blocks"].append({"pos": pos, "block": "minecraft:stripped_spruce_log"})
    for pos in ([2, 1, 2], [8, 1, 3], [3, 1, 8]):
        spec["blocks"].append({"pos": pos, "block": "minecraft:chiseled_stone_bricks"})
    spec["blocks"] += [
        {"pos": [8, 1, 5], "block": "minecraft:chiseled_stone_bricks"},
        {"pos": [8, 2, 5], "block": "minecraft:ochre_froglight"},
    ]
    write_json(PROTO / "signal_ruin.structure.json", spec)
    write_json(PROTO / "originality-and-authoring.json", {
        "label": LABEL, "authorship": "Original deterministic Python-authored block composition.",
        "third_party_expression": "NONE", "java_evidence": "NOT_APPLICABLE",
        "visual_intent": spec["shape_grammar"], "editable_source": "signal_ruin.structure.json",
    })
    structure = structure_nbt(spec)
    structure_path = BP / "structures/ccoriginal_cc/signal_ruin.mcstructure"
    structure_path.parent.mkdir(parents=True, exist_ok=True)
    structure_path.write_bytes(structure)

    bp_manifest = {
        "format_version": 2,
        "header": {"name": "Signal Ruin - " + LABEL, "description": LABEL, "uuid": "556acdce-2ddc-4cbd-b08d-f62681387306", "version": [0, 1, 0], "min_engine_version": [1, 21, 80]},
        "modules": [
            {"type": "data", "uuid": "59c9ac60-a5ba-44a2-8517-c1f7a2fd51e3", "version": [0, 1, 0]},
            {"type": "script", "language": "javascript", "entry": "scripts/signal_ruin.js", "uuid": "45e8f7ad-197e-45ff-99ee-60b6fec7e30d", "version": [0, 1, 0]},
        ],
        "dependencies": [
            {"uuid": "f15d006f-c77c-45e5-a6d8-84da52a5db0e", "version": [0, 1, 0]},
            {"module_name": "@minecraft/server", "version": "2.0.0"},
        ],
        "metadata": {"authors": ["Original Bedrock-native production"], "product_type": "addon"},
    }
    rp_manifest = {
        "format_version": 2,
        "header": {"name": "Signal Ruin Resources - " + LABEL, "description": LABEL, "uuid": "f15d006f-c77c-45e5-a6d8-84da52a5db0e", "version": [0, 1, 0], "min_engine_version": [1, 21, 80], "pack_scope": "world"},
        "modules": [{"type": "resources", "uuid": "214f239c-6fe6-44b1-b69f-38c9b005a3dd", "version": [0, 1, 0]}],
        "dependencies": [{"uuid": "556acdce-2ddc-4cbd-b08d-f62681387306", "version": [0, 1, 0]}],
    }
    write_json(BP / "manifest.json", bp_manifest)
    write_json(RP / "manifest.json", rp_manifest)
    write_json(BP / "entities/signal_ruin_anchor.json", {
        "format_version": "1.21.80", "minecraft:entity": {
            "description": {"identifier": "ccoriginal_cc:signal_ruin_anchor", "is_spawnable": False, "is_summonable": True},
            "components": {
                "minecraft:type_family": {"family": ["signal_ruin_anchor", "inanimate"]},
                "minecraft:collision_box": {"width": 0.8, "height": 1.0},
                "minecraft:health": {"value": 1, "max": 1},
                "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": False}]},
                "minecraft:physics": {"has_gravity": False, "has_collision": False},
                "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
                "minecraft:interact": {"interactions": [{"interact_text": "action.interact.signal_ruin", "on_interact": {"event": "ccoriginal_cc:signal_ruin_activation", "target": "self"}}]},
            },
            "events": {"ccoriginal_cc:signal_ruin_activation": {}},
        }
    })
    write_json(RP / "entity/signal_ruin_anchor.entity.json", {
        "format_version": "1.10.0", "minecraft:client_entity": {"description": {
            "identifier": "ccoriginal_cc:signal_ruin_anchor",
            "materials": {"default": "entity_alphatest"}, "textures": {"default": "textures/entity/signal_ruin_anchor"},
            "geometry": {"default": "geometry.ccoriginal_cc.signal_ruin_anchor"},
            "render_controllers": ["controller.render.signal_ruin_anchor"],
        }}
    })
    write_json(RP / "models/entity/signal_ruin_anchor.geo.json", {
        "format_version": "1.12.0", "minecraft:geometry": [{"description": {
            "identifier": "geometry.ccoriginal_cc.signal_ruin_anchor", "texture_width": 16, "texture_height": 16,
            "visible_bounds_width": 2, "visible_bounds_height": 2, "visible_bounds_offset": [0, 1, 0]},
            "bones": [{"name": "root", "pivot": [0, 0, 0], "cubes": [
                {"origin": [-5, 0, -5], "size": [10, 3, 10], "uv": [0, 0]},
                {"origin": [-2, 3, -2], "size": [4, 8, 4], "uv": [0, 3]},
            ]}]}]
    })
    # Small original 16x16 RGBA amber/charcoal checker PNG.
    def chunk(kind: bytes, data: bytes) -> bytes:
        import zlib
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    import zlib
    rows = []
    for y in range(16):
        row = bytearray([0])
        for x in range(16):
            row += bytes((214, 154, 48, 255) if (x // 4 + y // 4) % 2 else (45, 49, 43, 255))
        rows.append(bytes(row))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b"")
    texture = RP / "textures/entity/signal_ruin_anchor.png"
    texture.parent.mkdir(parents=True, exist_ok=True)
    texture.write_bytes(png)
    write_json(RP / "render_controllers/signal_ruin.render_controllers.json", {
        "format_version": "1.8.0", "render_controllers": {"controller.render.signal_ruin_anchor": {
            "geometry": "Geometry.default", "materials": [{"*": "Material.default"}], "textures": ["Texture.default"]}}
    })
    write_json(RP / "texts/languages.json", ["en_US"])
    write_text(RP / "texts/en_US.lang", f"entity.ccoriginal_cc:signal_ruin_anchor.name=Signal Ruin Anchor\npack.name={LABEL}\naction.interact.signal_ruin=Awaken Signal Ruin\n")
    write_json(BP / "loot_tables/ccoriginal_cc/signal_ruin_cache.json", {
        "pools": [{"rolls": 1, "entries": [{"type": "item", "name": "minecraft:chest", "weight": 1,
            "functions": [{"function": "set_name", "name": "Signal Ruin Shared Cache"}]}]},
            {"rolls": 1, "entries": [{"type": "item", "name": "minecraft:emerald", "weight": 3,
                                      "functions": [{"function": "set_count", "count": {"min": 2, "max": 5}}]},
                                     {"type": "item", "name": "minecraft:golden_apple", "weight": 1}]}]
    })
    functions = {
        "place": f"# {LABEL}\nstructure load ccoriginal_cc:signal_ruin ~ ~ ~\nsummon ccoriginal_cc:signal_ruin_anchor ~8.5 ~1 ~5.5\n",
        "stress": f"# {LABEL}\nfunction ccoriginal_cc/signal_ruin/cleanup\nstructure load ccoriginal_cc:signal_ruin ~ ~ ~\nsummon ccoriginal_cc:signal_ruin_anchor ~8.5 ~1 ~5.5\nstructure load ccoriginal_cc:signal_ruin ~24 ~ ~\nsummon ccoriginal_cc:signal_ruin_anchor ~32.5 ~1 ~5.5\n",
        "cleanup": f"# {LABEL}\nkill @e[type=ccoriginal_cc:signal_ruin_anchor]\nkill @e[tag=ccoriginal_cc_signal_ruin_mob]\n",
    }
    for name, body in functions.items():
        write_text(BP / f"functions/ccoriginal_cc/signal_ruin/{name}.mcfunction", body)
    write_text(BP / "functions/ccoriginal_cc/signal_ruin/INTERNAL-TEST-ONLY.txt", LABEL + "\n")
    write_text(BP / "scripts/signal_ruin.js", SCRIPT)
    write_json(FEATURE / "tests/scenarios.json", {
        "label": LABEL, "scenarios": [
            "single activation and three-wave completion", "two-player activation contention",
            "four-player shared completion", "duplicate reward refusal", "disconnect and late join",
            "restart in every active phase", "corrupt-state fallback", "failure cleanup to zero",
            "two-instance worst-credible load",
        ]
    })
    write_json(FEATURE / "reports/readiness-matrix.json", {
        "label": LABEL, "static": "PASSED_BY_FEATURE_TEST", "blockbench_native_roundtrip": "PENDING_MAIN_CODEX",
        "creator_tools": "PENDING_MAIN_CODEX", "stable_bds": "PENDING_MAIN_CODEX", "bedrock_desktop": "UNEXECUTED",
        "persistence_multiplayer": "UNEXECUTED", "performance": "UNEXECUTED",
        "physical_ps4": "NOT_PHYSICAL_PS4_CERTIFIED", "marketplace": "NOT_MARKETPLACE_APPROVED",
    })
    write_json(FEATURE / "reports/provenance.json", {
        "label": LABEL, "production_lane": "ORIGINAL_BEDROCK_NATIVE", "third_party_assets": [],
        "source_expression_used": False, "java_evidence": "NOT_APPLICABLE",
        "inputs": ["consumer-safe original production manifest", "reserved identifiers and UUIDs"],
    })
    addon = FEATURE / "dist/signal-ruin-INTERNAL-TEST.mcaddon"
    stable_zip(addon, [(BP, "signal_ruin_BP"), (RP, "signal_ruin_RP")])
    write_text(FEATURE / "dist/README-INTERNAL-TEST.txt",
               LABEL + "\nImport the mcaddon, enable both packs in an existing internal-test world, then run /function ccoriginal_cc/signal_ruin/place.\n"
               "A .mcworld is intentionally not emitted because this feature-local builder does not own a qualified Bedrock world database.\n")
    artifact_rows = []
    generated_roots = (BP, RP, FEATURE / "dist")
    generated_files = [
        p for root in generated_roots for p in root.rglob("*") if p.is_file()
    ] + [
        FEATURE / "tests/scenarios.json",
        PROTO / "signal_ruin.structure.json",
        PROTO / "originality-and-authoring.json",
    ]
    for path in sorted(generated_files):
        artifact_rows.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    write_json(FEATURE / "reports/artifact-manifest.json", {"label": LABEL, "artifacts": artifact_rows,
        "package_sha256": {"mcaddon": sha(addon)}, "mcworld": "NOT_EMITTED_NO_QUALIFIED_WORLD_DATABASE"})


SCRIPT = r'''import { world, system } from "@minecraft/server";
const NS = "ccoriginal_cc:signal_ruin_";
const VALID = new Set(["READY","ACTIVE_WAVE_1","ACTIVE_WAVE_2","ACTIVE_WAVE_3","REWARD_READY","COMPLETE"]);
const CAP = 12;
const INSTANCE_CAP = 2;
const ENCOUNTER_SECONDS_CAP = 80;
function get(a,k,d){ const v=a.getDynamicProperty(NS+k); return v===undefined?d:v; }
function set(a,k,v){ a.setDynamicProperty(NS+k,v); }
function state(a){
  const reward=!!get(a,"reward_issued",false), raw=String(get(a,"state","READY"));
  if(reward) return "COMPLETE";
  return VALID.has(raw)?raw:"READY";
}
function mobs(a){ const id=String(get(a,"instance",a.id)).replace(/[^A-Za-z0-9_-]/g,"_"); return a.dimension.getEntities({tags:["ccoriginal_cc_signal_ruin_mob","sri_"+id]}); }
function clean(a){ for(const e of mobs(a)) e.remove(); set(a,"token",Number(get(a,"token",0))+1); }
function activeInstances(){
  let count=0;
  for(const d of ["overworld","nether","the_end"].map(x=>world.getDimension(x)))
    for(const a of d.getEntities({type:"ccoriginal_cc:signal_ruin_anchor"}))
      if(state(a).startsWith("ACTIVE_")) count++;
  return count;
}
function spawnWave(a,w){
  const token=Number(get(a,"token",0))+1; set(a,"token",token); set(a,"state","ACTIVE_WAVE_"+w); set(a,"wave",w);
  const id=String(get(a,"instance",a.id)).replace(/[^A-Za-z0-9_-]/g,"_");
  const types=w===1?["minecraft:zombie","minecraft:zombie","minecraft:spider"]:w===2?["minecraft:skeleton","minecraft:skeleton","minecraft:zombie","minecraft:spider"]:["minecraft:husk","minecraft:skeleton","minecraft:zombie","minecraft:spider","minecraft:spider"];
  for(let i=0;i<types.length && mobs(a).length<CAP;i++){ const q=a.dimension.spawnEntity(types[i],{x:a.location.x+(i%3-1)*4,y:a.location.y,z:a.location.z+(Math.floor(i/3)*3+4)}); q.addTag("ccoriginal_cc_signal_ruin_mob"); q.addTag("sri_"+id); }
}
function reward(a){
  if(get(a,"reward_issued",false)) { set(a,"state","COMPLETE"); return; }
  set(a,"state","REWARD_READY"); set(a,"reward_issued",true);
  a.dimension.runCommand(`loot spawn ${a.location.x} ${a.location.y+1} ${a.location.z} loot "ccoriginal_cc/signal_ruin_cache"`);
  set(a,"state","COMPLETE"); world.sendMessage("Signal Ruin completed. One shared cache has formed.");
}
function activate(a,p){
  if(state(a)!=="READY"){ p.sendMessage(state(a)==="COMPLETE"?"This Signal Ruin is quiet; its cache was already issued.":"This Signal Ruin is already active."); return; }
  if(activeInstances()>=INSTANCE_CAP){ p.sendMessage("Only two Signal Ruins may be active at once. This ruin remains ready."); return; }
  set(a,"schema",1); set(a,"instance",a.id); set(a,"reward_issued",false); set(a,"absent_seconds",0); set(a,"elapsed_seconds",0); spawnWave(a,1);
}
world.afterEvents.playerInteractWithEntity.subscribe(e=>{ if(e.target.typeId==="ccoriginal_cc:signal_ruin_anchor") activate(e.target,e.player); });
world.afterEvents.worldLoad.subscribe(()=>system.runTimeout(()=>{
  for(const d of ["overworld","nether","the_end"].map(x=>world.getDimension(x))) for(const a of d.getEntities({type:"ccoriginal_cc:signal_ruin_anchor"})){
    const s=state(a); if(s==="COMPLETE"){set(a,"state","COMPLETE");continue;} if(s.startsWith("ACTIVE_")){clean(a);set(a,"elapsed_seconds",0);spawnWave(a,Math.max(1,Math.min(3,Number(get(a,"wave",1)))));}
  }
},1));
system.runInterval(()=>{
  for(const d of ["overworld","nether","the_end"].map(x=>world.getDimension(x))) for(const a of d.getEntities({type:"ccoriginal_cc:signal_ruin_anchor"})){
    const s=state(a); if(!s.startsWith("ACTIVE_")) continue;
    const elapsed=Number(get(a,"elapsed_seconds",0))+1; set(a,"elapsed_seconds",elapsed);
    if(elapsed>=ENCOUNTER_SECONDS_CAP){ clean(a); set(a,"state","READY"); set(a,"wave",0); set(a,"absent_seconds",0); set(a,"elapsed_seconds",0); continue; }
    const near=d.getPlayers({location:a.location,maxDistance:32});
    if(!near.length){ const absent=Number(get(a,"absent_seconds",0))+1; set(a,"absent_seconds",absent); if(absent>=20){clean(a);set(a,"state","READY");set(a,"wave",0);set(a,"elapsed_seconds",0);} continue; }
    set(a,"absent_seconds",0);
    if(mobs(a).length===0){ const w=Number(get(a,"wave",1)); if(w<3) spawnWave(a,w+1); else reward(a); }
  }
},20);
'''

if __name__ == "__main__":
    main()
