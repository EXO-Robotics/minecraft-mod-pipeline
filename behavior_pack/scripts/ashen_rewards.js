export const KILN_SKY_CORE_CHANCE = 0.14;
export const KILN_SKY_CACHE_ROLLS = 5;

// All identities already exist in ratified Ashen warehouse/Packet 006
// authority. The selected quantities/rolls are inside W1-004-AH bounds.
export const KILN_SKY_SIGNATURE_MATERIALS = Object.freeze([
  "aionbound:drake_scale", "aionbound:basalt_core", "aionbound:furnace_chitin",
]);
export const KILN_SKY_CATALYSTS = Object.freeze([
  "aionbound:ash_crystal", "aionbound:heatstone", "aionbound:ember_resin", "aionbound:volcanic_glass_shard",
]);
const CACHE_TYPES = new Set([...KILN_SKY_SIGNATURE_MATERIALS, ...KILN_SKY_CATALYSTS, "aionbound:ember_forge_core"]);

const boundedRandom = random => {
  const value = Number(random());
  return Number.isFinite(value) ? Math.max(0, Math.min(0.999999999999, value)) : 0;
};
const choose = (items, random) => items[Math.floor(boundedRandom(random) * items.length)];
const key = (dimension, location) => `${dimension?.id ?? "minecraft:overworld"}:${Math.floor(location.x)},${Math.floor(location.y)},${Math.floor(location.z)}`;
const inventory = block => block?.getComponent?.("minecraft:inventory")?.container;
const contents = container => {
  const result = [];
  for (let slot = 0; slot < (container?.size ?? 0); slot++) { const item = container.getItem(slot); if (item) result.push(item); }
  return result;
};

export function rollKilnSkyParticipantPackage(random = Math.random) {
  const items = [];
  // Midpoints: three signature rolls, quantity two; one catalyst roll,
  // quantity one. The optional mastery trophy uses the E-envelope midpoint.
  for (let roll = 0; roll < 3; roll++) items.push({ typeId: choose(KILN_SKY_SIGNATURE_MATERIALS, random), amount: 2 });
  items.push({ typeId: choose(KILN_SKY_CATALYSTS, random), amount: 1 });
  if (boundedRandom(random) < KILN_SKY_CORE_CHANCE) items.push({ typeId: "aionbound:ember_forge_core", amount: 1 });
  return items;
}

export function rollKilnSkyCache(random = Math.random) {
  const regional = [...KILN_SKY_SIGNATURE_MATERIALS, ...KILN_SKY_CATALYSTS];
  return Array.from({ length: KILN_SKY_CACHE_ROLLS }, () => ({ typeId: choose(regional, random), amount: 1 }));
}

export function createAshenRewardHooks({ ItemStack, random = Math.random, resolveArena, isArenaComplete = () => false }) {
  const openedCaches = new Set();

  function give(player, item) {
    const stack = new ItemStack(item.typeId, item.amount), container = player.getComponent?.("minecraft:inventory")?.container;
    const remainder = container?.addItem ? container.addItem(stack) : stack;
    if (remainder) player.dimension.spawnItem(remainder, player.location);
  }

  function canDeliverHorn(player) {
    const container = player.getComponent?.("minecraft:inventory")?.container;
    if (!container) return false;
    if (Number.isInteger(container.emptySlotsCount)) return container.emptySlotsCount > 0;
    for (let slot = 0; slot < container.size; slot++) if (!container.getItem(slot)) return true;
    return false;
  }

  function deliverHorn(player) {
    const container = player.getComponent?.("minecraft:inventory")?.container;
    if (!container?.addItem) return false;
    return !container.addItem(new ItemStack("aionbound:ash_drake_horn", 1));
  }

  function grantMaterialPackage(player) {
    try { for (const item of rollKilnSkyParticipantPackage(random)) give(player, item); return true; }
    catch { return false; }
  }

  function openArenaCache({ arena }) {
    const block = arena?.dimension?.getBlock?.(arena.cacheLocation), container = inventory(block);
    if (block?.typeId !== "minecraft:barrel" || !container) return false;
    const existing = contents(container);
    if (existing.some(item => !CACHE_TYPES.has(item.typeId))) return false;
    const items = rollKilnSkyCache(random);
    if (items.length > container.size) return false;
    try {
      for (let slot = 0; slot < container.size; slot++) container.setItem(slot, undefined);
      for (let slot = 0; slot < items.length; slot++) container.setItem(slot, new ItemStack(items[slot].typeId, items[slot].amount));
      openedCaches.add(key(arena.dimension, arena.cacheLocation)); return true;
    } catch { return false; }
  }

  function guardArenaCacheInteraction(event) {
    if (event.block?.typeId !== "minecraft:barrel") return false;
    const arena = resolveArena?.(event.block);
    if (!arena || key(arena.dimension, arena.cacheLocation) !== key(event.block.dimension, event.block.location)) return false;
    const unlocked = openedCaches.has(key(arena.dimension, arena.cacheLocation)) || isArenaComplete(arena) === true;
    if (!unlocked) event.cancel = true;
    return !unlocked;
  }

  return Object.freeze({ canDeliverHorn, deliverHorn, grantMaterialPackage, openArenaCache, guardArenaCacheInteraction });
}
