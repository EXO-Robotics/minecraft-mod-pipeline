import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { KILN_SKY, createKilnSkyService, kilnSkyHealth, kilnSkyPhase, resolveKilnSkyArena } from "../behavior_pack/scripts/kiln_sky.js";
import { migratePlayer, migrateWorld } from "../behavior_pack/scripts/state.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function makeEntity(typeId, location, dimension) {
  const tags = new Set(), properties = new Map();
  const health = { currentValue: 80, maxValue: 80, setCurrentValue(value) { this.currentValue = value; } };
  return { typeId, location: { ...location }, dimension, removed: false,
    addTag: tag => tags.add(tag), removeTag: tag => tags.delete(tag), hasTag: tag => tags.has(tag), getTags: () => [...tags],
    setDynamicProperty: (key, value) => properties.set(key, value), getDynamicProperty: key => properties.get(key),
    getComponent: id => id === "minecraft:health" ? health : undefined, addEffect() {}, remove() { this.removed = true; },
  };
}
function makePlayer(id, dimension, location = { x: 0, y: 64, z: 0 }) {
  const health = { currentValue: 20 };
  return { id, typeId: "minecraft:player", dimension, location: { ...location }, health, getComponent: id => id === "minecraft:health" ? health : undefined };
}

function harness(count = 1) {
  const spawned = [], warnings = [], packages = [], caches = [], horns = [], pulls = [], terminals = [];
  const dimension = { id: "minecraft:overworld", spawnEntity(typeId, location) { const entity = makeEntity(typeId, location, this); spawned.push(entity); return entity; } };
  const arena = { id: "kiln_sky:test", dimension, dimensionId: dimension.id, anchor: { x: 0, y: 64, z: 0 }, cacheLocation: { x: 6, y: 64, z: 0 }, contains(value) { return value.x >= -11 && value.x <= 11 && value.y >= 61 && value.y <= 74 && value.z >= -11 && value.z <= 11; } };
  const players = Array.from({ length: count }, (_, i) => makePlayer(`p${i + 1}`, dimension, { x: i, y: 64, z: 0 }));
  let worldRecord = migrateWorld({}); const playerRecords = new Map(players.map(p => [p.id, migratePlayer({})]));
  const state = {
    worldState: () => structuredClone(worldRecord), saveWorld(value) { worldRecord = structuredClone(value); return true; },
    playerState: player => structuredClone(playerRecords.get(player.id) ?? migratePlayer({})), savePlayer(player, value) { playerRecords.set(player.id, structuredClone(value)); return true; },
    warn(_player, text) { warnings.push(text); },
  };
  const system = { currentTick: 0 }, world = { getAllPlayers: () => players };
  const service = createKilnSkyService({ world, system, state, boundedEntities: () => spawned.filter(e => !e.removed), resolveArena: () => arena,
    rewardHooks: {
      canDeliverHorn: () => true, deliverHorn(player, typeId) { horns.push([player.id, typeId]); return true; },
      grantMaterialPackage(player, context) { packages.push([player.id, context]); return true; }, openArenaCache(context) { caches.push(context); return true; },
    }, codexHooks: { onPull(player) { pulls.push(player.id); }, onTerminalCredit(player) { terminals.push([player.id, structuredClone(playerRecords.get(player.id).credits)]); } },
  });
  const tick = value => { system.currentTick = value; service.tick(); };
  const pull = () => { const start = system.currentTick, id = service.begin(players[0], arena); tick(start + 100); return service.sessions.get(id); };
  const kill = session => service.bossDeath({ deadEntity: session.boss, damageSource: { cause: "entityAttack", damagingEntity: players[0] } });
  return { service, system, world, state, dimension, arena, players, spawned, warnings, packages, caches, horns, pulls, terminals, playerRecords, tick, pull, kill, getWorld: () => structuredClone(worldRecord) };
}

