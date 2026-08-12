# Skyreach Packet 004 native production-readiness intake

Authority: integration commit `1810d0bb75e73be16d1c98e1d57dfe9ea485849d`; tree `11f377745f69b848396780dac1d039955fa90131`; frozen packet `program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-004-skyreach-cliffs`.

This is a read-only static intake. Blockbench was not launched; packet assets and BP/RP were not edited.

## Outcome

**NOT_READY_NATIVE_REPAIR_REQUIRED**

All 50 canonical assets have complete hashed artifact sets, parseable JSON, decoded PNGs, consistent `aionforge_sr` source identifiers, and byte-identical category mirrors. Those strengths establish packet integrity, not native production readiness.

- Native repair required: 30 custom-geometry assets (10 creatures, 10 plants, 10 landmarks).
- Blockbench not applicable: 20 ordinary full-cube/flat-item assets (10 blocks, 10 resources); static texture normalization remains required.
- Real editable locator elements: 0/50.
- Exported locator sets matching briefs: 50/50, but native equivalence is unproven.
- Declared clip sets matching exports: 0/50.
- Texture contracts admitting the actual 32x32 atlases: 4/50; mismatches: 46/50.
- Editable projects with absolute texture paths requiring staged relative rebind: 50/50.
- Assets with unbound related-asset prose: 2/50; exact or contained packet IDs remain recorded separately.

## Systemic findings

- `SR-NATIVE-001` — All 50 editable projects lack real locator elements even though every brief declares at least one locator; exported geometry contains matching locator names, so those exports are deterministic-tool products rather than proven native-equivalent exports.
- `SR-NATIVE-002` — No asset's declared clip set equals its editable/exported clip set. Every project/export contains generic idle and action clips, including assets whose briefs declare no animation.
- `SR-NATIVE-003` — All editable projects, geometry exports, and PNGs use 32x32 atlases; the exact compatible/mismatch count is measured in the summary and each per-asset record.
- `SR-NATIVE-004` — Canonical source identifiers consistently use aionforge_sr; shipping normalization must bind approved identities into aionbound without editing the frozen packet.
- `SR-NATIVE-005` — Exact mirrors and parse/decode success prove packet integrity only. They do not prove Blockbench round-trip, native export equivalence, client rendering, animation playback, Marketplace acceptance, or physical PS4 behavior.
- `SR-NATIVE-006` — Every editable project records an absolute author-workstation texture path and must be rebound to a relative staged path before any native round trip or shipping export.
- `SR-NATIVE-007` — Related-asset fields mix exact warehouse IDs with prose. Exact IDs are recorded; unbound prose remains an explicit engineering binding gap and is not treated as a new Creative identity.

## Representative class gate

Run native repair only after staging immutable copies. The first bounded gate is:

- `wind_roc` (apex_soaring_flyer): apex-scale wing silhouette, perch/soar/dive transitions, terminal fall, and effect/gaze locator coverage.
- `gale_hawk` (mid_soaring_flyer): compact flight, stoop transitions, wing-contact readability, and effect/gaze locators.
- `cloud_goat` (ledge_grazer_quadruped): four-leg contact, shelf locomotion, ledge-hop action, cloud-fleece silhouette, and effect/gaze locators.
- `wind_reed_plant` (hard_sway_cliff_plant): declared hard-sway loop, effect locator, and wind-bent thin-feature readability.
- `hanging_sky_vine` (hanging_cliff_plant): declared sway loop, effect locator, hanging contact, and vertical traversal readability.
- `wind_shrine` (animated_landmark_prop): declared chime loop, effect locator, crest-plate silhouette, and wind-worship landmark readability.
- `observation_tower` (static_landmark_prop): tall static shelf silhouette, effect locator, and 128 texture-contract representative.

Each representative must use real native locators, exact brief-declared clips, contract-compliant textures, a zero-warning reopen/save/reopen/native-export round trip, fixed Golden proof views, two critique cycles, and exact evidence hashes. Passing representatives establish construction templates only; every scaled asset still passes independently.

## Bounded repair order

Stage 1 is an implementation-safe normalization lane: blocks remain ordinary full cubes and resources remain flat inventory items, so their packet `.bbmodel`, locator, and generic animation defects are explicitly Blockbench `NOT_APPLICABLE`. Custom creatures, plants, and landmark props remain behind the representative native gate.

