# Current Bedrock schema and regression gates

Validate the exact generated package against the current Stable and Preview
BDS schemas. Do not rely on source-folder JSON parsing alone.

## Mandatory static checks

- Every current-format recipe has a deterministic non-empty `unlock` array
  bound to a valid ingredient or approved context.
- Custom block components use the current flattened namespaced component form;
  reject obsolete `minecraft:custom_components` unless the pinned target
  explicitly requires it.
- `@minecraft/server` uses the frozen stable version; reject experiments unless
  the product requirement is explicitly blocked without them.
- BP and RP dependencies are reciprocal and UUID/version compatible.
- Manifest `min_engine_version`, module types, UUIDs, and pack scope match the
  frozen current-platform profile.
- Consumables use current `minecraft:use_modifiers` and supported consumable
  components; reject obsolete item-use fields.
- Texture roots, render methods, geometry, animation/controller bindings,
  localization keys, and structure references resolve inside the exact archive.
- Stable and Preview schema divergence is recorded separately.

## BDS escape-to-regression loop

For each content-log error:

1. Preserve the candidate, package hash, server version, and exact log line.
2. Reproduce the fault in the generator or validator.
3. Repair the generator, not only its generated output.
4. Add a static test for the required schema.
5. Add a mutation that deletes or corrupts the required field.
6. Require the mutation to be killed.
7. Build twice, freeze a replacement candidate, and rerun Stable and Preview.

No schema warning is “non-material” merely because pack probes later succeed.

## Test strata

Keep these suites distinct:

- `CURRENT_CANDIDATE_GATE`: exact current commit and package.
- `SUPERSEDED_CANDIDATE_EVIDENCE`: immutable failures and repair lineage.
- `HISTORICAL_SECTION_TEST`: immutable section commit or recorded artifact.
- `CROSS_SECTION_INTEGRATION`: current promoted dependency graph.
- `AUTHORITATIVE_SEMANTIC`: private oracle and hidden mutations.

Historical tests must validate immutable commits or recorded hashes. If a later
repair intentionally invalidates their mutable path assumptions, classify the
assertion `SUPERSEDED_ASSERTION` with its original commit and reason. Do not let
it masquerade as a current-candidate failure, and do not silently delete it.

Before final reporting, refresh all status/readiness documents from the frozen
candidate and audit receipts. Stale “not started” or old-candidate claims fail
`FINAL_STATUS_REFRESH`.