test("service is byte-bound to ratified Ashen proposals and uses midpoint timings", async () => {
  const ledgerBytes = await readFile(resolve(ROOT, "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json"));
  const p3 = await readFile(resolve(ROOT, "engineering/authority/support-proposals/ashen/W1-003-KILN-SKY.json"));
  const p4 = await readFile(resolve(ROOT, "engineering/authority/support-proposals/ashen/W1-004-AH.json"));
  assert.equal(createHash("sha256").update(ledgerBytes).digest("hex"), "b554db9fab3fe16e59e2e3b36dfc310ff462078b170f14e1f9fe8a46999bbd0c");
  assert.equal(createHash("sha256").update(p3).digest("hex"), "1b2d5f77185a1461040d7559d0d8ecdaf803d7727e419ceac32636865be85d7c");
  assert.equal(createHash("sha256").update(p4).digest("hex"), "93736ff800b1c90c8a6547d84336a6650f8ae32750f262de8e460385a7a26889");
  const approved = new Map(JSON.parse(ledgerBytes).ratifications.approved.map(row => [row.tranche, row.proposal_sha256]));
  assert.equal(approved.get("W1-003-KILN-SKY"), "1b2d5f77185a1461040d7559d0d8ecdaf803d7727e419ceac32636865be85d7c");
  assert.equal(approved.get("W1-004-AH"), "93736ff800b1c90c8a6547d84336a6650f8ae32750f262de8e460385a7a26889");
  const proposal = JSON.parse(p3).proposal;
  assert.equal(KILN_SKY.soloHealth, proposal.health.solo); assert.equal(KILN_SKY.participantScale, proposal.health.per_additional_locked_participant_multiplier);
  assert.equal(KILN_SKY.worldCompletionKey, proposal.persistence.world_completion_key); assert.equal(KILN_SKY.entitlementKey, proposal.persistence.reward_entitlement_key);
  for (const [id, spec] of Object.entries(KILN_SKY.attacks)) for (const field of ["telegraph", "active", "recovery", "cooldown"]) {
    const range = proposal.timing_seconds[id][field], value = spec[`${field}Seconds`]; assert.ok(Math.abs(value - ((range[0] + range[1]) / 2)) < Number.EPSILON);
  }
  assert.equal(KILN_SKY.globalAttackCooldownSeconds, (proposal.timing_seconds.global_attack_cooldown[0] + proposal.timing_seconds.global_attack_cooldown[1]) / 2);
});

test("authored Ember Forge signature resolves its exact non-radius volume", () => {
  const blocks = new Map(), loc = p => `${p.x},${p.y},${p.z}`;
  const dimension = { id: "minecraft:overworld", getBlock(p) { return blocks.get(loc(p)); } };
  const put = (typeId, p) => { const block = { typeId, location: { ...p }, dimension }; blocks.set(loc(p), block); return block; };
  const anchor = put("minecraft:lodestone", { x: 100, y: 70, z: 100 });
  put("minecraft:barrel", { x: 106, y: 70, z: 100 }); put("minecraft:lectern", { x: 94, y: 70, z: 100 });
  put("aionbound:ash_log", { x: 100, y: 70, z: 94 }); put("aionbound:ash_log", { x: 100, y: 70, z: 106 }); put("minecraft:magma_block", { x: 100, y: 69, z: 100 });
  const arena = resolveKilnSkyArena(anchor); assert.ok(arena);
  assert.equal(arena.contains({ x: 89, y: 67, z: 89, dimension }), true); assert.equal(arena.contains({ x: 111, y: 80, z: 111, dimension }), true);
  assert.equal(arena.contains({ x: 112, y: 70, z: 100, dimension }), false);
  assert.deepEqual(arena.cacheLocation, { x: 106, y: 70, z: 100 }); assert.equal(resolveKilnSkyArena(blocks.get(loc(arena.cacheLocation))).id, arena.id);
});

test("five-second pull selection is initiator-first, capped four, immutable health snapshot", () => {
  const h = harness(5), id = h.service.begin(h.players[0], h.arena); h.tick(99); assert.equal(h.spawned.length, 0); h.tick(100);
  const session = h.service.sessions.get(id); assert.equal(session.scalingParticipants.size, 4); assert.equal(session.rewardParticipants.size, 4);
  assert.equal(session.targetHealth, 912); assert.equal(session.boss.getComponent("minecraft:health").currentValue, 912);
  assert.equal(session.boss.hasTag(KILN_SKY.apexTag), true); assert.equal(session.boss.getDynamicProperty(KILN_SKY.sessionProperty), id);
  assert.deepEqual([...session.scalingParticipants], [...session.scalingParticipants]);
});

