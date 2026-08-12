export const STORM_NEST = Object.freeze({
  id: "aionbound:storm_nest",
  bossType: "aionbound:wind_roc",
  addTypes: Object.freeze(["aionbound:ruin_harpy", "aionbound:gale_hawk"]),
  apexTag: "aionbound.storm_nest_apex",
  addTag: "aionbound.storm_nest_add",
  trimmedAddTag: "aionbound.storm_nest_trimmed",
  sessionProperty: "aionbound:storm_nest_session",
  soloHealth: 560,
  participantScale: 0.30,
  participantCap: 4,
  pullResidencyTicks: 100,
  lateJoinResidencyTicks: 300,
  disconnectGraceTicks: 1200,
  bossOutsideTicks: 200,
  allDeadOrOutsideTicks: 300,
  noEligibleTicks: 600,
  voluntaryOutsideTicks: 200,
  globalAddCap: 4,
  globalAttackCooldownSeconds: 3.75,
  phases: Object.freeze([
    Object.freeze({ id: "nest_guard", enter: 1, exit: .70, addCap: 0, attacks: Object.freeze(["wing_buffet", "talon_pin"]) }),
    Object.freeze({ id: "wind_roads", enter: .70, exit: .40, addCap: 0, attacks: Object.freeze(["wing_buffet", "talon_pin", "gale_dive", "feather_knives"]) }),
    Object.freeze({ id: "harpy_dirge", enter: .40, exit: .15, addCap: 4, attacks: Object.freeze(["gale_dive", "feather_knives", "call_of_the_nest", "storm_screech"]) }),
    Object.freeze({ id: "storm_crown", enter: .15, exit: 0, addCap: 2, attacks: Object.freeze(["wing_buffet", "gale_dive", "feather_knives", "storm_screech"]) }),
  ]),
  // Every value is the exact midpoint of its W1-003 closed interval. Tick
  // conversion is rounded only at the final scheduler boundary.
  attacks: Object.freeze({
    wing_buffet: Object.freeze({ telegraphSeconds: 1.3, activeSeconds: .7, recoverySeconds: 1.1, cooldownSeconds: 8.5 }),
    talon_pin: Object.freeze({ telegraphSeconds: 1.65, activeSeconds: .9, recoverySeconds: 1.4, cooldownSeconds: 13 }),
    gale_dive: Object.freeze({ telegraphSeconds: 2.1, activeSeconds: 1.05, recoverySeconds: 1.65, cooldownSeconds: 15.5 }),
    feather_knives: Object.freeze({ telegraphSeconds: 1.55, activeSeconds: 1.25, recoverySeconds: 1.2, cooldownSeconds: 11 }),
    call_of_the_nest: Object.freeze({ telegraphSeconds: 2.1, activeSeconds: .65, recoverySeconds: 1.55, cooldownSeconds: 23.5, spawnCount: 2 }),
    storm_screech: Object.freeze({ telegraphSeconds: 1.95, activeSeconds: 1, recoverySeconds: 1.55, cooldownSeconds: 16.5 }),
  }),
  worldCompletionKey: "aionbound.encounter.storm_nest.completed.v1",
  sealCreditKey: "aionbound.player.storm_nest.seal_credit.v1",
  entitlementKey: "aionbound.player.storm_nest.reward_entitled.v1",
  pinionClaimedKey: "aionbound.player.storm_nest.pinion_claimed.v1",
  pinionItem: "aionbound:storm_pinion",
  hardEnrageTicks: 8400,
  authoredVolume: Object.freeze({ min: Object.freeze({ x: -11, y: -3, z: -11 }), max: Object.freeze({ x: 11, y: 3, z: 11 }) }),
});

const TICKS_PER_SECOND = 20;
const ticks = seconds => Math.round(seconds * TICKS_PER_SECOND);
const dimensionId = value => value?.id ?? "minecraft:overworld";
const isEntityAvailable = entity => entity && entity.removed !== true && entity.isValid !== false;
const isAlive = player => (player.getComponent?.("minecraft:health")?.currentValue ?? 1) > 0;
const at = (origin, offset) => ({ x: origin.x + offset.x, y: origin.y + offset.y, z: origin.z + offset.z });
const locationKey = value => `${Math.floor(value.x)},${Math.floor(value.y)},${Math.floor(value.z)}`;
const rotations = ({ x, y, z }) => [{ x, y, z }, { x: z, y, z: -x }, { x: -x, y, z: -z }, { x: -z, y, z: x }];

