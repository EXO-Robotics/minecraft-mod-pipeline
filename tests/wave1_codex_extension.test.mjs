import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { WHISPERWOOD_CODEX_EXTENSION_ENTRIES } from "../behavior_pack/scripts/wave1_codex_extension_data.js";
import { WAVE1_CODEX_EVENT_INDEX, WAVE1_CODEX_REGISTRY_VERSION } from "../behavior_pack/scripts/wave1_codex_data.js";
import {
  CODEX_ENTRY_REGISTRY,
  CODEX_STRUCTURE_ACTIVATION_EVENTS,
  WHISPERWOOD_PROGRESSION_SITES,
  codexEventsForStructureActivation,
} from "../behavior_pack/scripts/catalog.js";
import { CODEX_CATEGORY_CAPS, STATE_VERSION, migratePlayer, transitionCodexDiscovery } from "../behavior_pack/scripts/state.js";
import { codexEntryBody, createCodexService } from "../behavior_pack/scripts/codex.js";
import { createStructureService } from "../behavior_pack/scripts/structures.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MAP = JSON.parse(await readFile(resolve(ROOT, "engineering/whisperwood-intake/codex-extension/WHISPERWOOD_CODEX_EXTENSION_MAP.json"), "utf8"));
const mappedEntries = ["structures", "equipment", "bosses", "progression"].flatMap(category => MAP.entries[category]);

test("generated Whisperwood extension remains exact after region append", () => {
  assert.equal(WAVE1_CODEX_REGISTRY_VERSION, 4);
  assert.equal(STATE_VERSION, 4);
  assert.equal(WHISPERWOOD_CODEX_EXTENSION_ENTRIES.length, 34);
  assert.equal(CODEX_ENTRY_REGISTRY.length, 204);
  assert.deepEqual(CODEX_CATEGORY_CAPS, MAP.compact_v4_extension.category_caps_after);
  assert.deepEqual(WHISPERWOOD_CODEX_EXTENSION_ENTRIES.map(entry => entry.id), mappedEntries.map(entry => entry.id));
  for (let index = 0; index < mappedEntries.length; index++) {
    const expected = mappedEntries[index], actual = WHISPERWOOD_CODEX_EXTENSION_ENTRIES[index];
    assert.deepEqual(actual.authorityText, expected.authority_text, expected.id);
    assert.deepEqual(actual.events.map(event => [event.id, event.state, event.action]), expected.discovery_events.map(event => [
      event.id,
      event.stage === "partial" ? 1 : 2,
      event.action,
    ]), expected.id);
  }
});

test("all structure activations are mapped while proximity remains unclaimed", () => {
  const structures = MAP.entries.structures;
  assert.equal(Object.keys(CODEX_STRUCTURE_ACTIVATION_EVENTS).length, 30);
  for (const entry of structures) {
    const activation = entry.discovery_events.find(event => event.action === "first_successful_activation");
    assert.deepEqual(codexEventsForStructureActivation(entry.id), [activation.id]);
    const proximity = entry.discovery_events.find(event => event.action === "recognized_structure_proximity");
    assert.ok(WAVE1_CODEX_EVENT_INDEX[proximity.id]);
  }
});

test("all ten authored anchors resolve under a quarter-turn without claiming loot", () => {
  const rotate = ({ x, z }) => ({ x: -z, z: x });
  for (const site of WHISPERWOOD_PROGRESSION_SITES) {
    const origin = { x: 100, y: 64, z: -30 }, blocks = new Map();
    const key = ({ x, y, z }) => `${x},${y},${z}`;
    blocks.set(key(origin), site.center);
    for (const signature of site.relativeSignatures) {
      const offset = rotate(signature);
      blocks.set(key({ x: origin.x + offset.x, y: origin.y + signature.y, z: origin.z + offset.z }), signature.typeId);
    }
    const dimension = { getBlock: location => ({ typeId: blocks.get(key(location)) ?? "minecraft:air", location }) };
    const stamps = [];
    const service = createStructureService({
      world: {}, system: { currentTick: 0 }, ItemStack: class {}, arbiter: { beginTick() {}, spend: () => true }, consumeOne: () => false,
      state: { stamp: (_player, stamp) => { stamps.push(stamp); return true; } },
    });
    const player = { id: "p", dimension };
    const activation = service.activateProgressionSite({ player, block: { typeId: site.center, location: origin } });
    assert.equal(activation?.site, site.id, site.id);
    assert.deepEqual(stamps, [site.stamp], site.id);
  }
});

