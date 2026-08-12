# Whisperwood Structure Runtime Implementation Map

Base: `c4d77b6` · Scope: Packet 001 ten structure and prop IDs · Status: historical planning authority with current static reconciliation.

## Boundary

- No pack files, structure bytes, layouts, loot probabilities, boss values, Blockbench evidence, BDS evidence, or candidate claims are produced by this map.
- Packet geometry is an approved visual input, not proof of an authored Minecraft encounter assembly.
- G7 structure code and templates are reusable engineering patterns, not approved Whisperwood layouts or reward identities.
- Current reconciliation proves only committed source-file presence and hash closure; it does not prove Bedrock load, generation, interaction, loot delivery, client presentation, or Checkpoint 1.
- Historical planning blockers remain recorded as base-commit evidence and are not current withholding claims.

## Disposition summary

- 2 direct custom-geometry prop placements: `lantern_post`, `moss_cairn`.
- 3 authored assembly POIs: `hunter_camp`, `broken_wagon`, `root_bridge`.
- 5 landmark encounters: `owl_shrine`, `forest_waystone`, `hollow_cave_entrance`, `ancient_totem`, `fallen_giant_tree`.
- At the historical base, 8 `.mcstructure` targets were absent; the two direct props intentionally did not require encounter assemblies.
- Current source reconciliation: 10 of 10 IDs have hash-bound source footprints, including 8 of 8 structure assemblies.
- Whisperwood identity authority is `WW_AH_AND_CM_RATIFIED_SKY_AND_FINALE_DEFERRED`; chapter-one loot authority is `WHISPERWOOD_ASHEN_AND_CRYSTAL_RATIFIED_SKY_AND_FINALE_DEFERRED`.
- These current facts supersede withholding language as an implementation status, but do not establish BDS or client proof.

## Per-ID map