1. Blockbench-N/A block/resource normalization; may start immediately and independently: `sky_feather`, `wind_silk`, `cloud_wool`, `cliff_crystal`, `storm_pinion`, `aether_stone`, `updraft_reed_item`, `sky_vine_item`, `float_resin`, `lift_bloom_item`, `skyreach_log`, `skyreach_wood`, `skyreach_planks`, `wind_slate`, `cliff_stone`, `rope_timber`, `cloud_wool_block`, `pale_shelf_stone`, `cliff_gravel`, `sky_moss_block`. Exit: native block/item form selected and textures normalized to the frozen brief without consuming packet geometry, locators, or generic animations.
2. seven representative custom-geometry class-gate assets only: `wind_roc`, `gale_hawk`, `cloud_goat`, `wind_reed_plant`, `hanging_sky_vine`, `wind_shrine`, `observation_tower`. Exit: all representative native and Golden gates pass before custom-geometry scale-out.
3. remaining custom-geometry creatures: `sky_fox`, `cliff_ram`, `ropewing`, `stone_vulture`, `glide_drake`, `storm_gull`, `ruin_harpy`. Exit: each creature independently passes native locator, declared motion, texture, Golden, and export-equivalence gates.
4. remaining custom-geometry plants: `cliff_flower`, `cloud_moss`, `floating_blossom`, `rope_root`, `cloudpuff_plant`, `shelf_shrub`, `skybloom`, `nest_thatch_tuft`. Exit: each plant independently passes its declared static-or-role-clip contract and native locator/export gate.
5. remaining custom-geometry landmarks: `rope_bridge`, `cliff_outpost`, `floating_ruin_floor`, `nest_platform`, `broken_sky_path`, `hanging_lift_frame`, `ancient_sky_arch`, `cliff_beacon`. Exit: each landmark independently passes its declared static-or-role-clip contract and native locator/export gate.

## Per-asset disposition

| Asset | Tier | Priority | Blockbench | Clips declared/exported | Locators source/export | Texture brief/actual | Related-ID gap |
|---|---|---:|---|---|---|---|---|
| `wind_roc` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 128×64/32x32 | none |
| `cloud_goat` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 | none |
| `sky_fox` | CREATURE | P1 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 | none |
| `cliff_ram` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 | none |
| `ropewing` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 | none |
| `gale_hawk` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 | none |
| `stone_vulture` | CREATURE | P1 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 | none |
| `glide_drake` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 128×64/32x32 | none |
| `storm_gull` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 6/2 | 0/2 | 64×64/32x32 | none |
| `ruin_harpy` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 128×64/32x32 | none |
| `sky_feather` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `wind_silk` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `cloud_wool` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `cliff_crystal` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `storm_pinion` | RESOURCE | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `aether_stone` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `updraft_reed_item` | RESOURCE | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `sky_vine_item` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `float_resin` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `lift_bloom_item` | RESOURCE | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `hanging_sky_vine` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16–32/32x32 | none |
| `cliff_flower` | PLANT | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16/32x32 | none |
| `cloud_moss` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16 seamless/32x32 | none |
| `wind_reed_plant` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16/32x32 | none |
| `floating_blossom` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16–32/32x32 | none |
| `rope_root` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16–32/32x32 | none |
| `cloudpuff_plant` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16–32/32x32 | none |
| `shelf_shrub` | PLANT | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16/32x32 | none |
| `skybloom` | PLANT | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16/32x32 | none |
| `nest_thatch_tuft` | PLANT | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16/32x32 | none |
| `skyreach_log` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | wood family |
| `skyreach_wood` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `skyreach_planks` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `wind_slate` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `cliff_stone` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `rope_timber` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `cloud_wool_block` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `pale_shelf_stone` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `cliff_gravel` | BLOCK | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `sky_moss_block` | BLOCK | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `rope_bridge` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 | none |
| `wind_shrine` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 64/32x32 | crest gold |
| `cliff_outpost` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 | none |
| `floating_ruin_floor` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 | none |
| `nest_platform` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 64–128/32x32 | none |
| `broken_sky_path` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 | none |
| `hanging_lift_frame` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 64–128/32x32 | none |
| `ancient_sky_arch` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 | none |
| `observation_tower` | LANDMARK | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 | none |
| `cliff_beacon` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 64/32x32 | none |

## Proof boundary

Proven here: exact packet hashes, JSON parsing, PNG CRC/decompression/scanlines, source namespace consistency, mirror equality, UUID/link closure, and declared-versus-actual static comparisons.

Not proven here: Blockbench UI round-trip, native-export equivalence, Golden visual quality, Bedrock rendering/animation/gameplay, Creator Tools/BDS admission, multiplayer, performance, console/controller/Realm/split-screen/physical PS4, Marketplace approval, or release readiness.

The machine-readable report contains every artifact path and SHA-256.
