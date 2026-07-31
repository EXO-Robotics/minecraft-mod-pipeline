# Crazy Craft Factory Middle-Layer Clearance Report

## Verdict

`FACTORY_MIDDLE_LAYER_FLOWING=PASS`

The production-to-testing handoff is functioning. Every pack-level candidate or near-candidate in the current factory map has an exact routing classification. All candidates that were mechanically ready during this clearance wave were consumed by deterministic preflight. The local tester executed nine exact-package jobs across the wave, including fresh generation-4 runs for Reliquary Vaults and Hearthveil. T10 is no longer starved: Aspectweave generation 5 completed substantive audit, Pocketbound generation 4 is now active, Wayfarer generation 3 is queued, and Reliquary plus Hearthveil remain in the immutable audit backlog.

No new product worker was created. Existing active product work was not interrupted.

## Exact candidate queue

| Pack | Generation | Mechanical | Stable tester | T10 | Exact next action |
|---|---:|---|---|---|---|
| Aspectweave | 5 | PASS | TEST_PASS / job 26 | REJECT_REPAIRABLE | Owner processes consolidated 10-finding repair |
| Pocketbound Companions | 4 | PASS | TEST_PASS / job 17 | ACTIVE | T10 publishes substantive result |
| Wayfarer Settlements | 3 | PASS | TEST_PASS / job 18 | QUEUED | Promote after Pocketbound |
| Reliquary Vaults | 4 | PASS | TEST_PASS / job 27 | BACKLOG 1 | Promote after Wayfarer |
| Hearthveil | 4 | PASS | TEST_PASS / job 28 | BACKLOG 2 | Promote after Reliquary |
| Vanguard Arsenal | 2 | PASS | TEST_PASS / job 20 | REJECT_REPAIRABLE | Owner processes consolidated 12-finding repair |
| Echo Vessels | 5 | MECHANICAL_DEFECT | NOT ADMITTED | NOT ADMITTED | Owner processes `MSG-T01-ECHO-MECHANICAL-REPAIR-000003`; generation 4 audit result remains preserved |
| Latchline Infrastructure | 5 | PASS | TEST_PASS / job 24 | REJECT_REPAIRABLE | Owner processes consolidated 13-finding repair |
| Aperture Foundry | 1 | PASS | TEST_PASS / job 25 | REJECT_REPAIRABLE | Owner processes consolidated 12-finding repair |
| Bounded Outcome Events | 14 | WAITING CALLABLE SURFACE | NOT ADMITTED | NOT ADMITTED | T2 freezes the exact callable surface; owner then publishes generation 15 |
| Hearth & Hall | 0 | NO CANDIDATE | NOT ROUTABLE | NOT QUEUED | Complete authorized fresh isolated reproduction |
| Momentum Menagerie | 0 | NO CANDIDATE | NOT ROUTABLE | NOT QUEUED | Complete runtime and Golden repairs, then publish first candidate |
| Trailbound Packs | 2 | ALREADY TESTED | TEST_PASS | EXISTING CLOSURE | Continue only unrun client/audio/controller/multiplayer gates |
| Quietwork | 1 | REFERENCE | PRESERVED | NOT QUEUED | Preserve for later exact integration |
| Shatterwild Foundry | 1 | REFERENCE | DESKTOP_SMOKE_READY | NOT QUEUED | Preserve for later exact integration |
| Catalyst Wilds | 1 | NO ROUTABLE TUPLE | NOT ROUTABLE | NOT QUEUED | Existing-product closure publishes exact BP/RP tuple or approved flat profile |

The exact repository, ref, commit, tree, artifact paths, sizes, hashes, receipts, submission messages, and blockers are recorded in `FACTORY_CANDIDATE_BACKLOG.json`.

## Mechanical results

Fresh passing admissions in the closing portion of the wave:

- Reliquary generation 4: scanner-only repair; exact product bytes unchanged; fresh no-local scan covered 280 paths and 455/455 reachable objects with zero restricted findings; noncircular process receipt validation passed.
- Hearthveil generation 4: 23/23 tests, 5/5 reachability checks, 10/10 mutations killed, deterministic double build, package verifier, and zero mandatory restricted findings.
- Aspectweave generation 5: 52/52 tests, zero repository findings, deterministic exact package rebuild.
- Latchline generation 5 and Aperture generation 1 were admitted earlier in this same routing wave and subsequently passed Stable BDS.

Mechanical defects were routed directly to owners and never sent to T10:

