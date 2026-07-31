# Crazy Craft factory safe restart

## Verdict

The paused factory was repaired and restarted without changing its pack map,
mailbox topology, production assignments, shared-runtime contract, or audit
contract. The router and local tester are live, T10's deleted recurring service
has been recreated, exact candidates have moved through mechanical admission
and real Stable BDS, T10 has produced a substantive result, the router
automatically returned one consolidated repair to the original owner, and the
one-active/one-queued T10 limit is populated.

Classification:
`FACTORY_SAFE_RESTART_COMPLETE_AUTONOMOUS_FLOW_ACTIVE`.

This classification proves factory routing, Stable BDS, audit, and repair
movement. It does not claim that any newly routed pack is accepted, integrated,
client-qualified, console-qualified, rights-cleared, Marketplace-ready, or
released.

## Starting and current authorities

- Frozen supervisor start: `acade0fe248464928e2677c6586f38bf84af0414`
  / `35e0037ede2fe2f642bbceaa7aa39f4283fd9dbc`.
- Frozen mailbox start: `dcbc94f58989c6b952514880a3061c69d809b3dc`.
- Initial router cursor: `2b3eac5281c1cea7d0766e5f63e6a6b5e85555e8`.
- Recovery anchor: `3a35fd783935ce1aa0cfbc4a9c8fb4d6c45373fc`.
- Evaluated mailbox HEAD and router cursor:
  `29da0f26e801e8aadf6d84d0282e51d32f1fa84d`.
- Current-cursor and full-history canonical projection:
  `0c48b8f9611bb42a701cb0746e8ff3138e77523f27c6d3107958457140fe64f3`.

## Exact mailbox compatibility

`ROUTER_LEGACY_COMPATIBILITY_LEDGER.json` contains four exact exemptions keyed
by commit, path, and raw SHA-256:

1. Aspectweave request 0001: historical, superseded by request 0002.
2. Aspectweave request 0002: historical, superseded by later product
   generations.
3. BOE Platform decision: authoritative historical rejection with its malformed
   legacy idempotency represented canonically only in the ledger.
4. Echo request 0002: pack-local quarantine requiring exact supersession.

No blanket legacy acceptance exists. Unknown invalid objects still fail closed.
Both replay modes reach the same projection, retain append-only history, and
produce no duplicate semantic action.

Echo superseded request 0002 with the valid exact request:

- Message: `MSG-P13-ECHO-PLATFORM-REQUEST-000003`
- Mailbox commit: `aac6e32835680d51083eb7f25b08f45e5917397b`
- Classification: `PRODUCT_LOCAL_REPAIR_ARTIFACTS_ONLY`
- Candidate classification: `NO_IMMUTABLE_G7_CANDIDATE`

The corrected request now waits on one exact T1 Platform admission and no longer
blocks any unrelated message.

## Router

The router now distinguishes:

- valid current messages;
- the four exact compatibility-ledger objects;
- new attributable pack-local invalid messages;
- global authority failures.

It also recognizes only two exact candidate scan-sidecar roles when each file
is added in the same commit as its candidate message and its raw SHA-256 is
bound by that message. This allowed Aspectweave generation 9's final-metadata
scan artifacts to remain evidence rather than being misclassified as mailbox
messages. An unbound or wrong-hash sidecar still fails closed.

It also treats current source-neutral shared-runtime requests as exact pending
T1-to-T2 routes instead of protocol poison. T1 Platform admission clears the
pending route, and T2 response messages are recorded without reinterpretation.

The launchd service `com.crazycraft.factory-router` is loaded as an expected
one-shot every 120 seconds. At the recorded snapshot it had 12 runs and last
exit 0. Between cycles, `not running` is the correct launchd state. Cursor and
mailbox HEAD agree, unseen message count is zero, and protocol defect count is
zero.

Targeted router tests: 35 passed.

## Tester

The exact historical Aperture intake `MSG-T01-APERTURE-BDS-000030` is bound in
`EXACT_TESTER_INTAKE_COMPATIBILITY_LEDGER.json`, invalidated once, superseded by
000031, and permanently excluded from redispatch. The valid retry and terminal
result remain authoritative.

The tester reconciliation bug that dereferenced a missing `job_root` on
mailbox-derived terminal jobs was repaired. The launchd service
`com.crazycraft.local-tester` is running at PID 23053. Its state contains 21
terminal jobs, no active job, and no pack-local rejection. The preserved
idempotency mismatch has not recurred since the fix.

Post-restart exact Stable results:

- Aperture generation 3: `JOB-000000000033`, `TEST_PASS`.
- Hearthveil generation 5: `JOB-000000000034`, `TEST_PASS`.
- Reliquary generation 6: `JOB-000000000035`, `TEST_PASS`.

The associated service receipts are bound in
`safe-restart/FACTORY_SAFE_RESTART_SERVICE_STATUS.json`. No candidate tuple was
mutated and no BDS job was duplicated.

Targeted tester tests: 14 passed.

## T10

The deleted heartbeat automation was recreated under the existing assignment:

- Automation ID: `t10-factory-audit-service`
- Schedule: `FREQ=MINUTELY;INTERVAL=15`
- Destination task: `019fa887-8d31-7741-bc92-51fe01bceb5c`
- Policy: `failed_runs_only`

The first post-recreation audit consumed exact Aperture generation 3 and
published `MSG-T10-APERTURE-AUDIT-000003` at mailbox commit
`2d807b27b7baa982f16dbbd3c02e6d7933a541f6`. It returned four bounded product
findings and did not edit the candidate. The router then automatically:

