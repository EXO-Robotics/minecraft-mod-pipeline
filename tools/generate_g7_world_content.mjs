import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";

const root = path.resolve(import.meta.dirname, "..");
const writeJson = (relative, value) => {
  const target = path.join(root, relative);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, `${JSON.stringify(value, null, 2)}\n`);
};
const title = id => id.split("_").map(part => part[0].toUpperCase() + part.slice(1)).join(" ");

const blocks = [
  ["ferrowake_ore", "#423c3a", "#d4814d"], ["ferrowake_bricks", "#694c3d", "#c0774f"],
  ["cut_ferrowake", "#765243", "#de8c56"], ["ferrowake_grate", "#302c2b", "#bf6f45"],
  ["riveted_ferrowake", "#4b4240", "#d58b5f"], ["ferrowake_beam", "#3b3433", "#92543c"],
  ["ferrowake_lamp", "#43332e", "#ffb45e"], ["salvage_bench", "#4e4035", "#d18b50"],
  ["aionite_ore", "#343c53", "#65d8ff"], ["charged_aionite_block", "#244c69", "#8df4ff"],
  ["prismglass_framed", "#43606b", "#a6f4ff"], ["prismglass_frosted", "#7596a0", "#d7fbff"],
  ["prismglass_signal", "#345a6d", "#66ffdc"], ["rootglass_mosaic", "#466253", "#a3e188"],
  ["rootglass_lantern", "#354a40", "#b9ff9a"], ["resonance_press", "#30384a", "#74c9ff"],
  ["lumen_salt_cluster", "#b5a67e", "#fff2a6"], ["lumen_stone", "#766d56", "#e5d18b"],
  ["carved_lumen_stone", "#80765b", "#fff0a3"], ["lumen_inlay", "#665f4e", "#ffd868"],
  ["lumen_brazier", "#4b4133", "#ffbd56"], ["trophy_plinth", "#4c4558", "#d8baff"],
  ["codex_lectern", "#493b2e", "#77d8c8"], ["survey_relay", "#323d4b", "#6be4ff"],
  ["rootglass_nodule", "#435746", "#b7f59c"], ["mite_resin_block", "#5b3f2d", "#dd9b45"],
  ["woven_nest", "#66513b", "#d8b879"], ["relic_sandstone", "#aa8f67", "#e5ce9a"],
  ["fossil_rib_block", "#80745f", "#d8ceb1"], ["storm_slate_tiles", "#39465c", "#708ebd"],
  ["brinewood_beam", "#3d5b53", "#7aa28e"], ["resonant_lamp", "#423d58", "#d798ff"]
];

const parseHex = color => color.slice(1).match(/../g).map(value => Number.parseInt(value, 16));
const crcTable = Array.from({ length: 256 }, (_, n) => {
  let c = n;
  for (let k = 0; k < 8; k += 1) c = (c & 1) ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
const crc32 = data => {
  let c = 0xffffffff;
  for (const byte of data) c = crcTable[(c ^ byte) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
};
const chunk = (type, data) => {
  const typeBytes = Buffer.from(type);
  const out = Buffer.alloc(12 + data.length);
  out.writeUInt32BE(data.length, 0); typeBytes.copy(out, 4); data.copy(out, 8);
  out.writeUInt32BE(crc32(Buffer.concat([typeBytes, data])), 8 + data.length);
  return out;
};
const png = (base, accent, seed) => {
  const [br, bg, bb] = parseHex(base); const [ar, ag, ab] = parseHex(accent);
  const raw = Buffer.alloc(16 * (1 + 16 * 4));
  for (let y = 0; y < 16; y += 1) {
    raw[y * 65] = 0;
    for (let x = 0; x < 16; x += 1) {
      const o = y * 65 + 1 + x * 4;
      const mark = ((x * 7 + y * 11 + seed) % 13 < 3) || ((x + seed) % 8 === 0 && y % 4 === 0);
      const shade = ((x + y + seed) % 3) - 1;
      raw[o] = Math.max(0, Math.min(255, (mark ? ar : br) + shade * 8));
      raw[o + 1] = Math.max(0, Math.min(255, (mark ? ag : bg) + shade * 8));
      raw[o + 2] = Math.max(0, Math.min(255, (mark ? ab : bb) + shade * 8));
      raw[o + 3] = 255;
    }
  }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(16, 0); ihdr.writeUInt32BE(16, 4); ihdr.set([8, 6, 0, 0, 0], 8);
  return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]), chunk("IHDR", ihdr), chunk("IDAT", zlib.deflateSync(raw, { level: 9 })), chunk("IEND", Buffer.alloc(0))]);
};

