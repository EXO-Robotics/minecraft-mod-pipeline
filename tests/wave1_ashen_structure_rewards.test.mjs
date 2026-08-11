import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  ASHEN_STRUCTURE_CHEST_TABLES,
  ASHEN_STRUCTURE_SIGNATURES,
  EMBER_FORGE_CACHE_OFFSET,
  createAshenStructureRewardHooks,
  identifyAshenStructureActivation,
  rollAshenStructureTable,
} from "../behavior_pack/scripts/ashen_structure_rewards.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
class FakeItemStack { constructor(typeId, amount) { this.typeId = typeId; this.amount = amount; } }
const countRange = entry => {
  const value = entry.functions?.find(fn => fn.function === "set_count")?.count ?? 1;
  return typeof value === "number" ? [value, value] : [value.min, value.max];
};

test("generated runtime tables mirror all exact JSON tables", async () => {
  for (const [tableId, table] of Object.entries(ASHEN_STRUCTURE_CHEST_TABLES)) {
    const document = JSON.parse(await readFile(resolve(ROOT, `behavior_pack/loot_tables/chests/ashen/${tableId}.json`)));
    const mirror = document.pools.map(pool => ({
      rolls: typeof pool.rolls === "number" ? [pool.rolls, pool.rolls] : [pool.rolls.min, pool.rolls.max],
      entries: pool.entries.map(entry => {
        const [min, max] = countRange(entry);
        return { typeId: entry.name, weight: entry.weight, min, max };
      }),
    }));
    assert.deepEqual(mirror, [
      { rolls: [table.guaranteedRolls, table.guaranteedRolls], entries: table.guaranteed },
      { rolls: table.choiceRolls, entries: table.choice },
    ], tableId);
  }
});

test("rolls stay within each ratified band and exclude protected identities", () => {
  for (const [tableId, table] of Object.entries(ASHEN_STRUCTURE_CHEST_TABLES)) {
    for (const random of [() => 0, () => .999999]) {
      const result = rollAshenStructureTable(tableId, random);
      assert.ok(result.length >= table.guaranteedRolls + table.choiceRolls[0], tableId);
      assert.ok(result.length <= table.guaranteedRolls + table.choiceRolls[1], tableId);
      assert.equal(result.some(item => ["aionbound:ash_drake_horn", "aionbound:ember_forge_core"].includes(item.typeId)), false);
    }
  }
});

const key = value => `${value.x},${value.y},${value.z}`;
const rotate = ({ x, y, z }, index) => [
  { x, y, z }, { x: z, y, z: -x }, { x: -x, y, z: -z }, { x: -z, y, z: x },
][index];

function forgeHarness(rotation = 0) {
  const signature = ASHEN_STRUCTURE_SIGNATURES.find(value => value.anchor_id === "ember_forge_arena");
  const centerLocation = { x: 40, y: 70, z: 20 }, blocks = new Map(), slots = Array(27);
  const container = { size: slots.length, getItem(slot) { return slots[slot]; }, setItem(slot, item) { slots[slot] = item; } };
  const dimension = { id: "minecraft:overworld", getBlock(location) { return blocks.get(key(location)); } };
  const block = (typeId, location, component) => ({ typeId, location: { ...location }, dimension, getComponent: id => id === "minecraft:inventory" ? component : undefined });
  const center = block(signature.anchor_type, centerLocation);
  blocks.set(key(centerLocation), center);
  for (const probe of signature.probes) {
    const offset = rotate({ x: probe.offset[0], y: probe.offset[1], z: probe.offset[2] }, rotation);
    const location = { x: centerLocation.x + offset.x, y: centerLocation.y + offset.y, z: centerLocation.z + offset.z };
    blocks.set(key(location), block(probe.expected_block, location));
  }
  const cacheOffset = rotate(EMBER_FORGE_CACHE_OFFSET, rotation);
  const cacheLocation = { x: centerLocation.x + cacheOffset.x, y: centerLocation.y, z: centerLocation.z + cacheOffset.z };
  const barrel = block("minecraft:barrel", cacheLocation, { container });
  blocks.set(key(cacheLocation), barrel);
  return { center, barrel, container, slots, dimension };
}