test("craft-only equipment pages have no substituted possession trigger", () => {
  const craftOnly = MAP.entries.equipment.filter(entry => entry.discovery_events[0].action === "successful_craft_output");
  assert.equal(craftOnly.length, 20);
  for (const entry of craftOnly) {
    assert.equal(WAVE1_CODEX_EVENT_INDEX[entry.discovery_events[0].id].event, "successful_craft_output");
  }
  const skull = MAP.entries.equipment.find(entry => entry.id === "thorn_stalker_skull");
  assert.equal(skull.discovery_events[0].action, "valid_thorn_court_terminal_credit");
  assert.equal(skull.physical_item_progression_blocker, false);
});

test("Thorn Court phase notes are hidden at pull and exact at victory", () => {
  const boss = CODEX_ENTRY_REGISTRY.find(entry => entry.kind === "boss" && entry.id === "thorn_court");
  const partial = codexEntryBody(boss, 1), complete = codexEntryBody(boss, 2);
  for (const phase of boss.authorityText.phase_field_notes) {
    assert.equal(partial.includes(phase), false, phase);
    assert.equal(complete.includes(phase), true, phase);
  }
});

test("first Whisperwood discovery opens the chapter and durable seal credit completes it", () => {
  let record = migratePlayer({});
  const state = {
    transitionCodex: (_player, region, category, index, requested) => {
      const transition = transitionCodexDiscovery(record.codex.discovery, region, category, index, requested);
      if (transition.changed) record.codex.discovery = transition.discovery;
      return transition.changed;
    },
  };
  const codex = createCodexService({ state }), player = { id: "p" };
  assert.equal(codex.discover(player, "codex:ww:structure:lantern_post:activated"), true);
  const chapterPartial = WAVE1_CODEX_EVENT_INDEX["codex:ww:progression:whisperwood_chapter:entered"];
  assert.equal(record.codex.discovery.ww.progression, "01");
  assert.equal(chapterPartial.state, 1);
  assert.equal(codex.discover(player, "codex:ww:progression:whisperwood_chapter:seal_credit"), true);
  assert.equal(record.codex.discovery.ww.progression, "02");
});

test("runtime composes boss, skull, and chapter transitions before trophy fulfillment", async () => {
  const runtime = await readFile(resolve(ROOT, "behavior_pack/scripts/runtime.js"), "utf8");
  const boss = runtime.indexOf("codex:ww:boss:thorn_court:defeated");
  const skull = runtime.indexOf("codex:ww:equipment:thorn_stalker_skull:earned");
  const chapter = runtime.indexOf("codex:ww:progression:whisperwood_chapter:seal_credit");
  assert.ok(boss >= 0 && skull > boss && chapter > skull);
});

test("Ashen rumor is Codex state with the exact safe hint and no runtime item", async () => {
  const rumor = CODEX_ENTRY_REGISTRY.find(entry => entry.kind === "progression" && entry.id === "ashen_rumor");
  assert.equal(rumor.authorityText.safe_spoiler, "Heat waits east of the burned wagons.");
  assert.ok(codexEntryBody(rumor, 2).includes(rumor.authorityText.safe_spoiler));
  const runtime = await readFile(resolve(ROOT, "behavior_pack/scripts/runtime.js"), "utf8");
  assert.ok(runtime.includes("codex:ww:progression:ashen_rumor:broken_wagon_activated"));
  assert.equal(runtime.includes("map_scrap"), false);
});
