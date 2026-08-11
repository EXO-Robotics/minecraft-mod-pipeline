# Ashen Highlands vertical readiness audit

Audit base: `4e75503cc0597ba7e7ffe369a61e6db09212933a` / tree `e4a94c579612030c6f853eac9d214153fb48ef95`.

Status: **ASHEN_VERTICAL_NOT_READY_AUTHORITY_AND_CONSTRUCTION_PENDING**

## Bottom line

No exact Packet002 creature, plant, structure, AI/spawn, worldgen, loot/recipe, Codex/progression/persistence, or Kiln Sky runtime implementation exists at the audit base. The only exact Packet002 BP/RP implementation is the ten flat resource-item registrations/icons and ten ordinary full-cube block registrations/textures.

Thirteen new Ashen Packet006 identities are absent. briar_ring is the existing Whisperwood base and is not Ashen implementation or authority for a heat-tempered sidegrade.

This is a point-in-time source audit. It does not authorize Ashen construction and it does not claim client or BDS proof.

## Counts

| Surface | Current evidence |
|---|---|
| Packet002 exact IDs | 50 |
| Packet002 static product implementation | 10 resources + 10 full-cube blocks |
| Packet002 entity / plant / structure runtime | 0 / 10, 0 / 10, 0 / 10 |
| Packet002 native evidence | 7 representative PASS; 23 repair required; 20 Blockbench N/A |
| Packet006 Ashen runtime | 13 new absent; `briar_ring` is existing WW base only |
| Ashen Codex/progression/persistence | intake maps only |
| Kiln Sky | identity map only; no executable encounter |
| Client / Stable BDS | unproven for Ashen product changes |

## Packet002 per-ID state

| Category | ID | Product state | Native evidence | Authority blockers |
|---|---|---|---|---|
| creatures | `ash_mite` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| creatures | `ember_crow` | SAFE_BUT_UNIMPLEMENTED | PASS_REPRESENTATIVE_NATIVE_REPAIR_GATE | W1-001-AH, W1-004-AH |
| creatures | `magma_lizard` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| creatures | `furnace_beetle` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| creatures | `char_wolf` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| creatures | `cinder_lynx` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| creatures | `ash_ram` | SAFE_BUT_UNIMPLEMENTED | PASS_REPRESENTATIVE_NATIVE_REPAIR_GATE | W1-001-AH, W1-004-AH |
| creatures | `soot_stag` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| creatures | `basalt_tortoise` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| creatures | `ash_drake` | SAFE_BUT_UNIMPLEMENTED | PASS_REPRESENTATIVE_NATIVE_REPAIR_GATE | W1-001-AH, W1-003-KILN-SKY, W1-004-AH |
| resources | `smolder_bark` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| resources | `charbone` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| resources | `sulfur_cluster` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| resources | `volcanic_glass_shard` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| resources | `ember_resin` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| resources | `heatstone` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| resources | `furnace_chitin` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| resources | `basalt_core` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| resources | `ash_crystal` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| resources | `fire_bloom_seed` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| blocks | `ash_log` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| blocks | `char_planks` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| blocks | `ash_soil` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| blocks | `cinder_gravel` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| blocks | `smolder_stone` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| blocks | `basalt_brick` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| blocks | `basalt_pillar` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| blocks | `heat_bark` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| blocks | `ember_moss` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| blocks | `volcanic_glass_block` | IMPLEMENTED_STATIC_PASS | NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM | W1-001-AH, W1-004-AH |
| plants | `cinder_grass` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| plants | `ash_fern` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| plants | `smoke_reed` | SAFE_BUT_UNIMPLEMENTED | PASS_REPRESENTATIVE_NATIVE_REPAIR_GATE | W1-001-AH, W1-004-AH |
| plants | `char_shrub` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| plants | `soot_mushroom` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| plants | `magma_moss` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| plants | `glow_root` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| plants | `basalt_flower` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| plants | `ember_vine` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| plants | `fire_bloom` | SAFE_BUT_UNIMPLEMENTED | PASS_REPRESENTATIVE_NATIVE_REPAIR_GATE | W1-001-AH, W1-004-AH |
| structures | `fire_totem` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| structures | `burned_camp` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| structures | `char_wagon` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| structures | `broken_bridge` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| structures | `basalt_arch` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| structures | `ash_watchtower` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| structures | `ancient_kiln` | SAFE_BUT_UNIMPLEMENTED | PASS_REPRESENTATIVE_NATIVE_REPAIR_GATE | W1-001-AH, W1-004-AH |
| structures | `ember_forge` | SAFE_BUT_UNIMPLEMENTED | PASS_REPRESENTATIVE_NATIVE_REPAIR_GATE | W1-001-AH, W1-004-AH |
| structures | `lava_shrine` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |
| structures | `ash_cave` | SAFE_BUT_UNIMPLEMENTED | NATIVE_REPAIR_REQUIRED | W1-001-AH, W1-004-AH |

