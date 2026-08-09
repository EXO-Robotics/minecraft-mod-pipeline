import { COMBINED_BUDGETS } from "./budgets.js";
import { TECH_LOOPS } from "./catalog.js";

const keyFor = block => `${block.dimension?.id ?? "minecraft:overworld"}:${block.location.x},${block.location.y},${block.location.z}`;

export function createDeviceService({ world, system, ItemStack, state, arbiter, consumeOne }) {
  function selected(player) { return player.getComponent("minecraft:inventory")?.container?.getItem(player.selectedSlotIndex); }
  function useSalvage({ player }) {
    const item = selected(player), result = item && TECH_LOOPS.salvage[item.typeId];
    if (!result) return state.warn(player, "Hold a supported duplicate equipment item to salvage it.");
    if (!consumeOne(player, item.typeId)) return;
    player.dimension.spawnItem(new ItemStack(result.item, result.count), player.location);
  }
  function usePress({ player, block }) {
    const item = selected(player), result = item && TECH_LOOPS.press[item.typeId], w = state.worldState(), key = keyFor(block);
    if (!result) return state.warn(player, "The press needs a recognized raw Aionbound material.");
    if (w.devices[key] || Object.keys(w.devices).length >= COMBINED_BUDGETS.devicesWorld) return state.warn(player, "The device registry or this press is busy; input was not consumed.");
    if (!consumeOne(player, item.typeId)) return;
    w.devices[key] = { v: 3, kind: "press", owner: player.id, dimension: player.dimension.id, location: block.location, output: result, ready: system.currentTick + COMBINED_BUDGETS.deviceIntervalTicks };
    if (!state.saveWorld(w)) { delete w.devices[key]; player.dimension.spawnItem(new ItemStack(item.typeId, 1), player.location); }
  }
  function useSurvey({ player }) {
    const p = state.playerState(player);
    const suggestions = [
      ["landmark:foundry", "A foundry wreck can be recognized by its mechanical silhouette."],
      ["destination:burrowgate", "Orevein Hollow gates lead to owner-bound pockets."],
      ["pilgrimage:storm", "Storm slate marks one branch of the pilgrimage."],
      ["rumor:pilgrimage_threshold", "A rare threshold is rumored beyond the ordinary pilgrimage traces."],
    ];
    const next = suggestions.find(([stamp]) => !p.stamps.includes(stamp)) ?? suggestions[0];
    player.sendMessage(`§b[Survey Relay]§r ${next[1]}`);
  }
  function tick() {
    arbiter.beginTick(system.currentTick); const w = state.worldState(); let changed = false;
    for (const [key, job] of Object.entries(w.devices)) {
      if (job.kind !== "press" || job.ready > system.currentTick || !arbiter.spend("deviceOpsTick")) continue;
      world.getDimension(job.dimension).spawnItem(new ItemStack(job.output.item, job.output.count), { x: job.location.x + 0.5, y: job.location.y + 1, z: job.location.z + 0.5 });
      delete w.devices[key]; changed = true;
    }
    if (changed) state.saveWorld(w);
  }
  return { useSalvage, usePress, useSurvey, tick, keyFor };
}
