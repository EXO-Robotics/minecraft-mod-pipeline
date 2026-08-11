# Whisperwood Entity Runtime Implementation Map

Status: **IMPLEMENTATION_MAP_NOT_RUNTIME_PROOF**

This is a construction map for Packet 001's ten creatures. It does not edit BP/RP files and does not claim runtime behavior.

## Binding rules

- **Namespace:** aionbound
- **Numeric Policy:** No health, damage, speed, priority, distance, spawn weight, group size, drop chance, or boss threshold is selected here.
- **G7 Reuse Rule:** Reuse only named component families and script responsibilities; G7 numeric values and cast identities do not transfer.
- **Animation Rule:** Generic exported idle/action clips do not satisfy differently named brief-declared role clips.
- **Persistence Rule:** G7 proves player/world encounter journals, not ordinary-creature restart persistence. Entity persistence/despawn semantics require an explicit successor decision.
- **Loot Rule:** Warehouse identities are eligible for wiring; narrative-only drop names remain withheld under W1-CREATIVE-001; probabilities remain withheld under W1-CREATIVE-004.
- **Sound Rule:** Placeholder sounds are allowed only during construction; identity sound assets remain required before Whisperwood Done.

## Per-creature map

### `bark_wraith`

- Approved role: `elite_spectral`; runtime class: `hostile`; apex: `false`
- Movement: spectral phase-drift
- G7 pattern: `no_complete_g7_pattern`
- Creative evidence: `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md:107`
- G7-proven component families: `minecraft:collision_box`, `minecraft:health`, `minecraft:loot`, `minecraft:movement`, `minecraft:movement.basic`, `minecraft:navigation.walk`, `minecraft:physics`, `minecraft:type_family`
- Required but unproven extensions: movement/navigation family for phase drift, target policy, soft-spectral attack delivery
- Spawn dependencies: night, deep forest, totems, very low frequency
- Warehouse drops eligible for wiring: whisper_bark, hollow_amber, moon_sap, ancient_acorn_display
- Narrative-only drops withheld: Wraith Mask Fragment
- Codex trigger: night deep-forest or totem encounter
- Declared clips: `death_collapse`, `drift_walk`, `hurt`, `idle_sway`, `reach_attack`
- Actual clips: `animation.aionforge_ww.bark_wraith.action`, `animation.aionforge_ww.bark_wraith.idle`
- Blockers: `SPECTRAL_MOTION_ARCHITECTURE`, `SPECTRAL_TARGET_POLICY`, `LOOT_IDENTITY_W1_CREATIVE_001`, `PERSISTENCE_SEMANTICS`, `ANIMATION_COVERAGE`, `NATIVE_ASSET_DISPOSITION`

Target creates:

- `behavior_pack/entities/bark_wraith.entity.json`
- `behavior_pack/spawn_rules/bark_wraith.spawn_rules.json`
- `behavior_pack/loot_tables/entities/bark_wraith.json`
- `resource_pack/entity/bark_wraith.entity.json`
- `resource_pack/models/aionbound/whisperwood/bark_wraith.geo.json`
- `resource_pack/animations/aionbound/whisperwood/bark_wraith.animation.json`
- `resource_pack/textures/aionbound/whisperwood/bark_wraith.png`

### `briar_elk`

- Approved role: `elite_grazer_mini_apex`; runtime class: `neutral`; apex: `false`
- Movement: ground stag gait
- G7 pattern: `neutral_retaliatory_ground`
- Creative evidence: `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md:103`
- G7-proven component families: `minecraft:collision_box`, `minecraft:health`, `minecraft:loot`, `minecraft:movement`, `minecraft:movement.basic`, `minecraft:navigation.walk`, `minecraft:physics`, `minecraft:type_family`, `minecraft:attack`, `minecraft:behavior.hurt_by_target`, `minecraft:behavior.melee_attack`, `minecraft:behavior.random_stroll`, `minecraft:behavior.look_at_player`
- Required but unproven extensions: mini-apex initiation policy, heavy-antler presentation tuning
- Spawn dependencies: meadows, rare
- Warehouse drops eligible for wiring: briar_antler, briar_elk_trophy, ancient_acorn
- Narrative-only drops withheld: Thick Hide, Briar Crown
- Codex trigger: hunt or witness meadow rite
- Declared clips: `antler_shake`, `death`, `hurt`, `idle`, `trot`, `walk`
- Actual clips: `animation.aionforge_ww.briar_elk.action`, `animation.aionforge_ww.briar_elk.idle`
- Blockers: `MINI_APEX_TARGET_POLICY`, `LOOT_IDENTITY_W1_CREATIVE_001`, `PERSISTENCE_SEMANTICS`, `ANIMATION_COVERAGE`, `NATIVE_ASSET_DISPOSITION`

