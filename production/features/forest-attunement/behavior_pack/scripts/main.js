import { system, world } from "@minecraft/server";
import {
  PROPERTY_ID,
  canonicalState,
  decodeState,
  isForestAttuned,
  resetForestAttunement,
} from "./state.js";

const SIGIL_ID = "ccoriginal_cc:forest_attunement_sigil";
const RESET_EVENT = "ccoriginal_cc:forest_attunement_reset";
const FOREST_BIOMES = new Set([
  "minecraft:forest",
  "minecraft:flower_forest",
  "minecraft:birch_forest",
  "minecraft:old_growth_birch_forest",
  "minecraft:dark_forest",
  "minecraft:grove",
]);

function warn(player, decoded) {
  console.warn(`[Forest Attunement] ${player.name}: ${decoded.diagnostic}; state preserved and activation refused.`);
  player.sendMessage("§cThe sigil found unreadable attunement data. No item was consumed; ask an operator to reset it.");
}

function selectedSigil(player) {
  const inventory = player.getComponent("minecraft:inventory")?.container;
  if (!inventory) return undefined;
  const slot = player.selectedSlotIndex;
  const stack = inventory.getItem(slot);
  if (!stack || stack.typeId !== SIGIL_ID || stack.amount < 1) return undefined;
  return { inventory, slot };
}

function consumeSelectedSigil(player, selection = selectedSigil(player)) {
  if (!selection) return false;
  const { inventory, slot } = selection;
  const stack = inventory.getItem(slot);
  if (!stack || stack.typeId !== SIGIL_ID || stack.amount < 1) return false;
  if (stack.amount === 1) inventory.setItem(slot, undefined);
  else {
    stack.amount -= 1;
    inventory.setItem(slot, stack);
  }
  return true;
}

function bestEffortMessage(player, message) {
  try {
    player.sendMessage(message);
  } catch (error) {
    console.warn(`[Forest Attunement] optional message failed for ${player.name}: ${error}`);
  }
}

function rollbackUncommittedWrite(player, reason) {
  try {
    player.setDynamicProperty(PROPERTY_ID, undefined);
  } catch (rollbackError) {
    console.warn(`[Forest Attunement] rollback failed for ${player.name} after ${reason}: ${rollbackError}`);
  }
}

function presentActivation(player) {
  try {
    player.sendMessage("§2The forest's cadence settles into your steps.");
    player.dimension.spawnParticle("minecraft:villager_happy", player.location);
  } catch (error) {
    console.warn(`[Forest Attunement] optional activation presentation failed for ${player.name}: ${error}`);
  }
}

function activate(player) {
  const decoded = decodeState(player.getDynamicProperty(PROPERTY_ID));
  if (decoded.kind === "current" || decoded.kind === "legacy") {
    if (decoded.kind === "legacy") isForestAttuned(player);
    bestEffortMessage(player, "§aYou are already attuned. The sigil remains in your hand.");
    return;
  }
  if (decoded.kind === "unknown" || decoded.kind === "corrupt") {
    warn(player, decoded);
    return;
  }

  // Snapshot and validate the exact selected inventory slot before persisting.
  const selection = selectedSigil(player);
  if (!selection) {
    bestEffortMessage(player, "§cActivation stopped because no valid sigil is selected.");
    return;
  }

  try {
    player.setDynamicProperty(PROPERTY_ID, canonicalState());
  } catch (error) {
    console.warn(`[Forest Attunement] activation write failed for ${player.name}: ${error}`);
    bestEffortMessage(player, "§cAttunement could not be saved. No item was consumed.");
    return;
  }

  // Inventory consumption is the final transactional mutation. A failure here
  // rolls back only the uncommitted property write.
  try {
    if (!consumeSelectedSigil(player, selection)) {
      rollbackUncommittedWrite(player, "inventory validation failure");
      bestEffortMessage(player, "§cActivation stopped because the held sigil changed.");
      return;
    }
  } catch (error) {
    rollbackUncommittedWrite(player, "inventory mutation exception");
    console.warn(`[Forest Attunement] sigil consumption failed for ${player.name}: ${error}`);
    bestEffortMessage(player, "§cActivation stopped before commitment.");
    return;
  }

  // Persistence and consumption are now committed. Presentation is optional
  // and must never clear the unlock or restore/consume another item.
  presentActivation(player);
}

world.afterEvents.itemUse.subscribe(({ itemStack, source }) => {
  if (itemStack?.typeId === SIGIL_ID && source) activate(source);
});

system.afterEvents.scriptEventReceive.subscribe(({ id, sourceEntity }) => {
  if (id !== RESET_EVENT || sourceEntity?.typeId !== "minecraft:player") return;
  const player = sourceEntity;
  if (!player.isOp()) {
    player.sendMessage("§cForest Attunement reset requires operator permission.");
    return;
  }
  resetForestAttunement(player);
  player.sendMessage("§eYour Forest Attunement record was reset.");
});

system.runInterval(() => {
  for (const player of world.getAllPlayers().slice(0, 4)) {
    if (!player) continue;
    if (!isForestAttuned(player)) continue;
    try {
      const biome = player.dimension.getBiome(player.location);
      if (FOREST_BIOMES.has(biome.id)) {
        player.addEffect("speed", 120, { amplifier: 0, showParticles: false });
      }
    } catch (error) {
      console.warn(`[Forest Attunement] bounded biome check failed for ${player.name}: ${error}`);
    }
  }
}, 100);

export { activate, consumeSelectedSigil };