for (const [id, base, accent] of blocks) {
  writeJson(`behavior_pack/blocks/${id}.block.json`, {
    format_version: "1.21.80",
    "minecraft:block": {
      description: { identifier: `aionbound:${id}`, menu_category: { category: "construction" } },
      components: {
        "minecraft:display_name": title(id),
        "minecraft:destructible_by_mining": { seconds_to_destroy: id.includes("ore") || id.includes("nodule") || id.includes("cluster") ? 3.5 : 2 },
        "minecraft:geometry": "minecraft:geometry.full_block",
        "minecraft:material_instances": { "*": { texture: id, render_method: id.includes("glass") || id.includes("grate") ? "alpha_test" : "opaque" } }
      }
    }
  });
  fs.writeFileSync(path.join(root, `resource_pack/textures/aionbound/${id}.png`), png(base, accent, id.length));
}
const terrainPath = path.join(root, "resource_pack/textures/terrain_texture.json");
const terrain = JSON.parse(fs.readFileSync(terrainPath));
const blockCatalogPath = path.join(root, "resource_pack/blocks.json");
const blockCatalog = JSON.parse(fs.readFileSync(blockCatalogPath));
for (const [id] of blocks) {
  terrain.texture_data[id] = { textures: `textures/aionbound/${id}` };
  blockCatalog[`aionbound:${id}`] = { sound: id.includes("beam") || id.includes("nest") || id.includes("bench") || id.includes("lectern") ? "wood" : "stone", textures: id };
}
writeJson("resource_pack/textures/terrain_texture.json", terrain);
writeJson("resource_pack/blocks.json", blockCatalog);

const itemAtlasPath = path.join(root, "resource_pack/textures/item_texture.json");
const itemAtlas = JSON.parse(fs.readFileSync(itemAtlasPath));
for (const itemPath of fs.readdirSync(path.join(root, "behavior_pack/items")).filter(name => name.endsWith(".json")).sort()) {
  const document = JSON.parse(fs.readFileSync(path.join(root, "behavior_pack/items", itemPath)));
  const identifier = document["minecraft:item"].description.identifier;
  const id = identifier.split(":", 2)[1];
  const texturePath = path.join(root, `resource_pack/textures/aionbound/${id}.png`);
  if (!fs.existsSync(texturePath)) fs.writeFileSync(texturePath, png("#3f4858", "#78e0c5", id.length));
  itemAtlas.texture_data[id] = { textures: `textures/aionbound/${id}` };
}
writeJson("resource_pack/textures/item_texture.json", itemAtlas);

