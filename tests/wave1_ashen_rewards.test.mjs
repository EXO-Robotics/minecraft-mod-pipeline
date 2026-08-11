import test from "node:test";
import assert from "node:assert/strict";
import { KILN_SKY_CACHE_ROLLS, KILN_SKY_CORE_CHANCE, createAshenRewardHooks, rollKilnSkyCache, rollKilnSkyParticipantPackage } from "../behavior_pack/scripts/ashen_rewards.js";

class FakeItemStack { constructor(typeId, amount) { this.typeId = typeId; this.amount = amount; } }
const sequence = values => { let i = 0; return () => values[i++] ?? 0; };

test("participant package uses ratified midpoint rolls and optional non-seal E midpoint", () => {
  assert.equal(KILN_SKY_CORE_CHANCE, .14);
  const without = rollKilnSkyParticipantPackage(sequence([0, .4, .8, .2, .14]));
  assert.deepEqual(without.map(x => x.amount), [2, 2, 2, 1]); assert.equal(without.some(x => x.typeId === "aionbound:ember_forge_core"), false);
  const withCore = rollKilnSkyParticipantPackage(sequence([0, 0, 0, 0, .139]));
  assert.equal(withCore.at(-1).typeId, "aionbound:ember_forge_core");
  assert.equal(withCore.some(x => x.typeId === "aionbound:ash_drake_horn"), false);
});

test("cache is five rolls inside apex 4-6 band and never contains critical trophy", () => {
  const cache = rollKilnSkyCache(() => 0); assert.equal(KILN_SKY_CACHE_ROLLS, 5); assert.equal(cache.length, 5);
  assert.equal(cache.some(x => x.typeId === "aionbound:ash_drake_horn" || x.typeId === "aionbound:ember_forge_core"), false);
});

test("claim hook requires capacity and delivers through inventory only", () => {
  const slots = Array(2), accepted = [], container = { size: 2, getItem: i => slots[i], addItem(item) { accepted.push(item); slots[0] = item; return undefined; } };
  const player = { getComponent: id => id === "minecraft:inventory" ? { container } : undefined };
  const hooks = createAshenRewardHooks({ ItemStack: FakeItemStack, resolveArena: () => null });
  assert.equal(hooks.canDeliverHorn(player), true); assert.equal(hooks.deliverHorn(player), true); assert.equal(accepted[0].typeId, "aionbound:ash_drake_horn");
  slots[1] = new FakeItemStack("minecraft:stone", 1); assert.equal(hooks.canDeliverHorn(player), false);
});

test("arena cache remains locked until terminal service opens it or durable completion confirms it", () => {
  const items = [new FakeItemStack("aionbound:drake_scale", 1)], container = { size: 6, getItem: i => items[i] };
  const dimension = { id: "minecraft:overworld" }, block = { typeId: "minecraft:barrel", location: { x: 1, y: 2, z: 3 }, dimension, getComponent: () => ({ container }) };
  const arena = { dimension, cacheLocation: block.location };
  const locked = createAshenRewardHooks({ ItemStack: FakeItemStack, resolveArena: () => arena }), first = { block, cancel: false };
  assert.equal(locked.guardArenaCacheInteraction(first), true); assert.equal(first.cancel, true);
  const completed = createAshenRewardHooks({ ItemStack: FakeItemStack, resolveArena: () => arena, isArenaComplete: () => true }), second = { block, cancel: false };
  assert.equal(completed.guardArenaCacheInteraction(second), false); assert.equal(second.cancel, false);
});