function addTag(entity, tag) { if (!entity.hasTag?.(tag)) entity.addTag?.(tag); }
function clearTagPrefix(entity, prefix) { for (const tag of entity.getTags?.() ?? []) if (tag.startsWith(prefix)) entity.removeTag?.(tag); }
function phaseTag(entity, id) { clearTagPrefix(entity, "aionbound.storm_nest.phase."); addTag(entity, `aionbound.storm_nest.phase.${id}`); }
function attackTag(entity, id, stage) {
  clearTagPrefix(entity, "aionbound.storm_nest.attack.");
  if (id && stage) addTag(entity, `aionbound.storm_nest.attack.${id}.${stage}`);
}

export function stormNestHealth(participants) {
  const count = Math.max(1, Math.min(STORM_NEST.participantCap, Math.trunc(participants || 1)));
  return Math.round(STORM_NEST.soloHealth * (1 + STORM_NEST.participantScale * (count - 1)));
}

export function stormNestPhase(healthFraction) {
  if (healthFraction <= .15) return 3;
  if (healthFraction <= .40) return 2;
  if (healthFraction <= .70) return 1;
  return 0;
}

function blockAt(dimension, location) { return dimension?.getBlock?.(location); }
function matchesNestAnchor(block) {
  if (block?.typeId !== "aionbound:sky_moss_block") return false;
  const expected = [
    [{ x: 0, y: -1, z: 0 }, "aionbound:cloud_wool_block"],
    [{ x: 0, y: -2, z: 0 }, "aionbound:rope_timber"],
    [{ x: 0, y: -3, z: 0 }, "aionbound:cliff_stone"],
    [{ x: 8, y: 0, z: 0 }, "aionbound:rope_timber"],
    [{ x: -8, y: 0, z: 0 }, "aionbound:rope_timber"],
    [{ x: 0, y: 0, z: 8 }, "aionbound:rope_timber"],
    [{ x: 0, y: 0, z: -8 }, "aionbound:rope_timber"],
  ];
  return expected.every(([offset, typeId]) => blockAt(block.dimension, at(block.location, offset))?.typeId === typeId);
}

export function resolveStormNestArena(block) {
  if (!block?.dimension || !block?.location) return null;
  const candidates = [block];
  for (const offset of [{ x: 0, y: 0, z: 0 }, { x: 8, y: 0, z: 0 }, { x: -8, y: 0, z: 0 }, { x: 0, y: 0, z: 8 }, { x: 0, y: 0, z: -8 }]) {
    const anchor = blockAt(block.dimension, at(block.location, { x: -offset.x, y: -offset.y, z: -offset.z }));
    if (anchor && !candidates.includes(anchor)) candidates.push(anchor);
  }
  for (const anchor of candidates) {
      if (!matchesNestAnchor(anchor)) continue;
      const contains = location => dimensionId(location?.dimension) === dimensionId(anchor.dimension)
        && location.x >= anchor.location.x + STORM_NEST.authoredVolume.min.x && location.x <= anchor.location.x + STORM_NEST.authoredVolume.max.x
        && location.y >= anchor.location.y + STORM_NEST.authoredVolume.min.y && location.y <= anchor.location.y + STORM_NEST.authoredVolume.max.y
        && location.z >= anchor.location.z + STORM_NEST.authoredVolume.min.z && location.z <= anchor.location.z + STORM_NEST.authoredVolume.max.z;
      return Object.freeze({ id: `storm_nest:${dimensionId(anchor.dimension)}:${locationKey(anchor.location)}`, formId: "nest_platform", dimension: anchor.dimension, dimensionId: dimensionId(anchor.dimension), anchor: { ...anchor.location }, claimLocation: { ...anchor.location }, contains });
  }
  return null;
}

