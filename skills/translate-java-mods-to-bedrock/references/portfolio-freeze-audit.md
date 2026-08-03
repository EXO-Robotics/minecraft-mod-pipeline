# Portfolio Freeze and Audit

Use this reference for full-mod inventory reconciliation, private-oracle
mutation campaigns, partial freezes, and final promotion decisions.

## Reconcile the inventory

Preserve two count systems:

- Raw declarations: classes, registry entries, recipes, structures, and
  generation routines actually inventoried.
- Logical roles: player-facing or shared-system responsibilities suitable for
  product selection.

Assign every raw entry exactly one final disposition:

- `IMPLEMENTED`
- `MERGED_INTO_PRODUCT_FEATURE`
- `REDESIGNED_FOR_BEDROCK`
- `SUPERSEDED_BY_SHARED_SYSTEM`
- `DEFERRED_CLIENT_OR_PLATFORM_BOUNDARY`
- `EVIDENCE_INSUFFICIENT`
- `RIGHTS_NOT_AUTHORIZED`
- `NOT_PRODUCT_RELEVANT`

Require a product counterpart and qualification reference for each implemented,
merged, redesigned, or superseded entry. A difficult feature may be deferred
only when the record names a real evidence, rights, stable-API, performance, or
client boundary.

## Validate the private oracle

Freeze requirements before production. After candidate freeze:

1. Run the oracle against the unmutated exact candidate.
2. Require zero baseline failures for the requirement surface under mutation.
3. Copy the candidate into a fresh temporary root for each mutation.
4. Mutate only the named requirement boundary.
5. Require the expected requirement ID to transition from pass to fail.
6. Record other failures, but do not count them as the kill.
7. Mark a case `INCONCLUSIVE` if the expected failure existed at baseline.
8. Bind results to candidate commit, package SHA-256, oracle SHA-256, harness
   commit, and case inventory.

Do not count production-local mutations as authoritative-oracle mutations
unless the frozen oracle explicitly maps them. Fix a flawed auditor harness and
rerun from a clean baseline; do not preserve a convenient false positive.

## Bind exact packages

Extract candidate bytes from the immutable candidate commit. Record BP, RP, and
combined package hashes in every MCTools, BDS, determinism, audit, and freeze
receipt. BDS evidence may carry forward across a test-only or report-only commit
only when:

- BP, RP, and combined SHA-256 values are byte-identical.
- No pack member changed.
- The new commit is recorded as metadata-only.
- The original package-bound receipt remains preserved.

Any package-affecting repair creates a replacement candidate and invalidates all
dependent gates.

## Separate technical and clean-room gates

Audit independently:

- Exact package and Git binding
- Frozen semantic oracle
- Deterministic packaging
- MCTools/Creator Tools
- Stable and Preview BDS
- Static contamination scan
- Originality evidence
- Actual production-process isolation
- Repair activation attestations
- Clean-room ancestry and lineage

No prohibited expression detected is narrower than copying prevention proven.
A clean prompt, standalone repository, or later deterministic rebuild cannot
retroactively prove isolated authorship.

## Freeze honestly

Create a full-success tag only when every required semantic, isolation,
lineage, originality, deterministic, Stable BDS, and Preview BDS gate passes.

When useful exact artifacts pass technical qualification but a non-waivable
gate fails:

- Preserve the candidate as a partial freeze.
- Record the primary partial classification and each hard substatus.
- Preserve superseded candidates, package hashes, qualification receipts, and
  audit findings.
- Do not create the full-success tag.
- Keep desktop client, controller, Realm, split-screen, physical PS4,
  Marketplace, and release statuses independent.
