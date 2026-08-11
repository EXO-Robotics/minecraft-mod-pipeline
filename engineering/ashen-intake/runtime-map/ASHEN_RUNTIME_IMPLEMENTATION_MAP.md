# Ashen Highlands ratified runtime implementation ownership map

Status: **RATIFIED FOR SCOPED IMPLEMENTATION; ASSET AND PRODUCT PROOF GAPS REMAIN**

Exact base: commit `9c2880863ff260410028284228f5995b59dcacfc`, tree `91d7ed5ffbe94d693c5d37848942b2702edfbd69`.

This source-only map reconciles Packet 002 after Whisperwood Checkpoint 1. It edits no BP/RP files, runs no build or BDS, and proves no Ashen gameplay. G7 remains immutable and G8 is the active successor line.

## Ratified authority

Decision ledger v3 (`b554db9f...`) ratifies the following proposal bytes exactly:

- `W1-001-AH` — `dd26a683f7f3e5301b66d7f2861454b5bf6b79818d12e0e8e1b22b6f07217774`
- `W1-003-KILN-SKY` — `1b2d5f77185a1461040d7559d0d8ecdaf803d7727e419ceac32636865be85d7c`
- `W1-004-AH` — `93736ff800b1c90c8a6547d84336a6650f8ae32750f262de8e460385a7a26889`

The machine map embeds each exact proposal object and records that its original proposal bytes are preserved. `W1-CREATIVE-005` remains deferred: base equipment identities may proceed, but no Summit Hammer or AH-tempered sibling identity or behavior is authorized.

## Reconciliation

| System | Disposition | Binding use |
|---|---|---|
| Runtime/router, structure service, Codex schema | `KEEP` | Reuse composition and bounded service architecture. |
| Persistence, budgets, equipment framework, Kiln Sky | `REFINE` | Add exact Ashen state and rules; preserve caps. |
| Loot/recipes, natural rules, Codex/progression content | `REPLACE` | Packet 002 and ratified Ashen authority own content. |
| Legacy G7 Ashen cast | `SUPERSEDE` | Reuse role patterns only; never relabel legacy identities. |
| Ashen regrowth | `DEFER` | No Ashen regrowth authority exists; Whisperwood sapling semantics do not transfer. |

The machine map assigns dedicated source ownership for all 10 creatures, 10 plants, 10 blocks, 10 resources, 10 structures, and 14 Packet 006 Ashen-facing links. Shared runtime, persistence, catalogs, atlases, localization, and composition remain primary-integrator-only.

## Identity and economy resolution

All 22 creature-loot prose terms are resolved without inventing identities:

- 20 terms alias `charbone`, `furnace_chitin`, `ember_resin`, `basalt_core`, or `volcanic_glass_shard` exactly as `W1-001-AH` specifies.
- `Pack Cinder Mark` is narrative/Codex-only.
- `Drake Scale` selects the existing `aionbound:drake_scale` new-required-item row. Its `ashen_set_upgrade` craft-home prose does not authorize an upgrade or sidegrade while `W1-CREATIVE-005` is deferred.

Loot tables and structure chests may select numbers only inside the closed `W1-004-AH` ranges. No new loot identity is authorized. `aionbound:ash_drake_horn` is the sole chapter-critical seal. `aionbound:ember_forge_core` is optional mastery/forge reward only and cannot fill the seal slot.

## Kiln Sky

The exact `W1-003-KILN-SKY` encounter envelope is ready for implementation: `aionbound:kiln_sky`, arena entity `aionbound:ash_drake`, structure `aionbound:ember_forge`, apex tag `aionbound.kiln_sky_apex`, immutable pull-time health scaling, four approved phases, timing/cooldown composition, mite caps, multiplayer eligibility, reset/re-entry, persistence, terminal ordering, recovery, and repeat semantics.

Natural/ecology Ash Drake cannot receive the arena tag, create or join the session, complete the chapter, write completion/reward state, or deliver the horn. Physical horn fulfillment is at-most-once best effort with the approved recovery claim; durable virtual seal credit is the progression representation. Repeat clears may grant materials/chest rewards and the optional forge-core roll, but not duplicate seal or horn entitlement.

Damage values, attack-effect radii, and arena radius are still explicit nondecisions. Engineering may not create new attacks or phases. No Thorn Court, Whisperwood, or other-region tuning transfers.

## Asset gates

The initial intake remains historical evidence: all 50 canonical artifact sets existed, while 30 custom-geometry assets required native repair and 20 blocks/resources were Blockbench-N/A only if shipped as native full cubes or flat items.

Current representative evidence advances exactly seven assets—`ash_drake`, `ember_crow`, `ash_ram`, `fire_bloom`, `smoke_reed`, `ember_forge`, and `ancient_kiln`—through native round-trip/export-equivalence gates. Twenty-three custom-geometry assets remain native-repair dependencies. Blocks/resources still require static texture normalization. Golden promotion and client visual review remain withheld. The representative PASS does not prove BP/RP binding, gameplay, BDS, client, multiplayer, PS4, Marketplace, or release.

## Ecology, progression, and budgets

Nine creatures may receive natural Ashen rules; Ash Drake is arena-only. Preserve global `naturalEntitiesTarget: 40`, structure queue `4`, active structures `1`, and structure-block cap `4096`. Exact Ashen weights and group sizes remain engineering tuning. Registry growth does not increase loaded-area density.

Plants use their own Ashen placement tuning and no invented regrowth. All ten visual structure props require authored `.mcstructure` assemblies and dedicated placement/loot binding. Codex hooks cover discovery, acquisition, structures, equipment, Kiln Sky, chapter seal credit, and the Crystal Marsh rumor. The transition remains sandbox-soft.

## Verification boundary

`test_ashen_runtime_map.py` verifies exact base/hash authority, embedded proposal equality, all roster counts and IDs, 22 identity dispositions, closed classifications, nonconflicting owners, native proof gaps, no Whisperwood tuning transfer, unchanged budgets, and byte-deterministic regeneration.

This map authorizes scoped implementation ownership. It is not an implementation, build, BDS, client, multiplayer, console, or release receipt.
