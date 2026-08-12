const event = (id, state, kind) => Object.freeze({ id, state, event: kind });
const entry = (id, runtimeId, category, events, authorityText = undefined) => Object.freeze({
  id, warehouseId: id, runtimeId, region: "sr", kind: category, category,
  events: Object.freeze(events), ...(authorityText ? { authorityText: Object.freeze(authorityText) } : {}),
});

export const SKYREACH_CODEX_RUNTIME_ENTRIES = Object.freeze([
  entry("wing_bone_stay", "aionbound:wing_bone_stay", "equipment", [event("codex:sr:equipment:wing_bone_stay:first_owned", 2, "first_owned")]),
  entry("glider_panel", "aionbound:glider_panel", "equipment", [event("codex:sr:equipment:glider_panel:first_owned", 2, "first_owned")]),
  entry("glider_frame", "aionbound:glider_frame", "equipment", [event("codex:sr:equipment:glider_frame:first_owned", 2, "first_owned")]),
  entry("climbing_rope", "aionbound:climbing_rope", "equipment", [event("codex:sr:equipment:climbing_rope:first_owned", 2, "first_owned")]),
  entry("climbing_hook_head", "aionbound:climbing_hook_head", "equipment", [event("codex:sr:equipment:climbing_hook_head:first_owned", 2, "first_owned")]),
  entry("soft_landing_pad", "aionbound:soft_landing_pad", "equipment", [event("codex:sr:equipment:soft_landing_pad:first_owned", 2, "first_owned")]),
  entry("lift_tonic", "aionbound:lift_tonic", "equipment", [event("codex:sr:equipment:lift_tonic:first_owned", 2, "first_owned")]),
  entry("aether_bind", "aionbound:aether_bind", "equipment", [event("codex:sr:equipment:aether_bind:first_owned", 2, "first_owned")]),
  entry("surveyor_staff", "aionbound:surveyor_staff", "equipment", [event("codex:sr:equipment:surveyor_staff:first_owned", 2, "first_owned")]),
  entry("trail_compass", "aionbound:trail_compass", "equipment", [event("codex:sr:equipment:trail_compass:first_owned", 2, "first_owned")]),
  entry("surveyor_medallion", "aionbound:surveyor_medallion", "equipment", [event("codex:sr:equipment:surveyor_medallion:first_owned", 2, "first_owned")]),
  entry("warden_sigil", "aionbound:warden_sigil", "equipment", [event("codex:sr:equipment:warden_sigil:first_owned", 2, "first_owned")]),
  entry("storm_pinion", "aionbound:storm_pinion", "equipment", [event("codex:sr:equipment:storm_pinion:first_owned", 2, "first_owned")]),
  entry("storm_nest", "aionbound:wind_roc", "boss", [
    event("codex:sr:boss:storm_nest:encountered", 1, "valid_storm_nest_pull"),
    event("codex:sr:boss:storm_nest:defeated", 2, "valid_storm_nest_terminal"),
  ], { encounter: "Storm Nest", phases: "Nest Guard, Wind Roads, Harpy Dirge, Storm Crown", critical_reward: "Durable Storm Pinion seal credit" }),
  entry("skyreach_chapter", "aionbound:skyreach_chapter", "progression", [event("codex:sr:progression:skyreach_chapter:entered", 1, "first_regional_discovery")]),
  entry("pilgrimage_handoff", "aionbound:storm_pinion", "progression", [event("codex:sr:progression:skyreach_chapter:seal_credit", 2, "valid_storm_nest_terminal")]),
]);
