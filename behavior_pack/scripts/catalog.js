import { WHISPERWOOD_CODEX_ENTRIES, WAVE1_CODEX_EVENT_INDEX, WAVE1_CODEX_REGISTRY_VERSION } from "./wave1_codex_data.js";

export const IDS = Object.freeze({
  world: "aionbound:core/world/v4",
  player: "aionbound:core/player/v4",
  oldWorldV3: "aionbound:core/world/v3",
  oldPlayerV3: "aionbound:core/player/v3",
  oldWorldV2: "aionbound:core/world/v2",
  oldPlayerV2: "aionbound:core/player/v2",
  oldWorldV1: "aionbound:core/world/v1",
  oldPlayerV1: "aionbound:core/player/v1",
});

// The registry is data-only. Presentation remains a separately authorized
// non-chat surface; the existing Codex chat page is retained as a fallback.
export const CODEX_ENTRY_REGISTRY = WHISPERWOOD_CODEX_ENTRIES;
export const CODEX_EVENT_INDEX = WAVE1_CODEX_EVENT_INDEX;
export const CODEX_REGISTRY_VERSION = WAVE1_CODEX_REGISTRY_VERSION;

export const PILGRIMAGE = Object.freeze({
  "aionbound:gloam_moss_block": "pilgrimage:gloam",
  "aionbound:brinewood_planks": "pilgrimage:brine",
  "aionbound:ember_vent_stone": "pilgrimage:vent",
  "aionbound:scorch_glass_shard_block": "pilgrimage:cinderglass",
  "aionbound:storm_slate": "pilgrimage:storm",
  "aionbound:abyss_silt": "pilgrimage:abyss",
  "aionbound:boneplain_soil": "pilgrimage:boneplain",
  "aionbound:rift_crust": "pilgrimage:riftscar",
  "aionbound:twinbond_obelisk_site": "pilgrimage:twinbond",
});

// Discovery and action are deliberately separate. A block may do both; this
// closes the G6 early-return collision without making handler order authority.
export const BLOCK_ROUTES = Object.freeze({
  "aionbound:gloam_moss_block": { discoveries: ["pilgrimage:gloam"], actions: ["guidance"] },
  "aionbound:brinewood_planks": { discoveries: ["pilgrimage:brine"], actions: ["guidance"] },
  "aionbound:ember_vent_stone": { discoveries: ["pilgrimage:vent"], actions: ["boss:basalt"] },
  "aionbound:scorch_glass_shard_block": { discoveries: ["pilgrimage:cinderglass"], actions: ["guidance"] },
  "aionbound:storm_slate": { discoveries: ["pilgrimage:storm"], actions: ["guidance"] },
  "aionbound:abyss_silt": { discoveries: ["pilgrimage:abyss"], actions: ["guidance"] },
  "aionbound:boneplain_soil": { discoveries: ["pilgrimage:boneplain"], actions: ["guidance"] },
  "aionbound:rift_crust": { discoveries: ["pilgrimage:riftscar"], actions: ["boss:rift"] },
  "aionbound:twinbond_obelisk_site": { discoveries: ["pilgrimage:twinbond"], actions: ["boss:twinbond"] },
  "aionbound:orevein_hollow_gate": { discoveries: ["destination:burrowgate"], actions: ["pocket"] },
  "aionbound:roving_foundry_wreck": { discoveries: ["landmark:foundry"], actions: ["boss:foundry"] },
  "aionbound:creature_nest": { discoveries: ["landmark:creature_nest"], actions: ["boss:royal_moth"] },
  "aionbound:chaos_crate_t0": { discoveries: ["system:bounded_chaos"], actions: ["chaos"] },
  "aionbound:prismglass_chest": { discoveries: ["block:prismglass_chest"], actions: ["safe_storage_notice"] },
  "aionbound:salvage_bench": { discoveries: ["technology:salvage"], actions: ["site_reward", "device:salvage"] },
  "aionbound:resonance_press": { discoveries: ["technology:press"], actions: ["site_reward", "device:press"] },
  "aionbound:survey_relay": { discoveries: ["technology:survey"], actions: ["site_reward", "device:survey"] },
  "aionbound:codex_lectern": { discoveries: ["codex:lectern"], actions: ["site_reward", "codex"] },
  "aionbound:lumen_brazier": { discoveries: [], actions: ["site_reward"] },
  "aionbound:woven_nest": { discoveries: [], actions: ["site_reward"] },
  "aionbound:trophy_plinth": { discoveries: [], actions: ["site_reward"] },
  "aionbound:lumen_salt_cluster": { discoveries: [], actions: ["site_reward"] },
  "aionbound:ferrowake_ore": { discoveries: [], actions: ["site_reward"] },
  "aionbound:resonant_lamp": { discoveries: [], actions: ["site_reward"] },
  "aionbound:rootglass_nodule": { discoveries: [], actions: ["site_reward"] },
  "aionbound:brinewood_beam": { discoveries: [], actions: ["site_reward"] },
  "aionbound:rootglass_lantern": { discoveries: [], actions: ["site_reward"] },
  "aionbound:ferrowake_lamp": { discoveries: [], actions: ["site_reward"] },
});

