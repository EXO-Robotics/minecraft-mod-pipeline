# Segment Qualification and Repair Loop

Use this checklist for a connected multi-feature candidate.

## Freeze in two commits

1. Run production-local tests and static checks.
2. Build twice from clean generated output and compare every artifact hash.
3. Commit implementation, tests, package, package manifest, and production
   validation as the immutable candidate.
4. Extract the package with `git show <candidate>:<package-path>`.
5. Verify the extracted bytes against the expected SHA-256.
6. Run audits and BDS against those bytes.
7. Commit audit, BDS, candidate-manifest, provenance, and final-classification
   records in a later evidence-only commit.

Never amend the candidate after qualification starts.

## Repair propagation

For every finding:

1. Record its severity, violated oracle IDs, and invalidated gates.
2. Return an abstract defect to the isolated production lane; do not transfer
   evidence, private cases, or source identifiers.
3. Apply the smallest production-safe repair.
4. Add an integration test that crosses the boundary where the defect escaped.
5. Commit the repair in the isolated lane.
6. Transfer the unchanged repair commit into integration.
7. Produce a new candidate commit and new package hashes.
8. Rerun affected production tests, the complete authoritative oracle and
   mutations, contamination/originality, lineage/isolation, deterministic
   packaging, Stable BDS, and Preview BDS.
9. Preserve the superseded candidate commit, package hash, and audit result.

Do not stop at the first repairable audit failure.

## Production defect watchlist

Run all of these checks even when static validation or Creator Tools passes:

- Inspect BDS content logs for zero component, material, script, manifest, and
  dependency errors. Creator Tools can miss runtime component errors.
- Keep all faces in one `minecraft:material_instances` group on one render
  pipeline. Bedrock rejects mixed opaque and transparent methods. A visually
  opaque PNG may use the common blend pipeline when another face needs
  transparency.
- Use cooperative texture roots such as
  `textures/<creator-project>/<game>/blocks/` and `items/`; reject common loose
  `textures/blocks` and `textures/items` layouts when the active profile does.
- Set resource-pack `pack_scope` and reciprocal BP/RP dependencies required by
  the exact Creator Tools profile; validate the frozen `.mcaddon`, not source
  folders alone.
- Retain a persistent cleanup record until owned signal cells, paired blocks,
  or other world artifacts are actually cleared. Unloaded, blocked, successful,
  and stale-revision paths all require regressions.
- Treat external model reviews as advisory. Independently reproduce each
  critical/high finding, accept only evidence-backed defects, and preserve
  rejected or contradictory findings in the disposition record.
- Run a current-schema gate for recipe `unlock` arrays, flattened custom block
  components, stable Script API versions, reciprocal BP/RP dependencies,
  current use/consumable modifiers, and Stable/Preview divergence.
- Convert every BDS-only schema escape into a generator regression plus a
  mutation that proves the invalid form is rejected.

## Test evidence strata

Label every test as `CURRENT_CANDIDATE_GATE`,
`SUPERSEDED_CANDIDATE_EVIDENCE`, `HISTORICAL_SECTION_TEST`,
`CROSS_SECTION_INTEGRATION_TEST`, or `AUTHORITATIVE_SEMANTIC_TEST`.
Historical tests bind to immutable commits and hashes. If a later repair changes
their path or package hash, preserve them as `SUPERSEDED_ASSERTION`; do not let
stale assertions fail the current candidate and do not silently rewrite them.
Before final classification, refresh every status from receipts bound to the
final candidate hash.

## Item authority checks

For marked item operations, test together:

- event-observed same-inventory, hotbar-to-inventory, and
  inventory-to-hotbar movement;
- true loss and unmarked replacement;
- add-before-remove and remove-before-add ordering;
- duplicate events and one pending reconciliation callback maximum;
- completion, cancellation, and supersession races;
- two- and four-player ownership;
- exact tracked-slot durability write and rollback;
- absence of inventory/world scans and polling.

A controller test that passes a tracked slot is insufficient by itself. Add a
runtime/static assertion proving the inventory write uses that slot rather
than `selectedSlotIndex`.

## BDS claim boundary

Exact-package Stable/Preview restart qualification proves pack load, script
initialization, stable API compatibility at boot, and the explicit log probes.
It does not prove real item-use delivery, real multiplayer gameplay,
player-record persistence, desktop rendering, Realm behavior, controller
ergonomics, split-screen, or physical PS4 performance.

Record server binary hashes, container image digest, candidate commit, package
hash, world/pack hash, restart totals, log hashes, and critical-line count.

A separate marker pack proves that the stable Script API runtime initialized;
it does not by itself prove that candidate gameplay callbacks executed. Claim
candidate pack load only when the exact candidate is bound into the world and
its content log is clean. Prove semantics through the private oracle and direct
candidate-module tests.
