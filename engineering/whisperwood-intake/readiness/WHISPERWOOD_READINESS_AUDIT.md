# Whisperwood readiness audit

Audited integration prefix: `a9d64b2a999462a2c8e2f1f1779e06c8cf6ca702`

Result: **PRE_LOOT_INTEGRATION_PREFIX_NOT_VERTICAL_COMPLETE**

Checkpoint 1 is **not authorized**. This prefix is a useful source-complete normalization and runtime scaffold, but it is not Wave A vertical completion and cannot yet satisfy the player's command-free Whisperwood journey.

## Binding contract result

| Contract criterion | Classification | Evidence-backed finding |
|---|---|---|
| Objective: first living biome fully playable offline | `MISSING_IMPLEMENTATION` | The obtainable loot/craft/progression loop and WW-facing Packet 006 subset are absent. Offline behavior is also unproven. |
| All 001 IDs in world | `MISSING_IMPLEMENTATION` | All 50 identities close in source, but the 10 resources have no acquisition routes, three plants have no natural placement, and no client/BDS load proves in-world presence. |
| WW craft loop | `MISSING_IMPLEMENTATION` | Only four ordinary timber recipes exist. There is no resource → component → WW equipment loop. |
| Hunter camp + waystone + cave | `MISSING_IMPLEMENTATION` | All three templates/rules exist statically, but their anchors are inert and empty; waystone activation and visit rewards are absent, terrain behavior unproven. |
| Thorn apex runnable | `WITHHELD_TICKET` | Thorn Stalker is explicitly a base hostile shell. `W1-CREATIVE-003/004` block apex and reward semantics. |
| Drops feed WW crafts | `WITHHELD_TICKET` | All ten WW entity definitions deliberately omit loot. `W1-CREATIVE-001/004` block identities/ranges. |
| Non-statue ambient | `PASS_SOURCE` | Static tests prove role-specific movement/AI components across all ten entities. This is not live-motion proof. |
| Spawn → explore WW without commands | `UNPROVEN_CLIENT_OR_BDS` | Natural-spawn/worldgen source exists, but no authorized runtime observation has occurred and the complete loop is absent. |
| Craft spear or armor piece | `MISSING_IMPLEMENTATION` | `mossfang_spear`, the four WW armor pieces, and the rest of the 21 WW-facing Packet 006 IDs are absent. |
| Find structure | `UNPROVEN_CLIENT_OR_BDS` | Eight templates plus two direct-prop paths close statically; discoverability and terrain fit are unproven. |
| Defeat stalker or complete shrine path | `WITHHELD_TICKET` | Apex logic is withheld and Owl Shrine has no rite/reward implementation. |
| Activate waystone | `MISSING_IMPLEMENTATION` | The template contains an inert lodestone anchor only; no handler or persistent stamp exists. |
| Obtain AH rumor | `MISSING_IMPLEMENTATION` | Broken Wagon exists, but the AH map-scrap/rumor reward and transition hook do not. |

## Checkpoint 1 contract

Every Checkpoint 1 question remains `UNPROVEN_CLIENT_OR_BDS`: normalized asset loading, natural entity initialization, structure/resource registration, clean runtime start, same-world reopen, and the candidate-scoped error scan.

The source evidence is strong but deliberately narrower:

- `tools/validate_wave1.py`: PASS; exact source-tree SHA-256 `1126b0e38ac1dd7e04af005918f721e0362c9a45f91313b100f46a5375dcc19f`.
- Runtime/Codex Node suite: 35 pass, 0 fail.
- Validator unit suite: 14 pass, 0 fail.
- Whisperwood lane tests: the audit exposed a non-relocatable repository-local authority path; that source-only defect was repaired after the audit.

The user's verification ladder permits only three meaningful BDS moments: Gate 0, Checkpoint 1 after Whisperwood vertical completion, and the final immutable candidate gate. Therefore an early pre-loot smoke is disallowed even if it is technically runnable. It would spend the authorized checkpoint without answering the binding Wave A questions and risk restarting verification churn.

## Exact minimal closure path

1. Ratify `W1-CREATIVE-001`, `003`, `004`, and the same-base-ID WW behavior decision from `005`.
2. Implement ten resource acquisition paths and entity/structure loot using only approved identities and ranges.
3. Implement all 21 WW-facing Packet 006 IDs: presentation, components, recipes/rewards, repair, behavior, and placeable trophies.
4. Implement Thorn Court phases, reset/ownership/persistence, guarded skull reward, and the alternate shrine path.
5. Implement Waystone activation/persistence and Broken Wagon's AH rumor/map-scrap handoff.
6. Complete sound bindings, required restart semantics, sapling regrowth, and natural placement for `star_grass`, `pale_reed`, and `ember_thistle`.
7. Close source tests, then authorize the one bounded Checkpoint 1 exact-package BDS smoke.

## Safe work before ticket ratification

Safe targeted checks and fail-closed scaffolding remain:

- repair the non-relocatable repository-local authority path and rerun mapping tests;
- add explicit missing/present inventory tests for the 21 WW-facing Packet 006 IDs;
- add source closure tests for resource acquisition, Waystone activation, AH rumor routing, sapling growth, sound bindings, and the three unplaced plants;
- rerun the source validator and bounded semantic tests after each non-ticketed slice.

Do not add provisional loot values, apex timings, reward semantics, or sidegrade sibling identities while their tickets remain open. Do not run BDS, build, package, or freeze at this prefix.

## Proof boundary

This audit produced no BDS, immutable-package, client, console, multiplayer, or release evidence. `PASS_SOURCE` means source semantics only.
