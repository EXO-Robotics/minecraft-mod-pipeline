import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SOURCE = resolve(ROOT, "behavior_pack/scripts");
const MODULE_DIR = await mkdtemp(resolve(tmpdir(), "aionbound-codex-events-"));
for (const name of ["wave1_codex_extension_data", "wave1_codex_ashen_data", "wave1_codex_crystal_data", "wave1_codex_skyreach_data", "wave1_codex_data", "wave1_codex_ui_data", "catalog", "budgets", "state", "codex", "router"]) {
  const source = (await readFile(resolve(SOURCE, `${name}.js`), "utf8"))
    .replaceAll(/from "\.\/([a-z0-9_]+)\.js"/g, 'from "./$1.mjs"');
  await writeFile(resolve(MODULE_DIR, `${name}.mjs`), source);
}
const load = name => import(pathToFileURL(resolve(MODULE_DIR, `${name}.mjs`)).href);
const catalog = await load("catalog");
const stateModule = await load("state");
const { createCodexService } = await load("codex");
const { createInteractionRouter } = await load("router");
const map = JSON.parse(await readFile(resolve(ROOT, "engineering/whisperwood-intake/codex/WHISPERWOOD_CODEX_IMPLEMENTATION_MAP.json"), "utf8"));

const expectedRoutes = (kinds, eventName) => Object.fromEntries(map.entries
  .filter(entry => kinds.includes(entry.entry_kind))
  .flatMap(entry => [...entry.discovery_stamps, ...(entry.detail_events ?? [])]
    .filter(event => event.event === eventName)
    .map(event => [entry.runtime_id, event.id])));

test("catalog preserves exact Whisperwood routes and appends later-region harvest routes", () => {
  const expected = {
    ...expectedRoutes(["block"], "harvested"),
    ...expectedRoutes(["block"], "crafted"),
    ...expectedRoutes(["plant"], "harvested"),
  };
  assert.equal(Object.keys(catalog.CODEX_BLOCK_INTERACTION_ROUTES).length, 60);
  assert.deepEqual(Object.fromEntries(Object.entries(catalog.CODEX_BLOCK_INTERACTION_ROUTES).filter(([id]) => id in expected).map(([id, events]) => [id, events[0]])), expected);
});

test("all interaction routes resolve to integrated behavior-pack blocks", async () => {
  for (const runtimeId of Object.keys(catalog.CODEX_BLOCK_INTERACTION_ROUTES)) {
    const id = runtimeId.slice("aionbound:".length);
    const document = JSON.parse(await readFile(resolve(ROOT, `behavior_pack/blocks/${id}.block.json`), "utf8"));
    assert.equal(document["minecraft:block"].description.identifier, runtimeId);
  }
});

test("catalog binds exact creature observation and completion transitions", () => {
  const expectedInteractions = expectedRoutes(["creature"], "observe_nearby");
  const expectedDeaths = expectedRoutes(["creature"], "defeat");
  assert.deepEqual(Object.fromEntries(Object.entries(catalog.CODEX_ENTITY_INTERACTION_ROUTES).filter(([id]) => id in expectedInteractions).map(([id, events]) => [id, events[0]])), expectedInteractions);
  assert.deepEqual(Object.fromEntries(Object.entries(catalog.CODEX_ENTITY_DEATH_ROUTES).filter(([id]) => id in expectedDeaths).map(([id, events]) => [id, events[0]])), expectedDeaths);
  assert.ok(Object.keys(catalog.CODEX_ENTITY_INTERACTION_ROUTES).length >= 6);
  assert.ok(Object.keys(catalog.CODEX_ENTITY_DEATH_ROUTES).length >= 7);
});

function harness() {
  const legacy = [], codex = [], actions = [];
  const router = createInteractionRouter({
    discover: (_player, key) => legacy.push(key),
    codexDiscover: (_player, eventId) => codex.push(eventId),
    blockActions: { "boss:basalt": () => actions.push("boss:basalt") },
    itemActions: {},
    entityActions: { waykeeper_notice: () => actions.push("waykeeper_notice") },
  });
  return { router, legacy, codex, actions };
}

test("block routing stays compositional and adds silent Codex discovery", () => {
  const { router, legacy, codex, actions } = harness();
  assert.equal(router.dispatchBlock({ player: {}, block: { typeId: "aionbound:whisperwood_log" } }), true);
  assert.deepEqual(codex, ["codex:ww:block:whisperwood_log:harvested"]);
  assert.equal(router.dispatchBlock({ player: {}, block: { typeId: "aionbound:ember_vent_stone" } }), true);
  assert.deepEqual(legacy, ["pilgrimage:vent"]);
  assert.deepEqual(actions, ["boss:basalt"]);
  assert.equal(router.dispatchBlock({ player: {}, block: { typeId: "minecraft:stone" } }), false);
});

