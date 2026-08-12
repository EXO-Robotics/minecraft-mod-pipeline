import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, resolve } from "node:path";
import { tmpdir } from "node:os";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SOURCE_DIR = resolve(ROOT, "behavior_pack/scripts");
const MODULE_NAMES = ["wave1_codex_extension_data", "wave1_codex_ashen_data", "wave1_codex_crystal_data", "wave1_codex_skyreach_data", "wave1_codex_data", "wave1_codex_ui_data", "wave1_equipment_roles", "crystal_equipment_roles", "crystal_equipment", "crystal_reward_data", "crystal_rewards", "pearl_depths", "whisperwood_regrowth", "whisperwood_rewards", "ashen_structure_reward_data", "ashen_structure_rewards", "catalog", "budgets", "state", "router", "codex", "combat", "devices", "encounters", "thorn_court", "chaos", "structures", "runtime", "main"];
const MODULE_DIR = await mkdtemp(resolve(tmpdir(), "aionbound-g7-modules-"));
for (const name of MODULE_NAMES) {
  const source = (await readFile(resolve(SOURCE_DIR, `${name}.js`), "utf8"))
    .replaceAll(/from "\.\/([a-z0-9_]+)\.js"/g, 'from "./$1.mjs"')
    .replace('from "@minecraft/server"', 'from "./minecraft-server.mjs"')
    .replace('from "@minecraft/server-ui"', 'from "./minecraft-server-ui.mjs"');
  await writeFile(resolve(MODULE_DIR, `${name}.mjs`), source);
}
await writeFile(resolve(MODULE_DIR, "minecraft-server.mjs"), `
const signal=()=>({callbacks:[],subscribe(callback){this.callbacks.push(callback);return callback;}});
export const world={
  afterEvents:{itemUse:signal(),itemCompleteUse:signal(),playerBreakBlock:signal(),playerInteractWithEntity:signal(),entityHitEntity:signal(),entityHurt:signal(),entityDie:signal()},
  beforeEvents:{playerInteractWithBlock:signal()},
  getDynamicProperty(){return undefined;},setDynamicProperty(){},getAllPlayers(){return[];},
  getDimension(){return{getEntities(){return[];}};}
};
export const system={beforeEvents:{startup:signal()},currentTick:0,queue:[],intervals:[],run(callback){this.queue.push(callback);},runInterval(callback,ticks){this.intervals.push([callback,ticks]);}};
export class ItemStack{constructor(typeId,amount){this.typeId=typeId;this.amount=amount;}}
export const EquipmentSlot={Offhand:"Offhand",Head:"Head",Chest:"Chest",Legs:"Legs",Feet:"Feet"};
export const EntityComponentTypes={Equippable:"minecraft:equippable"};
`);
await writeFile(resolve(MODULE_DIR, "minecraft-server-ui.mjs"), `
export class ActionFormData{title(){return this;}body(){return this;}button(){return this;}show(){return Promise.resolve({canceled:true});}}
`);
const load = name => import(pathToFileURL(resolve(MODULE_DIR, `${name}.mjs`)).href);
const { ACCESSORY_ROLES, ARMOR_SETS, BLOCK_ROUTES, CHAOS_OUTCOMES, CONSUMABLE_EFFECTS, MELEE_WEAPON_ROLES, NATURAL_ENTITY_IDS, RANGED_WEAPON_ROLES, STRUCTURE_REWARDS, STRUCTURE_SITES, TECH_LOOPS } = await load("catalog");
const { WHISPERWOOD_MELEE_ROLES, WHISPERWOOD_UTILITY_ROLES } = await load("wave1_equipment_roles");
const { COMBINED_BUDGETS, RuntimeArbiter } = await load("budgets");
const { migratePlayer, migrateWorld } = await load("state");
const { createInteractionRouter } = await load("router");
const { createStructureService } = await load("structures");
const { createChaosService, selectOutcomeIndex } = await load("chaos");
const { createCombatService } = await load("combat");

