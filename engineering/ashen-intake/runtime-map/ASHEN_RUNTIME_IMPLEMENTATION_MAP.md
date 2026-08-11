# Ashen Highlands Runtime Implementation Map

Status: **SOURCE OWNERSHIP MAPPED — IMPLEMENTATION GATED**

Base: `9acf1b0f62ade90b59ba65e0a9e0618852ff3159`
Tree: `9b7b425e535439658df29c92f82ad73e9aa54e3d`

This is the source-only Packet 002 execution map requested after Whisperwood Checkpoint 1. It creates no BP/RP bytes, runs no build or BDS, and proves no Ashen runtime behavior. G7 remains immutable.

The machine authority is `ASHEN_RUNTIME_IMPLEMENTATION_MAP.json`. It inventories all 50 Packet 002 IDs plus the 14 Packet 006 links that face Ashen, binds every dedicated target to one source owner, and fails closed wherever Creative authority is still deferred.

## Reconciliation result

| System | Disposition | Engineering use |
|---|---|---|
| Composed runtime and router | `KEEP` | Add Ashen handlers without reintroducing early-return suppression. |
| Persistence schema | `REFINE` | Append idempotent AH discovery, claim, boss, and reward state only after ownership authority. |
| Runtime budgets | `REFINE` | Preserve the global natural-entity target of 40; tune locality before requesting any increase. |
| Legacy G7 entity cast | `SUPERSEDE` | Packet 002 owns Ashen identity. Reuse role architecture, never old cast identity or numbers. |
| Natural spawn rules | `REPLACE` | Nine natural Ashen rules; Ash Drake remains arena-only. |
| Structure runtime service | `KEEP` | Retain bounded placement and per-player claim architecture. |
| Ashen structure assemblies | `REFINE` | Author ten Ashen `.mcstructure` assemblies and region-specific placement rules. Packet prop meshes are not encounter assemblies. |
| Loot and recipes | `REPLACE` | Approved Ashen identities own the economy after later-region authority is ratified. |
| Codex schema | `KEEP` | Append AH categories and indices; do not reorder Whisperwood state. |
| Codex/progression content | `REPLACE` | Bind AH discovery, burned-camp CM rumor, and chapter-two seal flow. |
| Equipment framework | `REFINE` | Packet 006 identities replace legacy content while preserving lateral roles. |
| Kiln Sky executable shell/rewards | `DEFER` | Phase names and attack identities are known; executable ownership, timing, persistence, and rewards are not. |

## Creature runtime map

| ID | Approved role | Reusable pattern | Disposition | Spawn boundary | Persistence boundary |
|---|---|---|---|---|---|
| `ash_mite` | swarm hostile | G7 hostile melee ground | `REFINE` | high near vents/caves; exact weight/group withheld | no restart persistence required |
| `ember_crow` | ambient air | G7 ambient flyer | `REFINE` | medium sky; exact weight/group withheld | none |
| `magma_lizard` | small hostile | G7 hostile melee ground | `REFINE` | medium hot rock | none |
| `furnace_beetle` | hostile | G7 hostile melee ground | `REFINE` | medium-low | none |
| `char_wolf` | hostile pack | Whisperwood pack hostile | `REFINE` | medium packs; exact cap withheld | none |
| `cinder_lynx` | elite hunter | hostile pursue/melee architecture | `REFINE` | low | none |
| `ash_ram` | neutral territorial | neutral retaliatory ground | `REFINE` | low plateaus | none |
| `soot_stag` | neutral rare | rare neutral ground | `REFINE` | low plateaus | none |
| `basalt_tortoise` | tank neutral | neutral retaliatory ground | `REFINE` | rare | none |
| `ash_drake` | chapter apex | legacy cast only as negative evidence; Thorn Court architecture only after ratification | `SUPERSEDE` identity / `DEFER` encounter | arena-only | blocked encounter/ownership/reward state |

Every ordinary hostile must roam, acquire or retaliate as its role requires, navigate, attack, and recover/disengage. Neutral creatures must roam and retaliate rather than pre-aggro. Ember Crow must use readable flight. These are quality bars, not proof that the current pack supplies them.

`ash_sovereign_wyrm` is not renamed into Ash Drake. The approved `aionbound:ash_drake` identity supersedes that legacy cast; legacy health, movement, damage, and reward numbers do not transfer.

## Plants, blocks, resources, and structures

The machine map covers exactly:

