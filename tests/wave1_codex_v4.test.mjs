import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SOURCE = resolve(ROOT, "behavior_pack/scripts");
const MODULE_DIR = await mkdtemp(resolve(tmpdir(), "aionbound-codex-v4-"));
for (const name of ["wave1_codex_extension_data", "wave1_codex_ashen_data", "wave1_codex_crystal_data", "wave1_codex_skyreach_data", "wave1_codex_data", "wave1_codex_ui_data", "catalog", "budgets", "state", "codex"]) {
  const source = (await readFile(resolve(SOURCE, `${name}.js`), "utf8"))
    .replaceAll(/from "\.\/([a-z0-9_]+)\.js"/g, 'from "./$1.mjs"');
  await writeFile(resolve(MODULE_DIR, `${name}.mjs`), source);
}
const load = name => import(pathToFileURL(resolve(MODULE_DIR, `${name}.mjs`)).href);
const data = await load("wave1_codex_data");
const catalog = await load("catalog");
const stateModule = await load("state");
const { COMBINED_BUDGETS } = await load("budgets");
const { createCodexService } = await load("codex");

const map = JSON.parse(await readFile(resolve(ROOT, "engineering/whisperwood-intake/codex/WHISPERWOOD_CODEX_IMPLEMENTATION_MAP.json"), "utf8"));
const extensionMap = JSON.parse(await readFile(resolve(ROOT, "engineering/whisperwood-intake/codex-extension/WHISPERWOOD_CODEX_EXTENSION_MAP.json"), "utf8"));
const mappedEvents = map.entries.flatMap(entry => [
  ...entry.discovery_stamps,
  ...(entry.detail_events ?? []),
].map(discovery => ({ id: discovery.id, state: discovery.stage === "partial" ? 1 : 2, event: discovery.event, warehouseId: entry.warehouse_id })));

test("runtime registry preserves the exact WW/AH/CM prefix and appends Skyreach", () => {
  const extensionEntries = ["structures", "equipment", "bosses", "progression"].flatMap(category => extensionMap.entries[category]);
  assert.equal(data.WAVE1_CODEX_REGISTRY_VERSION, 5);
  assert.equal(data.WHISPERWOOD_CODEX_FOUNDATION_ENTRIES.length, 40);
  assert.equal(data.WHISPERWOOD_CODEX_ENTRIES.length, 74);
  assert.deepEqual(data.WHISPERWOOD_CODEX_ENTRIES.slice(0, 40).map(entry => entry.id), map.entries.map(entry => entry.id));
  assert.deepEqual(data.WHISPERWOOD_CODEX_ENTRIES.slice(0, 40).map(entry => entry.warehouseId), map.entries.map(entry => entry.warehouse_id));
  assert.deepEqual(data.WHISPERWOOD_CODEX_ENTRIES.slice(40).map(entry => entry.id), extensionEntries.map(entry => entry.id));
  assert.equal(data.WAVE1_CODEX_ENTRIES.length, 254);
  assert.deepEqual(data.WAVE1_CODEX_ENTRIES.slice(0, 74), data.WHISPERWOOD_CODEX_ENTRIES);
  assert.equal(data.WAVE1_CODEX_ENTRIES.slice(140, 204).length, 64);
  assert.equal(data.WAVE1_CODEX_ENTRIES[140].region, "cm");
  assert.equal(data.WAVE1_CODEX_ENTRIES.slice(204).length, 50);
  assert.ok(data.WAVE1_CODEX_ENTRIES.slice(204).every(entry => entry.region === "sr"));
  assert.ok(Object.keys(data.WAVE1_CODEX_EVENT_INDEX).length > mappedEvents.length + extensionEntries.reduce((count, entry) => count + entry.discovery_events.length, 0));
  for (const expected of mappedEvents) {
    const actual = data.WAVE1_CODEX_EVENT_INDEX[expected.id];
    assert.ok(actual, expected.id);
    assert.equal(actual.state, expected.state, expected.id);
    assert.equal(actual.event, expected.event, expected.id);
    assert.equal(data.WHISPERWOOD_CODEX_ENTRIES.find(entry => entry.warehouseId === expected.warehouseId).events.some(event => event.id === expected.id), true);
  }
  assert.strictEqual(catalog.CODEX_ENTRY_REGISTRY, data.WAVE1_CODEX_ENTRIES);
});