test("G6 collision blocks compose discovery and boss action", () => {
  assert.deepEqual(BLOCK_ROUTES["aionbound:ember_vent_stone"], { discoveries: ["pilgrimage:vent"], actions: ["boss:basalt"] });
  assert.deepEqual(BLOCK_ROUTES["aionbound:rift_crust"], { discoveries: ["pilgrimage:riftscar"], actions: ["boss:rift"] });
  assert.deepEqual(BLOCK_ROUTES["aionbound:twinbond_obelisk_site"], { discoveries: ["pilgrimage:twinbond"], actions: ["boss:twinbond"] });
  const calls = [];
  const router = createInteractionRouter({ discover: (_p, key) => calls.push(`discover:${key}`), blockActions: { "boss:basalt": () => calls.push("action:basalt") }, itemActions: {} });
  assert.equal(router.dispatchBlock({ player: {}, block: { typeId: "aionbound:ember_vent_stone" } }), true);
  assert.deepEqual(calls, ["discover:pilgrimage:vent", "action:basalt"]);
});

test("schema v4 migrations preserve prior authority and are idempotent", () => {
  const v2w = { v: 2, journals: { a: { terminal: true } }, structures: { s: 1 }, cells: { p: { state: "ready" } }, encounters: { active: { e: 1 }, terminal: { t: 1 } }, quarantine: ["q"] };
  const once = migrateWorld(v2w), twice = migrateWorld(once);
  assert.equal(once.v, 4); assert.deepEqual(twice, once); assert.deepEqual(once.cells, v2w.cells); assert.deepEqual(once.encounters.active, v2w.encounters.active);
  const v2p = { v: 2, stamps: ["glasswing:first_defeat", "pilgrimage:vent"], credits: { old: 1 }, cooldowns: { ray: 12 }, opens: [1], cell: { owner: "p" }, endpoint: true };
  const player = migratePlayer(v2p); assert.deepEqual(migratePlayer(player), player); assert.deepEqual(player.stamps, v2p.stamps); assert.equal(player.endpoint, true);
});

test("one arbiter enforces per-tick, active, and backlog limits", () => {
  const arbiter = new RuntimeArbiter({ ...COMBINED_BUDGETS, callbacksTick: 2, chaosActiveWorld: 1, schedulerBacklog: 1 });
  arbiter.beginTick(1); assert.equal(arbiter.spend("callbacksTick"), true); assert.equal(arbiter.spend("callbacksTick"), true); assert.equal(arbiter.spend("callbacksTick"), false);
  arbiter.beginTick(2); assert.equal(arbiter.spend("callbacksTick"), true);
  assert.equal(arbiter.admit("chaos", "chaosActiveWorld"), true); assert.equal(arbiter.admit("chaos", "chaosActiveWorld"), false); arbiter.release("chaos"); assert.equal(arbiter.admit("chaos", "chaosActiveWorld"), true);
  const queued = []; const system = { run: callback => queued.push(callback) };
  assert.equal(arbiter.defer(system, () => {}), true); assert.equal(arbiter.defer(system, () => {}), false); queued.shift()(); assert.equal(arbiter.backlog, 0);
});

test("18 chaos outcomes cover six bounded classes exactly three times", () => {
  assert.equal(CHAOS_OUTCOMES.length, 18);
  const counts = Object.groupBy(CHAOS_OUTCOMES, outcome => outcome.class);
  assert.deepEqual(Object.fromEntries(Object.entries(counts).map(([key, values]) => [key, values.length])), {
    boon: 3, bounded_skirmish: 3, material_burst: 3, harmless_transformation: 3, temporary_hazard: 3, discovery_clue: 3,
  });
  for (const outcome of CHAOS_OUTCOMES) {
    assert.ok((outcome.entities?.length ?? 0) <= COMBINED_BUDGETS.chaosEntitiesEvent);
    assert.ok((outcome.temporary?.[1] ?? 0) <= COMBINED_BUDGETS.chaosCleanupTicks);
  }
  assert.equal(selectOutcomeIndex(17, -9, 12), selectOutcomeIndex(17, -9, 12));
});

