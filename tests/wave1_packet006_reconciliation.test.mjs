import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SOURCE = resolve(ROOT, "behavior_pack/scripts");
const MODULE_DIR = await mkdtemp(resolve(tmpdir(), "aionbound-packet006-reconciliation-"));
const encounterSource = (await readFile(resolve(SOURCE, "encounters.js"), "utf8"))
  .replaceAll(/from "\.\/([a-z0-9_]+)\.js"/g, 'from "./$1.mjs"');
await writeFile(resolve(MODULE_DIR, "encounters.mjs"), encounterSource);
await writeFile(resolve(MODULE_DIR, "catalog.mjs"), "export const BOSS_LADDER = {}; export const BOSS_REWARDS = {};\n");
await writeFile(resolve(MODULE_DIR, "budgets.mjs"), "export const COMBINED_BUDGETS = { bossesWorld: 4, twinbondMax: 2, mountsWorld: 4 };\n");
const load = name => import(pathToFileURL(resolve(MODULE_DIR, `${name}.mjs`)).href);
const { createEncounterService } = await load("encounters");

test("superseded finale ignition key cannot launch Twinbond or mutate state", () => {
  const messages = [];
  const state = {
    warn: (_player, message) => messages.push(message),
    playerState: () => { throw new Error("legacy player state read"); },
    worldState: () => { throw new Error("legacy world admission"); },
    saveWorld: () => { throw new Error("legacy world write"); },
  };
  const player = {
    id: "p",
    dimension: {
      spawnEntity: () => { throw new Error("legacy Twinbond spawn"); },
      spawnItem: () => { throw new Error("legacy reward spawn"); },
    },
  };
  const service = createEncounterService({
    world: { getAllPlayers: () => [player] }, ItemStack: class {}, state,
    boundedEntities: () => [], consumeOne: () => { throw new Error("legacy key consumption"); },
  });
  assert.equal(service.spawnTwinbond(player, { x: 0, y: 64, z: 0 }, "aionbound:finale_ignition_key"), false);
  assert.deepEqual(messages, ["Twinbond is withheld pending the ratified Wave 1 finale contract."]);
});

test("legacy Twinbond deaths cannot award Concord Scale or endpoint state", () => {
  const forbiddenState = {
    warn() {},
    worldState: () => { throw new Error("legacy terminal journal write"); },
    playerState: () => { throw new Error("legacy endpoint read"); },
    saveWorld: () => { throw new Error("legacy terminal journal save"); },
    savePlayer: () => { throw new Error("legacy endpoint save"); },
    stamp: () => { throw new Error("legacy Twinbond stamp"); },
  };
  const service = createEncounterService({
    world: { getAllPlayers: () => { throw new Error("legacy owner lookup"); } },
    ItemStack: class { constructor() { throw new Error("legacy reward item"); } },
    state: forbiddenState, boundedEntities: () => [], consumeOne: () => false,
  });
  for (const [typeId, key] of [
    ["aionbound:ash_sovereign_wyrm", "twinbond:p:ash"],
    ["aionbound:tide_empress_wyrm", "twinbond:p:tide"],
  ]) {
    const deadEntity = {
      typeId,
      getDynamicProperty: property => property === "aionbound:owner" ? "p" : key,
    };
    assert.equal(service.bossDeath({ deadEntity }), true);
  }
});

test("shipping encounter source contains no superseded launcher or reward identity", async () => {
  const source = await readFile(resolve(SOURCE, "encounters.js"), "utf8");
  for (const superseded of ["aionbound:finale_ignition_key", "aionbound:trophy_concord_scale", '"endpoint:concord"']) {
    assert.equal(source.includes(superseded), false, superseded);
  }
  assert.equal(source.includes("Twinbond is withheld pending the ratified Wave 1 finale contract."), true);
});