| ID | Class | Historical generation / encounter target | Historical loot or activation target | Historical missing target | Current source status | Historical blockers |
|---|---|---|---|---|---|---|
| `lantern_post` | CUSTOM_GEOMETRY_BLOCK_PROP | `behavior_pack/features/lantern_post.feature.json` + `behavior_pack/feature_rules/lantern_post.feature_rule.json` | `behavior_pack/loot_tables/blocks/lantern_post.json` | `N/A — direct prop` | `INTEGRATED_SOURCE_BYTES_PRESENT_STATIC_ONLY` | `NATIVE_ASSET_DISPOSITION`, `DECLARED_PROP_ANIMATION_NOT_YET_SHIPPING`, `W1-CREATIVE-004_FINAL_LOOT_VALUES`, `W1-CREATIVE-001_UNRESOLVED_LOOT_OR_COMPONENT_IDENTITY` |
| `moss_cairn` | CUSTOM_GEOMETRY_BLOCK_PROP | `behavior_pack/features/moss_cairn.feature.json` + `behavior_pack/feature_rules/moss_cairn.feature_rule.json` | `behavior_pack/loot_tables/blocks/moss_cairn.json` | `N/A — direct prop` | `INTEGRATED_SOURCE_BYTES_PRESENT_STATIC_ONLY` | `NATIVE_ASSET_DISPOSITION`, `W1-CREATIVE-004_FINAL_LOOT_VALUES`, `W1-CREATIVE-001_UNRESOLVED_LOOT_OR_COMPONENT_IDENTITY` |
| `hunter_camp` | AUTHORED_MCSTRUCTURE_ASSEMBLY | `behavior_pack/features/hunter_camp.structure_feature.json` + `behavior_pack/feature_rules/hunter_camp.structure_feature_rule.json` | `behavior_pack/loot_tables/chests/whisperwood/hunter_camp.json` | `behavior_pack/structures/aionbound/hunter_camp.mcstructure` | `INTEGRATED_SOURCE_BYTES_PRESENT_STATIC_ONLY` | `NATIVE_ASSET_DISPOSITION`, `AUTHORED_STRUCTURE_BYTES_ABSENT`, `W1-CREATIVE-004_FINAL_LOOT_VALUES`, `W1-CREATIVE-001_UNRESOLVED_LOOT_OR_COMPONENT_IDENTITY` |
| `broken_wagon` | AUTHORED_MCSTRUCTURE_ASSEMBLY | `behavior_pack/features/broken_wagon.structure_feature.json` + `behavior_pack/feature_rules/broken_wagon.structure_feature_rule.json` | `behavior_pack/loot_tables/chests/whisperwood/broken_wagon.json` | `behavior_pack/structures/aionbound/broken_wagon.mcstructure` | `INTEGRATED_SOURCE_BYTES_PRESENT_STATIC_ONLY` | `NATIVE_ASSET_DISPOSITION`, `AUTHORED_STRUCTURE_BYTES_ABSENT`, `W1-CREATIVE-004_FINAL_LOOT_VALUES`, `W1-CREATIVE-001_UNRESOLVED_LOOT_OR_COMPONENT_IDENTITY` |
| `root_bridge` | AUTHORED_MCSTRUCTURE_ASSEMBLY | `behavior_pack/features/root_bridge.structure_feature.json` + `behavior_pack/feature_rules/root_bridge.structure_feature_rule.json` | `behavior_pack/loot_tables/chests/whisperwood/root_bridge.json` | `behavior_pack/structures/aionbound/root_bridge.mcstructure` | `INTEGRATED_SOURCE_BYTES_PRESENT_STATIC_ONLY` | `NATIVE_ASSET_DISPOSITION`, `AUTHORED_STRUCTURE_BYTES_ABSENT`, `W1-CREATIVE-004_FINAL_LOOT_VALUES` |
| `owl_shrine` | LANDMARK_ENCOUNTER | `behavior_pack/features/owl_shrine.structure_feature.json` + `behavior_pack/feature_rules/owl_shrine.structure_feature_rule.json` | `behavior_pack/loot_tables/chests/whisperwood/owl_shrine.json` | `behavior_pack/structures/aionbound/owl_shrine.mcstructure` | `INTEGRATED_SOURCE_BYTES_PRESENT_STATIC_ONLY` | `NATIVE_ASSET_DISPOSITION`, `AUTHORED_STRUCTURE_BYTES_ABSENT`, `DECLARED_PROP_ANIMATION_NOT_YET_SHIPPING`, `W1-CREATIVE-004_FINAL_LOOT_VALUES`, `W1-CREATIVE-001_UNRESOLVED_LOOT_OR_COMPONENT_IDENTITY` |
| `forest_waystone` | LANDMARK_ENCOUNTER | `behavior_pack/features/forest_waystone.structure_feature.json` + `behavior_pack/feature_rules/forest_waystone.structure_feature_rule.json` | `behavior_pack/scripts/structures.js` | `behavior_pack/structures/aionbound/forest_waystone.mcstructure` | `INTEGRATED_SOURCE_BYTES_PRESENT_STATIC_ONLY` | `NATIVE_ASSET_DISPOSITION`, `AUTHORED_STRUCTURE_BYTES_ABSENT`, `DECLARED_PROP_ANIMATION_NOT_YET_SHIPPING`, `W1-CREATIVE-004_FINAL_LOOT_VALUES`, `W1-CREATIVE-001_UNRESOLVED_LOOT_OR_COMPONENT_IDENTITY`, `RUNTIME_INTERACTION_OR_ENCOUNTER_SEMANTICS_NOT_YET_IMPLEMENTED` |
| `hollow_cave_entrance` | LANDMARK_ENCOUNTER | `behavior_pack/features/hollow_cave_entrance.structure_feature.json` + `behavior_pack/feature_rules/hollow_cave_entrance.structure_feature_rule.json` | `behavior_pack/loot_tables/chests/whisperwood/hollow_cave_entrance.json` | `behavior_pack/structures/aionbound/hollow_cave_entrance.mcstructure` | `INTEGRATED_SOURCE_BYTES_PRESENT_STATIC_ONLY` | `NATIVE_ASSET_DISPOSITION`, `AUTHORED_STRUCTURE_BYTES_ABSENT`, `W1-CREATIVE-004_FINAL_LOOT_VALUES`, `RUNTIME_INTERACTION_OR_ENCOUNTER_SEMANTICS_NOT_YET_IMPLEMENTED` |
| `ancient_totem` | LANDMARK_ENCOUNTER | `behavior_pack/features/ancient_totem.structure_feature.json` + `behavior_pack/feature_rules/ancient_totem.structure_feature_rule.json` | `behavior_pack/loot_tables/chests/whisperwood/ancient_totem.json` | `behavior_pack/structures/aionbound/ancient_totem.mcstructure` | `INTEGRATED_SOURCE_BYTES_PRESENT_STATIC_ONLY` | `NATIVE_ASSET_DISPOSITION`, `AUTHORED_STRUCTURE_BYTES_ABSENT`, `DECLARED_PROP_ANIMATION_NOT_YET_SHIPPING`, `W1-CREATIVE-004_FINAL_LOOT_VALUES`, `W1-CREATIVE-001_UNRESOLVED_LOOT_OR_COMPONENT_IDENTITY`, `RUNTIME_INTERACTION_OR_ENCOUNTER_SEMANTICS_NOT_YET_IMPLEMENTED` |
| `fallen_giant_tree` | LANDMARK_ENCOUNTER | `behavior_pack/features/fallen_giant_tree.structure_feature.json` + `behavior_pack/feature_rules/fallen_giant_tree.structure_feature_rule.json` | `behavior_pack/loot_tables/chests/whisperwood/fallen_giant_tree.json` | `behavior_pack/structures/aionbound/fallen_giant_tree.mcstructure` | `INTEGRATED_SOURCE_BYTES_PRESENT_STATIC_ONLY` | `NATIVE_ASSET_DISPOSITION`, `AUTHORED_STRUCTURE_BYTES_ABSENT`, `W1-CREATIVE-004_FINAL_LOOT_VALUES`, `W1-CREATIVE-001_UNRESOLVED_LOOT_OR_COMPONENT_IDENTITY`, `RUNTIME_INTERACTION_OR_ENCOUNTER_SEMANTICS_NOT_YET_IMPLEMENTED` |

