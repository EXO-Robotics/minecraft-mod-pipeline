export const TWINBOND = Object.freeze({
  id: "aionbound:twinbond",
  aspectTypes: Object.freeze(["aionbound:ash_sovereign_wyrm", "aionbound:tide_empress_wyrm"]),
  aspectTags: Object.freeze(["aionbound.twinbond.aspect.ember", "aionbound.twinbond.aspect.tide"]),
  sessionProperty: "aionbound:twinbond_session",
  siteKey: "aionbound.structure.twinbond.site.v1",
  worldCompletionKey: "aionbound.encounter.twinbond.completed.v1",
  playerCompletionKey: "aionbound.player.twinbond.completed.v1",
  entitlementKey: "aionbound.player.twinbond.reward_entitled.v1",
  relicClaimedKey: "aionbound.player.twinbond.relic_claimed.v1",
  edgeIgnitedKey: "aionbound.player.twinbond.edge_ignited.v1",
  memoryClaimedKey: "aionbound.player.twinbond.memory_claimed.v1",
  masteryStampKey: "aionbound.player.twinbond.mastery_stamp.v1",
  // Existing-schema cache fields needed to distinguish durable progression
  // credit from at-most-once physical fulfillment. They are not a new domain.
  edgeClaimedKey: "aionbound.player.twinbond.edge_claimed.v1",
  blankEntitledKey: "aionbound.player.twinbond.blank_entitled.v1",
  blankClaimedKey: "aionbound.player.twinbond.blank_claimed.v1",
  concordSparkKey: "aionbound.player.twinbond.concord_spark.v1",
  memoryCreditKeys: Object.freeze([
    "aionbound.player.twinbond.memory_credit.ww.v1",
    "aionbound.player.twinbond.memory_credit.ah.v1",
    "aionbound.player.twinbond.memory_credit.cm.v1",
    "aionbound.player.twinbond.memory_credit.sr.v1",
  ]),
  requiredSealKeys: Object.freeze([
    "aionbound.player.thorn_court.seal_credit.v1",
    "aionbound.player.kiln_sky.seal_credit.v1",
    "aionbound.player.pearl_depths.seal_credit.v1",
    "aionbound.player.storm_nest.seal_credit.v1",
  ]),
  requiredPilgrimageStamps: Object.freeze([
    "pilgrimage:gloam", "pilgrimage:brine", "pilgrimage:vent", "pilgrimage:cinderglass", "pilgrimage:storm",
    "pilgrimage:abyss", "pilgrimage:boneplain", "pilgrimage:riftscar", "pilgrimage:twinbond",
  ]),
  blankItem: "aionbound:trophy_edge_blank",
  relicItem: "aionbound:twinbond_relic",
  edgeItem: "aionbound:trophy_edge",
  memoryItem: "aionbound:memory_of_four_lands",
  participantCap: 4,
  pullResidencyTicks: 100,
  lateJoinTicks: 300,
  disconnectGraceTicks: 1200,
  aspectOutsideTicks: 200,
  allDeadOrOutsideTicks: 300,
  noEligibleTicks: 600,
  relicChannelTicks: 240,
  relicAbsenceResetTicks: 40,
  finaleIgnitionTicks: 100,
  globalActionCooldownTicks: 75,
  thresholds: Object.freeze({ split: 0.70, relic: 0.40 }),
  actions: Object.freeze({
    split: Object.freeze({ telegraph: 30, active: 18, recovery: 25, cooldown: 150 }),
    concord: Object.freeze({ telegraph: 38, active: 24, recovery: 30, cooldown: 220 }),
  }),
  size: Object.freeze({ x: 128, y: 48, z: 128 }),
  anchors: Object.freeze({
    arrival: Object.freeze({ x: 64, y: 12, z: 22 }),
    gate: Object.freeze({ x: 64, y: 12, z: 30 }),
    ember: Object.freeze({ x: 36, y: 12, z: 64 }),
    tide: Object.freeze({ x: 92, y: 12, z: 64 }),
    center: Object.freeze({ x: 64, y: 12, z: 64 }),
    completion: Object.freeze({ x: 64, y: 12, z: 94 }),
  }),
});

