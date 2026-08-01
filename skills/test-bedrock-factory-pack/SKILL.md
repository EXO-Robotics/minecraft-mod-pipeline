---
name: test-bedrock-factory-pack
description: Qualify one exact immutable Bedrock factory candidate through T1 mechanical preflight and, when admitted, Stable BDS testing. Use for hash-bound candidate validation, deterministic Docker/BDS qualification, product-versus-infrastructure failure classification, or consolidated repair generation without modifying candidate bytes.
---

# Test one Bedrock factory pack

Remain independent of production. Verify exact candidate identity and never edit,
rebuild, repair, or replace it.

## T1 mechanical preflight

Use `$qualify-bedrock-candidate`. Verify immutable generation, artifact and
manifest hashes, package structure, references, media, scripts, restricted
scans, production commit/tree, deterministic build authority, and isolation
receipt. Publish a hash-bound PASS or one consolidated product failure.

## Stable BDS

Run only after T1 admits the exact candidate. Use
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

Classify environmental, Docker, image, host, or missing-tool failures as
infrastructure failures; do not issue a product repair for them. For a product
failure, publish structured failed fields, expected/observed values, exact
receipts, rejected generation `N`, and required replacement `N+1`. The overseer
owns reactivation and retry scheduling.
