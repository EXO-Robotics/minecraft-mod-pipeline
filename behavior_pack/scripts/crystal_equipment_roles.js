// Ratified Crystal Marsh base roles. Values are conservative refinements of
// the existing stable ranged/safe-poke patterns; W1-CREATIVE-005 sidegrades
// remain outside this table.
export const CRYSTAL_MELEE_ROLES = Object.freeze({
  "aionbound:crystal_pike": Object.freeze({ role: "safe_poke", cooldown: 16 }),
});

export const CRYSTAL_RANGED_ROLES = Object.freeze({
  "aionbound:prism_bow": Object.freeze({
    role: "prism_ray",
    range: 20,
    damage: 5,
    cooldown: 20,
    particles: 5,
    ammo: "minecraft:arrow",
    durabilityCost: 1,
  }),
});

export const CRYSTAL_ACCESSORY_ROLES = Object.freeze({
  "aionbound:crystal_talisman": "wet_vision",
  // Intentionally narrative-only: the approved contract calls the wight
  // resistance a narrative identity and does not authorize combat values.
  "aionbound:marsh_idol": "structure_calm_narrative",
});

export const CRYSTAL_ROLE_WITHHOLDS = Object.freeze({
  "aionbound:prism_bow": "Gale-strung sidegrade remains W1-CREATIVE-005 deferred.",
  "aionbound:crystal_talisman": "Pearl-luck has no stable exact representation and remains withheld.",
  "aionbound:marsh_idol": "Wight resistance is narrative-only; no combat mutation is authorized.",
  "aionbound:explorer_cloak": "Inventory capacity and travel-value mutation are not authorized by an exact stable contract.",
});
