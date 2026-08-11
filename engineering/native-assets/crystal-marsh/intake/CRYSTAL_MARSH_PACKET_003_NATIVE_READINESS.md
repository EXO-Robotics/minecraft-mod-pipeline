# Crystal Marsh Packet 003 native production-readiness intake

Authority: integration commit `bcd65076900a3688dd797d54719263d88afd501c`; tree `4d876b233e6b510687d238f1d7f6611c7c0c4ab9`; frozen packet `program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-003-crystal-marsh`.

This is a read-only static intake. Blockbench was not launched; packet assets and BP/RP were not edited.

## Outcome

**NOT_READY_NATIVE_REPAIR_REQUIRED**

All 50 canonical assets have complete hashed artifact sets, parseable JSON, decoded PNGs, consistent `aionforge_cm` source identifiers, and byte-identical category mirrors. Those strengths establish packet integrity, not native production readiness.

- Native repair required: 30 custom-geometry assets (10 creatures, 10 plants, 10 landmarks).
- Blockbench not applicable: 20 ordinary full-cube/flat-item assets (10 blocks, 10 resources); static texture normalization remains required.
- Real editable locator elements: 0/50.
- Exported locator sets matching briefs: 50/50, but native equivalence is unproven.
- Declared clip sets matching exports: 0/50.
- Texture contracts admitting the actual 32x32 atlases: 3/50; mismatches: 47/50.
- Editable projects with absolute texture paths requiring staged relative rebind: 50/50.
- Assets with unbound related-asset prose: 13/50; exact or contained packet IDs remain recorded separately.

## Systemic findings

- `CM-NATIVE-001` — All 50 editable projects lack real locator elements even though every brief declares at least one locator; exported geometry contains matching locator names, so those exports are deterministic-tool products rather than proven native-equivalent exports.
- `CM-NATIVE-002` — No asset's declared clip set equals its editable/exported clip set. Every project/export contains generic idle and action clips, including assets whose briefs declare no animation.
- `CM-NATIVE-003` — All editable projects, geometry exports, and PNGs use 32x32 atlases; the exact compatible/mismatch count is measured in the summary and each per-asset record.
- `CM-NATIVE-004` — Canonical source identifiers consistently use aionforge_cm; shipping normalization must bind approved identities into aionbound without editing the frozen packet.
- `CM-NATIVE-005` — Exact mirrors and parse/decode success prove packet integrity only. They do not prove Blockbench round-trip, native export equivalence, client rendering, animation playback, Marketplace acceptance, or physical PS4 behavior.
- `CM-NATIVE-006` — Every editable project records an absolute author-workstation texture path and must be rebound to a relative staged path before any native round trip or shipping export.
- `CM-NATIVE-007` — Related-asset fields mix exact warehouse IDs with prose. Exact IDs are recorded; unbound prose remains an explicit engineering binding gap and is not treated as a new Creative identity.

## Representative class gate

Run native repair only after staging immutable copies. The first bounded gate is:

- `marsh_wight` (hostile_biped_chapter_apex): chapter-facing silhouette, biped contacts, reach action, terminal collapse, and effect/gaze locator coverage.
- `crystal_dragonfly` (small_flying_creature): hover, flight, dart transitions, transparent thin-feature readability, and effect/gaze locators.
- `silt_crocodile` (large_aquatic_ambush_creature): long-body articulation, swim/submerge/lunge/bite coverage, 128x64 contract, and effect/gaze locators.
- `bubble_pod` (animated_translucent_plant): declared bob clip, effect locator, transparent material readability, and small-form UV coverage.
- `flood_reed` (animated_plant_sway): declared sway loop, effect locator, and thin-feature contact/readability representative.
- `sunken_shrine` (animated_landmark_prop): declared glow clip, effect locator, and submerged landmark material representative.
- `ancient_boat` (static_landmark_prop): complex static silhouette, effect locator, and 64-128 texture-contract representative.

Each representative must use real native locators, exact brief-declared clips, contract-compliant textures, a zero-warning reopen/save/reopen/native-export round trip, fixed Golden proof views, two critique cycles, and exact evidence hashes. Passing representatives establish construction templates only; every scaled asset still passes independently.

## Bounded repair order

Stage 1 is an implementation-safe normalization lane: blocks remain ordinary full cubes and resources remain flat inventory items, so their packet `.bbmodel`, locator, and generic animation defects are explicitly Blockbench `NOT_APPLICABLE`. Custom creatures, plants, and landmark props remain behind the representative native gate.

