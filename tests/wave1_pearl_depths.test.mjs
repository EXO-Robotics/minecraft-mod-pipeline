import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { PEARL_DEPTHS, createPearlDepthsService, pearlDepthsHealth, pearlDepthsPhase, resolvePearlDepthsArena } from "../behavior_pack/scripts/pearl_depths.js";
import { migratePlayer, migrateWorld } from "../behavior_pack/scripts/state.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function entity(typeId, location, dimension) {
  const tags = new Set(), properties = new Map();
  const health = { currentValue: 80, maxValue: 80, setCurrentValue(value) { this.currentValue = value; } };
  return { typeId, location: { ...location }, dimension, removed: false,
    addTag: tag => tags.add(tag), removeTag: tag => tags.delete(tag), hasTag: tag => tags.has(tag), getTags: () => [...tags],
    setDynamicProperty: (key, value) => properties.set(key, value), getDynamicProperty: key => properties.get(key),
    getComponent: id => id === "minecraft:health" ? health : undefined, addEffect() {}, remove() { this.removed = true; },
  };
}
function player(id, dimension, location = { x: 0, y: 64, z: 0 }) {
  const health = { currentValue: 20 };
  return { id, typeId: "minecraft:player", dimension, location: { ...location }, health,
    getComponent: id => id === "minecraft:health" ? health : undefined,
  };
}

function harness(count = 1, canDeliver = true) {
  const spawned = [], warnings = [], materials = [], caches = [], masks = [], pulls = [], terminals = [], restored = [], phases = [];
  const dimension = { id: "minecraft:overworld", spawnEntity(typeId, location) { const value = entity(typeId, location, this); spawned.push(value); return value; } };
  const arena = { id: "pearl_depths:test", formId: "deep_pool_entrance", dimension, dimensionId: dimension.id, anchor: { x: 0, y: 64, z: 0 }, rotationIndex: 0,
    contains(value) { return value.x >= -9 && value.x <= 9 && value.y >= 63 && value.y <= 74 && value.z >= -13 && value.z <= 5; } };
  const players = Array.from({ length: count }, (_, index) => player(`p${index + 1}`, dimension, { x: index, y: 64, z: 0 }));
  let worldRecord = migrateWorld({}); const playerRecords = new Map(players.map(value => [value.id, migratePlayer({})]));
  const state = {
    worldState: () => structuredClone(worldRecord), saveWorld(value) { worldRecord = structuredClone(value); return true; },
    playerState: value => structuredClone(playerRecords.get(value.id) ?? migratePlayer({})), savePlayer(value, data) { playerRecords.set(value.id, structuredClone(data)); return true; },
    warn(_player, text) { warnings.push(text); },
  };
  const system = { currentTick: 0 }, world = { getAllPlayers: () => players };
  const service = createPearlDepthsService({ world, system, state, boundedEntities: () => spawned.filter(value => !value.removed), resolveArena: () => arena,
    rewardHooks: {
      canDeliverMask: () => canDeliver, deliverMask(value, typeId) { masks.push([value.id, typeId]); return true; },
      grantMaterialPackage(value, context) { materials.push([value.id, context]); return true; }, openArenaCache(context) { caches.push(context); return true; },
    },
    codexHooks: { onPull(value) { pulls.push(value.id); }, onTerminalCredit(value) { terminals.push([value.id, structuredClone(playerRecords.get(value.id).credits)]); } },
    arenaHooks: { onPhase(_arena, id) { phases.push(id); }, restore() { restored.push(system.currentTick); } },
  });
  const tick = value => { system.currentTick = value; service.tick(); };
  const pull = () => { const id = service.begin(players[0], arena); tick(system.currentTick + PEARL_DEPTHS.pullResidencyTicks); return service.sessions.get(id); };
  const kill = session => service.bossDeath({ deadEntity: session.boss, damageSource: { damagingEntity: players[0] } });
  return { service, system, state, dimension, arena, players, spawned, warnings, materials, caches, masks, pulls, terminals, restored, phases, playerRecords, tick, pull, kill, getWorld: () => structuredClone(worldRecord) };
}

test("ratified constants preserve exact phase, timing, scaling, and persistence envelope", async () => {
  const proposal = JSON.parse(await readFile(resolve(ROOT, "engineering/authority/support-proposals/crystal-marsh/W1-003-PEARL-DEPTHS.json"))).proposal;
  assert.equal(PEARL_DEPTHS.soloHealth, proposal.health.solo);
  assert.equal(PEARL_DEPTHS.participantScale, proposal.health.per_additional_locked_participant_multiplier);
  assert.equal(PEARL_DEPTHS.worldCompletionKey, proposal.persistence.world_completion_key);
  assert.equal(PEARL_DEPTHS.maskClaimedKey, proposal.persistence.physical_mask_claimed_key);
  assert.deepEqual(PEARL_DEPTHS.phases.map(row => row.exit), proposal.new_numbers_proposed_not_ratified.phase_exit_health_fractions);
  for (const [id, spec] of Object.entries(PEARL_DEPTHS.attacks)) {
    const source = proposal.timing_seconds[id];
    for (const field of ["telegraph", "active", "recovery"]) assert.equal(spec[`${field}Seconds`], (source[field][0] + source[field][1]) / 2);
    if (Array.isArray(source.cooldown)) assert.equal(spec.cooldownSeconds, (source.cooldown[0] + source.cooldown[1]) / 2);
  }
});

