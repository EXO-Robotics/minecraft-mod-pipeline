import { WHISPERWOOD_CODEX_EXTENSION_ENTRIES } from "./wave1_codex_extension_data.js";
import { ASHEN_CODEX_ENTRIES } from "./wave1_codex_ashen_data.js";
import { CRYSTAL_CODEX_ENTRIES } from "./wave1_codex_crystal_data.js";
import { SKYREACH_CODEX_ENTRIES } from "./wave1_codex_skyreach_data.js";
import { SKYREACH_CODEX_RUNTIME_ENTRIES } from "./wave1_codex_skyreach_runtime_data.js";

// Machine-bound from the Whisperwood Codex implementation maps. This module
// contains only SAFE_NOW identity and discovery-transition data. Acquisition
// guidance whose live completion is blocked remains outside the runtime.
export const WAVE1_CODEX_REGISTRY_VERSION = 5;
const event = (id, state, kind) => Object.freeze({ id, state, event: kind });
const entry = (id, kind, events) => Object.freeze({
  id,
  warehouseId: id,
  runtimeId: `aionbound:${id}`,
  region: "ww",
  kind,
  category: kind === "block" ? "resource" : kind,
  events: Object.freeze(events),
});

export const WHISPERWOOD_CODEX_FOUNDATION_ENTRIES = Object.freeze([
  entry("whisper_bark", "resource", [event("codex:ww:resource:whisper_bark:harvested", 2, "harvested")]),
  entry("moss_resin", "resource", [event("codex:ww:resource:moss_resin:harvested", 2, "harvested")]),
  entry("glow_spore", "resource", [event("codex:ww:resource:glow_spore:harvested", 2, "harvested")]),
  entry("hollow_amber", "resource", [event("codex:ww:resource:hollow_amber:harvested", 2, "harvested")]),
  entry("lantern_fur", "resource", [event("codex:ww:resource:lantern_fur:harvested", 2, "harvested")]),
  entry("moon_sap", "resource", [event("codex:ww:resource:moon_sap:harvested", 2, "harvested")]),
  entry("root_heart", "resource", [event("codex:ww:resource:root_heart:harvested", 2, "harvested")]),
  entry("briar_antler", "resource", [event("codex:ww:resource:briar_antler:harvested", 2, "harvested")]),
  entry("widow_silk", "resource", [event("codex:ww:resource:widow_silk:harvested", 2, "harvested")]),
  entry("ancient_acorn", "resource", [event("codex:ww:resource:ancient_acorn:harvested", 2, "harvested")]),
  entry("whisperwood_log", "block", [event("codex:ww:block:whisperwood_log:harvested", 2, "harvested")]),
  entry("stripped_whisperwood_log", "block", [event("codex:ww:block:stripped_whisperwood_log:crafted", 2, "crafted")]),
  entry("whisperwood_wood", "block", [event("codex:ww:block:whisperwood_wood:crafted", 2, "crafted")]),
  entry("whisperwood_planks", "block", [event("codex:ww:block:whisperwood_planks:crafted", 2, "crafted")]),
  entry("whisperwood_leaves", "block", [event("codex:ww:block:whisperwood_leaves:harvested", 2, "harvested")]),
  entry("whisperwood_sapling", "block", [event("codex:ww:block:whisperwood_sapling:harvested", 2, "harvested")]),
  entry("whisperwood_roots", "block", [event("codex:ww:block:whisperwood_roots:harvested", 2, "harvested")]),
  entry("moss_bark", "block", [event("codex:ww:block:moss_bark:harvested", 2, "harvested")]),
  entry("hollow_wood", "block", [event("codex:ww:block:hollow_wood:harvested", 2, "harvested")]),
  entry("forest_brick", "block", [event("codex:ww:block:forest_brick:crafted", 2, "crafted")]),
  entry("star_grass", "plant", [event("codex:ww:plant:star_grass:harvested", 2, "harvested")]),
  entry("whisper_fern", "plant", [event("codex:ww:plant:whisper_fern:harvested", 2, "harvested")]),
  entry("pale_reed", "plant", [event("codex:ww:plant:pale_reed:harvested", 2, "harvested")]),
  entry("glow_moss", "plant", [event("codex:ww:plant:glow_moss:harvested", 2, "harvested")]),
  entry("mooncap_mushroom", "plant", [event("codex:ww:plant:mooncap_mushroom:harvested", 2, "harvested")]),
  entry("lantern_bloom", "plant", [event("codex:ww:plant:lantern_bloom:harvested", 2, "harvested")]),
  entry("hollow_lily", "plant", [event("codex:ww:plant:hollow_lily:harvested", 2, "harvested")]),
  entry("root_flower", "plant", [event("codex:ww:plant:root_flower:harvested", 2, "harvested")]),
  entry("briar_vine", "plant", [event("codex:ww:plant:briar_vine:harvested", 2, "harvested")]),
  entry("ember_thistle", "plant", [event("codex:ww:plant:ember_thistle:harvested", 2, "harvested")]),
  entry("mosskip_fawn", "creature", [event("codex:ww:creature:mosskip_fawn:observed", 1, "observe_nearby")]),
  entry("mosskip_doe", "creature", [event("codex:ww:creature:mosskip_doe:observed", 1, "observe_nearby")]),
  entry("mosskip_buck", "creature", [event("codex:ww:creature:mosskip_buck:observed", 1, "observe_nearby"), event("codex_detail:ww:creature:mosskip_buck:defeated", 2, "defeat")]),
  entry("lantern_hare", "creature", [event("codex:ww:creature:lantern_hare:observed", 1, "observe_nearby")]),
  entry("rootback_boar", "creature", [event("codex:ww:creature:rootback_boar:observed", 1, "observe_nearby"), event("codex_detail:ww:creature:rootback_boar:defeated", 2, "defeat")]),
  entry("briar_elk", "creature", [event("codex:ww:creature:briar_elk:observed", 1, "observe_nearby"), event("codex_detail:ww:creature:briar_elk:defeated", 2, "defeat")]),
  entry("rot_wolf", "creature", [event("codex:ww:creature:rot_wolf:defeated", 2, "defeat")]),
  entry("thorn_stalker", "creature", [event("codex:ww:creature:thorn_stalker:defeated", 2, "defeat")]),
  entry("hollow_widow_spider", "creature", [event("codex:ww:creature:hollow_widow_spider:defeated", 2, "defeat")]),
  entry("bark_wraith", "creature", [event("codex:ww:creature:bark_wraith:defeated", 2, "defeat")]),
]);