export const STRUCTURE_SITES = Object.freeze([
  { id: "mote_shrine", center: "aionbound:lumen_brazier", signature: "aionbound:carved_lumen_stone", pool: "shrine" },
  { id: "collapsed_survey_camp", center: "aionbound:survey_relay", signature: "aionbound:brinewood_beam", pool: "survey_cache" },
  { id: "ridge_nest", center: "aionbound:woven_nest", signature: "aionbound:storm_slate_tiles", pool: "nest" },
  { id: "scrap_cache", center: "aionbound:salvage_bench", signature: "aionbound:riveted_ferrowake", pool: "foundry" },
  { id: "overgrown_waystation", center: "aionbound:codex_lectern", signature: "aionbound:rootglass_mosaic", pool: "wild_cache" },
  { id: "broken_relay", center: "aionbound:survey_relay", signature: "aionbound:charged_aionite_block", pool: "survey_cache" },
  { id: "pilgrim_cairn", center: "aionbound:trophy_plinth", signature: "aionbound:lumen_stone", pool: "pilgrimage" },
  { id: "lumen_seep", center: "aionbound:lumen_salt_cluster", signature: "aionbound:lumen_inlay", pool: "shrine" },
  { id: "ferrowake_prospect", center: "aionbound:ferrowake_ore", signature: "aionbound:ferrowake_beam", pool: "survey_cache" },
  { id: "warded_cellar", center: "aionbound:resonant_lamp", signature: "aionbound:relic_sandstone", pool: "elite" },
  { id: "burrow_breach", center: "aionbound:rootglass_nodule", signature: "aionbound:mite_resin_block", pool: "burrow" },
  { id: "hunters_blind", center: "aionbound:brinewood_beam", signature: "aionbound:woven_nest", pool: "wild_cache" },
  { id: "glassroot_grotto", center: "aionbound:rootglass_lantern", signature: "aionbound:rootglass_mosaic", pool: "burrow" },
  { id: "silent_foundry", center: "aionbound:resonance_press", signature: "aionbound:ferrowake_bricks", pool: "foundry" },
  { id: "lantern_causeway", center: "aionbound:ferrowake_lamp", signature: "aionbound:storm_slate_tiles", pool: "pilgrimage" },
]);

export const STRUCTURE_REWARDS = Object.freeze({
  wild_cache: Object.freeze(["aionbound:waystone_ration", 1]),
  survey_cache: Object.freeze(["aionbound:stabilizing_chalk", 2]),
  nest: Object.freeze(["aionbound:mite_resin", 2]),
  foundry: Object.freeze(["aionbound:tempered_ferrowake", 1]),
  shrine: Object.freeze(["aionbound:prismatic_binder", 1]),
  burrow: Object.freeze(["aionbound:woven_sinew", 1]),
  elite: Object.freeze(["aionbound:ward_knot", 1]),
  pilgrimage: Object.freeze(["aionbound:trophy_codex", 1]),
});

export const ITEM_ROUTES = Object.freeze({
  "aionbound:barkling_token": "familiar",
  "aionbound:stripvein_charge": "stripvein",
  "aionbound:vector_ray_projector": "ray",
  "aionbound:waykeeper_whistle": "mount",
  "aionbound:starter_codex_bookmark": "codex",
  "aionbound:trophy_codex": "codex",
  "aionbound:trophy_edge": "edge_stamp",
});

