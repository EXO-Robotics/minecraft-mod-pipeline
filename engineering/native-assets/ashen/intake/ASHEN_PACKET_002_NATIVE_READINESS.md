# Ashen Packet 002 native production-readiness intake

Authority: integration commit `9acf1b0f62ade90b59ba65e0a9e0618852ff3159`; frozen packet `program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-002-ashen-highlands`.

This is a read-only static intake. Blockbench was not launched; packet assets and BP/RP were not edited.

## Outcome

**NOT_READY_NATIVE_REPAIR_REQUIRED**

All 50 canonical assets have complete hashed artifact sets, parseable JSON, decoded PNGs, consistent `aionforge_ah` source identifiers, and byte-identical category mirrors. Those strengths establish packet integrity, not native production readiness.

- Native repair required: 30 custom-geometry assets (10 creatures, 10 plants, 10 landmarks).
- Blockbench not applicable: 20 ordinary full-cube/flat-item assets (10 blocks, 10 resources); static texture normalization remains required.
- Real editable locator elements: 0/50.
- Exported locator sets matching briefs: 50/50, but native equivalence is unproven.
- Declared clip sets matching exports: 0/50.
- Texture contracts admitting the actual 32x32 atlases: 2/50; mismatches: 48/50.

## Systemic findings

- `AH-NATIVE-001` — All 50 editable projects lack real locator elements even though every brief declares at least one locator; exported geometry contains matching locator names, so those exports are deterministic-tool products rather than proven native-equivalent exports.
- `AH-NATIVE-002` — No asset's declared clip set equals its editable/exported clip set. Every project/export contains generic idle and action clips, including assets whose briefs declare no animation.
- `AH-NATIVE-003` — All editable projects, geometry exports, and PNGs use 32x32 atlases; only two brief declarations admit 32x32, leaving 48 texture-contract mismatches.
- `AH-NATIVE-004` — Canonical source identifiers consistently use aionforge_ah; shipping normalization must bind approved identities into aionbound without editing the frozen packet.
- `AH-NATIVE-005` — Exact mirrors and parse/decode success prove packet integrity only. They do not prove Blockbench round-trip, native export equivalence, client rendering, animation playback, Marketplace acceptance, or physical PS4 behavior.

## Representative class gate

Run native repair only after staging immutable copies. The first bounded gate is:

- `ash_drake` (elite_multipart_projectile_locator): highest creature density, wing articulation, and three required locators.
- `ember_crow` (flying_creature): flight, glide, perch, contact, and loop-transition coverage.
- `ash_ram` (ground_creature): walk contact and headbutt action representative.
- `fire_bloom` (animated_plant): declared glow clip and small-form UV/readability representative.
- `smoke_reed` (animated_plant_sway): declared sway loop and thin-feature representative.
- `ember_forge` (animated_landmark_prop): declared glow idle and effect-locator representative.
- `ancient_kiln` (static_landmark_prop): complex static prop and large-atlas representative.

Each representative must use real native locators, exact brief-declared clips, contract-compliant textures, a zero-warning reopen/save/reopen/native-export round trip, fixed Golden proof views, two critique cycles, and exact evidence hashes. Passing representatives establish construction templates only; every scaled asset still passes independently.

## Bounded repair order

1. seven representative class-gate assets only: `ash_drake`, `ember_crow`, `ash_ram`, `fire_bloom`, `smoke_reed`, `ember_forge`, `ancient_kiln`. Exit: all representative native and Golden gates pass.
2. remaining P0 custom-geometry assets: `basalt_tortoise`, `char_wolf`, `cinder_grass`, `ash_fern`, `magma_moss`, `burned_camp`, `lava_shrine`, `ash_cave`. Exit: each asset independently passes its class-native gate.
3. remaining P1 creatures: `cinder_lynx`, `ash_mite`, `soot_stag`, `magma_lizard`, `furnace_beetle`. Exit: each creature has declared motion coverage and native locator equivalence.
4. remaining P1 plants and landmarks: `ember_vine`, `basalt_flower`, `char_shrub`, `glow_root`, `soot_mushroom`, `ash_watchtower`, `char_wagon`, `basalt_arch`, `fire_totem`, `broken_bridge`. Exit: each asset independently passes its class-native gate.
5. Blockbench-N/A static normalization: `charbone`, `ember_resin`, `basalt_core`, `volcanic_glass_shard`, `ash_crystal`, `smolder_bark`, `fire_bloom_seed`, `furnace_chitin`, `sulfur_cluster`, `heatstone`, `ash_log`, `char_planks`, `basalt_brick`, `smolder_stone`, `ash_soil`, `ember_moss`, `volcanic_glass_block`, `heat_bark`, `basalt_pillar`, `cinder_gravel`. Exit: native block/item form selected and textures normalized to the frozen brief without consuming packet geometry or generic animations.

