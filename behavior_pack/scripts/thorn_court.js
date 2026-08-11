export const THORN_COURT = Object.freeze({
  id: "aionbound:thorn_court",
  bossType: "aionbound:thorn_stalker",
  apexTag: "aionbound.thorn_court_apex",
  addTag: "aionbound.thorn_court_add",
  sessionProperty: "aionbound:thorn_court_session",
  soloHealth: 360,
  participantScale: 0.35,
  participantCap: 4,
  arenaRadius: 48,
  armTicks: 100,
  lateJoinTicks: 300,
  disconnectGraceTicks: 1200,
  bossLeashGraceTicks: 200,
  noEligibleGraceTicks: 600,
  wipeGraceTicks: 300,
  hardEnrageTicks: 7200,
  globalAddCap: 4,
  phases: Object.freeze([
    Object.freeze({ id: "briar_rise", enter: 1, exit: 0.7, addCap: 0 }),
    Object.freeze({ id: "widow_wire", enter: 0.7, exit: 0.35, addCap: 2 }),
    Object.freeze({ id: "crown_of_thorns", enter: 0.35, exit: 0.1, addCap: 2 }),
    Object.freeze({ id: "forest_scream", enter: 0.1, exit: 0, addCap: 2 }),
  ]),
  // Midpoints are bounded engineering choices inside the ratified closed ranges.
  attacks: Object.freeze({
    lunge_barb: Object.freeze({ telegraph: 16, active: 7, recovery: 20, cooldown: 100 }),
    thorn_fan: Object.freeze({ telegraph: 22, active: 4, recovery: 16, cooldown: 130 }),
    root_snare: Object.freeze({ telegraph: 30, active: 80, recovery: 14, cooldown: 200 }),
    silk_spit: Object.freeze({ telegraph: 20, active: 4, recovery: 16, cooldown: 170 }),
    howl_call: Object.freeze({ telegraph: 32, active: 8, recovery: 24, cooldown: 420 }),
    death_bloom_transition: Object.freeze({ telegraph: 36, active: 10, recovery: 30, cooldown: null }),
  }),
  globalAttackCooldownTicks: 70,
  worldCompletionKey: "aionbound.encounter.thorn_court.completed.v1",
  playerCompletionKey: "aionbound.player.thorn_court.completed.v1",
  entitlementKey: "aionbound.player.thorn_court.reward_entitled.v1",
  sealCreditKey: "aionbound.player.thorn_court.seal_credit.v1",
  trophyClaimedKey: "aionbound.player.thorn_court.trophy_claimed.v1",
  trophyClaimStateKey: "aionbound.player.thorn_court.trophy_claim_state.v1",
  trophyRecoveryKey: "aionbound.player.thorn_court.trophy_recovery.v1",
  trophyItem: "aionbound:thorn_stalker_skull",
});

const TICKS_PER_SECOND = 20;
const sq = value => value * value;
const distanceSquared = (a, b) => sq(a.x - b.x) + sq(a.y - b.y) + sq(a.z - b.z);
const isInside = (location, center) => distanceSquared(location, center) <= sq(THORN_COURT.arenaRadius);
const dimensionId = value => value?.id ?? "minecraft:overworld";
const isAlive = player => (player.getComponent?.("minecraft:health")?.currentValue ?? 1) > 0;
const isEntityAvailable = entity => entity && entity.removed !== true && entity.isValid !== false;

function addTag(entity, tag) { if (!entity.hasTag?.(tag)) entity.addTag?.(tag); }
function clearPrefixedTags(entity, prefix) {
  for (const tag of entity.getTags?.() ?? []) if (tag.startsWith(prefix)) entity.removeTag?.(tag);
}
function setPhaseTag(entity, phase) {
  clearPrefixedTags(entity, "aionbound.thorn_court.phase.");
  addTag(entity, `aionbound.thorn_court.phase.${phase}`);
}
function setAttackTag(entity, attack, stage) {
  clearPrefixedTags(entity, "aionbound.thorn_court.attack.");
  if (attack && stage) addTag(entity, `aionbound.thorn_court.attack.${attack}.${stage}`);
}

export function thornCourtHealth(participants) {
  const bounded = Math.max(1, Math.min(THORN_COURT.participantCap, Math.trunc(participants || 1)));
  return Math.round(THORN_COURT.soloHealth * (1 + THORN_COURT.participantScale * (bounded - 1)));
}