test("exact Sunken Shrine and Deep Pool signatures resolve rotated authored volumes", () => {
  const blocks = new Map(), key = value => `${value.x},${value.y},${value.z}`;
  const dimension = { id: "minecraft:overworld", getBlock(location) { return blocks.get(key(location)); } };
  const put = (typeId, location) => { const block = { typeId, location: { ...location }, dimension }; blocks.set(key(location), block); return block; };
  const shrine = put("minecraft:lodestone", { x: 100, y: 70, z: 100 });
  put("aionbound:glass_root_block", { x: 100, y: 69, z: 100 }); put("minecraft:lectern", { x: 105, y: 67, z: 100 }); put("aionbound:prism_brick", { x: 105, y: 74, z: 95 });
  const shrineArena = resolvePearlDepthsArena(shrine); assert.equal(shrineArena.formId, "sunken_shrine");
  assert.equal(shrineArena.contains({ x: 92, y: 65, z: 92, dimension }), true); assert.equal(shrineArena.contains({ x: 109, y: 70, z: 100, dimension }), false);
  blocks.clear(); const pool = put("minecraft:lodestone", { x: 20, y: 50, z: 20 });
  // Rotation 1 maps (x,z) to (z,-x).
  put("minecraft:barrel", { x: 17, y: 51, z: 24 }); put("aionbound:algae_block", { x: 17, y: 50, z: 23 }); put("aionbound:crystal_stone", { x: 24, y: 51, z: 14 });
  const poolArena = resolvePearlDepthsArena(pool); assert.equal(poolArena.formId, "deep_pool_entrance"); assert.equal(poolArena.rotationIndex, 1);
  assert.equal(poolArena.contains({ x: 7, y: 49, z: 29, dimension }), true); assert.equal(poolArena.contains({ x: 6, y: 50, z: 20, dimension }), false);
});

test("pull is five seconds, capped four, and late join never rescales health", () => {
  const h = harness(5), id = h.service.begin(h.players[0], h.arena); h.tick(99); assert.equal(h.spawned.length, 0); h.tick(100);
  const session = h.service.sessions.get(id); assert.equal(session.scalingParticipants.size, 4); assert.equal(session.rewardParticipants.size, 4);
  assert.equal(session.targetHealth, pearlDepthsHealth(4)); assert.equal(session.targetHealth, 988);
  const lateHarness = harness(), pulled = lateHarness.pull(), late = player("late", lateHarness.dimension, { x: 30, y: 64, z: 0 }); lateHarness.players.push(late);
  lateHarness.tick(101); late.location.x = 0; lateHarness.tick(102); lateHarness.tick(401); assert.equal(pulled.rewardParticipants.has("late"), false); lateHarness.tick(402);
  assert.equal(pulled.rewardParticipants.has("late"), true); assert.equal(pulled.targetHealth, 520); assert.equal(pulled.scalingParticipants.size, 1);
});

test("70/40/15/enrage phases, serialized attack cooldowns, and bounded add trimming hold", () => {
  assert.deepEqual([pearlDepthsPhase(1), pearlDepthsPhase(.70), pearlDepthsPhase(.40), pearlDepthsPhase(.15), pearlDepthsPhase(1, 8400)], [0, 1, 2, 3, 3]);
  const h = harness(), session = h.pull(); session.boss.getComponent("minecraft:health").currentValue = 300; h.tick(101); assert.equal(session.phase, 1); assert.equal(session.attack.id, "drown_hymn");
  session.attack = null; session.globalReadyAt = 0; session.attackCursor = 3; h.tick(102); assert.equal(session.attack.id, "reed_serpent_call"); h.tick(139); assert.equal(session.adds.length, 2);
  session.attack = null; session.globalReadyAt = 0; session.attackReadyAt.clear(); session.attackCursor = 3; h.tick(140); h.tick(177); assert.equal(session.adds.length, 3);
  session.boss.getComponent("minecraft:health").currentValue = 70; h.tick(178); assert.equal(session.phase, 3); assert.equal(session.adds.length, 2);
  assert.equal(h.spawned.filter(value => value.hasTag?.(PEARL_DEPTHS.trimmedAddTag)).length, 1);
  session.attack = { id: "silt_grasp", stage: "recovery", stageEnds: 200 }; h.tick(200);
  assert.equal(session.globalReadyAt, 278); assert.equal(session.attackReadyAt.get("silt_grasp"), 370);
});