export function createStormNestService({ world, system, state, boundedEntities, resolveArena = resolveStormNestArena, rewardHooks = {}, codexHooks = {} }) {
  const sessions = new Map();
  let sequence = 0, addSequence = 0;
  const hooks = Object.freeze({
    canDeliverPinion: rewardHooks.canDeliverPinion ?? (() => false),
    deliverPinion: rewardHooks.deliverPinion ?? (() => false),
    grantMaterialPackage: rewardHooks.grantMaterialPackage ?? (() => false),
    openArenaCache: rewardHooks.openArenaCache ?? (() => false),
  });
  const codex = Object.freeze({ onPull: codexHooks.onPull ?? (() => false), onTerminalCredit: codexHooks.onTerminalCredit ?? (() => false) });
  const byId = id => world.getAllPlayers().find(player => player.id === id);
  const playersFor = session => world.getAllPlayers().filter(player => dimensionId(player.dimension) === session.dimensionId);
  const inside = (playerOrEntity, arena) => arena.contains({ ...playerOrEntity.location, dimension: playerOrEntity.dimension ?? arena.dimension });

  function readCredits(player) { const current = state.playerState(player); return { current, credits: { ...(current.credits ?? {}) } }; }
  function writeFirstCredit(player) {
    const { current, credits } = readCredits(player), first = credits[STORM_NEST.sealCreditKey] !== true;
    const needsRepair = first || credits[STORM_NEST.entitlementKey] !== true;
    if (!needsRepair) return { saved: true, first: false };
    credits[STORM_NEST.sealCreditKey] = true;
    credits[STORM_NEST.entitlementKey] = true;
    const saved = state.savePlayer(player, { ...current, credits });
    return { saved, first: saved && first };
  }
  function claimPinion(player) {
    const { current, credits } = readCredits(player);
    if (credits[STORM_NEST.sealCreditKey] !== true || credits[STORM_NEST.entitlementKey] !== true || credits[STORM_NEST.pinionClaimedKey] === true) return false;
    if (hooks.canDeliverPinion(player) !== true) return false;
    credits[STORM_NEST.pinionClaimedKey] = true;
    if (!state.savePlayer(player, { ...current, credits })) return false;
    try { hooks.deliverPinion(player, STORM_NEST.pinionItem); } catch {}
    return true;
  }
  const recoverPinion = player => claimPinion(player);

  function queuePending(playerId) {
    const w = state.worldState(), pending = { ...(w.encounters.pendingStormNest ?? {}) };
    pending[playerId] = { sealCredit: true, entitlement: true, repeatRewards: true };
    w.encounters.pendingStormNest = pending; return state.saveWorld(w);
  }
  function flushPending() {
    const w = state.worldState(), pending = { ...(w.encounters.pendingStormNest ?? {}) };
    let changed = false;
    for (const player of world.getAllPlayers()) {
      if (!pending[player.id]) continue;
      const result = writeFirstCredit(player); if (!result.saved) continue;
      codex.onTerminalCredit(player); hooks.grantMaterialPackage(player, { encounterId: STORM_NEST.id, repeatClear: !result.first });
      if (result.first) claimPinion(player);
      delete pending[player.id]; changed = true;
    }
    if (changed) { w.encounters.pendingStormNest = pending; state.saveWorld(w); }
    return changed;
  }

  function begin(player, arenaOrBlock) {
    const arena = arenaOrBlock?.contains ? arenaOrBlock : resolveArena(arenaOrBlock);
    if (!arena || !inside(player, arena) || [...sessions.values()].some(session => session.arena.id === arena.id)) return null;
    const id = `${arena.id}:${++sequence}`, now = system.currentTick;
    const session = { id, status: "arming", initiator: player.id, arena, dimension: arena.dimension, dimensionId: arena.dimensionId, dwell: new Map(), scalingParticipants: new Map(), rewardParticipants: new Map(), lateDwell: new Map(), lateJoinClosed: false, adds: [], boss: null, phase: 0, attack: null, attackCursor: 0, globalReadyAt: 0, attackReadyAt: new Map(), bossOutsideSince: null, wipeSince: null, noEligibleSince: null };
    for (const candidate of playersFor(session)) if (inside(candidate, arena) && isAlive(candidate)) session.dwell.set(candidate.id, now);
    sessions.set(id, session); return id;
  }

  function setBossHealth(boss, target) {
    const health = boss.getComponent?.("minecraft:health"), baseMax = health?.effectiveMax ?? health?.defaultValue ?? health?.maxValue ?? 80;
    const amplifier = Math.max(0, Math.ceil((target - baseMax) / 4) - 1);
    if (amplifier > 0) boss.addEffect?.("health_boost", 999999, { amplifier, showParticles: false });
    (boss.getComponent?.("minecraft:health") ?? health)?.setCurrentValue?.(target);
    boss.setDynamicProperty?.("aionbound:storm_nest_target_health", target);
  }

  function pull(session) {
    const now = system.currentTick;
    const eligible = playersFor(session).filter(player => {
      const entered = session.dwell.get(player.id);
      return entered !== undefined && now - entered >= STORM_NEST.pullResidencyTicks && inside(player, session.arena) && isAlive(player);
    });
    if (!eligible.some(player => player.id === session.initiator)) { sessions.delete(session.id); return false; }
    eligible.sort((a, b) => a.id === session.initiator ? -1 : b.id === session.initiator ? 1 : (session.dwell.get(a.id) - session.dwell.get(b.id)) || a.id.localeCompare(b.id));
    const selected = eligible.slice(0, STORM_NEST.participantCap);
    let boss;
    try {
      boss = session.dimension.spawnEntity(STORM_NEST.bossType, session.arena.anchor);
      addTag(boss, STORM_NEST.apexTag); boss.setDynamicProperty?.(STORM_NEST.sessionProperty, session.id);
      for (const player of selected) {
        const record = { admittedAt: now, disconnectedAt: null, outsideSince: null, diedDuringSession: false };
        session.scalingParticipants.set(player.id, Object.freeze({ admittedAt: now }));
        session.rewardParticipants.set(player.id, record);
      }
      session.targetHealth = stormNestHealth(selected.length); setBossHealth(boss, session.targetHealth); phaseTag(boss, STORM_NEST.phases[0].id);
    } catch { boss?.remove?.(); sessions.delete(session.id); return false; }
    session.boss = boss; session.status = "active"; session.pulledAt = now; session.globalReadyAt = now + ticks(STORM_NEST.globalAttackCooldownSeconds);
    for (const player of selected) codex.onPull(player);
    return true;
  }

  function updateArming(session) {
    const present = new Set(playersFor(session).map(player => player.id));
    for (const id of session.dwell.keys()) if (!present.has(id)) session.dwell.delete(id);
    for (const player of playersFor(session)) {
      if (inside(player, session.arena) && isAlive(player)) session.dwell.set(player.id, session.dwell.get(player.id) ?? system.currentTick);
      else session.dwell.delete(player.id);
    }
    const initiatorDwell = session.dwell.get(session.initiator);
    if (initiatorDwell !== undefined && system.currentTick - initiatorDwell >= STORM_NEST.pullResidencyTicks) pull(session);
  }

  function updatePresence(session) {
    const now = system.currentTick, online = new Map(playersFor(session).map(player => [player.id, player]));
    for (const id of session.lateDwell.keys()) if (!online.has(id)) session.lateDwell.delete(id);
    for (const [id, record] of [...session.rewardParticipants]) {
      const player = online.get(id);
      if (!player) { record.disconnectedAt ??= now; record.outsideSince = null; continue; }
      record.disconnectedAt = null;
      if (!isAlive(player)) { record.diedDuringSession = true; record.outsideSince = null; continue; }
      if (inside(player, session.arena)) record.outsideSince = null;
      else {
        record.outsideSince ??= now;
        if (now - record.outsideSince >= STORM_NEST.voluntaryOutsideTicks) session.rewardParticipants.delete(id);
      }
    }
    if (session.phase >= 2) { session.lateJoinClosed = true; session.lateDwell.clear(); return; }
    const qualifiers = [];
    for (const player of online.values()) {
      if (session.rewardParticipants.has(player.id) || !inside(player, session.arena) || !isAlive(player)) { session.lateDwell.delete(player.id); continue; }
      const entered = session.lateDwell.get(player.id) ?? now; session.lateDwell.set(player.id, entered);
      if (now - entered >= STORM_NEST.lateJoinResidencyTicks) qualifiers.push(player);
    }
    qualifiers.sort((a, b) => a.id.localeCompare(b.id));
    for (const player of qualifiers) {
      if (session.rewardParticipants.size >= STORM_NEST.participantCap) break;
      session.rewardParticipants.set(player.id, { admittedAt: now, disconnectedAt: null, outsideSince: null, diedDuringSession: false, lateJoin: true });
      session.lateDwell.delete(player.id); codex.onPull(player);
    }
  }

  function liveAdds(session) { session.adds = session.adds.filter(row => isEntityAvailable(row.entity)); return session.adds; }
  function trimAdds(session) {
    const cap = Math.min(STORM_NEST.phases[session.phase].addCap, STORM_NEST.globalAddCap), adds = liveAdds(session).sort((a, b) => a.sequence - b.sequence);
    while (adds.length > cap) { const row = adds.shift(); addTag(row.entity, STORM_NEST.trimmedAddTag); row.entity.remove?.(); }
    session.adds = adds;
  }
  function spawnAdds(session, requested) {
    trimAdds(session);
    const cap = Math.min(STORM_NEST.phases[session.phase].addCap, STORM_NEST.globalAddCap), accepted = Math.min(requested, Math.max(0, cap - session.adds.length));
    for (let index = 0; index < accepted; index++) {
      try {
        const typeId = STORM_NEST.addTypes[addSequence % STORM_NEST.addTypes.length];
        const add = session.dimension.spawnEntity(typeId, session.boss.location ?? session.arena.anchor);
        addTag(add, STORM_NEST.addTag); add.setDynamicProperty?.(STORM_NEST.sessionProperty, session.id);
        session.adds.push({ entity: add, sequence: ++addSequence });
      } catch { break; }
    }
    return accepted;
  }

  function startAttack(session, id) {
    const spec = STORM_NEST.attacks[id];
    session.attack = { id, stage: "telegraph", stageEnds: system.currentTick + ticks(spec.telegraphSeconds) };
    attackTag(session.boss, id, "telegraph");
  }
  function advanceAttack(session) {
    const current = session.attack; if (!current || system.currentTick < current.stageEnds) return;
    const spec = STORM_NEST.attacks[current.id];
    if (current.stage === "telegraph") {
      current.stage = "active"; current.stageEnds = system.currentTick + ticks(spec.activeSeconds); attackTag(session.boss, current.id, "active");
      if (current.id === "call_of_the_nest") spawnAdds(session, spec.spawnCount); return;
    }
    if (current.stage === "active") { current.stage = "recovery"; current.stageEnds = system.currentTick + ticks(spec.recoverySeconds); attackTag(session.boss, current.id, "recovery"); return; }
    attackTag(session.boss, null, null); session.attack = null;
    session.globalReadyAt = system.currentTick + ticks(STORM_NEST.globalAttackCooldownSeconds);
    session.attackReadyAt.set(current.id, system.currentTick + ticks(spec.cooldownSeconds));
  }
  function scheduleAttack(session) {
    if (session.attack || system.currentTick < session.globalReadyAt) return;
    const available = STORM_NEST.phases[session.phase].attacks;
    for (let offset = 0; offset < available.length; offset++) {
      const index = (session.attackCursor + offset) % available.length, id = available[index];
      if (system.currentTick < (session.attackReadyAt.get(id) ?? 0)) continue;
      session.attackCursor = index + 1; startAttack(session, id); return;
    }
  }
  function phaseAndAttacks(session) {
    const health = session.boss.getComponent?.("minecraft:health")?.currentValue ?? session.targetHealth;
    const next = stormNestPhase(Math.max(0, health) / session.targetHealth);
    const enraged = system.currentTick - session.pulledAt >= STORM_NEST.hardEnrageTicks;
    const targetPhase = enraged ? 3 : next;
    if (targetPhase > session.phase) {
      session.phase = targetPhase; phaseTag(session.boss, STORM_NEST.phases[targetPhase].id); trimAdds(session);
      if (targetPhase >= 2) { session.lateJoinClosed = true; session.lateDwell.clear(); }
    }
    advanceAttack(session); scheduleAttack(session);
  }

  function clearSessionActors(session) {
    for (const row of liveAdds(session)) { addTag(row.entity, STORM_NEST.trimmedAddTag); row.entity.remove?.(); }
    session.adds = [];
    if (isEntityAvailable(session.boss)) { attackTag(session.boss, null, null); session.boss.remove?.(); }
  }
  function reset(session, reason = "reset") {
    clearSessionActors(session); sessions.delete(session.id);
    const initiator = byId(session.initiator); if (initiator) state.warn(initiator, `Storm Nest ${reason.replaceAll("_", " ")}; the nest is unpulled.`);
    return true;
  }
  function resetChecks(session) {
    const now = system.currentTick;
    session.bossOutsideSince = inside(session.boss, session.arena) ? null : (session.bossOutsideSince ?? now);
    if (session.bossOutsideSince !== null && now - session.bossOutsideSince >= STORM_NEST.bossOutsideTicks) return reset(session, "leash reset");
    const connected = [...session.rewardParticipants.keys()].map(byId).filter(Boolean);
    const allDeadOrOutside = connected.length > 0 && connected.every(player => !isAlive(player) || !inside(player, session.arena));
    session.wipeSince = allDeadOrOutside ? (session.wipeSince ?? now) : null;
    if (session.wipeSince !== null && now - session.wipeSince >= STORM_NEST.allDeadOrOutsideTicks) return reset(session, "wipe reset");
    const anyConnectedAliveInside = connected.some(player => isAlive(player) && inside(player, session.arena));
    session.noEligibleSince = anyConnectedAliveInside ? null : (session.noEligibleSince ?? now);
    if (session.noEligibleSince !== null && now - session.noEligibleSince >= STORM_NEST.noEligibleTicks) return reset(session, "no eligible player reset");
    return false;
  }

  function completeWorld() {
    const w = state.worldState();
    if (w.encounters.terminal[STORM_NEST.worldCompletionKey]?.completed === true) return true;
    w.encounters.terminal[STORM_NEST.worldCompletionKey] = { completed: true, v: 1 };
    return state.saveWorld(w);
  }
  function terminalEligibleIds(session) {
    const now = system.currentTick, online = new Map(playersFor(session).map(player => [player.id, player]));
    return [...session.rewardParticipants].filter(([id, record]) => {
      const player = online.get(id);
      if (player && isAlive(player) && inside(player, session.arena)) return true;
      if (player && !isAlive(player)) { record.diedDuringSession = true; return true; }
      if (record.diedDuringSession) return true;
      return !player && record.disconnectedAt !== null && now - record.disconnectedAt <= STORM_NEST.disconnectGraceTicks;
    }).map(([id]) => id);
  }
  function isValidDeath(event, session) {
    const entity = event.deadEntity;
    return session?.status === "active" && entity === session.boss && entity.typeId === STORM_NEST.bossType
      && entity.hasTag?.(STORM_NEST.apexTag) === true && entity.getDynamicProperty?.(STORM_NEST.sessionProperty) === session.id;
  }
  function bossDeath(event) {
    if (event.deadEntity?.typeId !== STORM_NEST.bossType) return false;
    const id = event.deadEntity.getDynamicProperty?.(STORM_NEST.sessionProperty), session = sessions.get(id);
    if (!isValidDeath(event, session)) return false;
    const eligibleIds = terminalEligibleIds(session); if (!eligibleIds.length) { reset(session, "no terminal participant reset"); return false; }
    if (!completeWorld()) { reset(session, "completion persistence reset"); return false; }
    for (const playerId of eligibleIds) {
      const player = byId(playerId);
      if (!player) { queuePending(playerId); continue; }
      const result = writeFirstCredit(player); if (!result.saved) continue;
      codex.onTerminalCredit(player); hooks.grantMaterialPackage(player, { encounterId: STORM_NEST.id, repeatClear: !result.first });
      if (result.first) claimPinion(player);
    }
    hooks.openArenaCache({ encounterId: STORM_NEST.id, arena: session.arena });
    // Terminal completion wins over every pending reset clock.
    for (const row of liveAdds(session)) { addTag(row.entity, STORM_NEST.trimmedAddTag); row.entity.remove?.(); }
    sessions.delete(session.id); return true;
  }

  function tick() {
    if (system.currentTick % TICKS_PER_SECOND === 0) flushPending();
    for (const session of [...sessions.values()]) {
      if (session.status === "arming") { updateArming(session); continue; }
      if (!isEntityAvailable(session.boss)) { reset(session, "missing boss reset"); continue; }
      updatePresence(session); phaseAndAttacks(session); if (resetChecks(session)) continue;
    }
  }
  function reconcile() {
    // Active fights are intentionally memory-only. Tagged orphans are removed;
    // untagged ecology Ash Drakes remain untouched and cannot complete.
    for (const entity of boundedEntities()) {
      const id = entity.getDynamicProperty?.(STORM_NEST.sessionProperty);
      if (!id) continue;
      const session = sessions.get(id);
      if (!session || (entity.hasTag?.(STORM_NEST.apexTag) && entity !== session.boss)) entity.remove?.();
    }
    flushPending();
  }

  function blockInteraction(player, block) {
    const arena = resolveArena(block);
    if (!arena) return false;
    const { credits } = readCredits(player);
    if (credits[STORM_NEST.entitlementKey] === true && credits[STORM_NEST.pinionClaimedKey] !== true) {
      // Recovery entitlement owns this interaction even when inventory is full;
      // it must never fall through into a new pull.
      claimPinion(player);
      return true;
    }
    begin(player, arena);
    return true;
  }

  return Object.freeze({ begin, tick, bossDeath, reconcile, blockInteraction, claimPinion, recoverPinion, flushPending, resolveArena, sessions, constants: STORM_NEST });
}
