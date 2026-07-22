# AI tool interface

## Contract

The planned interface is a deterministic application service shared by CLI and an MCP-equivalent adapter. JSON stdout contains one versioned response; human logs use stderr. Mutations require project revision checks and record actor, authority, evidence, reason, timestamp, and before/after digests.

```json
{
  "schema_version": "1.0.0",
  "operation": "inspect_behavior",
  "ok": true,
  "project_revision": 17,
  "result": {},
  "diagnostics": [],
  "artifacts": [],
  "provenance": {}
}
```

## Operation families

- Project: create/open/status, unresolved work, blocking failures, next task.
- Analysis: scan mod/modpack, list/inspect content and loader constructs, trace dependencies/calls, show evidence, compare source/JAR.
- Intent: extract/propose/accept/edit/reject intent and list ambiguity or unsupported operations.
- Planning: compare strategies, plan a feature, approve/reject approximations, record redesigns, apply overrides, estimate fidelity/performance.
- Generation: feature scaffolds, scripts, packs, world, and `.mcaddon`.
- Validation: IR, symbols, target, rights, static/script/assets/performance, runtime, multiplayer, persistence, logs, expected behavior, reports.
- Safe editing: protected custom implementations, pattern additions, provenance-bearing patches, mappings, and rights evidence.

## Trust model

AI proposals are advisory. Acceptance is a distinct authorized action. Rights clearance is human-only. Every focused query returns stable IDs and evidence references rather than requiring an agent to ingest the entire IR. Protected custom work is never overwritten by generation.

## Current status

The current worktree includes a versioned operation registry, JSON envelopes, a JSON-lines stdio adapter, project create/status/open/unresolved/blocking/next-task operations, focused behavior/evidence queries, and strategy decisions. Tests prove create/scan/resume/query/revision-conflict and shared adapter behavior. Most operation families listed above remain unimplemented, and there is no complete MCP transport or end-to-end conversion-project workflow yet.
