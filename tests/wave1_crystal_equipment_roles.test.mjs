import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createCrystalEquipmentService } from "../behavior_pack/scripts/crystal_equipment.js";
import { CRYSTAL_ACCESSORY_ROLES, CRYSTAL_MELEE_ROLES, CRYSTAL_RANGED_ROLES, CRYSTAL_ROLE_WITHHOLDS } from "../behavior_pack/scripts/crystal_equipment_roles.js";
import { NATURAL_ENTITY_IDS } from "../behavior_pack/scripts/catalog.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const readJson = async path => JSON.parse(await readFile(resolve(ROOT, path), "utf8"));

function harness() {
  const effects = [], damage = [], particles = [], warnings = [];
  const durability = { damage: 0, maxDurability: 420 };
  const bow = { typeId: "aionbound:prism_bow", amount: 1, getComponent: id => id === "minecraft:durability" ? durability : undefined };
  const slots = [bow, { typeId: "minecraft:arrow", amount: 2 }];
  const container = { size: slots.length, getItem: index => slots[index], setItem: (index, value) => { slots[index] = value; } };
  const equipment = new Map();
  const dimension = { getBlock: () => ({ typeId: "minecraft:water" }), spawnParticle: (...args) => particles.push(args) };
  const player = {
    id: "p1", typeId: "minecraft:player", selectedSlotIndex: 0, location: { x: 0, y: 62, z: 0 }, dimension,
    getComponent: id => id === "minecraft:inventory" ? { container } : id === "minecraft:equippable" ? { getEquipment: slot => equipment.get(slot) } : undefined,
    getEntitiesFromViewDirection: () => [], getViewDirection: () => ({ x: 1, y: 0, z: 0 }), getHeadLocation: () => ({ x: 0, y: 63, z: 0 }),
    addEffect: (...args) => effects.push(args),
  };
  let record = { cooldowns: {} };
  const state = { playerState: () => structuredClone(record), savePlayer: (_p, next) => { record = structuredClone(next); return true; }, warn: (_p, message) => warnings.push(message) };
  const system = { currentTick: 100 }, arbiter = { spend: () => true };
  const service = createCrystalEquipmentService({ system, state, arbiter });
  const target = { applyDamage: (...args) => damage.push(args) };
  return { service, player, target, slots, durability, equipment, effects, damage, particles, warnings, system };
}

test("role scope is exact and explicitly withholds unratified semantics", () => {
  assert.deepEqual(Object.keys(CRYSTAL_MELEE_ROLES), ["aionbound:crystal_pike"]);
  assert.deepEqual(Object.keys(CRYSTAL_RANGED_ROLES), ["aionbound:prism_bow"]);
  assert.equal(CRYSTAL_RANGED_ROLES["aionbound:prism_bow"].ammo, "minecraft:arrow");
  assert.equal(CRYSTAL_ACCESSORY_ROLES["aionbound:crystal_talisman"], "wet_vision");
  assert.match(CRYSTAL_ROLE_WITHHOLDS["aionbound:prism_bow"], /W1-CREATIVE-005/);
  assert.match(CRYSTAL_ROLE_WITHHOLDS["aionbound:marsh_idol"], /narrative-only/);
  assert.match(CRYSTAL_ROLE_WITHHOLDS["aionbound:explorer_cloak"], /not authorized/);
});

test("Prism Bow requires a bounded target and arrow before cooldown mutation", () => {
  const h = harness();
  assert.equal(h.service.useRanged(h.player, "aionbound:prism_bow"), false);
  assert.equal(h.slots[1].amount, 2); assert.equal(h.durability.damage, 0);
  h.player.getEntitiesFromViewDirection = () => [{ entity: h.target }]; h.slots[1] = undefined;
  assert.equal(h.service.useRanged(h.player, "aionbound:prism_bow"), false);
  assert.match(h.warnings.at(-1), /needs an arrow/); assert.equal(h.durability.damage, 0);
});

