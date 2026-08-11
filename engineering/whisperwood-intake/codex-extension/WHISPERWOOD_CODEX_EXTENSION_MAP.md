# Whisperwood Codex extension implementation map

Base: `00840aaae36a0cfb83955ca7b416c1d2886a6261`. Status: **DETERMINISTIC_IMPLEMENTATION_MAP_ONLY**.

This is a deterministic map and bounded test surface only. It does not edit or prove the shipping runtime.

## Coverage

| Category | Added | Result |
|---|---:|---|
| Structures | 10 | One page for every Packet 001 prop ID |
| Equipment | 21 | 5 weapons, 4 armor, 3 tools, 5 accessories, 4 trophies |
| Bosses | 1 | Thorn Court with victory-only phase field notes |
| Progression | 2 | Whisperwood chapter and Ashen rumor |
| **Total** | **34** | 74 Whisperwood pages after the existing 40 |

## Structure pages

Each structure completes on either its first recognized activation or 200 consecutive ticks of recognized-site proximity. Neither event claims loot.

| ID | Importance | Story text (exact Creative text) |
|---|---|---|
| `lantern_post` | `craft_core` | Old path network of the Owl faithful |
| `moss_cairn` | `exploration` | Travelers stack moss for those lost to bark wraiths |
| `hunter_camp` | `exploration` | Rangers tracked rot wolves; left in a hurry when thorn stalkers came |
| `broken_wagon` | `critical_path` | Merchants fled heat rumors east; one wheel burned already |
| `root_bridge` | `exploration` | Roots grew where a wooden bridge failed |
| `owl_shrine` | `craft_core` | Pre-human forest worship; eyes still watch |
| `forest_waystone` | `critical_path` | Stones older than hunters; moss grows in circuit patterns |
| `hollow_cave_entrance` | `craft_core` | Widow dens under giant roots |
| `ancient_totem` | `critical_path` | Bound something under roots; cracks show amber light |
| `fallen_giant_tree` | `exploration` | Something large pushed it — not weather |

## Equipment and trophy pages

| Subtype | IDs | Unlock |
|---|---|---|
| weapon | `mossfang_spear`, `widow_fang_dagger`, `thorn_whip`, `briar_cleaver`, `moon_sap_staff` | Successful craft output |
| armor | `whisperwood_helmet`, `whisperwood_chest`, `whisperwood_legs`, `whisperwood_boots` | Successful craft output |
| tool | `root_knife`, `whisperwood_hatchet`, `lantern_hook` | Successful craft output |
| accessory | `moss_charm`, `root_bracelet`, `lantern_badge`, `moon_sap_pendant`, `briar_ring` | Successful craft output |
| trophy | `thorn_stalker_skull`, `briar_elk_trophy`, `mosskip_trophy`, `ancient_acorn_display` | Valid Thorn Court terminal credit for `thorn_stalker_skull`; successful craft for the other entries |

`briar_elk_trophy`, `mosskip_trophy`, and `ancient_acorn_display` remain optional. The first two are explicitly mastery-only and never fill the chapter-seal slot.

## Thorn Court and progression

The Thorn Court page becomes partial only on a valid arena pull and complete only on a valid arena-form terminal event. Ecology-form Thorn Stalkers cannot complete it. Victory reveals the exact phase names `Briar Rise`, `Widow Wire`, `Crown of Thorns`, and `Forest Scream`.

The trophy page follows durable seal credit, not physical-item presence. This preserves once-per-player credit and recoverable best-effort physical delivery. Repeat clears cannot repeat the page, seal credit, or trophy entitlement.

The Ashen rumor is a Codex/recognized-structure-state page with the exact safe hint: “Heat waits east of the burned wagons.” It is not a map-scrap item, inventory grant, or Ashen unlock token.

## Compact v4 extension

Keep state schema v4 and bump only the registry version from 1 to 2. Append `structure:10`, `equipment:21`, `boss:1`, and `progression:2`; never reorder the existing categories or their 40 entries. This adds 11 encoded bytes per populated region. A fully populated four-region discovery object is 596 JSON bytes against the existing 8192-byte player budget.

## Runtime conflicts

- `behavior_pack/scripts/wave1_codex_data.js` — registry contains only 40 entries and registry version 1. Needed: append this map's 34 entries and bump registry version to 2 without reordering the original 40.
- `behavior_pack/scripts/state.js` — category caps omit structure/equipment/boss/progression. Needed: add exact caps from compact_v4_extension; retain STATE_VERSION 4 and idempotent normalization.
- `behavior_pack/scripts/codex.js` — UI exposes only resource/plant/creature and has no boss field-note gating. Needed: add four categories and state-gated exact authority fields without making chat the primary UX.
- `behavior_pack/scripts/wave1_codex_ui_data.js` — question rows cover only the original 40 entries. Needed: bind exact authority_text fields from this map; do not synthesize missing lore.
- `behavior_pack/scripts/catalog.js` — Codex routes only block/plant/creature events; structure registry recognizes only two Whisperwood progression sites. Needed: add compositional routes for all 10 recognized structures, 21 equipment outputs, Thorn Court terminal events, and two progression pages.
- `behavior_pack/scripts/structures.js` — only forest_waystone and broken_wagon have progression activation hooks; no 10-second proximity service exists. Needed: reuse canonical site recognizers and a bounded per-player 200-tick accumulator; activation/proximity must not claim loot implicitly.
- `behavior_pack/scripts/runtime.js` — no exact successful-craft output event is currently routed. Needed: select and Stable-API-audit an exact craft-completion signal before implementation; first possession is not silently equivalent to craft.
- `Thorn Court runtime integration lane` — boss, trophy, seal-credit, and progression transitions share one terminal event. Needed: one compositional terminal transaction in the exact cross_page_semantics order; no early-return suppression.

## Proof boundary

This map proves deterministic coverage, exact authority phrase binding, trigger semantics, and state-budget arithmetic. It does not prove runtime hooks, BDS, client UI, loot, trophy delivery, boss behavior, console behavior, or Checkpoint 1 readiness.