1. Blockbench-N/A block/resource normalization; may start immediately and independently: `prism_pearl`, `crystal_reed_item`, `marsh_resin`, `glass_algae`, `silt_core`, `flood_crystal`, `moon_pearl`, `wet_chitin`, `mire_bloom_item`, `crystal_root_item`, `crystal_log`, `marsh_wood`, `flood_planks`, `crystal_stone`, `prism_brick`, `wet_clay_block`, `glass_root_block`, `algae_block`, `marsh_soil`, `crystal_gravel`. Exit: native block/item form selected and textures normalized to the frozen brief without consuming packet geometry, locators, or generic animations.
2. seven representative custom-geometry class-gate assets only: `marsh_wight`, `crystal_dragonfly`, `silt_crocodile`, `bubble_pod`, `flood_reed`, `sunken_shrine`, `ancient_boat`. Exit: all representative native and Golden gates pass before custom-geometry scale-out.
3. remaining custom-geometry creatures: `crystal_newt`, `prism_frog`, `glass_heron`, `mire_turtle`, `bloom_crab`, `reed_serpent`, `bog_watcher`. Exit: each creature independently passes native locator, declared motion, texture, Golden, and export-equivalence gates.
4. remaining custom-geometry plants: `crystal_lily`, `prism_bloom`, `glass_moss`, `marsh_fern`, `glow_kelp`, `mire_orchid`, `pearl_grass`, `crystal_vine`. Exit: each plant independently passes its declared static-or-role-clip contract and native locator/export gate.
5. remaining custom-geometry landmarks: `crystal_obelisk`, `flooded_dock`, `marsh_totem`, `marsh_broken_bridge`, `crystal_arch`, `pearl_cairn`, `ruined_observatory`, `deep_pool_entrance`. Exit: each landmark independently passes its declared static-or-role-clip contract and native locator/export gate.

## Per-asset disposition

| Asset | Tier | Priority | Blockbench | Clips declared/exported | Locators source/export | Texture brief/actual | Related-ID gap |
|---|---|---:|---|---|---|---|---|
| `crystal_newt` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 6/2 | 0/2 | 64×64/32x32 | crystal_root |
| `marsh_wight` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 | none |
| `silt_crocodile` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 6/2 | 0/2 | 128×64/32x32 | none |
| `prism_frog` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 | none |
| `glass_heron` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 6/2 | 0/2 | 64–128/32x32 | none |
| `mire_turtle` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 6/2 | 0/2 | 64×64/32x32 | none |
| `bloom_crab` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 | mire_bloom |
| `reed_serpent` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 | none |
| `crystal_dragonfly` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 5/2 | 0/2 | 64×64/32x32 | none |
| `bog_watcher` | CREATURE | P0 | NATIVE_REPAIR_REQUIRED | 6/2 | 0/2 | 64–128/32x32 | deep_pool, bog threat |
| `prism_pearl` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `crystal_reed_item` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `marsh_resin` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | not moss_resin / not ember_resin |
| `glass_algae` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `silt_core` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `flood_crystal` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `moon_pearl` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | not moon_sap |
| `wet_chitin` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `mire_bloom_item` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `crystal_root_item` | RESOURCE | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `crystal_lily` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16–32/32x32 | none |
| `flood_reed` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16/32x32 | none |
| `prism_bloom` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16–32/32x32 | none |
| `glass_moss` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16 seamless/32x32 | not glow_moss WW |
| `marsh_fern` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16/32x32 | not whisper_fern |
| `glow_kelp` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16/32x32 | deep water edge |
| `mire_orchid` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16–32/32x32 | none |
| `bubble_pod` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16/32x32 | bubble aesthetic |
| `pearl_grass` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 16/32x32 | none |
| `crystal_vine` | PLANT | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 16/32x32 | crystal_root |
| `crystal_log` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | wood family |
| `marsh_wood` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `flood_planks` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `crystal_stone` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `prism_brick` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `wet_clay_block` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `glass_root_block` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `algae_block` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `marsh_soil` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `crystal_gravel` | BLOCK | P0 | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | 0/2 | 0/1 | 16×16/32x32 | none |
| `sunken_shrine` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 64–128/32x32 | none |
| `crystal_obelisk` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 64/32x32 | none |
| `flooded_dock` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 64–128/32x32 | none |
| `ancient_boat` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 64–128/32x32 | none |
| `marsh_totem` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 1/2 | 0/1 | 64/32x32 | none |
| `marsh_broken_bridge` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 | not ashen broken_bridge |
| `crystal_arch` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 | none |
| `pearl_cairn` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 64/32x32 | none |
| `ruined_observatory` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 | sunken civilization |
| `deep_pool_entrance` | LANDMARK | P0 | NATIVE_REPAIR_REQUIRED | 0/2 | 0/1 | 128/32x32 | none |

## Proof boundary

Proven here: exact packet hashes, JSON parsing, PNG CRC/decompression/scanlines, source namespace consistency, mirror equality, UUID/link closure, and declared-versus-actual static comparisons.

Not proven here: Blockbench UI round-trip, native-export equivalence, Golden visual quality, Bedrock rendering/animation/gameplay, Creator Tools/BDS admission, multiplayer, performance, console/controller/Realm/split-screen/physical PS4, Marketplace approval, or release readiness.

The machine-readable report contains every artifact path and SHA-256.
