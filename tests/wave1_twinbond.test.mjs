import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { TWINBOND, createTwinbondService, twinbondArena, twinbondPhase } from "../behavior_pack/scripts/twinbond.js";
import { migratePlayer, migrateWorld } from "../behavior_pack/scripts/state.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

class ItemStack {
  constructor(typeId, amount = 1) { this.typeId = typeId; this.amount = amount; this.maxAmount = 1; }
}
function inventory(size = 8) {
  const slots = Array(size).fill(undefined);
  return {
    size, slots, getItem: index => slots[index], setItem: (index, value) => { slots[index] = value; },
    addItem(item) { const index = slots.findIndex(value => !value); if (index < 0) return item; slots[index] = item; return undefined; },
  };
}
function entity(typeId, location, dimension) {
  const tags = new Set(), properties = new Map(), health = { currentValue: 160, setCurrentValue(value) { this.currentValue = value; } };
  return { typeId, location: { ...location }, dimension, removed: false,
    addTag: tag => tags.add(tag), removeTag: tag => tags.delete(tag), hasTag: tag => tags.has(tag), getTags: () => [...tags],
    setDynamicProperty: (key, value) => properties.set(key, value), getDynamicProperty: key => properties.get(key),
    getComponent: id => id === "minecraft:health" ? health : undefined, remove() { this.removed = true; },
  };
}
function player(id, dimension, location, capacity = 8) {
  const health = { currentValue: 20 }, items = inventory(capacity);
  return { id, typeId: "minecraft:player", dimension, location: { ...location }, items,
    getComponent(id) { if (id === "minecraft:health") return health; if (id === "minecraft:inventory") return { container: items }; return undefined; },
  };
}

function harness(count = 1, capacity = 8) {
  const spawned = [], placed = [], warnings = [], pulls = [], terminals = [], mastery = [];
  const blocks = new Map(), key = value => `${Math.floor(value.x)},${Math.floor(value.y)},${Math.floor(value.z)}`;
  const dimension = { id: "minecraft:overworld",
    spawnEntity(typeId, location) { const value = entity(typeId, location, this); spawned.push(value); return value; },
    getBlock(location) { return blocks.get(key(location)); },
  };
  const put = (typeId, location) => { const block = { typeId, location: { ...location }, dimension, setType(next) { this.typeId = next; } }; blocks.set(key(location), block); return block; };
  const marker = put("aionbound:twinbond_obelisk_site", { x: 64, y: 12, z: 30 });
  const arena = twinbondArena({ x: 0, y: 0, z: 0 }, dimension);
  const players = Array.from({ length: count }, (_, index) => player(`p${index + 1}`, dimension, { x: 64 + index, y: 12, z: 30 }, capacity));
  let worldRecord = migrateWorld({});
  const playerRecords = new Map(players.map(value => [value.id, migratePlayer({
    stamps: [...TWINBOND.requiredPilgrimageStamps],
    credits: Object.fromEntries(TWINBOND.requiredSealKeys.map(name => [name, true])),
  })]));
  const state = {
    worldState: () => structuredClone(worldRecord), saveWorld(value) { worldRecord = structuredClone(value); return true; },
    playerState: value => structuredClone(playerRecords.get(value.id) ?? migratePlayer({})), savePlayer(value, data) { playerRecords.set(value.id, structuredClone(data)); return true; },
    stamp(value, stamp) { const current = this.playerState(value); if (current.stamps.includes(stamp)) return false; current.stamps.push(stamp); return this.savePlayer(value, current); },
    warn(_player, text) { warnings.push(text); },
  };
  const system = { currentTick: 0 }, world = { getAllPlayers: () => players, getDimension: () => dimension };
  const placeSite = (_block, resolved) => {
    placed.push(resolved.origin);
    put("aionbound:twinbond_approach_marker", resolved.arrival); put("aionbound:twinbond_obelisk_site", resolved.gate);
    put("aionbound:twin_thrones", resolved.ember); put("aionbound:twinbond_obsidian_ring", resolved.center); put("aionbound:ceremony_anvil_site", resolved.completion);
    return true;
  };
  const service = createTwinbondService({ world, system, ItemStack, state, boundedEntities: () => spawned.filter(value => !value.removed), placeSite,
    codexHooks: { onPull(value) { pulls.push(value.id); }, onTerminalCredit(value) { terminals.push(value.id); }, onMastery(value) { mastery.push(value.id); } },
  });
  const tick = value => { system.currentTick = value; service.tick(); };
  const placeAndClaimBlank = () => { service.blockInteraction(players[0], marker); return service.arenaFromRecord(); };
  const beginAndPull = () => {
    const resolved = placeAndClaimBlank();
    const existing = [...service.sessions.keys()][0];
    const gate = dimension.getBlock(resolved.gate), id = existing ?? service.begin(players[0], gate); tick(system.currentTick + TWINBOND.pullResidencyTicks);
    return service.sessions.get(id);
  };
  return { service, system, state, world, dimension, marker, arena, players, spawned, placed, warnings, pulls, terminals, mastery, playerRecords, tick, put, placeAndClaimBlank, beginAndPull, getWorld: () => structuredClone(worldRecord) };
}

