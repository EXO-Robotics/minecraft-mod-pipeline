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

All 77 required operation names are dispatchable through the versioned registry and JSON-lines adapter. Artifact-backed analysis, intent review, planning, generation, validation, reporting, and safe-edit operations run against persistent revisioned projects. `author_blockbench_asset` accepts validated native Blockbench sources, Bedrock exports, machine visual-quality evidence, rights provenance, and deterministic revision data. `start_test_runtime` supports an explicitly authorized, immutable-image, port-free Docker BDS diagnostic adapter; installation, physical clients, multiplayer clients, and console operations remain unavailable. Tests exercise Benchmark A through create, scan, overrides, deterministic generation, validation, package, report, and reopen/resume. Full MCP transport remains incomplete.

Additional safe operations expose protected custom implementations, custom behavior-handler records, project patterns, provenance-bound IR patches, rights evidence, and mappings. Additional qualification operations expose pinned Creator Tools invocation and aggregate Marketplace-candidate evaluation; neither implies runtime execution or Marketplace approval.
