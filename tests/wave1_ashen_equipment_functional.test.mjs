import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createAshenEquipmentService } from "../behavior_pack/scripts/ashen_equipment.js";
import { ASHEN_ACCESSORY_ROLES, ASHEN_ARMOR_SET, ASHEN_ARMORED_TARGETS, ASHEN_MELEE_ROLES, ASHEN_RANGED_ROLES } from "../behavior_pack/scripts/ashen_equipment_roles.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const readJson = async path => JSON.parse(await readFile(resolve(ROOT, path), "utf8"));

function harness() {
  const effects = [], damage = [], fire = [], particles = [], warnings = [], spent = [];
  const durability = { damage: 0, maxDurability: 360 };
  const repeater = { typeId: "aionbound:ash_repeater", amount: 1, getComponent: id => id === "minecraft:durability" ? durability : undefined };
  const slots = [repeater, { typeId: "aionbound:volcanic_glass_shard", amount: 2 }];
  const container = { size: slots.length, getItem: i => slots[i], setItem: (i, value) => { slots[i] = value; } };
  const equipment = new Map(), nearby = [];
  const dimension = { getEntities: () => nearby, spawnParticle: (id, location) => particles.push([id, location]) };
  const player = {
    id: "p1", typeId: "minecraft:player", selectedSlotIndex: 0, location: { x: 0, y: 64, z: 0 }, dimension,
    getComponent: id => id === "minecraft:inventory" ? { container } : id === "minecraft:equippable" ? { getEquipment: slot => equipment.get(slot) } : undefined,
    getEntitiesFromViewDirection: () => [], getViewDirection: () => ({ x: 1, y: 0, z: 0 }), getHeadLocation: () => ({ x: 0, y: 65, z: 0 }),
    addEffect: (...args) => effects.push(args),
  };
  let record = { cooldowns: {} };
  const state = { playerState: () => structuredClone(record), savePlayer: (_p, next) => { record = structuredClone(next); return true; }, warn: (_p, message) => warnings.push(message) };
  const system = { currentTick: 100 }, arbiter = { spend: name => { spent.push(name); return true; } }, world = { getAllPlayers: () => [player] };
  const service = createAshenEquipmentService({ world, system, state, arbiter });
  const entity = (id, typeId = "minecraft:zombie") => ({ id, typeId, location: { x: 1, y: 64, z: 0 }, dimension, addEffect: (...args) => effects.push([id, ...args]), applyDamage: (...args) => damage.push([id, ...args]), setOnFire: (...args) => fire.push([id, ...args]) });
  return { service, player, slots, durability, equipment, nearby, effects, damage, fire, particles, warnings, spent, entity, system };
}

test("role tables preserve exact identities and conservative bounded refinements", () => {
  assert.deepEqual(Object.keys(ASHEN_MELEE_ROLES), ["aionbound:basalt_hammer", "aionbound:ember_great_axe"]);
  assert.equal(ASHEN_RANGED_ROLES["aionbound:ash_repeater"].ammo, "aionbound:volcanic_glass_shard");
  assert.ok(ASHEN_RANGED_ROLES["aionbound:ash_repeater"].range <= 24); assert.ok(ASHEN_RANGED_ROLES["aionbound:ash_repeater"].particles <= 8);
  assert.ok(ASHEN_MELEE_ROLES["aionbound:ember_great_axe"].targets <= 4); assert.equal(ASHEN_ACCESSORY_ROLES["aionbound:ember_totem"], "heat_ward");
  assert.equal(ASHEN_ARMORED_TARGETS.has("aionbound:basalt_tortoise"), true); assert.equal(ASHEN_ARMORED_TARGETS.has("minecraft:player"), false);
});

test("basalt hammer stuns and strengthens only against exact armored identities", () => {
  const h = harness(), target = h.entity("t", "aionbound:basalt_tortoise"); h.slots[0] = { typeId: "aionbound:basalt_hammer" };
  assert.equal(h.service.routeMeleeHurt({ hurtEntity: target, damageSource: { damagingEntity: h.player } }), true);
  assert.deepEqual(h.effects.map(row => row[1]), ["slowness", "weakness"]);
  assert.equal(h.service.routeMeleeHurt({ hurtEntity: target, damageSource: { damagingEntity: h.player } }), false);
});