- Vanguard generation 1: candidate envelope, package-container, restricted scan, and receipt defects; corrected by generation 2.
- Latchline generation 4: archive policy mismatch; corrected by generation 5.
- Reliquary generation 3: committed scanner execution error; corrected by generation 4.
- Hearthveil generation 3: reachable restricted receipt metadata findings; corrected by generation 4.
- Echo generation 5: the fresh 82/82 tests and deterministic package rebuild passed, but an unsuperseded stale qualification receipt contradicted the generation-5 tuple and the claimed Git-object scan did not inspect reachable blob contents. The exact two-finding mechanical repair was returned to the original owner without consuming BDS or T10 capacity.

## Local BDS tester

`com.crazycraft.local-tester` remains running with a two-job ceiling and the pinned qualifier image:

`crazycraft-exact-package-qualifier@sha256:c3adfe3f7cad7c174d23db52dd14da6937901b1df7f9be853c65167086ed811f`

Current Stable BDS version: `1.26.33.2`.

The latest parallel pair completed:

- `JOB-000000000027` — Reliquary generation 4 — `TEST_PASS`
- `JOB-000000000028` — Hearthveil generation 4 — `TEST_PASS`

Both results bind exact package hashes and prove only package activation, shipped-entrypoint initialization, clean shutdown, and same-world restart. Client and release gates are not inferred.

## T10 routing

T10 capacity remains exactly one active and one queued:

- Active: Pocketbound generation 4.
- Queued: Wayfarer generation 3.
- Immutable backlog: Reliquary generation 4, Hearthveil generation 4.

T10 results for Vanguard, Echo, Latchline, Aperture, and Aspectweave were consumed. Each became one consolidated owner repair message. T10 did not receive mechanical submission defects.

## Hearth & Hall isolation disposition

Grandfathering was rejected. The preserved preliminary package remains immutable, but it cannot prove contemporaneous isolation. The existing durable owner is actively rebuilding the accepted source-neutral product in the allocated independent repository and must publish generation 1 with a contemporaneous candidate-bound receipt.

## BOE Platform decision

T2's repaired Platform authority `4e533598b6b1f5ec1f86fd000b21ee6addab38c1` / `77ff9369d0722982ea603a2c17439f6c4176646a` passed a fresh no-local 27/27 targeted suite. The bounded callable-surface result then proved that authority exposes only a same-module-graph internal registrar and lacks a deliverable pack-local acquisition, negotiation, lifecycle, or package-linkage surface. T1 recorded `PLATFORM_CHANGE_REJECTED_WITH_REASON` in `MSG-T01-OUTCOMES-PLATFORM-DECISION-000001`; the owner consumed it in `MSG-P14-OUTCOMES-PLATFORM-DISPOSITION-000001` without creating generation 15 or mutating product bytes. BOE generation 14 remains immutable and unadmitted unless a separate T1 decision authorizes an integration-level acquisition-and-linkage change.

## Reliquary state

Reliquary generation 4 is mechanically admitted and Stable-BDS-qualified. It is not complete: substantive generation-4 T10 audit remains pending behind the explicit one-active/one-queued backlog.

## Repair routing

Consolidated owner repair messages now exist for:

- Vanguard Arsenal — 12 T10 findings.
- Echo Vessels — 11 T10 findings produced generation 5; generation 5 then received the two-finding mechanical repair `MSG-T01-ECHO-MECHANICAL-REPAIR-000003`.
- Latchline Infrastructure — 13 T10 findings.
- Aperture Foundry — 12 T10 findings.
- Aspectweave — 10 T10 findings.
- Hearthveil generation 2 — 3 BDS product findings, repaired by generation 4.
- Reliquary generation 3 — 1 mechanical scanner defect, repaired by generation 4.
- BOE — one admitted pack-local Platform adapter replacement.

No tester-infrastructure failure was misclassified as a product defect.

## Integration

No new integration-intake message was issued. None of the current candidates has both a current exact-package tester pass and a current T10 substantive pass. Stable BDS alone is insufficient for integration.

## Remaining exact blockers

- T10 throughput remains intentionally bounded at one active and one queued.
- Vanguard, Latchline, Aperture, and Aspectweave require owner product repairs; Echo requires a narrowly scoped mechanical-proof repair for generation 5.
- BOE cannot consume the current Platform authority from a separate pack; it awaits a separate integration-level acquisition-and-linkage authorization or exact terminal disposition.
- Hearth & Hall is still constructing its first isolated reproduction candidate.
- Momentum Menagerie has no immutable candidate yet.
- Catalyst Wilds lacks a tester-routable exact BP/RP tuple or approved flat-package profile.
- Preview BDS, desktop client, audio, controller, live multiplayer, Realm, split-screen, physical console, rights, branding, Marketplace, integration, and release remain independent gates.

## Worker continuity

Active work was confirmed for Reliquary, Hearth & Hall, Aspectweave, Aperture, Echo Vessels, Momentum Menagerie, and Latchline. BOE is correctly idle under its exact Platform blocker, and T10 is actively auditing Pocketbound without another auditor controller. No replacement product worker was created.