Target creates:

- `behavior_pack/entities/briar_elk.entity.json`
- `behavior_pack/spawn_rules/briar_elk.spawn_rules.json`
- `behavior_pack/loot_tables/entities/briar_elk.json`
- `resource_pack/entity/briar_elk.entity.json`
- `resource_pack/models/aionbound/whisperwood/briar_elk.geo.json`
- `resource_pack/animations/aionbound/whisperwood/briar_elk.animation.json`
- `resource_pack/textures/aionbound/whisperwood/briar_elk.png`

### `hollow_widow_spider`

- Approved role: `hostile_elite`; runtime class: `hostile`; apex: `false`
- Movement: ground plus climb
- G7 pattern: `hostile_melee_ground`
- Creative evidence: `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md:106`
- G7-proven component families: `minecraft:collision_box`, `minecraft:health`, `minecraft:loot`, `minecraft:movement`, `minecraft:movement.basic`, `minecraft:navigation.walk`, `minecraft:physics`, `minecraft:type_family`, `minecraft:attack`, `minecraft:behavior.hurt_by_target`, `minecraft:behavior.melee_attack`, `minecraft:behavior.random_stroll`, `minecraft:behavior.look_at_player`, `minecraft:behavior.nearest_attackable_target`
- Required but unproven extensions: minecraft:can_climb, minecraft:navigation.climb, silk attack delivery and status semantics
- Spawn dependencies: caves, giant roots
- Warehouse drops eligible for wiring: widow_silk
- Narrative-only drops withheld: Hollow Venom Sac, Chitin Shard, Widow Eye
- Codex trigger: cave encounter
- Declared clips: `bite`, `death`, `hurt`, `idle`, `rear_threat`, `walk_skitter`
- Actual clips: `animation.aionforge_ww.hollow_widow_spider.action`, `animation.aionforge_ww.hollow_widow_spider.idle`
- Blockers: `CLIMB_RUNTIME_PATTERN_NOT_IN_G7`, `SILK_COMBAT_BINDING`, `LOOT_IDENTITY_W1_CREATIVE_001`, `PERSISTENCE_SEMANTICS`, `ANIMATION_COVERAGE`, `NATIVE_ASSET_DISPOSITION`

Target creates:

- `behavior_pack/entities/hollow_widow_spider.entity.json`
- `behavior_pack/spawn_rules/hollow_widow_spider.spawn_rules.json`
- `behavior_pack/loot_tables/entities/hollow_widow_spider.json`
- `resource_pack/entity/hollow_widow_spider.entity.json`
- `resource_pack/models/aionbound/whisperwood/hollow_widow_spider.geo.json`
- `resource_pack/animations/aionbound/whisperwood/hollow_widow_spider.animation.json`
- `resource_pack/textures/aionbound/whisperwood/hollow_widow_spider.png`

### `lantern_hare`

