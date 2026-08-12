import { COMBINED_BUDGETS } from "./budgets.js";
import { CODEX_EVENT_INDEX, CODEX_REGISTRY_VERSION, IDS } from "./catalog.js";

export const STATE_VERSION = 4;
export const CODEX_DISCOVERY_REGIONS = Object.freeze(["ww", "ah", "cm", "sr"]);
export const CODEX_DISCOVERY_VERSION = CODEX_REGISTRY_VERSION;
// Schema remains v4. Registry v5 appends Skyreach using region-local category
// addresses without reallocating any Whisperwood/Ashen/Crystal Marsh address.
export const CODEX_CATEGORY_CAPS = Object.freeze({
  resource: 20,
  plant: 10,
  creature: 10,
  structure: 10,
  equipment: 21,
  boss: 1,
  progression: 2,
});

export function parseObject(raw, fallback = null) {
  try { const value = JSON.parse(raw || ""); return value && typeof value === "object" && !Array.isArray(value) ? value : fallback; }
  catch { return fallback; }
}
const objectOrEmpty = value => value && typeof value === "object" && !Array.isArray(value) ? value : {};
const strings = (value, cap) => [...new Set(Array.isArray(value) ? value.filter(x => typeof x === "string") : [])].slice(0, cap);
const hexLength = category => Math.ceil(CODEX_CATEGORY_CAPS[category] / 4) * 2;
const emptyCategory = category => "0".repeat(hexLength(category));
const hasCategory = category => Object.prototype.hasOwnProperty.call(CODEX_CATEGORY_CAPS, category);
const normalizeCategoryBits = (value, category) => typeof value === "string" && /^[0-9a-f]+$/i.test(value) && value.length === hexLength(category)
  ? value.toLowerCase()
  : emptyCategory(category);

export function normalizeCodexDiscovery(value = {}) {
  const source = objectOrEmpty(value), result = { rv: CODEX_DISCOVERY_VERSION };
  for (const region of CODEX_DISCOVERY_REGIONS) {
    const regionSource = objectOrEmpty(source[region]), regionResult = {};
    for (const category of Object.keys(CODEX_CATEGORY_CAPS)) {
      const bits = normalizeCategoryBits(regionSource[category], category);
      if (bits !== emptyCategory(category)) regionResult[category] = bits;
    }
    if (Object.keys(regionResult).length) result[region] = regionResult;
  }
  return result;
}

export function codexDiscoveryState(discovery, region, category, index) {
  if (!CODEX_DISCOVERY_REGIONS.includes(region) || !hasCategory(category) || !Number.isInteger(index) || index < 0 || index >= CODEX_CATEGORY_CAPS[category]) return 0;
  const bits = normalizeCategoryBits(objectOrEmpty(objectOrEmpty(discovery)[region])[category], category);
  const byte = Number.parseInt(bits.slice(Math.floor(index / 4) * 2, Math.floor(index / 4) * 2 + 2), 16);
  return (byte >> ((index % 4) * 2)) & 3;
}

export function transitionCodexDiscovery(discovery, region, category, index, requestedState) {
  const current = codexDiscoveryState(discovery, region, category, index);
  if (!CODEX_DISCOVERY_REGIONS.includes(region) || !hasCategory(category) || !Number.isInteger(index) || index < 0 || index >= CODEX_CATEGORY_CAPS[category] || ![1, 2].includes(requestedState) || requestedState <= current) {
    return { changed: false, discovery: normalizeCodexDiscovery(discovery), previous: current, current };
  }
  const normalized = normalizeCodexDiscovery(discovery), bytes = [];
  const bits = normalizeCategoryBits(normalized[region]?.[category], category);
  for (let offset = 0; offset < hexLength(category); offset += 2) bytes.push(Number.parseInt(bits.slice(offset, offset + 2), 16));
  const byteIndex = Math.floor(index / 4), shift = (index % 4) * 2;
  bytes[byteIndex] = (bytes[byteIndex] & ~(3 << shift)) | (requestedState << shift);
  const encoded = bytes.map(byte => byte.toString(16).padStart(2, "0")).join("");
  normalized[region] = { ...objectOrEmpty(normalized[region]), [category]: encoded };
  return { changed: true, discovery: normalized, previous: current, current: requestedState };
}

const migrateCodex = (source, stamps = []) => {
  let discovery = normalizeCodexDiscovery(source?.discovery);
  for (const stamp of stamps) {
    const event = CODEX_EVENT_INDEX[stamp];
    if (!event) continue;
    discovery = transitionCodexDiscovery(discovery, event.region, event.category, event.index, event.state).discovery;
  }
  return {
    ...objectOrEmpty(source),
    topic: Number.isSafeInteger(source?.topic) ? source.topic : 0,
    discovery,
  };
};