test("exact Ember Forge cache is empty and guarded before a valid Kiln Sky clear", () => {
  const harness = forgeHarness(1), hooks = createAshenStructureRewardHooks({ ItemStack: FakeItemStack, random: () => 0 });
  const event = { block: harness.barrel, player: { dimension: harness.dimension }, cancel: false };
  assert.equal(hooks.guardArenaCacheInteraction(event), true);
  assert.equal(event.cancel, true);
  assert.equal(hooks.openArenaCache({ dimension: harness.dimension, center: harness.center.location, validClear: false }), false);
  assert.equal(harness.slots.filter(Boolean).length, 0);
  assert.equal(hooks.openArenaCache({ dimension: harness.dimension, center: harness.center.location, validClear: true }), true);
  assert.ok(harness.slots.filter(Boolean).length >= 4 && harness.slots.filter(Boolean).length <= 6);
  assert.equal(harness.slots.filter(Boolean).some(item => ["aionbound:ash_drake_horn", "aionbound:ember_forge_core"].includes(item.typeId)), false);
  const post = { block: harness.barrel, player: { dimension: harness.dimension }, cancel: false };
  assert.equal(hooks.guardArenaCacheInteraction(post), false);
  assert.equal(post.cancel, false);
});

test("arena cache refuses to erase unknown player storage", () => {
  const harness = forgeHarness(), hooks = createAshenStructureRewardHooks({ ItemStack: FakeItemStack, random: () => 0 });
  harness.slots[4] = new FakeItemStack("minecraft:diamond", 1);
  assert.equal(hooks.openArenaCache({ dimension: harness.dimension, center: harness.center.location, validClear: true }), false);
  assert.equal(harness.slots[4].typeId, "minecraft:diamond");
});

test("ordinary bridge delivers inventory first and overflows at the owning player", () => {
  const accepted = [], overflow = [], player = {
    location: { x: 3, y: 80, z: 7 },
    dimension: { spawnItem(item, location) { overflow.push([item, location]); } },
    getComponent: id => id === "minecraft:inventory" ? { container: { addItem(item) { accepted.push(item); return accepted.length === 1 ? item : undefined; } } } : undefined,
  };
  const hooks = createAshenStructureRewardHooks({ ItemStack: FakeItemStack, random: () => 0 });
  assert.equal(hooks.grantTable(player, "burned_camp"), true);
  assert.equal(accepted.length, 2);
  assert.equal(overflow.length, 1);
  assert.deepEqual(overflow[0][1], player.location);
});

test("exact assembly signature identifies one activation and returns the stable stamp", () => {
  const harness = forgeHarness(3), activation = identifyAshenStructureActivation(harness.center);
  assert.equal(activation.structure, "ember_forge");
  assert.equal(activation.anchorId, "ember_forge_arena");
  assert.equal(activation.stamp, "aionbound.structure.ashen.ember_forge.discovered.v1");
});

test("runtime composes the command-free guard and discovery hook without claiming terminal ownership", async () => {
  const runtime = await readFile(resolve(ROOT, "behavior_pack/scripts/runtime.js"), "utf8");
  const bridge = await readFile(resolve(ROOT, "behavior_pack/scripts/ashen_structure_rewards.js"), "utf8");
  assert.equal(runtime.includes("platform.ashenStructureRewardHooks ?? createAshenStructureRewardHooks"), true);
  assert.equal(runtime.includes("ashenStructureRewardHooks.guardArenaCacheInteraction?.(event)"), true);
  assert.ok(runtime.indexOf("ashenStructureRewardHooks.guardArenaCacheInteraction?.(event)") < runtime.indexOf("callback(() => {", runtime.indexOf("playerInteractWithBlock.subscribe")));
  assert.equal(runtime.includes("state.stamp(event.player, activation.stamp)"), true);
  for (const source of [runtime, bridge]) for (const forbidden of ["runCommand", "runCommandAsync", "aionbound:ash_drake_horn", "aionbound:ember_forge_core"]) assert.equal(source.includes(forbidden), false);
  assert.equal(bridge.includes("bossDeath"), false);
});
