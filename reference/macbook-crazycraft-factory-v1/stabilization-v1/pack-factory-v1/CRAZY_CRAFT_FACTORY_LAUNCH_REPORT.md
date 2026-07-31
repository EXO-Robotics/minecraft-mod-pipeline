# Crazy Craft Factory Launch Report

Updated after committed resume: `2026-07-29T20:26:53Z`

## Outcome

The pack-production factory is executing under append-only resume decision
`FD-T01-PACK-FACTORY-RESUME-0001`, supervisor commit
`34d78ad14d0112e6a5eb010cc4e9fc34645e13e9`, tree
`63bc75d9a1286d3ab4dbbffe85bb33dd0f2c05e1`. The decision changes run control
only: all durable assignments, candidates, worktrees, and prior receipts remain
valid and were not restarted.

All ten visible pack owners accepted the resume authority. Eight currently have
active Codex turns; Hearthveil is waiting through its resumed mailbox automation
after publishing generation 2, and T10 is idle by design because no new candidate
has yet crossed its mechanical-admission boundary. T2 is active on bounded
shared-runtime and integration requests.

`FACTORY_LAUNCHED=PASS`. The persistent MacBook tester is running as PID `20295`
with two global slots and one slot per pack. On restart it recovered publication
for already-executed Reliquary `JOB-000000000019` without rerunning BDS and
published immutable `MSG-TESTER-000000000019-PASS`. No product candidate was
changed by service recovery or task resume.

## Live service authority

- Resume decision: `34d78ad14d0112e6a5eb010cc4e9fc34645e13e9`
  / `63bc75d9a1286d3ab4dbbffe85bb33dd0f2c05e1`.
- Mailbox head after launch validation:
  `a3455fcbc8ed71b46bbf13f648a6f5cdd9c4f5c2`
  / `aa00a05128d5349fe3086f10561e728fb9132bdc`.
- Tester service receipt for Reliquary:
  `9e8ccbd2a793e90d499602abaf7d41da397164fccd6a56bf250dfe692e83299d`.
- Reliquary result-message SHA-256:
  `489bcc38d41905f71497eeda05b84cb48bb71e05f8f7a5b045fd767661652a3e`.
- T2 head: `7708d3b84120261ce9bebae9f0a1f55db3961936`
  / `2c6a40cc767a4dbf8e3a484ddef9d82f708c5ebc`.
- T10 head: `b458c6b92a71be47ae87ef4b1c015c702ed3bed2`
  / `1a27754c6c0cbc576ce1b483d3d056a58427a346`.

## Durable pack owners

| Pack | Task | Assignment | State | Product progress |
|---|---|---|---|---|
| Reliquary Vaults | `019fae2a-1ba8-71b1-a5f9-8025bbff1430` | `PA-07-RELIQUARY_VAULTS-V1` | ACTIVE | Generation 2 published; recovered real Stable BDS `TEST_PASS`; remaining audit/integration work active. |
| Hearth & Hall | `019fae2a-1e88-7a43-aae5-238305c09a85` | `PA-08-HEARTH_AND_HALL-V1` | ACTIVE | 44 blocks, 6 items, 50 recipes, 44 loot tables, persistence/recovery runtime, and 15/15 focused tests; assets active. |
| Hearthveil | `019fae2a-2119-7543-aee8-72b261a0db66` | `PA-09-HEARTHVEIL-V1` | WAITING_TESTER | Generation 2 remains immutable; resumed mailbox automation is waiting for a tester or repair result. |
| Aspectweave | `019fae2a-2394-7c23-8a00-090d630e4087` | `PA-10-ASPECTWEAVE-V1` | ACTIVE | Candidate is committed and factory routing is active. |
| Vanguard Arsenal | `019fae2a-3694-7271-9168-ee644d4886a1` | `PA-11-VANGUARD_ARSENAL-V1` | ACTIVE | Generation 2 is published and the bounded repair/routing lifecycle is active. |
| Aperture Foundry | `019fae2a-2ba4-7710-ab61-54ce7e6f9bd1` | `PA-12-APERTURE_FOUNDRY-V1` | ACTIVE_FAIL_CLOSED | Immutable C0 exists; publication waits for canonical scan, receipt, and message authority. |
| Echo Vessels | `019fae2a-31a5-7443-80d9-406c4aa09888` | `PA-13-ECHO_VESSELS-V1` | ACTIVE_WAITING_RESULT | Generation 3 is published and immutable; no duplicate candidate was created on resume. |
| Bounded Outcome Events | `019fae2a-2955-72e2-b3c4-618cb1f1ad10` | `PA-14-BOUNDED_OUTCOME_EVENTS-V1` | ACTIVE | Generation 4 is published and its bounded Platform request is active. |
| Momentum Menagerie | `019fae2a-2edf-7b83-9706-b4a7e88d0560` | `PA-15-MOMENTUM_MENAGERIE-V1` | ACTIVE | Runtime and five runtime-to-visual identities are under reconciliation with 23 preserved editable variants; candidate tooling active. |
| Latchline Infrastructure | `019fae2a-265c-7163-967f-6076198a1f05` | `PA-16-LATCHLINE_INFRASTRUCTURE-V1` | ACTIVE | Generation 3 is published and factory routing is active. |


## Existing-candidate tester closure

- Trailbound Packs: preserved Stable pass, `MSG-T09-TRAILBOUND-BDS-RESULT-000005`.
- Pocketbound Companions: Stable pass, `MSG-TESTER-000000000017-PASS`.
- Wayfarer Settlements: Stable pass, `MSG-TESTER-000000000018-PASS`.
- Reliquary Vaults generation 2: Stable pass,
  `MSG-TESTER-000000000019-PASS`; publication was recovered from complete
  execution evidence without rerunning BDS.
- Catalyst Wilds: blocked before intake because no exact committed BP/RP tuple or
  approved flat-addon profile exists in the preserved authority.

The first Pocketbound/Wayfarer requests failed closed as infrastructure because the
request profiles omitted their declared script modules. Linked retries declared
`scripts/main.js`, retained the same exact candidate hashes, and passed.

## Proof boundaries

The launch proves committed run-control resume, durable task activation,
substantive Bedrock authoring, mailbox consumption, and exact Stable BDS
load/restart for the named candidates—including Reliquary generation 2. It does
not prove completion for an unfinished pack, Preview, client rendering, audio,
controller, multiplayer, Realm, split-screen, physical console, rights, branding,
Marketplace, release, combined integration, or final portfolio result.

Mac Studio remains optional overflow capacity and is not a scheduling blocker.

## Mechanical routing

Factory validation rejected Echo generation 3 before T10 because its mailbox
envelope omitted the canonical top-level `artifact_manifest` and `tests`
objects. T1 published immutable correction instruction
`MSG-T01-ECHO-MECHANICAL-REPAIR-000002`; Echo consumed it and published linked
generation 4 as `MSG-P10-ECHO-CANDIDATE-000004`. The replacement preserves
content A `e64be610288de02626430e2633afa839da442377`, metadata B
`d36189c771de3cd63795c7d092257649e1107d1d`, and every exact package hash while
adding the required canonical fields. This is one mechanically routed envelope
correction, not a product failure and not a factory-wide blocker.