- Approved role: `ambient_curiosity`; runtime class: `ambient`; apex: `false`
- Movement: ground quick-hop
- G7 pattern: `ambient_ground`
- Creative evidence: `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md:101`
- G7-proven component families: `minecraft:collision_box`, `minecraft:health`, `minecraft:loot`, `minecraft:movement`, `minecraft:movement.basic`, `minecraft:navigation.walk`, `minecraft:physics`, `minecraft:type_family`, `minecraft:behavior.random_stroll`, `minecraft:behavior.look_at_player`
- Required but unproven extensions: flee behavior family and target filters, night glow presentation
- Spawn dependencies: night, near lantern_bloom, near lantern_post
- Warehouse drops eligible for wiring: lantern_fur
- Narrative-only drops withheld: Glow Soft Pellet, Hare's Lucky Foot
- Codex trigger: night observation near blooms
- Declared clips: `alert`, `death`, `hop`, `hurt`, `idle_ear_flick`
- Actual clips: `animation.aionforge_ww.lantern_hare.action`, `animation.aionforge_ww.lantern_hare.idle`
- Blockers: `FLEE_TARGET_POLICY`, `LOOT_IDENTITY_W1_CREATIVE_001`, `PERSISTENCE_SEMANTICS`, `ANIMATION_COVERAGE`, `NATIVE_ASSET_DISPOSITION`

Target creates:

- `behavior_pack/entities/lantern_hare.entity.json`
- `behavior_pack/spawn_rules/lantern_hare.spawn_rules.json`
- `behavior_pack/loot_tables/entities/lantern_hare.json`
- `resource_pack/entity/lantern_hare.entity.json`
- `resource_pack/models/aionbound/whisperwood/lantern_hare.geo.json`
- `resource_pack/animations/aionbound/whisperwood/lantern_hare.animation.json`
- `resource_pack/textures/aionbound/whisperwood/lantern_hare.png`

### `mosskip_buck`

- Approved role: `neutral_territorial`; runtime class: `neutral`; apex: `false`
- Movement: ground bound-hop/charge
- G7 pattern: `neutral_retaliatory_ground`
- Creative evidence: `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md:100`
- G7-proven component families: `minecraft:collision_box`, `minecraft:health`, `minecraft:loot`, `minecraft:movement`, `minecraft:movement.basic`, `minecraft:navigation.walk`, `minecraft:physics`, `minecraft:type_family`, `minecraft:attack`, `minecraft:behavior.hurt_by_target`, `minecraft:behavior.melee_attack`, `minecraft:behavior.random_stroll`, `minecraft:behavior.look_at_player`
- Required but unproven extensions: herd relationship and defense target acquisition, charge presentation tuning
- Spawn dependencies: near mosskip herd
- Warehouse drops eligible for wiring: moss_resin, whisper_bark, mosskip_trophy
- Narrative-only drops withheld: Hardened Moss Plate, Mosskip Crown Fragment
- Codex trigger: defeat or rare peaceful study
- Declared clips: `death`, `hop_bound`, `hurt`, `idle_graze`, `look`, `walk`
- Actual clips: `animation.aionforge_ww.mosskip_buck.action`, `animation.aionforge_ww.mosskip_buck.idle`
- Blockers: `HERD_DEFENSE_BINDING`, `LOOT_IDENTITY_W1_CREATIVE_001`, `PERSISTENCE_SEMANTICS`, `ANIMATION_COVERAGE`, `NATIVE_ASSET_DISPOSITION`

Target creates:

- `behavior_pack/entities/mosskip_buck.entity.json`
- `behavior_pack/spawn_rules/mosskip_buck.spawn_rules.json`
- `behavior_pack/loot_tables/entities/mosskip_buck.json`
- `resource_pack/entity/mosskip_buck.entity.json`
- `resource_pack/models/aionbound/whisperwood/mosskip_buck.geo.json`
- `resource_pack/animations/aionbound/whisperwood/mosskip_buck.animation.json`
- `resource_pack/textures/aionbound/whisperwood/mosskip_buck.png`

### `mosskip_doe`

