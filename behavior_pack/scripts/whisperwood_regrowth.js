const SAPLING = "aionbound:whisperwood_sapling";
const STRUCTURE = "aionbound:ww_sapling_growth_tree";
const SOILS = new Set([
  "minecraft:grass_block",
  "minecraft:dirt",
  "minecraft:coarse_dirt",
  "minecraft:podzol",
  "minecraft:moss_block",
]);

function occupiedOffsets() {
  const blocks = new Map();
  const put = (x, y, z, type) => blocks.set(`${x},${y},${z}`, { x, y, z, type });
  for (let y = 0; y < 6; y++) put(3, y, 3, "log");
  for (const [x, y, z] of [[2, 0, 3], [4, 0, 3], [3, 0, 2], [3, 0, 4], [1, 0, 3], [3, 0, 5]]) put(x, y, z, "roots");
  for (const [x, y, z] of [[2, 4, 3], [4, 4, 3], [3, 5, 2], [3, 5, 4]]) put(x, y, z, "log");
  for (const [y, cx, cz, radius] of [[4, 3, 3, 3], [5, 3, 3, 3], [6, 3, 3, 2], [7, 3, 2, 2]]) {
    for (let x = 0; x < 7; x++) for (let z = 0; z < 7; z++) {
      if (Math.abs(x - cx) + Math.abs(z - cz) <= radius && (x + 2 * z + y) % 5 !== 0) {
        const key = `${x},${y},${z}`;
        if (!blocks.has(key)) put(x, y, z, "leaves");
      }
    }
  }
  for (const [x, y, z] of [[3, 8, 2], [2, 8, 2], [3, 8, 1], [4, 7, 4]]) put(x, y, z, "leaves");
  for (const [x, y, z] of [[4, 2, 3], [2, 4, 3], [3, 6, 4]]) put(x, y, z, "moss");
  return Object.freeze([...blocks.values()].map(({ x, y, z }) => Object.freeze({ x: x - 3, y, z: z - 3 })));
}

export const WHISPERWOOD_TREE_OFFSETS = occupiedOffsets();

function blockAt(dimension, location) {
  try { return dimension.getBlock(location); } catch { return undefined; }
}

function canGrow(block) {
  if (!block || block.typeId !== SAPLING) return false;
  const { x, y, z } = block.location;
  if (!SOILS.has(blockAt(block.dimension, { x, y: y - 1, z })?.typeId)) return false;
  for (const offset of WHISPERWOOD_TREE_OFFSETS) {
    if (offset.x === 0 && offset.y === 0 && offset.z === 0) continue;
    if (blockAt(block.dimension, { x: x + offset.x, y: y + offset.y, z: z + offset.z })?.typeId !== "minecraft:air") return false;
  }
  return true;
}

function attemptGrowth(world, block) {
  if (!canGrow(block)) return false;
  const { x, y, z } = block.location;
  try {
    world.structureManager.place(STRUCTURE, block.dimension, { x: x - 3, y, z: z - 3 });
    return true;
  } catch {
    return false;
  }
}

function heldBoneMeal(player) {
  const container = player?.getComponent("minecraft:inventory")?.container;
  const slot = player?.selectedSlotIndex;
  const item = Number.isInteger(slot) ? container?.getItem(slot) : undefined;
  return item?.typeId === "minecraft:bone_meal" ? { container, slot, item } : undefined;
}

function consumeBoneMeal(player, held) {
  if (player.getGameMode?.() === "creative") return;
  if (held.item.amount > 1) {
    held.item.amount--;
    held.container.setItem(held.slot, held.item);
  } else held.container.setItem(held.slot, undefined);
}

export function createWhisperwoodRegrowthComponent({ world, random = Math.random }) {
  return {
    onTick(event) { attemptGrowth(world, event.block); },
    onPlayerInteract(event) {
      const held = heldBoneMeal(event.player);
      if (!held || random() >= 1 / 3) return;
      if (attemptGrowth(world, event.block)) consumeBoneMeal(event.player, held);
    },
  };
}

export function registerWhisperwoodRegrowth(startupEvent, world, random = Math.random) {
  startupEvent.blockComponentRegistry.registerCustomComponent(
    "aionbound:whisperwood_sapling_regrowth",
    createWhisperwoodRegrowthComponent({ world, random }),
  );
}