test("constants bind exact ratified finale proposal hashes and numeric envelope", async () => {
  const p2 = JSON.parse(await readFile(resolve(ROOT, "engineering/authority/support-proposals/finale/W1-002-TWINBOND.json")));
  const p3 = JSON.parse(await readFile(resolve(ROOT, "engineering/authority/support-proposals/finale/W1-003-TWINBOND.json"))).proposal;
  const p4 = JSON.parse(await readFile(resolve(ROOT, "engineering/authority/support-proposals/finale/W1-004-TWINBOND.json"))).proposal;
  assert.equal(p2.proposal.finale_container.site_count, "one_durable_site_per_world");
  assert.deepEqual(TWINBOND.aspectTypes, p3.aspect_entities);
  assert.equal(TWINBOND.participantCap, p3.multiplayer.participant_cap);
  assert.equal(TWINBOND.disconnectGraceTicks, p3.multiplayer.disconnect_grace_seconds * 20);
  assert.equal(TWINBOND.worldCompletionKey, p3.persistence.durable_world_key);
  assert.deepEqual([TWINBOND.thresholds.split, TWINBOND.thresholds.relic], [0.70, 0.40]);
  assert.deepEqual(TWINBOND.actions.split, { telegraph: 30, active: 18, recovery: 25, cooldown: 150 });
  assert.deepEqual(TWINBOND.actions.concord, { telegraph: 38, active: 24, recovery: 30, cooldown: 220 });
  assert.equal(TWINBOND.relicItem, p4.first_eligible_clear_package.twinbond_relic.id);
  assert.equal(TWINBOND.memoryItem, "aionbound:memory_of_four_lands");
  assert.deepEqual(twinbondPhase(1, 1), 0); assert.deepEqual(twinbondPhase(.70, .70), 1); assert.deepEqual(twinbondPhase(.40, .40), 2);
});

test("four seals and full pilgrimage gate one durable same-world site and inert Edge recovery", () => {
  const h = harness();
  const current = h.playerRecords.get("p1"); delete current.credits[TWINBOND.requiredSealKeys[3]]; h.playerRecords.set("p1", current);
  h.service.blockInteraction(h.players[0], h.marker); assert.equal(h.placed.length, 0); assert.match(h.warnings.at(-1), /Four chapter seals/);
  current.credits[TWINBOND.requiredSealKeys[3]] = true; h.playerRecords.set("p1", current);
  const arena = h.placeAndClaimBlank(); assert.ok(arena); assert.equal(h.placed.length, 1); assert.equal(h.players[0].items.slots[0].typeId, TWINBOND.blankItem);
  h.service.blockInteraction(h.players[0], h.marker); assert.equal(h.placed.length, 1);
  assert.deepEqual(h.getWorld().structures[TWINBOND.siteKey], { v: 1, state: "ready", dimension: "minecraft:overworld", origin: { x: 0, y: 0, z: 0 } });
});

