---
name: oversee-java-to-bedrock-factory
description: Operate the Studio Java-to-Bedrock conversion factory from the current Codex task as the only user interface. Use when a user points a thread at a local Java modpack, asks to start or resume an automated conversion campaign, wants worker/tester/auditor threads coordinated, or wants factory status, repair, recovery, and immutable candidate routing handled without routine questions.
---

# Oversee the Java-to-Bedrock factory

Act as the conversation-facing overseer. Do not create a web UI, dashboard app,
HTTP service, or second user interface.

## Locate authority

Use the current repository root: the nearest parent containing `AGENTS.md`,
`pyproject.toml`, and `tools/factory/`. If the user supplies another checkout,
resolve and verify that root before running commands.

Require these live files before activation:

```text
.mccompiler/factory-v1/factory-config.json
.mccompiler/factory-v1/runtime/receipts/synthetic-rehearsal.json
```

Verify `overseer_interface` is `CODEX_TASK`, `activation_allowed` is true, and
the rehearsal receipt hash matches the config. Never import paths, task IDs,
mailbox history, runtime queues, credentials, or compatibility exceptions from
another checkout or machine.

## Start or resume

1. Record the exact local source path and source-inspection/operation authority.
2. Use `$make-java-to-bedrock-task-packs` to freeze intake and separate work.
3. Use `$operate-bedrock-factory-mailbox` to reconstruct the authoritative
   candidate, message, repair, and dispatch frontier.
4. Spawn only bounded, role-specific subagents for ready work. Give every agent
   one role, one assignment, one writable scope, and one completion condition.
5. Route production to `$work-bedrock-factory-pack`. Dispatch
   `$test-bedrock-factory-pack` once at `PRE_BDS_MILESTONE`, immediately before
   the first BDS run. Dispatch `$audit-bedrock-factory-pack` once at
   `FINAL_MOD_MILESTONE`, immediately before completion; observation, T10,
   T2/integration, persistence, lineage, and bundle specialists operate inside
   that single milestone packet and do not become separate queue jobs.
6. Reconcile results through committed repository/mailbox state. Do not rely on
   chat prose as durable authority.
7. Continue the loop until every pack is accepted, waiting on its proper
   external owner, or stopped by one structured non-routine block.

Default concurrency is two task-maker workers, two production workers, one
integration worker, two qualification workers, and one audit worker. These are
starting capacities, not a fixed worker-auditor-tester ratio.
Count the pre-BDS milestone and BDS runtime in `tester_workers`; reserve
`audit_workers` for the single final-mod milestone packet.

## Adapt capacity on every heartbeat

Use the durable adaptive controller on every overseer heartbeat. There must be
exactly one heartbeat owner. When the `oversee` runtime loop is active, it
advances the controller and this conversation reads `scaling-status`; use
`scaling-heartbeat` manually only when no runtime loop is active. Never advance
one logical heartbeat from both places. Count only a
`READY` packet, or a `WAITING` packet explicitly marked
`payload.capacity_blocked: true`; never count ordinary dependency waits as
capacity pressure. Pass the current live conversation-task count for every pool
with repeated `--assigned POOL=COUNT` arguments so the controller cannot exceed
a pool maximum and can release only verified idle excess tasks.

```bash
.venv/bin/bedrock-factory scaling-status \
  --state .mccompiler/factory-v1/runtime/adaptive-scaling/state.json \
  --config .mccompiler/factory-v1/factory-config.json
```

```bash
.venv/bin/bedrock-factory \
  --db .mccompiler/factory-v1/orchestration.sqlite3 \
  scaling-heartbeat \
  --state .mccompiler/factory-v1/runtime/adaptive-scaling/state.json \
  --config .mccompiler/factory-v1/factory-config.json \
  --campaign CAMPAIGN_ID \
  --assigned task_maker=COUNT \
  --assigned production_workers=COUNT \
  --assigned integration_worker=COUNT \
  --assigned tester_workers=COUNT \
  --assigned audit_workers=COUNT
```

Apply each open directive mechanically:

- `SPAWN_THREAD`: after two consecutive waiting heartbeats, spawn one
  role-specific task for the exact packet, then acknowledge the directive with
  its real task ID. Do not create a second task while that packet's directive
  remains open.
- `BACKPRESSURE_UPSTREAM`: stop admitting more work from the listed upstream
  pool until the constrained packet is claimed or the service frees capacity.
  Do not cancel leased work.
- `RELEASE_IDLE_THREAD`: after four idle heartbeats, release exactly one idle
  excess task and acknowledge it. Never interrupt an active or leased task.

```bash
.venv/bin/bedrock-factory scaling-ack \
  --state .mccompiler/factory-v1/runtime/adaptive-scaling/state.json \
  --config .mccompiler/factory-v1/factory-config.json \
  --directive DIRECTIVE_ID \
  --outcome ASSIGNED \
  --worker-task-id TASK_ID
```

Stable BDS has two proven execution slots. More tester conversation tasks do
not create Docker capacity. When both slots are occupied, obey
`BACKPRESSURE_UPSTREAM` against production instead of spawning a third BDS
task. Increase that service cap only after separately proving isolated
containers, ports, input roots, output roots, and one active test per pack.
The configured maxima are task maker 4, production 6, integration 2, audit 3,
and tester 4.

## User interaction

Use portfolio defaults and task-pack fields for routine choices. Ask the user
only for missing rights/operation authority, public publication authority, or
release/Marketplace authority. Private immutable candidate submission is not
public publication.

A mechanically validated standing campaign authority may cover routine new,
continuation, repair, recovery, and bounded T2 launches when every bound source,
rights, private-scope, security, role, lane, root, denial, and receipt field is
unchanged. If this checkout does not provide and pass that validator, obtain
explicit current authority. Always ask again for a rights, source, security
model, authenticated identity, Realms, retail client, console, publication, or
release expansion.

Report concise progress while work runs. Surface pack, generation, current
owner, last durable result, next action, and any structured block. Never ask a
production worker to obtain milestone, BDS, client, Realms, controller,
split-screen, PS4, or release PASS.

Prefer bounded vertical slices that can traverse all applicable gates. Report
candidate admitted, slice qualified, integrated, client-qualified,
console-qualified, and released as separate states. Do not reactivate a product
repair from missing observation or infrastructure alone.

## Recovery and safety

Resume from committed repositories, the SQLite store, the Git mailbox, and
hash-bound dispatch history. A sent request identity must not create a second
worker. An assigned scaling directive stays bound until its exact packet leaves
the actionable queue. Preserve rejected generation `N`; a material repair
publishes exactly `N+1`. Never retry unchanged candidate bytes. Reopen only the
repaired branch and its descendants.

Treat activation ordinal separately from candidate generation. Evidence-only
continuation and host-only recovery use new activations while preserving exact
product bytes. Never expose the host Docker socket to a sandboxed worker. Until
a controller-owned least-authority privileged-action broker exists, stop such
work as infrastructure-blocked before worker startup.

Do not claim the campaign is fully automated merely because a shadow rollout or
synthetic rehearsal passed. Require live worker delivery and the named gate
receipts for the real candidate.