const dimensionId = value => value?.id ?? "minecraft:overworld";
const isEntityAvailable = entity => entity && entity.removed !== true && entity.isValid !== false;
const isAlive = player => (player.getComponent?.("minecraft:health")?.currentValue ?? 1) > 0;
const floorLocation = value => ({ x: Math.floor(value.x), y: Math.floor(value.y), z: Math.floor(value.z) });
const add = (left, right) => ({ x: left.x + right.x, y: left.y + right.y, z: left.z + right.z });
const subtract = (left, right) => ({ x: left.x - right.x, y: left.y - right.y, z: left.z - right.z });
const sameBlock = (left, right) => {
  const a = floorLocation(left), b = floorLocation(right);
  return a.x === b.x && a.y === b.y && a.z === b.z;
};
const hasTag = (entity, tag) => entity.hasTag?.(tag) === true;
function addTag(entity, tag) { if (!hasTag(entity, tag)) entity.addTag?.(tag); }
function clearTags(entity, prefix) { for (const tag of entity.getTags?.() ?? []) if (tag.startsWith(prefix)) entity.removeTag?.(tag); }
function phaseTag(entity, phase) { clearTags(entity, "aionbound.twinbond.phase."); addTag(entity, `aionbound.twinbond.phase.${phase}`); }
function actionTag(entity, stage) { clearTags(entity, "aionbound.twinbond.action."); if (stage) addTag(entity, `aionbound.twinbond.action.${stage}`); }

export function twinbondArena(origin, dimension) {
  const anchor = name => add(origin, TWINBOND.anchors[name]);
  return Object.freeze({
    id: `twinbond:${dimensionId(dimension)}:${origin.x},${origin.y},${origin.z}`,
    dimension,
    dimensionId: dimensionId(dimension),
    origin: { ...origin },
    arrival: anchor("arrival"), gate: anchor("gate"), ember: anchor("ember"), tide: anchor("tide"), center: anchor("center"), completion: anchor("completion"),
    contains(value) {
      return dimensionId(value?.dimension) === dimensionId(dimension)
        && value.x >= origin.x && value.x < origin.x + TWINBOND.size.x
        && value.y >= origin.y && value.y < origin.y + TWINBOND.size.y
        && value.z >= origin.z && value.z < origin.z + TWINBOND.size.z;
    },
    inRelicFocus(value) { return dimensionId(value?.dimension) === dimensionId(dimension) && sameBlock(value, anchor("center")); },
  });
}

export function twinbondPhase(emberFraction, tideFraction) {
  if (emberFraction <= TWINBOND.thresholds.relic && tideFraction <= TWINBOND.thresholds.relic) return 2;
  if (emberFraction <= TWINBOND.thresholds.split && tideFraction <= TWINBOND.thresholds.split) return 1;
  return 0;
}