const lang = ["pack.name=Aionbound Core Content Beta", "pack.description=Generation 7 expanded content beta"];
for (const folder of ["blocks", "items", "entities"]) {
  for (const name of fs.readdirSync(path.join(root, `behavior_pack/${folder}`)).filter(value => value.endsWith(".json")).sort()) {
    const document = JSON.parse(fs.readFileSync(path.join(root, `behavior_pack/${folder}`, name)));
    const component = folder === "blocks" ? "minecraft:block" : folder === "items" ? "minecraft:item" : "minecraft:entity";
    const body = document[component]; const id = body.description.identifier.split(":", 2)[1];
    const rawName = body.components?.["minecraft:display_name"];
    const label = typeof rawName === "string" ? rawName : rawName?.value ?? title(id);
    const key = folder === "blocks" ? `tile.aionbound:${id}.name` : folder === "items" ? `item.aionbound:${id}` : `entity.aionbound:${id}.name`;
    lang.push(`${key}=${label}`);
  }
}
fs.writeFileSync(path.join(root, "resource_pack/texts/en_US.lang"), `${lang.join("\n")}\n`);

const oreSpecs = [
  ["ferrowake_ore", 7, -16, 64, 4], ["aionite_ore", 5, -48, 12, 3],
  ["lumen_salt_cluster", 6, -24, 48, 3], ["rootglass_nodule", 4, -32, 24, 2]
];
for (const [id, count, ymin, ymax, iterations] of oreSpecs) {
  writeJson(`behavior_pack/features/${id}.ore_feature.json`, {
    format_version: "1.21.10",
    "minecraft:ore_feature": {
      description: { identifier: `aionbound:${id}_ore_feature` }, count, discard_chance_on_air_exposure: 0.25,
      replace_rules: [{ places_block: `aionbound:${id}`, may_replace: ["minecraft:stone", "minecraft:deepslate"] }]
    }
  });
  writeJson(`behavior_pack/feature_rules/${id}.ore_feature_rule.json`, {
    format_version: "1.21.40",
    "minecraft:feature_rules": {
      description: { identifier: `aionbound:${id}.ore_feature_rule`, places_feature: `aionbound:${id}_ore_feature` },
      conditions: { placement_pass: "underground_pass", "minecraft:biome_filter": { test: "has_biome_tag", operator: "==", value: "overworld" } },
      distribution: { coordinate_eval_order: "xzy", iterations, scatter_chance: 1.0,
        x: { distribution: "uniform", extent: [0, 15] }, y: { distribution: "uniform", extent: [ymin, ymax] }, z: { distribution: "uniform", extent: [0, 15] } }
    }
  });
}

class Nbt {
  constructor() { this.parts = []; }
  u8(v) { const b = Buffer.alloc(1); b.writeUInt8(v); this.parts.push(b); }
  i32(v) { const b = Buffer.alloc(4); b.writeInt32LE(v); this.parts.push(b); }
  str(v) { const s = Buffer.from(v); const b = Buffer.alloc(2); b.writeUInt16LE(s.length); this.parts.push(b, s); }
  head(type, name) { this.u8(type); this.str(name); }
  int(name, value) { this.head(3, name); this.i32(value); }
  string(name, value) { this.head(8, name); this.str(value); }
  list(name, type, values, emit) { this.head(9, name); this.u8(type); this.i32(values.length); for (const value of values) emit(value); }
  listPayload(type, values, emit) { this.u8(type); this.i32(values.length); for (const value of values) emit(value); }
  compound(name, emit) { this.head(10, name); emit(); this.u8(0); }
  done() { return Buffer.concat(this.parts); }
}
const structure = (palette, size, indices) => {
  const n = new Nbt(); n.head(10, "");
  n.int("format_version", 1);
  n.list("size", 3, size, value => n.i32(value));
  n.list("structure_world_origin", 3, [0, 0, 0], value => n.i32(value));
  n.compound("structure", () => {
    n.list("block_indices", 9, [indices, Array(indices.length).fill(-1)], layer => n.listPayload(3, layer, value => n.i32(value)));
    n.list("entities", 10, [], () => {});
    n.compound("palette", () => n.compound("default", () => {
      n.list("block_palette", 10, palette, entry => {
        n.string("name", entry);
        n.compound("states", () => {});
        n.int("version", 18168865);
        n.u8(0);
      });
      n.compound("block_position_data", () => {});
    }));
  });
  n.u8(0); return n.done();
};

