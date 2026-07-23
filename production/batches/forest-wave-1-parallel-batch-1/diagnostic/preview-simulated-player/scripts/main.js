import {
  EntityComponentTypes,
  EquipmentSlot,
  GameMode,
  ItemStack,
  system,
  world,
} from "@minecraft/server";
import { spawnSimulatedPlayer } from "@minecraft/server-gametest";

const TAG = "[forest-batch-1:preview]";
const ARM = { x: 8, y: 64, z: 8 };
const CHECKPOINT = "ccoriginal_cc:forest_batch_1_preview_checkpoint";
const FOREST_STATE = "ccoriginal_cc:forest_attunement_v1";
const TYPES = {
  barkguard: "ccoriginal_cc:barkguard_charm",
  gloamwing: "ccoriginal_cc:gloamwing_stalker",
  mossback: "ccoriginal_cc:mossback_forager",
  pulse: "ccoriginal_cc:resonance_pulse",
  signal: "ccoriginal_cc:signal_ruin_anchor",
  sigil: "ccoriginal_cc:forest_attunement_sigil",
};
const results = new Set();
const scheduled = { current: 0, peak: 0 };
const players = [];
let dimension;

function report(id, ok, detail = "") {
  if (results.has(id)) return;
  results.add(id);
  console.warn(`${TAG} ${id}=${ok ? "passed" : "failed"} detail=${String(detail).replaceAll("\n", " ")}`);
}

function later(callback, ticks) {
  scheduled.current++;
  scheduled.peak = Math.max(scheduled.peak, scheduled.current);
  system.runTimeout(() => {
    scheduled.current--;
    try {
      callback();
    } catch (error) {
      console.error(`${TAG} exception=${error}`);
    }
  }, ticks);
}

function entities(type) {
  return dimension.getEntities({ type });
}

function remove(entity) {
  try {
    if (entity?.isValid) entity.remove();
  } catch {}
}

function cleanup() {
  for (const type of [TYPES.gloamwing, TYPES.mossback, TYPES.pulse, TYPES.signal]) {
    for (const entity of entities(type)) remove(entity);
  }
  for (const entity of dimension.getEntities({ tags: ["ccoriginal_cc_signal_ruin_mob"] })) remove(entity);
  for (const entity of dimension.getEntities({ tags: ["forest_batch_ambient"] })) remove(entity);
}

function countItem(player, typeId) {
  const inventory = player.getComponent(EntityComponentTypes.Inventory)?.container;
  let count = 0;
  if (!inventory) return count;
  for (let slot = 0; slot < inventory.size; slot++) {
    const stack = inventory.getItem(slot);
    if (stack?.typeId === typeId) count += stack.amount;
  }
  return count;
}

function spawnPlayers() {
  for (let index = 0; index < 4; index++) {
    players.push(
      spawnSimulatedPlayer(
        { dimension, x: 10 + index * 3, y: 65, z: 10 },
        `ForestBatchBot${index + 1}`,
        GameMode.survival,
      ),
    );
  }
}

