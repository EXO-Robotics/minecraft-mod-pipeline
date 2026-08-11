import { CRYSTAL_REWARD_CONTRACT, CRYSTAL_STRUCTURE_SIGNATURES, PEARL_DEPTHS_CACHE_TABLE, PEARL_DEPTHS_MATERIAL_TABLE } from "./crystal_reward_data.js";

export { CRYSTAL_REWARD_CONTRACT, CRYSTAL_STRUCTURE_SIGNATURES, PEARL_DEPTHS_CACHE_TABLE, PEARL_DEPTHS_MATERIAL_TABLE };

const rotations = ({ x, y, z }) => [{ x, y, z }, { x: z, y, z: -x }, { x: -x, y, z: -z }, { x: -z, y, z: x }];
const at = (origin, offset) => ({ x: origin.x + offset.x, y: origin.y + offset.y, z: origin.z + offset.z });
const locationKey = block => `${block?.dimension?.id ?? "minecraft:overworld"}:${Math.floor(block.location.x)},${Math.floor(block.location.y)},${Math.floor(block.location.z)}`;
const boundedRandom = random => {
  const value = Number(random());
  return Number.isFinite(value) ? Math.max(0, Math.min(.999999999999, value)) : 0;
};
const randomCount = (range, random) => range[0] + Math.floor(boundedRandom(random) * (range[1] - range[0] + 1));

function matchingDeepPoolAnchor(dimension, barrelLocation) {
  const contract = CRYSTAL_REWARD_CONTRACT.deepPoolCache, matches = [];
  for (let rotationIndex = 0; rotationIndex < 4; rotationIndex++) {
    const cacheOffset = rotations(contract.cacheOffset)[rotationIndex];
    const anchor = dimension.getBlock?.(at(barrelLocation, { x: -cacheOffset.x, y: -cacheOffset.y, z: -cacheOffset.z }));
    if (anchor?.typeId !== contract.anchorType) continue;
    if (!contract.probes.every(probe => {
      const offset = rotations(probe.offset)[rotationIndex];
      return dimension.getBlock?.(at(anchor.location, offset))?.typeId === probe.typeId;
    })) continue;
    matches.push({ anchor, rotationIndex });
  }
  return matches.length === 1 ? matches[0] : null;
}

function signatureMatches(block, signature, rotationIndex) {
  if (block?.typeId !== signature.anchorType || !block.dimension) return false;
  return signature.probes.every(probe => {
    const offset = rotations(probe.offset)[rotationIndex];
    return block.dimension.getBlock?.(at(block.location, offset))?.typeId === probe.typeId;
  });
}

export function identifyCrystalStructureActivation(block) {
  const matches = [];
  for (const signature of CRYSTAL_STRUCTURE_SIGNATURES) {
    for (let rotationIndex = 0; rotationIndex < 4; rotationIndex++) {
      if (signatureMatches(block, signature, rotationIndex)) matches.push({ signature, rotationIndex });
    }
  }
  if (matches.length !== 1) return null;
  const match = matches[0];
  return Object.freeze({
    structure: match.signature.structure,
    anchorId: match.signature.anchorId,
    rotationIndex: match.rotationIndex,
    stamp: `landmark:${match.signature.structure}`,
  });
}

function hasOneItemCapacity(container, typeId, ItemStack) {
  if (!container || typeof ItemStack !== "function") return false;
  if (Number.isFinite(container.emptySlotsCount) && container.emptySlotsCount > 0) return true;
  for (let slot = 0; slot < (container.size ?? 0); slot++) {
    const item = container.getItem?.(slot);
    if (!item) return true;
    if (item.typeId === typeId && item.amount < (item.maxAmount ?? 64)) return true;
  }
  return false;
}

function weighted(entries, random) {
  const total = entries.reduce((sum, entry) => sum + entry.weight, 0);
  let cursor = boundedRandom(random) * total;
  return entries.find(entry => ((cursor -= entry.weight) < 0)) ?? entries.at(-1);
}

