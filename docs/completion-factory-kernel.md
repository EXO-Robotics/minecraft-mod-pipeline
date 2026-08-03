# Completion Factory Kernel

The reusable product in this repository is not a Minecraft worker. It is a
completion system in which an exact artifact advances only when a named
authority, an independent gate, and a bounded claim agree.

```text
frozen work order
  -> bounded producer
  -> immutable artifact
  -> mechanical admission
  -> real-runtime execution
  -> independent evaluation
  -> explicit repair or promotion
  -> integration
  -> environment, human, publication, or release gate
```

## Kernel responsibilities

The kernel owns authority, typed identities, immutable artifact registration,
the canonical append-only event stream, rebuildable projections, dependency and
gate graphs, role policy, hash-bound dispatch, minimal activation attestations, platform
qualification, queue backpressure, metrics, promotion boundaries, and portable
regression fixtures.

Broad validation is restricted to `PRE_BDS_MILESTONE` and
`FINAL_MOD_MILESTONE`. Cheap identity, hash, path, lease, and append-only
invariants remain always on; they are not separate validation jobs.

Minecraft Java evidence, Bedrock T1/MCTools/BDS, protocol observation, and
Blockbench authoring are domain adapters. Blockbench-native authoring is useful
but optional; it is not part of the minimum orchestration kernel.

Other adapters can bind the same kernel to iOS build/simulator/device gates,
OCR and ML blind benchmarks, Unreal PIE/package validation, CAD validation,
machine-production files, robotics simulation, or hardware-in-the-loop tests.

## Evidence-enabling candidates

An `EVIDENCE_ENABLING_REPLACEMENT` changes candidate bytes for a bounded
observability purpose. It receives a new `C#` identity and reruns every gate
affected by those bytes, but it does not automatically reject its predecessor.
A failure of its declared diagnostic behavior applies to that diagnostic
candidate. It does not authorize another candidate automatically. Promotion to
product authority is a separate adjudication.

Control-only `INFRASTRUCTURE_ONLY_RETRY` and `HOST_AUTHORITY_REBIND` transitions
use a new `A#`, preserve candidate bytes and `C#`, and rerun only the affected
host binding or receipt checks.

## Integration trains

Start a bounded integration train when either:

- three accepted slices have accumulated since the prior train; or
- one accepted slice changes a shared runtime interface.

The first train checks combined startup, unique event subscription, shared
property registration, two-identity ownership, restart, duplicate prevention,
shared budgets, resource-pack merging, identifier collisions, and migration
order. It does not need to wait for the whole portfolio.

## Full and slice oracle layers

A full oracle qualification is periodic platform confidence. An active slice
references a projection containing only its required behaviors and dependency
closure. Full-oracle evidence is reusable only while source authority, oracle
implementation, and comparison-rule hashes remain exact.

## Assurance profiles

- `LIGHTWEIGHT`: reversible work order, implementation, local tests, review,
  merge.
- `STANDARD_PRODUCT`: immutable candidate, CI admission, runtime execution,
  independent evaluation, staged integration and release.
- `HIGH_ASSURANCE`: source/evidence isolation, sanitized contract,
  least-authority production, independent mechanical/runtime/semantic and
  hidden gates, explicit integration, and physical/human/release authority.

The profile reduces unnecessary ceremony for low-risk work without weakening
high-assurance boundaries where false completion is costly.