test("chaos journal admits one operation and records at-most-once completion", () => {
  const queued = [], spawned = [], effects = [], messages = [];
  const playerData = { v: 3, stamps: [], credits: {}, cooldowns: {}, opens: [], cell: null, endpoint: false, codex: { topic: 0 }, goals: {} };
  let worldData = { v: 3, journals: {}, journalOrder: [], structures: {}, quarantine: [], cells: {}, devices: {}, sequence: 0, encounters: { active: {}, terminal: {} } };
  const player = { id: "p", dimension: { id: "minecraft:overworld" }, addEffect: (...args) => effects.push(args) };
  const dimension = { spawnItem: item => spawned.push(item), spawnEntity: id => ({ addTag: tag => spawned.push([id, tag]) }), getBlock: () => ({ typeId: "minecraft:stone", setType() {} }) };
  const state = {
    playerState: () => structuredClone(playerData), savePlayer: (_p, value) => (Object.assign(playerData, value), true),
    worldState: () => structuredClone(worldData), saveWorld: value => (worldData = structuredClone(value), true),
    nextOperationId: prefix => { worldData.sequence++; return `${prefix}:p:${worldData.sequence}`; },
    stamp: (_p, key) => (playerData.stamps.push(key), true), warn: (_p, text) => messages.push(text),
    pruneJournals() {},
  };
  class ItemStack { constructor(typeId, amount) { this.typeId = typeId; this.amount = amount; } }
  const system = { currentTick: 100, run: callback => queued.push(callback) }, arbiter = new RuntimeArbiter(); arbiter.beginTick(100);
  const service = createChaosService({ world: { getDimension: () => dimension, getAllPlayers: () => [player] }, system, ItemStack, state, arbiter });
  service.use({ player, block: { location: { x: 2, y: 64, z: 7 } } }); assert.equal(queued.length, 1);
  const id = Object.keys(worldData.journals)[0]; queued.shift()();
  if (worldData.journals[id].state === "cleanup") { system.currentTick = worldData.journals[id].cleanupAt; service.tick(); }
  const effectsAfter = effects.length + spawned.length;
  assert.equal(worldData.journals[id].state, "terminal");
  assert.equal(worldData.journals[id].deliverySemantics, "at_most_once");
  assert.ok(["completed_in_process", "temporary_cleanup_completed"].includes(worldData.journals[id].completion));
  assert.equal(service.execute(id, player), false); assert.equal(effects.length + spawned.length, effectsAfter);
});

test("15 real structure sites resolve signatures and claim once per player", () => {
  assert.equal(STRUCTURE_SITES.length, 15); assert.equal(new Set(STRUCTURE_SITES.map(site => site.id)).size, 15);
  assert.deepEqual(new Set(STRUCTURE_SITES.map(site => site.pool)), new Set(Object.keys(STRUCTURE_REWARDS)));
  const survey = STRUCTURE_SITES.filter(site => site.center === "aionbound:survey_relay");
  assert.deepEqual(new Set(survey.map(site => site.signature)), new Set(["aionbound:brinewood_beam", "aionbound:charged_aionite_block"]));
  const drops = [], stamps = [], playerRecord = { v: 3, stamps: [], credits: {}, cooldowns: {}, opens: [], cell: null, endpoint: false, codex: { topic: 0 }, goals: {} };
  const dimension = { id: "minecraft:overworld", getBlock: location => ({ typeId: location.x === 1 ? "aionbound:charged_aionite_block" : "minecraft:air" }), spawnItem: item => drops.push(item) };
  const player = { id: "p", dimension, location: { x: 0, y: 64, z: 0 }, sendMessage() {} };
  const state = { stamp: (_p, key) => (stamps.push(key), true), playerState: () => structuredClone(playerRecord), savePlayer: (_p, value) => (Object.assign(playerRecord, value), true), warn() {}, worldState: () => ({ cells: {} }), saveWorld: () => true };
  class ItemStack { constructor(typeId, amount) { this.typeId = typeId; this.amount = amount; } }
  const service = createStructureService({ world: {}, system: { currentTick: 1 }, ItemStack, state, arbiter: new RuntimeArbiter(), consumeOne: () => true });
  const context = { player, block: { typeId: "aionbound:survey_relay", location: { x: 0, y: 64, z: 0 } } };
  assert.equal(service.resolveSite(context.block, dimension).id, "broken_relay"); service.claimSite(context); service.claimSite(context);
  assert.equal(drops.length, 1); assert.ok(stamps.includes("landmark:broken_relay"));
});

test("three representative technology loops are bound", () => {
  assert.ok(Object.keys(TECH_LOOPS.salvage).length >= 2); assert.ok(Object.keys(TECH_LOOPS.press).length >= 3);
  assert.deepEqual(BLOCK_ROUTES["aionbound:survey_relay"].actions, ["site_reward", "device:survey"]);
});