test("v3 to v4 migration is idempotent and preserves stamps topic goals and other domains", () => {
  const source = {
    v: 3,
    stamps: ["legacy:one", "codex:ww:creature:mosskip_buck:observed", "codex_detail:ww:creature:mosskip_buck:defeated"],
    credits: { old: 4 }, cooldowns: { ray: 12 }, opens: [1, 2], cell: { owner: "p" }, endpoint: true,
    codex: { topic: 3 }, goals: { arsenal: true, naturalist: false, surveyor: true }, extraDomain: { keep: true },
  };
  const once = stateModule.migratePlayer(source), twice = stateModule.migratePlayer(once);
  assert.deepEqual(twice, once);
  assert.equal(once.v, 4);
  assert.deepEqual(once.stamps, source.stamps);
  assert.equal(once.codex.topic, 3);
  assert.deepEqual(once.goals, source.goals);
  assert.deepEqual(once.extraDomain, source.extraDomain);
  assert.equal(stateModule.codexDiscoveryState(once.codex.discovery, "ww", "creature", 2), 2);
  const worldV3 = { v: 3, journals: { a: { state: "terminal" } }, journalOrder: ["a"], structures: { s: 1 }, quarantine: ["q"], cells: { c: 1 }, devices: { d: 1 }, sequence: 9, encounters: { active: { e: 1 }, terminal: { t: 1 } }, extraWorld: true };
  const worldOnce = stateModule.migrateWorld(worldV3);
  assert.deepEqual(stateModule.migrateWorld(worldOnce), worldOnce);
  assert.deepEqual(worldOnce, { ...worldV3, v: 4 });
});

test("v4 reopen is canonical and malformed or unknown discovery data is bounded away", () => {
  const source = stateModule.migratePlayer({ v: 4, stamps: ["x", "x"], codex: { topic: 2, discovery: { rv: 99, ww: { resource: "A".repeat(10), plant: "bad!", unknown: "ff" }, zz: { resource: "ff" } } }, goals: {} });
  assert.deepEqual(stateModule.migratePlayer(source), source);
  assert.deepEqual(source.stamps, ["x"]);
  assert.deepEqual(source.codex.discovery, { rv: 4, ww: { resource: "aaaaaaaaaa" } });
});

test("two-bit transitions are monotonic, duplicate-safe, and reject unknown coordinates", () => {
  let discovery = stateModule.normalizeCodexDiscovery();
  let result = stateModule.transitionCodexDiscovery(discovery, "ww", "creature", 2, 1);
  assert.equal(result.changed, true); discovery = result.discovery;
  assert.equal(stateModule.codexDiscoveryState(discovery, "ww", "creature", 2), 1);
  result = stateModule.transitionCodexDiscovery(discovery, "ww", "creature", 2, 1); assert.equal(result.changed, false);
  result = stateModule.transitionCodexDiscovery(discovery, "ww", "creature", 2, 2); assert.equal(result.changed, true); discovery = result.discovery;
  result = stateModule.transitionCodexDiscovery(discovery, "ww", "creature", 2, 1); assert.equal(result.changed, false);
  assert.equal(stateModule.codexDiscoveryState(discovery, "ww", "creature", 2), 2);
  for (const args of [["bad", "creature", 0, 2], ["ww", "bad", 0, 2], ["ww", "resource", 20, 2], ["ww", "resource", 0, 3]]) {
    assert.equal(stateModule.transitionCodexDiscovery(discovery, ...args).changed, false);
  }
});

test("four fully populated regions remain compact under the player byte budget", () => {
  let discovery = stateModule.normalizeCodexDiscovery();
  for (const region of stateModule.CODEX_DISCOVERY_REGIONS) {
    for (const [category, cap] of Object.entries(stateModule.CODEX_CATEGORY_CAPS)) {
      for (let index = 0; index < cap; index++) discovery = stateModule.transitionCodexDiscovery(discovery, region, category, index, 2).discovery;
    }
  }
  const discoveryBytes = JSON.stringify(discovery).length;
  assert.equal(discoveryBytes, extensionMap.compact_v4_extension.fully_populated_four_region_discovery_json_bytes);
  assert.ok(discoveryBytes < COMBINED_BUDGETS.playerBytes * 0.08, discoveryBytes);
  const player = stateModule.migratePlayer({ v: 3, stamps: Array.from({ length: COMBINED_BUDGETS.discoveries }, (_, index) => `s:${index}`), codex: { topic: 4, discovery }, goals: {} });
  assert.ok(JSON.stringify(player).length < COMBINED_BUDGETS.playerBytes);
  assert.equal(Object.keys(discovery).length, 5);
});

