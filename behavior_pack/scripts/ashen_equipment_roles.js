// Packet 006 Ashen functional identities. Creative owns the role names. Every
// number here is a conservative engineering refinement bounded against the
// retained G7 and Whisperwood implementation patterns.
export const ASHEN_MELEE_ROLES = Object.freeze({
  "aionbound:basalt_hammer": Object.freeze({ role: "basalt_stun", cooldown: 30, stunTicks: 20, armoredWeaknessTicks: 40 }),
  "aionbound:ember_great_axe": Object.freeze({ role: "wide_heat_pressure", cooldown: 24, radius: 3, targets: 3, pressureDamage: 1, fireSeconds: 2 }),
});

export const ASHEN_RANGED_ROLES = Object.freeze({
  "aionbound:ash_repeater": Object.freeze({ role: "ash_heat_bolt", range: 18, damage: 4, cooldown: 12, particles: 4, fireSeconds: 2, ammo: "aionbound:volcanic_glass_shard", durabilityCost: 1 }),
});

export const ASHEN_ACCESSORY_ROLES = Object.freeze({
  "aionbound:ember_totem": "heat_ward",
});

export const ASHEN_ARMOR_SET = Object.freeze([
  "aionbound:ashen_helmet", "aionbound:ashen_chest", "aionbound:ashen_legs", "aionbound:ashen_boots",
]);

// Existing material/construct identities used only to strengthen the approved
// armored-foe role. This does not create a new entity family or tag.
export const ASHEN_ARMORED_TARGETS = Object.freeze(new Set([
  "aionbound:basalt_tortoise", "aionbound:furnace_beetle", "aionbound:ash_drake",
  "aionbound:basalt_behemoth", "aionbound:ferrowake_bulwark", "aionbound:chrono_robo_sentinel", "aionbound:colossus_shard_golem",
]));