export function createTwinbondService({ world, system, ItemStack, state, boundedEntities, placeSite = null, codexHooks = {} }) {
  const sessions = new Map();
  let sequence = 0;
  const codex = Object.freeze({
    onPull: codexHooks.onPull ?? (() => false),
    onTerminalCredit: codexHooks.onTerminalCredit ?? (() => false),
    onMastery: codexHooks.onMastery ?? (() => false),
  });
  const byId = id => world.getAllPlayers().find(player => player.id === id);
  const playersFor = session => world.getAllPlayers().filter(player => dimensionId(player.dimension) === session.arena.dimensionId);
  const inside = (subject, arena) => arena.contains({ ...subject.location, dimension: subject.dimension ?? arena.dimension });

  function readCredits(player) {
    const current = state.playerState(player);
    return { current, credits: { ...(current.credits ?? {}) } };
  }
  function siteRecord() { return state.worldState().structures?.[TWINBOND.siteKey] ?? null; }
  function arenaFromRecord(record = siteRecord()) {
    if (!record || record.state !== "ready" || record.dimension !== "minecraft:overworld") return null;
    return twinbondArena(record.origin, world.getDimension("overworld"));
  }
  function siteBlockMatches(block, arena) {
    if (!arena || dimensionId(block?.dimension) !== arena.dimensionId) return false;
    return (block.typeId === "aionbound:twinbond_approach_marker" && sameBlock(block.location, arena.arrival))
      || (block.typeId === "aionbound:twinbond_obelisk_site" && sameBlock(block.location, arena.gate))
      || (block.typeId === "aionbound:ceremony_anvil_site" && sameBlock(block.location, arena.completion));
  }
  function originForMarker(block) {
    const anchor = block.typeId === "aionbound:twinbond_approach_marker" ? TWINBOND.anchors.arrival : TWINBOND.anchors.gate;
    return subtract(floorLocation(block.location), anchor);
  }
  function defaultPlaceSite(block, arena) {
    const result = block.dimension.runCommand?.(`structure load aionbound:twinbond_slice_v1 ${arena.origin.x} ${arena.origin.y} ${arena.origin.z}`);
    if (result && Number.isFinite(result.successCount) && result.successCount < 1) return false;
    const placements = [
      [arena.arrival, "aionbound:twinbond_approach_marker"],
      [arena.gate, "aionbound:twinbond_obelisk_site"],
      [arena.ember, "aionbound:twin_thrones"],
      [arena.center, "aionbound:twinbond_obsidian_ring"],
      [arena.completion, "aionbound:ceremony_anvil_site"],
    ];
    for (const [location, typeId] of placements) block.dimension.getBlock?.(location)?.setType?.(typeId);
    return true;
  }
  function ensureSite(player, block) {
    const existing = siteRecord();
    if (existing?.state === "ready") return arenaFromRecord(existing);
    if (existing) { state.warn(player, "The Twinbond site is still reconciling."); return null; }
    if (dimensionId(block?.dimension) !== "minecraft:overworld" || !["aionbound:twinbond_obelisk_site", "aionbound:twinbond_approach_marker"].includes(block?.typeId)) return null;
    const origin = originForMarker(block), arena = twinbondArena(origin, block.dimension), w = state.worldState();
    w.structures ??= {};
    w.structures[TWINBOND.siteKey] = { v: 1, state: "placing", dimension: "minecraft:overworld", origin };
    if (!state.saveWorld(w)) return null;
    let placed = false;
    try { placed = (placeSite ?? defaultPlaceSite)(block, arena) === true; } catch { placed = false; }
    const next = state.worldState(); next.structures ??= {};
    if (!placed) { delete next.structures[TWINBOND.siteKey]; state.saveWorld(next); state.warn(player, "The authored Twinbond site could not be placed."); return null; }
    next.structures[TWINBOND.siteKey] = { v: 1, state: "ready", dimension: "minecraft:overworld", origin };
    if (!state.saveWorld(next)) { state.warn(player, "The Twinbond site could not be made durable."); return null; }
    return arena;
  }

  function hasPrerequisites(player) {
    const { current, credits } = readCredits(player);
    return TWINBOND.requiredSealKeys.every(key => credits[key] === true)
      && TWINBOND.requiredPilgrimageStamps.every(key => current.stamps.includes(key));
  }
  function container(player) { return player.getComponent?.("minecraft:inventory")?.container ?? null; }
  function hasItem(player, itemId) {
    const inventory = container(player); if (!inventory) return false;
    for (let slot = 0; slot < inventory.size; slot++) if (inventory.getItem(slot)?.typeId === itemId) return true;
    return false;
  }
  function canDeliver(player, itemId) {
    const inventory = container(player); if (!inventory) return false;
    for (let slot = 0; slot < inventory.size; slot++) {
      const item = inventory.getItem(slot);
      if (!item || (item.typeId === itemId && item.amount < (item.maxAmount ?? 1))) return true;
    }
    return false;
  }
  function deliverOnce(player, itemId, claimedKey) {
    let { current, credits } = readCredits(player);
    if (credits[claimedKey] === true || !canDeliver(player, itemId)) return false;
    credits[claimedKey] = true;
    if (!state.savePlayer(player, { ...current, credits })) return false;
    try {
      const remainder = container(player)?.addItem?.(new ItemStack(itemId, 1));
      return remainder === undefined || remainder === null || remainder.amount === 0;
    } catch { return false; }
  }
  function ensureBlankEntitlement(player) {
    if (!hasPrerequisites(player)) { state.warn(player, "Four chapter seals and the full pilgrimage are required."); return false; }
    let { current, credits } = readCredits(player);
    if (credits[TWINBOND.blankEntitledKey] !== true) {
      credits[TWINBOND.blankEntitledKey] = true;
      if (!state.savePlayer(player, { ...current, credits })) return false;
    }
    if (credits[TWINBOND.blankClaimedKey] !== true) deliverOnce(player, TWINBOND.blankItem, TWINBOND.blankClaimedKey);
    if (!hasItem(player, TWINBOND.blankItem) && credits[TWINBOND.blankClaimedKey] !== true) state.warn(player, "Make one inventory slot for the inert Trophy Edge, then return.");
    return true;
  }

  function worldCompleted() {
    return state.worldState().encounters.terminal[TWINBOND.worldCompletionKey]?.completed === true;
  }
  function writeWorldCompletion() {
    const w = state.worldState();
    if (w.encounters.terminal[TWINBOND.worldCompletionKey]?.completed === true) return true;
    w.encounters.terminal[TWINBOND.worldCompletionKey] = { v: 1, completed: true };
    return state.saveWorld(w);
  }
  function writePlayerTerminal(player) {
    const { current, credits } = readCredits(player), first = credits[TWINBOND.playerCompletionKey] !== true;
    credits[TWINBOND.playerCompletionKey] = true;
    credits[TWINBOND.entitlementKey] = true;
    credits[TWINBOND.concordSparkKey] = true;
    credits[TWINBOND.edgeIgnitedKey] = true;
    for (const key of TWINBOND.memoryCreditKeys) credits[key] = true;
    credits[TWINBOND.masteryStampKey] = true;
    const saved = state.savePlayer(player, { ...current, credits, endpoint: true });
    if (saved && !current.stamps.includes("endpoint:twinbond")) state.stamp(player, "endpoint:twinbond");
    return { saved, first: saved && first };
  }
  function physicalUnclaimed(credits) {
    return credits[TWINBOND.relicClaimedKey] !== true || credits[TWINBOND.edgeClaimedKey] !== true || credits[TWINBOND.memoryClaimedKey] !== true;
  }
  function fulfill(player) {
    let { credits } = readCredits(player);
    if (credits[TWINBOND.entitlementKey] !== true || !worldCompleted()) return false;
    if (credits[TWINBOND.relicClaimedKey] !== true) deliverOnce(player, TWINBOND.relicItem, TWINBOND.relicClaimedKey);
    ({ credits } = readCredits(player));
    if (credits[TWINBOND.edgeIgnitedKey] === true && credits[TWINBOND.edgeClaimedKey] !== true) deliverOnce(player, TWINBOND.edgeItem, TWINBOND.edgeClaimedKey);
    ({ credits } = readCredits(player));
    const memoryComplete = TWINBOND.memoryCreditKeys.every(key => credits[key] === true);
    if (memoryComplete && credits[TWINBOND.memoryClaimedKey] !== true) deliverOnce(player, TWINBOND.memoryItem, TWINBOND.memoryClaimedKey);
    return !physicalUnclaimed(readCredits(player).credits);
  }
  function recover(player) {
    const { credits } = readCredits(player);
    if (credits[TWINBOND.entitlementKey] !== true || !physicalUnclaimed(credits)) return false;
    fulfill(player);
    if (physicalUnclaimed(readCredits(player).credits)) state.warn(player, "Twinbond reward recovery is waiting for inventory space.");
    return true;
  }
  function queuePending(playerId) {
    const w = state.worldState(), pending = { ...(w.encounters.pendingTwinbond ?? {}) };
    pending[playerId] = { completion: true, entitlement: true };
    w.encounters.pendingTwinbond = pending; return state.saveWorld(w);
  }
  function flushPending() {
    const w = state.worldState(), pending = { ...(w.encounters.pendingTwinbond ?? {}) };
    let changed = false;
    for (const player of world.getAllPlayers()) {
      if (!pending[player.id]) continue;
      const result = writePlayerTerminal(player); if (!result.saved) continue;
      codex.onTerminalCredit(player); codex.onMastery(player); fulfill(player);
      delete pending[player.id]; changed = true;
    }
    if (changed) { w.encounters.pendingTwinbond = pending; state.saveWorld(w); }
    return changed;
  }

  function begin(player, block) {
    if (worldCompleted()) { recover(player); return null; }
    if (!ensureBlankEntitlement(player)) return null;
    let arena = arenaFromRecord();
    if (!arena) arena = ensureSite(player, block);
    if (!arena || !siteBlockMatches(block, arena)) { state.warn(player, "Only the durable authored Twinbond site can admit the finale."); return null; }
    if (!hasItem(player, TWINBOND.blankItem)) { state.warn(player, "Bring the inert Trophy Edge to the authored gate."); return null; }
    if (sessions.size || [...sessions.values()].some(session => session.arena.id === arena.id)) { state.warn(player, "Twinbond is already active."); return null; }
    const now = system.currentTick, id = `${arena.id}:${++sequence}`;
    const session = {
      id, status: "arming", terminalLock: false, initiator: player.id, arena, dimension: arena.dimension, dwell: new Map(), lateDwell: new Map(),
      participants: new Map(), aspects: [], phase: 0, action: null, nextActionAt: 0, actionCursor: 0,
      channelTicks: 0, focusAbsentSince: null, aspectOutsideSince: new Map(), wipeSince: null, noEligibleSince: null,
    };
    for (const candidate of playersFor(session)) if (inside(candidate, arena) && isAlive(candidate)) session.dwell.set(candidate.id, now);
    sessions.set(id, session); return id;
  }
  function pull(session) {
    const now = system.currentTick;
    const eligible = playersFor(session).filter(player => {
      const entered = session.dwell.get(player.id);
      return entered !== undefined && now - entered >= TWINBOND.pullResidencyTicks && inside(player, session.arena) && isAlive(player);
    }).sort((a, b) => a.id === session.initiator ? -1 : b.id === session.initiator ? 1 : a.id.localeCompare(b.id)).slice(0, TWINBOND.participantCap);
    if (!eligible.some(player => player.id === session.initiator)) { sessions.delete(session.id); return false; }
    const spawned = [];
    try {
      for (let index = 0; index < TWINBOND.aspectTypes.length; index++) {
        const entity = session.dimension.spawnEntity(TWINBOND.aspectTypes[index], index === 0 ? session.arena.ember : session.arena.tide);
        addTag(entity, TWINBOND.aspectTags[index]); phaseTag(entity, "split_approach");
        entity.setDynamicProperty?.(TWINBOND.sessionProperty, session.id); spawned.push(entity);
      }
    } catch { for (const entity of spawned) entity.remove?.(); sessions.delete(session.id); return false; }
    for (const player of eligible) session.participants.set(player.id, { disconnectedAt: null, outsideSince: null, diedDuringSession: false });
    session.aspects = spawned; session.status = "active"; session.nextActionAt = now + TWINBOND.globalActionCooldownTicks;
    for (const player of eligible) codex.onPull(player);
    return true;
  }
  function updateArming(session) {
    const present = new Set(playersFor(session).map(player => player.id));
    for (const id of session.dwell.keys()) if (!present.has(id)) session.dwell.delete(id);
    for (const player of playersFor(session)) {
      if (inside(player, session.arena) && isAlive(player)) session.dwell.set(player.id, session.dwell.get(player.id) ?? system.currentTick);
      else session.dwell.delete(player.id);
    }
    const entered = session.dwell.get(session.initiator);
    if (entered !== undefined && system.currentTick - entered >= TWINBOND.pullResidencyTicks) pull(session);
  }
  function updatePresence(session) {
    const now = system.currentTick, online = new Map(playersFor(session).map(player => [player.id, player]));
    for (const [id, record] of [...session.participants]) {
      const player = online.get(id);
      if (!player) { record.disconnectedAt ??= now; continue; }
      record.disconnectedAt = null;
      if (!isAlive(player)) { record.diedDuringSession = true; continue; }
      record.outsideSince = inside(player, session.arena) ? null : (record.outsideSince ?? now);
    }
    if (session.phase >= 2) { session.lateDwell.clear(); return; }
    for (const player of online.values()) {
      if (session.participants.has(player.id) || !inside(player, session.arena) || !isAlive(player)) { session.lateDwell.delete(player.id); continue; }
      const entered = session.lateDwell.get(player.id) ?? now; session.lateDwell.set(player.id, entered);
      if (now - entered >= TWINBOND.lateJoinTicks && session.participants.size < TWINBOND.participantCap) {
        session.participants.set(player.id, { disconnectedAt: null, outsideSince: null, diedDuringSession: false, lateJoin: true });
        session.lateDwell.delete(player.id); codex.onPull(player);
      }
    }
  }
  function health(entity) { return entity.getComponent?.("minecraft:health"); }
  function fractions(session) {
    return session.aspects.map(entity => Math.max(0, health(entity)?.currentValue ?? 160) / 160);
  }
  function clamp(entity, target) {
    const component = health(entity); if (component && component.currentValue < target) component.setCurrentValue?.(target);
  }
  function updatePhase(session) {
    const [ember, tide] = fractions(session), next = twinbondPhase(ember, tide);
    if (next <= session.phase) return;
    session.phase = next; session.action = null;
    const id = next === 1 ? "concord_pressure" : "relic_trial";
    for (const entity of session.aspects) { actionTag(entity, null); phaseTag(entity, id); }
    if (next === 2) for (const entity of session.aspects) clamp(entity, 64);
    session.nextActionAt = system.currentTick + TWINBOND.globalActionCooldownTicks;
  }
  function startAction(session) {
    const spec = session.phase === 0 ? TWINBOND.actions.split : TWINBOND.actions.concord;
    const targets = session.phase === 0 ? [session.aspects[session.actionCursor++ % 2]] : session.aspects;
    session.action = { spec, targets, stage: "telegraph", stageEnds: system.currentTick + spec.telegraph };
    for (const entity of targets) actionTag(entity, "telegraph");
  }
  function advanceAction(session) {
    const current = session.action; if (!current || system.currentTick < current.stageEnds) return;
    if (current.stage === "telegraph") { current.stage = "active"; current.stageEnds = system.currentTick + current.spec.active; for (const entity of current.targets) actionTag(entity, "active"); return; }
    if (current.stage === "active") { current.stage = "recovery"; current.stageEnds = system.currentTick + current.spec.recovery; for (const entity of current.targets) actionTag(entity, "recovery"); return; }
    for (const entity of current.targets) actionTag(entity, null);
    session.action = null; session.nextActionAt = system.currentTick + Math.max(TWINBOND.globalActionCooldownTicks, current.spec.cooldown);
  }
  function scheduleAction(session) { advanceAction(session); if (!session.action && session.phase < 3 && system.currentTick >= session.nextActionAt) startAction(session); }
  function updateRelicTrial(session) {
    if (session.phase !== 2) return;
    for (const entity of session.aspects) clamp(entity, 64);
    const focused = [...session.participants.keys()].map(byId).filter(Boolean).some(player => isAlive(player) && session.arena.inRelicFocus({ ...player.location, dimension: player.dimension }));
    if (focused) { session.focusAbsentSince = null; session.channelTicks++; }
    else {
      session.focusAbsentSince ??= system.currentTick;
      if (system.currentTick - session.focusAbsentSince >= TWINBOND.relicAbsenceResetTicks) session.channelTicks = 0;
    }
    if (session.channelTicks < TWINBOND.relicChannelTicks) return;
    session.phase = 3; session.action = null; session.ignitionEnds = system.currentTick + TWINBOND.finaleIgnitionTicks;
    for (const entity of session.aspects) { actionTag(entity, null); phaseTag(entity, "finale_ignition"); }
  }
  function terminalEligibleIds(session) {
    const now = system.currentTick, online = new Map(playersFor(session).map(player => [player.id, player]));
    return [...session.participants].filter(([id, record]) => {
      const player = online.get(id);
      if (player && inside(player, session.arena)) return true;
      if (player && record.diedDuringSession) return true;
      return !player && record.disconnectedAt !== null && now - record.disconnectedAt <= TWINBOND.disconnectGraceTicks;
    }).map(([id]) => id);
  }
  function clearSession(session) { for (const entity of session.aspects) if (isEntityAvailable(entity)) { actionTag(entity, null); entity.remove?.(); } sessions.delete(session.id); }
  function reset(session, reason) { clearSession(session); const player = byId(session.initiator); if (player) state.warn(player, `Twinbond ${reason.replaceAll("_", " ")}; the authored site is unpulled.`); return true; }
  function complete(session) {
    if (session.terminalLock || session.phase !== 3 || system.currentTick < session.ignitionEnds) return false;
    session.terminalLock = true;
    const eligible = terminalEligibleIds(session);
    if (!eligible.length || !writeWorldCompletion()) { session.terminalLock = false; return reset(session, "terminal persistence reset"); }
    for (const id of eligible) {
      const player = byId(id);
      if (!player) { queuePending(id); continue; }
      const result = writePlayerTerminal(player); if (!result.saved) continue;
      codex.onTerminalCredit(player); codex.onMastery(player); fulfill(player);
    }
    clearSession(session); return true;
  }
  function resetChecks(session) {
    const now = system.currentTick;
    for (const entity of session.aspects) {
      const outside = inside(entity, session.arena) ? null : (session.aspectOutsideSince.get(entity) ?? now);
      if (outside === null) session.aspectOutsideSince.delete(entity); else session.aspectOutsideSince.set(entity, outside);
      if (outside !== null && now - outside >= TWINBOND.aspectOutsideTicks) return reset(session, "aspect leash reset");
    }
    const connected = [...session.participants.keys()].map(byId).filter(Boolean);
    const allDeadOrOutside = connected.length > 0 && connected.every(player => !isAlive(player) || !inside(player, session.arena));
    session.wipeSince = allDeadOrOutside ? (session.wipeSince ?? now) : null;
    if (session.wipeSince !== null && now - session.wipeSince >= TWINBOND.allDeadOrOutsideTicks) return reset(session, "wipe reset");
    const anyEligible = connected.some(player => isAlive(player) && inside(player, session.arena));
    session.noEligibleSince = anyEligible ? null : (session.noEligibleSince ?? now);
    if (session.noEligibleSince !== null && now - session.noEligibleSince >= TWINBOND.noEligibleTicks) return reset(session, "no eligible player reset");
    return false;
  }
  function tick() {
    if (system.currentTick % 20 === 0) flushPending();
    for (const session of [...sessions.values()]) {
      if (session.status === "arming") { updateArming(session); continue; }
      if (session.aspects.length !== 2 || session.aspects.some(entity => !isEntityAvailable(entity))) { reset(session, "missing aspect reset"); continue; }
      updatePresence(session); updatePhase(session); updateRelicTrial(session);
      if (session.phase === 3) { complete(session); continue; }
      scheduleAction(session); if (resetChecks(session)) continue;
    }
  }
  function handleHurt(event) {
    const entity = event.hurtEntity, id = entity?.getDynamicProperty?.(TWINBOND.sessionProperty), session = sessions.get(id);
    if (!session || !session.aspects.includes(entity) || session.terminalLock) return false;
    const index = session.aspects.indexOf(entity), other = session.aspects[1 - index], currentHealth = health(entity)?.currentValue ?? 160;
    if (session.phase >= 2) clamp(entity, 64);
    else if (session.phase === 1 && (health(other)?.currentValue ?? 160) > 64 && currentHealth < 64) clamp(entity, 64);
    else if (session.phase === 0 && (health(other)?.currentValue ?? 160) > 112 && currentHealth < 112) clamp(entity, 112);
    updatePhase(session); return true;
  }
  function bossDeath(event) {
    const entity = event.deadEntity, id = entity?.getDynamicProperty?.(TWINBOND.sessionProperty), session = sessions.get(id);
    if (!TWINBOND.aspectTypes.includes(entity?.typeId) || !session) return false;
    // No individual aspect death, command kill, or ordinary death event is a
    // valid terminal. The sole terminal is the completed ignition window.
    reset(session, "invalid individual death reset"); return true;
  }
  function blockInteraction(player, block) {
    if (!block || !["aionbound:twinbond_obelisk_site", "aionbound:twinbond_approach_marker", "aionbound:ceremony_anvil_site"].includes(block.typeId)) return false;
    if (worldCompleted()) { recover(player); return true; }
    begin(player, block); return true;
  }
  function reconcile() {
    for (const entity of boundedEntities()) {
      const id = entity.getDynamicProperty?.(TWINBOND.sessionProperty);
      if (id && !sessions.has(id)) entity.remove?.();
    }
    const w = state.worldState(), record = w.structures?.[TWINBOND.siteKey];
    if (record?.state === "placing") { delete w.structures[TWINBOND.siteKey]; state.saveWorld(w); }
    flushPending();
  }

  return Object.freeze({ begin, tick, handleHurt, bossDeath, blockInteraction, reconcile, recover, fulfill, flushPending, arenaFromRecord, sessions, constants: TWINBOND });
}
