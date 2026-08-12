export const SKYREACH_REWARD_CONTRACT = Object.freeze({
  encounterId: "aionbound:storm_nest",
  chapterSeal: "aionbound:storm_pinion",
  proposalHashes: Object.freeze({
    identities: "926a401add04b6611d7cee7dd1fa3bcf6a3fe44cf656ef9aa34d9b1bad5f30cd",
    encounter: "59b4493857bf3d90d402d438553f4b7fc03c6b45689e5897f8a8cb501bfc15d0",
    loot: "823894296bb4b4ed1becd1a1a5ccc814f734cecc50c8433be855bdf1e080e4bf",
  }),
  progressionSubstitutes: Object.freeze([]),
  optionalMasteryInventoryItems: Object.freeze([]),
});

export const STORM_NEST_MATERIAL_TABLE = Object.freeze({
  pools: Object.freeze([
    Object.freeze({ rolls: Object.freeze([2, 4]), entries: Object.freeze([
      Object.freeze({ typeId: "aionbound:sky_feather", weight: 35, min: 1, max: 3 }),
      Object.freeze({ typeId: "aionbound:wind_silk", weight: 30, min: 1, max: 3 }),
      Object.freeze({ typeId: "aionbound:float_resin", weight: 20, min: 1, max: 3 }),
      Object.freeze({ typeId: "aionbound:wing_bone_stay", weight: 15, min: 1, max: 1 }),
    ]) }),
    Object.freeze({ rolls: Object.freeze([1, 2]), entries: Object.freeze([
      Object.freeze({ typeId: "aionbound:aether_stone", weight: 55, min: 1, max: 2 }),
      Object.freeze({ typeId: "aionbound:cliff_crystal", weight: 45, min: 1, max: 2 }),
    ]) }),
  ]),
});

const boundedRandom = random => {
  const value = Number(random());
  return Number.isFinite(value) ? Math.max(0, Math.min(.999999999999, value)) : 0;
};
const randomCount = (range, random) => range[0] + Math.floor(boundedRandom(random) * (range[1] - range[0] + 1));
const weighted = (entries, random) => {
  const total = entries.reduce((sum, entry) => sum + entry.weight, 0);
  let cursor = boundedRandom(random) * total;
  return entries.find(entry => ((cursor -= entry.weight) < 0)) ?? entries.at(-1);
};

export function rollStormNestMaterials(random = Math.random) {
  const output = [];
  for (const pool of STORM_NEST_MATERIAL_TABLE.pools) {
    const rolls = randomCount(pool.rolls, random);
    for (let index = 0; index < rolls; index++) {
      const selected = weighted(pool.entries, random);
      output.push({ typeId: selected.typeId, amount: randomCount([selected.min, selected.max], random) });
    }
  }
  return output;
}

function hasOneItemCapacity(container, typeId) {
  if (!container) return false;
  if (Number.isFinite(container.emptySlotsCount) && container.emptySlotsCount > 0) return true;
  for (let slot = 0; slot < (container.size ?? 0); slot++) {
    const item = container.getItem?.(slot);
    if (!item) return true;
    if (item.typeId === typeId && item.amount < (item.maxAmount ?? 64)) return true;
  }
  return false;
}

export function createSkyreachRewardHooks({ ItemStack, random = Math.random }) {
  function canDeliverPinion(player, typeId = SKYREACH_REWARD_CONTRACT.chapterSeal) {
    return hasOneItemCapacity(player.getComponent?.("minecraft:inventory")?.container, typeId);
  }

  function deliverPinion(player, typeId = SKYREACH_REWARD_CONTRACT.chapterSeal) {
    const container = player.getComponent?.("minecraft:inventory")?.container;
    if (!container?.addItem || !hasOneItemCapacity(container, typeId)) return false;
    try { return !container.addItem(new ItemStack(typeId, 1)); }
    catch { return false; }
  }

  function grantMaterialPackage(player, context) {
    if (context?.encounterId !== SKYREACH_REWARD_CONTRACT.encounterId) return false;
    const container = player.getComponent?.("minecraft:inventory")?.container;
    try {
      for (const item of rollStormNestMaterials(random)) {
        const stack = new ItemStack(item.typeId, item.amount);
        const remainder = container?.addItem ? container.addItem(stack) : stack;
        if (remainder) player.dimension.spawnItem(remainder, player.location);
      }
      return true;
    } catch { return false; }
  }

  // The ratified arena chest is separate from terminal progression. The
  // current authored nest platform has no container; this hook therefore
  // cannot invent one and remains a bounded no-op until a container-bearing
  // authored structure exists. Material packages and seal recovery are live.
  function openArenaCache() { return false; }

  return Object.freeze({ canDeliverPinion, deliverPinion, grantMaterialPackage, openArenaCache });
}
