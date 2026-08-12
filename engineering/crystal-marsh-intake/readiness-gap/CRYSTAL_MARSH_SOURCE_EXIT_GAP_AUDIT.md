# Crystal Marsh source-exit gap audit

Status: `CRYSTAL_MARSH_SOURCE_EXIT_GAPS_BOUNDED`

## Exact audit authority

- Integration commit: `dde6dbe1a331ee2d1673624daaad0c56fc1f9950`
- Integration tree: `5111a8f664cd072bafe5654cfc31753235e8d567`
- Audit mode: read-only product inspection plus targeted non-BDS checks
- Excluded assigned lanes: Pearl Depths/Codex/runtime/persistence and Crystal equipment-role closure
- Excluded actions: BP/RP/script/authority mutation, BDS, package build, candidate freeze

## Proven source foundations

- Ten creatures have BP/RP definitions, role-specific movement/AI, exact native presentation bindings, nine bounded natural spawn rules, and exact loot-table bindings. Marsh Wight remains an arena-only natural-spawn exclusion and its ecology table contains no seal.
- Ten plants have custom-block definitions, native geometry/textures, exact self/resource loot, and conservative swamp/river placement totaling `0.929687` attempts per chunk before filters with no cap increase.
- Ten resource items and ten full-cube blocks have registry, icon/texture, localization, block loot, and acquisition closure.
- Twelve recipes close the ratified Crystal component/equipment graph without a trophy or deferred sidegrade bypass.
- Seven ordinary structure barrels are bound to their exact ratified loot tables. `deep_pool_entrance` remains an empty protected Pearl Depths cache. `marsh_wight_mask` is absent from static loot.
- Crystal plant ecology has no ratified regrowth system. The absence of a Whisperwood-style regrowth service is therefore not a Crystal defect and no regrowth mechanic should be invented.

## Remaining gaps

### 1. Natural-entity aggregate budget roster does not include Crystal

Severity: source-exit blocking runtime-budget composition gap.

Evidence:

- `behavior_pack/scripts/budgets.js` retains `naturalEntitiesTarget: 40`.
- `behavior_pack/scripts/combat.js::reconcileNaturalEntities` queries only `NATURAL_ENTITY_IDS` and removes rows beyond that unchanged target.
- `behavior_pack/scripts/catalog.js::NATURAL_ENTITY_IDS` contains eight predecessor IDs and none of the nine naturally spawning Crystal IDs.
- Crystal spawn rules do have conservative per-type density limits, but those limits do not make the existing aggregate target account for Crystal concurrency.

Minimum closure:

- Append exactly the nine natural Crystal IDs to the existing `NATURAL_ENTITY_IDS` roster: `prism_frog`, `crystal_newt`, `crystal_dragonfly`, `bloom_crab`, `mire_turtle`, `glass_heron`, `reed_serpent`, `silt_crocodile`, and `bog_watcher`.
- Do not add `marsh_wight`, raise `naturalEntitiesTarget`, add a subscription, or introduce a scheduler.
- Add a targeted semantic test proving all nine are counted, Marsh Wight is excluded, the target remains 40, and deterministic trimming still composes with predecessor IDs.

### 2. Two structures lack executable discovery/purpose handoff

Severity: source-exit blocking only if the assigned Codex/runtime lane does not close it.

Evidence:

- `marsh_totem` and `sunken_shrine` intentionally have no approved chest identities and remain byte-identical inert assemblies in `CRYSTAL_STRUCTURE_ECONOMY_BINDING.json`.
- Each contains reserved lodestone/lectern anchors for the ratified idol/record and shrine/Drowned Choir purposes.
- No Crystal structure interaction route exists at this audited commit.

Minimum closure:

- The assigned Crystal Codex/runtime lane should recognize these exact assembly signatures through existing block-interaction composition and fire their already-authorized structure discovery/Codex events.
- Do not invent loot, replace the anchors, add a new subscription, or make either structure a chapter-seal source.

### 3. `mire_bloom_item` has acquisition but no gameplay sink

Severity: economy exit gap unless explicitly covered by the assigned equipment-role/economy closure.

Evidence:

- `mire_orchid` yields `aionbound:mire_bloom_item` at the ratified uncommon plant-resource rate.
- The implementation contract assigns Mire Bloom a `Consumable / dye` soft-craft role.
- No recipe or existing completed-item route consumes or activates `mire_bloom_item` at this audited commit.

Minimum closure:

- Add one bounded, already-ratified soft-craft or consumable use inside an existing recipe or completed-item handler surface, with no new identity, subscription, persistence, or balance redesign; or bind an explicit engineering disposition that the present vertical intentionally supplies it only as downstream input.
- Add a targeted test proving the acquired item is not dead in the Wave 1 economy.

### 4. Final Crystal implemented-closure evidence is not yet generated

Severity: source-exit evidence gap; expected while assigned lanes are active.

Minimum closure after Pearl/Codex and equipment-role merges:

- Generate one Crystal implemented-closure manifest covering creatures, plants, blocks/resources, ecology/spawn rules, structures, loot, recipes, equipment/presentation, Codex/progression, Pearl Depths, persistence, and exact shared-handler composition.
- Add it to validator authority and generate an evidence-derived source validation receipt.
- Run the bounded targeted Crystal suites and global source validator only. Do not run BDS, deep T10, build, or freeze.

## Assigned/in-progress gaps not duplicated here

- Pearl Depths thresholds, reset/re-entry, multiplayer ownership/scaling, terminal mask entitlement/recovery, durable seal credit, protected-cache guard, and existing-schema persistence are assigned to the active Pearl lane.
- The 64 Crystal Codex pages, recognized structure routes, Crystal chapter state, and structural Skyreach rumor are assigned to the active Pearl/Codex lane.
- Prism Bow execution, Pike role, Sickle bulk-harvest behavior, cloak/accessory behavior, durability/cooldown composition, and equipment intake evidence refresh are assigned to the active equipment-role lane.

## Targeted checks observed

- Crystal economy/equipment suite: 9 tests PASS.
- Crystal plant runtime suite: 6 tests PASS.
- Crystal ecology suite: 5 tests PASS.
- Crystal entity runtime suite: role/AI, spawn, native, loot, Marsh Wight exclusion, and deterministic checks PASS.
- Crystal block/resource suites PASS after the block-loot regeneration fix.
- Crystal structure-economy suite: 6 tests PASS with seven ordinary bindings, two inert no-chest structures, and one protected empty encounter cache.
- Economy author check and post-merge loot binder check PASS (`20` bindings).
- No runtime, BDS, client, multiplayer, console, package, candidate, or release proof is claimed.

## Minimum source-exit sequence

1. Merge and validate the assigned Pearl/Codex and equipment-role closures.
2. Add the nine Crystal natural IDs to the existing aggregate reconciliation roster without raising its target.
3. Close `marsh_totem` and `sunken_shrine` through the assigned recognized-structure/Codex path, with no invented loot.
4. Give `mire_bloom_item` one ratified sink or bind its explicit downstream-only disposition.
5. Generate the Crystal implemented-closure manifest and evidence-derived validation receipt, then run targeted local validation.

At that point Crystal may be classified source-complete under the bounded proof boundary; BDS and candidate claims remain unavailable.
