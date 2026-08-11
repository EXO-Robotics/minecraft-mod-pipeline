import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  THORN_COURT_CACHE_OFFSET,
  THORN_COURT_CACHE_TABLE,
  THORN_COURT_MATERIAL_POOLS,
  createWhisperwoodRewardHooks,
  rollThornCourtCache,
  rollThornCourtMaterials,
} from "../behavior_pack/scripts/whisperwood_rewards.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
class FakeItemStack { constructor(typeId, amount) { this.typeId = typeId; this.amount = amount; } }
const sequence = values => { let index = 0; return () => values[index++] ?? 0; };
const countRange = entry => {
  const value = entry.functions?.find(fn => fn.function === "set_count")?.count ?? 1;
  return typeof value === "number" ? [value, value] : [value.min, value.max];
};

test("source material and cache mirrors close exactly over protected loot JSON", async () => {
  const materials = JSON.parse(await readFile(resolve(ROOT, "behavior_pack/loot_tables/encounters/whisperwood/thorn_court_materials.json")));
  const materialMirror = materials.pools.map(pool => {
    const entry = pool.entries[0], [min, max] = countRange(entry);
    return { typeId: entry.name, min, max, chance: pool.conditions?.find(condition => condition.condition === "random_chance")?.chance ?? 1 };
  });
  assert.deepEqual(materialMirror, THORN_COURT_MATERIAL_POOLS);

  const cache = JSON.parse(await readFile(resolve(ROOT, "behavior_pack/loot_tables/chests/whisperwood/thorn_court.json")));
  assert.deepEqual(cache.pools.map(pool => pool.rolls), [2, 3]);
  assert.deepEqual(cache.pools[0].entries, cache.pools[1].entries);
  const cacheMirror = cache.pools[0].entries.map(entry => {
    const [min, max] = countRange(entry);
    return { typeId: entry.name, weight: entry.weight, min, max };
  });
  assert.equal(cache.pools.reduce((sum, pool) => sum + pool.rolls, 0), THORN_COURT_CACHE_TABLE.rolls);
  assert.deepEqual(cacheMirror, THORN_COURT_CACHE_TABLE.entries);
  assert.equal([...THORN_COURT_MATERIAL_POOLS, ...THORN_COURT_CACHE_TABLE.entries].some(entry => entry.typeId === "aionbound:thorn_stalker_skull"), false);
});

test("injected randomness independently rolls each participant package and five-roll cache", () => {
  const materials = rollThornCourtMaterials(sequence([0, .999, .999, .49, 0, .5, .11, 0]));
  assert.deepEqual(materials, [
    { typeId: "aionbound:widow_silk", amount: 1 },
    { typeId: "aionbound:thorn_barb", amount: 3 },
    { typeId: "aionbound:hollow_amber", amount: 2 },
    { typeId: "aionbound:root_heart", amount: 1 },
    { typeId: "aionbound:ancient_acorn", amount: 1 },
  ]);
  const cache = rollThornCourtCache(sequence([0, 0, .4, .999, .7, 0, .9, .999, .999, 0]));
  assert.deepEqual(cache, [
    { typeId: "aionbound:widow_silk", amount: 1 },
    { typeId: "aionbound:thorn_barb", amount: 2 },
    { typeId: "aionbound:hollow_amber", amount: 1 },
    { typeId: "aionbound:root_heart", amount: 2 },
    { typeId: "aionbound:ancient_acorn", amount: 1 },
  ]);
});

function cacheHarness(rotatedOffset = { x: 2, y: 0, z: 2 }) {
  const center = { x: 10, y: 64, z: 10 }, barrelLocation = {
    x: center.x + rotatedOffset.x, y: center.y + rotatedOffset.y, z: center.z + rotatedOffset.z,
  };
  const slots = Array(27), locKey = value => `${value.x},${value.y},${value.z}`;
  const container = {
    size: slots.length,
    getItem(slot) { return slots[slot]; },
    setItem(slot, item) { slots[slot] = item; },
  };
  const dimension = {
    id: "minecraft:overworld", blocks: new Map(),
    getBlock(location) { return this.blocks.get(locKey(location)); },
  };
  const block = (typeId, location, component) => ({ typeId, location: { ...location }, dimension, getComponent: id => id === "minecraft:inventory" ? component : undefined });
  const barrel = block("minecraft:barrel", barrelLocation, { container });
  dimension.blocks.set(locKey(center), block("minecraft:lodestone", center));
  dimension.blocks.set(locKey({ x: center.x, y: center.y + 1, z: center.z }), block("aionbound:hollow_wood", { x: center.x, y: center.y + 1, z: center.z }));
  dimension.blocks.set(locKey(barrelLocation), barrel);
  return { center, barrel, container, slots, dimension };
}