## Per-asset disposition

| Asset | Tier | Phase | Blockbench | Clips declared/exported | Locators source/export | Texture brief/actual |
|---|---|---:|---|---|---|---|
| `ash_ram` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 |
| `cinder_lynx` | CREATURE | P1 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 |
| `ember_crow` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 6/2 | 0/2 | 64×64/32x32 |
| `basalt_tortoise` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64–128/32x32 |
| `ash_mite` | CREATURE | P1 | NATIVE_REPAIR_REQUIRED | 4/2 | 0/1 | 64×64/32x32 |
| `soot_stag` | CREATURE | P1 | NATIVE_REPAIR_REQUIRED | 6/2 | 0/2 | 128×64/32x32 |
| `magma_lizard` | CREATURE | P1 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 |
| `char_wolf` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 6/2 | 0/2 | 64×64/32x32 |
| `furnace_beetle` | CREATURE | P1 | NATIVE_REPAIR_REQUIRED | 6/2 | 0/2 | 64–128/32x32 |
| `ash_drake` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 6/2 | 0/3 | 128×128/32x32 |
| `charbone` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `ember_resin` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `basalt_core` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `volcanic_glass_shard` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `ash_crystal` | RESOURCE | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `smolder_bark` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `fire_bloom_seed` | RESOURCE | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `furnace_chitin` | RESOURCE | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `sulfur_cluster` | RESOURCE | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `heatstone` | RESOURCE | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `fire_bloom` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16–32/32x32 |
| `cinder_grass` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16/32x32 |
| `ash_fern` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16/32x32 |
| `ember_vine` | PLANT | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16/32x32 |
| `magma_moss` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16/32x32 |
| `smoke_reed` | PLANT | P1 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16/32x32 |
| `basalt_flower` | PLANT | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16/32x32 |
| `char_shrub` | PLANT | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16–32/32x32 |
| `glow_root` | PLANT | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16/32x32 |
| `soot_mushroom` | PLANT | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16/32x32 |
| `ash_log` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `char_planks` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `basalt_brick` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `smolder_stone` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `ash_soil` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `ember_moss` | BLOCK | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `volcanic_glass_block` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `heat_bark` | BLOCK | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `basalt_pillar` | BLOCK | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `cinder_gravel` | BLOCK | P1 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 |
| `burned_camp` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 |
| `lava_shrine` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 64/32x32 |
| `ancient_kiln` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 64–128/32x32 |
| `ash_watchtower` | LANDMARK | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 |
| `char_wagon` | LANDMARK | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 64–128/32x32 |
| `basalt_arch` | LANDMARK | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 |
| `ember_forge` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 64/32x32 |
| `fire_totem` | LANDMARK | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 64/32x32 |
| `ash_cave` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 |
| `broken_bridge` | LANDMARK | P1 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 |

## Proof boundary

Proven here: exact packet hashes, JSON parsing, PNG CRC/decompression/scanlines, source namespace consistency, mirror equality, UUID/link closure, and declared-versus-actual static comparisons.

Not proven here: Blockbench UI round-trip, native-export equivalence, Golden visual quality, Bedrock rendering/animation/gameplay, Creator Tools/BDS admission, multiplayer, performance, console/controller/Realm/split-screen/physical PS4, Marketplace approval, or release readiness.

The machine-readable report contains every artifact path and SHA-256.
