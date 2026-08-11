import test from "node:test";
import assert from "node:assert/strict";
import { ACCESSORY_ROLES } from "../behavior_pack/scripts/catalog.js";
import { createCombatService } from "../behavior_pack/scripts/combat.js";

const expectedRoles = Object.freeze({
  "aionbound:moss_charm": "forest_sustain",
  "aionbound:root_bracelet": "gather_focus",
  "aionbound:lantern_badge": "soft_light",
  "aionbound:moon_sap_pendant": "night_comfort",
  "aionbound:briar_ring": "thorn_chip",
});

function harness(accessory, { blockType = "aionbound:root_flower", time = 18000 } = {}) {
  const effects = [], monsters = Array.from({ length: 6 }, (_, index) => ({ id: `monster-${index}`, effects: [], addEffect(name) { this.effects.push(name); } }));
  const equipment = { getEquipment(slot) { return slot === "Offhand" ? { typeId: accessory } : undefined; } };
  const player = {
    id: "player", typeId: "minecraft:player", location: { x: 0, y: 64, z: 0 }, effects,
    addEffect(name) { effects.push(name); },
    getComponent(name) { if (name === "minecraft:equippable") return equipment; return { container: { getItem() { return undefined; } } }; },
    getBlockFromViewDirection() { return { block: { typeId: blockType } }; },
    dimension: { getEntities() { return monsters; } },
  };
  const stateRecord = { cooldowns: {} };
  const combat = createCombatService({
    world: { getAllPlayers: () => [player], getTimeOfDay: () => time },
    system: { currentTick: 200 }, ItemStack: class {}, EquipmentSlot: { Offhand: "Offhand", Head: "Head", Chest: "Chest", Legs: "Legs", Feet: "Feet" }, EntityComponentTypes: { Equippable: "minecraft:equippable" },
    state: { playerState: () => stateRecord, savePlayer: () => true, warn() {} },
    arbiter: { spend: () => true }, boundedEntities: () => [], consumeOne: () => false,
  });
  return { combat, player, effects, monsters, stateRecord };
}

test("five Whisperwood accessories bind exact approved role families", () => {
  for (const [id, role] of Object.entries(expectedRoles)) assert.equal(ACCESSORY_ROLES[id], role);
});

test("moss charm provides bounded sustain while equipped", () => {
  const { combat, effects } = harness("aionbound:moss_charm"); combat.tickPlayers();
  assert.deepEqual(effects, ["regeneration"]);
});

test("root bracelet accelerates only approved Aionbound gathering targets", () => {
  const active = harness("aionbound:root_bracelet"); active.combat.tickPlayers(); assert.deepEqual(active.effects, ["haste"]);
  const inactive = harness("aionbound:root_bracelet", { blockType: "minecraft:stone" }); inactive.combat.tickPlayers(); assert.deepEqual(inactive.effects, []);
});

test("lantern badge applies soft light and caps fear-soft targets at four", () => {
  const { combat, effects, monsters } = harness("aionbound:lantern_badge"); combat.tickPlayers();
  assert.deepEqual(effects, ["night_vision"]);
  assert.equal(monsters.filter(monster => monster.effects.includes("weakness")).length, 4);
});

test("moon sap pendant comforts at night but not during day", () => {
  const night = harness("aionbound:moon_sap_pendant"); night.combat.tickPlayers(); assert.deepEqual(night.effects, ["night_vision"]);
  const day = harness("aionbound:moon_sap_pendant", { time: 6000 }); day.combat.tickPlayers(); assert.deepEqual(day.effects, []);
});

test("briar ring returns one bounded thorn chip through the composed hurt handler", () => {
  const { combat, player, stateRecord } = harness("aionbound:briar_ring");
  const attacker = { id: "attacker", damage: [], applyDamage(value) { this.damage.push(value); } };
  assert.equal(combat.handlePlayerHurt({ hurtEntity: player, damageSource: { damagingEntity: attacker } }), true);
  assert.deepEqual(attacker.damage, [1]);
  assert.equal(stateRecord.cooldowns["accessory:briar_ring"], 240);
});