test("chaos restart resumes accepted owner and releases executing capacity", () => {
  const player = { id: "p", addEffect() {} }, dimension = { spawnItem() {}, spawnEntity() { return { addTag() {} }; }, getBlock() { return { typeId: "minecraft:stone", setType() {} }; } };
  let data = { v: 3, journals: {
    accepted: { v: 3, kind: "chaos", state: "accepted", owner: "p", dimension: "minecraft:overworld", location: { x: 0, y: 64, z: 0 }, outcome: 0 },
    executing: { v: 3, kind: "chaos", state: "executing", owner: "p", dimension: "minecraft:overworld", location: { x: 1, y: 64, z: 0 }, outcome: 1 },
  }, journalOrder: ["accepted", "executing"], sequence: 2 };
  const state = { worldState: () => structuredClone(data), saveWorld: value => (data = structuredClone(value), true), pruneJournals() {}, stamp() { return true; } };
  class ItemStack { constructor(typeId, amount) { this.typeId = typeId; this.amount = amount; } }
  const system = { currentTick: 200, run() {} }, arbiter = new RuntimeArbiter();
  const service = createChaosService({ world: { getDimension: () => dimension, getAllPlayers: () => [player] }, system, ItemStack, state, arbiter });
  service.reconcile(); assert.equal(data.journals.executing.state, "terminal");
  assert.equal(data.journals.executing.deliverySemantics, "at_most_once");
  assert.equal(data.journals.executing.completion, "replay_suppressed_after_uncertain_execution");
  assert.equal(data.journals.executing.replaySuppressed, true); assert.equal(arbiter.active.chaos, 1);
  service.tick(); assert.equal(data.journals.accepted.state, "terminal"); assert.equal(arbiter.active.chaos, 0);
});

test("all combat, accessory, armor, and consumable roles are non-inert and bounded", () => {
  assert.equal(Object.keys(MELEE_WEAPON_ROLES).length, 5); assert.equal(Object.keys(RANGED_WEAPON_ROLES).length, 3);
  assert.equal(Object.keys(ACCESSORY_ROLES).length, 11); assert.equal(Object.keys(CONSUMABLE_EFFECTS).length, 4);
  assert.deepEqual(Object.values(ARMOR_SETS).map(ids => ids.length), [4, 4]);
  for (const role of Object.values(MELEE_WEAPON_ROLES)) { assert.ok(role.cooldown > 0); assert.ok((role.targets ?? 0) <= 4); }
  for (const role of Object.values(RANGED_WEAPON_ROLES)) { assert.ok(role.cooldown > 0); assert.ok(role.range <= COMBINED_BUDGETS.rayRange); assert.ok(role.particles <= COMBINED_BUDGETS.particlesAction); }
});

test("ranged cooldown and maul splash cap are enforced semantically", () => {
  const record = { v: 3, stamps: [], credits: {}, cooldowns: {}, opens: [], codex: { topic: 0 }, goals: {} }, damages = [], splash = [];
  let selected = "aionbound:gale_repeater";
  const target = { id: "target", applyDamage: amount => damages.push(amount), applyImpulse() {}, dimension: null, location: { x: 0, y: 0, z: 0 } };
  const extras = Array.from({ length: 8 }, (_, index) => ({ id: `e${index}`, applyDamage: () => splash.push(index) })); target.dimension = { getEntities: () => [target, ...extras] };
  const player = {
    id: "p", typeId: "minecraft:player", selectedSlotIndex: 0, location: { x: 0, y: 0, z: 0 }, dimension: { spawnParticle() {}, getEntities: () => [] },
    getComponent: id => id === "minecraft:inventory" ? { container: { getItem: () => ({ typeId: selected }) } } : null,
    getEntitiesFromViewDirection: () => [{ entity: target }], getViewDirection: () => ({ x: 1, y: 0, z: 0 }), getHeadLocation: () => ({ x: 0, y: 1, z: 0 }),
  };
  const state = { playerState: () => structuredClone(record), savePlayer: (_p, value) => (Object.assign(record, value), true), warn() {}, stamp() { return true; } };
  const service = createCombatService({ world: { getAllPlayers: () => [] }, system: { currentTick: 10 }, ItemStack: class {}, state, arbiter: new RuntimeArbiter(), boundedEntities: () => [], consumeOne: () => true });
  assert.equal(service.useRanged(player, selected), true); assert.equal(service.useRanged(player, selected), false); assert.deepEqual(damages, [3]);
  selected = "aionbound:basalt_maul"; assert.equal(service.routeMeleeHurt({ hurtEntity: target, damageSource: { damagingEntity: player } }), true); assert.equal(splash.length, 4);
});

