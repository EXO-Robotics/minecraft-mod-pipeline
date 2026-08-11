# Wave 1 Packet Normalization Inventory

Status: **STATIC_INVENTORY_COMPLETE_NORMALIZATION_AND_NATIVE_REPAIR_REQUIRED**

This is a deterministic static inventory. It does not prove a native Blockbench round-trip, native-export equivalence, Bedrock rendering, gameplay behavior, or physical-console readiness.

## Authority binding

- Creative contract SHA-256: `aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5`
- Engineering decision ledger SHA-256: `3bd4e790382b15133e76fdfc5d4ac77d176adcda5af2e0184d5a219907ffdb73`
- Canonical editable source: each sprint's `assets/editable/<warehouse_id>.bbmodel` and sibling PNG.
- Category copies are mirrors only and are compared byte-for-byte.
- Shipping namespace decision: `aionbound:<warehouse_id>`; packet namespace identifiers require normalization in successor production files.

## Result

- Warehouse IDs bound: **250 / 250**
- Canonical file sets complete: **250 / 250**
- Category mirrors exact: **250 / 250**
- Static format sets valid: **250 / 250**
- Assets requiring normalization or repair: **250**
- Native Blockbench/editor proof: **NOT RUN**

## Packet rollup

| Packet | IDs | Canonical complete | Mirrors exact | Static valid | Repair/normalize |
|---|---:|---:|---:|---:|---:|
| 001 001_whisperwood | 50 | 50 | 50 | 50 | 50 |
| 002 002_ashen_highlands | 50 | 50 | 50 | 50 | 50 |
| 003 003_crystal_marsh | 50 | 50 | 50 | 50 | 50 |
| 004 004_skyreach_cliffs | 50 | 50 | 50 | 50 | 50 |
| 006 006_equipment | 50 | 50 | 50 | 50 | 50 |

## Evidence-derived findings

- `BRIEF_TEXTURE_RESOLUTION_MISMATCH`: 154
- `DECLARED_ANIMATION_COVERAGE_ABSENT`: 102
- `DECLARED_LOCATORS_ABSENT_FROM_EDITABLE_AND_EXPORT`: 250
- `EDITABLE_ABSOLUTE_TEXTURE_PATH_REQUIRES_NORMALIZATION`: 250
- `RELATED_ASSET_PROSE_REQUIRES_ENGINEERING_BINDING`: 60
- `RUNTIME_NAMESPACE_NORMALIZATION_REQUIRED`: 250

The two highest-risk findings are contractual rather than cosmetic:

- Briefs declare locator names that are absent as native locator elements in editable projects and absent from exported geometry. Locator-dependent or hero shipping use requires repair; ordinary native-JSON/block-assembly implementations may instead document Blockbench as `NOT_APPLICABLE` under the decision ledger.
- Briefs declare role-specific animation sets, while exported animation files expose only the actually inventoried clips. Missing declared clips must be implemented or explicitly removed from the implementation contract.

## Complete warehouse binding

