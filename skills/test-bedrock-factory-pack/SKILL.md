---
name: test-bedrock-factory-pack
description: Own the PRE_BDS_MILESTONE for one exact immutable Bedrock candidate and then run the first exact-package Stable BDS execution. Use only at this named milestone, never as a per-worker or per-activation validation job.
---

# Test one Bedrock factory pack

Remain independent of production. Verify exact candidate identity and never edit,
rebuild, repair, or replace it.

## PRE_BDS_MILESTONE

Run this broad validation exactly once before the candidate's first BDS run,
unless a bound hash changed or the prior milestone receipt is missing/invalid.
Verify exact candidate binding, deterministic build twice, package root,
manifests, icons, references, media, shipped entrypoint reachability,
restricted scans, and T1/MCTools mechanical admission. Consume the minimal
activation attestation; do not reconstruct or validate a large worker receipt.

If candidate bytes and all milestone-bound validator/config/package-authority
hashes are unchanged, reuse the existing PASS. Do not create another job.

## Stable BDS

Run only after `PRE_BDS_MILESTONE` admits the exact candidate. Use
`$qualify-bedrock-addon-bds`. Bind image/toolchain/base-world hashes, distinct
container/ports/input/output roots, logs, restart results, and exact package
hash. Never infer desktop client, Realms, controller, split-screen, console, or
release proof from BDS.

Keep candidate-only lifecycle qualification separate from instrumented or
network-player observation. Record Stable and Preview lifecycle results
separately from Stable and Preview protocol-player results. Route gameplay
collection to `$observe-bedrock-factory-pack`; a clean boot, direct hook, test
double, or mutation harness is not ordinary network-player proof.

Tag queued work mechanically with `payload.qualification_gate: STABLE_BDS`.
Stable BDS has two proven execution slots on Studio. A tester must not start a
third concurrent BDS execution or suggest that another conversation task adds
Docker capacity. Leave the packet actionable for the overseer's heartbeat
controller; at 2/2 it will backpressure production, and below 2/2 it may assign
one exact waiting packet after two consecutive heartbeats.

The BDS execution is runtime work between the two milestones, not a third
validation milestone. Classify environmental, Docker, image, host, or missing-tool failures as
infrastructure failures; do not issue a product repair for them. For a product
failure, publish structured failed fields, expected/observed values, exact
receipts, rejected generation `N`, and required replacement `N+1`. The overseer
owns reactivation and retry scheduling.
