# Whisperwood Equipment Intake

Status: **DETERMINISTIC INTAKE COMPLETE — BASE PREPARATION AUTHORIZED; FINAL DEPENDENCIES PARTLY BLOCKED**

This is the Packet 006 intake map for Wave A only. It does not implement equipment, invent recipes, choose stats, create loot, alter art, or modify shared authority.

## Exact subset

| Class | Exact Packet 006 IDs |
|---|---|
| Weapons (5) | `mossfang_spear`, `widow_fang_dagger`, `thorn_whip`, `briar_cleaver`, `moon_sap_staff` |
| Armor (4) | `whisperwood_helmet`, `whisperwood_chest`, `whisperwood_legs`, `whisperwood_boots` |
| Tools (3) | `root_knife`, `whisperwood_hatchet`, `lantern_hook` |
| Accessories (5) | `moss_charm`, `root_bracelet`, `lantern_badge`, `moon_sap_pendant`, `briar_ring` |
| Trophies (4) | `thorn_stalker_skull`, `briar_elk_trophy`, `mosskip_trophy`, `ancient_acorn_display` |

The 21 IDs are the exact union of the Packet 006 Whisperwood row, the contract's Packet 001 equipment links, and the Wave A requirement for the WW-facing subset of 006. `root_knife` is included because the Creative contract binds its spawn-to-WW upgrade path into Wave A. Cross-biome-only and finale-only equipment is excluded.

## Exact canonical source files

Packet root:

`program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-006-equipment-progression`

For every exact ID above, the canonical source set is:

```text
assets/editable/<id>.bbmodel
assets/editable/<id>.png
assets/briefs/<id>.json
assets/export/models/<id>.geo.json
assets/export/animations/<id>.animation.json
```

The exact byte hashes are bound transitively through `engineering/normalization/PACKET_NORMALIZATION_INVENTORY.json` at SHA-256 `4a65ccbc10f47a86e3aec649874916a9d4ad5cb9feef7817d75a527774a3a842`. Category-folder files are mirrors, not source authority.

## Native repair bar

All 21 canonical `.bbmodel` files require native Blockbench work before shipping use:

- All 21 declare an `effect` locator, but the locator is absent from the editable model. The static preview geometry contains one; a real native locator must be created and proven by native export.
- Ten assets lack their declared role clips: all five weapons, all three tools, `moss_charm`, and `moon_sap_pendant`.
- All 21 use the warehouse geometry namespace `geometry.aionforge_eq.*` and absolute local texture paths; normalize to `geometry.aionbound.*` and portable texture bindings.
- Sixteen assets declare 64×64 while the approved packet PNG and model atlas are 32×32. The five accessories declare a 32–64 range and have 32×32 PNGs. Intake does not upscale or redraw; Engineering must explicitly normalize the mismatch while preserving packet pixels.
- Native open/save/reopen, native codec exports, exact locator inspection, export equivalence, and exact shipping PNG decode remain required. Client, BDS, and physical PS4 proof remain unrun.

## Acquisition and ticket boundary

Safe identities already exist for the approved warehouse resources and these derived components: `moss_bind_glue`, `amber_core`, `thorn_cord`, `cleaver_blank`, and `living_root_focus`.

The exact per-asset dependency map is in the JSON twin. The practical blockers are:

- `W1-CREATIVE-001`: unresolved canonical inputs such as Thorn Barb, Stalker Claw/Boar Tusk, hide/plate terms, scrap inputs, brass scrap, silk thread, crown fragments, and pedestal wood.
- `W1-CREATIVE-003`: Thorn Stalker completion, ownership, persistence, reset, and terminal reward rules.
- `W1-CREATIVE-004`: loot quantities/ranges, reward guards, and alternate/soft-seal semantics.
- `W1-CREATIVE-005`: Skywidow/grapnel/heat-tempered and root-knife upgrade identity semantics.

Native repair, namespace/path normalization, presentation shells, approved base-item behavior interfaces, and non-rewarding placeable trophy presentation are safe now. Final recipes, loot, boss rewards, sidegrade identities, and unresolved inventory terms are not.

All 21 exact base IDs should therefore proceed first within that safe boundary. `W1-CREATIVE-005` is isolated to four deferred identity decisions: `thorn_whip` → Skywidow Whip, `lantern_hook` → Cliff grapnel, `briar_ring` → heat-tempered ring, and the same-ID amber-tip `root_knife` upgrade. It does not withhold their base models, presentation, or behavior interfaces.

## Proposed BP/RP targets

| Profile | Proposed target set |
|---|---|
| Held weapon/tool | `behavior_pack/items/<id>.item.json`; `resource_pack/attachables/<id>.attachable.json`; `resource_pack/models/aionbound/equipment/<id>.geo.json`; `resource_pack/textures/aionbound/wave1/equipment/items/<id>.png`; optional approved animation/controller files; item atlas + language |
| Wearable armor | BP item; RP attachable; `models/aionbound/equipment/<id>.geo.json`; `textures/aionbound/wave1/equipment/armor/<id>.png`; item atlas + language |
| Accessory | BP item; RP attachable/presentation model; `textures/aionbound/wave1/equipment/accessories/<id>.png`; approved animation only where declared; item atlas + language |
| Placeable trophy | `behavior_pack/blocks/<id>.block.json`; block loot table; `resource_pack/models/blocks/<id>.geo.json`; `textures/aionbound/wave1/equipment/trophies/<id>.png`; block/terrain atlases + language |

These are cooperative product-root proposals only. They do not assert a finished Bedrock binding or authorize gameplay values.

## G7 collision result

- Exact runtime-ID collisions: **0 of 21**.
- Exact proposed target-path collisions at base `a9d64b2`: **0**.
- Semantic reconciliation remains for `mossfang_spear` versus G7 `brine_spear`, `widow_fang_dagger` versus G7 `brood_fang_daggers`, the WW armor set versus G7 Ferrowake/Concord armor, and the four WW trophies versus the retained/refined `trophy_edge` chain.
- Those are role/progression overlaps, not namespace collisions. This intake makes no KEEP/REFINE/REPLACE decision beyond the existing reconciliation ledger.

## Proof boundary

The validator proves authority hashes, exact subset membership, canonical source existence and hashes, normalization findings, absence of exact G7 IDs, and absence of proposed target-path collisions at the pinned base. It does not prove native Blockbench repair, in-game rendering, gameplay balance, Stable BDS, client behavior, or PS4 behavior.