test("ember great axe applies bounded wide heat pressure without hitting the player or primary twice", () => {
  const h = harness(), target = h.entity("primary"), extras = Array.from({ length: 5 }, (_, i) => h.entity(`e${i}`)); h.nearby.push(target, h.player, ...extras); h.slots[0] = { typeId: "aionbound:ember_great_axe" };
  assert.equal(h.service.routeMeleeHurt({ hurtEntity: target, damageSource: { damagingEntity: h.player } }), true);
  assert.equal(h.damage.length, 3); assert.equal(h.fire.length, 4); assert.equal(h.spent.filter(x => x === "entityQuery").length, 3);
});

test("ash repeater requires and consumes one approved shard, damages durability, and emits bounded heat", () => {
  const h = harness(), target = h.entity("target"); h.player.getEntitiesFromViewDirection = () => [{ entity: target }];
  assert.equal(h.service.useRanged(h.player, "aionbound:ash_repeater"), true); assert.equal(h.slots[1].amount, 1); assert.equal(h.durability.damage, 1);
  assert.equal(h.damage[0][1], 4); assert.equal(h.fire[0][1], 2); assert.equal(h.particles.length, 4);
  h.system.currentTick = 101; assert.equal(h.service.useRanged(h.player, "aionbound:ash_repeater"), false); assert.equal(h.slots[1].amount, 1);
});

test("full Ashen armor and Ember Totem provide only their approved heat identity", () => {
  const h = harness(), slotNames = ["Head", "Chest", "Legs", "Feet"]; ASHEN_ARMOR_SET.forEach((typeId, i) => h.equipment.set(slotNames[i], { typeId }));
  h.equipment.set("Offhand", { typeId: "aionbound:ember_totem" }); assert.equal(h.service.armorSet(h.player), true); h.service.tickPlayers();
  assert.deepEqual(h.effects.map(row => row[0]), ["fire_resistance", "fire_resistance"]);
  assert.equal(h.service.handlePlayerHurt({ hurtEntity: h.player, damageSource: { cause: "lava" } }), true);
});

test("declarative components close damage, durability, repair, armor, and tool roles", async () => {
  const ids = ["basalt_hammer", "ember_great_axe", "ash_repeater", "ashen_helmet", "ashen_chest", "ashen_legs", "ashen_boots", "basalt_pick", "ember_hammer", "ore_chisel"];
  const items = new Map(); for (const id of ids) items.set(id, (await readJson(`behavior_pack/items/${id}.item.json`))["minecraft:item"].components);
  for (const id of ids) { assert.ok(items.get(id)["minecraft:durability"].max_durability > 0); assert.ok(items.get(id)["minecraft:repairable"].repair_items.length); }
  for (const id of ["basalt_hammer", "basalt_pick", "ember_hammer", "ore_chisel"]) assert.ok(items.get(id)["minecraft:digger"].destroy_speeds.length);
  assert.deepEqual(["ashen_helmet", "ashen_chest", "ashen_legs", "ashen_boots"].map(id => items.get(id)["minecraft:wearable"].protection), [2, 5, 4, 2]);
});

test("Briar Ring bytes and deferred Creative boundary remain unchanged; shared activation is absent", async () => {
  const briar = await readFile(resolve(ROOT, "behavior_pack/items/briar_ring.item.json")); assert.equal(createHash("sha256").update(briar).digest("hex"), "052dde829b4b96fb01f3c060062e14e2f5f5d27c48ac841d56ae54eb34bc4748");
  const ledger = await readJson("engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json"); assert.ok(ledger.ratifications.deferred.includes("W1-CREATIVE-005"));
  const combat = await readFile(resolve(ROOT, "behavior_pack/scripts/combat.js"), "utf8"); const runtime = await readFile(resolve(ROOT, "behavior_pack/scripts/runtime.js"), "utf8");
  assert.equal(combat.includes("./ashen_equipment.js"), false); assert.equal(runtime.includes("createAshenEquipmentService"), false);
});