export function rollCrystalRewardTable(table, random = Math.random) {
  const output = [];
  for (const pool of table.pools) {
    const rolls = randomCount(pool.rolls, random);
    for (let index = 0; index < rolls; index++) {
      const selected = weighted(pool.entries, random);
      output.push({ typeId: selected.typeId, amount: randomCount([selected.min, selected.max], random) });
    }
  }
  return output;
}

function blockInventory(block) { return block?.getComponent?.("minecraft:inventory")?.container; }
function contents(container) {
  const items = [];
  for (let slot = 0; slot < (container?.size ?? 0); slot++) {
    const item = container.getItem(slot); if (item) items.push(item);
  }
  return items;
}

export function createCrystalRewardHooks({ ItemStack, state, random = Math.random }) {
  const openedArenaCaches = new Set();
  const arenaTypes = new Set(PEARL_DEPTHS_CACHE_TABLE.pools.flatMap(pool => pool.entries.map(entry => entry.typeId)));

  function canDeliverMask(player, typeId = CRYSTAL_REWARD_CONTRACT.chapterSeal) {
    return hasOneItemCapacity(player.getComponent?.("minecraft:inventory")?.container, typeId, ItemStack);
  }

  function deliverMask(player, typeId = CRYSTAL_REWARD_CONTRACT.chapterSeal) {
    const container = player.getComponent?.("minecraft:inventory")?.container;
    if (!container?.addItem || !hasOneItemCapacity(container, typeId, ItemStack)) return false;
    try { return !container.addItem(new ItemStack(typeId, 1)); }
    catch { return false; }
  }

  function grantMaterialPackage(player, context) {
    if (context?.encounterId !== CRYSTAL_REWARD_CONTRACT.encounterId) return false;
    const container = player.getComponent?.("minecraft:inventory")?.container;
    try {
      for (const item of rollCrystalRewardTable(PEARL_DEPTHS_MATERIAL_TABLE, random)) {
        const stack = new ItemStack(item.typeId, item.amount);
        const remainder = container?.addItem ? container.addItem(stack) : stack;
        if (remainder) player.dimension.spawnItem(remainder, player.location);
      }
      return true;
    } catch { return false; }
  }

  function openArenaCache(context) {
    if (context?.validClear !== true) return false;
    if (context.arena?.formId !== "deep_pool_entrance") return false;
    const offset = rotations(CRYSTAL_REWARD_CONTRACT.deepPoolCache.cacheOffset)[context.arena.rotationIndex];
    const location = at(context.arena.anchor, offset), block = context.arena.dimension.getBlock?.(location), container = blockInventory(block);
    if (block?.typeId !== "minecraft:barrel" || !container) return false;
    const existing = contents(container);
    if (existing.some(item => !arenaTypes.has(item.typeId))) return false;
    const items = rollCrystalRewardTable(PEARL_DEPTHS_CACHE_TABLE, random);
    if (items.length > container.size) return false;
    try {
      for (let slot = 0; slot < container.size; slot++) container.setItem(slot, undefined);
      for (let slot = 0; slot < items.length; slot++) container.setItem(slot, new ItemStack(items[slot].typeId, items[slot].amount));
      openedArenaCaches.add(`${context.arena.dimensionId}:${Math.floor(location.x)},${Math.floor(location.y)},${Math.floor(location.z)}`);
      return true;
    } catch { return false; }
  }

  function guardArenaCacheInteraction(event) {
    const block = event.block, dimension = block?.dimension ?? event.player?.dimension;
    if (block?.typeId !== CRYSTAL_REWARD_CONTRACT.deepPoolCache.cacheType || !dimension) return false;
    if (!matchingDeepPoolAnchor(dimension, block.location)) return false;
    const worldState = state.worldState();
    const completed = worldState.encounters.terminal["aionbound.encounter.pearl_depths.completed.v1"]?.completed === true;
    const unlocked = completed || openedArenaCaches.has(locationKey(block));
    if (!unlocked) event.cancel = true;
    return !unlocked;
  }

  return Object.freeze({ canDeliverMask, deliverMask, grantMaterialPackage, openArenaCache, guardArenaCacheInteraction, identifyStructureActivation: identifyCrystalStructureActivation });
}
