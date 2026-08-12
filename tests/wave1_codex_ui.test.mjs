import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SOURCE = resolve(ROOT, "behavior_pack/scripts");
const MODULE_DIR = await mkdtemp(resolve(tmpdir(), "aionbound-codex-ui-"));
for (const name of ["wave1_codex_extension_data", "wave1_codex_ashen_data", "wave1_codex_crystal_data", "wave1_codex_skyreach_data", "wave1_codex_data", "wave1_codex_ui_data", "catalog", "budgets", "state", "codex"]) {
  const source = (await readFile(resolve(SOURCE, `${name}.js`), "utf8"))
    .replaceAll(/from "\.\/([a-z0-9_]+)\.js"/g, 'from "./$1.mjs"');
  await writeFile(resolve(MODULE_DIR, `${name}.mjs`), source);
}
const load = name => import(pathToFileURL(resolve(MODULE_DIR, `${name}.mjs`)).href);
const uiData = await load("wave1_codex_ui_data");
const catalog = await load("catalog");
const stateModule = await load("state");
const codexModule = await load("codex");
const map = JSON.parse(await readFile(resolve(ROOT, "engineering/whisperwood-intake/codex/WHISPERWOOD_CODEX_IMPLEMENTATION_MAP.json"), "utf8"));
const questionKeys = ["what_did_i_find", "what_can_i_make", "what_should_i_investigate_next"];

test("UI data binds all approved available answers and omits every blocked answer", async () => {
  assert.equal(Object.keys(uiData.WHISPERWOOD_CODEX_UI_BY_ID).length, 40);
  const source = await readFile(resolve(SOURCE, "wave1_codex_ui_data.js"), "utf8");
  for (const entry of map.entries) {
    const actual = uiData.WHISPERWOOD_CODEX_UI_BY_ID[entry.id].answers;
    const expected = questionKeys.map(key => {
      const question = entry.player_questions[key];
      return question.blocked_by.length ? null : question.text;
    });
    assert.deepEqual(actual, expected, entry.id);
    for (const key of questionKeys) {
      const question = entry.player_questions[key];
      if (question.blocked_by.length) assert.equal(source.includes(question.text), false, `${entry.id}:${key}`);
    }
  }
});

test("locked partial and complete state deterministically control disclosure", () => {
  const entry = catalog.CODEX_ENTRY_REGISTRY.find(candidate => candidate.id === "stripped_whisperwood_log");
  assert.equal(codexModule.codexEntryTitle(entry, 0), "Unknown entry");
  assert.equal(codexModule.codexEntryBody(entry, 0), "This entry has not been discovered.");
  const partial = codexModule.codexEntryBody(entry, 1);
  assert.ok(partial.includes("Worked Whisperwood timber."));
  assert.equal((partial.match(/Complete this entry to reveal this answer\./g) ?? []).length, 2);
  const complete = codexModule.codexEntryBody(entry, 2);
  assert.ok(complete.includes("Worked Whisperwood timber."));
  assert.ok(complete.includes("Intermediate timber for player builds."));
  assert.ok(complete.includes("Use crafted forest wood to extend camps and bases."));
  const blocked = catalog.CODEX_ENTRY_REGISTRY.find(candidate => candidate.id === "mosskip_buck");
  assert.equal((codexModule.codexEntryBody(blocked, 2).match(/Unavailable until its approved runtime dependency is complete\./g) ?? []).length, 3);
});

function createPlayerState() {
  const properties = new Map(), messages = [];
  const player = {
    id: "p", typeId: "minecraft:player", isSneaking: false,
    getDynamicProperty: id => properties.get(id),
    setDynamicProperty: (id, value) => properties.set(id, value),
    sendMessage: message => messages.push(message),
  };
  const world = { getDynamicProperty: () => undefined, setDynamicProperty() {} };
  return { player, messages, state: stateModule.createStateService({ world, system: { currentTick: 0 } }) };
}