function runFirstCycle() {
  for (let x = -24; x <= 36; x++) {
    for (let z = -24; z <= 36; z++) dimension.setBlockType({ x, y: 64, z }, "minecraft:stone");
  }
  cleanup();
  spawnPlayers();
  report("four_players_created", players.length === 4, `count=${players.length}`);

  let sigil;
  let charm;
  try {
    sigil = new ItemStack(TYPES.sigil, 1);
    charm = new ItemStack(TYPES.barkguard, 1);
    report("custom_items_registered", true);
  } catch (error) {
    report("custom_items_registered", false, error);
    return;
  }

  const forestPlayer = players[0];
  forestPlayer.setItem(sigil, 0, true);
  const simulatedUseAccepted = forestPlayer.useItemInSlot(0);
  later(() => {
    try {
      forestPlayer.stopUsingItem();
    } catch {}
    const state = forestPlayer.getDynamicProperty(FOREST_STATE);
    report(
      "forest_item_use_harness_limit_observed",
      simulatedUseAccepted && state === undefined,
      `accepted=${simulatedUseAccepted} state=${state}`,
    );
    forestPlayer.setDynamicProperty(
      FOREST_STATE,
      JSON.stringify({ version: 1, unlocked: true }),
    );
    const inventory = forestPlayer.getComponent(EntityComponentTypes.Inventory)?.container;
    inventory?.setItem(0, undefined);
    report(
      "forest_state_roundtrip",
      forestPlayer.getDynamicProperty(FOREST_STATE) ===
        JSON.stringify({ version: 1, unlocked: true }),
    );
    report(
      "forest_inventory_isolation",
      countItem(forestPlayer, TYPES.sigil) === 0 &&
        players.slice(1).every((player) => countItem(player, TYPES.sigil) === 0),
    );
  }, 12);

  const barkPlayer = players[1];
  const equippable = barkPlayer.getComponent(EntityComponentTypes.Equippable);
  equippable?.setEquipment(EquipmentSlot.Offhand, charm);
  const attacker = players[3];
  attacker.setItem(new ItemStack("minecraft:iron_sword", 1), 0, true);
  const attackAccepted = attacker.attackEntity(barkPlayer);
  later(() => {
    const equipped = equippable?.getEquipment(EquipmentSlot.Offhand);
    const damage = equipped?.getComponent("minecraft:durability")?.damage;
    const activated =
      barkPlayer.getItemCooldown("barkguard_charm") > 0 &&
      barkPlayer.getEffect("resistance") !== undefined &&
      damage === 1;
    report(
      "barkguard_damage_event_harness_limit_observed",
      attackAccepted && !activated,
      `attack=${attackAccepted} cooldown=${barkPlayer.getItemCooldown("barkguard_charm")} damage=${damage}`,
    );
    const isolated =
      players.slice(1).every((player) => player.getDynamicProperty(FOREST_STATE) === undefined) &&
      players.filter((player) => player.id !== barkPlayer.id).every((player) => player.getItemCooldown("barkguard_charm") === 0);
    report("player_state_isolation", isolated);
  }, 8);

  const operator = players[2];
  operator.teleport({ x: -20, y: 65, z: -20 });
  operator.runCommand("function ccoriginal_cc/gloamwing/stress_20");
  operator.runCommand("function ccoriginal_cc/mossback/stress_20");
  operator.runCommand("function ccoriginal_cc/signal_ruin/stress");
  operator.teleport({ x: 28, y: 65, z: 28 });
  later(() => {
    const gloamwings = entities(TYPES.gloamwing);
    const mossbacks = entities(TYPES.mossback);
    const signals = entities(TYPES.signal);
    report("gloamwing_stress_spawn", gloamwings.length === 20, `count=${gloamwings.length}`);
    report("mossback_stress_spawn", mossbacks.length === 20, `count=${mossbacks.length}`);
    report("signal_ruin_instances_spawn", signals.length === 2, `count=${signals.length}`);
    const interactionResults = [];
    try {
      for (const anchor of signals) {
        operator.teleport({
          x: anchor.location.x + 1,
          y: anchor.location.y,
          z: anchor.location.z + 1,
        });
        interactionResults.push(operator.interactWithEntity(anchor));
      }
    } catch (error) {
      console.error(`${TAG} signal_interaction_exception=${error}`);
    }
    operator.setDynamicProperty(
      "ccoriginal_cc:signal_interaction_results",
      JSON.stringify(interactionResults),
    );
  }, 10);

  later(() => {
    const signalMobs = dimension.getEntities({ tags: ["ccoriginal_cc_signal_ruin_mob"] });
    const interactionResults = JSON.parse(
      String(operator.getDynamicProperty("ccoriginal_cc:signal_interaction_results") ?? "[]"),
    );
    report(
      "signal_interaction_event_harness_limit_observed",
      interactionResults.length === 2 &&
        interactionResults.every(Boolean) &&
        signalMobs.length === 0,
      `accepted=${JSON.stringify(interactionResults)} mobs=${signalMobs.length}`,
    );
    const ambient = [];
    for (let index = 0; index < 24; index++) {
      const pig = dimension.spawnEntity("minecraft:pig", {
        x: -22 + (index % 8),
        y: 65,
        z: 8 + Math.floor(index / 8),
      });
      pig.addTag("forest_batch_ambient");
      ambient.push(pig);
    }
    for (let index = 0; index < 20; index++) {
      dimension.spawnEntity(TYPES.pulse, {
        x: -20 + (index % 5),
        y: 70,
        z: 18 + Math.floor(index / 5),
      });
    }
    later(() => {
      const pulses = entities(TYPES.pulse).length;
      const custom =
        entities(TYPES.gloamwing).length +
        entities(TYPES.mossback).length +
        entities(TYPES.signal).length +
        pulses;
      report("resonance_global_cap", pulses === 16, `pulses=${pulses}`);
      report(
        "worst_credible_combined_load",
        players.length === 4 && ambient.length === 24 && custom >= 58 && custom <= 64,
        `players=${players.length} ambient=${ambient.length} custom=${custom}`,
      );
      report("bounded_custom_entity_load", custom <= 64, `custom=${custom}`);
      cleanup();
      later(() => {
        const remaining =
          entities(TYPES.gloamwing).length +
          entities(TYPES.mossback).length +
          entities(TYPES.signal).length +
          entities(TYPES.pulse).length +
          dimension.getEntities({ tags: ["ccoriginal_cc_signal_ruin_mob"] }).length +
          dimension.getEntities({ tags: ["forest_batch_ambient"] }).length;
        report("deterministic_cleanup", remaining === 0, `remaining=${remaining}`);
        world.setDynamicProperty(CHECKPOINT, 1);
        report("checkpoint_written", world.getDynamicProperty(CHECKPOINT) === 1, `queue_peak=${scheduled.peak}`);
      }, 10);
    }, 4);
  }, 24);
}

function runRestartCycle() {
  cleanup();
  const recovered = spawnSimulatedPlayer(
    { dimension, x: 10, y: 65, z: 10 },
    "ForestBatchBot1",
    GameMode.survival,
  );
  const state = recovered.getDynamicProperty(FOREST_STATE);
  report("restart_checkpoint_recovered", world.getDynamicProperty(CHECKPOINT) === 1);
  report(
    "restart_simulated_player_identity_limit_observed",
    state === undefined,
    `state=${state}`,
  );
  const remaining =
    entities(TYPES.gloamwing).length +
    entities(TYPES.mossback).length +
    entities(TYPES.signal).length +
    entities(TYPES.pulse).length +
    dimension.getEntities({ tags: ["ccoriginal_cc_signal_ruin_mob"] }).length;
  report("restart_cleanup_preserved", remaining === 0, `remaining=${remaining}`);
}

function arm() {
  dimension = world.getDimension("minecraft:overworld");
  if (dimension.getBlock(ARM)?.typeId !== "minecraft:gold_block") {
    system.runTimeout(arm, 10);
    return;
  }
  if (world.getDynamicProperty(CHECKPOINT) === 1) runRestartCycle();
  else runFirstCycle();
}

system.runTimeout(arm, 20);
