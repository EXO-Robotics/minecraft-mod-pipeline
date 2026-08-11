# Twinbond Existing Authority Audit

Status: `EVIDENCE_COMPLETE_PARTIAL_TICKET_RESOLUTION_RECOMMENDED`

This is a read-only authority audit based on integration commit `45828b9540a6ec7af211072e36432dddf900b903` (tree `f90bb3a909d89102ae9d0426591cbdce06f75269`). It does not amend the Wave 1 decision ledger, select unapproved content, modify packs, run BDS, or declare a candidate.

## Outcome

`W1-CREATIVE-002` should be narrowed, not closed wholesale.

Existing authority is sufficient to bind the exact Twinbond aspect entities and art inputs, the prepared arena/approach asset set, and the primary Wave 1 reward identity. It is not sufficient to choose the finale container/placement, dispose of every secondary reward term, or decide whether Twinbond completion is mandatory for the Wave 1 machine-exit token.

| Ticket question | Evidence-backed result |
|---|---|
| Exact aspect entities | Resolve to `aionbound:ash_sovereign_wyrm` + `aionbound:tide_empress_wyrm` |
| Existing boss art inputs | Exact wave2 `.bbmodel`, geometry, animation, texture, and locator-bearing exports exist |
| Arena art | Exact dual-throne, obelisk, anvil, ring, approach, and 128×48×128 massing inputs exist |
| Primary reward | Current Wave 1 authority binds `twinbond_relic` → Trophy Edge ignition |
| Old concord-scale reward | Superseded for Wave 1; do not preserve it as the finale reward by inertia |
| Finale container | Still unresolved: old prep says isolated logical `twinbond`; current Wave 1 does not ratify that placement |
| Machine exit dependency | Still unresolved |

## Authority precedence

1. The current Wave 1 implementation contract and linked Creative documents bind the current progression and reward identity.
2. Binding catalog documents bind product ownership and name the dual wyrms as Core's Twinbond representative.
3. The Twinbond prep contract, bounded kit, and massing bind prepared art/geometry, while explicitly leaving gameplay and pipeline qualification open.
4. Frozen G7 is reusable engineering substrate evidence, not current Creative authority and not proof of a working Twinbond encounter.
5. Files explicitly marked `draft` or `data_only_not_wired` are historical inputs only when current authority does not conflict.

This ordering resolves the apparent conflict. Creative says Twinbond is “not a warehouse biome boss mesh”; the Ash and Tide wyrms are non-warehouse wave2 assets. Catalog assigns the named pair to Core Twinbond, while the prep contract calls them approved authority and says not to replace them. No new identity is needed.

## Exact entity and art inputs

### Ash Sovereign Wyrm

- Canonical entity ID: `aionbound:ash_sovereign_wyrm`
- Brief: `program/crazycraft-pack-production-v1/studio-epic-wave2/assets/briefs/ash_sovereign_wyrm.json`, SHA-256 `963411b28025ebc22bc51eef6b2835b59768b032d261eb87eb90349f23f4cf68`
- Editable: `program/crazycraft-pack-production-v1/studio-epic-wave2/assets/editable/ash_sovereign_wyrm.bbmodel`, SHA-256 `91c636c697afb624105ed95969ae11f866f3aaafcdcea23c33518487c852591d`
- Geometry: `program/crazycraft-pack-production-v1/studio-epic-wave2/assets/export/models/ash_sovereign_wyrm.geo.json`, SHA-256 `a10684809384452ccac2d70a43e481266fdd512bf68d2a763c46d15c1f275db3`
- Animation: `program/crazycraft-pack-production-v1/studio-epic-wave2/assets/export/animations/ash_sovereign_wyrm.animation.json`, SHA-256 `100b06d916e0874c97da13034abb2a855f48c4c6dd9b6c8f35fa5c4bd29afef5`
- Texture: `program/crazycraft-pack-production-v1/studio-epic-wave2/assets/export/textures/ash_sovereign_wyrm.png`, SHA-256 `5145059c4bb5526e183618e4b6341c3a428d6c6debded039a227ebebad39f4aa`

