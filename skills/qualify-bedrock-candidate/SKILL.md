---
name: qualify-bedrock-candidate
description: Qualify an immutable Minecraft Bedrock candidate package with exact-hash Stable and Preview Bedrock Dedicated Server execution, bounded probes, restart, persistence, stress, cleanup, and simulated-player diagnostics. Use when a Java-to-Bedrock production or integration candidate is frozen and Codex must generate authoritative BDS receipts without claiming desktop, Realm, controller, split-screen, physical PS4, or Marketplace approval.
---

# Qualify a Bedrock Candidate

Operate as a read-only qualification role. Do not modify the candidate, packs,
world, source, or frozen commit. Write only runner-local logs and receipts.

Require a standardized assignment for role `bds_qualifier`, skill
`qualify-bedrock-candidate`, and lane `AUDIT`. Validate it with
`$translate-java-mods-to-bedrock`'s
`references/role-contract-standard.md` and validator.

Use `$qualify-bedrock-addon-bds` as the exact-package execution harness. Its
architecture inspection, MCTools log binding, deterministic package checks,
and diagnostic controls belong to this single milestone execution; do not
dispatch any of them as separate recurring validation jobs.

## Bind the immutable candidate

Require:

- Candidate commit and clean repository identity.
- Expected BP, RP, `.mcaddon`, `.mcworld`, and combined-package SHA-256 values.
- Pinned Stable and Preview BDS versions and container image digests.
- Explicit script-runtime or asset-only policy.
- Bounded restart count, observation time, probes, entity/projectile load, and
  cleanup target.
- Expected log markers and forbidden content-error patterns.

Extract candidate bytes from the immutable commit. Recompute every hash and stop
on mismatch. Never qualify a mutable working-tree package.

## Run Stable BDS

Use an isolated Docker volume, publish no gameplay ports, and permit bootstrap
network only when explicitly authorized to download the pinned server version.
Record the container digest, BDS binary version, candidate hashes, commands,
timestamps, exit status, raw content log hash, and normalized result.

Run the assigned restart cycles. Require clean pack loading, reciprocal BP/RP
dependencies, stable Script API initialization when scripts exist, persistence
checkpoint recovery, and zero candidate-scoped content errors.

Stop a declared ledger on the first disqualifying failure. Do not repeat
unchanged candidate bytes to manufacture a passing streak. Preserve that
ledger, run separately labeled packless/minimal/architecture controls, and
require a material repair or architecture change before opening a new
qualification ledger.

For asset-only candidates, require clean entity/pack loading and bounded probes
without inventing a script marker.

## Run Preview diagnostics

Keep Preview/GameTest content in a separate never-ship diagnostic package.
Exercise only the assignment's bounded simulated-player, interaction,
concurrency, stress, persistence, migration, cleanup, and restart probes.

Classify known SimulatedPlayer gaps as harness limitations. Accepted simulated
calls that do not deliver the production event payload are not gameplay passes.

## Emit the gate ledger

Emit separate gate records for:

- Stable exact-package boot/load.
- Stable restart and persistence.
- Preview diagnostic initialization.
- Each simulated behavior actually observed.
- Stress caps and cleanup-to-zero.
- Deterministic candidate identity.

Every passed record must name its authority, exact artifact hash, receipt, and
narrow evidence classification. Use only standardized gate statuses.

Return BDS schema/content defects as generator escapes bound to the failed
candidate and log. Do not repair them. The controller must issue a new
production or integration assignment, preserve the superseded candidate, and
rerun affected gates.

Validate the final receipt, qualification metadata, MCTools log, repository
commit, and package path with
`qualify-bedrock-addon-bds/scripts/validate_bds_receipt.py`.

## Report limitations

BDS and Preview diagnostics do not establish client rendering, normal physical
player input, real multiplayer identity/reconnect, Realm transfer, controller
focus, split-screen, physical PS4 performance, rights clearance, Marketplace
submission, or Marketplace approval. Keep each unexecuted surface `PENDING`.
