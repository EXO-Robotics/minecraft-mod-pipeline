// Runtime-facing contract for the ratified Crystal Marsh economy. The
// protected loot-table bytes are supplied by the economy lane; Pearl Depths
// consumes only these exact paths and identities.
export const CRYSTAL_REWARD_CONTRACT = Object.freeze({
  chapterSeal: "aionbound:marsh_wight_mask",
  encounterId: "aionbound:pearl_depths",
  materialTablePath: "loot_tables/encounters/crystal/pearl_depths_materials.json",
  arenaCacheTablePath: "loot_tables/chests/crystal/pearl_depths.json",
  optionalMasteryItems: Object.freeze([
    "aionbound:moon_pearl_pedestal",
    "aionbound:crystal_obelisk_fragment",
    "aionbound:marsh_idol",
  ]),
  progressionSubstitutes: Object.freeze([]),
  deepPoolCache: Object.freeze({
    anchorType: "minecraft:lodestone",
    cacheType: "minecraft:barrel",
    cacheOffset: Object.freeze({ x: -4, y: 1, z: -3 }),
    probes: Object.freeze([
      Object.freeze({ offset: Object.freeze({ x: -3, y: 0, z: -3 }), typeId: "aionbound:algae_block" }),
      Object.freeze({ offset: Object.freeze({ x: 6, y: 1, z: 4 }), typeId: "aionbound:crystal_stone" }),
    ]),
  }),
});

// Semantic mirrors of the protected Bedrock tables. Focused tests bind these
// pools, weights, counts, and roll ranges back to the JSON package bytes.
export const PEARL_DEPTHS_MATERIAL_TABLE = Object.freeze({
  pools: Object.freeze([
    Object.freeze({ rolls: Object.freeze([2, 4]), entries: Object.freeze([
      Object.freeze({ typeId: "aionbound:wight_shroud", weight: 30, min: 1, max: 1 }),
      Object.freeze({ typeId: "aionbound:flood_crystal", weight: 40, min: 1, max: 3 }),
      Object.freeze({ typeId: "aionbound:crystal_root_item", weight: 30, min: 1, max: 2 }),
    ]) }),
    Object.freeze({ rolls: Object.freeze([1, 2]), entries: Object.freeze([
      Object.freeze({ typeId: "aionbound:prism_pearl", weight: 55, min: 1, max: 2 }),
      Object.freeze({ typeId: "aionbound:moon_pearl", weight: 45, min: 1, max: 2 }),
    ]) }),
  ]),
});

export const PEARL_DEPTHS_CACHE_TABLE = Object.freeze({
  pools: Object.freeze([
    Object.freeze({ rolls: Object.freeze([2, 2]), entries: Object.freeze([
      Object.freeze({ typeId: "aionbound:flood_crystal", weight: 45, min: 1, max: 3 }),
      Object.freeze({ typeId: "aionbound:crystal_root_item", weight: 30, min: 1, max: 2 }),
      Object.freeze({ typeId: "aionbound:wight_shroud", weight: 25, min: 1, max: 1 }),
    ]) }),
    Object.freeze({ rolls: Object.freeze([2, 4]), entries: Object.freeze([
      Object.freeze({ typeId: "aionbound:prism_pearl", weight: 30, min: 1, max: 2 }),
      Object.freeze({ typeId: "aionbound:moon_pearl", weight: 25, min: 1, max: 2 }),
      Object.freeze({ typeId: "aionbound:wight_shroud", weight: 20, min: 1, max: 1 }),
      Object.freeze({ typeId: "aionbound:watcher_lens", weight: 15, min: 1, max: 1 }),
      Object.freeze({ typeId: "aionbound:silt_core", weight: 10, min: 1, max: 1 }),
    ]) }),
  ]),
});

const probe = (x, y, z, typeId) => Object.freeze({ offset: Object.freeze({ x, y, z }), typeId });
const signature = (structure, anchorId, anchorType, probes) => Object.freeze({ structure, anchorId, anchorType, probes: Object.freeze(probes) });

// One exact authored handoff anchor per Crystal structure. These signatures
// are derived from the committed mcstructure authoring coordinates; they do
// not introduce proximity radii or synthetic marker blocks.
export const CRYSTAL_STRUCTURE_SIGNATURES = Object.freeze([
  signature("flooded_dock", "flooded_dock_cache", "minecraft:barrel", [probe(-8, 0, 1, "minecraft:lectern"), probe(0, -1, 0, "aionbound:flood_planks"), probe(1, 0, -1, "aionbound:marsh_wood")]),
  signature("ancient_boat", "ancient_boat_locker", "minecraft:barrel", [probe(-5, 0, 0, "aionbound:crystal_log"), probe(-5, 4, 0, "aionbound:flood_planks"), probe(-1, 0, 3, "aionbound:marsh_wood")]),
  signature("marsh_broken_bridge", "marsh_bridge_route", "minecraft:lodestone", [probe(11, 1, 0, "minecraft:barrel"), probe(0, 1, 0, "aionbound:flood_planks"), probe(3, -1, 0, "aionbound:crystal_log")]),
  signature("pearl_cairn", "pearl_cairn_cache", "minecraft:barrel", [probe(0, 4, -3, "aionbound:prism_brick"), probe(0, 0, -1, "aionbound:crystal_stone"), probe(0, -1, 0, "aionbound:crystal_gravel")]),
  signature("marsh_totem", "marsh_totem_altar", "minecraft:lodestone", [probe(-3, 0, -1, "minecraft:lectern"), probe(0, 0, -3, "aionbound:marsh_wood"), probe(0, 3, -3, "aionbound:glass_root_block")]),
  signature("crystal_arch", "crystal_arch_cache", "minecraft:barrel", [probe(0, 13, -2, "aionbound:prismglass_signal"), probe(-5, 1, -2, "aionbound:crystal_stone"), probe(-5, 11, -2, "aionbound:prism_brick")]),
  signature("crystal_obelisk", "crystal_obelisk_stamp", "minecraft:lodestone", [probe(-3, 0, -4, "minecraft:barrel"), probe(0, 15, -4, "aionbound:prismglass_signal"), probe(0, 0, -1, "aionbound:crystal_stone")]),
  signature("sunken_shrine", "sunken_shrine_altar", "minecraft:lodestone", [probe(0, -1, 0, "aionbound:glass_root_block"), probe(5, -3, 0, "minecraft:lectern"), probe(5, 4, -5, "aionbound:prism_brick")]),
  signature("ruined_observatory", "ruined_observatory_chart", "minecraft:lectern", [probe(10, 0, 0, "minecraft:barrel"), probe(5, 0, 0, "aionbound:crystal_log"), probe(5, 15, -2, "aionbound:prismglass_signal")]),
  signature("deep_pool_entrance", "deep_pool_depth", "minecraft:lodestone", [probe(-4, 1, -3, "minecraft:barrel"), probe(-3, 0, -3, "aionbound:algae_block"), probe(6, 1, 4, "aionbound:crystal_stone")]),
]);