- Plants: `cinder_grass`, `ash_fern`, `smoke_reed`, `char_shrub`, `soot_mushroom`, `magma_moss`, `glow_root`, `basalt_flower`, `ember_vine`, `fire_bloom`.
- Blocks: `ash_log`, `char_planks`, `ash_soil`, `cinder_gravel`, `smolder_stone`, `basalt_brick`, `basalt_pillar`, `heat_bark`, `ember_moss`, `volcanic_glass_block`.
- Resources: `smolder_bark`, `charbone`, `sulfur_cluster`, `volcanic_glass_shard`, `ember_resin`, `heatstone`, `furnace_chitin`, `basalt_core`, `ash_crystal`, `fire_bloom_seed`.
- Structures: `fire_totem`, `burned_camp`, `char_wagon`, `broken_bridge`, `basalt_arch`, `ash_watchtower`, `ancient_kiln`, `ember_forge`, `lava_shrine`, `ash_cave`.

Plant placement uses the proven Whisperwood feature/feature-rule shape but not its ecology numbers. No Ashen regrowth loop is authorized, so none is invented. Blocks and flat resources may remain Blockbench-N/A only when their shipping form is a native full cube or flat item. Custom-geometry plants and landmarks must pass native repair first.

All ten structure prop assets are visual inputs, not authored world structures. Each target owns a dedicated assembly, structure feature, feature rule, and structure-specific chest table. `ember_forge` remains one per Highlands realm by design and cannot become a live Kiln Sky trigger until the boss envelope is ratified.

## Packet 006 Ashen-facing equipment

| Category | IDs | Disposition |
|---|---|---|
| Weapons | `basalt_hammer`, `ember_great_axe`, `ash_repeater` | `REPLACE` legacy content; `REFINE` framework |
| Armor | `ashen_helmet`, `ashen_chest`, `ashen_legs`, `ashen_boots` | `REPLACE` legacy content; `REFINE` framework |
| Tools | `basalt_pick`, `ember_hammer`, `ore_chisel` | `REPLACE` legacy content; `REFINE` framework |
| Accessories | `ember_totem`, `briar_ring` | Ember Totem `REPLACE`; Briar Ring base `KEEP` |
| Trophies | `ash_drake_horn`, `ember_forge_core` | Approved identities; grant semantics deferred |

The existing Briar Ring item, recipe, art, and bounded thorn-chip effect are retained. “Temper in AH” does not authorize a sibling item or an additional mechanic. `W1-CREATIVE-005` remains deferred.

Every other equipment entry has dedicated item, recipe, attachable, model, animation, icon, Codex, acquisition, durability/repair, and role targets in the JSON map. The map does not select unapproved stats or treat a registry entry as complete gameplay.

## Kiln Sky boundary

Binding identity already available:

- Boss: `aionbound:ash_drake`
- Arena link: `aionbound:ember_forge`
- Seal: `aionbound:ash_drake_horn`
- Phases: Ash Landing, Vent Choir, Glass Wing, Kiln Heart
- Attacks: Cinder Breath, Tail Slag, Thermal Dive, Mite Shake, Basalt Quake, Glass Feather Storm

Still blocked by `W1-CREATIVE-003-KILN-SKY`:

- Phase thresholds and timing
- Leash, timeout, wipe, reset, and re-entry
- Add caps
- Multiplayer ownership and scaling
- Late join and disconnect handling
- Persistence and encounter recovery
- Idempotent terminal grant and recovery
- Repeat-clear semantics

Still blocked by `W1-CREATIVE-004-ASHEN`:

- Probabilities, quantities, chest rolls, guaranteed package details, and alternate-seal semantics

Thorn Court supplies reusable architectural lessons—session-scoped boss tags, bounded participants, durable entitlements, and recovery-aware physical delivery—but none of its values or exact ownership rules transfer automatically.

## Remaining identity blockers

The later-region tranche of `W1-CREATIVE-001` remains deferred. These 22 terms may not become items yet:

`Ash Dust`, `Ash Wool`, `Beetle Core Fragment`, `Char Feather`, `Char Hide`, `Char Pelt`, `Cinder Beak`, `Cinder Pelt`, `Drake Scale`, `Ember Fang`, `Ember Sinew`, `Heat Scale`, `Lynx Claw`, `Mite Mandible`, `Pack Cinder Mark`, `Ram Horn Curve`, `Shell Plate`, `Smolder Gland`, `Soot Antler`, `Stag Heart Cinder`, `Swarm Queen Scale`, `Warm Blood Vial`.