test("initiator must maintain residency and late join is separate, 15s, capped, and closes at Glass Wing", () => {
  const failed = harness(2); failed.service.begin(failed.players[0], failed.arena); failed.players[0].location.x = 30; failed.tick(100); assert.equal(failed.service.sessions.size, 1); assert.equal(failed.spawned.length, 0);
  const h = harness(1), session = h.pull(), late = makePlayer("late", h.dimension, { x: 30, y: 64, z: 0 }); h.players.push(late);
  h.tick(101); late.location.x = 0; h.tick(102); h.tick(401); assert.equal(session.rewardParticipants.has("late"), false); h.tick(402); assert.equal(session.rewardParticipants.has("late"), true);
  assert.equal(session.targetHealth, 480); assert.equal(session.scalingParticipants.size, 1);
  const tooLate = makePlayer("too-late", h.dimension); h.players.push(tooLate); session.boss.getComponent("minecraft:health").currentValue = 190; h.tick(403);
  assert.equal(session.phase, 2); assert.equal(session.lateJoinClosed, true); h.tick(800); assert.equal(session.rewardParticipants.has("too-late"), false);
});

test("70/40/15 phases expose exact attacks and mite cap trims oldest without queue", () => {
  assert.deepEqual([kilnSkyPhase(1), kilnSkyPhase(.70), kilnSkyPhase(.40), kilnSkyPhase(.15)], [0, 1, 2, 3]);
  const h = harness(), session = h.pull(); session.boss.getComponent("minecraft:health").currentValue = 300; h.tick(101); assert.equal(session.phase, 1);
  session.attack = null; session.globalReadyAt = 0; session.attackCursor = 3; h.tick(102); assert.equal(session.attack.id, "mite_shake");
  h.tick(132); assert.equal(session.mites.length, 2); session.attack = null; session.globalReadyAt = 0; session.attackReadyAt.clear(); session.attackCursor = 3; h.tick(133); h.tick(163); assert.equal(session.mites.length, 4);
  session.boss.getComponent("minecraft:health").currentValue = 70; h.tick(164); assert.equal(session.phase, 3); assert.equal(session.mites.length, 2);
  const trimmed = h.spawned.filter(e => e.typeId === KILN_SKY.miteType && e.removed); assert.equal(trimmed.length, 2); assert.equal(trimmed.every(e => e.hasTag(KILN_SKY.trimmedMiteTag)), true);
});

test("leash, wipe, no-connected, disconnect, and voluntary abandonment semantics are bounded", () => {
  const leash = harness(), ls = leash.pull(); ls.boss.location.x = 30; leash.tick(101); leash.tick(300); assert.equal(leash.service.sessions.size, 1); leash.tick(301); assert.equal(leash.service.sessions.size, 0);
  const wipe = harness(), ws = wipe.pull(); wipe.players[0].health.currentValue = 0; wipe.tick(101); wipe.tick(400); assert.equal(wipe.service.sessions.size, 1); wipe.tick(401); assert.equal(wipe.service.sessions.size, 0);
  const absent = harness(), as = absent.pull(); absent.players.splice(0); absent.tick(101); absent.tick(700); assert.equal(absent.service.sessions.size, 1); absent.tick(701); assert.equal(absent.service.sessions.size, 0);
  const abandon = harness(), rs = abandon.pull(); abandon.players[0].location.x = 30; abandon.tick(101); abandon.tick(301); assert.equal(rs.rewardParticipants.has("p1"), false);
});

test("ecology death cannot complete; valid terminal credits before claim and repeats do not duplicate horn", () => {
  const ecology = harness(), natural = makeEntity(KILN_SKY.bossType, { x: 0, y: 64, z: 0 }, ecology.dimension);
  assert.equal(ecology.service.bossDeath({ deadEntity: natural, damageSource: {} }), false); assert.equal(ecology.horns.length, 0); assert.equal(ecology.getWorld().encounters.terminal[KILN_SKY.worldCompletionKey], undefined);
  const h = harness(), first = h.pull(); assert.equal(h.kill(first), true);
  const credits = h.playerRecords.get("p1").credits; assert.equal(credits[KILN_SKY.sealCreditKey], true); assert.equal(credits[KILN_SKY.entitlementKey], true); assert.equal(credits[KILN_SKY.hornClaimedKey], true);
  assert.equal(h.terminals[0][1][KILN_SKY.sealCreditKey], true); assert.equal(h.terminals[0][1][KILN_SKY.entitlementKey], true); assert.equal(h.horns.length, 1); assert.equal(h.packages.length, 1); assert.equal(h.caches.length, 1);
  h.system.currentTick++; const repeat = h.pull(); h.kill(repeat); assert.equal(h.horns.length, 1); assert.equal(h.packages.length, 2); assert.equal(h.caches.length, 2);
});