- Approved role: `ambient_adult`; runtime class: `ambient`; apex: `false`
- Movement: ground bound-hop
- G7 pattern: `ambient_ground`
- Creative evidence: `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md:99`
- G7-proven component families: `minecraft:collision_box`, `minecraft:health`, `minecraft:loot`, `minecraft:movement`, `minecraft:movement.basic`, `minecraft:navigation.walk`, `minecraft:physics`, `minecraft:type_family`, `minecraft:behavior.random_stroll`, `minecraft:behavior.look_at_player`
- Required but unproven extensions: flee behavior family and target filters, calf relationship and conditional defense
- Spawn dependencies: herds, trails
- Warehouse drops eligible for wiring: moss_resin
- Narrative-only drops withheld: Lantern-adjacent soft hide scrap, Mosskip Antler Bud
- Codex trigger: observe or gentle approach
- Declared clips: `death`, `hop_bound`, `hurt`, `idle_graze`, `look`, `walk`
- Actual clips: `animation.aionforge_ww.mosskip_doe.action`, `animation.aionforge_ww.mosskip_doe.idle`
- Blockers: `FLEE_TARGET_POLICY`, `HERD_DEFENSE_BINDING`, `PERSISTENCE_SEMANTICS`, `ANIMATION_COVERAGE`, `NATIVE_ASSET_DISPOSITION`

Target creates:

- `behavior_pack/entities/mosskip_doe.entity.json`
- `behavior_pack/spawn_rules/mosskip_doe.spawn_rules.json`
- `behavior_pack/loot_tables/entities/mosskip_doe.json`
- `resource_pack/entity/mosskip_doe.entity.json`
- `resource_pack/models/aionbound/whisperwood/mosskip_doe.geo.json`
- `resource_pack/animations/aionbound/whisperwood/mosskip_doe.animation.json`
- `resource_pack/textures/aionbound/whisperwood/mosskip_doe.png`

### `mosskip_fawn`

- Approved role: `ambient_young`; runtime class: `ambient`; apex: `false`
- Movement: ground bound-hop
- G7 pattern: `ambient_ground`
- Creative evidence: `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md:98`
- G7-proven component families: `minecraft:collision_box`, `minecraft:health`, `minecraft:loot`, `minecraft:movement`, `minecraft:movement.basic`, `minecraft:navigation.walk`, `minecraft:physics`, `minecraft:type_family`, `minecraft:behavior.random_stroll`, `minecraft:behavior.look_at_player`
- Required but unproven extensions: flee behavior family and target filters
- Spawn dependencies: clearings, near mosskip_doe
- Warehouse drops eligible for wiring: moss_resin, star_grass
- Narrative-only drops withheld: Mosskip Tuft
- Codex trigger: observe in sun-flecked clearings
- Declared clips: `death`, `hop`, `hurt`, `idle`, `skitter`
- Actual clips: `animation.aionforge_ww.mosskip_fawn.action`, `animation.aionforge_ww.mosskip_fawn.idle`
- Blockers: `FLEE_TARGET_POLICY`, `PERSISTENCE_SEMANTICS`, `ANIMATION_COVERAGE`, `NATIVE_ASSET_DISPOSITION`

Target creates:

- `behavior_pack/entities/mosskip_fawn.entity.json`
- `behavior_pack/spawn_rules/mosskip_fawn.spawn_rules.json`
- `behavior_pack/loot_tables/entities/mosskip_fawn.json`
- `resource_pack/entity/mosskip_fawn.entity.json`
- `resource_pack/models/aionbound/whisperwood/mosskip_fawn.geo.json`
- `resource_pack/animations/aionbound/whisperwood/mosskip_fawn.animation.json`
- `resource_pack/textures/aionbound/whisperwood/mosskip_fawn.png`

### `rootback_boar`

- Approved role: `neutral_provoked`; runtime class: `neutral`; apex: `false`
- Movement: ground trundle/charge
- G7 pattern: `neutral_retaliatory_ground`
- Creative evidence: `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md:102`
- G7-proven component families: `minecraft:collision_box`, `minecraft:health`, `minecraft:loot`, `minecraft:movement`, `minecraft:movement.basic`, `minecraft:navigation.walk`, `minecraft:physics`, `minecraft:type_family`, `minecraft:attack`, `minecraft:behavior.hurt_by_target`, `minecraft:behavior.melee_attack`, `minecraft:behavior.random_stroll`, `minecraft:behavior.look_at_player`
- Required but unproven extensions: charge presentation tuning
- Spawn dependencies: understory
- Warehouse drops eligible for wiring: whisper_bark, root_heart
- Narrative-only drops withheld: Boar Tusk Shard, Root Plate
- Codex trigger: defeat when provoked
- Declared clips: `charge_snort`, `death`, `hurt`, `idle`, `walk_trundle`
- Actual clips: `animation.aionforge_ww.rootback_boar.action`, `animation.aionforge_ww.rootback_boar.idle`
- Blockers: `LOOT_IDENTITY_W1_CREATIVE_001`, `PERSISTENCE_SEMANTICS`, `ANIMATION_COVERAGE`, `NATIVE_ASSET_DISPOSITION`

