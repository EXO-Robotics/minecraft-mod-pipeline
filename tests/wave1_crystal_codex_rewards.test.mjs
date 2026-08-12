import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { CRYSTAL_CODEX_ENTRIES } from "../behavior_pack/scripts/wave1_codex_crystal_data.js";
import { WAVE1_CODEX_ENTRIES, WAVE1_CODEX_EVENT_INDEX, WAVE1_CODEX_REGISTRY_VERSION } from "../behavior_pack/scripts/wave1_codex_data.js";
import { createCodexService } from "../behavior_pack/scripts/codex.js";
import { migratePlayer, transitionCodexDiscovery } from "../behavior_pack/scripts/state.js";
import { CRYSTAL_REWARD_CONTRACT, PEARL_DEPTHS_CACHE_TABLE, PEARL_DEPTHS_MATERIAL_TABLE } from "../behavior_pack/scripts/crystal_reward_data.js";
import { createCrystalRewardHooks, identifyCrystalStructureActivation, rollCrystalRewardTable } from "../behavior_pack/scripts/crystal_rewards.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MAP = JSON.parse(await readFile(resolve(ROOT, "engineering/crystal-marsh-intake/codex/CRYSTAL_CODEX_PROGRESSION_INTAKE_MAP.json")));

test("exact 64-row Crystal append preserves the 140-row prefix and every local address", () => {
  assert.equal(WAVE1_CODEX_REGISTRY_VERSION, 5); assert.equal(WAVE1_CODEX_ENTRIES.length, 254); assert.equal(CRYSTAL_CODEX_ENTRIES.length, 64);
  assert.deepEqual(WAVE1_CODEX_ENTRIES.slice(140, 204), CRYSTAL_CODEX_ENTRIES);
  const sourceRows = [...MAP.packet003_entries, ...MAP.packet006_direct_equipment_pages, MAP.pearl_depths, ...MAP.progression_pages];
  for (let index = 0; index < sourceRows.length; index++) {
    const source = sourceRows[index], entry = CRYSTAL_CODEX_ENTRIES[index];
    assert.equal(source.global_append_ordinal, index + 140, source.id); assert.equal(entry.id, source.id); assert.equal(entry.categoryIndex, source.category_index);
    const routes = source.discovery_routes ?? source.events;
    assert.deepEqual(entry.events.map(row => row.id), routes.map(row => row.id), source.id);
  }
});

test("Crystal discovery auto-opens its chapter and the observatory completes only the Codex rumor", () => {
  let record = migratePlayer({});
  const state = { playerState: () => structuredClone(record), savePlayer: (_player, value) => { record = structuredClone(value); return true; }, transitionCodex: (_player, region, category, index, requested) => {
    const result = transitionCodexDiscovery(record.codex.discovery, region, category, index, requested); if (result.changed) record.codex.discovery = result.discovery; return result.changed;
  } };
  const codex = createCodexService({ state }), player = { id: "p" };
  assert.equal(codex.discover(player, "codex:cm:structure:flooded_dock:visited"), true);
  const chapter = WAVE1_CODEX_EVENT_INDEX["codex:cm:progression:crystal_marsh_chapter:entered"];
  assert.equal(record.codex.discovery.cm.progression, "01"); assert.equal(chapter.state, 1);
  assert.equal(codex.discover(player, "codex:cm:progression:skyreach_rumor:ruined_observatory_visited"), true);
  assert.equal(record.codex.discovery.cm.progression, "09");
});

function jsonTable(table) {
  return { pools: table.pools.map(pool => ({ rolls: pool.rolls[0] === pool.rolls[1] ? pool.rolls[0] : { min: pool.rolls[0], max: pool.rolls[1] }, entries: pool.entries.map(entry => ({
    type: "item", name: entry.typeId, weight: entry.weight, ...(entry.min === 1 && entry.max === 1 ? {} : { functions: [{ function: "set_count", count: { min: entry.min, max: entry.max } }] }),
  })) })) };
}

test("reward mirrors are byte-semantic equivalents of the protected economy tables", async () => {
  assert.equal(CRYSTAL_REWARD_CONTRACT.materialTablePath, "loot_tables/encounters/crystal/pearl_depths_materials.json");
  assert.equal(CRYSTAL_REWARD_CONTRACT.arenaCacheTablePath, "loot_tables/chests/crystal/pearl_depths.json");
  assert.deepEqual(jsonTable(PEARL_DEPTHS_MATERIAL_TABLE), JSON.parse(await readFile(resolve(ROOT, `behavior_pack/${CRYSTAL_REWARD_CONTRACT.materialTablePath}`))));
  assert.deepEqual(jsonTable(PEARL_DEPTHS_CACHE_TABLE), JSON.parse(await readFile(resolve(ROOT, `behavior_pack/${CRYSTAL_REWARD_CONTRACT.arenaCacheTablePath}`))));
  assert.deepEqual(CRYSTAL_REWARD_CONTRACT.progressionSubstitutes, []);
  assert.equal(rollCrystalRewardTable(PEARL_DEPTHS_MATERIAL_TABLE, () => 0).length, 3);
});

test("deep-pool signature and synchronous pre-clear cache guard are bounded", () => {
  const blocks = new Map(), key = value => `${value.x},${value.y},${value.z}`, inventory = { size: 27, getItem: () => undefined, setItem() {} };
  const dimension = { id: "minecraft:overworld", getBlock(location) { return blocks.get(key(location)); }, spawnItem() {} };
  const put = (typeId, location, withInventory = false) => { const block = { typeId, location, dimension, getComponent: id => withInventory && id === "minecraft:inventory" ? { container: inventory } : undefined }; blocks.set(key(location), block); return block; };
  const anchor = put("minecraft:lodestone", { x: 0, y: 64, z: 0 }); const barrel = put("minecraft:barrel", { x: -4, y: 65, z: -3 }, true);
  put("aionbound:algae_block", { x: -3, y: 64, z: -3 }); put("aionbound:crystal_stone", { x: 6, y: 65, z: 4 });
  assert.equal(identifyCrystalStructureActivation(anchor).structure, "deep_pool_entrance");
  let worldState = { encounters: { terminal: {} } };
  const hooks = createCrystalRewardHooks({ ItemStack: class { constructor(typeId, amount) { this.typeId = typeId; this.amount = amount; } }, state: { worldState: () => structuredClone(worldState) }, random: () => 0 });
  const event = { block: barrel, player: { dimension }, cancel: false }; assert.equal(hooks.guardArenaCacheInteraction(event), true); assert.equal(event.cancel, true);
  worldState.encounters.terminal["aionbound.encounter.pearl_depths.completed.v1"] = { completed: true, v: 1 };
  event.cancel = false; assert.equal(hooks.guardArenaCacheInteraction(event), false); assert.equal(event.cancel, false);
});

test("shared runtime composition is unconditional and does not activate dormant Ashen services", async () => {
  const source = await readFile(resolve(ROOT, "behavior_pack/scripts/runtime.js"), "utf8");
  for (const fragment of ["pearlDepths.reconcile()", "pearlDepths.tick()", "pearlDepths.bossDeath(event)", "pearlDepths.blockInteraction(event.player, event.block)"]) assert.ok(source.includes(fragment), fragment);
  assert.equal(source.includes("createKilnSkyService"), false); assert.equal(source.includes("createAshenEquipmentRoleService"), false);
  const death = source.slice(source.indexOf("afterEvents.entityDie.subscribe"), source.indexOf("platform.system.runInterval"));
  assert.equal(death.includes("if (!pearlDepths.bossDeath"), false);
});
