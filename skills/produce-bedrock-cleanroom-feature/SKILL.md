---
name: produce-bedrock-cleanroom-feature
description: Independently implement an original Bedrock feature or bounded feature slice from a sanitized production contract inside an isolated production lane. Use when a production subagent must create stable-API behavior/resource packs, original assets, local tests, deterministic packages, provenance, and a frozen candidate without access to Java evidence or the private semantic oracle.
---

# Produce a Bedrock Clean-Room Feature

Require a standardized assignment for role `feature_producer`, skill
`produce-bedrock-cleanroom-feature`, and lane `PRODUCTION`. Validate it with
`$translate-java-mods-to-bedrock`'s role-contract validator.
`requires_process_receipt` must be true.

Operate only inside the assigned production worktree. The sanitized contract and
production oracle interface are the sole semantic authority.

## Run production preflight

Require `PRODUCTION_SANDBOX_PREFLIGHT` and launch this actual agent through the
recorded sandbox executor. Verify lane-local `HOME`, `TMPDIR`, caches, logs, and
indexes; absent remotes/alternates; denied evidence, control, private oracle,
and canary; and the approved network policy. Record PID, command,
prompt/context hash, tool hashes, timestamps, exit status, and input hashes.
Stop with `CLEANROOM_BOUNDARY_FAILED` when that process receipt is missing.

1. Validate the assignment packet and exact input hashes.
2. Verify the baseline commit, branch, worktree, remotes, and Git alternates.
3. Prove the evidence vault, control plane, private oracle, hidden canary, shared
   caches, and source-only identifiers are denied or absent.
4. Confirm only assigned output paths are writable.
5. Stop with `PRODUCTION_INPUT_INTEGRITY_FAILED` or
   `PRODUCTION_ISOLATION_INVALIDATED` on any mismatch.

Do not search for the Java source or infer its identity. Do not ask the main
agent to summarize source behavior beyond the sanitized contract.

## Implement Bedrock-native behavior

- Prefer native components, states, permutations, recipes, loot, and stable
  `@minecraft/server` events.
- Use server-authoritative, event-driven state with explicit caps.
- Use versioned persistent records only when required.
- Guard callbacks with generation or operation IDs.
- Bound scans, queues, records, entities, projectiles, particles, and cleanup.
- Separate collision, appearance, redstone, ownership, and persistence.
- Replace unsupported Java rendering, GUI, keybind, or world behavior with only
  the approved original substitute.
- Use controller-simple interactions and conservative console budgets.

For persistent block devices, retain cleanup records until owned world artifacts
are cleared. For item operations, bind authority to player and item identity as
required; never rely only on selected slot or item type.

Implement and record a public reachability path:

`acquisition/spawn → registered event/component → authoritative handler →
state transition → reward/persistence → cleanup`.

Do not mark exported functions or stress-only summon fixtures as player-facing.
If client delivery cannot be exercised locally, pass direct/runtime tests but
record `CLIENT_EVENT_DELIVERY_PENDING`.

## Create original presentation

Create original namespaces, identifiers, textures, localization, models,
animations, particles, and sounds. Use Blockbench only when geometry, rigging,
UVs, locators, or animation materially require it; otherwise record
`NOT_APPLICABLE`.

When Blockbench is applicable, invoke `$produce-golden-blockbench-asset` with
the typed visual contract and class profile from the production packet. Do not
send it evidence, control references, or private oracle cases. Consume only its
frozen asset commit, export hashes, proof inventory, provenance, and
production-local validation results.

## Validate locally

Label tests `PRODUCTION_LOCAL`. Cover state transitions, invalid input,
duplicates, stale callbacks, lifecycle cleanup, persistence, two/four-player
isolation, and caps. Run JSON, manifest, UUID, namespace, stable-API, asset,
localization, provenance, pack-load, script-load, and `git diff --check`
validation. Run the pack-hazard validator from
`$translate-java-mods-to-bedrock`.

Build twice from clean generated outputs and require matching hashes. Creator
Tools and local BDS smoke tests are complementary; inspect content logs.

Run current-schema checks for recipe unlock arrays, flattened custom
components, stable API versions, reciprocal pack dependencies, and current
use/consumable modifiers. Turn every BDS-only schema escape into a static
regression and mutation. Every repair must be performed by a newly
receipt-bound sandboxed process. Preserve the superseded commit and label
obsolete path/hash tests `SUPERSEDED_ASSERTION`.

Pin every Script API event member to the declared stable module version. Reject
removed registrations and defer restricted-mode mutations through a supported
scheduler. Add a module-registration smoke test, not only syntax parsing.

## Freeze without overclaiming

Commit the candidate and deterministic artifacts, record package hashes and
provenance, and leave a clean worktree. Do not amend a frozen candidate.
Return `CANDIDATE_READY_FOR_INDEPENDENT_AUDIT` only when all production-local
gates pass. Keep semantic preservation, contamination, originality,
authoritative BDS, desktop, Realm, PS4, distribution, and Marketplace status
explicitly unaudited or pending.
