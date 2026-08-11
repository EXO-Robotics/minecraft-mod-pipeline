import { ASHEN_STRUCTURE_CHEST_TABLES, ASHEN_STRUCTURE_SIGNATURES } from "./ashen_structure_reward_data.js";

export { ASHEN_STRUCTURE_CHEST_TABLES, ASHEN_STRUCTURE_SIGNATURES };
export const EMBER_FORGE_CACHE_OFFSET = Object.freeze({ x: 6, y: 0, z: 0 });

const rotations = ({ x, y, z }) => [
  { x, y, z }, { x: z, y, z: -x }, { x: -x, y, z: -z }, { x: -z, y, z: x },
];
const at = (origin, offset) => ({ x: origin.x + offset.x, y: origin.y + offset.y, z: origin.z + offset.z });
const boundedRandom = random => {
  const value = Number(random());
  return Number.isFinite(value) ? Math.max(0, Math.min(0.999999999999, value)) : 0;
};
const randomCount = (range, random) => range[0] + Math.floor(boundedRandom(random) * (range[1] - range[0] + 1));
const inventory = block => block?.getComponent?.("minecraft:inventory")?.container;
const locationKey = block => `${block?.dimension?.id ?? "minecraft:overworld"}:${Math.floor(block.location.x)},${Math.floor(block.location.y)},${Math.floor(block.location.z)}`;

function weighted(entries, random) {
  const total = entries.reduce((sum, entry) => sum + entry.weight, 0);
  let cursor = boundedRandom(random) * total;
  return entries.find(entry => ((cursor -= entry.weight) < 0)) ?? entries.at(-1);
}

export function rollAshenStructureTable(tableId, random = Math.random) {
  const table = ASHEN_STRUCTURE_CHEST_TABLES[tableId];
  if (!table) return [];
  const output = [];
  for (const pool of [
    { rolls: [table.guaranteedRolls, table.guaranteedRolls], entries: table.guaranteed },
    { rolls: table.choiceRolls, entries: table.choice },
  ]) {
    const rolls = randomCount(pool.rolls, random);
    for (let roll = 0; roll < rolls; roll++) {
      const spec = weighted(pool.entries, random);
      output.push({ typeId: spec.typeId, amount: randomCount([spec.min, spec.max], random) });
    }
  }
  return output;
}

function signatureMatches(dimension, anchorBlock, signature) {
  if (!dimension || anchorBlock?.typeId !== signature.anchor_type) return false;
  return rotations({ x: 0, y: 0, z: 0 }).some((_unused, rotationIndex) => signature.probes.every(probe => {
    const rotated = rotations({ x: probe.offset[0], y: probe.offset[1], z: probe.offset[2] })[rotationIndex];
    return dimension.getBlock?.(at(anchorBlock.location, rotated))?.typeId === probe.expected_block;
  }));
}

export function identifyAshenStructureActivation(block) {
  const dimension = block?.dimension;
  const matches = ASHEN_STRUCTURE_SIGNATURES.filter(signature => signatureMatches(dimension, block, signature));
  if (matches.length !== 1) return null;
  return Object.freeze({ structure: matches[0].structure, anchorId: matches[0].anchor_id, stamp: matches[0].stamp });
}

function emberForgeCenter(dimension, barrelLocation) {
  const arenaSignature = ASHEN_STRUCTURE_SIGNATURES.find(value => value.anchor_id === "ember_forge_arena");
  const candidates = rotations(EMBER_FORGE_CACHE_OFFSET).map(offset => dimension.getBlock?.(at(barrelLocation, { x: -offset.x, y: -offset.y, z: -offset.z }))).filter(block => signatureMatches(dimension, block, arenaSignature));
  return candidates.length === 1 ? candidates[0] : null;
}

function resolveEmberForgeCache(dimension, center) {
  const matches = rotations(EMBER_FORGE_CACHE_OFFSET).map(offset => dimension.getBlock?.(at(center, offset))).filter(block => block?.typeId === "minecraft:barrel" && emberForgeCenter(dimension, block.location));
  return matches.length === 1 ? matches[0] : null;
}

function contents(container) {
  const output = [];
  for (let slot = 0; slot < container.size; slot++) {
    const item = container.getItem(slot);
    if (item) output.push(item);
  }
  return output;
}

export function createAshenStructureRewardHooks({ ItemStack, random = Math.random }) {
  const openedArenaCaches = new Set();
  const arenaTypes = new Set([...ASHEN_STRUCTURE_CHEST_TABLES.ember_forge.guaranteed, ...ASHEN_STRUCTURE_CHEST_TABLES.ember_forge.choice].map(entry => entry.typeId));

  function grantTable(player, tableId) {
    const packageItems = rollAshenStructureTable(tableId, random);
    const container = player.getComponent?.("minecraft:inventory")?.container;
    try {
      for (const item of packageItems) {
        const stack = new ItemStack(item.typeId, item.amount);
        const remainder = container?.addItem ? container.addItem(stack) : stack;
        if (remainder) player.dimension.spawnItem(remainder, player.location);
      }
      return packageItems.length > 0;
    } catch {
      return false;
    }
  }

  function openArenaCache({ dimension, center, validClear = false }) {
    if (validClear !== true) return false;
    const block = resolveEmberForgeCache(dimension, center), container = inventory(block);
    if (!block || !container) return false;
    const existing = contents(container);
    if (existing.some(item => !arenaTypes.has(item.typeId))) return false;
    const packageItems = rollAshenStructureTable("ember_forge", random);
    if (packageItems.length > container.size) return false;
    try {
      for (let slot = 0; slot < container.size; slot++) container.setItem(slot, undefined);
      for (let slot = 0; slot < packageItems.length; slot++) {
        const item = packageItems[slot];
        container.setItem(slot, new ItemStack(item.typeId, item.amount));
      }
      openedArenaCaches.add(locationKey(block));
      return true;
    } catch {
      return false;
    }
  }

  function guardArenaCacheInteraction(event) {
    const block = event.block, dimension = block?.dimension ?? event.player?.dimension;
    if (block?.typeId !== "minecraft:barrel" || !dimension || !emberForgeCenter(dimension, block.location)) return false;
    const items = inventory(block) ? contents(inventory(block)) : [];
    const unlocked = openedArenaCaches.has(locationKey(block)) || (items.length > 0 && items.every(item => arenaTypes.has(item.typeId)));
    if (!unlocked) event.cancel = true;
    return !unlocked;
  }

  return Object.freeze({ grantTable, openArenaCache, guardArenaCacheInteraction, identifyStructureActivation: identifyAshenStructureActivation });
}