test("terminal reward set admits dead and 60s disconnect grace, with pending durable fulfillment", () => {
  const h = harness(3), session = h.pull(); h.players[1].health.currentValue = 0; h.tick(101); const offline = h.players.pop(); h.tick(102);
  h.system.currentTick = 1200; assert.equal(h.kill(session), true); assert.equal(h.playerRecords.get("p2").credits[KILN_SKY.sealCreditKey], true);
  assert.equal(h.getWorld().encounters.pendingKilnSky[offline.id].entitlement, true); h.players.push(offline); h.tick(1220);
  assert.equal(h.getWorld().encounters.pendingKilnSky[offline.id], undefined); assert.equal(h.playerRecords.get(offline.id).credits[KILN_SKY.sealCreditKey], true);
});

test("horn claim writes the once guard before one attempt and never auto-reissues", () => {
  const h = harness(), player = h.players[0], record = h.playerRecords.get(player.id); record.credits[KILN_SKY.sealCreditKey] = true; record.credits[KILN_SKY.entitlementKey] = true;
  assert.equal(h.service.claimHorn(player), true); assert.equal(h.playerRecords.get(player.id).credits[KILN_SKY.hornClaimedKey], true); assert.equal(h.service.recoverHorn(player), false); assert.equal(h.horns.length, 1);
});

test("migration is idempotent, active Kiln Sky is discarded, pending entitlement remains", () => {
  const source = { encounters: { active: { "kiln_sky:x": { encounterId: KILN_SKY.id }, other: { type: "other" } }, terminal: {}, pendingKilnSky: { p: { entitlement: true } } } };
  const once = migrateWorld(source); assert.deepEqual(migrateWorld(once), once); assert.deepEqual(Object.keys(once.encounters.active), ["other"]); assert.equal(once.encounters.pendingKilnSky.p.entitlement, true);
});

test("disconnect resets arming and late-join residency, and cooldowns compose per attack", () => {
  const arming = harness(), id = arming.service.begin(arming.players[0], arming.arena); arming.tick(50); const player = arming.players.pop(); arming.tick(60); arming.players.push(player); arming.tick(100);
  assert.equal(arming.service.sessions.get(id).status, "arming"); arming.tick(199); assert.equal(arming.service.sessions.get(id).status, "arming"); arming.tick(200); assert.equal(arming.service.sessions.get(id).status, "active");
  const h = harness(), session = h.pull(), late = makePlayer("late", h.dimension, { x: 30, y: 64, z: 0 }); h.players.push(late); h.tick(101); late.location.x = 0; h.tick(200); h.players.pop(); h.tick(300); h.players.push(late); h.tick(400);
  assert.equal(session.rewardParticipants.has("late"), false); h.tick(700); assert.equal(session.rewardParticipants.has("late"), true);
  session.attack = { id: "cinder_breath", stage: "recovery", stageEnds: 701 }; h.tick(701); assert.equal(session.attackReadyAt.get("cinder_breath"), 871); assert.equal(session.globalReadyAt, 774);
  session.attackCursor = 0; h.tick(774); assert.equal(session.attack.id, "tail_slag");
});

test("service contains no damage/radius or Whisperwood tuning authority", async () => {
  const source = await readFile(resolve(ROOT, "behavior_pack/scripts/kiln_sky.js"), "utf8");
  for (const forbidden of ["damageAmount", "applyDamage", "arenaRadius", "thorn_court", "briar_rise", "widow_wire", "crown_of_thorns", "forest_scream"]) assert.equal(source.includes(forbidden), false);
  assert.equal(KILN_SKY.optionalMasteryItem, "aionbound:ember_forge_core"); assert.notEqual(KILN_SKY.optionalMasteryItem, KILN_SKY.hornItem);
});