test("Prism Bow consumes once and bounds damage durability particles and cooldown", () => {
  const h = harness(); h.player.getEntitiesFromViewDirection = () => [{ entity: h.target }];
  assert.equal(h.service.useRanged(h.player, "aionbound:prism_bow"), true);
  assert.equal(h.slots[1].amount, 1); assert.equal(h.durability.damage, 1);
  assert.equal(h.damage[0][0], 5); assert.equal(h.particles.length, 5);
  h.system.currentTick = 101; assert.equal(h.service.useRanged(h.player, "aionbound:prism_bow"), false);
  assert.equal(h.slots[1].amount, 1); assert.equal(h.durability.damage, 1);
});

test("Crystal Talisman grants wet vision only while wet; Marsh Idol mutates nothing", () => {
  const h = harness(); h.equipment.set("Offhand", { typeId: "aionbound:crystal_talisman" });
  assert.equal(h.service.tickPlayer(h.player), true); assert.equal(h.effects[0][0], "night_vision");
  h.equipment.set("Offhand", { typeId: "aionbound:marsh_idol" });
  assert.equal(h.service.tickPlayer(h.player), false); assert.equal(h.effects.length, 1);
});

test("declarative roles close Pike Sickle Cloak and Mire Bloom soft craft", async () => {
  const pike = (await readJson("behavior_pack/items/crystal_pike.item.json"))["minecraft:item"].components;
  const sickle = (await readJson("behavior_pack/items/marsh_sickle.item.json"))["minecraft:item"].components;
  const cloak = (await readJson("behavior_pack/items/explorer_cloak.item.json"))["minecraft:item"].components;
  const dye = (await readJson("behavior_pack/recipes/mire_bloom_cyan_dye.recipe.json"))["minecraft:recipe_shapeless"];
  assert.equal(pike["minecraft:damage"], 6); assert.ok(pike["minecraft:durability"]); assert.ok(pike["minecraft:repairable"]);
  assert.ok(sickle["minecraft:digger"].destroy_speeds.length >= 11); assert.ok(sickle["minecraft:repairable"]);
  assert.equal(cloak["minecraft:wearable"].slot, "slot.armor.chest"); assert.ok(cloak["minecraft:repairable"]);
  assert.deepEqual(dye.ingredients, [{ item: "aionbound:mire_bloom_item" }]); assert.equal(dye.result.item, "minecraft:cyan_dye");
});

test("runtime composes into existing handlers without new subscription or interval", async () => {
  const runtime = await readFile(resolve(ROOT, "behavior_pack/scripts/runtime.js"), "utf8");
  assert.equal((runtime.match(/itemCompleteUse\.subscribe/g) ?? []).length, 1);
  assert.equal((runtime.match(/runInterval\(/g) ?? []).length, 1);
  assert.equal(runtime.includes("createAshenEquipmentService"), false);
  assert.match(runtime, /crystalEquipment\.useRanged/); assert.match(runtime, /crystalEquipment\.tickPlayer/);
});

test("natural registry includes nine Crystal ecology entities, excludes the arena Wight, and preserves cap", async () => {
  const expected = ["bloom_crab", "bog_watcher", "crystal_dragonfly", "crystal_newt", "glass_heron", "mire_turtle", "prism_frog", "reed_serpent", "silt_crocodile"].map(id => `aionbound:${id}`);
  for (const typeId of expected) assert.equal(NATURAL_ENTITY_IDS.includes(typeId), true, typeId);
  assert.equal(NATURAL_ENTITY_IDS.includes("aionbound:marsh_wight"), false);
  const budgets = await readFile(resolve(ROOT, "behavior_pack/scripts/budgets.js"), "utf8");
  const combat = await readFile(resolve(ROOT, "behavior_pack/scripts/combat.js"), "utf8");
  assert.match(budgets, /naturalEntitiesTarget:\s*40/);
  assert.match(combat, /natural\.sort\(/); assert.match(combat, /natural\.slice\(COMBINED_BUDGETS\.naturalEntitiesTarget\)/);
});
