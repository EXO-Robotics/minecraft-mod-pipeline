---
name: launch-cleanroom-production-worker
description: Initialize and prove an isolated Codex production or repair worker for clean-room Java-to-Bedrock reconstruction. Use when a worker needs minimum local Codex authentication access solely for startup, a separate Git object store and filesystem lane, deny-by-default evidence controls, sanitized prompt transfer, negative-access probes, credential cleanup, and a process-bound receipt that excludes credentials from production lineage.
---

# Launch a clean-room production worker

Read [worker-receipt-contract.md](references/worker-receipt-contract.md) before
startup.

## Freeze inputs

Require:

- A validated standardized role assignment naming the exact role, skill, lane,
  gate authority, stop states, artifact hashes, and process-receipt policy.
- An independent production repository or clone with no alternates to the
  evidence repository.
- A sanitized contract hash and assignment packet.
- Explicit readable and writable roots.
- Explicit denied evidence, control, canary, history, and main-repository paths.
- A lane-local home, temp root, caches, logs, and output root.
- The exact worker command and tool inventory.

Do not start production from a clean prompt alone. Prove process and filesystem
isolation.

Never mount, expose, or proxy the host Docker socket into the worker boundary.
That would let the worker ask the host daemon to mount paths outside its lane.
Privileged host actions require a controller-owned least-authority broker that
validates an allowlisted action, exact inputs and outputs, denied paths,
cleanup, and a receipt. If no qualified broker exists, stop before worker
startup as infrastructure-blocked; do not create a product finding or candidate.

When the repository provides
`translate-java-mods-to-bedrock/scripts/validate_role_contract.py`, validate
the assignment and shared gate ledger before startup. A worker receipt cannot
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

## Launch and prove

1. Record the environment and prompt hashes without credential content.
2. Start the actual worker inside the frozen boundary.
3. From the launched process, probe every denied path and the evidence canary.
4. Require every denied probe to fail.
5. Probe approved production inputs and output paths.
6. Record process ID, launcher identity, start time, exact assignment hash, and
   output commit.
7. Search startup and production roots for `auth.json`, `installation_id`,
   credential exports, evidence paths, and canaries after launch.
8. Delete temporary authentication copies immediately after the worker is
   initialized.

Stop production if a denied probe succeeds, credential material appears in an
artifact, or the worker can reach raw Java evidence.

Bind the receipt to the validated role assignment hash. Do not accept a
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

## Validate

Run:

```bash
python3 scripts/validate_worker_receipt.py /absolute/path/worker-receipt.json
```

Then independently search the production repository and startup temp root for
forbidden filenames. The validator proves receipt shape, not operating-system
enforcement by itself.