// Append-only migration rule: never reorder the original forty entries or the
// mapped extension categories. Category-local indices are independently bound
// by the maps and checked below.
export const WHISPERWOOD_CODEX_ENTRIES = Object.freeze([
  ...WHISPERWOOD_CODEX_FOUNDATION_ENTRIES,
  ...WHISPERWOOD_CODEX_EXTENSION_ENTRIES,
]);

export const WAVE1_CODEX_ENTRIES = Object.freeze([
  ...WHISPERWOOD_CODEX_ENTRIES,
  ...ASHEN_CODEX_ENTRIES,
  ...CRYSTAL_CODEX_ENTRIES,
  ...SKYREACH_CODEX_ENTRIES,
  ...SKYREACH_CODEX_RUNTIME_ENTRIES,
]);

const eventIndex = {};
const categoryCounts = Object.create(null);
for (let index = 0; index < WAVE1_CODEX_ENTRIES.length; index++) {
  const entryData = WAVE1_CODEX_ENTRIES[index];
  const categoryKey = `${entryData.region}:${entryData.category}`;
  const categoryIndex = categoryCounts[categoryKey] ?? 0;
  if (Number.isInteger(entryData.categoryIndex) && entryData.categoryIndex !== categoryIndex) {
    throw new Error(`Codex category index mismatch: ${entryData.category}:${entryData.id}`);
  }
  categoryCounts[categoryKey] = categoryIndex + 1;
  for (const transition of entryData.events) {
    if (Object.prototype.hasOwnProperty.call(eventIndex, transition.id)) throw new Error(`Duplicate Codex event: ${transition.id}`);
    eventIndex[transition.id] = Object.freeze({ region: entryData.region, category: entryData.category, index: categoryIndex, state: transition.state, event: transition.event ?? transition.action });
  }
}
export const WAVE1_CODEX_EVENT_INDEX = Object.freeze(eventIndex);