test("pull waits five seconds, caps four, and early-phase late join does not change aspect balance", () => {
  const h = harness(5); h.placeAndClaimBlank(); const id = [...h.service.sessions.keys()][0];
  h.tick(99); assert.equal(h.spawned.length, 0); h.tick(100);
  const session = h.service.sessions.get(id); assert.equal(session.participants.size, 4); assert.equal(session.aspects.length, 2);
  for (const aspect of session.aspects) assert.equal(aspect.getComponent("minecraft:health").currentValue, 160);
  const late = h.players[4]; session.participants.delete("p4"); h.players[3].location = { x: 200, y: 12, z: 30 }; late.location = { x: 200, y: 12, z: 30 }; h.tick(101); late.location = { x: 65, y: 12, z: 31 };
  h.tick(102); h.tick(401); assert.equal(session.participants.has(late.id), false); h.tick(402); assert.equal(session.participants.has(late.id), true);
});

test("paired health floors prevent individual terminal and relic trial uses exact center cell", () => {
  const h = harness(), session = h.beginAndPull(), [ember, tide] = session.aspects;
  ember.getComponent("minecraft:health").currentValue = 90; h.service.handleHurt({ hurtEntity: ember }); assert.equal(ember.getComponent("minecraft:health").currentValue, 112); assert.equal(session.phase, 0);
  tide.getComponent("minecraft:health").currentValue = 112; h.service.handleHurt({ hurtEntity: tide }); assert.equal(session.phase, 1);
  ember.getComponent("minecraft:health").currentValue = 20; h.service.handleHurt({ hurtEntity: ember }); assert.equal(ember.getComponent("minecraft:health").currentValue, 64);
  tide.getComponent("minecraft:health").currentValue = 64; h.service.handleHurt({ hurtEntity: tide }); assert.equal(session.phase, 2);
  h.players[0].location = { ...session.arena.center }; for (let index = 0; index < 239; index++) h.tick(103 + index); assert.equal(session.phase, 2);
  h.tick(342); assert.equal(session.phase, 3); assert.equal(session.ignitionEnds, 442);
});

test("only the five-second ignition terminal writes completion and guaranteed once-per-player package", () => {
  const h = harness(), session = h.beginAndPull(), [ember, tide] = session.aspects;
  assert.equal(h.service.bossDeath({ deadEntity: ember }), true); assert.equal(h.getWorld().encounters.terminal[TWINBOND.worldCompletionKey], undefined);
  const final = h.beginAndPull(); for (const aspect of final.aspects) aspect.getComponent("minecraft:health").currentValue = 64;
  h.tick(h.system.currentTick + 1); h.players[0].location = { ...final.arena.center };
  for (let index = 0; index < TWINBOND.relicChannelTicks; index++) h.tick(h.system.currentTick + 1);
  assert.equal(final.phase, 3); h.tick(final.ignitionEnds - 1); assert.equal(h.getWorld().encounters.terminal[TWINBOND.worldCompletionKey], undefined);
  h.tick(final.ignitionEnds); const credits = h.playerRecords.get("p1").credits;
  assert.equal(h.getWorld().encounters.terminal[TWINBOND.worldCompletionKey].completed, true);
  for (const key of [TWINBOND.playerCompletionKey, TWINBOND.entitlementKey, TWINBOND.edgeIgnitedKey, TWINBOND.masteryStampKey, ...TWINBOND.memoryCreditKeys]) assert.equal(credits[key], true);
  assert.deepEqual(h.players[0].items.slots.filter(Boolean).map(item => item.typeId), [TWINBOND.blankItem, TWINBOND.relicItem, TWINBOND.edgeItem, TWINBOND.memoryItem]);
  assert.equal(h.playerRecords.get("p1").endpoint, true); assert.deepEqual(h.terminals, ["p1"]); assert.deepEqual(h.mastery, ["p1"]);
});

