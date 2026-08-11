import test from "node:test";
import assert from "node:assert/strict";
import {
  WHISPERWOOD_TREE_OFFSETS,
  createWhisperwoodRegrowthComponent,
  registerWhisperwoodRegrowth,
} from "../behavior_pack/scripts/whisperwood_regrowth.js";

function fixture({ blocked = false, amount = 2, gameMode = "survival" } = {}) {
  const sapling = { x: 10, y: 64, z: 20 };
  const placements = [], writes = [];
  const blocks = new Map();
  blocks.set("10,63,20", "minecraft:dirt");
  if (blocked) blocks.set("11,68,20", "minecraft:stone");
  const dimension = {
    getBlock(location) {
      const key = `${location.x},${location.y},${location.z}`;
      return { typeId: blocks.get(key) ?? "minecraft:air" };
    },
  };
  const block = { typeId: "aionbound:whisperwood_sapling", location: sapling, dimension };
  const held = { typeId: "minecraft:bone_meal", amount };
  const player = {
    selectedSlotIndex: 0,
    getGameMode: () => gameMode,
    getComponent: id => id === "minecraft:inventory" ? {
      container: { getItem: () => held, setItem: (slot, item) => writes.push([slot, item?.amount]) },
    } : undefined,
  };
  const world = { structureManager: { place: (...args) => placements.push(args) } };
  return { block, player, world, placements, writes };
}

test("regrowth footprint exactly mirrors the 77-block ratified assembly", () => {
  assert.equal(WHISPERWOOD_TREE_OFFSETS.length, 77);
  assert.equal(new Set(WHISPERWOOD_TREE_OFFSETS.map(({ x, y, z }) => `${x},${y},${z}`)).size, 77);
  assert.deepEqual(WHISPERWOOD_TREE_OFFSETS.find(value => value.x === 0 && value.y === 0 && value.z === 0), { x: 0, y: 0, z: 0 });
});

test("natural tick atomically checks clearance and places the approved structure origin", () => {
  const clear = fixture();
  createWhisperwoodRegrowthComponent({ world: clear.world }).onTick({ block: clear.block });
  assert.deepEqual(clear.placements, [["aionbound:ww_sapling_growth_tree", clear.block.dimension, { x: 7, y: 64, z: 17 }]]);
  const blocked = fixture({ blocked: true });
  createWhisperwoodRegrowthComponent({ world: blocked.world }).onTick({ block: blocked.block });
  assert.equal(blocked.placements.length, 0);
});

test("bone meal applies one-in-three gate and consumes at most one only after success", () => {
  const failedGate = fixture();
  createWhisperwoodRegrowthComponent({ world: failedGate.world, random: () => 0.9 }).onPlayerInteract(failedGate);
  assert.equal(failedGate.placements.length, 0); assert.equal(failedGate.writes.length, 0);
  const success = fixture();
  createWhisperwoodRegrowthComponent({ world: success.world, random: () => 0.1 }).onPlayerInteract(success);
  assert.equal(success.placements.length, 1); assert.deepEqual(success.writes, [[0, 1]]);
  const creative = fixture({ gameMode: "creative" });
  createWhisperwoodRegrowthComponent({ world: creative.world, random: () => 0.1 }).onPlayerInteract(creative);
  assert.equal(creative.placements.length, 1); assert.equal(creative.writes.length, 0);
});

test("startup registration binds exactly the ratified custom component", () => {
  const calls = [], event = { blockComponentRegistry: { registerCustomComponent: (...args) => calls.push(args) } };
  registerWhisperwoodRegrowth(event, fixture().world, () => 0.1);
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], "aionbound:whisperwood_sapling_regrowth");
  assert.equal(typeof calls[0][1].onTick, "function");
  assert.equal(typeof calls[0][1].onPlayerInteract, "function");
});
