# T1 Durable Dispatcher Activation Report

Snapshot: `2026-07-30T14:07:09Z`

## Verdict

The durable T1 dispatcher is implemented and active. It executed the five
prepared actions, published exact immutable downstream messages, resumed
original durable owners once, reconstructed state from SQLite and mailbox
authority, and completed a post-implementation candidate-to-repair chain.

`FACTORY_END_TO_END_AUTONOMY_PROVEN=PASS`.

## Dispatcher authority

- Code commit: `118bb8260113555655990a6de56e564620ea4f87`
- Code tree: `ec46276edcc973b92e76c89d0686d3d348aa8885`
- Durable journal: `runtime/t1-state.sqlite3`
- Persistence: active Codex heartbeat `t1-durable-factory-dispatcher`
- Target task: `019fb31d-6a02-7143-a822-3fa9c7e201c0`
- Poll interval: 60 seconds
- Router semantic executor: disabled so one service owns semantic execution
- Router polling, validation, cursor ownership, and mailbox consumption: unchanged

The heartbeat is the durable task owner; individual dispatcher process PIDs are
per-cycle and intentionally bounded. The latest status snapshot recorded its
cycle PID in `runtime/status.json`.

## Prepared actions

All four candidate actions produced mechanical PASS and Stable BDS PASS:

| Pack | Generation | Mechanical result | Tester result | Current downstream state |
|---|---:|---|---|---|
| Aspectweave | 9 | `MSG-T1D-ASPECTWEAVE-G000009-MECHANICAL-PASS-11D2BF1DA024` | `MSG-TESTER-000000000036-PASS` | T10 active |
| Latchline Infrastructure | 7 | `MSG-T1D-LATCHLINE-INFRASTRUCTURE-G000007-MECHANICAL-PASS-B8918AC8BFFA` | `MSG-TESTER-000000000038-PASS` | T10 backlog |
| Bounded Outcome Events | 15 | `MSG-T1D-BOUNDED-OUTCOME-EVENTS-G000015-MECHANICAL-PASS-F4045DC89BDA` | `MSG-TESTER-000000000039-PASS` | T10 queued |
| Aperture Foundry | 4 | `MSG-T1D-APERTURE-FOUNDRY-G000004-MECHANICAL-PASS-7AF58FA7D481` | `MSG-TESTER-000000000037-PASS` | T10 failed; g5 repair at owner |

Latchline's pass includes the exact 698-reachable-blob, zero-unclassified,
zero-unused-classification check. BOE's pass binds current Platform linkage.
Aperture resolves only to `aperture-foundry-reproduction-v1`.

Echo request `MSG-P13-ECHO-PLATFORM-REQUEST-000003` produced exact admission
`MSG-T1D-ECHO-G000007-PLATFORM-ADMISSION-F719FD37F136`. T2 returned
`MSG-T02-ECHO-PLATFORM-ADMISSION-RESULT-000001`, rejecting authority expansion.
T1 routed the result to Echo as
`MSG-T1D-ECHO-PLATFORM-REPAIR-2E0207673BCE`. Echo remains generation 6; no
generation-7 candidate was created or claimed.

## Durable workers

- Reliquary Vaults: original task resumed once for generation 7.
- Hearthveil: original task resumed once for generation 6.
- Hearth & Hall: original task resumed once; generation 2 was published as
  `MSG-P08-HEARTH-HALL-CANDIDATE-000002`, then passed mechanical and BDS as
  job 40.
- Aperture Foundry: original reproduction task resumed once from the new T10
  repair for generation 5.
- Vanguard Arsenal: the orphaned committed T1 repair was reconstructed and its
  original task resumed once for generation 3.
- Echo Vessels: the original task is active on a product-local Platform adapter
  repair; candidate publication remains prohibited.
- Momentum Menagerie: not resumed. No usable replacement authority is
  committed; commit `4501555d3ff5a59e7175d23ddad33aa9ea08fa71` remains the
  preserved boundary.

## Tests and safety

The targeted dispatcher suite passed 15/15. Existing router tests passed 35/35
and local tester tests passed 14/14. The dispatcher publishes only through the
canonical CAS mailbox publisher and never writes product repositories,
candidate bytes, shared runtime, BDS state, T10 results, or integration product.

One T1-generated Echo wrapper used an unrecognized message type before the
router-compatible superseding disposition was published. The immutable bad
wrapper is `MSG-T1D-ECHO-PLATFORM-REPAIR-32FF96245B1F`; it caused one
non-blocking router protocol-defect record and no product or candidate write.
The dispatcher marks its journal action `SUPERSEDED` and uses only
`MSG-T1D-ECHO-PLATFORM-REPAIR-2E0207673BCE`.

## Remaining blockers

1. Momentum lacks exact committed narrower registration or separately
   authorized owner binding.
2. Integration intake is empty because no post-implementation T10 PASS exists.
3. Latchline g7 and Hearth & Hall g2 await T10 capacity.
4. The immutable superseded Echo wrapper remains visible as one non-blocking
   router protocol defect; it does not stop cursor advancement.

The dispatcher remains active.