export function thornCourtPhase(healthFraction, elapsedTicks = 0) {
  if (elapsedTicks >= THORN_COURT.hardEnrageTicks || healthFraction <= 0.1) return 3;
  if (healthFraction <= 0.35) return 2;
  if (healthFraction <= 0.7) return 1;
  return 0;
}

export function createThornCourtService({ world, system, ItemStack, state, boundedEntities, rewardHooks = {}, codexHooks = {} }) {
  const sessions = new Map();
  let sequence = 0;
  const hooks = Object.freeze({
    deliverTrophy: rewardHooks.deliverTrophy ?? ((player, itemId) => {
      player.dimension.spawnItem(new ItemStack(itemId, 1), player.location);
      return true;
    }),
    grantMaterialPackage: rewardHooks.grantMaterialPackage ?? (() => false),
    openArenaChest: rewardHooks.openArenaChest ?? (() => false),
  });
  const codex = Object.freeze({
    onPull: codexHooks.onPull ?? (() => false),
    onTerminalCredit: codexHooks.onTerminalCredit ?? (() => false),
  });

  const sessionPlayers = session => world.getAllPlayers().filter(player => dimensionId(player.dimension) === session.dimensionId);
  const byId = id => world.getAllPlayers().find(player => player.id === id);
  const sessionId = (player, center) => `thorn_court:${dimensionId(player.dimension)}:${Math.floor(center.x)},${Math.floor(center.y)},${Math.floor(center.z)}:${++sequence}`;

  function playerCredits(player) {
    const current = state.playerState(player);
    return { current, credits: { ...(current.credits ?? {}) } };
  }

  function writeFirstCompletion(player) {
    const { current, credits } = playerCredits(player);
    const first = credits[THORN_COURT.playerCompletionKey] !== true;
    if (!first) return { saved: true, first: false };
    credits[THORN_COURT.playerCompletionKey] = true;
    credits[THORN_COURT.entitlementKey] = true;
    credits[THORN_COURT.sealCreditKey] = true;
    const saved = state.savePlayer(player, { ...current, credits });
    return { saved, first: saved };
  }

  function claimTrophy(player) {
    let { current, credits } = playerCredits(player);
    if (credits[THORN_COURT.entitlementKey] !== true || credits[THORN_COURT.trophyClaimedKey] === true) return false;
    // Commit the at-most-once guard before the external item effect. A crash
    // after delivery cannot replay a second physical trophy.
    credits[THORN_COURT.trophyClaimedKey] = true;
    credits[THORN_COURT.trophyClaimStateKey] = "inflight";
    if (!state.savePlayer(player, { ...current, credits })) return false;
    try {
      if (hooks.deliverTrophy(player, THORN_COURT.trophyItem) !== true) throw new Error("delivery_refused");
    } catch {
      ({ current, credits } = playerCredits(player));
      credits[THORN_COURT.trophyClaimedKey] = false;
      credits[THORN_COURT.trophyClaimStateKey] = "recoverable_synchronous_failure";
      credits[THORN_COURT.trophyRecoveryKey] = true;
      state.savePlayer(player, { ...current, credits });
      return false;
    }
    ({ current, credits } = playerCredits(player));
    credits[THORN_COURT.trophyClaimStateKey] = "delivered";
    credits[THORN_COURT.trophyRecoveryKey] = false;
    state.savePlayer(player, { ...current, credits });
    return true;
  }

  function recoverTrophy(player) {
    const { current, credits } = playerCredits(player);
    if (credits[THORN_COURT.entitlementKey] !== true) return false;
    if (credits[THORN_COURT.trophyClaimStateKey] === "recoverable_synchronous_failure") return claimTrophy(player);
    if (credits[THORN_COURT.trophyClaimStateKey] !== "inflight") return false;
    // An interrupted inflight claim is externally uncertain. Recovery records
    // museum/display fulfillment without risking a duplicate physical item.
    credits[THORN_COURT.trophyClaimStateKey] = "museum_recovery_only";
    credits[THORN_COURT.trophyRecoveryKey] = true;
    return state.savePlayer(player, { ...current, credits });
  }

  function queueOfflineEntitlement(playerId) {
    const w = state.worldState();
    const pending = { ...(w.encounters.pendingThornCourt ?? {}) };
    pending[playerId] = {
      completion: true,
      entitlement: true,
      sealCredit: true,
    };
    w.encounters.pendingThornCourt = pending;
    return state.saveWorld(w);
  }

  function flushPendingEntitlements() {
    const w = state.worldState(), pending = { ...(w.encounters.pendingThornCourt ?? {}) };
    let changed = false;
    for (const player of world.getAllPlayers()) {
      if (!pending[player.id]) continue;
      const result = writeFirstCompletion(player); if (!result.saved) continue;
      codex.onTerminalCredit(player);
      hooks.grantMaterialPackage(player, { encounterId: THORN_COURT.id, repeatClear: !result.first });
      delete pending[player.id]; changed = true;
      if (result.first) claimTrophy(player);
    }
    if (changed) { w.encounters.pendingThornCourt = pending; state.saveWorld(w); }
    return changed;
  }

  function begin(player, center = player.location) {
    if (sessions.size >= 1) { state.warn(player, "The Thorn Court is already stirring."); return null; }
    const id = sessionId(player, center), now = system.currentTick;
    const session = {
      id, status: "arming", initiator: player.id, dimension: player.dimension, dimensionId: dimensionId(player.dimension),
      center: { x: center.x, y: center.y, z: center.z }, armedAt: now, pullAt: now + THORN_COURT.armTicks,
      dwell: new Map(), lateDwell: new Map(), participants: new Map(), adds: new Set(), boss: null,
      phase: 0, attackCursor: 0, attack: null, nextAttackAt: 0, bossOutsideSince: null, noEligibleSince: null, wipeSince: null,
    };
    for (const candidate of sessionPlayers(session)) if (isInside(candidate.location, session.center)) session.dwell.set(candidate.id, now);
    sessions.set(id, session);
    return id;
  }

  function setBossHealth(boss, targetHealth) {
    const health = boss.getComponent?.("minecraft:health");
    const baseMax = health?.effectiveMax ?? health?.defaultValue ?? health?.maxValue ?? 52;
    const amplifier = Math.max(0, Math.ceil((targetHealth - baseMax) / 4) - 1);
    if (amplifier > 0) boss.addEffect?.("health_boost", 999999, { amplifier, showParticles: false });
    const refreshed = boss.getComponent?.("minecraft:health") ?? health;
    refreshed?.setCurrentValue?.(targetHealth);
    boss.setDynamicProperty?.("aionbound:thorn_court_target_health", targetHealth);
  }

  function pull(session) {
    const now = system.currentTick;
    const eligible = sessionPlayers(session).filter(player => {
      const enteredAt = session.dwell.get(player.id);
      return enteredAt !== undefined && now - enteredAt >= THORN_COURT.armTicks && isInside(player.location, session.center);
    }).slice(0, THORN_COURT.participantCap);
    if (!eligible.length) { sessions.delete(session.id); return false; }
    let boss;
    try {
      boss = session.dimension.spawnEntity(THORN_COURT.bossType, session.center);
      addTag(boss, THORN_COURT.apexTag);
      boss.setDynamicProperty?.(THORN_COURT.sessionProperty, session.id);
      for (const player of eligible) session.participants.set(player.id, { kind: "locked", disconnectedAt: null, lastInsideAt: now });
      session.targetHealth = thornCourtHealth(eligible.length);
      setBossHealth(boss, session.targetHealth);
      setPhaseTag(boss, THORN_COURT.phases[0].id);
    } catch {
      boss?.remove?.(); sessions.delete(session.id); return false;
    }
    session.boss = boss; session.status = "active"; session.pulledAt = now; session.nextAttackAt = now + THORN_COURT.globalAttackCooldownTicks;
    for (const player of eligible) codex.onPull(player);
    return true;
  }

  function updatePresence(session) {
    const now = system.currentTick, online = new Map(sessionPlayers(session).map(player => [player.id, player]));
    for (const [id, participant] of session.participants) {
      const player = online.get(id);
      if (!player) { participant.disconnectedAt ??= now; continue; }
      participant.disconnectedAt = null;
      if (isInside(player.location, session.center)) participant.lastInsideAt = now;
    }
    if (session.phase >= 2) { session.lateDwell.clear(); return; }
    for (const player of online.values()) {
      if (session.participants.has(player.id) || !isInside(player.location, session.center)) { session.lateDwell.delete(player.id); continue; }
      const entered = session.lateDwell.get(player.id) ?? now; session.lateDwell.set(player.id, entered);
      if (now - entered >= THORN_COURT.lateJoinTicks && session.participants.size < THORN_COURT.participantCap) {
        session.participants.set(player.id, { kind: "approved_late_join", disconnectedAt: null, lastInsideAt: now });
        session.lateDwell.delete(player.id);
        codex.onPull(player);
      }
    }
  }

  function removeAdds(session) {
    for (const add of session.adds) if (isEntityAvailable(add)) add.remove?.();
    session.adds.clear();
  }

  function reset(session, reason = "reset") {
    removeAdds(session);
    if (isEntityAvailable(session.boss)) {
      setAttackTag(session.boss, null, null);
      session.boss.remove?.();
    }
    sessions.delete(session.id);
    const player = byId(session.initiator); if (player) state.warn(player, `Thorn Court ${reason.replaceAll("_", " ")}; the arena is unpulled.`);
    return true;
  }

  function spawnHowlAdds(session) {
    const phaseCap = THORN_COURT.phases[session.phase].addCap;
    session.adds = new Set([...session.adds].filter(isEntityAvailable));
    const count = Math.min(2, phaseCap - session.adds.size, THORN_COURT.globalAddCap - session.adds.size);
    for (let index = 0; index < count; index++) {
      try {
        const add = session.dimension.spawnEntity("aionbound:rot_wolf", {
          x: session.center.x + (index ? 3 : -3), y: session.center.y, z: session.center.z + 2,
        });
        addTag(add, THORN_COURT.addTag); add.setDynamicProperty?.(THORN_COURT.sessionProperty, session.id); session.adds.add(add);
      } catch { break; }
    }
  }

  function startAttack(session, id) {
    const spec = THORN_COURT.attacks[id], now = system.currentTick;
    session.attack = { id, stage: "telegraph", stageEnds: now + spec.telegraph };
    setAttackTag(session.boss, id, "telegraph");
  }

  function advanceAttack(session) {
    const current = session.attack; if (!current || system.currentTick < current.stageEnds) return;
    const spec = THORN_COURT.attacks[current.id];
    if (current.stage === "telegraph") {
      current.stage = "active"; current.stageEnds = system.currentTick + spec.active; setAttackTag(session.boss, current.id, "active");
      if (current.id === "howl_call") spawnHowlAdds(session);
      return;
    }
    if (current.stage === "active") {
      current.stage = "recovery"; current.stageEnds = system.currentTick + spec.recovery; setAttackTag(session.boss, current.id, "recovery"); return;
    }
    setAttackTag(session.boss, null, null); session.attack = null;
    session.nextAttackAt = system.currentTick + Math.max(THORN_COURT.globalAttackCooldownTicks, spec.cooldown ?? 0);
  }

  function scheduleAttack(session) {
    if (session.attack || system.currentTick < session.nextAttackAt) return;
    const rotation = ["lunge_barb", "thorn_fan", "root_snare", "silk_spit", "howl_call"];
    let id = rotation[session.attackCursor++ % rotation.length];
    if (id === "howl_call" && THORN_COURT.phases[session.phase].addCap === 0) id = "lunge_barb";
    startAttack(session, id);
  }

  function phaseAndAttacks(session) {
    const health = session.boss.getComponent?.("minecraft:health")?.currentValue ?? session.targetHealth;
    const next = thornCourtPhase(Math.max(0, health) / session.targetHealth, system.currentTick - session.pulledAt);
    if (next > session.phase) {
      session.phase = next; setPhaseTag(session.boss, THORN_COURT.phases[next].id);
      startAttack(session, "death_bloom_transition");
    }
    advanceAttack(session); scheduleAttack(session);
  }

  function resetChecks(session) {
    const now = system.currentTick, bossInside = isInside(session.boss.location ?? session.center, session.center);
    session.bossOutsideSince = bossInside ? null : (session.bossOutsideSince ?? now);
    if (session.bossOutsideSince !== null && now - session.bossOutsideSince >= THORN_COURT.bossLeashGraceTicks) return reset(session, "leash reset");

    const participants = [...session.participants.keys()].map(byId).filter(Boolean);
    session.noEligibleSince = participants.length ? null : (session.noEligibleSince ?? now);
    if (session.noEligibleSince !== null && now - session.noEligibleSince >= THORN_COURT.noEligibleGraceTicks) return reset(session, "no eligible player reset");

    const ready = participants.some(player => isInside(player.location, session.center) && isAlive(player));
    session.wipeSince = ready ? null : (session.wipeSince ?? now);
    if (session.wipeSince !== null && now - session.wipeSince >= THORN_COURT.wipeGraceTicks) return reset(session, "wipe reset");
    return false;
  }

  function tick() {
    if (system.currentTick % TICKS_PER_SECOND === 0) flushPendingEntitlements();
    for (const session of [...sessions.values()]) {
      if (session.status === "arming") {
        for (const player of sessionPlayers(session)) {
          if (isInside(player.location, session.center)) session.dwell.set(player.id, session.dwell.get(player.id) ?? system.currentTick);
          else session.dwell.delete(player.id);
        }
        if (system.currentTick >= session.pullAt) pull(session);
        continue;
      }
      if (!isEntityAvailable(session.boss)) { reset(session, "missing boss reset"); continue; }
      phaseAndAttacks(session);
      updatePresence(session);
      if (resetChecks(session)) continue;
    }
  }

  function isValidArenaDeath(event, session) {
    const entity = event.deadEntity, killer = event.damageSource?.damagingEntity;
    return session?.status === "active" && entity === session.boss && entity.typeId === THORN_COURT.bossType
      && entity.hasTag?.(THORN_COURT.apexTag) === true && entity.getDynamicProperty?.(THORN_COURT.sessionProperty) === session.id
      && killer?.typeId === "minecraft:player" && session.participants.has(killer.id);
  }

  function terminalEligibleIds(session) {
    const now = system.currentTick, online = new Map(sessionPlayers(session).map(player => [player.id, player]));
    return [...session.participants].filter(([id, participant]) => {
      const player = online.get(id);
      if (player) return isInside(player.location, session.center);
      return participant.disconnectedAt !== null && now - participant.disconnectedAt <= THORN_COURT.disconnectGraceTicks;
    }).map(([id]) => id);
  }

  function completeWorldStamp() {
    const w = state.worldState();
    if (w.encounters.terminal[THORN_COURT.worldCompletionKey]?.completed === true) return true;
    w.encounters.terminal[THORN_COURT.worldCompletionKey] = { completed: true, v: 1 };
    return state.saveWorld(w);
  }

  function bossDeath(event) {
    if (event.deadEntity?.typeId !== THORN_COURT.bossType) return false;
    const id = event.deadEntity.getDynamicProperty?.(THORN_COURT.sessionProperty), session = sessions.get(id);
    if (!isValidArenaDeath(event, session)) {
      if (session) reset(session, "invalid terminal reset");
      return false;
    }
    const eligibleIds = terminalEligibleIds(session);
    if (!eligibleIds.length) { reset(session, "no terminal participant reset"); return false; }
    if (!completeWorldStamp()) { reset(session, "completion persistence reset"); return false; }
    for (const playerId of eligibleIds) {
      const player = byId(playerId);
      if (!player) { queueOfflineEntitlement(playerId); continue; }
      const result = writeFirstCompletion(player);
      if (!result.saved) continue;
      codex.onTerminalCredit(player);
      hooks.grantMaterialPackage(player, { encounterId: THORN_COURT.id, repeatClear: !result.first });
      if (result.first) claimTrophy(player);
    }
    hooks.openArenaChest({ encounterId: THORN_COURT.id, dimension: session.dimension, center: session.center });
    removeAdds(session); sessions.delete(session.id);
    return true;
  }

  function reconcile() {
    // Active fights are intentionally absent from persistence. Only orphaned
    // tagged arena actors are removed after reload; ecology shells are untouched.
    for (const entity of boundedEntities()) {
      const id = entity.getDynamicProperty?.(THORN_COURT.sessionProperty);
      if (!id) continue;
      const session = sessions.get(id);
      if (!session || (entity.hasTag?.(THORN_COURT.apexTag) && entity !== session.boss)) entity.remove?.();
    }
    flushPendingEntitlements();
  }

  return Object.freeze({ begin, tick, bossDeath, reconcile, claimTrophy, recoverTrophy, flushPendingEntitlements, sessions, constants: THORN_COURT });
}
