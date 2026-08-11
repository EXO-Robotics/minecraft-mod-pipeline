export const KILN_SKY = Object.freeze({
  id: "aionbound:kiln_sky",
  bossType: "aionbound:ash_drake",
  miteType: "aionbound:ash_mite",
  apexTag: "aionbound.kiln_sky_apex",
  miteTag: "aionbound.kiln_sky_mite",
  trimmedMiteTag: "aionbound.kiln_sky_trimmed",
  sessionProperty: "aionbound:kiln_sky_session",
  soloHealth: 480,
  participantScale: 0.30,
  participantCap: 4,
  pullResidencyTicks: 100,
  lateJoinResidencyTicks: 300,
  disconnectGraceTicks: 1200,
  bossOutsideTicks: 200,
  allDeadOrOutsideTicks: 300,
  noEligibleTicks: 600,
  voluntaryOutsideTicks: 200,
  globalMiteCap: 4,
  globalAttackCooldownSeconds: 3.625,
  phases: Object.freeze([
    Object.freeze({ id: "ash_landing", enter: 1, exit: .70, miteCap: 0, attacks: Object.freeze(["cinder_breath", "tail_slag"]) }),
    Object.freeze({ id: "vent_choir", enter: .70, exit: .40, miteCap: 4, attacks: Object.freeze(["cinder_breath", "tail_slag", "thermal_dive", "mite_shake"]) }),
    Object.freeze({ id: "glass_wing", enter: .40, exit: .15, miteCap: 4, attacks: Object.freeze(["cinder_breath", "thermal_dive", "basalt_quake", "glass_feather_storm", "mite_shake"]) }),
    Object.freeze({ id: "kiln_heart", enter: .15, exit: 0, miteCap: 2, attacks: Object.freeze(["cinder_breath", "tail_slag", "thermal_dive", "basalt_quake", "glass_feather_storm"]) }),
  ]),
  // Every value is the exact midpoint of its W1-003 closed interval. Tick
  // conversion is rounded only at the final scheduler boundary.
  attacks: Object.freeze({
    cinder_breath: Object.freeze({ telegraphSeconds: 1.15, activeSeconds: 1.5, recoverySeconds: 1.05, cooldownSeconds: 8.5 }),
    tail_slag: Object.freeze({ telegraphSeconds: .85, activeSeconds: .35, recoverySeconds: .95, cooldownSeconds: 6.5 }),
    thermal_dive: Object.freeze({ telegraphSeconds: 1.6, activeSeconds: .8, recoverySeconds: 1.55, cooldownSeconds: 12 }),
    mite_shake: Object.freeze({ telegraphSeconds: 1.5, activeSeconds: .4, recoverySeconds: 1.2, cooldownSeconds: 21, spawnCount: 2 }),
    basalt_quake: Object.freeze({ telegraphSeconds: 1.5, activeSeconds: .45, recoverySeconds: 1.2, cooldownSeconds: 12 }),
    glass_feather_storm: Object.freeze({ telegraphSeconds: 1.8, activeSeconds: 5, recoverySeconds: 1.55, cooldownSeconds: 17 }),
  }),
  worldCompletionKey: "aionbound.encounter.kiln_sky.completed.v1",
  sealCreditKey: "aionbound.player.kiln_sky.seal_credit.v1",
  entitlementKey: "aionbound.player.kiln_sky.reward_entitled.v1",
  hornClaimedKey: "aionbound.player.kiln_sky.trophy_claimed.v1",
  hornItem: "aionbound:ash_drake_horn",
  optionalMasteryItem: "aionbound:ember_forge_core",
  optionalMasteryChance: .14,
  authoredVolume: Object.freeze({ min: Object.freeze({ x: -11, y: -3, z: -11 }), max: Object.freeze({ x: 11, y: 10, z: 11 }) }),
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
function phaseTag(entity, id) { clearTagPrefix(entity, "aionbound.kiln_sky.phase."); addTag(entity, `aionbound.kiln_sky.phase.${id}`); }
function attackTag(entity, id, stage) {
  clearTagPrefix(entity, "aionbound.kiln_sky.attack.");
  if (id && stage) addTag(entity, `aionbound.kiln_sky.attack.${id}.${stage}`);
}

export function kilnSkyHealth(participants) {
  const count = Math.max(1, Math.min(KILN_SKY.participantCap, Math.trunc(participants || 1)));
  return Math.round(KILN_SKY.soloHealth * (1 + KILN_SKY.participantScale * (count - 1)));
}

export function kilnSkyPhase(healthFraction) {
  if (healthFraction <= .15) return 3;
  if (healthFraction <= .40) return 2;
  if (healthFraction <= .70) return 1;
  return 0;
}

function blockAt(dimension, location) { return dimension?.getBlock?.(location); }
function matchesForgeAnchor(block, rotation) {
  if (block?.typeId !== "minecraft:lodestone") return false;
  const expected = [
    [{ x: 6, y: 0, z: 0 }, "minecraft:barrel"],
    [{ x: -6, y: 0, z: 0 }, "minecraft:lectern"],
    [{ x: 0, y: 0, z: -6 }, "aionbound:ash_log"],
    [{ x: 0, y: 0, z: 6 }, "aionbound:ash_log"],
    [{ x: 0, y: -1, z: 0 }, "minecraft:magma_block"],
  ];
  return expected.every(([offset, typeId]) => blockAt(block.dimension, at(block.location, rotation(offset)))?.typeId === typeId);
}

export function resolveKilnSkyArena(block) {
  if (!block?.dimension || !block?.location) return null;
  const candidates = [];
  if (block.typeId === "minecraft:lodestone") candidates.push(block);
  if (block.typeId === "minecraft:barrel") {
    for (const offset of rotations({ x: 6, y: 0, z: 0 })) {
      const anchor = blockAt(block.dimension, at(block.location, { x: -offset.x, y: -offset.y, z: -offset.z }));
      if (anchor) candidates.push(anchor);
    }
  }
  for (const anchor of candidates) {
    for (const rotate of [0, 1, 2, 3]) {
      const rotation = offset => rotations(offset)[rotate];
      if (!matchesForgeAnchor(anchor, rotation)) continue;
      const cacheLocation = at(anchor.location, rotation({ x: 6, y: 0, z: 0 }));
      const recordLocation = at(anchor.location, rotation({ x: -6, y: 0, z: 0 }));
      const contains = location => dimensionId(location?.dimension) === dimensionId(anchor.dimension)
        && location.x >= anchor.location.x + KILN_SKY.authoredVolume.min.x && location.x <= anchor.location.x + KILN_SKY.authoredVolume.max.x
        && location.y >= anchor.location.y + KILN_SKY.authoredVolume.min.y && location.y <= anchor.location.y + KILN_SKY.authoredVolume.max.y
        && location.z >= anchor.location.z + KILN_SKY.authoredVolume.min.z && location.z <= anchor.location.z + KILN_SKY.authoredVolume.max.z;
      return Object.freeze({ id: `kiln_sky:${dimensionId(anchor.dimension)}:${locationKey(anchor.location)}`, dimension: anchor.dimension, dimensionId: dimensionId(anchor.dimension), anchor: { ...anchor.location }, cacheLocation, recordLocation, contains });
    }
  }
  return null;
}

export function createKilnSkyService({ world, system, state, boundedEntities, resolveArena = resolveKilnSkyArena, rewardHooks = {}, codexHooks = {} }) {
  const sessions = new Map();
  let sequence = 0, miteSequence = 0;
  const hooks = Object.freeze({
    canDeliverHorn: rewardHooks.canDeliverHorn ?? (() => false),
    deliverHorn: rewardHooks.deliverHorn ?? (() => false),
    grantMaterialPackage: rewardHooks.grantMaterialPackage ?? (() => false),
    openArenaCache: rewardHooks.openArenaCache ?? (() => false),
  });
  const codex = Object.freeze({ onPull: codexHooks.onPull ?? (() => false), onTerminalCredit: codexHooks.onTerminalCredit ?? (() => false) });
  const byId = id => world.getAllPlayers().find(player => player.id === id);
  const playersFor = session => world.getAllPlayers().filter(player => dimensionId(player.dimension) === session.dimensionId);
  const inside = (playerOrEntity, arena) => arena.contains({ ...playerOrEntity.location, dimension: playerOrEntity.dimension ?? arena.dimension });

  function readCredits(player) { const current = state.playerState(player); return { current, credits: { ...(current.credits ?? {}) } }; }
  function writeFirstCredit(player) {
    const { current, credits } = readCredits(player), first = credits[KILN_SKY.sealCreditKey] !== true;
    const needsRepair = first || credits[KILN_SKY.entitlementKey] !== true;
    if (!needsRepair) return { saved: true, first: false };
    credits[KILN_SKY.sealCreditKey] = true;
    credits[KILN_SKY.entitlementKey] = true;
    const saved = state.savePlayer(player, { ...current, credits });
    return { saved, first: saved && first };
  }
  function claimHorn(player) {
    const { current, credits } = readCredits(player);
    if (credits[KILN_SKY.sealCreditKey] !== true || credits[KILN_SKY.entitlementKey] !== true || credits[KILN_SKY.hornClaimedKey] === true) return false;
    if (hooks.canDeliverHorn(player) !== true) return false;
    credits[KILN_SKY.hornClaimedKey] = true;
    if (!state.savePlayer(player, { ...current, credits })) return false;
    try { hooks.deliverHorn(player, KILN_SKY.hornItem); } catch {}
    return true;
  }
  const recoverHorn = player => claimHorn(player);

  function queuePending(playerId) {
    const w = state.worldState(), pending = { ...(w.encounters.pendingKilnSky ?? {}) };
    pending[playerId] = { sealCredit: true, entitlement: true, repeatRewards: true };
    w.encounters.pendingKilnSky = pending; return state.saveWorld(w);
  }
  function flushPending() {
    const w = state.worldState(), pending = { ...(w.encounters.pendingKilnSky ?? {}) };
    let changed = false;
    for (const player of world.getAllPlayers()) {
      if (!pending[player.id]) continue;
      const result = writeFirstCredit(player); if (!result.saved) continue;
      codex.onTerminalCredit(player); hooks.grantMaterialPackage(player, { encounterId: KILN_SKY.id, repeatClear: !result.first });
      if (result.first) claimHorn(player);
      delete pending[player.id]; changed = true;
    }
    if (changed) { w.encounters.pendingKilnSky = pending; state.saveWorld(w); }
    return changed;
  }

  function begin(player, arenaOrBlock) {
    const arena = arenaOrBlock?.contains ? arenaOrBlock : resolveArena(arenaOrBlock);
    if (!arena || !inside(player, arena) || [...sessions.values()].some(session => session.arena.id === arena.id)) return null;
    const id = `${arena.id}:${++sequence}`, now = system.currentTick;
    const session = { id, status: "arming", initiator: player.id, arena, dimension: arena.dimension, dimensionId: arena.dimensionId, dwell: new Map(), scalingParticipants: new Map(), rewardParticipants: new Map(), lateDwell: new Map(), lateJoinClosed: false, mites: [], boss: null, phase: 0, attack: null, attackCursor: 0, globalReadyAt: 0, attackReadyAt: new Map(), bossOutsideSince: null, wipeSince: null, noEligibleSince: null };
    for (const candidate of playersFor(session)) if (inside(candidate, arena) && isAlive(candidate)) session.dwell.set(candidate.id, now);
    sessions.set(id, session); return id;
  }

  function setBossHealth(boss, target) {
    const health = boss.getComponent?.("minecraft:health"), baseMax = health?.effectiveMax ?? health?.defaultValue ?? health?.maxValue ?? 80;
    const amplifier = Math.max(0, Math.ceil((target - baseMax) / 4) - 1);
    if (amplifier > 0) boss.addEffect?.("health_boost", 999999, { amplifier, showParticles: false });
    (boss.getComponent?.("minecraft:health") ?? health)?.setCurrentValue?.(target);
    boss.setDynamicProperty?.("aionbound:kiln_sky_target_health", target);
  }

  function pull(session) {
    const now = system.currentTick;
    const eligible = playersFor(session).filter(player => {
      const entered = session.dwell.get(player.id);
      return entered !== undefined && now - entered >= KILN_SKY.pullResidencyTicks && inside(player, session.arena) && isAlive(player);
    });
    if (!eligible.some(player => player.id === session.initiator)) { sessions.delete(session.id); return false; }
    eligible.sort((a, b) => a.id === session.initiator ? -1 : b.id === session.initiator ? 1 : (session.dwell.get(a.id) - session.dwell.get(b.id)) || a.id.localeCompare(b.id));
    const selected = eligible.slice(0, KILN_SKY.participantCap);
    let boss;
    try {
      boss = session.dimension.spawnEntity(KILN_SKY.bossType, session.arena.anchor);
      addTag(boss, KILN_SKY.apexTag); boss.setDynamicProperty?.(KILN_SKY.sessionProperty, session.id);
      for (const player of selected) {
        const record = { admittedAt: now, disconnectedAt: null, outsideSince: null, diedDuringSession: false };
        session.scalingParticipants.set(player.id, Object.freeze({ admittedAt: now }));
        session.rewardParticipants.set(player.id, record);
      }
      session.targetHealth = kilnSkyHealth(selected.length); setBossHealth(boss, session.targetHealth); phaseTag(boss, KILN_SKY.phases[0].id);
    } catch { boss?.remove?.(); sessions.delete(session.id); return false; }
    session.boss = boss; session.status = "active"; session.pulledAt = now; session.globalReadyAt = now + ticks(KILN_SKY.globalAttackCooldownSeconds);
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
    if (initiatorDwell !== undefined && system.currentTick - initiatorDwell >= KILN_SKY.pullResidencyTicks) pull(session);
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
        if (now - record.outsideSince >= KILN_SKY.voluntaryOutsideTicks) session.rewardParticipants.delete(id);
      }
    }
    if (session.phase >= 2) { session.lateJoinClosed = true; session.lateDwell.clear(); return; }
    const qualifiers = [];
    for (const player of online.values()) {
      if (session.rewardParticipants.has(player.id) || !inside(player, session.arena) || !isAlive(player)) { session.lateDwell.delete(player.id); continue; }
      const entered = session.lateDwell.get(player.id) ?? now; session.lateDwell.set(player.id, entered);
      if (now - entered >= KILN_SKY.lateJoinResidencyTicks) qualifiers.push(player);
    }
    qualifiers.sort((a, b) => a.id.localeCompare(b.id));
    for (const player of qualifiers) {
      if (session.rewardParticipants.size >= KILN_SKY.participantCap) break;
      session.rewardParticipants.set(player.id, { admittedAt: now, disconnectedAt: null, outsideSince: null, diedDuringSession: false, lateJoin: true });
      session.lateDwell.delete(player.id); codex.onPull(player);
    }
  }

  function liveMites(session) { session.mites = session.mites.filter(row => isEntityAvailable(row.entity)); return session.mites; }
  function trimMites(session) {
    const cap = Math.min(KILN_SKY.phases[session.phase].miteCap, KILN_SKY.globalMiteCap), mites = liveMites(session).sort((a, b) => a.sequence - b.sequence);
    while (mites.length > cap) { const row = mites.shift(); addTag(row.entity, KILN_SKY.trimmedMiteTag); row.entity.remove?.(); }
    session.mites = mites;
  }
  function spawnMites(session, requested) {
    trimMites(session);
    const cap = Math.min(KILN_SKY.phases[session.phase].miteCap, KILN_SKY.globalMiteCap), accepted = Math.min(requested, Math.max(0, cap - session.mites.length));
    for (let index = 0; index < accepted; index++) {
      try {
        const mite = session.dimension.spawnEntity(KILN_SKY.miteType, session.boss.location ?? session.arena.anchor);
        addTag(mite, KILN_SKY.miteTag); mite.setDynamicProperty?.(KILN_SKY.sessionProperty, session.id);
        session.mites.push({ entity: mite, sequence: ++miteSequence });
      } catch { break; }
    }
    return accepted;
  }

  function startAttack(session, id) {
    const spec = KILN_SKY.attacks[id];
    session.attack = { id, stage: "telegraph", stageEnds: system.currentTick + ticks(spec.telegraphSeconds) };
    attackTag(session.boss, id, "telegraph");
  }
  function advanceAttack(session) {
    const current = session.attack; if (!current || system.currentTick < current.stageEnds) return;
    const spec = KILN_SKY.attacks[current.id];
    if (current.stage === "telegraph") {
      current.stage = "active"; current.stageEnds = system.currentTick + ticks(spec.activeSeconds); attackTag(session.boss, current.id, "active");
      if (current.id === "mite_shake") spawnMites(session, spec.spawnCount); return;
    }
    if (current.stage === "active") { current.stage = "recovery"; current.stageEnds = system.currentTick + ticks(spec.recoverySeconds); attackTag(session.boss, current.id, "recovery"); return; }
    attackTag(session.boss, null, null); session.attack = null;
    session.globalReadyAt = system.currentTick + ticks(KILN_SKY.globalAttackCooldownSeconds);
    session.attackReadyAt.set(current.id, system.currentTick + ticks(spec.cooldownSeconds));
  }
  function scheduleAttack(session) {
    if (session.attack || system.currentTick < session.globalReadyAt) return;
    const available = KILN_SKY.phases[session.phase].attacks;
    for (let offset = 0; offset < available.length; offset++) {
      const index = (session.attackCursor + offset) % available.length, id = available[index];
      if (system.currentTick < (session.attackReadyAt.get(id) ?? 0)) continue;
      session.attackCursor = index + 1; startAttack(session, id); return;
    }
  }
  function phaseAndAttacks(session) {
    const health = session.boss.getComponent?.("minecraft:health")?.currentValue ?? session.targetHealth;
    const next = kilnSkyPhase(Math.max(0, health) / session.targetHealth);
    if (next > session.phase) {
      session.phase = next; phaseTag(session.boss, KILN_SKY.phases[next].id); trimMites(session);
      if (next >= 2) { session.lateJoinClosed = true; session.lateDwell.clear(); }
    }
    advanceAttack(session); scheduleAttack(session);
  }

  function clearSessionActors(session) {
    for (const row of liveMites(session)) { addTag(row.entity, KILN_SKY.trimmedMiteTag); row.entity.remove?.(); }
    session.mites = [];
    if (isEntityAvailable(session.boss)) { attackTag(session.boss, null, null); session.boss.remove?.(); }
  }
  function reset(session, reason = "reset") {
    clearSessionActors(session); sessions.delete(session.id);
    const initiator = byId(session.initiator); if (initiator) state.warn(initiator, `Kiln Sky ${reason.replaceAll("_", " ")}; the forge is unpulled.`);
    return true;
  }
  function resetChecks(session) {
    const now = system.currentTick;
    session.bossOutsideSince = inside(session.boss, session.arena) ? null : (session.bossOutsideSince ?? now);
    if (session.bossOutsideSince !== null && now - session.bossOutsideSince >= KILN_SKY.bossOutsideTicks) return reset(session, "leash reset");
    const connected = [...session.rewardParticipants.keys()].map(byId).filter(Boolean);
    const allDeadOrOutside = connected.length > 0 && connected.every(player => !isAlive(player) || !inside(player, session.arena));
    session.wipeSince = allDeadOrOutside ? (session.wipeSince ?? now) : null;
    if (session.wipeSince !== null && now - session.wipeSince >= KILN_SKY.allDeadOrOutsideTicks) return reset(session, "wipe reset");
    const anyConnectedAliveInside = connected.some(player => isAlive(player) && inside(player, session.arena));
    session.noEligibleSince = anyConnectedAliveInside ? null : (session.noEligibleSince ?? now);
    if (session.noEligibleSince !== null && now - session.noEligibleSince >= KILN_SKY.noEligibleTicks) return reset(session, "no eligible player reset");
    return false;
  }

  function completeWorld() {
    const w = state.worldState();
    if (w.encounters.terminal[KILN_SKY.worldCompletionKey]?.completed === true) return true;
    w.encounters.terminal[KILN_SKY.worldCompletionKey] = { completed: true, v: 1 };
    return state.saveWorld(w);
  }
  function terminalEligibleIds(session) {
    const now = system.currentTick, online = new Map(playersFor(session).map(player => [player.id, player]));
    return [...session.rewardParticipants].filter(([id, record]) => {
      const player = online.get(id);
      if (player && isAlive(player) && inside(player, session.arena)) return true;
      if (player && !isAlive(player)) { record.diedDuringSession = true; return true; }
      if (record.diedDuringSession) return true;
      return !player && record.disconnectedAt !== null && now - record.disconnectedAt <= KILN_SKY.disconnectGraceTicks;
    }).map(([id]) => id);
  }
  function isValidDeath(event, session) {
    const entity = event.deadEntity;
    return session?.status === "active" && entity === session.boss && entity.typeId === KILN_SKY.bossType
      && entity.hasTag?.(KILN_SKY.apexTag) === true && entity.getDynamicProperty?.(KILN_SKY.sessionProperty) === session.id;
  }
  function bossDeath(event) {
    if (event.deadEntity?.typeId !== KILN_SKY.bossType) return false;
    const id = event.deadEntity.getDynamicProperty?.(KILN_SKY.sessionProperty), session = sessions.get(id);
    if (!isValidDeath(event, session)) return false;
    const eligibleIds = terminalEligibleIds(session); if (!eligibleIds.length) { reset(session, "no terminal participant reset"); return false; }
    if (!completeWorld()) { reset(session, "completion persistence reset"); return false; }
    for (const playerId of eligibleIds) {
      const player = byId(playerId);
      if (!player) { queuePending(playerId); continue; }
      const result = writeFirstCredit(player); if (!result.saved) continue;
      codex.onTerminalCredit(player); hooks.grantMaterialPackage(player, { encounterId: KILN_SKY.id, repeatClear: !result.first });
      if (result.first) claimHorn(player);
    }
    hooks.openArenaCache({ encounterId: KILN_SKY.id, arena: session.arena });
    // Terminal completion wins over every pending reset clock.
    for (const row of liveMites(session)) { addTag(row.entity, KILN_SKY.trimmedMiteTag); row.entity.remove?.(); }
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
      const id = entity.getDynamicProperty?.(KILN_SKY.sessionProperty);
      if (!id) continue;
      const session = sessions.get(id);
      if (!session || (entity.hasTag?.(KILN_SKY.apexTag) && entity !== session.boss)) entity.remove?.();
    }
    flushPending();
  }

  return Object.freeze({ begin, tick, bossDeath, reconcile, claimHorn, recoverHorn, flushPending, resolveArena, sessions, constants: KILN_SKY });
}
