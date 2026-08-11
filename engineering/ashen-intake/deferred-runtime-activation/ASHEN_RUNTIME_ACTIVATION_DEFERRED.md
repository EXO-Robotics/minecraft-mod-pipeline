# Ashen deferred shared-runtime activation

Status: `ASHEN_VERTICAL_SOURCE_COMPLETE_RUNTIME_ACTIVATION_DEFERRED`  
Blocker: `MANAGED_REVIEWER_ACTIVATION_BLOCKED`  
Classification: tooling/governance blocker, not a demonstrated Ashen product defect

## Exact source authority

- Commit: `bcd65076900a3688dd797d54719263d88afd501c`
- Tree: `4d876b233e6b510687d238f1d7f6611c7c0c4ab9`
- Subject: `Bind functional Ashen equipment validation`
- G7 and prior immutable generations modified: no

This receipt preserves the clean G8 source authority unchanged. Ashen is source-complete but is **not** fully runtime-complete.

## Deferred scope only

1. Ashen equipment-role composition into the existing completed-item, hurt, and 20-tick live handlers.
2. Kiln Sky composition into the existing reconcile, tick, block-interaction, and death live handlers.

All other Ashen work already implemented and validated outside those two compositions remains valid engineering work. This ticket does not block Crystal Marsh or Skyreach source development.

## Implemented services

- `behavior_pack/scripts/ashen_equipment.js::createAshenEquipmentService` implements `routeMeleeHurt`, `useRanged`, `armorSet`, `handlePlayerHurt`, and `tickPlayers` against the ratified role data.
- `behavior_pack/scripts/kiln_sky.js::createKilnSkyService` implements `begin`, `tick`, `bossDeath`, `reconcile`, `claimHorn`, `recoverHorn`, `flushPending`, and `resolveArena`.
- `behavior_pack/scripts/ashen_rewards.js::createAshenRewardHooks` implements horn delivery, participant materials, guarded cache population, and the synchronous cache guard.

## Dormant shared connections

1. `behavior_pack/scripts/catalog.js::COMPLETED_ITEM_ROUTES` — route aionbound:ash_repeater to ashen_ranged (`ABSENT`).
2. `behavior_pack/scripts/runtime.js::itemActions` — ashen_ranged calls only ashenEquipment.useRanged (`ABSENT`).
3. `behavior_pack/scripts/runtime.js::existing entityHurt subscriber` — compose routeMeleeHurt and handlePlayerHurt without early return (`ABSENT`).
4. `behavior_pack/scripts/runtime.js::existing 20-tick player cadence` — compose ashenEquipment.tickPlayers beside combat.tickPlayers (`ABSENT`).
5. `behavior_pack/scripts/runtime.js::reconcile and existing tick callback` — compose kilnSky.reconcile and kilnSky.tick (`ABSENT`).
6. `behavior_pack/scripts/runtime.js::existing synchronous/deferred block-interaction paths` — make durable Kiln completion authoritative for overlapping Ember Forge cache guards, retain synchronous pre-clear lock, recover pending horn entitlement before any begin path (`ABSENT`).
7. `behavior_pack/scripts/runtime.js::existing entityDie subscriber` — compose kilnSky.bossDeath beside thornCourt.bossDeath (`ABSENT`).
8. `behavior_pack/scripts/runtime.js::return object` — expose ashenEquipment and kilnSky for semantic testing (`ABSENT`).

## Existing persistence/cache surfaces

No new persistence schema is required. Later activation is bounded to existing player `cooldowns` and `credits`, existing world `encounters.terminal` and `encounters.pendingKilnSky`, selected-item ammunition/durability mutation, the in-memory encounter session map, and the in-memory opened-cache guard.

The exact durable keys are recorded in the JSON twin. A full-inventory horn-entitled player must remain on the recovery path and must not fall through into a new encounter.

## Passed evidence and proof boundary

The bound source receipt reports `PASS` for its source/mechanical checks. Dedicated equipment semantics, declarative item components, Kiln Sky source-semantic tests, and state migration are proven by their existing receipts. Shared runtime activation is explicitly false in both dedicated receipts.

Focused tests bound to this ticket:

- `node --test tests/wave1_ashen_equipment_functional.test.mjs`
- `node --test tests/wave1_kiln_sky.test.mjs tests/wave1_ashen_rewards.test.mjs tests/wave1_ashen_structure_rewards.test.mjs`
- `python3 engineering/ashen-intake/equipment-functional/test_ashen_equipment_evidence.py`

No BDS, package, client, or live shared-runtime proof is claimed for the dormant compositions.

## Known receipt reconciliation debt

`engineering/ashen-intake/kiln-sky-runtime/test_kiln_sky_runtime_evidence.py` currently runs two checks: the activation-absent/source-boundary check passes, while the checked-in deterministic evidence comparison fails because the receipt binds the earlier `state.js` hash `b6d569...` and the integrated source now hashes to `69eb00...`. The dedicated service semantics remain 30/30 PASS in the focused Node run. This is recorded as stale receipt debt after later integration movement, not as a Kiln Sky semantic failure or a demonstrated product defect. The prior evidence is intentionally untouched here.

## Reviewer rejection history

The exact refs `codex/ashen-shared-activation`, `-r2`, and `-r3`, plus the two standing-authority refs, all remained at `bcd65076900a3688dd797d54719263d88afd501c`. No activation or authority commit landed. Historical reviewer reports described the requested work as a broad persistent shared-runtime mutation or governance-scope expansion and did not accept delegated authority as trusted direct approval. The separate decision-source audit classified decisive attribution as partial; this receipt therefore records the blocker without claiming which hidden component authored the denial.

## Deferred integration ticket

Ticket: `W1-G8-ASHEN-SHARED-RUNTIME-ACTIVATION-DEFERRED`

No new Creative or gameplay-design decision is required. Acceptance criteria:

- Import and instantiate exactly one Ashen equipment service and one Kiln Sky service using existing dependencies.
- Use only existing completed-item, hurt, 20-tick, reconcile, tick, block-interaction, and death paths; add no subscription or interval class.
- Preserve current balance, persistence schema, ownership, encounter, reward, duplicate, replay, and recovery semantics.
- Make durable Kiln completion authoritative for overlapping Ember Forge cache guards while retaining synchronous pre-clear locking.
- When a horn-entitled player has full inventory, remain in recovery and do not fall through into a new encounter.
- Pass targeted shared-handler semantic tests, prove no duplicate subscription/double dispatch, and prove bounded/idempotent persistent mutations where designed.
- Run no BDS solely for activation; final integrated qualification remains separately gated.

Before the final immutable Wave 1 candidate, this ticket must either activate normally or the product contract must be explicitly revised. Dormant gameplay must not ship silently.