1. published
   `MSG-T1R-APERTURE-FOUNDRY-OWNER-REPAIR-G000003-66866054D18D`;
2. promoted Hearthveil generation 5 to active; and
3. moved Reliquary generation 6 into the queued slot.

Momentum generation 3 is terminal, not active. T10 completed Hearthveil
generation 5 as `TEST_FAIL_PRODUCT`; the router published one consolidated
generation-6 repair and immediately promoted Reliquary generation 6 from queued
to active. No queued candidate currently exists.

## T2 and Momentum

The T2 outer repository is clean at:

- Commit: `298014213c7ccdb013f8fb4d9e7d48fdac7a799e`
- Tree: `8ca1fa6302af2383b568f5fd23614d12d5a1e2fa`

The nested Platform authority remains unchanged:

- Commit: `4e533598b6b1f5ec1f86fd000b21ee6addab38c1`
- Tree: `77ff9369d0722982ea603a2c17439f6c4176646a`

All outer untracked roots were classified and excluded from execution and
packaging. Nothing was deleted. No pack worker received Platform write
authority.

Momentum retained product-repair commit
`4501555d3ff5a59e7175d23ddad33aa9ea08fa71` but may not publish generation 4
from that commit alone. T1 published the required consolidated repair
`MSG-T1R-MOMENTUM-MENAGERIE-OWNER-REPAIR-G000003-8FEF231A154C`.

T2 processed exact assignment
`SA-T02-MOMENTUM-PLATFORM-ADMISSION-000001` and published
`MSG-T02-MOMENTUM-PLATFORM-ADMISSION-RESULT-000001`:
`PLATFORM_CHANGE_REJECTED_WITH_REASON`. The current Platform does not register
Momentum and does not claim the requested automatic exact-once or durable
recoverable lease semantics. This is a Platform blocker, not a product failure.

The uncommitted `audits/` and three listed tools remain preserved as
`UNCOMMITTED_LOCAL_EVIDENCE_AND_TOOLING_NOT_CANDIDATE_AUTHORITY`.

## Blockbench

PID 16180 was inspected before closure. It used the dedicated
`/private/tmp/ccr_p16-blockbench-profile`, had no unsaved project, and was tied
to the superseded original Aperture repository. It was deliberately closed
without changing candidate or asset bytes. The unrelated main Blockbench
process remains untouched. Any next Aperture native edit belongs exclusively to
`aperture-foundry-reproduction-v1` under a fresh single lease.

## Pack transitions

- Aperture G3: mechanical PASS, Stable PASS, T10 product failure, owner active
  on bounded G4 repair in the reproduction repository only.
- Hearthveil G5: mechanical PASS, Stable PASS, T10 product failure, exact
  consolidated G6 repair published. Preview remains a separate required gate.
- Reliquary G6: mechanical PASS, fresh Stable PASS, T10 active; G4 evidence was
  not carried forward as final proof.
- Aspectweave G8 remains preserved after mechanical failure. G9 is now an
  immutable candidate at mailbox commit `bd25df51d2b84f929c4413fe60136bed5bb25a3e`
  and awaits exact mechanical preflight.
- Momentum G3: consolidated repair active; Platform dependency rejected with
  exact reason; no G4 until a later T1 decision resolves it.
- Echo G7: corrected request 0003 committed; no immutable G7 candidate exists.
- Hearth & Hall G1: accepted isolation remains closed; owner active on G2
  reciprocal BP/RP and literal entrypoint repair.
- Latchline G6 was not closed by `ce12ad…`; G7 is now an immutable candidate
  at mailbox commit `29da0f26e801e8aadf6d84d0282e51d32f1fa84d` and awaits exact
  mechanical preflight.
- BOE G14: preserved; owner active on the exact pack-local adapter authority for
  G15. No materially unchanged Platform request is permitted.

The detailed machine-readable transitions are in
`safe-restart/PACK_TRANSITION_LEDGER.json`.

## Active work and bounded blockers

Restarted existing tasks only:

- Momentum Menagerie
- Hearth & Hall
- Latchline Infrastructure
- Bounded Outcome Events
- Aspectweave
- Aperture Foundry reproduction

Echo completed its exact atomic request correction and stopped. Hearthveil and
Reliquary owners remain paused while downstream work runs. T2 completed the
Momentum decision and returns to quiescence pending another exact admitted
request.

Remaining blockers are pack-local:

- Echo request 0003 awaits a later T1 Platform admission.
- Momentum requires a new T1 decision about narrower registration and any
  genuinely required durable lease protocol.
- Aspectweave G9 awaits exact T1 mechanical preflight.
- Hearthveil requires its authorized G6 bounded repair.
- Reliquary G6 is the active T10 candidate.
- Client, controller, physical-console, rights, Marketplace, integration
  acceptance, and release gates remain separate.

## Proof of autonomous movement

The restart is not classified from service loading alone. The observed chain
was:

`Aperture G3 mechanical PASS`
→ `exact Stable BDS PASS`
→ `T10 active audit`
→ `T10 TEST_FAIL_PRODUCT`
→ `router consolidated owner repair`
→ `Hearthveil active`
→ `Reliquary queued`.

The subsequent autonomous chain also completed:

`Aspectweave G9 immutable publication`
→ `Hearthveil G5 T10 TEST_FAIL_PRODUCT`
→ `router consolidated Hearthveil G6 repair`
→ `Reliquary G6 promoted active`.

In parallel, Hearthveil and Reliquary each completed exact Stable BDS, Echo
published its valid superseding request, and T2 published a bounded Momentum
Platform decision. No superseded Aperture repository received restart write
authority.
