export const THORN_COURT_CACHE_OFFSET = Object.freeze({ x: -2, y: 0, z: 2 });

// These source constants are semantic mirrors of the protected Bedrock loot
// tables. Tests bind every pool, chance, count range, weight, and roll count to
// the JSON bytes so command-based loot execution is unnecessary.
export const THORN_COURT_MATERIAL_POOLS = Object.freeze([
  Object.freeze({ typeId: "aionbound:widow_silk", min: 1, max: 3, chance: 1 }),
  Object.freeze({ typeId: "aionbound:thorn_barb", min: 1, max: 3, chance: 1 }),
  Object.freeze({ typeId: "aionbound:hollow_amber", min: 1, max: 2, chance: 1 }),
  Object.freeze({ typeId: "aionbound:root_heart", min: 1, max: 1, chance: 0.5 }),
  Object.freeze({ typeId: "aionbound:moon_sap", min: 1, max: 1, chance: 0.5 }),
  Object.freeze({ typeId: "aionbound:ancient_acorn", min: 1, max: 1, chance: 0.12 }),
]);

export const THORN_COURT_CACHE_TABLE = Object.freeze({
  rolls: 5,
  entries: Object.freeze([
    Object.freeze({ typeId: "aionbound:widow_silk", weight: 40, min: 1, max: 2 }),
    Object.freeze({ typeId: "aionbound:thorn_barb", weight: 30, min: 1, max: 2 }),
    Object.freeze({ typeId: "aionbound:hollow_amber", weight: 15, min: 1, max: 2 }),
    Object.freeze({ typeId: "aionbound:root_heart", weight: 10, min: 1, max: 2 }),
    Object.freeze({ typeId: "aionbound:ancient_acorn", weight: 5, min: 1, max: 2 }),
  ]),
});

const CACHE_TYPES = new Set(THORN_COURT_CACHE_TABLE.entries.map(entry => entry.typeId));
const rotations = ({ x, y, z }) => [
  { x, y, z },
  { x: z, y, z: -x },
  { x: -x, y, z: -z },
  { x: -z, y, z: x },
];
const at = (origin, offset) => ({ x: origin.x + offset.x, y: origin.y + offset.y, z: origin.z + offset.z });
const key = (dimension, location) => `${dimension?.id ?? "minecraft:overworld"}:${Math.floor(location.x)},${Math.floor(location.y)},${Math.floor(location.z)}`;
const inventory = block => block?.getComponent?.("minecraft:inventory")?.container;
const boundedRandom = random => {
  const value = Number(random());
  return Number.isFinite(value) ? Math.max(0, Math.min(0.999999999999, value)) : 0;
};
const count = (spec, random) => spec.min + Math.floor(boundedRandom(random) * (spec.max - spec.min + 1));

export function rollThornCourtMaterials(random = Math.random) {
  const output = [];
  for (const spec of THORN_COURT_MATERIAL_POOLS) {
    if (spec.chance < 1 && boundedRandom(random) >= spec.chance) continue;
    output.push({ typeId: spec.typeId, amount: count(spec, random) });
  }
  return output;
}

export function rollThornCourtCache(random = Math.random) {
  const output = [], total = THORN_COURT_CACHE_TABLE.entries.reduce((sum, entry) => sum + entry.weight, 0);
  for (let roll = 0; roll < THORN_COURT_CACHE_TABLE.rolls; roll++) {
    let cursor = boundedRandom(random) * total;
    const spec = THORN_COURT_CACHE_TABLE.entries.find(entry => ((cursor -= entry.weight) < 0)) ?? THORN_COURT_CACHE_TABLE.entries.at(-1);
    output.push({ typeId: spec.typeId, amount: count(spec, random) });
  }
  return output;
}

function ancientTotemLodestone(dimension, barrelLocation) {
  const matches = rotations(THORN_COURT_CACHE_OFFSET).map(offset => at(barrelLocation, { x: -offset.x, y: -offset.y, z: -offset.z })).filter(location => {
    const center = dimension.getBlock?.(location), signature = dimension.getBlock?.({ x: location.x, y: location.y + 1, z: location.z });
    return center?.typeId === "minecraft:lodestone" && signature?.typeId === "aionbound:hollow_wood";
  });
  return matches.length === 1 ? matches[0] : null;
}

function resolveCache(dimension, center) {
  const matches = rotations(THORN_COURT_CACHE_OFFSET).map(offset => dimension.getBlock?.(at(center, offset))).filter(block =>
    block?.typeId === "minecraft:barrel" && ancientTotemLodestone(dimension, block.location));
  return matches.length === 1 ? matches[0] : null;
}

function content(container) {
  const items = [];
  for (let slot = 0; slot < container.size; slot++) {
    const item = container.getItem(slot);
    if (item) items.push(item);
  }
  return items;
}

export function createWhisperwoodRewardHooks({ ItemStack, random = Math.random }) {
  const openedCaches = new Set();

  function grantMaterialPackage(player) {
    const packageItems = rollThornCourtMaterials(random), container = player.getComponent?.("minecraft:inventory")?.container;
    try {
      for (const item of packageItems) {
        const stack = new ItemStack(item.typeId, item.amount);
        const remainder = container?.addItem ? container.addItem(stack) : stack;
        if (remainder) player.dimension.spawnItem(remainder, player.location);
      }
      return true;
    } catch {
      return false;
    }
  }

  function openArenaChest({ dimension, center }) {
    const block = resolveCache(dimension, center), container = inventory(block);
    if (!block || !container) return false;
    const existing = content(container);
    // Never erase player storage or an unknown external mutation. Prior arena
    // cache contents may be replaced on a ratified repeat clear.
    if (existing.some(item => !CACHE_TYPES.has(item.typeId))) return false;
    const packageItems = rollThornCourtCache(random);
    if (packageItems.length > container.size) return false;
    try {
      for (let slot = 0; slot < container.size; slot++) container.setItem(slot, undefined);
      for (let slot = 0; slot < packageItems.length; slot++) {
        const item = packageItems[slot];
        container.setItem(slot, new ItemStack(item.typeId, item.amount));
      }
      openedCaches.add(key(dimension, block.location));
      return true;
    } catch {
      return false;
    }
  }

  function guardArenaCacheInteraction(event) {
    const block = event.block, dimension = block?.dimension ?? event.player?.dimension;
    if (block?.typeId !== "minecraft:barrel" || !dimension || !ancientTotemLodestone(dimension, block.location)) return false;
    const items = inventory(block) ? content(inventory(block)) : [];
    const unlocked = openedCaches.has(key(dimension, block.location)) || (items.length > 0 && items.every(item => CACHE_TYPES.has(item.typeId)));
    if (!unlocked) event.cancel = true;
    return !unlocked;
  }

  return Object.freeze({ grantMaterialPackage, openArenaChest, guardArenaCacheInteraction });
}