Target creates:

- `behavior_pack/entities/rootback_boar.entity.json`
- `behavior_pack/spawn_rules/rootback_boar.spawn_rules.json`
- `behavior_pack/loot_tables/entities/rootback_boar.json`
- `resource_pack/entity/rootback_boar.entity.json`
- `resource_pack/models/aionbound/whisperwood/rootback_boar.geo.json`
- `resource_pack/animations/aionbound/whisperwood/rootback_boar.animation.json`
- `resource_pack/textures/aionbound/whisperwood/rootback_boar.png`

### `rot_wolf`

- Approved role: `hostile_pack`; runtime class: `hostile`; apex: `false`
- Movement: ground pack-run
- G7 pattern: `hostile_melee_ground`
- Creative evidence: `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md:104`
- G7-proven component families: `minecraft:collision_box`, `minecraft:health`, `minecraft:loot`, `minecraft:movement`, `minecraft:movement.basic`, `minecraft:navigation.walk`, `minecraft:physics`, `minecraft:type_family`, `minecraft:attack`, `minecraft:behavior.hurt_by_target`, `minecraft:behavior.melee_attack`, `minecraft:behavior.random_stroll`, `minecraft:behavior.look_at_player`, `minecraft:behavior.nearest_attackable_target`
- Required but unproven extensions: bounded pack coordination and pack cap
- Spawn dependencies: night, deep trails, pack grouping
- Warehouse drops eligible for wiring: none
- Narrative-only drops withheld: Rot Fang, Tainted Pelt, Marrow Scrap, Pack Alpha Mark
- Codex trigger: survive a pack
- Declared clips: `death`, `hurt`, `idle`, `run`, `snarl_attack`, `walk`
- Actual clips: `animation.aionforge_ww.rot_wolf.action`, `animation.aionforge_ww.rot_wolf.idle`
- Blockers: `PACK_COORDINATION_BINDING`, `LOOT_IDENTITY_W1_CREATIVE_001`, `PERSISTENCE_SEMANTICS`, `ANIMATION_COVERAGE`, `NATIVE_ASSET_DISPOSITION`

Target creates:

- `behavior_pack/entities/rot_wolf.entity.json`
- `behavior_pack/spawn_rules/rot_wolf.spawn_rules.json`
- `behavior_pack/loot_tables/entities/rot_wolf.json`
- `resource_pack/entity/rot_wolf.entity.json`
- `resource_pack/models/aionbound/whisperwood/rot_wolf.geo.json`
- `resource_pack/animations/aionbound/whisperwood/rot_wolf.animation.json`
- `resource_pack/textures/aionbound/whisperwood/rot_wolf.png`

### `thorn_stalker`

