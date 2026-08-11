# Whisperwood readiness audit v2

Audited integration commit: `1d424aed1182e910eb82a143bd3c2c947ac226ed`

Result: **VERTICAL_IMPLEMENTATION_PARTIAL — CHECKPOINT 1 NOT AUTHORIZED**

The integration is materially beyond the earlier pre-loot prefix. All 50 Packet 001 identities close in source; all 21 Whisperwood-facing Packet 006 base IDs now have shipping icons and runtime registrations; the three formerly unplaced plants have conservative natural placement; all ten creatures have role-specific AI/motion source and early vanilla placeholder audio; and the forest waystone plus broken wagon now record duplicate-safe persistent landmarks. Those gains do not yet complete the command-free Wave A journey.

## Contract reassessment

| Contract criterion | Classification | Evidence-derived finding |
|---|---|---|
| First living biome fully playable offline | `MISSING_IMPLEMENTATION` | Loot/acquisition, the WW crafting economy, the Thorn Court, shrine alternative, return-travel behavior, and AH-rumor presentation remain incomplete. Offline play is unrun. |
| All Packet 001 IDs in world | `PASS_SOURCE_REGISTRATION` | Ten creatures, resources, plants, blocks, and props each close in source. All ten plants now have placement paths. Actual Bedrock load and command-free discoverability remain unproven. |
| WW craft loop | `MISSING_IMPLEMENTATION` | Only four timber recipes exist. The resource/component/equipment recipe graph and legal acquisition paths are absent. |
| Hunter camp + waystone + cave | `PARTIAL_SOURCE` | Templates and generation rules close statically. The waystone has a signature-scoped persistent activation stamp, but return travel and structure loot are absent; terrain/discovery behavior is unproven. |
| Thorn apex runnable | `WITHHELD_UNRATIFIED_AUTHORITY` | Thorn Stalker remains a hostile shell. `W1-003-THORN-COURT` and `W1-004-WW-CH1` are proposed but not ratified. |
| Drops feed WW crafts | `WITHHELD_UNRATIFIED_AUTHORITY` | None of the ten WW entities binds a loot table, and no WW structure chest table exists. `W1-001-WW` and `W1-004-WW-CH1` are proposed but nonbinding. |
| Non-statue ambient | `PASS_SOURCE` | Role-specific roam, panic/react, pursuit, climb/flight, and pack-oriented components plus authored animation sets close statically. Live movement remains a Checkpoint 1 observation. |
| Spawn → explore WW without commands | `UNPROVEN_CLIENT_OR_BDS` | Spawn/worldgen source exists, but the full loop is incomplete and no authorized Checkpoint 1 run has occurred. |
| Craft spear or armor piece | `MISSING_ACQUISITION` | Spear and four armor items exist with runtime identity; no player-legal recipe/reward path exists. |
| Find structure | `UNPROVEN_CLIENT_OR_BDS` | Eight structure templates and two direct-prop paths close statically; discoverability and terrain fit are unrun. |
| Defeat stalker or complete shrine path | `WITHHELD_UNRATIFIED_AUTHORITY` | Thorn Court phase/reward semantics and the alternate shrine rite/reward are absent. |
| Activate waystone | `PARTIAL_SOURCE` | Activation is signature-scoped, persisted, and duplicate-safe. Return-network behavior and player-facing presentation are absent. |
| Obtain AH rumor | `MISSING_PRESENTATION` | Broken Wagon records `landmark:broken_wagon` and the `ww_to_ah` hook, but intentionally grants no rumor/map item, text, or Ashen unlock. |

## Improvements since the stale audit

- Registered conservative placements for `star_grass`, `pale_reed`, and `ember_thistle`; aggregate attempt density remains below the existing ceiling.
- Integrated 21 exact WW-facing Packet 006 base IDs: 5 weapons, 4 armor pieces, 3 tools, 5 accessories, and 4 placeable trophies.
- Bound 21 distinct 32×32 shipping inventory icons and native model/animation evidence without using model UV sheets as icons.
- Added bounded gameplay roles for the equipment base IDs while withholding unapproved sidegrades, rewards, loot, and acquisition.
- Added persistent duplicate-safe `forest_waystone` and `broken_wagon` landmark routing without event cancellation, reward invention, or chat spam.
- Added early placeholder ambient/hurt/death mappings for all ten WW creatures. No custom audio bytes or final sound-identity claim were introduced.

## Source evidence

- `tools/validate_wave1.py`: **PASS**, 979 pack-source files, source SHA-256 `6bd6c983118187eb7533a3a9be4257d3351ac37e09644aaae71eb319f75108a5`.
- Combined runtime/Codex/equipment/progression Node suite: **47 pass, 0 fail**.
- Twenty-four bounded Python/static commands passed, including equipment A/B, icons, plants, ecology, structures, Codex, audio, importer, native evidence, validator units, and proposal-shape tests.
- One legacy evidence-map test command failed with six setup errors. `engineering/whisperwood-intake/entity-runtime/build_entity_runtime_map.py` resolves Creative authority to `/Users/blakegrove/Desktop/bedrock-server/crazycraft-pack-production-v1/...` instead of `/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/...`; therefore `engineering/whisperwood-intake/entity-runtime/test_entity_runtime_map.py` is not relocatable in this isolated worktree.

The failing mapper is a source-evidence defect, not gameplay proof and not permission to modify this audit's BP/RP/runtime scope. It must be repaired and rerun before Checkpoint 1 source closure.

## Exact remaining blockers before Checkpoint 1

1. Ratify only the minimum Whisperwood proposal tranches: `W1-001-WW`, `W1-003-THORN-COURT`, and `W1-004-WW-CH1`, then bind them into replacement machine-readable engineering authority. `W1-CREATIVE-005` remains deferrable for cross-region sidegrades.
2. Implement legal acquisition for all ten WW resources and the 21 WW-facing equipment/trophy IDs; add the approved derived components, recipes, repair relationships, and no-dead-end closure.
3. Implement approved creature and structure loot, rarity ranges, structure chest value, trophy/seal guards, and per-player durable reward semantics.
4. Implement Thorn Court phases, timing, reset/leash, participant ownership/scaling, persistence, and idempotent terminal rewards; implement the approved Owl Shrine alternative.
5. Complete forest-waystone return behavior and the Broken Wagon AH-rumor/map presentation without inventing an unapproved item or unlock.
6. Implement and test Whisperwood sapling regrowth. Existing sapling block/world placement is not renewable tree growth.
7. Repair the isolated-worktree authority resolution in the entity-runtime evidence mapper and rerun its six tests.
8. Rerun targeted source closure. Only then spend the single bounded Checkpoint 1 exact-package Stable BDS smoke.

`W1-ASSET-AUDIO-001` remains open, but it blocks final Wave 1 exit rather than Whisperwood Checkpoint 1. Placeholder bindings are sufficient for this early checkpoint only; client playback and final audio identity remain unproven.

## Checkpoint 1 boundary

All six Checkpoint 1 questions remain `UNPROVEN_CLIENT_OR_BDS`: normalized asset loading, natural entity initialization, structure/resource registration, clean runtime start, same-world reopen, and candidate-scoped error absence. The three-BDS-moment ladder permits no early substitute run. Running BDS now would consume the intended milestone without testing a vertically complete Whisperwood.

This audit produced no build, package, freeze, BDS, client, console, multiplayer, or release evidence.