| Packet | Category | Warehouse ID | Runtime ID | Static status | Native risk |
|---|---|---|---|---|---|
| 001 | resources | `ancient_acorn` | `aionbound:ancient_acorn` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | structures | `ancient_totem` | `aionbound:ancient_totem` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | creatures | `bark_wraith` | `aionbound:bark_wraith` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 001 | resources | `briar_antler` | `aionbound:briar_antler` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | creatures | `briar_elk` | `aionbound:briar_elk` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 001 | plants | `briar_vine` | `aionbound:briar_vine` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | structures | `broken_wagon` | `aionbound:broken_wagon` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | plants | `ember_thistle` | `aionbound:ember_thistle` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | structures | `fallen_giant_tree` | `aionbound:fallen_giant_tree` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | blocks | `forest_brick` | `aionbound:forest_brick` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | structures | `forest_waystone` | `aionbound:forest_waystone` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | plants | `glow_moss` | `aionbound:glow_moss` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | resources | `glow_spore` | `aionbound:glow_spore` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | resources | `hollow_amber` | `aionbound:hollow_amber` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | structures | `hollow_cave_entrance` | `aionbound:hollow_cave_entrance` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | plants | `hollow_lily` | `aionbound:hollow_lily` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | creatures | `hollow_widow_spider` | `aionbound:hollow_widow_spider` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 001 | blocks | `hollow_wood` | `aionbound:hollow_wood` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | structures | `hunter_camp` | `aionbound:hunter_camp` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | plants | `lantern_bloom` | `aionbound:lantern_bloom` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | resources | `lantern_fur` | `aionbound:lantern_fur` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | creatures | `lantern_hare` | `aionbound:lantern_hare` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 001 | structures | `lantern_post` | `aionbound:lantern_post` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | resources | `moon_sap` | `aionbound:moon_sap` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | plants | `mooncap_mushroom` | `aionbound:mooncap_mushroom` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | blocks | `moss_bark` | `aionbound:moss_bark` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | structures | `moss_cairn` | `aionbound:moss_cairn` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | resources | `moss_resin` | `aionbound:moss_resin` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | creatures | `mosskip_buck` | `aionbound:mosskip_buck` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 001 | creatures | `mosskip_doe` | `aionbound:mosskip_doe` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 001 | creatures | `mosskip_fawn` | `aionbound:mosskip_fawn` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 001 | structures | `owl_shrine` | `aionbound:owl_shrine` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | plants | `pale_reed` | `aionbound:pale_reed` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | structures | `root_bridge` | `aionbound:root_bridge` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | plants | `root_flower` | `aionbound:root_flower` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | resources | `root_heart` | `aionbound:root_heart` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | creatures | `rootback_boar` | `aionbound:rootback_boar` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 001 | creatures | `rot_wolf` | `aionbound:rot_wolf` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 001 | plants | `star_grass` | `aionbound:star_grass` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | blocks | `stripped_whisperwood_log` | `aionbound:stripped_whisperwood_log` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | creatures | `thorn_stalker` | `aionbound:thorn_stalker` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 001 | resources | `whisper_bark` | `aionbound:whisper_bark` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | plants | `whisper_fern` | `aionbound:whisper_fern` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | blocks | `whisperwood_leaves` | `aionbound:whisperwood_leaves` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | blocks | `whisperwood_log` | `aionbound:whisperwood_log` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | blocks | `whisperwood_planks` | `aionbound:whisperwood_planks` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | blocks | `whisperwood_roots` | `aionbound:whisperwood_roots` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | blocks | `whisperwood_sapling` | `aionbound:whisperwood_sapling` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | blocks | `whisperwood_wood` | `aionbound:whisperwood_wood` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 001 | resources | `widow_silk` | `aionbound:widow_silk` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | structures | `ancient_kiln` | `aionbound:ancient_kiln` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | structures | `ash_cave` | `aionbound:ash_cave` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | resources | `ash_crystal` | `aionbound:ash_crystal` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | creatures | `ash_drake` | `aionbound:ash_drake` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 002 | plants | `ash_fern` | `aionbound:ash_fern` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | blocks | `ash_log` | `aionbound:ash_log` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | creatures | `ash_mite` | `aionbound:ash_mite` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 002 | creatures | `ash_ram` | `aionbound:ash_ram` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 002 | blocks | `ash_soil` | `aionbound:ash_soil` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | structures | `ash_watchtower` | `aionbound:ash_watchtower` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | structures | `basalt_arch` | `aionbound:basalt_arch` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | blocks | `basalt_brick` | `aionbound:basalt_brick` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | resources | `basalt_core` | `aionbound:basalt_core` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | plants | `basalt_flower` | `aionbound:basalt_flower` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | blocks | `basalt_pillar` | `aionbound:basalt_pillar` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | creatures | `basalt_tortoise` | `aionbound:basalt_tortoise` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 002 | structures | `broken_bridge` | `aionbound:broken_bridge` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | structures | `burned_camp` | `aionbound:burned_camp` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | blocks | `char_planks` | `aionbound:char_planks` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | plants | `char_shrub` | `aionbound:char_shrub` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | structures | `char_wagon` | `aionbound:char_wagon` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | creatures | `char_wolf` | `aionbound:char_wolf` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 002 | resources | `charbone` | `aionbound:charbone` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | plants | `cinder_grass` | `aionbound:cinder_grass` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | blocks | `cinder_gravel` | `aionbound:cinder_gravel` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | creatures | `cinder_lynx` | `aionbound:cinder_lynx` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 002 | creatures | `ember_crow` | `aionbound:ember_crow` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 002 | structures | `ember_forge` | `aionbound:ember_forge` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | blocks | `ember_moss` | `aionbound:ember_moss` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | resources | `ember_resin` | `aionbound:ember_resin` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | plants | `ember_vine` | `aionbound:ember_vine` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | plants | `fire_bloom` | `aionbound:fire_bloom` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | resources | `fire_bloom_seed` | `aionbound:fire_bloom_seed` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | structures | `fire_totem` | `aionbound:fire_totem` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | creatures | `furnace_beetle` | `aionbound:furnace_beetle` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 002 | resources | `furnace_chitin` | `aionbound:furnace_chitin` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | plants | `glow_root` | `aionbound:glow_root` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | blocks | `heat_bark` | `aionbound:heat_bark` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | resources | `heatstone` | `aionbound:heatstone` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | structures | `lava_shrine` | `aionbound:lava_shrine` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | creatures | `magma_lizard` | `aionbound:magma_lizard` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 002 | plants | `magma_moss` | `aionbound:magma_moss` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | plants | `smoke_reed` | `aionbound:smoke_reed` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | resources | `smolder_bark` | `aionbound:smolder_bark` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | blocks | `smolder_stone` | `aionbound:smolder_stone` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | plants | `soot_mushroom` | `aionbound:soot_mushroom` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | creatures | `soot_stag` | `aionbound:soot_stag` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 002 | resources | `sulfur_cluster` | `aionbound:sulfur_cluster` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | blocks | `volcanic_glass_block` | `aionbound:volcanic_glass_block` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 002 | resources | `volcanic_glass_shard` | `aionbound:volcanic_glass_shard` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | blocks | `algae_block` | `aionbound:algae_block` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | structures | `ancient_boat` | `aionbound:ancient_boat` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | creatures | `bloom_crab` | `aionbound:bloom_crab` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 003 | creatures | `bog_watcher` | `aionbound:bog_watcher` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 003 | plants | `bubble_pod` | `aionbound:bubble_pod` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | structures | `crystal_arch` | `aionbound:crystal_arch` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | creatures | `crystal_dragonfly` | `aionbound:crystal_dragonfly` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 003 | blocks | `crystal_gravel` | `aionbound:crystal_gravel` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | plants | `crystal_lily` | `aionbound:crystal_lily` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | blocks | `crystal_log` | `aionbound:crystal_log` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | creatures | `crystal_newt` | `aionbound:crystal_newt` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 003 | structures | `crystal_obelisk` | `aionbound:crystal_obelisk` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | resources | `crystal_reed_item` | `aionbound:crystal_reed_item` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | resources | `crystal_root_item` | `aionbound:crystal_root_item` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | blocks | `crystal_stone` | `aionbound:crystal_stone` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | plants | `crystal_vine` | `aionbound:crystal_vine` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | structures | `deep_pool_entrance` | `aionbound:deep_pool_entrance` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | resources | `flood_crystal` | `aionbound:flood_crystal` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | blocks | `flood_planks` | `aionbound:flood_planks` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | plants | `flood_reed` | `aionbound:flood_reed` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | structures | `flooded_dock` | `aionbound:flooded_dock` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | resources | `glass_algae` | `aionbound:glass_algae` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | creatures | `glass_heron` | `aionbound:glass_heron` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 003 | plants | `glass_moss` | `aionbound:glass_moss` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | blocks | `glass_root_block` | `aionbound:glass_root_block` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | plants | `glow_kelp` | `aionbound:glow_kelp` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | structures | `marsh_broken_bridge` | `aionbound:marsh_broken_bridge` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | plants | `marsh_fern` | `aionbound:marsh_fern` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | resources | `marsh_resin` | `aionbound:marsh_resin` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | blocks | `marsh_soil` | `aionbound:marsh_soil` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | structures | `marsh_totem` | `aionbound:marsh_totem` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | creatures | `marsh_wight` | `aionbound:marsh_wight` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 003 | blocks | `marsh_wood` | `aionbound:marsh_wood` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | resources | `mire_bloom_item` | `aionbound:mire_bloom_item` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | plants | `mire_orchid` | `aionbound:mire_orchid` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | creatures | `mire_turtle` | `aionbound:mire_turtle` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 003 | resources | `moon_pearl` | `aionbound:moon_pearl` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | structures | `pearl_cairn` | `aionbound:pearl_cairn` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | plants | `pearl_grass` | `aionbound:pearl_grass` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | plants | `prism_bloom` | `aionbound:prism_bloom` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | blocks | `prism_brick` | `aionbound:prism_brick` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | creatures | `prism_frog` | `aionbound:prism_frog` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 003 | resources | `prism_pearl` | `aionbound:prism_pearl` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | creatures | `reed_serpent` | `aionbound:reed_serpent` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 003 | structures | `ruined_observatory` | `aionbound:ruined_observatory` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | resources | `silt_core` | `aionbound:silt_core` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | creatures | `silt_crocodile` | `aionbound:silt_crocodile` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 003 | structures | `sunken_shrine` | `aionbound:sunken_shrine` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | resources | `wet_chitin` | `aionbound:wet_chitin` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 003 | blocks | `wet_clay_block` | `aionbound:wet_clay_block` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | resources | `aether_stone` | `aionbound:aether_stone` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | structures | `ancient_sky_arch` | `aionbound:ancient_sky_arch` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | structures | `broken_sky_path` | `aionbound:broken_sky_path` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | structures | `cliff_beacon` | `aionbound:cliff_beacon` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | resources | `cliff_crystal` | `aionbound:cliff_crystal` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | plants | `cliff_flower` | `aionbound:cliff_flower` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | blocks | `cliff_gravel` | `aionbound:cliff_gravel` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | structures | `cliff_outpost` | `aionbound:cliff_outpost` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | creatures | `cliff_ram` | `aionbound:cliff_ram` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 004 | blocks | `cliff_stone` | `aionbound:cliff_stone` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | creatures | `cloud_goat` | `aionbound:cloud_goat` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 004 | plants | `cloud_moss` | `aionbound:cloud_moss` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | resources | `cloud_wool` | `aionbound:cloud_wool` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | blocks | `cloud_wool_block` | `aionbound:cloud_wool_block` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | plants | `cloudpuff_plant` | `aionbound:cloudpuff_plant` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | resources | `float_resin` | `aionbound:float_resin` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | plants | `floating_blossom` | `aionbound:floating_blossom` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | structures | `floating_ruin_floor` | `aionbound:floating_ruin_floor` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | creatures | `gale_hawk` | `aionbound:gale_hawk` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 004 | creatures | `glide_drake` | `aionbound:glide_drake` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 004 | structures | `hanging_lift_frame` | `aionbound:hanging_lift_frame` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | plants | `hanging_sky_vine` | `aionbound:hanging_sky_vine` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | resources | `lift_bloom_item` | `aionbound:lift_bloom_item` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | structures | `nest_platform` | `aionbound:nest_platform` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | plants | `nest_thatch_tuft` | `aionbound:nest_thatch_tuft` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | structures | `observation_tower` | `aionbound:observation_tower` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | blocks | `pale_shelf_stone` | `aionbound:pale_shelf_stone` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | structures | `rope_bridge` | `aionbound:rope_bridge` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | plants | `rope_root` | `aionbound:rope_root` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | blocks | `rope_timber` | `aionbound:rope_timber` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | creatures | `ropewing` | `aionbound:ropewing` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 004 | creatures | `ruin_harpy` | `aionbound:ruin_harpy` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 004 | plants | `shelf_shrub` | `aionbound:shelf_shrub` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | resources | `sky_feather` | `aionbound:sky_feather` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | creatures | `sky_fox` | `aionbound:sky_fox` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 004 | blocks | `sky_moss_block` | `aionbound:sky_moss_block` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | resources | `sky_vine_item` | `aionbound:sky_vine_item` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | plants | `skybloom` | `aionbound:skybloom` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | blocks | `skyreach_log` | `aionbound:skyreach_log` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | blocks | `skyreach_planks` | `aionbound:skyreach_planks` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | blocks | `skyreach_wood` | `aionbound:skyreach_wood` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | creatures | `stone_vulture` | `aionbound:stone_vulture` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 004 | creatures | `storm_gull` | `aionbound:storm_gull` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 004 | resources | `storm_pinion` | `aionbound:storm_pinion` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | resources | `updraft_reed_item` | `aionbound:updraft_reed_item` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | plants | `wind_reed_plant` | `aionbound:wind_reed_plant` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | creatures | `wind_roc` | `aionbound:wind_roc` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 004 | structures | `wind_shrine` | `aionbound:wind_shrine` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | resources | `wind_silk` | `aionbound:wind_silk` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 004 | blocks | `wind_slate` | `aionbound:wind_slate` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_DISPOSITION_REQUIRED_REPAIR_OR_DOCUMENTED_NOT_APPLICABLE |
| 006 | trophies | `ancient_acorn_display` | `aionbound:ancient_acorn_display` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | trophies | `ash_drake_horn` | `aionbound:ash_drake_horn` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | weapons | `ash_repeater` | `aionbound:ash_repeater` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | armor | `ashen_boots` | `aionbound:ashen_boots` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | armor | `ashen_chest` | `aionbound:ashen_chest` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | armor | `ashen_helmet` | `aionbound:ashen_helmet` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | armor | `ashen_legs` | `aionbound:ashen_legs` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | weapons | `basalt_hammer` | `aionbound:basalt_hammer` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | tools | `basalt_pick` | `aionbound:basalt_pick` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | weapons | `briar_cleaver` | `aionbound:briar_cleaver` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | trophies | `briar_elk_trophy` | `aionbound:briar_elk_trophy` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | accessories | `briar_ring` | `aionbound:briar_ring` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | armor | `crystal_circlet` | `aionbound:crystal_circlet` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | trophies | `crystal_obelisk_fragment` | `aionbound:crystal_obelisk_fragment` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | weapons | `crystal_pike` | `aionbound:crystal_pike` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | tools | `crystal_shovel` | `aionbound:crystal_shovel` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | accessories | `crystal_talisman` | `aionbound:crystal_talisman` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | trophies | `ember_forge_core` | `aionbound:ember_forge_core` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | weapons | `ember_great_axe` | `aionbound:ember_great_axe` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | tools | `ember_hammer` | `aionbound:ember_hammer` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | accessories | `ember_totem` | `aionbound:ember_totem` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | armor | `explorer_cloak` | `aionbound:explorer_cloak` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | accessories | `lantern_badge` | `aionbound:lantern_badge` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | tools | `lantern_hook` | `aionbound:lantern_hook` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | accessories | `marsh_idol` | `aionbound:marsh_idol` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | tools | `marsh_sickle` | `aionbound:marsh_sickle` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | trophies | `marsh_wight_mask` | `aionbound:marsh_wight_mask` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | trophies | `moon_pearl_pedestal` | `aionbound:moon_pearl_pedestal` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | accessories | `moon_sap_pendant` | `aionbound:moon_sap_pendant` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | weapons | `moon_sap_staff` | `aionbound:moon_sap_staff` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | accessories | `moss_charm` | `aionbound:moss_charm` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | weapons | `mossfang_spear` | `aionbound:mossfang_spear` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | trophies | `mosskip_trophy` | `aionbound:mosskip_trophy` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | tools | `ore_chisel` | `aionbound:ore_chisel` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | weapons | `prism_bow` | `aionbound:prism_bow` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | accessories | `root_bracelet` | `aionbound:root_bracelet` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | tools | `root_knife` | `aionbound:root_knife` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | accessories | `surveyor_medallion` | `aionbound:surveyor_medallion` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | tools | `surveyor_staff` | `aionbound:surveyor_staff` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | trophies | `thorn_stalker_skull` | `aionbound:thorn_stalker_skull` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | weapons | `thorn_whip` | `aionbound:thorn_whip` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | tools | `trail_compass` | `aionbound:trail_compass` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | trophies | `twinbond_relic` | `aionbound:twinbond_relic` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | accessories | `warden_sigil` | `aionbound:warden_sigil` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | armor | `whisperwood_boots` | `aionbound:whisperwood_boots` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | armor | `whisperwood_chest` | `aionbound:whisperwood_chest` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | tools | `whisperwood_hatchet` | `aionbound:whisperwood_hatchet` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | armor | `whisperwood_helmet` | `aionbound:whisperwood_helmet` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | armor | `whisperwood_legs` | `aionbound:whisperwood_legs` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |
| 006 | weapons | `widow_fang_dagger` | `aionbound:widow_fang_dagger` | NORMALIZATION_OR_REPAIR_REQUIRED | NATIVE_REPAIR_REQUIRED |

## Proof boundary

Static JSON/PNG/path/hash inspection was run. Blockbench GUI open/save/reopen, native codec export, Creator Tools, Stable BDS, Bedrock client, controller, multiplayer, Realm, split-screen, and physical PS4 gates were not run by this lane.

Regenerate with:

```sh
python3 engineering/normalization/tools/inventory_packets.py
```