export const COMPLETED_ITEM_ROUTES = Object.freeze({
  "aionbound:gale_repeater": "ranged",
  "aionbound:aether_gauntlet": "ranged",
  "aionbound:behemoth_tusk_bow": "ranged",
  "aionbound:lumen_draught": "consumable",
  "aionbound:miners_resin": "consumable",
  "aionbound:stabilizing_chalk": "consumable",
  "aionbound:waystone_ration": "consumable",
  "aionbound:mote_lantern": "accessory_pulse",
  "aionbound:wayfinder_spool": "accessory_pulse",
});

export const MELEE_WEAPON_ROLES = Object.freeze({
  "aionbound:cinder_saber": Object.freeze({ role: "ignite", cooldown: 20 }),
  "aionbound:basalt_maul": Object.freeze({ role: "bounded_shockwave", cooldown: 30, targets: 4 }),
  "aionbound:brine_spear": Object.freeze({ role: "reposition", cooldown: 16 }),
  "aionbound:brood_fang_daggers": Object.freeze({ role: "venom", cooldown: 12 }),
  "aionbound:roc_pinion_glaive": Object.freeze({ role: "lift", cooldown: 24 }),
});

export const RANGED_WEAPON_ROLES = Object.freeze({
  "aionbound:gale_repeater": Object.freeze({ role: "rapid_ray", range: 18, damage: 3, cooldown: 9, particles: 4 }),
  "aionbound:aether_gauntlet": Object.freeze({ role: "force_burst", range: 12, damage: 5, cooldown: 25, particles: 6 }),
  "aionbound:behemoth_tusk_bow": Object.freeze({ role: "heavy_ray", range: 24, damage: 9, cooldown: 30, particles: 8 }),
});

export const ACCESSORY_ROLES = Object.freeze({
  "aionbound:quarry_lens": "resource_hint",
  "aionbound:pilgrim_clasp": "fall_mitigation",
  "aionbound:mote_lantern": "landmark_pulse",
  "aionbound:salvage_magnet": "bounded_item_pull",
  "aionbound:ward_knot": "ward_cooldown",
  "aionbound:wayfinder_spool": "anchor_guidance",
});

export const CONSUMABLE_EFFECTS = Object.freeze({
  "aionbound:lumen_draught": Object.freeze([["night_vision", 1200, 0], ["speed", 200, 0]]),
  "aionbound:miners_resin": Object.freeze([["haste", 600, 0]]),
  "aionbound:stabilizing_chalk": Object.freeze([["resistance", 400, 0], ["slow_falling", 200, 0]]),
  "aionbound:waystone_ration": Object.freeze([["regeneration", 120, 0], ["saturation", 20, 0]]),
});

export const ARMOR_SETS = Object.freeze({
  ferrowake: Object.freeze(["aionbound:ferrowake_helmet", "aionbound:ferrowake_chestplate", "aionbound:ferrowake_leggings", "aionbound:ferrowake_boots"]),
  concord: Object.freeze(["aionbound:concord_helmet", "aionbound:concord_chestplate", "aionbound:concord_leggings", "aionbound:concord_boots"]),
});

export const BOSS_LADDER = Object.freeze({
  "boss:royal_moth": Object.freeze({ prerequisite: "glasswing:first_defeat", terminal: "trophy:royal_moth", type: "aionbound:royal_moth_empress" }),
  "boss:basalt": Object.freeze({ prerequisite: "trophy:royal_moth", terminal: "trophy:basalt", type: "aionbound:basalt_behemoth" }),
  "boss:rift": Object.freeze({ prerequisite: "trophy:basalt", terminal: "trophy:rift", type: "aionbound:rift_colossus" }),
});

export const BOSS_REWARDS = Object.freeze({
  "aionbound:chrono_robo_sentinel": ["chrono:first_defeat", "aionbound:chrono_core"],
  "aionbound:royal_moth_empress": ["trophy:royal_moth", "minecraft:amethyst_shard"],
  "aionbound:basalt_behemoth": ["trophy:basalt", "aionbound:trophy_basalt_tusk"],
  "aionbound:rift_colossus": ["trophy:rift", "aionbound:trophy_colossus_shard"],
});