test("Whisperwood equipment-A roles are exact, bounded, and composed through combat", () => {
  assert.deepEqual(Object.keys(WHISPERWOOD_MELEE_ROLES), ["aionbound:mossfang_spear", "aionbound:widow_fang_dagger", "aionbound:thorn_whip"]);
  assert.deepEqual(Object.keys(WHISPERWOOD_UTILITY_ROLES), ["aionbound:moon_sap_staff", "aionbound:lantern_hook"]);
  for (const spec of [...Object.values(WHISPERWOOD_MELEE_ROLES), ...Object.values(WHISPERWOOD_UTILITY_ROLES)]) assert.ok(spec.cooldown > 0);

  const record = { v: 4, stamps: [], credits: {}, cooldowns: {}, opens: [], codex: { topic: 0 }, goals: {} };
  let selected = "aionbound:mossfang_spear", tick = 10;
  const impulses = [], effects = [];
  const target = { location: { x: 4, y: 0, z: 0 }, applyImpulse: value => impulses.push(value), addEffect: (...args) => effects.push(args) };
  const player = {
    id: "p", typeId: "minecraft:player", selectedSlotIndex: 0, location: { x: 0, y: 0, z: 0 },
    getComponent: id => id === "minecraft:inventory" ? { container: { getItem: () => ({ typeId: selected }) } } : null,
    getViewDirection: () => ({ x: 1, y: 0, z: 0 }), addEffect: (...args) => effects.push(args),
  };
  const state = { playerState: () => structuredClone(record), savePlayer: (_p, value) => (Object.assign(record, value), true) };
  const system = { get currentTick() { return tick; } };
  const service = createCombatService({ world: { getAllPlayers: () => [] }, system, ItemStack: class {}, state, arbiter: new RuntimeArbiter(), boundedEntities: () => [], consumeOne: () => true });

  assert.equal(service.routeMeleeHurt({ hurtEntity: target, damageSource: { damagingEntity: player } }), true);
  assert.deepEqual(impulses.pop(), { x: 0.45, y: 0.08, z: 0 });
  selected = "aionbound:widow_fang_dagger"; tick += 20;
  assert.equal(service.routeMeleeHurt({ hurtEntity: target, damageSource: { damagingEntity: player } }), true);
  assert.equal(effects.at(-1)[0], "poison");
  selected = "aionbound:thorn_whip"; tick += 20;
  assert.equal(service.routeMeleeHurt({ hurtEntity: target, damageSource: { damagingEntity: player } }), true);
  assert.deepEqual(impulses.pop(), { x: -0.5, y: 0.08, z: 0 });

  tick += 20;
  assert.equal(service.useWhisperwoodUtility(player, "aionbound:moon_sap_staff"), true);
  assert.deepEqual(effects.slice(-2).map(value => value[0]), ["night_vision", "regeneration"]);
  assert.equal(service.useWhisperwoodUtility(player, "aionbound:moon_sap_staff"), false);
  tick += 220;
  assert.equal(service.useWhisperwoodUtility(player, "aionbound:lantern_hook"), true);
  assert.equal(effects.at(-1)[0], "night_vision");
});

test("natural custom entity reconciliation enforces 40 without touching excluded roles", () => {
  const entities = Array.from({ length: 50 }, (_, index) => ({ id: String(index).padStart(2, "0"), typeId: NATURAL_ENTITY_IDS[0], removed: false, remove() { this.removed = true; } }));
  const boss = { id: "boss", typeId: "aionbound:basalt_behemoth", removed: false, remove() { this.removed = true; } };
  const service = createCombatService({ world: { getAllPlayers: () => [] }, system: { currentTick: 100 }, ItemStack: class {}, state: {}, arbiter: new RuntimeArbiter(), boundedEntities: typeId => typeId === NATURAL_ENTITY_IDS[0] ? entities : [], consumeOne: () => true });
  const result = service.reconcileNaturalEntities(); assert.deepEqual(result, { observed: 50, removed: 10 });
  assert.equal(entities.filter(entity => entity.removed).length, 10); assert.equal(boss.removed, false); assert.equal(NATURAL_ENTITY_IDS.includes(boss.typeId), false);
});