test("exact rotated Ancient Totem cache is locked empty pre-clear and command-free populated post-clear", () => {
  assert.deepEqual(THORN_COURT_CACHE_OFFSET, { x: -2, y: 0, z: 2 });
  const h = cacheHarness(), hooks = createWhisperwoodRewardHooks({ ItemStack: FakeItemStack, random: () => 0 });
  const pre = { block: h.barrel, player: { dimension: h.dimension }, cancel: false };
  assert.equal(hooks.guardArenaCacheInteraction(pre), true); assert.equal(pre.cancel, true);
  assert.equal(hooks.openArenaChest({ dimension: h.dimension, center: h.center }), true);
  assert.equal(h.slots.filter(Boolean).length, 5);
  assert.equal(h.slots.filter(Boolean).every(item => item.typeId === "aionbound:widow_silk" && item.amount === 1), true);
  const post = { block: h.barrel, player: { dimension: h.dimension }, cancel: false };
  assert.equal(hooks.guardArenaCacheInteraction(post), false); assert.equal(post.cancel, false);
});

test("cache refill is repeatable but refuses to erase unknown player storage", () => {
  const h = cacheHarness({ x: -2, y: 0, z: -2 }), hooks = createWhisperwoodRewardHooks({ ItemStack: FakeItemStack, random: () => .99 });
  assert.equal(hooks.openArenaChest({ dimension: h.dimension, center: h.center }), true);
  assert.equal(hooks.openArenaChest({ dimension: h.dimension, center: h.center }), true);
  h.slots[10] = new FakeItemStack("minecraft:diamond", 1);
  assert.equal(hooks.openArenaChest({ dimension: h.dimension, center: h.center }), false);
  assert.equal(h.slots[10].typeId, "minecraft:diamond");
});

test("participant delivery prefers owned inventory and only drops overflow at that participant", () => {
  const accepted = [], overflow = [], container = { addItem(item) { accepted.push(item); return item.typeId === "aionbound:root_heart" ? item : undefined; } };
  const player = {
    location: { x: 4, y: 70, z: 9 },
    dimension: { spawnItem(item, location) { overflow.push([item, location]); } },
    getComponent: id => id === "minecraft:inventory" ? { container } : undefined,
  };
  const hooks = createWhisperwoodRewardHooks({ ItemStack: FakeItemStack, random: () => 0 });
  assert.equal(hooks.grantMaterialPackage(player), true);
  assert.equal(accepted.length, 6); assert.equal(overflow.length, 1);
  assert.equal(overflow[0][0].typeId, "aionbound:root_heart"); assert.deepEqual(overflow[0][1], player.location);
});

test("runtime composes the shipped bridge through the existing platform hook seam", async () => {
  const runtime = await readFile(resolve(ROOT, "behavior_pack/scripts/runtime.js"), "utf8");
  assert.equal(runtime.includes("platform.thornCourtRewardHooks ?? createWhisperwoodRewardHooks"), true);
  assert.equal(runtime.includes("thornCourtRewardHooks.guardArenaCacheInteraction?.(event)"), true);
  assert.ok(runtime.indexOf("thornCourtRewardHooks.guardArenaCacheInteraction?.(event)") < runtime.indexOf("callback(() => {", runtime.indexOf("playerInteractWithBlock.subscribe")));
  for (const forbidden of ["runCommand", "runCommandAsync", "loot spawn", "aionbound:thorn_stalker_skull"]) assert.equal(runtime.includes(forbidden), false);
});