export const CODEX_TOPICS = Object.freeze([
  Object.freeze({ id: "path", title: "Core Path", lines: ["Glasswing -> foundry robot", "Ray / Burrowgate / pilgrimage", "Royal Moth -> Basalt -> Rift", "Trophy Edge -> Twinbond -> Concord"] }),
  Object.freeze({ id: "arsenal", title: "Arsenal", lines: ["Trophy Edge: balanced trophy blade", "Vector Ray: precise energy strike", "Find materials for lateral weapon roles."] }),
  Object.freeze({ id: "naturalist", title: "Naturalist", lines: ["Observe ambient and neutral creatures.", "Creature drops feed equipment and utility.", "Rare creatures reveal unusual regions."] }),
  Object.freeze({ id: "surveyor", title: "Surveyor", lines: ["Waystones, nests, ruins, and foundries", "Burrowgate and pilgrimage destinations", "Survey Relays turn discovery into direction."] }),
  Object.freeze({ id: "materials", title: "Materials", lines: ["Ore + creature drop -> component", "Component -> equipment or device", "Boss material -> sidegrade or upgrade"] }),
]);

export const TECH_LOOPS = Object.freeze({
  salvage: Object.freeze({
    "aionbound:trophy_edge_preview": Object.freeze({ item: "aionbound:ferrowake_coupling", count: 2 }),
    "aionbound:vector_ray_projector": Object.freeze({ item: "aionbound:ferrowake_coupling", count: 3 }),
  }),
  press: Object.freeze({
    "aionbound:raw_ferrowake": Object.freeze({ item: "aionbound:tempered_ferrowake", count: 1 }),
    "aionbound:aionite_crystal": Object.freeze({ item: "aionbound:charged_prism", count: 1 }),
    "aionbound:rootglass_shard": Object.freeze({ item: "aionbound:prismatic_binder", count: 1 }),
  }),
});

export const NATURAL_ENTITY_IDS = Object.freeze([
  "aionbound:breezetail", "aionbound:galestrider", "aionbound:lanternback", "aionbound:pebblehorn",
  "aionbound:basalt_magma_spitter", "aionbound:cinder_brood_hatchling", "aionbound:tide_spawn_skitter", "aionbound:veil_mask_acolyte",
]);

// Six bounded classes, three deterministic variants each. Outcomes use only
// stable item/effect/entity/block primitives and never exceed their class cap.
export const CHAOS_OUTCOMES = Object.freeze([
  { id: "boon_speed", class: "boon", effect: ["speed", 200, 0] },
  { id: "boon_guard", class: "boon", effect: ["resistance", 160, 0] },
  { id: "boon_mend", class: "boon", effect: ["regeneration", 100, 0] },
  { id: "skirmish_slime", class: "bounded_skirmish", entities: ["minecraft:slime", "minecraft:slime"] },
  { id: "skirmish_husk", class: "bounded_skirmish", entities: ["minecraft:husk", "minecraft:husk"] },
  { id: "skirmish_mites", class: "bounded_skirmish", entities: ["minecraft:silverfish", "minecraft:silverfish", "minecraft:silverfish"] },
  { id: "burst_food", class: "material_burst", item: ["minecraft:baked_potato", 4] },
  { id: "burst_iron", class: "material_burst", item: ["minecraft:iron_nugget", 8] },
  { id: "burst_prism", class: "material_burst", item: ["minecraft:amethyst_shard", 3] },
  { id: "transform_light", class: "harmless_transformation", temporary: ["minecraft:glowstone", 200] },
  { id: "transform_moss", class: "harmless_transformation", temporary: ["minecraft:moss_block", 240] },
  { id: "transform_ice", class: "harmless_transformation", temporary: ["minecraft:ice", 160] },
  { id: "hazard_web", class: "temporary_hazard", temporary: ["minecraft:cobweb", 120] },
  { id: "hazard_fire", class: "temporary_hazard", temporary: ["minecraft:fire", 60] },
  { id: "hazard_powder", class: "temporary_hazard", temporary: ["minecraft:powder_snow", 100] },
  { id: "clue_wild", class: "discovery_clue", discovery: "rumor:wild_cache" },
  { id: "clue_foundry", class: "discovery_clue", discovery: "rumor:silent_foundry" },
  { id: "clue_pilgrimage", class: "discovery_clue", discovery: "rumor:pilgrimage_threshold" },
]);

export function routeForBlock(typeId) { return BLOCK_ROUTES[typeId] ?? null; }
export function routeForItem(typeId) { return ITEM_ROUTES[typeId] ?? null; }
export function routeForCompletedItem(typeId) { return COMPLETED_ITEM_ROUTES[typeId] ?? null; }