- Approved role: `hostile_elite_chapter_apex`; runtime class: `boss`; apex: `true`
- Movement: ground stalk/lunge
- G7 pattern: `hostile_melee_ground_plus_encounter_shell`
- Creative evidence: `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md:105`, `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md:111`
- G7-proven component families: `minecraft:collision_box`, `minecraft:health`, `minecraft:loot`, `minecraft:movement`, `minecraft:movement.basic`, `minecraft:navigation.walk`, `minecraft:physics`, `minecraft:type_family`, `minecraft:attack`, `minecraft:behavior.hurt_by_target`, `minecraft:behavior.melee_attack`, `minecraft:behavior.random_stroll`, `minecraft:behavior.look_at_player`, `minecraft:behavior.nearest_attackable_target`
- Required but unproven extensions: phase state machine, telegraphed projectile and area attacks, bounded add summons, reset and terminal reward semantics
- Spawn dependencies: deep briar elite ecology, Thorn Court arena encounter
- Warehouse drops eligible for wiring: briar_vine, thorn_stalker_skull
- Narrative-only drops withheld: Thorn Barb, Stalker Claw
- Codex trigger: defeat elite or Thorn Court apex
- Declared clips: `attack_slash`, `death`, `hurt`, `idle_crouch`, `pounce_pose`, `stalk_walk`
- Actual clips: `animation.aionforge_ww.thorn_stalker.action`, `animation.aionforge_ww.thorn_stalker.idle`
- Blockers: `BOSS_ENVELOPE_W1_CREATIVE_003`, `LOOT_IDENTITY_W1_CREATIVE_001`, `LOOT_RANGES_W1_CREATIVE_004`, `PERSISTENCE_SEMANTICS`, `ANIMATION_COVERAGE`, `NATIVE_ASSET_DISPOSITION`

Target creates:

- `behavior_pack/entities/thorn_stalker.entity.json`
- `behavior_pack/spawn_rules/thorn_stalker.spawn_rules.json`
- `behavior_pack/loot_tables/entities/thorn_stalker.json`
- `resource_pack/entity/thorn_stalker.entity.json`
- `resource_pack/models/aionbound/whisperwood/thorn_stalker.geo.json`
- `resource_pack/animations/aionbound/whisperwood/thorn_stalker.animation.json`
- `resource_pack/textures/aionbound/whisperwood/thorn_stalker.png`

## G7 evidence

- `ambient_ground`: `behavior_pack/entities/mosskip.entity.json` (`2692e88b6b9e73c67da50b1bcdc6d96620dea98e10b96b8f670ea6efee0c50a2`), `behavior_pack/entities/lanternback.entity.json` (`d3410654b8d3b1549e8f9c5432750ddd83877bd05b9fbaa07141489b5adfd119`)
- `neutral_retaliatory_ground`: `behavior_pack/entities/pebblehorn.entity.json` (`8c4302756ad2be49ab7d3a5668d99559469d1d01c141b3dd6eb62dd6b3caaa84`), `behavior_pack/entities/galestrider.entity.json` (`7f3709ef902186138c3470977d2a749bfd8cad561fa59b2e24e405ac898dbfff`)
- `hostile_melee_ground`: `behavior_pack/entities/cinder_brood_hatchling.entity.json` (`3c82a047a489a47d383313a17935bcb73075578487f4ee476640d274f33b2759`), `behavior_pack/entities/basalt_behemoth.entity.json` (`7418ca5bbcb03fcb027fbeea863392a18f5b3cdc4bb77de9b1b9be28db06b437`)
- `hostile_melee_ground_plus_encounter_shell`: `behavior_pack/entities/ash_sovereign_wyrm.entity.json` (`fd55521297173234fc4fde18a78e49b9f03216f721ec31a693ca9f2787cfdd4e`), `behavior_pack/scripts/encounters.js` (`4a0f9d384ca0db89496f8920495174012666ecc464dcf89e0bfc7cf0a2442559`), `behavior_pack/scripts/state.js` (`d40710101a34dc30f858ebde9f65c120cf698e1eb88c2b98511b35946a4cfa12`)
- `no_complete_g7_pattern`: no complete pattern

## Global blockers

- W1-CREATIVE-001 non-warehouse drop identities
- W1-CREATIVE-003 Thorn Court numeric/reset/multiplayer/persistence/reward envelope
- W1-CREATIVE-004 loot probability and quantity ranges
- All ten assets lack brief-declared animation clips in current exports
- All ten editable bbmodels require native locator/path round-trip disposition
- Ordinary-creature restart persistence conflicts with unspecified despawn/cap semantics

## Proof boundary

This map proves only: authority-bound role map; target-file map; G7 component-family provenance; declared-versus-actual animation gap inventory; explicit implementation blockers.

It does **not** prove: schema validity of future pack files; asset native round-trip; animation quality; entity movement; AI behavior; spawn ecology; loot economy; persistence; BDS; client; console; multiplayer; release.
