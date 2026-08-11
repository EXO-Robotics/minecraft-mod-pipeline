import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { THORN_COURT, createThornCourtService, thornCourtHealth, thornCourtPhase } from "../behavior_pack/scripts/thorn_court.js";
import { migratePlayer, migrateWorld } from "../behavior_pack/scripts/state.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

class FakeItemStack { constructor(typeId, amount) { this.typeId = typeId; this.amount = amount; } }

function makeEntity(typeId, location) {
  const tags = new Set(), properties = new Map();
  const health = { currentValue: 52, maxValue: 52, setCurrentValue(value) { this.currentValue = value; } };
  return {
    typeId, location: { ...location }, removed: false, effects: [],
    addTag: tag => tags.add(tag), removeTag: tag => tags.delete(tag), hasTag: tag => tags.has(tag), getTags: () => [...tags],
    setDynamicProperty: (key, value) => properties.set(key, value), getDynamicProperty: key => properties.get(key),
    getComponent: id => id === "minecraft:health" ? health : undefined,
    addEffect(name, duration, options) { this.effects.push({ name, duration, options }); },
    remove() { this.removed = true; },
  };
}

function makePlayer(id, dimension, location = { x: 0, y: 64, z: 0 }) {
  const health = { currentValue: 20 };
  return { id, typeId: "minecraft:player", dimension, location: { ...location }, getComponent: type => type === "minecraft:health" ? health : undefined, health };
}

function harness(playerCount = 1) {
  const spawned = [], items = [], warnings = [], material = [], chests = [];
  const dimension = {
    id: "minecraft:overworld",
    spawnEntity(typeId, location) { const entity = makeEntity(typeId, location); spawned.push(entity); return entity; },
    spawnItem(item, location) { items.push({ item, location }); return { item }; },
  };
  const players = Array.from({ length: playerCount }, (_, index) => makePlayer(`p${index + 1}`, dimension, { x: index, y: 64, z: 0 }));
  let worldRecord = migrateWorld({}), failWorldSave = false;
  const playerRecords = new Map(players.map(player => [player.id, migratePlayer({})]));
  const state = {
    worldState: () => structuredClone(worldRecord),
    saveWorld(value) { if (failWorldSave) return false; worldRecord = structuredClone(value); return true; },
    playerState: player => structuredClone(playerRecords.get(player.id) ?? migratePlayer({})),
    savePlayer(player, value) { playerRecords.set(player.id, structuredClone(value)); return true; },
    warn(_player, message) { warnings.push(message); },
  };
  const system = { currentTick: 0 };
  const world = { getAllPlayers: () => players, getDimension: () => dimension };
  const service = createThornCourtService({
    world, system, ItemStack: FakeItemStack, state,
    boundedEntities: () => spawned.filter(entity => !entity.removed),
    rewardHooks: {
      deliverTrophy(player, typeId) { player.dimension.spawnItem(new FakeItemStack(typeId, 1), player.location); return true; },
      grantMaterialPackage(player, context) { material.push([player.id, context]); return true; },
      openArenaChest(context) { chests.push(context); return true; },
    },
  });
  const advance = tick => { system.currentTick = tick; service.tick(); };
  const pull = () => { const start = system.currentTick; service.begin(players[0], { x: 0, y: 64, z: 0 }); advance(start + THORN_COURT.armTicks); return [...service.sessions.values()][0]; };
  const kill = (session, killer = players[0], cause = "entityAttack") => service.bossDeath({ deadEntity: session.boss, damageSource: { cause, damagingEntity: killer } });
  return {
    service, state, system, world, dimension, players, spawned, items, warnings, material, chests, advance, pull, kill,
    playerRecords, getWorld: () => structuredClone(worldRecord), setFailWorldSave: value => { failWorldSave = value; },
  };
}

test("runtime is byte-bound to the two ratified proposal siblings", async () => {
  const behaviorBytes = await readFile(resolve(ROOT, "engineering/authority/support-proposals/W1-CREATIVE-003/thorn_court_behavior_proposal.json"));
  const lootBytes = await readFile(resolve(ROOT, "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json"));
  assert.equal(createHash("sha256").update(behaviorBytes).digest("hex"), "04f7b9a75be6ac542d3488bd7563a601dcb94603905479b7c3e766c94b9d48c1");
  assert.equal(createHash("sha256").update(lootBytes).digest("hex"), "4412b24ad680a30e5548c731f8acba94e8fd858e4bb94f701a16eb17141f5ab7");
  const proposal = JSON.parse(behaviorBytes).proposal, guard = JSON.parse(lootBytes).proposal.arena_reward_guard;
  assert.equal(THORN_COURT.soloHealth, proposal.health.solo); assert.equal(THORN_COURT.participantScale, proposal.health.per_additional_locked_participant_multiplier);
  assert.equal(THORN_COURT.participantCap, proposal.health.participant_cap); assert.equal(THORN_COURT.arenaRadius, proposal.reset.arena_radius_blocks);
  assert.equal(THORN_COURT.worldCompletionKey, proposal.persistence.world_completion_key); assert.equal(THORN_COURT.playerCompletionKey, proposal.persistence.player_completion_key);
  assert.equal(THORN_COURT.entitlementKey, proposal.persistence.reward_entitlement_key); assert.equal(THORN_COURT.trophyItem, "aionbound:thorn_stalker_skull");
  assert.equal(guard.regular_entity_or_command_kill_can_grant_trophy, false);
});

