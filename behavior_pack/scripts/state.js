import { COMBINED_BUDGETS } from "./budgets.js";
import { IDS } from "./catalog.js";

export const STATE_VERSION = 3;

export function parseObject(raw, fallback = null) {
  try { const value = JSON.parse(raw || ""); return value && typeof value === "object" && !Array.isArray(value) ? value : fallback; }
  catch { return fallback; }
}
const objectOrEmpty = value => value && typeof value === "object" && !Array.isArray(value) ? value : {};
const strings = (value, cap) => [...new Set(Array.isArray(value) ? value.filter(x => typeof x === "string") : [])].slice(0, cap);

export function migrateWorld(source = {}) {
  if (source?.v === STATE_VERSION) {
    return {
      ...source,
      v: STATE_VERSION,
      journals: objectOrEmpty(source.journals), journalOrder: strings(source.journalOrder, COMBINED_BUDGETS.journalTerminal * 2),
      structures: objectOrEmpty(source.structures), quarantine: Array.isArray(source.quarantine) ? source.quarantine : [],
      cells: objectOrEmpty(source.cells), devices: objectOrEmpty(source.devices), sequence: Number.isSafeInteger(source.sequence) ? source.sequence : 0,
      encounters: { active: objectOrEmpty(source.encounters?.active), terminal: objectOrEmpty(source.encounters?.terminal ?? source.terminal) },
    };
  }
  return {
    v: STATE_VERSION,
    journals: objectOrEmpty(source.journals), journalOrder: [], structures: objectOrEmpty(source.structures),
    quarantine: Array.isArray(source.quarantine) ? source.quarantine : [], cells: objectOrEmpty(source.cells), devices: {}, sequence: 0,
    encounters: { active: objectOrEmpty(source.encounters?.active), terminal: objectOrEmpty(source.encounters?.terminal ?? source.terminal) },
  };
}

export function migratePlayer(source = {}) {
  if (source?.v === STATE_VERSION) {
    return {
      ...source, v: STATE_VERSION, stamps: strings(source.stamps, COMBINED_BUDGETS.discoveries), credits: objectOrEmpty(source.credits),
      cooldowns: objectOrEmpty(source.cooldowns), opens: Array.isArray(source.opens) ? source.opens.filter(Number.isFinite).slice(-COMBINED_BUDGETS.chaosMinute) : [],
      cell: source.cell ?? null, endpoint: source.endpoint === true,
      codex: { topic: Number.isSafeInteger(source.codex?.topic) ? source.codex.topic : 0 },
      goals: { arsenal: source.goals?.arsenal === true, naturalist: source.goals?.naturalist === true, surveyor: source.goals?.surveyor === true },
    };
  }
  return {
    v: STATE_VERSION, stamps: strings(source.stamps, COMBINED_BUDGETS.discoveries), credits: objectOrEmpty(source.credits),
    cooldowns: objectOrEmpty(source.cooldowns), opens: Array.isArray(source.opens) ? source.opens.filter(Number.isFinite).slice(-COMBINED_BUDGETS.chaosMinute) : [],
    cell: source.cell ?? null, endpoint: source.endpoint === true, codex: { topic: 0 },
    goals: { arsenal: false, naturalist: false, surveyor: false },
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
    const v2 = parseObject(world.getDynamicProperty(IDS.oldWorldV2));
    const migrated = migrateWorld(v2 ?? parseObject(world.getDynamicProperty(IDS.oldWorldV1), {}));
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
    const v2 = parseObject(player.getDynamicProperty(IDS.oldPlayerV2));
    const migrated = migratePlayer(v2 ?? parseObject(player.getDynamicProperty(IDS.oldPlayerV1), {}));
    savePlayer(player, migrated); return migrated;
  };
  const stamp = (player, key) => {
    const state = playerState(player);
    if (state.stamps.includes(key)) return false;
    if (state.stamps.length >= COMBINED_BUDGETS.discoveries) { warn(player, "Codex discovery capacity reached."); return false; }
    return savePlayer(player, { ...state, stamps: [...state.stamps, key] });
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
  return { worldState, saveWorld, playerState, savePlayer, stamp, warn, nextOperationId, pruneJournals };
}