test("Drown Hymn is transition-only before Flood Claim and joins rotation only there", () => {
  const h = harness(), session = h.pull();
  session.phase = 2; session.attack = null; session.globalReadyAt = 0; session.attackReadyAt.clear(); session.attackCursor = 3; h.tick(101);
  assert.notEqual(session.attack.id, "drown_hymn");
  session.phase = 3; session.attack = null; session.globalReadyAt = 0; session.attackReadyAt.clear(); session.attackCursor = 3; h.tick(102);
  assert.equal(session.attack.id, "drown_hymn");
});

test("leash and wipe restore transient arena state without clearing durable completion", () => {
  const leash = harness(), session = leash.pull(); session.boss.location.x = 30; leash.tick(101); leash.tick(300); assert.equal(leash.service.sessions.size, 1); leash.tick(301); assert.equal(leash.service.sessions.size, 0); assert.equal(leash.restored.length, 1);
  const wipe = harness(), wiped = wipe.pull(); wipe.players[0].health.currentValue = 0; wipe.tick(101); wipe.tick(400); assert.equal(wipe.service.sessions.size, 1); wipe.tick(401); assert.equal(wipe.service.sessions.size, 0); assert.ok(wiped.boss.removed);
});

test("natural Marsh Wight is ecology-only; valid death orders durable credit before mask", () => {
  const ecology = harness(), natural = entity(PEARL_DEPTHS.bossType, { x: 0, y: 64, z: 0 }, ecology.dimension);
  assert.equal(ecology.service.bossDeath({ deadEntity: natural }), false); assert.equal(ecology.getWorld().encounters.terminal[PEARL_DEPTHS.worldCompletionKey], undefined);
  const h = harness(), session = h.pull(); assert.equal(h.kill(session), true);
  const credits = h.playerRecords.get("p1").credits;
  assert.equal(credits[PEARL_DEPTHS.sealCreditKey], true); assert.equal(credits[PEARL_DEPTHS.entitlementKey], true); assert.equal(credits[PEARL_DEPTHS.maskClaimedKey], true);
  assert.equal(h.terminals[0][1][PEARL_DEPTHS.sealCreditKey], true); assert.equal(h.masks.length, 1); assert.equal(h.materials.length, 1); assert.equal(h.caches.length, 1);
  h.system.currentTick++; const repeat = h.pull(); h.kill(repeat); assert.equal(h.masks.length, 1); assert.equal(h.materials.length, 2); assert.equal(h.caches.length, 2);
});

test("full inventory preserves entitlement and recovery interaction cannot fall through", () => {
  const h = harness(1, false), session = h.pull(); h.kill(session);
  const credits = h.playerRecords.get("p1").credits; assert.equal(credits[PEARL_DEPTHS.entitlementKey], true); assert.notEqual(credits[PEARL_DEPTHS.maskClaimedKey], true);
  assert.equal(h.service.blockInteraction(h.players[0], {}), true); assert.equal(h.service.sessions.size, 0); assert.equal(h.masks.length, 0); assert.match(h.warnings.at(-1), /recovery remains pending/);
});

test("disconnect grace queues existing-domain recovery and migration is idempotent", () => {
  const h = harness(2), session = h.pull(), offline = h.players.pop(); h.tick(101); h.system.currentTick = 1200; assert.equal(h.kill(session), true);
  assert.equal(h.getWorld().encounters.pendingPearlDepths[offline.id].entitlement, true); h.players.push(offline); h.tick(1220);
  assert.equal(h.getWorld().encounters.pendingPearlDepths[offline.id], undefined); assert.equal(h.playerRecords.get(offline.id).credits[PEARL_DEPTHS.sealCreditKey], true);
  const source = { encounters: { active: { "pearl_depths:x": { encounterId: PEARL_DEPTHS.id }, other: { type: "other" } }, terminal: {}, pendingPearlDepths: { p: { entitlement: true } } } };
  const once = migrateWorld(source); assert.deepEqual(migrateWorld(once), once); assert.deepEqual(Object.keys(once.encounters.active), ["other"]); assert.equal(once.encounters.pendingPearlDepths.p.entitlement, true);
});

test("service introduces no damage, radius, persistent block mutation, or Ashen activation", async () => {
  const source = await readFile(resolve(ROOT, "behavior_pack/scripts/pearl_depths.js"), "utf8");
  for (const forbidden of ["applyDamage", "damageAmount", "arenaRadius", "setPermutation", "setType", "createKilnSkyService", "ashEquipmentRoles"]) assert.equal(source.includes(forbidden), false);
});
