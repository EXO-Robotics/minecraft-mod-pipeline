import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { SKYREACH_REWARD_CONTRACT, STORM_NEST_MATERIAL_TABLE, createSkyreachRewardHooks, rollStormNestMaterials } from "../behavior_pack/scripts/skyreach_rewards.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const json = async path => JSON.parse(await readFile(resolve(ROOT, path), "utf8"));
const sha = bytes => createHash("sha256").update(bytes).digest("hex");

test("Skyreach economy binds the three exact approved proposal bytes", async () => {
  const expected = {
    "W1-001-SR": "926a401add04b6611d7cee7dd1fa3bcf6a3fe44cf656ef9aa34d9b1bad5f30cd",
    "W1-003-STORM-NEST": "59b4493857bf3d90d402d438553f4b7fc03c6b45689e5897f8a8cb501bfc15d0",
    "W1-004-SR": "823894296bb4b4ed1becd1a1a5ccc814f734cecc50c8433be855bdf1e080e4bf",
  };
  for (const [id, hash] of Object.entries(expected)) {
    const path = id === "W1-001-SR" ? "engineering/authority/support-proposals/skyreach/W1-001-SR.json"
      : id === "W1-003-STORM-NEST" ? "engineering/authority/support-proposals/skyreach/W1-003-STORM-NEST.json"
      : "engineering/authority/support-proposals/skyreach/W1-004-SR.json";
    assert.equal(sha(await readFile(resolve(ROOT, path))), hash);
  }
  assert.deepEqual(SKYREACH_REWARD_CONTRACT.proposalHashes, { identities: expected["W1-001-SR"], encounter: expected["W1-003-STORM-NEST"], loot: expected["W1-004-SR"] });
});

test("only Wing Bone Stay is a new required identity and all approved derived craft homes exist", async () => {
  const required = await json("behavior_pack/items/wing_bone_stay.item.json");
  assert.equal(required["minecraft:item"].description.identifier, "aionbound:wing_bone_stay");
  for (const id of ["climbing_rope", "climbing_hook_head", "glider_panel", "glider_frame", "soft_landing_pad", "lift_tonic", "aether_bind", "twin_mineral_lens"]) {
    assert.equal((await json(`behavior_pack/items/${id}.item.json`))["minecraft:item"].description.identifier, `aionbound:${id}`);
    assert.equal((await json(`behavior_pack/recipes/${id}.recipe.json`))["minecraft:recipe_shaped"].result.item, `aionbound:${id}`);
  }
});

test("Packet 006 Skyreach links are ordinary recipes and deferred sidegrades remain absent", async () => {
  for (const id of ["surveyor_staff", "trail_compass", "surveyor_medallion", "warden_sigil"]) {
    assert.equal((await json(`behavior_pack/recipes/${id}.recipe.json`))["minecraft:recipe_shaped"].result.item, `aionbound:${id}`);
  }
  for (const id of ["gale_prism_bow", "nest_talon_dagger", "skywidow_whip", "stormcloak", "summit_hammer"]) {
    await assert.rejects(readFile(resolve(ROOT, `behavior_pack/items/${id}.item.json`)));
  }
});

test("ecology Wind Roc has no seal path and the other nine creatures have bounded regional acquisition", async () => {
  const roc = await json("behavior_pack/loot_tables/entities/aionbound/skyreach/wind_roc.json");
  assert.equal(JSON.stringify(roc).includes("storm_pinion"), false);
  for (const id of ["cloud_goat", "sky_fox", "cliff_ram", "storm_gull", "gale_hawk", "ropewing", "stone_vulture", "glide_drake", "ruin_harpy"]) {
    const loot = await json(`behavior_pack/loot_tables/entities/aionbound/skyreach/${id}.json`);
    assert.ok(loot.pools.length >= 2 && loot.pools.length <= 3);
    for (const pool of loot.pools) assert.ok(pool.conditions[0].chance >= .03 && pool.conditions[0].chance <= 1);
  }
});

test("all ten plants provide deterministic acquisition without a new runtime handler", async () => {
  for (const id of ["wind_reed_plant", "hanging_sky_vine", "rope_root", "cloud_moss", "cloudpuff_plant", "shelf_shrub", "cliff_flower", "skybloom", "floating_blossom", "nest_thatch_tuft"]) {
    const block = await json(`behavior_pack/blocks/${id}.block.json`);
    const table = block["minecraft:block"].components["minecraft:loot"];
    assert.equal(table, `loot_tables/blocks/aionbound/skyreach/${id}.json`);
    assert.equal((await json(`behavior_pack/${table}`)).pools[0].conditions[0].chance, 1);
  }
});

test("boss package uses ratified roll/quantity envelopes and physical pinion delivery is capacity-bounded", () => {
  assert.deepEqual(STORM_NEST_MATERIAL_TABLE.pools.map(pool => pool.rolls), [[2, 4], [1, 2]]);
  for (const pool of STORM_NEST_MATERIAL_TABLE.pools) for (const entry of pool.entries) assert.ok(entry.min >= 1 && entry.max <= 3);
  assert.ok(rollStormNestMaterials(() => 0).length >= 3);
  class ItemStack { constructor(typeId, amount) { this.typeId = typeId; this.amount = amount; } }
  const full = { size: 1, emptySlotsCount: 0, getItem: () => ({ typeId: "minecraft:stone", amount: 64, maxAmount: 64 }), addItem: () => { throw new Error("must not add"); } };
  const player = { getComponent: () => ({ container: full }) };
  const hooks = createSkyreachRewardHooks({ ItemStack, random: () => 0 });
  assert.equal(hooks.canDeliverPinion(player), false); assert.equal(hooks.deliverPinion(player), false);
});