### Tide Empress Wyrm

- Canonical entity ID: `aionbound:tide_empress_wyrm`
- Brief: `program/crazycraft-pack-production-v1/studio-epic-wave2/assets/briefs/tide_empress_wyrm.json`, SHA-256 `932df0c85b512c11dd79f5b5b902314a99670357eb5c37acfb96134b1ece93b1`
- Editable: `program/crazycraft-pack-production-v1/studio-epic-wave2/assets/editable/tide_empress_wyrm.bbmodel`, SHA-256 `b0247e92e67a8e57d4f459828ac70c90144cc6f7a10ffe384627bc82926199e2`
- Geometry: `program/crazycraft-pack-production-v1/studio-epic-wave2/assets/export/models/tide_empress_wyrm.geo.json`, SHA-256 `886b5b3ec30c2c2bf27340c73adabde11e76d6b905d61795d6f48dbc2dec8afc`
- Animation: `program/crazycraft-pack-production-v1/studio-epic-wave2/assets/export/animations/tide_empress_wyrm.animation.json`, SHA-256 `52941a8bd1a0d422df938a9981d40cf9ba7ab765320c3a524f554222c772914b`
- Texture: `program/crazycraft-pack-production-v1/studio-epic-wave2/assets/export/textures/tide_empress_wyrm.png`, SHA-256 `211cc89ffba21684f770f0012c5f38b759b1423c208007fc3de708bda0e133bf`

Both geometry exports contain the brief-declared `breath`, `effect`, and `projectile` locators. Each asset currently exposes only generic `idle` and `action` animation clips. That is sufficient to identify the art inputs, but not sufficient to claim phase-ready animation or native Blockbench shipping proof. Both hero models require native editor round-trip and encounter animation assessment under the existing asset-quality gate.

## Exact arena and approach inputs

The prepared region contract describes the same recognizable beats as current Creative: two thrones/two aspects, concord pressure, relic focus, and ignition. The massing is therefore reusable without inventing a new visual identity.

| Input | Exact source | SHA-256 |
|---|---|---|
| Full proxy massing | `program/crazycraft-pack-production-v1/studio-prep/regions/twinbond/massing/twinbond_slice_v1.mcstructure` | `dc980b99897129e3747409b169e648db4d7b82f9933effbdceeb022a01b6ef6e` |
| Dual thrones | `program/crazycraft-pack-production-v1/studio-prep/assets/editable/twin_thrones.bbmodel` | `c71472332345b0b3277405ddd2bf8a30f8a05903bd373ebf6d4b8fd102a451bd` |
| Control obelisk site | `program/crazycraft-pack-production-v1/studio-prep/assets/editable/twinbond_obelisk_site.bbmodel` | `122ccdaf69f43c65d86d1fda17311055221939c529eaa1c3f7c1361c69a62195` |
| Ceremony anvil site | `program/crazycraft-pack-production-v1/studio-prep/assets/editable/ceremony_anvil_site.bbmodel` | `e914c87f2385e3a0881bd8e4fd5253ef886b5e49694752a88ea094c32d9309cb` |
| Arena ring | `program/crazycraft-pack-production-v1/studio-prep/assets/editable/twinbond_obsidian_ring.bbmodel` | `33e24507ab0300c391f2c24f2f37c6f76c9dd72684535208b80f63a46e048c64` |
| Out-of-region foreshadow | `program/crazycraft-pack-production-v1/studio-prep/assets/editable/twinbond_approach_marker.bbmodel` | `488e75335e8c569de1ef33d98c917048a4c45161c8ad317fa4ee0f7bebb4cc91` |

The massing file is 6,292,473 bytes and its associated manifest declares `[128, 48, 128]`. It has exact anchors for arrival `[64,12,22]`, gate `[64,12,30]`, ember throne `[36,12,64]`, tide throne `[92,12,64]`, center `[64,12,64]`, and completion `[64,12,94]`. This is preparation evidence only: the source package explicitly says it does not prove boss mechanics, phases, hazards, rewards, persistence, replay, audio, or balance.

