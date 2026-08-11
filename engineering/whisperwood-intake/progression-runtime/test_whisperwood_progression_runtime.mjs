import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const SOURCE = resolve(ROOT, "behavior_pack/scripts");
const MODULE_DIR = await mkdtemp(resolve(tmpdir(), "aionbound-ww-progression-"));
for (const name of ["wave1_codex_data", "catalog", "budgets", "state", "structures", "router"]) {
  const source = (await readFile(resolve(SOURCE, `${name}.js`), "utf8"))
    .replaceAll(/from "\.\/([a-z0-9_]+)\.js"/g, 'from "./$1.mjs"');
  await writeFile(resolve(MODULE_DIR, `${name}.mjs`), source);
}
const load = name => import(pathToFileURL(resolve(MODULE_DIR, `${name}.mjs`)).href);
const catalog = await load("catalog");
const { createStateService } = await load("state");
const { createStructureService } = await load("structures");
const { createInteractionRouter } = await load("router");

function harness() {
  const playerProperties = new Map(), worldProperties = new Map(), messages = [], spawned = [];
  const blocks = new Map();
  const key = ({ x, y, z }) => `${x},${y},${z}`;
  const dimension = {
    id: "minecraft:overworld",
    getBlock: location => ({ typeId: blocks.get(key(location)) ?? "minecraft:air" }),
    spawnItem: item => spawned.push(item),
  };
  const player = {
    id: "player-one",
    dimension,
    location: { x: 0, y: 64, z: 0 },
    getDynamicProperty: id => playerProperties.get(id),
    setDynamicProperty: (id, value) => playerProperties.set(id, value),
    sendMessage: message => messages.push(message),
  };
  const world = {
    getDynamicProperty: id => worldProperties.get(id),
    setDynamicProperty: (id, value) => worldProperties.set(id, value),
  };
  const system = { currentTick: 10 };
  const makeState = () => createStateService({ world, system, notify: (_player, text) => messages.push(text) });
  const makeStructures = state => createStructureService({
    world,
    system,
    ItemStack: class {},
    state,
    arbiter: {},
    consumeOne: () => false,
  });
  return { blocks, key, player, messages, spawned, makeState, makeStructures };
}

test("catalog binds only the exact existing progression stamps and no reward identity", () => {
  assert.deepEqual(catalog.WHISPERWOOD_PROGRESSION_SITES, [
    {
      id: "forest_waystone", center: "minecraft:lodestone", signatures: ["aionbound:glow_moss"],
      stamp: "landmark:forest_waystone", role: "activation",
    },
    {
      id: "broken_wagon", center: "minecraft:barrel", signatures: ["aionbound:whisperwood_roots", "aionbound:whisperwood_planks"],
      stamp: "landmark:broken_wagon", role: "transition_hook", transition: "ww_to_ah",
      presentation: "WITHHELD_PENDING_CREATIVE_AUTHORITY",
    },
  ]);
  assert.deepEqual(catalog.BLOCK_ROUTES["minecraft:lodestone"], { discoveries: [], actions: ["ww_progression_site"] });
  assert.deepEqual(catalog.BLOCK_ROUTES["minecraft:barrel"], { discoveries: [], actions: ["ww_progression_site"] });
  assert.equal(JSON.stringify(catalog.WHISPERWOOD_PROGRESSION_SITES).includes("reward"), false);
  assert.equal(JSON.stringify(catalog.WHISPERWOOD_PROGRESSION_SITES).includes("aionbound:ah_"), false);
});

test("forest waystone activation is signature-scoped duplicate-safe and persistent", () => {
  const h = harness(), anchor = { typeId: "minecraft:lodestone", location: { x: 0, y: 64, z: 0 } };
  let state = h.makeState(), structures = h.makeStructures(state);
  assert.equal(structures.activateProgressionSite({ player: h.player, block: anchor }), false);
  h.blocks.set(h.key({ x: 1, y: 65, z: 0 }), "aionbound:glow_moss");
  assert.deepEqual(structures.activateProgressionSite({ player: h.player, block: anchor }), {
    site: "forest_waystone", stamp: "landmark:forest_waystone", role: "activation", transition: null, changed: true,
  });
  assert.equal(structures.activateProgressionSite({ player: h.player, block: anchor }).changed, false);
  state = h.makeState(); structures = h.makeStructures(state);
  assert.deepEqual(state.playerState(h.player).stamps, ["landmark:forest_waystone"]);
  assert.equal(structures.activateProgressionSite({ player: h.player, block: anchor }).changed, false);
  assert.deepEqual(h.messages, []);
  assert.deepEqual(h.spawned, []);
});

test("broken wagon records only the exact landmark transition hook and withholds rumor presentation", () => {
  const h = harness(), anchor = { typeId: "minecraft:barrel", location: { x: 8, y: 66, z: 3 } };
  h.blocks.set(h.key({ x: 8, y: 65, z: 3 }), "aionbound:whisperwood_roots");
  const state = h.makeState(), structures = h.makeStructures(state);
  assert.equal(structures.activateProgressionSite({ player: h.player, block: anchor }), false);
  h.blocks.set(h.key({ x: 7, y: 66, z: 3 }), "aionbound:whisperwood_planks");
  assert.deepEqual(structures.activateProgressionSite({ player: h.player, block: anchor }), {
    site: "broken_wagon", stamp: "landmark:broken_wagon", role: "transition_hook", transition: "ww_to_ah", changed: true,
  });
  const record = state.playerState(h.player);
  assert.deepEqual(record.stamps, ["landmark:broken_wagon"]);
  assert.equal(record.stamps.some(stamp => stamp.startsWith("rumor:")), false);
  assert.deepEqual(h.messages, []);
  assert.deepEqual(h.spawned, []);
});

test("router keeps progression actions compositional and ordinary anchors are harmless", () => {
  const calls = [], router = createInteractionRouter({
    discover: (_player, stamp) => calls.push(`discover:${stamp}`),
    blockActions: { ww_progression_site: () => calls.push("action:ww_progression_site") },
    itemActions: {},
  });
  assert.equal(router.dispatchBlock({ player: {}, block: { typeId: "minecraft:lodestone" } }), true);
  assert.deepEqual(calls, ["action:ww_progression_site"]);
  const h = harness(), structures = h.makeStructures(h.makeState());
  assert.equal(structures.activateProgressionSite({ player: h.player, block: { typeId: "minecraft:barrel", location: { x: 0, y: 64, z: 0 } } }), false);
  assert.deepEqual(h.makeState().playerState(h.player).stamps, []);
});

test("runtime binds the progression action without loot or cancellation", async () => {
  const runtime = await readFile(resolve(SOURCE, "runtime.js"), "utf8");
  const structures = await readFile(resolve(SOURCE, "structures.js"), "utf8");
  assert.equal(runtime.includes("ww_progression_site: context => structures.activateProgressionSite(context)"), true);
  assert.equal(structures.includes("spawnItem(new ItemStack(reward[0]"), true);
  const activationStart = structures.indexOf("function activateProgressionSite");
  const activationEnd = structures.indexOf("function claimSite", activationStart);
  const activation = structures.slice(activationStart, activationEnd);
  assert.equal(activation.includes("spawnItem"), false);
  assert.equal(activation.includes("sendMessage"), false);
  assert.equal(runtime.includes('if (event.block.typeId === "minecraft:lodestone") event.cancel = true'), false);
  assert.equal(runtime.includes('if (event.block.typeId === "minecraft:barrel") event.cancel = true'), false);
});
