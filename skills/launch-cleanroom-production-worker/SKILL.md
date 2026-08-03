---
name: launch-cleanroom-production-worker
description: Launch an isolated Codex production or repair activation using a separately qualified platform and emit one minimal activation attestation. Use for ordinary reconstruction work between the two validation milestones.
---

# Launch a clean-room production worker

Read [activation-attestation-contract.md](references/activation-attestation-contract.md) before
startup.

## Freeze inputs

Require:

- A validated standardized role assignment naming the exact role, skill, lane,
  gate authority, stop states, artifact hashes, and activation-attestation policy.
- An independent production repository or clone with no alternates to the
  evidence repository.
- A sanitized contract hash and assignment packet.
- Explicit readable and writable roots.
- Explicit denied evidence, control, canary, history, and main-repository paths.
- A lane-local home, temp root, caches, logs, and output root.
- The exact worker command and tool inventory.

Do not start production from a clean prompt alone. Require a PASS platform
qualification bound to the exact launcher and security model.

Never mount, expose, or proxy the host Docker socket into the worker boundary.
That would let the worker ask the host daemon to mount paths outside its lane.
Privileged host actions require a controller-owned least-authority broker that
validates an allowlisted action, exact inputs and outputs, denied paths,
cleanup, and a receipt. If no qualified broker exists, stop before worker
startup as infrastructure-blocked; do not create a product finding or candidate.

When the repository provides
`translate-java-mods-to-bedrock/scripts/validate_role_contract.py`, validate
the assignment and shared gate ledger before startup. An activation attestation cannot
repair an invalid or ambiguous assignment.

## Handle authentication minimally

When the user explicitly authorizes local Codex authentication for worker
startup:

1. Grant read access only to the exact approved authentication files and
   minimum startup metadata.
2. Keep authentication handling outside the production repository and artifact
   lineage.
3. Never print, hash, serialize, copy into prompts, or include authentication
   values in receipts.
4. Do not read unrelated sessions, prompts, history, or agent metadata.
5. If a temporary copy is unavoidable, place it in the lane-local startup area,
   restrict its permissions, start the worker, and delete it immediately.
6. Record only boolean facts such as `authentication_used_for_startup: true`
   and `temporary_auth_copies_remaining: false`.

Never broaden this permission to evidence or control access.

## Launch

1. Hash-bind the existing platform-qualification receipt.
2. Start the worker inside the already-qualified boundary.
3. Enforce cheap assignment, path, ref, and input-hash invariants.
4. Delete activation-owned temporary cache material.
5. Emit only the minimal activation attestation.

Do not rerun denial/network/path canaries, full environment inventories,
package scans, deterministic rebuilds, or receipt validators for every worker.
Those platform checks belong to platform qualification; package checks belong
to `PRE_BDS_MILESTONE`.

Stop production if a denied probe succeeds, credential material appears in an
artifact, or the worker can reach raw Java evidence.

Bind the attestation to the validated role assignment hash. Do not accept a
successful process launch as authority to pass a gate the assignment did not
delegate.

A standing campaign authority may satisfy routine launch authority only when a
repository-owned validator binds its exact security model, lane, role, roots,
denials, source scope, and receipt policy to this activation. If the validator
is absent or any bound field changed, require explicit current authority.

## Repair workers

Use the same or a newly frozen equivalent boundary. A repair receipt must bind
the superseded candidate, abstract defect, authorized changed paths, new
candidate, and cleanup proof. Never let a repair worker read the private oracle
or hidden test that found the defect.

Do not dispatch a worker-receipt validator. The controller records the bounded
attestation mechanically and defers broad validation to the two milestones.
