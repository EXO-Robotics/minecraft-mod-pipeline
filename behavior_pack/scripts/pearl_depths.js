export const PEARL_DEPTHS = Object.freeze({
  id: "aionbound:pearl_depths",
  bossType: "aionbound:marsh_wight",
  bogWatcherType: "aionbound:bog_watcher",
  reedSerpentType: "aionbound:reed_serpent",
  apexTag: "aionbound.pearl_depths_apex",
  addTag: "aionbound.pearl_depths_add",
  trimmedAddTag: "aionbound.pearl_depths_trimmed",
  sessionProperty: "aionbound:pearl_depths_session",
  soloHealth: 520,
  participantScale: .30,
  participantCap: 4,
  pullResidencyTicks: 100,
  lateJoinResidencyTicks: 300,
  disconnectGraceTicks: 1200,
  bossOutsideTicks: 200,
  allDeadOrOutsideTicks: 300,
  noEligibleTicks: 600,
  hardEnrageTicks: 8400,
  globalAddCap: 4,
  globalAttackCooldownSeconds: 3.875,
  phases: Object.freeze([
    Object.freeze({ id: "fog_rise", enter: 1, exit: .70, addCap: 0, attacks: Object.freeze(["silt_grasp", "prism_lance"]) }),
    Object.freeze({ id: "choir_below", enter: .70, exit: .40, addCap: 3, attacks: Object.freeze(["silt_grasp", "prism_lance", "wail", "reed_serpent_call"]) }),
    Object.freeze({ id: "mask_unsealed", enter: .40, exit: .15, addCap: 4, attacks: Object.freeze(["prism_lance", "wail", "pearl_orbit", "drown_hymn"]) }),
    Object.freeze({ id: "flood_claim", enter: .15, exit: 0, addCap: 2, attacks: Object.freeze(["silt_grasp", "prism_lance", "pearl_orbit", "drown_hymn"]) }),
  ]),
  // Values are exact midpoints of the ratified closed intervals. No damage,
  // effect-radius, or invented arena-radius value is introduced here.
  attacks: Object.freeze({
    silt_grasp: Object.freeze({ telegraphSeconds: 1.4, activeSeconds: .8, recoverySeconds: 1.1, cooldownSeconds: 8.5 }),
    prism_lance: Object.freeze({ telegraphSeconds: 1.6, activeSeconds: 1, recoverySeconds: 1.2, cooldownSeconds: 10 }),
    wail: Object.freeze({ telegraphSeconds: 1.75, activeSeconds: 1.25, recoverySeconds: 1.4, cooldownSeconds: 14.5 }),
    reed_serpent_call: Object.freeze({ telegraphSeconds: 1.85, activeSeconds: .55, recoverySeconds: 1.3, cooldownSeconds: 22, spawnCount: 2 }),
    pearl_orbit: Object.freeze({ telegraphSeconds: 2, activeSeconds: 6, recoverySeconds: 1.55, cooldownSeconds: 18 }),
    drown_hymn: Object.freeze({ telegraphSeconds: 2.25, activeSeconds: 1.25, recoverySeconds: 1.75, cooldownSeconds: 0 }),
  }),
  worldCompletionKey: "aionbound.encounter.pearl_depths.completed.v1",
  sealCreditKey: "aionbound.player.pearl_depths.seal_credit.v1",
  entitlementKey: "aionbound.player.pearl_depths.reward_entitled.v1",
  maskClaimedKey: "aionbound.player.pearl_depths.mask_claimed.v1",
  maskItem: "aionbound:marsh_wight_mask",
  arenaForms: Object.freeze({
    sunken_shrine: Object.freeze({
      anchorType: "minecraft:lodestone",
      min: Object.freeze({ x: -8, y: -5, z: -8 }),
      max: Object.freeze({ x: 8, y: 5, z: 8 }),
      probes: Object.freeze([
        Object.freeze({ offset: Object.freeze({ x: 0, y: -1, z: 0 }), typeId: "aionbound:glass_root_block" }),
        Object.freeze({ offset: Object.freeze({ x: 5, y: -3, z: 0 }), typeId: "minecraft:lectern" }),
        Object.freeze({ offset: Object.freeze({ x: 5, y: 4, z: -5 }), typeId: "aionbound:prism_brick" }),
      ]),
    }),
    deep_pool_entrance: Object.freeze({
      anchorType: "minecraft:lodestone",
      min: Object.freeze({ x: -9, y: -1, z: -13 }),
      max: Object.freeze({ x: 9, y: 10, z: 5 }),
      probes: Object.freeze([
        Object.freeze({ offset: Object.freeze({ x: -4, y: 1, z: -3 }), typeId: "minecraft:barrel" }),
        Object.freeze({ offset: Object.freeze({ x: -3, y: 0, z: -3 }), typeId: "aionbound:algae_block" }),
        Object.freeze({ offset: Object.freeze({ x: 6, y: 1, z: 4 }), typeId: "aionbound:crystal_stone" }),
      ]),
    }),
  }),
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
function phaseTag(entity, id) { clearTagPrefix(entity, "aionbound.pearl_depths.phase."); addTag(entity, `aionbound.pearl_depths.phase.${id}`); }
function attackTag(entity, id, stage) {
  clearTagPrefix(entity, "aionbound.pearl_depths.attack.");
  if (id && stage) addTag(entity, `aionbound.pearl_depths.attack.${id}.${stage}`);
}

export function pearlDepthsHealth(participants) {
  const count = Math.max(1, Math.min(PEARL_DEPTHS.participantCap, Math.trunc(participants || 1)));
  return Math.round(PEARL_DEPTHS.soloHealth * (1 + PEARL_DEPTHS.participantScale * (count - 1)));
}

export function pearlDepthsPhase(healthFraction, elapsedTicks = 0) {
  if (elapsedTicks >= PEARL_DEPTHS.hardEnrageTicks || healthFraction <= .15) return 3;
  if (healthFraction <= .40) return 2;
  if (healthFraction <= .70) return 1;
  return 0;
}

function localDelta(worldDelta, rotationIndex) {
  return rotations(worldDelta)[(4 - rotationIndex) % 4];
}

function matchesArenaForm(block, form, rotationIndex) {
  if (block?.typeId !== form.anchorType || !block.dimension) return false;
  return form.probes.every(probe => {
    const rotated = rotations(probe.offset)[rotationIndex];
    return block.dimension.getBlock?.(at(block.location, rotated))?.typeId === probe.typeId;
  });
}

export function resolvePearlDepthsArena(block) {
  if (!block?.dimension || !block?.location || block.typeId !== "minecraft:lodestone") return null;
  const matches = [];
  for (const [formId, form] of Object.entries(PEARL_DEPTHS.arenaForms)) {
    for (let rotationIndex = 0; rotationIndex < 4; rotationIndex++) {
      if (!matchesArenaForm(block, form, rotationIndex)) continue;
      const contains = value => {
        if (dimensionId(value?.dimension) !== dimensionId(block.dimension)) return false;
        const local = localDelta({ x: value.x - block.location.x, y: value.y - block.location.y, z: value.z - block.location.z }, rotationIndex);
        return local.x >= form.min.x && local.x <= form.max.x
          && local.y >= form.min.y && local.y <= form.max.y
          && local.z >= form.min.z && local.z <= form.max.z;
      };
      matches.push(Object.freeze({
        id: `pearl_depths:${formId}:${dimensionId(block.dimension)}:${locationKey(block.location)}`,
        formId, dimension: block.dimension, dimensionId: dimensionId(block.dimension),
        anchor: { ...block.location }, rotationIndex, contains,
      }));
    }
  }
  return matches.length === 1 ? matches[0] : null;
}

export function createPearlDepthsService({ world, system, state, boundedEntities, resolveArena = resolvePearlDepthsArena, rewardHooks = {}, codexHooks = {}, arenaHooks = {} }) {
  const sessions = new Map();
  let sequence = 0, addSequence = 0;
  const hooks = Object.freeze({
    canDeliverMask: rewardHooks.canDeliverMask ?? (() => false),
    deliverMask: rewardHooks.deliverMask ?? (() => false),
    grantMaterialPackage: rewardHooks.grantMaterialPackage ?? (() => false),
    openArenaCache: rewardHooks.openArenaCache ?? (() => false),
  });
  const codex = Object.freeze({
    onPull: codexHooks.onPull ?? (() => false),
    onTerminalCredit: codexHooks.onTerminalCredit ?? (() => false),
  });
  const arenaState = Object.freeze({
    onPhase: arenaHooks.onPhase ?? (() => false),
    restore: arenaHooks.restore ?? (() => false),
  });
  const byId = id => world.getAllPlayers().find(player => player.id === id);
  const playersFor = session => world.getAllPlayers().filter(player => dimensionId(player.dimension) === session.dimensionId);
  const inside = (playerOrEntity, arena) => arena.contains({ ...playerOrEntity.location, dimension: playerOrEntity.dimension ?? arena.dimension });

  function readCredits(player) {
    const current = state.playerState(player);
    return { current, credits: { ...(current.credits ?? {}) } };
  }
  function writeFirstCredit(player) {
    const { current, credits } = readCredits(player), first = credits[PEARL_DEPTHS.sealCreditKey] !== true;
    const needsRepair = first || credits[PEARL_DEPTHS.entitlementKey] !== true;
    if (!needsRepair) return { saved: true, first: false };
    credits[PEARL_DEPTHS.sealCreditKey] = true;
    credits[PEARL_DEPTHS.entitlementKey] = true;
    const saved = state.savePlayer(player, { ...current, credits });
    return { saved, first: saved && first };
  }
  function claimMask(player) {
    const { current, credits } = readCredits(player);
    if (credits[PEARL_DEPTHS.sealCreditKey] !== true || credits[PEARL_DEPTHS.entitlementKey] !== true || credits[PEARL_DEPTHS.maskClaimedKey] === true) return false;
    // A full inventory leaves the entitlement recoverable and does not set the
    // at-most-once physical-fulfillment guard.
    if (hooks.canDeliverMask(player, PEARL_DEPTHS.maskItem) !== true) return false;
    credits[PEARL_DEPTHS.maskClaimedKey] = true;
    if (!state.savePlayer(player, { ...current, credits })) return false;
    // The guard is durable before the external item effect. An interruption
    // here cannot replay another physical mask; virtual seal credit survives.
    try { hooks.deliverMask(player, PEARL_DEPTHS.maskItem); } catch {}
    return true;
  }
  const recoverMask = player => claimMask(player);

  function queuePending(playerId) {
    const current = state.worldState(), pending = { ...(current.encounters.pendingPearlDepths ?? {}) };
    pending[playerId] = { sealCredit: true, entitlement: true, repeatRewards: true };
    current.encounters.pendingPearlDepths = pending;
    return state.saveWorld(current);
  }
  function flushPending() {
    const current = state.worldState(), pending = { ...(current.encounters.pendingPearlDepths ?? {}) };
    let changed = false;
    for (const player of world.getAllPlayers()) {
      if (!pending[player.id]) continue;
      const result = writeFirstCredit(player);
      if (!result.saved) continue;
      codex.onTerminalCredit(player);
      hooks.grantMaterialPackage(player, { encounterId: PEARL_DEPTHS.id, repeatClear: !result.first });
      if (result.first) claimMask(player);
      delete pending[player.id]; changed = true;
    }
    if (changed) { current.encounters.pendingPearlDepths = pending; state.saveWorld(current); }
    return changed;
  }

  function begin(player, arenaOrBlock) {
    const arena = arenaOrBlock?.contains ? arenaOrBlock : resolveArena(arenaOrBlock);
    if (!arena || !inside(player, arena) || [...sessions.values()].some(session => session.arena.id === arena.id)) return null;
    const id = `${arena.id}:${++sequence}`, now = system.currentTick;
    const session = {
      id, encounterId: PEARL_DEPTHS.id, status: "arming", initiator: player.id, arena,
      dimension: arena.dimension, dimensionId: arena.dimensionId, dwell: new Map(), scalingParticipants: new Map(),
      rewardParticipants: new Map(), lateDwell: new Map(), lateJoinClosed: false, adds: [], boss: null,
      phase: 0, attack: null, attackCursor: 0, globalReadyAt: 0, attackReadyAt: new Map(),
      bossOutsideSince: null, wipeSince: null, noEligibleSince: null, enraged: false,
    };
    for (const candidate of playersFor(session)) if (inside(candidate, arena) && isAlive(candidate)) session.dwell.set(candidate.id, now);
    sessions.set(id, session);
    return id;
  }

  function setBossHealth(boss, target) {
    const health = boss.getComponent?.("minecraft:health"), baseMax = health?.effectiveMax ?? health?.defaultValue ?? health?.maxValue ?? 80;
    const amplifier = Math.max(0, Math.ceil((target - baseMax) / 4) - 1);
    if (amplifier > 0) boss.addEffect?.("health_boost", 999999, { amplifier, showParticles: false });
    (boss.getComponent?.("minecraft:health") ?? health)?.setCurrentValue?.(target);
    boss.setDynamicProperty?.("aionbound:pearl_depths_target_health", target);
  }

  function pull(session) {
    const now = system.currentTick;
    const eligible = playersFor(session).filter(player => {
      const entered = session.dwell.get(player.id);
      return entered !== undefined && now - entered >= PEARL_DEPTHS.pullResidencyTicks && inside(player, session.arena) && isAlive(player);
    }).sort((a, b) => (session.dwell.get(a.id) - session.dwell.get(b.id)) || a.id.localeCompare(b.id)).slice(0, PEARL_DEPTHS.participantCap);
    if (!eligible.length) return false;
    let boss;
    try {
      boss = session.dimension.spawnEntity(PEARL_DEPTHS.bossType, session.arena.anchor);
      addTag(boss, PEARL_DEPTHS.apexTag);
      boss.setDynamicProperty?.(PEARL_DEPTHS.sessionProperty, session.id);
      for (const player of eligible) {
        session.scalingParticipants.set(player.id, Object.freeze({ admittedAt: now }));
        session.rewardParticipants.set(player.id, { admittedAt: now, disconnectedAt: null, diedDuringSession: false });
      }
      session.targetHealth = pearlDepthsHealth(eligible.length);
      setBossHealth(boss, session.targetHealth); phaseTag(boss, PEARL_DEPTHS.phases[0].id);
    } catch { boss?.remove?.(); sessions.delete(session.id); return false; }
    session.boss = boss; session.status = "active"; session.pulledAt = now;
    session.globalReadyAt = now + ticks(PEARL_DEPTHS.globalAttackCooldownSeconds);
    for (const player of eligible) codex.onPull(player);
    arenaState.onPhase(session.arena, PEARL_DEPTHS.phases[0].id);
    return true;
  }

  function updateArming(session) {
    const online = new Set(playersFor(session).map(player => player.id));
    for (const id of session.dwell.keys()) if (!online.has(id)) session.dwell.delete(id);
    for (const player of playersFor(session)) {
      if (inside(player, session.arena) && isAlive(player)) session.dwell.set(player.id, session.dwell.get(player.id) ?? system.currentTick);
      else session.dwell.delete(player.id);
    }
    if ([...session.dwell.values()].some(entered => system.currentTick - entered >= PEARL_DEPTHS.pullResidencyTicks)) pull(session);
  }

  function updatePresence(session) {
    const now = system.currentTick, online = new Map(playersFor(session).map(player => [player.id, player]));
    for (const id of session.lateDwell.keys()) if (!online.has(id)) session.lateDwell.delete(id);
    for (const [id, record] of session.rewardParticipants) {
      const player = online.get(id);
      if (!player) { record.disconnectedAt ??= now; continue; }
      record.disconnectedAt = null;
      if (!isAlive(player)) record.diedDuringSession = true;
    }
    if (session.phase >= 2) { session.lateJoinClosed = true; session.lateDwell.clear(); return; }
    const qualifiers = [];
    for (const player of online.values()) {
      if (session.rewardParticipants.has(player.id) || !inside(player, session.arena) || !isAlive(player)) { session.lateDwell.delete(player.id); continue; }
      const entered = session.lateDwell.get(player.id) ?? now; session.lateDwell.set(player.id, entered);
      if (now - entered >= PEARL_DEPTHS.lateJoinResidencyTicks) qualifiers.push(player);
    }
    qualifiers.sort((a, b) => a.id.localeCompare(b.id));
    for (const player of qualifiers) {
      if (session.rewardParticipants.size >= PEARL_DEPTHS.participantCap) break;
      session.rewardParticipants.set(player.id, { admittedAt: now, disconnectedAt: null, diedDuringSession: false, lateJoin: true });
      session.lateDwell.delete(player.id); codex.onPull(player);
    }
  }

  function liveAdds(session) { session.adds = session.adds.filter(row => isEntityAvailable(row.entity)); return session.adds; }
  function trimAdds(session) {
    const cap = Math.min(PEARL_DEPTHS.phases[session.phase].addCap, PEARL_DEPTHS.globalAddCap);
    const adds = liveAdds(session).sort((a, b) => a.sequence - b.sequence);
    while (adds.length > cap) {
      const row = adds.shift(); addTag(row.entity, PEARL_DEPTHS.trimmedAddTag); row.entity.remove?.();
    }
    session.adds = adds;
  }
  function spawnAdds(session, requested) {
    trimAdds(session);
    const cap = Math.min(PEARL_DEPTHS.phases[session.phase].addCap, PEARL_DEPTHS.globalAddCap);
    const accepted = Math.min(requested, Math.max(0, cap - session.adds.length));
    const addTypes = [PEARL_DEPTHS.reedSerpentType, PEARL_DEPTHS.bogWatcherType];
    for (let index = 0; index < accepted; index++) {
      try {
        const entity = session.dimension.spawnEntity(addTypes[(session.adds.length + index) % addTypes.length], session.boss.location ?? session.arena.anchor);
        addTag(entity, PEARL_DEPTHS.addTag); entity.setDynamicProperty?.(PEARL_DEPTHS.sessionProperty, session.id);
        session.adds.push({ entity, sequence: ++addSequence });
      } catch { break; }
    }
    return accepted;
  }

  function startAttack(session, id) {
    const spec = PEARL_DEPTHS.attacks[id];
    session.attack = { id, stage: "telegraph", stageEnds: system.currentTick + ticks(spec.telegraphSeconds) };
    attackTag(session.boss, id, "telegraph");
  }
  function advanceAttack(session) {
    const current = session.attack;
    if (!current || system.currentTick < current.stageEnds) return;
    const spec = PEARL_DEPTHS.attacks[current.id];
    if (current.stage === "telegraph") {
      current.stage = "active"; current.stageEnds = system.currentTick + ticks(spec.activeSeconds); attackTag(session.boss, current.id, "active");
      if (current.id === "reed_serpent_call") spawnAdds(session, spec.spawnCount);
      return;
    }
    if (current.stage === "active") {
      current.stage = "recovery"; current.stageEnds = system.currentTick + ticks(spec.recoverySeconds); attackTag(session.boss, current.id, "recovery"); return;
    }
    attackTag(session.boss, null, null); session.attack = null;
    session.globalReadyAt = system.currentTick + ticks(PEARL_DEPTHS.globalAttackCooldownSeconds);
    session.attackReadyAt.set(current.id, system.currentTick + ticks(spec.cooldownSeconds));
  }
  function scheduleAttack(session) {
    if (session.attack || system.currentTick < session.globalReadyAt) return;
    const available = PEARL_DEPTHS.phases[session.phase].attacks;
    for (let offset = 0; offset < available.length; offset++) {
      const index = (session.attackCursor + offset) % available.length, id = available[index];
      // Drown Hymn is a phase-transition action until Flood Claim, where the
      // ratified envelope additionally admits it to the ordinary rotation.
      if (id === "drown_hymn" && session.phase < 3) continue;
      if (system.currentTick < (session.attackReadyAt.get(id) ?? 0)) continue;
      session.attackCursor = index + 1; startAttack(session, id); return;
    }
  }
  function phaseAndAttacks(session) {
    const health = session.boss.getComponent?.("minecraft:health")?.currentValue ?? session.targetHealth;
    const next = pearlDepthsPhase(Math.max(0, health) / session.targetHealth, system.currentTick - session.pulledAt);
    if (next > session.phase) {
      session.phase = next; session.enraged ||= system.currentTick - session.pulledAt >= PEARL_DEPTHS.hardEnrageTicks;
      phaseTag(session.boss, PEARL_DEPTHS.phases[next].id); trimAdds(session); arenaState.onPhase(session.arena, PEARL_DEPTHS.phases[next].id);
      if (next >= 2) { session.lateJoinClosed = true; session.lateDwell.clear(); }
      startAttack(session, "drown_hymn");
    }
    advanceAttack(session); scheduleAttack(session);
  }

  function clearSessionActors(session) {
    for (const row of liveAdds(session)) { addTag(row.entity, PEARL_DEPTHS.trimmedAddTag); row.entity.remove?.(); }
    session.adds = [];
    if (isEntityAvailable(session.boss)) { attackTag(session.boss, null, null); session.boss.remove?.(); }
    arenaState.restore(session.arena);
  }
  function reset(session, reason = "reset") {
    clearSessionActors(session); sessions.delete(session.id);
    const initiator = byId(session.initiator);
    if (initiator) state.warn(initiator, `Pearl Depths ${reason.replaceAll("_", " ")}; the authored arena is restored and unpulled.`);
    return true;
  }
  function resetChecks(session) {
    const now = system.currentTick;
    session.bossOutsideSince = inside(session.boss, session.arena) ? null : (session.bossOutsideSince ?? now);
    if (session.bossOutsideSince !== null && now - session.bossOutsideSince >= PEARL_DEPTHS.bossOutsideTicks) return reset(session, "leash reset");
    const connected = [...session.rewardParticipants.keys()].map(byId).filter(Boolean);
    const allDeadOrOutside = connected.length > 0 && connected.every(player => !isAlive(player) || !inside(player, session.arena));
    session.wipeSince = allDeadOrOutside ? (session.wipeSince ?? now) : null;
    if (session.wipeSince !== null && now - session.wipeSince >= PEARL_DEPTHS.allDeadOrOutsideTicks) return reset(session, "wipe reset");
    const anyConnectedAliveInside = connected.some(player => isAlive(player) && inside(player, session.arena));
    session.noEligibleSince = anyConnectedAliveInside ? null : (session.noEligibleSince ?? now);
    if (session.noEligibleSince !== null && now - session.noEligibleSince >= PEARL_DEPTHS.noEligibleTicks) return reset(session, "no eligible player reset");
    return false;
  }

  function completeWorld() {
    const current = state.worldState();
    if (current.encounters.terminal[PEARL_DEPTHS.worldCompletionKey]?.completed === true) return true;
    current.encounters.terminal[PEARL_DEPTHS.worldCompletionKey] = { completed: true, v: 1 };
    return state.saveWorld(current);
  }
  function terminalEligibleIds(session) {
    const now = system.currentTick, online = new Map(playersFor(session).map(player => [player.id, player]));
    return [...session.rewardParticipants].filter(([id, record]) => {
      const player = online.get(id);
      if (player && isAlive(player) && inside(player, session.arena)) return true;
      if (player && !isAlive(player)) { record.diedDuringSession = true; return true; }
      if (record.diedDuringSession) return true;
      return !player && record.disconnectedAt !== null && now - record.disconnectedAt <= PEARL_DEPTHS.disconnectGraceTicks;
    }).map(([id]) => id);
  }
  function isValidDeath(event, session) {
    const entity = event.deadEntity;
    return session?.status === "active" && entity === session.boss && entity.typeId === PEARL_DEPTHS.bossType
      && entity.hasTag?.(PEARL_DEPTHS.apexTag) === true
      && entity.getDynamicProperty?.(PEARL_DEPTHS.sessionProperty) === session.id;
  }
  function bossDeath(event) {
    if (event.deadEntity?.typeId !== PEARL_DEPTHS.bossType) return false;
    const id = event.deadEntity.getDynamicProperty?.(PEARL_DEPTHS.sessionProperty), session = sessions.get(id);
    if (!isValidDeath(event, session)) return false;
    const eligibleIds = terminalEligibleIds(session);
    if (!eligibleIds.length) { reset(session, "no terminal participant reset"); return false; }
    if (!completeWorld()) { reset(session, "completion persistence reset"); return false; }
    for (const playerId of eligibleIds) {
      const player = byId(playerId);
      if (!player) { queuePending(playerId); continue; }
      const result = writeFirstCredit(player);
      if (!result.saved) continue;
      codex.onTerminalCredit(player);
      hooks.grantMaterialPackage(player, { encounterId: PEARL_DEPTHS.id, repeatClear: !result.first });
      if (result.first) claimMask(player);
    }
    hooks.openArenaCache({ encounterId: PEARL_DEPTHS.id, arena: session.arena, validClear: true });
    for (const row of liveAdds(session)) { addTag(row.entity, PEARL_DEPTHS.trimmedAddTag); row.entity.remove?.(); }
    arenaState.restore(session.arena); sessions.delete(session.id);
    return true;
  }

  function blockInteraction(player, block) {
    const arena = resolveArena(block);
    if (!arena) return false;
    const { credits } = readCredits(player);
    if (credits[PEARL_DEPTHS.entitlementKey] === true && credits[PEARL_DEPTHS.maskClaimedKey] !== true) {
      if (!recoverMask(player)) state.warn(player, "Pearl Depths mask recovery remains pending; make one inventory slot available.");
      return true;
    }
    begin(player, arena);
    return true;
  }

  function tick() {
    if (system.currentTick % TICKS_PER_SECOND === 0) flushPending();
    for (const session of [...sessions.values()]) {
      if (session.status === "arming") { updateArming(session); continue; }
      if (!isEntityAvailable(session.boss)) { reset(session, "missing boss reset"); continue; }
      updatePresence(session); phaseAndAttacks(session); resetChecks(session);
    }
  }
  function reconcile() {
    // Sessions and authored-arena transformations are memory-only. Tagged
    // orphans are removed; natural Marsh Wights are never touched.
    for (const entity of boundedEntities()) {
      const id = entity.getDynamicProperty?.(PEARL_DEPTHS.sessionProperty);
      if (!id) continue;
      const session = sessions.get(id);
      if (!session || (entity.hasTag?.(PEARL_DEPTHS.apexTag) && entity !== session.boss)) entity.remove?.();
    }
    flushPending();
  }

  return Object.freeze({ begin, blockInteraction, tick, bossDeath, reconcile, claimMask, recoverMask, flushPending, resolveArena, sessions, constants: PEARL_DEPTHS });
}