test("full inventory remains in recovery and cannot fall through into a new encounter", () => {
  const h = harness(1, 4), session = h.beginAndPull();
  // Keep the blank and fill every remaining slot before terminal fulfillment.
  for (let index = 1; index < h.players[0].items.size; index++) h.players[0].items.slots[index] = new ItemStack(`minecraft:stone_${index}`);
  for (const aspect of session.aspects) aspect.getComponent("minecraft:health").currentValue = 64;
  h.tick(h.system.currentTick + 1); h.players[0].location = { ...session.arena.center };
  for (let index = 0; index < TWINBOND.relicChannelTicks; index++) h.tick(h.system.currentTick + 1); h.tick(session.ignitionEnds);
  let credits = h.playerRecords.get("p1").credits; assert.equal(credits[TWINBOND.entitlementKey], true); assert.notEqual(credits[TWINBOND.relicClaimedKey], true);
  const gate = h.dimension.getBlock(session.arena.gate); assert.equal(h.service.blockInteraction(h.players[0], gate), true); assert.equal(h.service.sessions.size, 0); assert.match(h.warnings.at(-1), /recovery/);
  h.players[0].items.slots[1] = undefined; h.service.blockInteraction(h.players[0], gate); credits = h.playerRecords.get("p1").credits;
  assert.equal(credits[TWINBOND.relicClaimedKey], true); assert.equal(h.service.sessions.size, 0);
});

test("disconnect grace queues entitlement in existing encounter map and migration is idempotent", () => {
  const h = harness(2), session = h.beginAndPull(), offline = h.players.pop();
  for (const aspect of session.aspects) aspect.getComponent("minecraft:health").currentValue = 64;
  h.tick(h.system.currentTick + 1); h.players[0].location = { ...session.arena.center };
  for (let index = 0; index < TWINBOND.relicChannelTicks; index++) h.tick(h.system.currentTick + 1); h.tick(session.ignitionEnds);
  assert.equal(h.getWorld().encounters.pendingTwinbond[offline.id].entitlement, true);
  h.players.push(offline); h.service.flushPending(); assert.equal(h.getWorld().encounters.pendingTwinbond?.[offline.id], undefined);
  assert.equal(h.playerRecords.get(offline.id).credits[TWINBOND.entitlementKey], true);
  const source = { encounters: { active: { "twinbond:x": { encounterId: TWINBOND.id }, other: { type: "other" } }, terminal: {}, pendingTwinbond: { p: { entitlement: true } } } };
  const once = migrateWorld(source); assert.deepEqual(migrateWorld(once), once); assert.deepEqual(Object.keys(once.encounters.active), ["other"]); assert.equal(once.encounters.pendingTwinbond.p.entitlement, true);
});

test("shared runtime composition adds no subscription or interval class and legacy identities stay absent", async () => {
  const runtime = await readFile(resolve(ROOT, "behavior_pack/scripts/runtime.js"), "utf8");
  const source = await readFile(resolve(ROOT, "behavior_pack/scripts/twinbond.js"), "utf8");
  assert.equal((runtime.match(/\.subscribe\(/g) ?? []).length, 8);
  assert.equal((runtime.match(/runInterval\(/g) ?? []).length, 1);
  for (const required of ["twinbond.reconcile()", "twinbond.tick()", "twinbond.handleHurt(event)", "twinbond.bossDeath(event)"]) assert.equal(runtime.includes(required), true);
  for (const forbidden of ["aionbound:finale_ignition_key", "aionbound:trophy_concord_scale", "concord_sigil", "concord_dueling_ring", "ash_crownblade", "empress_tide_lance"]) assert.equal(source.includes(forbidden), false);
});