test("entity interaction composes Whisperwood observation and existing Waykeeper action", () => {
  const { router, codex, actions } = harness();
  assert.equal(router.dispatchEntityInteraction({ player: {}, target: { typeId: "aionbound:mosskip_buck" } }), true);
  assert.deepEqual(codex, ["codex:ww:creature:mosskip_buck:observed"]);
  assert.equal(router.dispatchEntityInteraction({ player: {}, target: { typeId: "aionbound:waykeeper_courser" } }), true);
  assert.deepEqual(actions, ["waykeeper_notice"]);
  assert.equal(router.dispatchEntityInteraction({ player: {}, target: { typeId: "minecraft:cow" } }), false);
});

test("death discovery requires a player cause and uses only map-authorized completions", () => {
  const { router, codex } = harness();
  const player = { typeId: "minecraft:player" };
  assert.equal(router.dispatchEntityDeathEvent({ deadEntity: { typeId: "aionbound:mosskip_buck" }, damageSource: { damagingEntity: player } }), true);
  assert.deepEqual(codex, ["codex_detail:ww:creature:mosskip_buck:defeated"]);
  assert.equal(router.dispatchEntityDeathEvent({ deadEntity: { typeId: "aionbound:rot_wolf" }, damageSource: { damagingEntity: { typeId: "aionbound:bark_wraith" } } }), false);
  assert.equal(router.dispatchEntityDeathEvent({ deadEntity: { typeId: "aionbound:mosskip_fawn" }, damageSource: { damagingEntity: player } }), false);
  assert.equal(router.dispatchEntityDeathEvent({ deadEntity: { typeId: "aionbound:rot_wolf" }, damageSource: { damagingEntity: player } }), true);
  assert.deepEqual(codex, ["codex_detail:ww:creature:mosskip_buck:defeated", "codex:ww:creature:rot_wolf:defeated"]);
});

test("routed events drive monotonic persisted v4 state without chat", () => {
  const properties = new Map(), messages = [];
  const player = {
    id: "p", typeId: "minecraft:player",
    getDynamicProperty: id => properties.get(id),
    setDynamicProperty: (id, value) => properties.set(id, value),
    sendMessage: message => messages.push(message),
  };
  const world = { getDynamicProperty: () => undefined, setDynamicProperty() {} };
  const state = stateModule.createStateService({ world, system: { currentTick: 0 } });
  const codex = createCodexService({ state });
  const router = createInteractionRouter({ discover: state.stamp, codexDiscover: codex.discover, blockActions: {}, itemActions: {}, entityActions: {} });
  router.dispatchBlock({ player, block: { typeId: "aionbound:star_grass" } });
  router.dispatchEntityInteraction({ player, target: { typeId: "aionbound:mosskip_buck" } });
  router.dispatchEntityDeathEvent({ deadEntity: { typeId: "aionbound:mosskip_buck" }, damageSource: { damagingEntity: player } });
  const record = state.playerState(player);
  assert.equal(stateModule.codexDiscoveryState(record.codex.discovery, "ww", "plant", 0), 2);
  assert.equal(stateModule.codexDiscoveryState(record.codex.discovery, "ww", "creature", 2), 2);
  assert.deepEqual(record.stamps, []);
  assert.deepEqual(messages, []);
});

test("runtime death subscriber keeps Codex, boss, and Glasswing handlers unconditional", async () => {
  const source = await readFile(resolve(SOURCE, "runtime.js"), "utf8");
  const start = source.indexOf("platform.world.afterEvents.entityDie.subscribe");
  const end = source.indexOf("platform.system.runInterval", start);
  const handler = source.slice(start, end);
  const calls = ["router.dispatchEntityDeathEvent(event)", "encounters.bossDeath(event)", "combat.glasswingDeath(event)"];
  assert.deepEqual(calls.map(call => handler.indexOf(call) >= 0), [true, true, true]);
  assert.ok(handler.indexOf(calls[0]) < handler.indexOf(calls[1]));
  assert.ok(handler.indexOf(calls[1]) < handler.indexOf(calls[2]));
  assert.equal(handler.includes("if (!encounters.bossDeath"), false);
});
