// Packet 006 Whisperwood equipment-A roles. Keep this table separate from the
// retained G7 catalog so vertical integrations can reconcile without replacing
// proven substrate entries.
export const WHISPERWOOD_MELEE_ROLES = Object.freeze({
  "aionbound:mossfang_spear": Object.freeze({ role: "safe_poke", cooldown: 14 }),
  "aionbound:widow_fang_dagger": Object.freeze({ role: "venom", cooldown: 10 }),
  "aionbound:thorn_whip": Object.freeze({ role: "pull", cooldown: 16 }),
});

export const WHISPERWOOD_UTILITY_ROLES = Object.freeze({
  "aionbound:moon_sap_staff": Object.freeze({ role: "light_support", cooldown: 200 }),
  "aionbound:lantern_hook": Object.freeze({ role: "portable_light", cooldown: 200 }),
});