Curiosity terms remain Codex-only unless Creative explicitly promotes them. Crates, bundles, scraps, chips, and quantity language do not silently create new item identities.

## Native readiness dependency

The independent Packet 002 asset lane reports:

- 50/50 complete artifact sets and exact category mirrors
- 30 custom-geometry assets requiring native repair: all creatures, plants, and landmarks
- 20 blocks/resources that are Blockbench-N/A only as native full cubes/flat items
- 0/50 editable assets with real locator elements
- 0/50 declared clip sets matching the generic exports
- 2/50 texture contracts compatible; 48/50 require disposition

Representative class gates are `ash_drake`, `ember_crow`, `ash_ram`, `fire_bloom`, `smoke_reed`, `ember_forge`, and `ancient_kiln`. Do not scale class construction until these pass real-locator, exact-clip, texture-contract, native round-trip/export-equivalence, and Golden evidence.

Companion evidence remains separately reviewable:

- Authority intake: commit `8bd48a13ff3448f062c2752f9fc8d26668da2bbf`, tree `87ab1fff18d04d323ff0104662f741121d4d85e0`
- Native readiness: commit `f3c39dd5766bfa5ba56486b2b804e2d6efdfa88f`, tree `567925c0cefef0052e963960be2ef9b42754c575`

## Worldgen and runtime budgets

- Preserve `naturalEntitiesTarget: 40`; no increase is authorized.
- Preserve structure queue `4`, active structures `1`, and structure block cap `4096`.
- Ash Drake is arena-only; nine Ashen creatures may receive natural rules.
- Keep the Creative density ordering from ash-mite swarms down to rare tortoises and arena-only Drake.
- Keep soft cell targets: path props 4–10, camps/wagons 1–2, major landmarks 0–1, apex arena one per biome realm.
- Exact spawn weights and herd sizes are engineering tuning work, not selected by this map.

Registry growth must not become loaded-area growth.

## Codex, progression, and ownership

The append-only Ashen data target covers ten creatures, ten plants, ten blocks, ten resources, ten structures, fourteen equipment links, Kiln Sky, the Ashen chapter, and the Crystal Marsh rumor.

The integrator alone owns edits to shared composition files: `runtime.js`, `state.js`, `catalog.js`, `wave1_codex_data.js`, `wave1_equipment_roles.js`, the shared texture atlases, `blocks.json`, and localization. Dedicated lanes own only their non-overlapping files listed in the JSON map.

The progression remains soft: the AH trophy or a heat-resistant kit can support the CM transition. The map does not create a mandatory linear quest lock. The existing Whisperwood Ashen rumor is an invitation into AH, not evidence that AH is implemented.

## Authority evidence

Primary hashes include:

- Contract JSON: `aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5`
- Ashen loot: `f5b2ff909a6e7b7669da561cc2659439819227f99d15d221dbea0147750d3727`
- Crafting tree: `1f3482ba3dd9f916e08aa544153cc841871a729a2e82d9e75601715f4b5ee807`
- Equipment progression: `7ecf57e6af099ae3cda8a7432228fb5ee996f20b02b76888a82c0c1a3e3c891d`
- World generation: `bc18a1e1f73d6045ab7e583afe910ca13d4776d439c8f3dfb45dae5784372f4b`
- Boss progression: `5ef85e1e0b29973a617f7dca4a8b119443c01644ba33f0e11166ef8d417d5a6f`
- Packet manifest: `6cb3bd25a1ef473e60e5ed0ebf78288bcc4d53db1ff4ec74db4d22ddb036c738`
- Base normalization inventory: `4a65ccbc10f47a86e3aec649874916a9d4ad5cb9feef7817d75a527774a3a842`
- Base decision ledger: `3e2b64785da9310b098e06981ebc95777ddc7e5d2666f803b79ce374470a9561`

The JSON map contains the complete authority list, canonical asset hashes, normalization findings, dedicated targets, base-presence checks, and owner labels.

## Verification

`test_ashen_runtime_map.py` proves exact counts and IDs, the closed disposition vocabulary, fail-closed Kiln Sky handling, unchanged console target, non-conflicting target ownership, exact-base authority hashes, source-only proof boundaries, and byte-deterministic regeneration.

This lane does not claim Ashen implementation readiness beyond the map. Broad implementation may proceed only after the blocking authority and asset gates above are satisfied or explicitly ticketed into scoped work that does not require invention.