test("Pilgrim Clasp proactively refreshes bounded fall mitigation", () => {
  const effects = [], equipment = { getEquipment: slot => slot === "Offhand" ? { typeId: "aionbound:pilgrim_clasp" } : undefined };
  const player = { getComponent: id => id === "minecraft:equippable" ? equipment : null, addEffect: (name, ticks) => effects.push([name, ticks]), dimension: { getEntities: () => [] } };
  const service = createCombatService({ world: { getAllPlayers: () => [player] }, system: { currentTick: 20 }, ItemStack: class {}, state: {}, arbiter: new RuntimeArbiter(), boundedEntities: () => [], consumeOne: () => true });
  service.tickPlayers(); assert.deepEqual(effects, [["slow_falling", 60]]);
});

test("shipping scripts use approved stable APIs only and one central arbiter", async () => {
  const scripts = ["main.js", "runtime.js", "catalog.js", "wave1_codex_extension_data.js", "wave1_codex_ashen_data.js", "wave1_codex_data.js", "wave1_codex_ui_data.js", "wave1_equipment_roles.js", "whisperwood_regrowth.js", "whisperwood_rewards.js", "ashen_structure_reward_data.js", "ashen_structure_rewards.js", "budgets.js", "state.js", "router.js", "codex.js", "combat.js", "devices.js", "encounters.js", "thorn_court.js", "chaos.js", "structures.js"];
  const source = (await Promise.all(scripts.map(name => readFile(resolve(ROOT, "behavior_pack/scripts", name), "utf8")))).join("\n");
  for (const forbidden of ["@minecraft/server-net", "@minecraft/server-admin", "@minecraft/server-gametest", "process.", "require(", "fetch(", "node:"]) assert.equal(source.includes(forbidden), false, forbidden);
  const runtime = await readFile(resolve(ROOT, "behavior_pack/scripts/runtime.js"), "utf8"), main = await readFile(resolve(ROOT, "behavior_pack/scripts/main.js"), "utf8");
  const manifest = JSON.parse(await readFile(resolve(ROOT, "behavior_pack/manifest.json"), "utf8"));
  assert.equal((runtime.match(/from "@minecraft\/server-ui"/g) ?? []).length, 1);
  assert.equal(manifest.dependencies.some(dependency => dependency.module_name === "@minecraft/server-ui" && dependency.version === "2.0.0"), true);
  assert.equal((runtime.match(/new RuntimeArbiter\(/g) ?? []).length, 1);
  assert.equal((main.match(/runtime-ready-g8/g) ?? []).length, 1); assert.ok(main.indexOf("runtime-ready-g8") < main.indexOf("startRuntime()"));
  assert.equal(runtime.includes("useProgressBlock"), false); assert.equal(runtime.includes("platform.world.beforeEvents.playerInteractWithBlock.subscribe"), true);
});

test("transformed source harness starts one stable subscription per routed event", async () => {
  const minecraft = await import(pathToFileURL(resolve(MODULE_DIR, "minecraft-server.mjs")).href);
  await load("main");
  assert.equal(minecraft.world.afterEvents.itemUse.callbacks.length, 1);
  assert.equal(minecraft.world.afterEvents.itemCompleteUse.callbacks.length, 1);
  assert.equal(minecraft.world.afterEvents.playerBreakBlock.callbacks.length, 1);
  assert.equal(minecraft.world.beforeEvents.playerInteractWithBlock.callbacks.length, 1);
  assert.equal(minecraft.world.afterEvents.playerInteractWithEntity.callbacks.length, 1);
  assert.equal(minecraft.world.afterEvents.entityHitEntity.callbacks.length, 1);
  assert.equal(minecraft.world.afterEvents.entityHurt.callbacks.length, 1);
  assert.equal(minecraft.world.afterEvents.entityDie.callbacks.length, 1);
  assert.equal(minecraft.system.beforeEvents.startup.callbacks.length, 1);
  assert.equal(minecraft.system.intervals.length, 1);
  assert.equal(minecraft.system.queue.length, 1);
});
