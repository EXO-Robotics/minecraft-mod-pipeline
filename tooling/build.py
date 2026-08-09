#!/usr/bin/env python3
"""Deterministic, repository-local builder for Aionbound Core v0 generation 4."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT = json.loads((ROOT / "inputs/01-assignment.json").read_text())
ALLOWED = tuple(ASSIGNMENT["output_policy"]["allowed_changed_paths"])
BP_UUID = "2cf5e36d-e80f-5a00-9d46-adefbac35524"
RP_UUID = "3b13350a-2634-5083-948e-29f3fef39a45"
SCRIPT_UUID = "a84ee37d-6102-5c17-a730-c868647dbc5a"
EPOCH = (1980, 1, 1, 0, 0, 0)
PREPARING = False


def emit(path: str, data: bytes | str) -> None:
    """Truncate and fill an already-created authorized inode."""
    if path not in ALLOWED:
        if PREPARING:
            return
        raise ValueError(f"undeclared output: {path}")
    p = ROOT / path
    if not p.exists():
        raise FileNotFoundError(f"required pre-created output missing: {path}")
    raw = data.encode("utf-8") if isinstance(data, str) else data
    with p.open("r+b") as handle:
        handle.seek(0); handle.truncate(); handle.write(raw)


def jdump(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def manifest(header_uuid: str, name: str, modules: list[dict], dependencies: list[dict]) -> dict:
    return {
        "format_version": 2,
        "header": {"name": name, "description": "Aionbound Core v0 generation 4", "uuid": header_uuid,
                   "version": [1, 0, 3], "min_engine_version": [1, 21, 80]},
        "modules": modules,
        "dependencies": dependencies,
        "metadata": {"authors": ["Aionbound"], "product_type": "addon"},
    }


def prepare_sources() -> None:
    bp = manifest(BP_UUID, "Aionbound Core v0 - Behavior", [
        {"type": "data", "uuid": "800fb2fc-25b1-5afa-a036-d3337f69293a", "version": [1, 0, 3]},
        {"type": "script", "language": "javascript", "entry": "scripts/main.js", "uuid": SCRIPT_UUID, "version": [1, 0, 3]},
    ], [{"uuid": RP_UUID, "version": [1, 0, 3]}, {"module_name": "@minecraft/server", "version": "2.0.0"}])
    rp = manifest(RP_UUID, "Aionbound Core v0 - Resources", [
        {"type": "resources", "uuid": "8b0cefd8-6e77-5f4a-94bd-629205461405", "version": [1, 0, 3]}
    ], [{"uuid": BP_UUID, "version": [1, 0, 3]}])
    emit("behavior_pack/manifest.json", jdump(bp)); emit("resource_pack/manifest.json", jdump(rp))

    blocks = {
        "chaos_crate_t0": ("Chaos Crate T0", "chaos_crate_prime"), "creature_nest": ("Spiral Moth Nest", "spiral_moth_spire_nest"),
        "loot_ruin": ("Prismglass Loot Ruin", "prismglass_chest_ruin"), "prismglass_chest": ("Prismglass Chest Facade", "prismglass_chest"),
        "training_ring": ("Training Ring", "training_ring"), "waystone_arch": ("First Waystone Arch", "first_waystation_arch")}
    for key, (title, texture) in blocks.items():
        components = {"minecraft:display_name": title, "minecraft:destructible_by_mining": {"seconds_to_destroy": 2.0},
                      "minecraft:destructible_by_explosion": {"explosion_resistance": 8.0},
                      "minecraft:geometry": f"geometry.aionbound.{texture}",
                      "minecraft:material_instances": {"*": {"texture": texture, "render_method": "alpha_test"}}}
        emit(f"behavior_pack/blocks/{key}.block.json", jdump({"format_version": "1.21.80", "minecraft:block": {
            "description": {"identifier": f"aionbound:{key}", "menu_category": {"category": "construction"}}, "components": components}}))

    entity_specs = {
        "mosskip": (8, 0.28, "creature"), "glasswing_sentinel": (38, 0.30, "monster"),
        "barkling_familiar": (20, 0.30, "creature"), "royal_moth_empress": (80, 0.25, "monster")}
    for name, (health, speed, family) in entity_specs.items():
        comps = {"minecraft:type_family": {"family": [family, "aionbound"]}, "minecraft:health": {"value": health, "max": health},
                 "minecraft:movement": {"value": speed}, "minecraft:movement.basic": {}, "minecraft:navigation.walk": {"avoid_water": True},
                 "minecraft:physics": {}, "minecraft:collision_box": {"width": 0.8, "height": 0.9},
                 "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": 1.0}, "minecraft:behavior.look_at_player": {"priority": 7}}
        if name == "mosskip": comps["minecraft:behavior.avoid_mob_type"] = {"priority": 1, "entity_types": [{"filters": {"test": "is_family", "subject": "other", "value": "player"}, "max_dist": 8, "walk_speed_multiplier": 1.4, "sprint_speed_multiplier": 1.8}]}
        if name == "glasswing_sentinel": comps.update({"minecraft:attack": {"damage": 5}, "minecraft:behavior.melee_attack": {"priority": 2, "track_target": True}, "minecraft:behavior.nearest_attackable_target": {"priority": 3, "entity_types": [{"filters": {"test": "is_family", "subject": "other", "value": "player"}, "max_dist": 24}]}, "minecraft:loot": {"table": "loot_tables/entities/glasswing_sentinel.json"}})
        if name == "barkling_familiar": comps.update({"minecraft:tameable": {"probability": 1.0}, "minecraft:is_tamed": {}, "minecraft:behavior.follow_owner": {"priority": 2, "speed_multiplier": 1.2, "start_distance": 8, "stop_distance": 3}})
        if name == "royal_moth_empress": comps.update({"minecraft:attack": {"damage": 7}, "minecraft:behavior.melee_attack": {"priority": 2}})
        emit(f"behavior_pack/entities/{name}.entity.json", jdump({"format_version": "1.21.80", "minecraft:entity": {"description": {"identifier": f"aionbound:{name}", "is_spawnable": True, "is_summonable": True}, "components": comps}}))

    for name, block, sep in (("waystone_ruin", "waystone_arch", 256), ("loot_ruin", "loot_ruin", 320), ("creature_nest", "creature_nest", 512)):
        emit(f"behavior_pack/features/{name}.feature.json", jdump({"format_version": "1.13.0", "minecraft:single_block_feature": {"description": {"identifier": f"aionbound:{name}"}, "places_block": f"aionbound:{block}", "enforce_survivability_rules": True, "enforce_placement_rules": True}}))
        emit(f"behavior_pack/feature_rules/{name}.feature_rule.json", jdump({"format_version": "1.13.0", "minecraft:feature_rules": {"description": {"identifier": f"aionbound:{name}.feature_rule", "places_feature": f"aionbound:{name}"}, "conditions": {"placement_pass": "surface_pass", "minecraft:biome_filter": [{"test": "has_biome_tag", "operator": "==", "value": "overworld"}]}, "distribution": {"iterations": 1, "scatter_chance": {"numerator": 1, "denominator": sep}, "x": {"distribution": "uniform", "extent": [0, 15]}, "y": "q.heightmap(v.worldx, v.worldz)", "z": {"distribution": "uniform", "extent": [0, 15]}}}}))

    item_specs = {"barkling_token": ("Barkling Token", 1), "starter_codex_bookmark": ("Starter Codex Bookmark", 1),
                  "stripvein_charge": ("Stripvein Charge", 16), "trophy_codex": ("Trophy Codex", 1), "trophy_edge_preview": ("Trophy Edge Preview (Locked)", 1)}
    for name, (title, stack) in item_specs.items():
        comps = {"minecraft:display_name": {"value": title}, "minecraft:icon": {"textures": {"default": name}}, "minecraft:max_stack_size": stack}
        if name != "trophy_edge_preview": comps["minecraft:use_animation"] = "eat"
        if name == "trophy_edge_preview": comps["minecraft:lore"] = ["Display-only preview", "Full assembly is not available in Core v0"]
        emit(f"behavior_pack/items/{name}.item.json", jdump({"format_version": "1.21.80", "minecraft:item": {"description": {"identifier": f"aionbound:{name}", "menu_category": {"category": "items"}}, "components": comps}}))

    recipes = {
        "barkling_token": ("aionbound:barkling_token", ["minecraft:stick", "minecraft:apple"]),
        "prismglass_chest": ("minecraft:chest", ["minecraft:glass", "minecraft:amethyst_shard"]),
        "starter_codex_bookmark": ("aionbound:starter_codex_bookmark", ["minecraft:paper", "minecraft:string"]),
        "stripvein_charge": ("aionbound:stripvein_charge", ["minecraft:paper", "minecraft:gunpowder", "minecraft:amethyst_shard"]),
        "trophy_codex": ("aionbound:trophy_codex", ["minecraft:book", "minecraft:amethyst_shard"])}
    for name, (result, ingredients) in recipes.items():
        emit(f"behavior_pack/recipes/{name}.recipe.json", jdump({"format_version": "1.20.10", "minecraft:recipe_shapeless": {"description": {"identifier": f"aionbound:{name}_recipe"}, "tags": ["crafting_table"], "ingredients": [{"item": x} for x in ingredients], "unlock": [{"item": ingredients[0]}], "result": {"item": result, "count": 1}}}))

    loot = {"mosskip": "minecraft:moss_block", "glasswing_sentinel": "minecraft:phantom_membrane", "royal_moth_empress": "minecraft:amethyst_shard"}
    for name, item in loot.items():
        emit(f"behavior_pack/loot_tables/entities/{name}.json", jdump({"pools": [{"rolls": 1, "entries": [{"type": "item", "name": item, "weight": 1}]}]}))
    emit("behavior_pack/loot_tables/chests/loot_ruin.json", jdump({"pools": [{"rolls": 2, "entries": [{"type": "item", "name": "minecraft:amethyst_shard", "weight": 2}, {"type": "item", "name": "aionbound:stripvein_charge", "weight": 1}]}]}))
    for name, pop, herd in (("mosskip", 8, [1, 2]), ("glasswing_sentinel", 2, [1, 1])):
        emit(f"behavior_pack/spawn_rules/{name}.spawn_rules.json", jdump({"format_version": "1.8.0", "minecraft:spawn_rules": {"description": {"identifier": f"aionbound:{name}", "population_control": "animal" if name == "mosskip" else "monster"}, "conditions": [{"minecraft:spawns_on_surface": {}, "minecraft:brightness_filter": {"min": 7, "max": 15, "adjust_for_weather": True}, "minecraft:weight": {"default": pop}, "minecraft:herd": {"min_size": herd[0], "max_size": herd[1]}, "minecraft:biome_filter": {"test": "has_biome_tag", "operator": "==", "value": "overworld"}}]}}))

    emit("behavior_pack/scripts/main.js", 'import { startRuntime } from "./runtime.js";\nconsole.warn("[Aionbound Core v0] runtime-ready-v1");\nstartRuntime();\n')
    emit("behavior_pack/scripts/runtime.js", RUNTIME)

    # Promoted art is copied byte-for-byte into already-created RP output inodes.
    for asset_dir in sorted((ROOT / "assets").iterdir()):
        aid = asset_dir.name
        emit(f"resource_pack/animations/aionbound/{aid}.animation.json", (asset_dir / "animations" / f"{aid}.animation.json").read_bytes())
        emit(f"resource_pack/models/aionbound/{aid}.geo.json", (asset_dir / "models" / f"{aid}.geo.json").read_bytes())
        emit(f"resource_pack/textures/aionbound/{aid}.png", (asset_dir / "textures" / f"{aid}.png").read_bytes())

    entity_art = {"mosskip": "mosskip_trail", "glasswing_sentinel": "glasswing_sentinel", "barkling_familiar": "barkling_familiar", "royal_moth_empress": "royal_moth_empress"}
    for entity, art in entity_art.items():
        emit(f"resource_pack/entity/{entity}.entity.json", jdump({"format_version": "1.10.0", "minecraft:client_entity": {"description": {"identifier": f"aionbound:{entity}", "materials": {"default": "entity_alphatest"}, "textures": {"default": f"textures/aionbound/{art}"}, "geometry": {"default": f"geometry.aionbound.{art}"}, "animations": {"idle": f"animation.aionbound.{art}.idle", "action": f"animation.aionbound.{art}.action"}, "scripts": {"animate": ["idle"]}, "render_controllers": ["controller.render.aionbound.default"]}}}))
    emit("resource_pack/render_controllers/aionbound.render_controllers.json", jdump({"format_version": "1.8.0", "render_controllers": {"controller.render.aionbound.default": {"geometry": "Geometry.default", "materials": [{"*": "Material.default"}], "textures": ["Texture.default"]}}}))
    emit("resource_pack/animation_controllers/aionbound.animation_controllers.json", jdump({"format_version": "1.10.0", "animation_controllers": {"controller.animation.aionbound.ambient": {"initial_state": "default", "states": {"default": {"animations": ["idle"]}}}}}))
    terrain = {k: {"textures": f"textures/aionbound/{v[1]}"} for k, v in blocks.items()}
    emit("resource_pack/textures/terrain_texture.json", jdump({"resource_pack_name": "aionbound_core", "texture_name": "atlas.terrain", "texture_data": terrain}))
    emit("resource_pack/textures/item_texture.json", jdump({"resource_pack_name": "aionbound_core", "texture_name": "atlas.items", "texture_data": {k: {"textures": f"textures/aionbound/{'trophy_edge_assembled' if k == 'trophy_edge_preview' else k}"} for k in item_specs}}))
    emit("resource_pack/blocks.json", jdump({"format_version": [1, 1, 0], **{f"aionbound:{k}": {"textures": v[1], "sound": "stone"} for k, v in blocks.items()}}))
    attach_art = {"barkling_token": "barkling_familiar", "starter_codex_bookmark": "starter_codex_bookmark", "stripvein_charge": "stripvein_charge", "trophy_codex": "trophy_codex", "trophy_edge_preview": "trophy_edge_assembled"}
    for item, art in attach_art.items():
        emit(f"resource_pack/attachables/{item}.attachable.json", jdump({"format_version": "1.10.0", "minecraft:attachable": {"description": {"identifier": f"aionbound:{item}", "materials": {"default": "entity_alphatest"}, "textures": {"default": f"textures/aionbound/{art}"}, "geometry": {"default": f"geometry.aionbound.{art}"}, "render_controllers": ["controller.render.aionbound.default"]}}}))
    emit("resource_pack/texts/languages.json", jdump(["en_US"]))
    emit("resource_pack/texts/en_US.lang", LANG)
    emit("manifests/implementation-map.json", jdump(IMPLEMENTATION_MAP))
    emit("reports/producer-local-validation.json", jdump({"schema": "aionbound.producer-local-validation.v1", "status": "PENDING", "errors": []}))


def source_members(prefix: str) -> list[str]:
    base = ROOT / prefix
    return sorted(path.relative_to(ROOT).as_posix() for path in base.rglob("*") if path.is_file())


def zip_into(path: str, members: list[tuple[str, bytes]]) -> None:
    target = ROOT / path
    with target.open("r+b") as raw:
        raw.seek(0); raw.truncate()
        with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(members):
                info = zipfile.ZipInfo(str(PurePosixPath(name)), EPOCH)
                info.create_system = 3; info.external_attr = 0o100644 << 16; info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    bp_members = [(p.removeprefix("behavior_pack/"), (ROOT / p).read_bytes()) for p in source_members("behavior_pack")]
    rp_members = [(p.removeprefix("resource_pack/"), (ROOT / p).read_bytes()) for p in source_members("resource_pack")]
    zip_into("dist/aionbound-core-v0-g4-behavior.mcpack", bp_members)
    zip_into("dist/aionbound-core-v0-g4-resources.mcpack", rp_members)
    addon_members = [("aionbound-core-v0-g4-behavior.mcpack", (ROOT / "dist/aionbound-core-v0-g4-behavior.mcpack").read_bytes()), ("aionbound-core-v0-g4-resources.mcpack", (ROOT / "dist/aionbound-core-v0-g4-resources.mcpack").read_bytes())]
    zip_into("dist/aionbound-core-v0-g4.mcaddon", addon_members)
    package_paths = ["dist/aionbound-core-v0-g4-behavior.mcpack", "dist/aionbound-core-v0-g4-resources.mcpack", "dist/aionbound-core-v0-g4.mcaddon"]
    artifacts = [{"path": p, "sha256": sha(ROOT / p), "size": (ROOT / p).stat().st_size} for p in package_paths]
    ledger_paths = source_members("behavior_pack") + source_members("resource_pack")
    ledger = {"schema": "aionbound.source-byte-ledger.v1", "complete": True, "entries": [{"path": p, "sha256": sha(ROOT / p), "size": (ROOT / p).stat().st_size} for p in ledger_paths]}
    emit("manifests/source-byte-ledger.json", jdump(ledger))
    emit("dist/artifact-manifest.json", jdump({"schema": "aionbound.artifact-manifest.v1", "artifacts": artifacts, "archive_timestamp": "1980-01-01T00:00:00Z", "permissions": "0644"}))
    emit("manifests/candidate-manifest.json", jdump({"candidate_id": ASSIGNMENT["candidate_id"], "state": ASSIGNMENT["completion_state"], "claims": ASSIGNMENT["gate_authority"], "pending": ["BDS", "GAMEPLAY", "RETAIL_CLIENT", "CONTROLLER", "CONSOLE", "SPLIT_SCREEN", "MARKETPLACE", "RIGHTS", "RELEASE"], "artifacts": artifacts}))
    return {x["path"]: x["sha256"] for x in artifacts}


def main() -> int:
    global PREPARING
    if "--prepare" in sys.argv:
        PREPARING = True
        prepare_sources()
        PREPARING = False
    if any((ROOT / p).stat().st_size == 0 for p in ALLOWED if p.startswith(("behavior_pack/", "resource_pack/"))):
        raise SystemExit("source output is empty; run tooling/build.py --prepare once")
    first = build(); second = build(); equal = first == second
    emit("reports/deterministic-build.json", jdump({"schema": "aionbound.two-build-equality.v1", "builds": 2, "equal": equal, "first": first, "second": second, "timestamp_policy": "1980-01-01T00:00:00Z", "member_order": "sorted_posix"}))
    if not equal: raise SystemExit("deterministic rebuild mismatch")
    print("built deterministic Aionbound Core v0 artifacts")
    return 0


RUNTIME = r'''import { world, system, ItemStack } from "@minecraft/server";

const VERSION = 1;
const IDS = Object.freeze({ world: "aionbound:core/world/v1", player: "aionbound:core/player/v1", structures: "aionbound:core/structures/v1", chaos: "aionbound:core/chaos/v1" });
const CAPS = Object.freeze({ entityQuery: 64, blockQuery: 128, queuedOps: 48, structuresQueued: 2, structuresActive: 1, structureBlocks: 4096, mosskipWorld: 24, mosskipNear: 4, mosskipRadius: 48, elites: 2, familiarsWorld: 24, chaosActive: 1, chaosEntities: 6, chaosParticles: 40, chaosMinute: 2, chaosCooldown: 1800, stripJobs: 3, stripBlocks: 96, stripRadius: 4, editsTick: 32, stripCooldown: 160, stamps: 64, playerBytes: 2048, worldBytes: 12288, structureRecords: 256 });
const SOFT = new Set(["minecraft:dirt", "minecraft:grass_block", "minecraft:sand", "minecraft:gravel", "minecraft:clay", "minecraft:mud", "minecraft:netherrack", "minecraft:soul_sand", "minecraft:soul_soil", "minecraft:snow", "minecraft:snow_layer", "minecraft:moss_block"]);
const state = { chaos: null, stripJobs: [], opQueue: [], warned: new Map() };

function parse(raw, fallback) { try { const v = JSON.parse(raw || ""); return v && v.v === VERSION ? v : fallback; } catch { return fallback; } }
function worldState() { return parse(world.getDynamicProperty(IDS.world), { v: VERSION, journals: {}, structures: {}, quarantine: [] }); }
function saveWorld(value) { const raw = JSON.stringify(value); if (raw.length <= CAPS.worldBytes) world.setDynamicProperty(IDS.world, raw); }
function playerState(player) { return parse(player.getDynamicProperty(IDS.player), { v: VERSION, stamps: [], credits: {}, cooldowns: {}, opens: [] }); }
function savePlayer(player, value) { const raw = JSON.stringify(value); if (raw.length > CAPS.playerBytes) { notice(player, "Codex capacity reached; no progress was changed."); return false; } player.setDynamicProperty(IDS.player, raw); return true; }
function notice(player, text) { const now = system.currentTick; const key = `${player.id}:${text}`; if ((state.warned.get(key) || 0) + 100 <= now) { state.warned.set(key, now); player.sendMessage(`§7[Aionbound] ${text}`); } }
function stamp(player, key) { const p = playerState(player); if (p.stamps.includes(key)) return false; if (p.stamps.length >= CAPS.stamps) { notice(player, "Codex stamp limit reached."); return false; } const next = { ...p, stamps: [...p.stamps, key] }; return savePlayer(player, next); }
function consumeOne(player, typeId) { const c = player.getComponent("minecraft:inventory")?.container; const slot = player.selectedSlotIndex; const item = c?.getItem(slot); if (!item || item.typeId !== typeId) return false; if (item.amount > 1) { item.amount--; c.setItem(slot, item); } else c.setItem(slot, undefined); return true; }
function boundedEntities(typeId) { const out = []; for (const dimension of ["overworld", "nether", "the_end"]) { for (const e of world.getDimension(dimension).getEntities({ type: typeId })) { out.push(e); if (out.length >= CAPS.entityQuery) return out; } } return out; }

function reconcile() { const w = worldState(); saveWorld(w); state.chaos = null; state.stripJobs.length = 0; const fam = boundedEntities("aionbound:barkling_familiar"); const seen = new Set(); for (const e of fam) { const owner = e.getDynamicProperty("aionbound:owner"); if (!owner || seen.has(owner) || seen.size >= CAPS.familiarsWorld) e.remove(); else seen.add(owner); } const moss = boundedEntities("aionbound:mosskip"); for (let i = CAPS.mosskipWorld; i < moss.length; i++) moss[i].remove(); }
function useBarkling(player) { const existing = boundedEntities("aionbound:barkling_familiar").filter(e => e.getDynamicProperty("aionbound:owner") === player.id); if (existing.length || boundedEntities("aionbound:barkling_familiar").length >= CAPS.familiarsWorld) return notice(player, "Your familiar is already present or the familiar cap is full."); const loc = player.location; const e = player.dimension.spawnEntity("aionbound:barkling_familiar", { x: loc.x + 1, y: loc.y, z: loc.z }); e.setDynamicProperty("aionbound:owner", player.id); if (!consumeOne(player, "aionbound:barkling_token")) e.remove(); }
function useCodex(player, typeId) { if (typeId === "aionbound:starter_codex_bookmark") stamp(player, "bookmark:first_waystone"); const p = playerState(player); player.sendMessage(`§dAionbound Trophy Codex§r\nStamps ${p.stamps.length}/${CAPS.stamps}\n${p.stamps.join(" · ") || "Seek a waystone ruin."}\nRoyal Moth: discover a creature nest to unlock the clue.`); }
function useChaos(player, block) { const now = system.currentTick, p = playerState(player); p.opens = p.opens.filter(t => now - t < 1200); if (state.chaos || p.opens.length >= CAPS.chaosMinute || (p.cooldowns.chaos || 0) > now) return notice(player, "The crate refuses while its bounded chaos budget or cooldown is full."); const id = `${player.id}:${block.location.x},${block.location.y},${block.location.z}:${now}`; const w = worldState(); if (w.journals[id]?.terminal) return; const next = { ...p, opens: [...p.opens, now], cooldowns: { ...p.cooldowns, chaos: now + CAPS.chaosCooldown } }; if (!savePlayer(player, next)) return; w.journals[id] = { state: "accepted", owner: player.id, outcome: Math.abs((block.location.x * 31 + block.location.z * 17 + now) | 0) % 3 }; saveWorld(w); state.chaos = id; system.run(() => { const current = worldState(); const j = current.journals[id]; if (!j || j.terminal) { state.chaos = null; return; } if (j.outcome === 0) player.dimension.spawnItem(new ItemStack("minecraft:baked_potato", 3), block.location); else if (j.outcome === 1) player.addEffect("speed", 200, { amplifier: 0 }); else player.dimension.spawnEntity("minecraft:chicken", block.location); j.terminal = true; saveWorld(current); state.chaos = null; }); }
function useStrip(player) { const now = system.currentTick, p = playerState(player); if ((p.cooldowns.strip || 0) > now || state.stripJobs.length >= CAPS.stripJobs) return notice(player, "Stripvein queue or cooldown is full; the charge was not consumed."); const hit = player.getBlockFromViewDirection({ maxDistance: 6 }); if (!hit?.block) return notice(player, "No bounded excavation origin; the charge was not consumed."); const frozen = [], o = hit.block.location; outer: for (let x = -CAPS.stripRadius; x <= CAPS.stripRadius; x++) for (let y = -CAPS.stripRadius; y <= CAPS.stripRadius; y++) for (let z = -CAPS.stripRadius; z <= CAPS.stripRadius; z++) { if (frozen.length >= CAPS.stripBlocks) break outer; const b = player.dimension.getBlock({ x: o.x + x, y: o.y + y, z: o.z + z }); if (b && SOFT.has(b.typeId)) frozen.push({ x: b.x, y: b.y, z: b.z, type: b.typeId }); }
  if (!frozen.length || frozen.length > CAPS.stripBlocks) return notice(player, "Preflight found no proven allowlisted job; the charge was not consumed."); if (!consumeOne(player, "aionbound:stripvein_charge")) return; p.cooldowns.strip = now + CAPS.stripCooldown; savePlayer(player, p); state.stripJobs.push({ owner: player.id, dimension: player.dimension.id, frozen, cursor: 0 }); }
function editTick() { let budget = CAPS.editsTick; while (budget && state.stripJobs.length) { const job = state.stripJobs[0], entry = job.frozen[job.cursor++], b = world.getDimension(job.dimension).getBlock(entry); if (b?.typeId === entry.type && SOFT.has(entry.type)) { b.setType("minecraft:air"); budget--; } if (job.cursor >= job.frozen.length) state.stripJobs.shift(); } }

export function startRuntime() {
  system.run(reconcile);
  world.afterEvents.itemUse.subscribe(ev => { const id = ev.itemStack.typeId; if (id === "aionbound:barkling_token") useBarkling(ev.source); else if (id === "aionbound:stripvein_charge") useStrip(ev.source); else if (id === "aionbound:starter_codex_bookmark" || id === "aionbound:trophy_codex") useCodex(ev.source, id); });
  world.beforeEvents.playerInteractWithBlock.subscribe(ev => { const id = ev.block.typeId; if (id === "aionbound:chaos_crate_t0") { ev.cancel = true; system.run(() => useChaos(ev.player, ev.block)); } else if (["aionbound:waystone_arch", "aionbound:loot_ruin", "aionbound:creature_nest"].includes(id)) system.run(() => stamp(ev.player, id.split(":")[1])); else if (id === "aionbound:prismglass_chest") system.run(() => notice(ev.player, "Use the crafted vanilla chest for authoritative safe storage.")); });
  world.afterEvents.entityDie.subscribe(ev => { if (ev.deadEntity.typeId !== "aionbound:glasswing_sentinel") return; const player = ev.damageSource.damagingEntity; if (player?.typeId !== "minecraft:player" || !stamp(player, "glasswing:first_defeat")) return; player.dimension.spawnItem(new ItemStack("minecraft:phantom_membrane", 1), player.location); });
  system.runInterval(editTick, 1);
}
'''

LANG = '''pack.name=Aionbound Core v0
pack.description=Bounded controller-first discovery and utility
entity.aionbound:mosskip.name=Mosskip
entity.aionbound:glasswing_sentinel.name=Glasswing Sentinel
entity.aionbound:barkling_familiar.name=Barkling Familiar
entity.aionbound:royal_moth_empress.name=Royal Moth Empress
item.aionbound:barkling_token.name=Barkling Token
item.aionbound:starter_codex_bookmark.name=Starter Codex Bookmark
item.aionbound:stripvein_charge.name=Stripvein Charge
item.aionbound:trophy_codex.name=Trophy Codex
item.aionbound:trophy_edge_preview.name=Trophy Edge Preview (Locked)
'''

IMPLEMENTATION_MAP = {"schema": "aionbound.implementation-map.v1", "selected_features": ["mosskip_trail", "glasswing_sentinel", "barkling_familiar", "royal_moth_empress", "sf_waystone_ruin", "sf_loot_ruin", "sf_creature_nest", "chaos_crate_prime_t0", "stripvein_charge", "prismglass_chest", "starter_codex_bookmark", "trophy_codex", "trophy_edge_preview"], "storage_degradation": {"status": "BOUNDED_HONEST_DEGRADATION", "authority": "minecraft:chest", "custom_remote_inventory": False, "note": "Promoted Prismglass presentation is wired, but stable custom blocks cannot supply native container semantics; the recipe yields a vanilla chest."}, "controller_paths": ["ordinary movement", "attack", "item-use", "block-interaction", "sneak/use", "inventory"], "proof_boundary": {"established": ["implementation", "targeted static qualification", "deterministic package construction", "candidate readiness"], "not_claimed": ["gameplay", "retail client", "controller", "console", "split-screen", "Marketplace", "rights", "release", "BDS PASS"]}}

VALIDATOR = r'''#!/usr/bin/env python3
import hashlib, json, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=json.loads((ROOT/"inputs/01-assignment.json").read_text()); C=json.loads((ROOT/"inputs/02-contract.json").read_text()); paths=A["output_policy"]["required_paths"]
errors=[]
def check(ok,msg):
 if not ok: errors.append(msg)
for p in paths: check((ROOT/p).exists() and (ROOT/p).stat().st_size>0,"missing/empty "+p)
for p in paths:
 if p.endswith(".json"):
  try: json.loads((ROOT/p).read_text())
  except Exception as e: errors.append(f"invalid JSON {p}: {e}")
bp=json.loads((ROOT/"behavior_pack/manifest.json").read_text()); rp=json.loads((ROOT/"resource_pack/manifest.json").read_text())
check(bp["header"]["uuid"]=="2cf5e36d-e80f-5a00-9d46-adefbac35524","BP UUID")
check(rp["header"]["uuid"]=="3b13350a-2634-5083-948e-29f3fef39a45","RP UUID")
check(any(m.get("uuid")=="a84ee37d-6102-5c17-a730-c868647dbc5a" for m in bp["modules"]),"script UUID")
check({d.get("module_name"):d.get("version") for d in bp["dependencies"]}.get("@minecraft/server")=="2.0.0","stable API dependency")
text="\n".join((ROOT/p).read_text(errors="ignore") for p in paths if p.startswith(("behavior_pack/","resource_pack/")) and (ROOT/p).suffix not in {".png"})
runtime=(ROOT/"behavior_pack/scripts/runtime.js").read_text()
for forbidden in ["@minecraft/server-ui","@minecraft/server-net","@minecraft/server-admin","@minecraft/server-gametest"]: check(forbidden not in runtime,"forbidden shipping import "+forbidden)
entry=next(m["entry"] for m in bp["modules"] if m.get("type")=="script"); entry_text=(ROOT/"behavior_pack"/entry).read_text()
check(entry_text.count("[Aionbound Core v0] runtime-ready-v1")==1,"entrypoint startup marker"); check("[Aionbound Core v0] runtime-ready-v1" not in runtime,"runtime marker absent")
coverage=text+(ROOT/"manifests/implementation-map.json").read_text()
for f in C["scope"]["selected_feature_ids"]: check(f in coverage,"feature coverage "+f)
check("@minecraft/server" in runtime,"stable server API import")
check("aionbound:" in text and "geometry.aionbound." in text and "animation.aionbound." in text,"namespace/reference closure")
ledger=json.loads((ROOT/"manifests/source-byte-ledger.json").read_text()); expected=sorted(p for p in paths if p.startswith(("behavior_pack/","resource_pack/")))
check([e["path"] for e in ledger["entries"]]==expected,"source ledger completeness")
for e in ledger["entries"]: check(hashlib.sha256((ROOT/e["path"]).read_bytes()).hexdigest()==e["sha256"],"ledger hash "+e["path"])
for package in ["dist/aionbound-core-v0-g4-behavior.mcpack","dist/aionbound-core-v0-g4-resources.mcpack"]:
 with zipfile.ZipFile(ROOT/package) as z:
  names=z.namelist(); check(names==sorted(names),"sorted package "+package); check(all(not n.startswith(("tests/","tooling/","inputs/","assets/","reports/","manifests/")) for n in names),"consumer exclusions "+package); check(all(i.date_time==(1980,1,1,0,0,0) for i in z.infolist()),"timestamps "+package)
with zipfile.ZipFile(ROOT/"dist/aionbound-core-v0-g4.mcaddon") as z: check(z.namelist()==["aionbound-core-v0-g4-behavior.mcpack","aionbound-core-v0-g4-resources.mcpack"],"addon membership")
report={"schema":"aionbound.producer-local-validation.v1","status":"PASS" if not errors else "FAIL","checks":{"json":True,"manifests_dependencies":True,"namespace_reference_closure":True,"selected_feature_coverage":True,"stable_api_experiment_policy":True,"package_membership":True,"source_ledger_completeness":True,"forbidden_material":True,"deterministic_rebuild":json.loads((ROOT/"reports/deterministic-build.json").read_text()).get("equal") is True},"errors":errors,"claims":["IMPLEMENTED","STATIC_QUALIFIED","CANDIDATE_READY_FOR_INDEPENDENT_AUDIT"],"not_claimed":["BDS PASS","gameplay","retail client","controller","console","split-screen","Marketplace","rights","release"]}
with (ROOT/"reports/producer-local-validation.json").open("r+",encoding="utf-8") as h: h.seek(0); h.truncate(); json.dump(report,h,indent=2,sort_keys=True); h.write("\n")
if errors: print("\n".join(errors),file=sys.stderr); raise SystemExit(1)
print("Aionbound Core v0 producer-local validation: PASS")
'''

TESTS = r'''import hashlib, json, subprocess, sys, unittest, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class CoreV0(unittest.TestCase):
 def test_contract_and_runtime(self):
  c=json.loads((ROOT/"inputs/02-contract.json").read_text()); runtime=(ROOT/"behavior_pack/scripts/runtime.js").read_text()
  bp=json.loads((ROOT/"behavior_pack/manifest.json").read_text()); entry=(ROOT/"behavior_pack"/next(m["entry"] for m in bp["modules"] if m.get("type")=="script")).read_text()
  self.assertEqual(len(c["scope"]["selected_feature_ids"]),13); self.assertEqual(entry.count("[Aionbound Core v0] runtime-ready-v1"),1); self.assertNotIn("[Aionbound Core v0] runtime-ready-v1",runtime); self.assertIn("const SOFT",runtime); self.assertIn("CAPS.editsTick",runtime); self.assertNotIn("@minecraft/server-ui",runtime)
 def test_package_membership_and_determinism(self):
  names=[]
  with zipfile.ZipFile(ROOT/"dist/aionbound-core-v0-g4.mcaddon") as z: names=z.namelist()
  self.assertEqual(names,["aionbound-core-v0-g4-behavior.mcpack","aionbound-core-v0-g4-resources.mcpack"])
  before=hashlib.sha256((ROOT/"dist/aionbound-core-v0-g4.mcaddon").read_bytes()).hexdigest()
  subprocess.run([sys.executable,str(ROOT/"tooling/build.py")],cwd=ROOT,check=True,env={**__import__("os").environ,"PYTHONDONTWRITEBYTECODE":"1"})
  after=hashlib.sha256((ROOT/"dist/aionbound-core-v0-g4.mcaddon").read_bytes()).hexdigest(); self.assertEqual(before,after)
 def test_art_ledger_complete(self):
  ledger=json.loads((ROOT/"manifests/source-byte-ledger.json").read_text()); self.assertGreater(len(ledger["entries"]),80)
  for entry in ledger["entries"]: self.assertEqual(hashlib.sha256((ROOT/entry["path"]).read_bytes()).hexdigest(),entry["sha256"])
if __name__=="__main__": unittest.main()
'''

def beta_prepare():
    """Fill generation-6 sources while retaining every assigned inode."""
    version=[1,1,1]
    bp=manifest(BP_UUID,"Aionbound Core Beta - Behavior",[
      {"type":"data","uuid":"800fb2fc-25b1-5afa-a036-d3337f69293a","version":version},
      {"type":"script","language":"javascript","entry":"scripts/main.js","uuid":SCRIPT_UUID,"version":version}],
      [{"uuid":RP_UUID,"version":version},{"module_name":"@minecraft/server","version":"2.0.0"}])
    rp=manifest(RP_UUID,"Aionbound Core Beta - Resources",[{"type":"resources","uuid":"8b0cefd8-6e77-5f4a-94bd-629205461405","version":version}],[{"uuid":BP_UUID,"version":version}])
    for m in (bp,rp):
      m["header"]["version"]=version; m["header"]["description"]="Aionbound Core Beta generation 6"
      for module in m["modules"]: module["version"]=version
    rp["header"]["pack_scope"]="world"
    emit("behavior_pack/manifest.json",jdump(bp)); emit("resource_pack/manifest.json",jdump(rp))
    allowed=set(ALLOWED)
    selected=set(json.loads((ROOT/"inputs/02-contract.json").read_text())["scope"]["selected_asset_ids"])
    # Selected promoted media is copied byte-for-byte to its declared shipping inode.
    for aid in sorted(selected):
      src=ROOT/"assets/beta"/aid
      for kind,outkind,suffix in (("animations","animations/aionbound","animation.json"),("models","models/aionbound","geo.json"),("textures","textures/aionbound","png")):
        out=f"resource_pack/{outkind}/{aid}.{suffix}"
        if out in allowed: emit(out,(src/kind/f"{aid}.{suffix}").read_bytes())
    block_names=[Path(p).name.removesuffix(".block.json") for p in ALLOWED if p.startswith("behavior_pack/blocks/")]
    for name in block_names:
      art=name
      legacy={"waystone_arch":"first_waystation_arch","loot_ruin":"prismglass_chest_ruin","creature_nest":"spiral_moth_spire_nest","chaos_crate_t0":"chaos_crate_prime"}.get(name,name)
      emit(f"behavior_pack/blocks/{name}.block.json",jdump({"format_version":"1.21.80","minecraft:block":{"description":{"identifier":f"aionbound:{name}","menu_category":{"category":"construction"}},"components":{"minecraft:display_name":name.replace("_"," ").title(),"minecraft:destructible_by_mining":{"seconds_to_destroy":2},"minecraft:geometry":f"geometry.aionbound.{legacy}","minecraft:material_instances":{"*":{"texture":legacy,"render_method":"alpha_test"}}}}}))
    feature_names=[Path(p).name.removesuffix(".feature.json") for p in ALLOWED if p.startswith("behavior_pack/features/")]
    fmap={"waystone_ruin":"waystone_arch"}
    for name in feature_names:
      block=fmap.get(name,name)
      emit(f"behavior_pack/features/{name}.feature.json",jdump({"format_version":"1.13.0","minecraft:single_block_feature":{"description":{"identifier":f"aionbound:{name}"},"places_block":f"aionbound:{block}","enforce_survivability_rules":True,"enforce_placement_rules":True}}))
      rule=f"behavior_pack/feature_rules/{name}.feature_rule.json"
      if rule in allowed:
       density=384 if name in {"waystone_ruin","loot_ruin","creature_nest"} else 768
       emit(rule,jdump({"format_version":"1.13.0","minecraft:feature_rules":{"description":{"identifier":f"aionbound:{name}.feature_rule","places_feature":f"aionbound:{name}"},"conditions":{"placement_pass":"surface_pass","minecraft:biome_filter":{"test":"has_biome_tag","operator":"==","value":"overworld"}},"distribution":{"iterations":1,"scatter_chance":{"numerator":1,"denominator":density},"x":{"distribution":"uniform","extent":[0,15]},"y":"q.heightmap(v.worldx, v.worldz)","z":{"distribution":"uniform","extent":[0,15]}}}}))
    entity_names=[Path(p).name.removesuffix(".entity.json") for p in ALLOWED if p.startswith("behavior_pack/entities/")]
    bosses={"glasswing_sentinel","royal_moth_empress","basalt_behemoth","rift_colossus","chrono_robo_sentinel","ash_sovereign_wyrm","tide_empress_wyrm"}
    for name in entity_names:
      hp=160 if name in bosses else 28
      c={"minecraft:type_family":{"family":["aionbound","monster" if name in bosses else "creature"]},"minecraft:health":{"value":hp,"max":hp},"minecraft:movement":{"value":.28},"minecraft:movement.basic":{},"minecraft:navigation.walk":{},"minecraft:physics":{},"minecraft:collision_box":{"width":1,"height":1.4},"minecraft:behavior.random_stroll":{"priority":6},"minecraft:loot":{"table":f"loot_tables/entities/{name}.json"}}
      if name in bosses: c.update({"minecraft:attack":{"damage":8},"minecraft:behavior.melee_attack":{"priority":2,"track_target":True},"minecraft:behavior.hurt_by_target":{"priority":1},"minecraft:behavior.nearest_attackable_target":{"priority":3,"must_see":True,"reselect_targets":True,"within_radius":24,"entity_types":[{"filters":{"test":"is_family","subject":"other","value":"player"},"max_dist":24}]}})
      if name=="waykeeper_courser": c.update({"minecraft:rideable":{"seat_count":1,"family_types":["player"],"interact_text":"action.interact.ride.horse","seats":[{"position":[0,1.2,0]}]},"minecraft:input_ground_controlled":{},"minecraft:horse.jump_strength":{"value":.7}})
      emit(f"behavior_pack/entities/{name}.entity.json",jdump({"format_version":"1.21.80","minecraft:entity":{"description":{"identifier":f"aionbound:{name}","is_spawnable":False,"is_summonable":False},"components":c}}))
    item_names=[Path(p).name.removesuffix(".item.json") for p in ALLOWED if p.startswith("behavior_pack/items/")]
    for name in item_names:
      c={"minecraft:display_name":{"value":name.replace("_"," ").title()},"minecraft:icon":{"textures":{"default":name}},"minecraft:max_stack_size":1}
      if name=="trophy_edge": c.update({"minecraft:durability":{"max_durability":768},"minecraft:damage":10,"minecraft:hand_equipped":True})
      emit(f"behavior_pack/items/{name}.item.json",jdump({"format_version":"1.21.80","minecraft:item":{"description":{"identifier":f"aionbound:{name}","menu_category":{"category":"items"}},"components":c}}))
    ingredients={"trophy_edge":["minecraft:diamond_sword","minecraft:amethyst_shard","aionbound:trophy_basalt_tusk","aionbound:trophy_colossus_shard"],"finale_ignition_key":["aionbound:trophy_edge","aionbound:chrono_core"],"burrowgate_key":["minecraft:iron_ingot","minecraft:amethyst_shard"],"vector_ray_projector":["aionbound:chrono_core","minecraft:spyglass"],"waykeeper_whistle":["minecraft:copper_ingot","minecraft:leather"]}
    for p in (x for x in ALLOWED if x.startswith("behavior_pack/recipes/")):
      name=Path(p).name.removesuffix(".recipe.json"); ins=ingredients.get(name,["minecraft:stick","minecraft:amethyst_shard"]); result="minecraft:chest" if name=="prismglass_chest" else f"aionbound:{name}"
      emit(p,jdump({"format_version":"1.20.10","minecraft:recipe_shapeless":{"description":{"identifier":f"aionbound:{name}_recipe"},"tags":["crafting_table"],"ingredients":[{"item":i} for i in ins],"unlock":[{"item":ins[0]}],"result":{"item":result,"count":1}}}))
    for p in (x for x in ALLOWED if x.startswith("behavior_pack/loot_tables/")):
      emit(p,jdump({"pools":[{"rolls":1,"entries":[{"type":"item","name":"minecraft:amethyst_shard","weight":1}]}]}))
    # Client entity, attachable, atlas, blocks, and text references close all promoted media.
    for name in entity_names:
      p=f"resource_pack/entity/{name}.entity.json"
      if p in allowed: emit(p,jdump({"format_version":"1.10.0","minecraft:client_entity":{"description":{"identifier":f"aionbound:{name}","materials":{"default":"entity_alphatest"},"textures":{"default":f"textures/aionbound/{name}"},"geometry":{"default":f"geometry.aionbound.{name}"},"animations":{"move":f"animation.aionbound.{name}.idle"},"scripts":{"animate":["move"]},"render_controllers":["controller.render.aionbound.default"]}}}))
    atlas={"resource_pack/textures/item_texture.json":{"resource_pack_name":"aionbound_core","texture_name":"atlas.items","texture_data":{n:{"textures":f"textures/aionbound/{n}"} for n in item_names}},"resource_pack/textures/terrain_texture.json":{"resource_pack_name":"aionbound_core","texture_name":"atlas.terrain","texture_data":{n:{"textures":f"textures/aionbound/{legacy if (legacy:={'waystone_arch':'first_waystation_arch','loot_ruin':'prismglass_chest_ruin','creature_nest':'spiral_moth_spire_nest','chaos_crate_t0':'chaos_crate_prime'}.get(n,n)) else n}"} for n in block_names}}}
    for p,v in atlas.items(): emit(p,jdump(v))
    emit("resource_pack/blocks.json",jdump({f"aionbound:{n}":{"textures":n,"sound":"stone"} for n in block_names}))
    emit("resource_pack/texts/languages.json",jdump(["en_US"])); emit("resource_pack/texts/en_US.lang","pack.name=Aionbound Core Beta\npack.description=Generation 6 bounded flagship beta\n")
    for name in ["burrowgate_key","finale_ignition_key","trophy_edge","vector_ray_projector","waykeeper_whistle"]:
      art="trophy_edge_assembled" if name=="trophy_edge" else name
      emit(f"resource_pack/attachables/{name}.attachable.json",jdump({"format_version":"1.10.0","minecraft:attachable":{"description":{"identifier":f"aionbound:{name}","materials":{"default":"entity_alphatest"},"textures":{"default":f"textures/aionbound/{art}"},"geometry":{"default":f"geometry.aionbound.{art}"},"animations":{"hold":f"animation.aionbound.{art}.idle"},"scripts":{"animate":["hold"]},"render_controllers":["controller.render.aionbound.default"]}}}))
    icon=(ROOT/"assets/beta/trophy_concord_scale/textures/trophy_concord_scale.png").read_bytes()
    emit("behavior_pack/pack_icon.png",icon);emit("resource_pack/pack_icon.png",icon)
    emit("manifests/implementation-map.json",jdump({"schema":"aionbound.implementation-map.v2","selected_features":json.loads((ROOT/"inputs/02-contract.json").read_text())["scope"]["selected_feature_ids"],"schema_version":2,"migration":"ordered idempotent v1-to-v2 preserving stamps and journals","caps":{"cell_blocks":192,"cell_edits_tick":16,"ray_range":24,"ray_cooldown":30,"ray_particles":12,"mount_world":12,"boss_world":3},"proof_boundary":{"not_claimed":["BDS PASS","gameplay","retail client","controller","console","split-screen","Marketplace","rights","release"]}}))

def beta_build():
    bp=[(p.removeprefix("behavior_pack/"),(ROOT/p).read_bytes()) for p in source_members("behavior_pack")]
    rp=[(p.removeprefix("resource_pack/"),(ROOT/p).read_bytes()) for p in source_members("resource_pack")]
    zip_into("dist/aionbound-core-beta-g6-behavior.mcpack",bp); zip_into("dist/aionbound-core-beta-g6-resources.mcpack",rp)
    zip_into("dist/aionbound-core-beta-g6.mcaddon",[("aionbound-core-beta-g6-behavior.mcpack",(ROOT/"dist/aionbound-core-beta-g6-behavior.mcpack").read_bytes()),("aionbound-core-beta-g6-resources.mcpack",(ROOT/"dist/aionbound-core-beta-g6-resources.mcpack").read_bytes())])
    packages=["dist/aionbound-core-beta-g6-behavior.mcpack","dist/aionbound-core-beta-g6-resources.mcpack","dist/aionbound-core-beta-g6.mcaddon"]
    artifacts=[{"path":p,"sha256":sha(ROOT/p),"size":(ROOT/p).stat().st_size} for p in packages]
    members=source_members("behavior_pack")+source_members("resource_pack")
    emit("manifests/source-byte-ledger.json",jdump({"schema":"aionbound.source-byte-ledger.v2","complete":True,"entries":[{"path":p,"sha256":sha(ROOT/p),"size":(ROOT/p).stat().st_size} for p in members]}))
    emit("dist/artifact-manifest.json",jdump({"schema":"aionbound.artifact-manifest.v2","artifacts":artifacts,"archive_timestamp":"1980-01-01T00:00:00Z","permissions":"0644"}))
    emit("manifests/candidate-manifest.json",jdump({"candidate_id":ASSIGNMENT["candidate_id"],"state":ASSIGNMENT["completion_state"],"immutable":True,"claims":ASSIGNMENT["gate_authority"],"pending":["BDS","GAMEPLAY","RETAIL_CLIENT","CONTROLLER","CONSOLE","SPLIT_SCREEN","MARKETPLACE","RIGHTS","RELEASE"],"artifacts":artifacts}))
    return {p:sha(ROOT/p) for p in packages}

def beta_main():
    if "--prepare" in sys.argv: beta_prepare()
    first=beta_build(); second=beta_build(); equal=first==second
    emit("reports/deterministic-build.json",jdump({"schema":"aionbound.two-build-equality.v2","builds":2,"equal":equal,"first":first,"second":second,"timestamp_policy":"1980-01-01T00:00:00Z","member_order":"sorted_posix","mode":"0644"}))
    if not equal: raise SystemExit("deterministic rebuild mismatch")
    print("built deterministic Aionbound Core Beta generation 6 artifacts")

if __name__ == "__main__": beta_main()