test("ratified constants, health scaling, thresholds, timing, leash, and caps are exact", () => {
  assert.deepEqual([1, 2, 3, 4].map(thornCourtHealth), [360, 486, 612, 738]);
  assert.deepEqual([thornCourtPhase(1), thornCourtPhase(0.7), thornCourtPhase(0.35), thornCourtPhase(0.1)], [0, 1, 2, 3]);
  assert.equal(thornCourtPhase(1, 7200), 3);
  assert.deepEqual(THORN_COURT.phases.map(phase => [phase.enter, phase.exit, phase.addCap]), [[1, .7, 0], [.7, .35, 2], [.35, .1, 2], [.1, 0, 2]]);
  assert.equal(THORN_COURT.arenaRadius, 48); assert.equal(THORN_COURT.globalAddCap, 4); assert.equal(THORN_COURT.participantCap, 4);
  assert.deepEqual(THORN_COURT.attacks.death_bloom_transition, { telegraph: 36, active: 10, recovery: 30, cooldown: null });
});

test("five-second continuous residency locks at pull, scales once, and tags only the spawned arena shell", () => {
  const h = harness(5), id = h.service.begin(h.players[0], { x: 0, y: 64, z: 0 });
  h.advance(99); assert.equal(h.spawned.length, 0);
  h.advance(100); const session = h.service.sessions.get(id);
  assert.ok(session); assert.equal(session.participants.size, 4); assert.equal(session.targetHealth, 738);
  assert.equal(session.boss.hasTag(THORN_COURT.apexTag), true);
  assert.equal(session.boss.getDynamicProperty(THORN_COURT.sessionProperty), id);
  assert.equal(session.boss.getComponent("minecraft:health").currentValue, 738);
});

test("leaving during the residency window excludes the player at pull", () => {
  const h = harness(2); h.service.begin(h.players[0]);
  h.players[1].location.x = 60; h.advance(40); h.players[1].location.x = 0; h.advance(100);
  const session = [...h.service.sessions.values()][0];
  assert.deepEqual([...session.participants.keys()], ["p1"]); assert.equal(session.targetHealth, 360);
});

test("late join requires fifteen continuous seconds and closes before Crown of Thorns without rescaling", () => {
  const h = harness(1), session = h.pull(), late = makePlayer("late", h.dimension, { x: 60, y: 64, z: 0 });
  h.players.push(late); h.advance(120); late.location.x = 0; h.advance(121); h.advance(420);
  assert.equal(session.participants.has("late"), false); h.advance(421); assert.equal(session.participants.has("late"), true);
  assert.equal(session.targetHealth, 360);
  const tooLate = makePlayer("too-late", h.dimension); h.players.push(tooLate);
  session.boss.getComponent("minecraft:health").currentValue = 100; h.advance(422); assert.equal(session.phase, 2);
  h.advance(800); assert.equal(session.participants.has("too-late"), false);
});

test("phase transitions are once-per-threshold, hard enrage is not an instant kill, and Howl adds remain bounded", () => {
  const h = harness(), session = h.pull();
  session.boss.getComponent("minecraft:health").currentValue = 250; h.advance(101);
  assert.equal(session.phase, 1); assert.equal(session.attack.id, "death_bloom_transition");
  h.advance(137); assert.equal(session.attack.stage, "active"); h.advance(147); assert.equal(session.attack.stage, "recovery");
  h.advance(177); assert.equal(session.attack, null);
  session.attack = null; session.nextAttackAt = 0; session.attackCursor = 4; h.advance(178);
  assert.equal(session.attack.id, "howl_call"); h.advance(210); assert.equal(session.adds.size, 2);
  session.attack = null; session.nextAttackAt = 0; session.attackCursor = 4; h.advance(211); h.advance(243);
  assert.equal(session.adds.size, 2);
  session.boss.getComponent("minecraft:health").currentValue = 200; h.advance(7301);
  assert.equal(session.phase, 3); assert.ok(session.boss.getComponent("minecraft:health").currentValue > 0);
});

test("boss leash, wipe, and no-player timers reset only after their ratified grace windows", () => {
  const leash = harness(), leashSession = leash.pull(); leashSession.boss.location.x = 49; leash.advance(101); leash.advance(300);
  assert.equal(leash.service.sessions.size, 1); leash.advance(301); assert.equal(leash.service.sessions.size, 0);

  const wipe = harness(), wipeSession = wipe.pull(); wipe.players[0].health.currentValue = 0; wipe.advance(101); wipe.advance(400);
  assert.equal(wipe.service.sessions.size, 1); wipe.advance(401); assert.equal(wipe.service.sessions.size, 0);

  const absent = harness(), absentSession = absent.pull(); absent.players.splice(0); absent.advance(101); absent.advance(400);
  assert.equal(absent.service.sessions.size, 1); absent.advance(401); assert.equal(absent.service.sessions.size, 0);
  assert.ok(absentSession.boss.removed);
});