## Reusable G7 engineering evidence

- KEEP: minecraft:structure_template_feature registration shape
- KEEP: feature-rule identifier and filename closure convention
- KEEP: bounded signature-based discovery and per-player claim guard
- KEEP: persistent landmark stamps and capped per-player site history
- KEEP: deterministic little-endian NBT writer as an authoring mechanism
- REFINE: Use Whisperwood-specific placement predicates; generic overworld non-ocean filters do not satisfy trail, ravine, face, high-ground, deep-core, or expanse semantics.
- REFINE: Use approved structure-specific rewards; G7 pool rewards cannot be relabeled as Whisperwood loot.
- REFINE: Author each assembly from approved Whisperwood blocks and props; G7 generic platform layouts are pattern evidence only.

## Historical implementation sequence (retained)

1. Promote each packet prop only after its native/static geometry disposition, texture path, animation declarations, and locator bindings close.
2. Implement `lantern_post` and `moss_cairn` as individually placeable custom-geometry blocks with direct feature rules; do not invent surrounding layouts.
3. Author the eight listed `.mcstructure` assemblies using approved Packet 001 blocks and promoted prop anchors. The packet prop model cannot substitute for those bytes.
4. Bind structure-specific biome/terrain predicates for trail, road, ravine, high ground, expanse, face, deep core, and wonder placement. Do not copy G7's generic overworld filter.
5. Wire qualitative loot identities and Codex stamps now, but leave numeric rolls/quantities and unresolved non-warehouse item IDs fail-closed until their ledger tickets close.
6. Run targeted JSON, identifier, structure-reference, loot-reference, and persistence tests before the bounded Whisperwood package smoke.

## Authority hashes

- `aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5`  `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json`
- `3116c217e06afe1fd0cd56ee742c537f948a4c91193ec831fd1b3ec362837bfc`  `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md`
- `9e62ae9ba6c1da33b64ff0bfa4ac4799b083c6de995585424864d5cf2b0cb076`  `program/crazycraft-pack-production-v1/studio-prep/creative/05_structures/STRUCTURES_DESIGN.md`
- `bc18a1e1f73d6045ab7e583afe910ca13d4776d439c8f3dfb45dae5784372f4b`  `program/crazycraft-pack-production-v1/studio-prep/creative/06_world_gen/WORLD_GENERATION.md`
- `c6846ecfcf51c1bdbe62b3ef81f37e7e86e6466a62b46f72cb3685516a216f24`  `program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_WHISPERWOOD.md`
- `b791c4b63d6ef09c2ac437fdc67065735a2363becad92b359cecb0a4e25c5172`  `engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json`