const sites = [
  ["mote_shrine", "lumen_brazier", "carved_lumen_stone", 192],
  ["collapsed_survey_camp", "survey_relay", "brinewood_beam", 224],
  ["ridge_nest", "woven_nest", "storm_slate_tiles", 256],
  ["scrap_cache", "salvage_bench", "riveted_ferrowake", 192],
  ["overgrown_waystation", "codex_lectern", "rootglass_mosaic", 224],
  ["broken_relay", "survey_relay", "charged_aionite_block", 320],
  ["pilgrim_cairn", "trophy_plinth", "lumen_stone", 256],
  ["lumen_seep", "lumen_salt_cluster", "lumen_inlay", 192],
  ["ferrowake_prospect", "ferrowake_ore", "ferrowake_beam", 192],
  ["warded_cellar", "resonant_lamp", "relic_sandstone", 384],
  ["burrow_breach", "rootglass_nodule", "mite_resin_block", 320],
  ["hunters_blind", "brinewood_beam", "woven_nest", 256],
  ["glassroot_grotto", "rootglass_lantern", "rootglass_mosaic", 640],
  ["silent_foundry", "resonance_press", "ferrowake_bricks", 768],
  ["lantern_causeway", "ferrowake_lamp", "storm_slate_tiles", 896]
];
for (const [id, focus, shell, denominator] of sites) {
  const size = id === "silent_foundry" || id === "lantern_causeway" || id === "glassroot_grotto" ? [9, 6, 9] : [7, 5, 7];
  const volume = size[0] * size[1] * size[2]; const indices = Array(volume).fill(0);
  const at = (x, y, z) => x + z * size[0] + y * size[0] * size[2];
  for (let z = 0; z < size[2]; z += 1) for (let x = 0; x < size[0]; x += 1) {
    if (x > 0 && z > 0 && x < size[0] - 1 && z < size[2] - 1) indices[at(x, 0, z)] = 2;
  }
  for (const [x, z] of [[1,1],[size[0]-2,1],[1,size[2]-2],[size[0]-2,size[2]-2]]) {
    for (let y = 1; y < Math.min(4, size[1]); y += 1) indices[at(x, y, z)] = 2;
  }
  indices[at(Math.floor(size[0] / 2), 1, Math.floor(size[2] / 2))] = 1;
  const target = path.join(root, `behavior_pack/structures/aionbound/${id}.mcstructure`);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, structure(["minecraft:air", `aionbound:${focus}`, `aionbound:${shell}`], size, indices));
  writeJson(`behavior_pack/features/${id}.structure_feature.json`, {
    format_version: "1.13.0",
    "minecraft:structure_template_feature": {
      description: { identifier: `aionbound:${id}_structure_feature` }, structure_name: `aionbound:${id}`,
      adjustment_radius: 4, facing_direction: "random",
      constraints: { grounded: {}, unburied: {}, block_intersection: { block_allowlist: ["minecraft:air", "minecraft:grass_block", "minecraft:dirt", "minecraft:stone", "minecraft:sand"] } }
    }
  });
  writeJson(`behavior_pack/feature_rules/${id}.structure_feature_rule.json`, {
    format_version: "1.13.0",
    "minecraft:feature_rules": {
      description: { identifier: `aionbound:${id}.structure_feature_rule`, places_feature: `aionbound:${id}_structure_feature` },
      conditions: { placement_pass: "surface_pass", "minecraft:biome_filter": { all_of: [
        { test: "has_biome_tag", operator: "==", value: "overworld" }, { test: "has_biome_tag", operator: "!=", value: "ocean" }
      ] } },
      distribution: { iterations: 1, scatter_chance: { numerator: 1, denominator },
        x: { distribution: "uniform", extent: [0, 15] }, y: "q.heightmap(v.worldx, v.worldz)", z: { distribution: "uniform", extent: [0, 15] } }
    }
  });
}