## Packet006 Ashen per-ID state

| Category | ID | Product state | Authority blockers |
|---|---|---|---|
| weapons | `basalt_hammer` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-001-AH, W1-004-AH |
| weapons | `ember_great_axe` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-001-AH, W1-004-AH |
| weapons | `ash_repeater` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-001-AH, W1-004-AH |
| armor | `ashen_helmet` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-001-AH, W1-004-AH |
| armor | `ashen_chest` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-001-AH, W1-004-AH |
| armor | `ashen_legs` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-001-AH, W1-004-AH |
| armor | `ashen_boots` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-001-AH, W1-004-AH |
| tools | `basalt_pick` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-001-AH, W1-004-AH |
| tools | `ember_hammer` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-001-AH, W1-004-AH |
| tools | `ore_chisel` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-001-AH, W1-004-AH |
| accessories | `ember_totem` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-001-AH, W1-004-AH |
| accessories | `briar_ring` | EXISTING_WHISPERWOOD_BASE_KEEP_NOT_ASHEN_IMPLEMENTATION | W1-CREATIVE-005 |
| trophies | `ash_drake_horn` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-003-KILN-SKY, W1-004-AH |
| trophies | `ember_forge_core` | SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED | W1-004-AH |

## Minimal continuation order after exact authorization

1. Ratify W1-001-AH, W1-003-KILN-SKY, and W1-004-AH exactly as proposed; preserve W1-CREATIVE-005 deferred.
2. Complete native repair/export evidence for the remaining 23 Packet002 custom assets and all 14 Packet006 source assets; do not replace the existing briar_ring base.
3. Finish the noncombat foundation: block drops/recipes, ten plants and harvesting, regional resources, bounded features, and placement/worldgen using the existing 20 static registrations.
4. Implement the nine non-apex creatures vertically: BP/RP binding, authored motion, role AI, natural spawn/caps, approved loot, discovery, and Codex hooks.
5. Implement all ten structure assemblies and bounded generation, with approved structure loot and encounter identities; keep ember_forge terminal behavior disabled until the Kiln Sky step.
6. Implement derived components, closed recipes, 13 new Packet006 runtime identities, repair/durability/roles, and reuse-only briar_ring linkage.
7. Implement Kiln Sky and ash_drake from the ratified envelope, including multiplayer ownership, reset, durable seal credit, once-per-player physical fulfillment, recovery, repeat-clear, and ember_forge_core non-seal semantics.
8. Append Ashen Codex/progression rows, apply the idempotent registry migration, compose handlers, close persistence/reward guards, then run targeted source/closure tests only; do not add an intermediate BDS gate.

## Proof boundary

Proven:

- exact source state at the pinned commit/tree
- per-ID BP/RP presence or absence for 50 Packet002 and 14 Packet006 Ashen identities
- current static item/block and native-evidence dispositions
- current authority blockers and test-coverage gaps

Not proven:

- future implementation correctness
- runtime AI, world generation, loot economy, progression, persistence, or Kiln Sky behavior
- Bedrock client rendering/audio/UI readability
- Stable BDS admission for Ashen changes
- multiplayer, controller, Realm, split-screen, physical PS4, Marketplace, release, or candidate readiness