test("only a tagged active arena death by a participant can create seal and trophy entitlement", () => {
  const ecology = harness(), natural = makeEntity(THORN_COURT.bossType, { x: 0, y: 64, z: 0 });
  assert.equal(ecology.service.bossDeath({ deadEntity: natural, damageSource: { cause: "entityAttack", damagingEntity: ecology.players[0] } }), false);
  assert.equal(ecology.items.length, 0);

  const command = harness(), session = command.pull();
  assert.equal(command.service.bossDeath({ deadEntity: session.boss, damageSource: { cause: "suicide" } }), false);
  assert.equal(command.items.length, 0); assert.equal(command.playerRecords.get("p1").credits[THORN_COURT.sealCreditKey], undefined);

  const arena = harness(), valid = arena.pull(); assert.equal(arena.kill(valid), true);
  const credits = arena.playerRecords.get("p1").credits;
  assert.equal(credits[THORN_COURT.playerCompletionKey], true); assert.equal(credits[THORN_COURT.entitlementKey], true);
  assert.equal(credits[THORN_COURT.sealCreditKey], true); assert.equal(credits[THORN_COURT.trophyClaimedKey], true);
  assert.equal(arena.items[0].item.typeId, THORN_COURT.trophyItem);
});

test("repeat clear reopens materials and arena chest but never duplicates progression or trophy", () => {
  const h = harness(), first = h.pull(); h.kill(first);
  h.system.currentTick += 1; const repeat = h.pull(); h.kill(repeat);
  assert.equal(h.items.length, 1); assert.equal(h.material.length, 2); assert.deepEqual(h.material.map(([, context]) => context.repeatClear), [false, true]);
  assert.equal(h.chests.length, 2); assert.equal(h.getWorld().encounters.terminal[THORN_COURT.worldCompletionKey].completed, true);
});

test("disconnect grace queues bounded durable entitlement and fulfills it on reconnect", () => {
  const h = harness(2), session = h.pull(), offline = h.players.pop();
  h.advance(101); assert.equal(session.participants.get(offline.id).disconnectedAt, 101);
  h.system.currentTick = 500; assert.equal(h.kill(session), true);
  assert.equal(h.getWorld().encounters.pendingThornCourt[offline.id].entitlement, true);
  h.players.push(offline); h.system.currentTick = 520; h.service.tick();
  assert.equal(h.getWorld().encounters.pendingThornCourt[offline.id], undefined);
  assert.equal(h.playerRecords.get(offline.id).credits[THORN_COURT.sealCreditKey], true);
});

test("at-most-once guard commits before delivery and uncertain recovery never emits a second physical item", () => {
  const h = harness(), player = h.players[0];
  const record = h.playerRecords.get(player.id); record.credits[THORN_COURT.entitlementKey] = true; record.credits[THORN_COURT.trophyClaimedKey] = true;
  record.credits[THORN_COURT.trophyClaimStateKey] = "inflight";
  assert.equal(h.service.recoverTrophy(player), true); assert.equal(h.items.length, 0);
  assert.equal(h.playerRecords.get(player.id).credits[THORN_COURT.trophyClaimStateKey], "museum_recovery_only");
  assert.equal(h.service.claimTrophy(player), false); assert.equal(h.items.length, 0);
});

test("reload migration is idempotent, clears only active Thorn Court rows, and reconciliation removes only tagged orphans", () => {
  const source = { encounters: { active: { "thorn_court:x": { encounterId: THORN_COURT.id }, other: { type: "other" } }, terminal: {}, pendingThornCourt: { p: { entitlement: true } } } };
  const once = migrateWorld(source); assert.deepEqual(migrateWorld(once), once); assert.deepEqual(Object.keys(once.encounters.active), ["other"]);
  assert.equal(once.encounters.pendingThornCourt.p.entitlement, true);

  const h = harness(), natural = makeEntity(THORN_COURT.bossType, { x: 0, y: 64, z: 0 }), orphan = makeEntity(THORN_COURT.bossType, { x: 0, y: 64, z: 0 });
  orphan.addTag(THORN_COURT.apexTag); orphan.setDynamicProperty(THORN_COURT.sessionProperty, "old-session");
  h.spawned.push(natural, orphan); h.service.reconcile(); assert.equal(natural.removed, false); assert.equal(orphan.removed, true);
});

test("mastery trophies are absent from all critical completion predicates", () => {
  const source = `${thornCourtHealth}\n${thornCourtPhase}\n${createThornCourtService}`;
  assert.equal(source.includes("briar_elk_trophy"), false); assert.equal(source.includes("mosskip_trophy"), false);
  assert.equal(THORN_COURT.trophyItem, "aionbound:thorn_stalker_skull");
});