function formHarness(responses) {
  const forms = [];
  class ActionFormData {
    constructor() { this.record = { title: "", body: "", buttons: [] }; forms.push(this.record); }
    title(value) { this.record.title = value; return this; }
    body(value) { this.record.body = value; return this; }
    button(value) { this.record.buttons.push(value); return this; }
    show() {
      const response = responses.shift();
      return response instanceof Error ? Promise.reject(response) : Promise.resolve(response);
    }
  }
  return { ActionFormData, forms };
}

test("existing Codex routes open category and entry ActionForms without chat", async () => {
  const { player, messages, state } = createPlayerState();
  const { ActionFormData, forms } = formHarness([{ canceled: false, selection: 0 }, { canceled: false, selection: 1 }, { canceled: false, selection: 0 }, { canceled: true }]);
  const codex = codexModule.createCodexService({ state, ActionFormData });
  assert.equal(codex.discover(player, "codex:ww:plant:star_grass:harvested"), true);
  assert.equal(await codex.use(player, "aionbound:trophy_codex"), false);
  assert.equal(forms.length, 4);
  assert.equal(forms[0].title, "Aionbound Codex — Living World");
  assert.deepEqual(forms[0].buttons, ["Whisperwood", "Ashen Highlands", "Crystal Marsh", "Skyreach"]);
  assert.equal(forms[1].title, "Aionbound Codex — Whisperwood");
  assert.deepEqual(forms[1].buttons, [
    "Resources & Blocks — 0/20",
    "Plants — 1/10",
    "Creatures — 0/10",
    "Structures — 0/10",
    "Equipment & Trophies — 0/21",
    "Bosses — 0/1",
    "Journey — 0/2",
    "Back",
  ]);
  assert.equal(forms[2].title, "Whisperwood — Plants");
  assert.equal(forms[2].buttons[0], "[Complete] Star Grass");
  assert.equal(forms[2].buttons[1], "[Locked] Unknown entry");
  assert.ok(forms[3].body.includes("What did I find?"));
  assert.ok(forms[3].body.includes("Unavailable until its approved runtime dependency is complete."));
  assert.ok(forms[3].body.includes("Early fiber and fodder."));
  assert.deepEqual(messages, []);
});

test("a rejected form produces one bounded legacy guidance fallback", async () => {
  const { player, messages, state } = createPlayerState();
  const { ActionFormData, forms } = formHarness([new Error("busy")]);
  const codex = codexModule.createCodexService({ state, ActionFormData });
  assert.equal(await codex.use(player, "aionbound:trophy_codex"), false);
  assert.equal(forms.length, 1);
  assert.equal(messages.length, 1);
  assert.ok(messages[0].includes("Aionbound Codex"));
  assert.equal(state.playerState(player).codex.topic, 1);
});

test("bookmark route preserves its legacy stamp before opening the primary UI", async () => {
  const { player, messages, state } = createPlayerState();
  const { ActionFormData } = formHarness([{ canceled: true }]);
  const codex = codexModule.createCodexService({ state, ActionFormData });
  await codex.use(player, "aionbound:starter_codex_bookmark");
  assert.deepEqual(state.playerState(player).stamps, ["bookmark:first_waystone"]);
  assert.deepEqual(messages, []);
});

test("manifest and runtime pin the locally available stable server-ui module", async () => {
  const manifest = JSON.parse(await readFile(resolve(ROOT, "behavior_pack/manifest.json"), "utf8"));
  const uiDependencies = manifest.dependencies.filter(dependency => dependency.module_name === "@minecraft/server-ui");
  assert.deepEqual(uiDependencies, [{ module_name: "@minecraft/server-ui", version: "2.0.0" }]);
  const runtime = await readFile(resolve(SOURCE, "runtime.js"), "utf8");
  assert.equal((runtime.match(/import \{ ActionFormData \} from "@minecraft\/server-ui";/g) ?? []).length, 1);
  assert.equal(runtime.includes("ActionFormData: platform.ActionFormData"), true);
});