const lootPools = {
  wild_cache: ["aionbound:waystone_ration", "aionbound:pinion_feather_tuft", "aionbound:wayfinder_spool"],
  survey_cache: ["aionbound:charged_prism", "aionbound:stabilizing_chalk", "aionbound:quarry_lens"],
  nest: ["aionbound:mite_resin", "aionbound:anvil_chitin", "aionbound:brood_fang_daggers"],
  foundry: ["aionbound:tempered_ferrowake", "aionbound:miners_resin", "aionbound:salvage_magnet"],
  shrine: ["aionbound:prismatic_binder", "aionbound:lumen_draught", "aionbound:mote_lantern"],
  burrow: ["aionbound:woven_sinew", "aionbound:prism_dew_crystal", "aionbound:pilgrim_clasp"],
  elite: ["aionbound:trophy_relic_tooth", "aionbound:roc_pinion_glaive", "aionbound:ward_knot"],
  pilgrimage: ["aionbound:trophy_colossus_shard", "aionbound:behemoth_tusk_bow", "aionbound:trophy_codex"]
};
for (const [id, entries] of Object.entries(lootPools)) {
  writeJson(`behavior_pack/loot_tables/chests/${id}.json`, {
    pools: [
      { rolls: 1, entries: entries.slice(0, 2).map((name, index) => ({ type: "item", name, weight: index === 0 ? 3 : 2, functions: [{ function: "set_count", count: { min: 1, max: index === 0 ? 2 : 3 } }] })) },
      { rolls: 1, entries: [{ type: "item", name: entries[2], weight: 1 }, { type: "item", name: "minecraft:bread", weight: 3 }] }
    ]
  });
}

const blockRecipes = [
  ["ferrowake_bricks", ["TT", "TT"], { T: "aionbound:tempered_ferrowake" }, 4],
  ["ferrowake_lamp", [" T ", "TLT", " T "], { T: "aionbound:tempered_ferrowake", L: "aionbound:lumen_salt" }, 2],
  ["prismglass_framed", ["TGT", "GPG", "TGT"], { T: "aionbound:tempered_ferrowake", G: "minecraft:glass", P: "aionbound:prism_dew_crystal" }, 4],
  ["rootglass_mosaic", ["RR", "RR"], { R: "aionbound:rootglass_shard" }, 4],
  ["lumen_stone", ["SS", "SS"], { S: "aionbound:lumen_salt" }, 4],
  ["salvage_bench", ["TCT", "PBP", "T T"], { T: "aionbound:tempered_ferrowake", C: "aionbound:ferrowake_coupling", P: "minecraft:planks", B: "minecraft:crafting_table" }, 1],
  ["resonance_press", ["TCT", "RPR", "T T"], { T: "aionbound:tempered_ferrowake", C: "aionbound:resonance_coil", R: "minecraft:redstone", P: "minecraft:piston" }, 1],
  ["survey_relay", [" A ", "CSC", " T "], { A: "aionbound:aionite_crystal", C: "aionbound:charged_prism", S: "aionbound:survey_core", T: "aionbound:tempered_ferrowake" }, 1]
];
for (const [id, pattern, keys, count] of blockRecipes) {
  writeJson(`behavior_pack/recipes/${id}.recipe.json`, {
    format_version: "1.20.10",
    "minecraft:recipe_shaped": {
      description: { identifier: `aionbound:${id}_recipe` }, tags: ["crafting_table"], pattern,
      key: Object.fromEntries(Object.entries(keys).map(([key, item]) => [key, { item }])),
      result: { item: `aionbound:${id}`, count }, unlock: [{ item: Object.values(keys)[0] }]
    }
  });
}

console.log(JSON.stringify({ blocks: blocks.length, ores: oreSpecs.length, structures: sites.length, lootPools: Object.keys(lootPools).length, blockRecipes: blockRecipes.length }));