The one unresolved arena decision is location/container. The old prep contract proposes an isolated logical `twinbond` container with an Editor UUID still TBD. Current Wave 1 authority does not explicitly adopt that container or replace it with a same-world site. Selecting either would exceed this audit.

## Reward authority

Current Wave 1 authority is clear on the primary reward chain:

`twinbond_relic` + Concord rite → full `trophy_edge`, with campaign clear, memory-set completion, and post-game mastery.

The Packet 006 `twinbond_relic` has exact art:

- Brief: `program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-006-equipment-progression/assets/briefs/twinbond_relic.json`, SHA-256 `43972f15c767808f4caf53dce5c3c7169aaa5db2719fd66e74db5fb723840f63`
- Editable: `program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-006-equipment-progression/assets/editable/twinbond_relic.bbmodel`, SHA-256 `e00dfc9d760c61f0c34607157e3bda0d8b4739336a9eeac433302f88f931c309`
- Geometry: `program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-006-equipment-progression/assets/export/models/twinbond_relic.geo.json`, SHA-256 `a47e96a31bfcc01b4ef60f56b05986dc419c7d0b759166e8489fad92a983f21c`
- Animation: `program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-006-equipment-progression/assets/export/animations/twinbond_relic.animation.json`, SHA-256 `cabecfd47525f992d6e660c44986c3318cf6c01a7069dfe1225eb283d8d03388`
- Texture: `program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-006-equipment-progression/assets/export/textures/twinbond_relic.png`, SHA-256 `d30406aabbb3d851966368fb0817a471e659e8e2f8ea4c54695bbacf85e9e228`

Its art still needs repair: the brief requires `dual_pulse`, while editable and exported animation data contain only `idle` and `action`. The geometry does contain the `effect` locator. This is a concrete Asset/Engineering repair, not a missing Creative identity.

The older finale reward `trophy_concord_scale` and old ignition key are superseded by the Wave 1 `twinbond_relic` chain. Likewise, `concord_sigil`, `concord_dueling_ring`, `ash_crownblade`, and `empress_tide_lance` occur in the old region kit but are not current Wave 1 finale rewards. They must not enter Wave 1 by inheritance.

Still unresolved are Concord Spark, the shipping presentation for Memory of Four Lands, any mastery-sigil term not already bound to Packet 006, and the exact award/ownership/persistence semantics. The latter semantics belong to `W1-CREATIVE-003`/`004`, not the asset-identity portion of `002`.

## G7 evidence and limits

Frozen G7 already contains:

- BP entities for both named wyrms with health, movement, melee targeting, loot-table links, and non-spawnable/non-summonable encounter posture;
- matching RP client entities, normalized geometry, identical source texture bytes, and generic animations;
- an obelisk-site block, feature, feature rule, runtime route, paired admission journal, pair cap, owner keys, terminal stamps, endpoint state, and `trophy_concord_scale` award;
- a `trophy_edge` item and finale-key path.

This proves reusable implementation exists. It does not bind Wave 1 semantics. The old reward, eight-trophy prerequisite, ad hoc worldgen obelisk, and generic dual melee entities conflict with or underspecify the current four-seal/relic/phase contract and should be refined or superseded. Gate 0 classified G7 `G7_STABLE_BDS_SUBSTRATE_FAIL_CONTENT_SCHEMA`; no Twinbond runtime behavior claim is made here.

## Recommended ledger action

At the next authorized decision-ledger revision, narrow `W1-CREATIVE-002`:

- Close: exact aspect IDs and existing art inputs.
- Close: arena/approach asset IDs and source locations.
- Close: primary finale reward identity (`twinbond_relic` + Trophy Edge ignition).
- Keep open: isolated-container versus same-world placement.
- Keep open: Concord Spark, Memory of Four Lands presentation, and any unbound mastery-sigil disposition.
- Keep open: whether Twinbond completion is mandatory for the Wave 1 machine-exit token.

Do not fold numeric phases, resets, multiplayer ownership, persistence, terminal reward guards, or loot probabilities into this resolution; those remain the separate `W1-CREATIVE-003` and `W1-CREATIVE-004` boundaries.