test("Codex service translates known events silently and rejects duplicates and unknown IDs", () => {
  let playerRecord = stateModule.migratePlayer({ v: 3, stamps: [], codex: { topic: 0 }, goals: {} });
  const calls = [];
  const state = {
    playerState: () => structuredClone(playerRecord),
    transitionCodex: (_player, region, category, index, value) => {
      calls.push([region, category, index, value]);
      const result = stateModule.transitionCodexDiscovery(playerRecord.codex.discovery, region, category, index, value);
      if (result.changed) playerRecord.codex.discovery = result.discovery;
      return result.changed;
    },
    stamp: () => true, savePlayer: () => true,
  };
  const messages = [], player = { id: "p", isSneaking: false, sendMessage: message => messages.push(message) };
  const codex = createCodexService({ state });
  const observed = "codex:ww:creature:mosskip_buck:observed", defeated = "codex_detail:ww:creature:mosskip_buck:defeated";
  assert.equal(codex.discover(player, observed), true);
  assert.equal(codex.discover(player, observed), false);
  assert.equal(codex.discover(player, defeated), true);
  assert.equal(codex.discover(player, "codex:ww:unknown"), false);
  assert.equal(messages.length, 0);
  assert.deepEqual(calls.map(call => call[3]), [1, 1, 1, 1, 1, 2]);
});

test("bounded inventory reconciliation completes exact Ashen first-owned entries", () => {
  let playerRecord = stateModule.migratePlayer({ v: 4, stamps: [], codex: { topic: 0 }, goals: {} });
  const state = {
    playerState: () => structuredClone(playerRecord),
    transitionCodex: (_player, region, category, index, value) => {
      const result = stateModule.transitionCodexDiscovery(playerRecord.codex.discovery, region, category, index, value);
      if (result.changed) playerRecord.codex.discovery = result.discovery;
      return result.changed;
    },
    stamp: () => true, savePlayer: () => true,
  };
  const items = [{ typeId: "aionbound:smolder_bark" }, { typeId: "aionbound:basalt_hammer" }];
  const player = { getComponent: () => ({ container: { size: 2, getItem: slot => items[slot] } }) };
  const codex = createCodexService({ state });
  assert.equal(codex.reconcileOwnedItems(player), 2);
  assert.equal(stateModule.codexDiscoveryState(playerRecord.codex.discovery, "ah", "resource", 0), 2);
  assert.equal(stateModule.codexDiscoveryState(playerRecord.codex.discovery, "ah", "equipment", 0), 2);
  assert.equal(stateModule.codexDiscoveryState(playerRecord.codex.discovery, "ah", "progression", 0), 1);
  assert.equal(codex.reconcileOwnedItems(player), 0);
});

test("existing owned-item reconciliation completes all twenty Whisperwood craft-output pages without a new subscription", () => {
  let playerRecord = stateModule.migratePlayer({ v: 4, stamps: [], codex: { topic: 0 }, goals: {} });
  const state = {
    playerState: () => structuredClone(playerRecord),
    transitionCodex: (_player, region, category, index, value) => {
      const result = stateModule.transitionCodexDiscovery(playerRecord.codex.discovery, region, category, index, value);
      if (result.changed) playerRecord.codex.discovery = result.discovery;
      return result.changed;
    },
    stamp: () => true, savePlayer: () => true,
  };
  const craftOnly = extensionMap.entries.equipment.filter(entry => entry.discovery_events[0].action === "successful_craft_output");
  assert.equal(craftOnly.length, 20);
  const items = craftOnly.map(entry => ({ typeId: entry.runtime_id }));
  const player = { getComponent: () => ({ container: { size: items.length, getItem: slot => items[slot] } }) };
  const codex = createCodexService({ state });

  assert.deepEqual([
    codex.reconcileOwnedItems(player),
    codex.reconcileOwnedItems(player),
    codex.reconcileOwnedItems(player),
    codex.reconcileOwnedItems(player),
  ], [8, 8, 4, 0]);
  for (const entry of craftOnly) {
    assert.equal(stateModule.codexDiscoveryState(playerRecord.codex.discovery, "ww", "equipment", entry.category_index), 2, entry.id);
  }
});

test("state service reads v3 once, writes v4, and reopens the v4 value", () => {
  const properties = new Map([[catalog.IDS.oldPlayerV3, JSON.stringify({ v: 3, stamps: ["legacy"], codex: { topic: 4 }, goals: { arsenal: true } })]]);
  const writes = [];
  const player = { id: "p", getDynamicProperty: id => properties.get(id), setDynamicProperty: (id, value) => { writes.push([id, value]); properties.set(id, value); } };
  const world = { getDynamicProperty: () => undefined, setDynamicProperty() {} };
  const service = stateModule.createStateService({ world, system: { currentTick: 0 } });
  const first = service.playerState(player), reopened = service.playerState(player);
  assert.equal(first.v, 4); assert.deepEqual(reopened, first);
  assert.equal(writes.length, 1); assert.equal(writes[0][0], catalog.IDS.player);
});