export function migrateWorld(source = {}) {
  const encounterSource = objectOrEmpty(source.encounters);
  const encounterActive = { ...objectOrEmpty(encounterSource.active) };
  const pendingThornCourt = objectOrEmpty(encounterSource.pendingThornCourt);
  const pendingKilnSky = objectOrEmpty(encounterSource.pendingKilnSky);
  const pendingPearlDepths = objectOrEmpty(encounterSource.pendingPearlDepths);
  // Ratified arena sessions are live-memory only. Drop only legacy or
  // interrupted rows for those encounters while preserving all other encounters.
  for (const [key, value] of Object.entries(encounterActive)) {
    if (key.startsWith("thorn_court:") || value?.encounterId === "aionbound:thorn_court"
      || key.startsWith("kiln_sky:") || value?.encounterId === "aionbound:kiln_sky"
      || key.startsWith("pearl_depths:") || value?.encounterId === "aionbound:pearl_depths") delete encounterActive[key];
  }
  return {
    ...objectOrEmpty(source),
    v: STATE_VERSION,
    journals: objectOrEmpty(source.journals), journalOrder: strings(source.journalOrder, COMBINED_BUDGETS.journalTerminal * 2), structures: objectOrEmpty(source.structures),
    quarantine: Array.isArray(source.quarantine) ? source.quarantine : [], cells: objectOrEmpty(source.cells), devices: objectOrEmpty(source.devices),
    sequence: Number.isSafeInteger(source.sequence) ? source.sequence : 0,
    encounters: {
      active: encounterActive,
      terminal: objectOrEmpty(encounterSource.terminal ?? source.terminal),
      ...(Object.keys(pendingThornCourt).length ? { pendingThornCourt } : {}),
      ...(Object.keys(pendingKilnSky).length ? { pendingKilnSky } : {}),
      ...(Object.keys(pendingPearlDepths).length ? { pendingPearlDepths } : {}),
    },
  };
}

export function migratePlayer(source = {}) {
  const migratedStamps = strings(source.stamps, COMBINED_BUDGETS.discoveries);
  return {
    ...objectOrEmpty(source), v: STATE_VERSION, stamps: migratedStamps, credits: objectOrEmpty(source.credits),
    cooldowns: objectOrEmpty(source.cooldowns), opens: Array.isArray(source.opens) ? source.opens.filter(Number.isFinite).slice(-COMBINED_BUDGETS.chaosMinute) : [],
    cell: source.cell ?? null, endpoint: source.endpoint === true, codex: migrateCodex(source.codex, migratedStamps),
    goals: { arsenal: source.goals?.arsenal === true, naturalist: source.goals?.naturalist === true, surveyor: source.goals?.surveyor === true },
  };
}

export function createStateService({ world, system, notify = () => {} }) {
  const warnings = new Map();
  const warn = (player, text) => {
    const key = `${player.id}:${text}`, now = system.currentTick;
    if ((warnings.get(key) ?? -100) + 100 <= now) { warnings.set(key, now); notify(player, text); }
  };
  const encode = (value, cap) => { const raw = JSON.stringify(value); return raw.length <= cap ? raw : null; };
  const saveWorld = value => { const raw = encode(value, COMBINED_BUDGETS.worldBytes); if (!raw) return false; world.setDynamicProperty(IDS.world, raw); return true; };
  const worldState = () => {
    const current = parseObject(world.getDynamicProperty(IDS.world));
    if (current?.v === STATE_VERSION) return migrateWorld(current);
    const v3 = parseObject(world.getDynamicProperty(IDS.oldWorldV3));
    const v2 = parseObject(world.getDynamicProperty(IDS.oldWorldV2));
    const migrated = migrateWorld(v3 ?? v2 ?? parseObject(world.getDynamicProperty(IDS.oldWorldV1), {}));
    saveWorld(migrated); return migrated;
  };
  const savePlayer = (player, value) => {
    const raw = encode(value, COMBINED_BUDGETS.playerBytes);
    if (!raw) { warn(player, "Codex capacity reached; no progress was changed."); return false; }
    player.setDynamicProperty(IDS.player, raw); return true;
  };
  const playerState = player => {
    const current = parseObject(player.getDynamicProperty(IDS.player));
    if (current?.v === STATE_VERSION) return migratePlayer(current);
    const v3 = parseObject(player.getDynamicProperty(IDS.oldPlayerV3));
    const v2 = parseObject(player.getDynamicProperty(IDS.oldPlayerV2));
    const migrated = migratePlayer(v3 ?? v2 ?? parseObject(player.getDynamicProperty(IDS.oldPlayerV1), {}));
    savePlayer(player, migrated); return migrated;
  };
  const stamp = (player, key) => {
    const state = playerState(player);
    if (state.stamps.includes(key)) return false;
    if (state.stamps.length >= COMBINED_BUDGETS.discoveries) { warn(player, "Codex discovery capacity reached."); return false; }
    return savePlayer(player, { ...state, stamps: [...state.stamps, key] });
  };
  const transitionCodex = (player, region, category, index, requestedState) => {
    const current = playerState(player);
    const transition = transitionCodexDiscovery(current.codex.discovery, region, category, index, requestedState);
    if (!transition.changed) return false;
    return savePlayer(player, { ...current, codex: { ...current.codex, discovery: transition.discovery } });
  };
  const nextOperationId = (prefix, playerId) => {
    const state = worldState(); state.sequence = (state.sequence + 1) % Number.MAX_SAFE_INTEGER;
    if (!saveWorld(state)) return null;
    return `${prefix}:${playerId}:${state.sequence}`;
  };
  const pruneJournals = state => {
    const terminal = state.journalOrder.filter(id => state.journals[id]?.state === "terminal");
    while (terminal.length > COMBINED_BUDGETS.journalTerminal) { const id = terminal.shift(); delete state.journals[id]; state.journalOrder = state.journalOrder.filter(x => x !== id); }
  };
  return { worldState, saveWorld, playerState, savePlayer, stamp, transitionCodex, warn, nextOperationId, pruneJournals };
}
