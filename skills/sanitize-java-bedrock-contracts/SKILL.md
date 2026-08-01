---
name: sanitize-java-bedrock-contracts
description: Convert evidence-backed Java behavior claims into product-selected Bedrock requirements, equivalence classes, a private semantic oracle, a restricted production interface, and sanitized clean-room contracts. Use when a control-plane subagent must freeze the source-to-abstract-to-product boundary before Bedrock production. Do not use for Java evidence collection or production implementation.
---

# Sanitize Java-Bedrock Contracts

Require a standardized assignment for role `contract_steward`, skill
`sanitize-java-bedrock-contracts`, and lane `CONTROL`. Validate it with
`$translate-java-mods-to-bedrock`'s
`references/role-contract-standard.md` and validator before transformation.

Operate as the product selector, test authority, and sanitizer. Keep private
oracle material separate from production-facing artifacts.

## Verify inputs

Require an assignment packet plus:

- Evidence-claim bundle and contradictions.
- Rights restrictions and production-visibility labels.
- Product scope, Bedrock/PS4 constraints, and namespace allocation.
- Immutable evidence-manifest and claim-bundle hashes.

Reject inputs that omit uncertainty, rights scope, or lineage. Do not inspect
more source than the assignment permits.

## Perform the three-stage transformation

For every accepted behavior, record:

1. Evidence-backed source observation.
2. Abstract semantic requirement.
3. Product-selected production requirement.

Classify product decisions as `REQUIRED`, `OPTIONAL`, `REDESIGNED`, `OMITTED`,
or `MORE_EVIDENCE_REQUIRED`. Classify accepted requirements as
`EXACT_INVARIANT`, `RANGE_EQUIVALENT`, `FUNCTIONALLY_EQUIVALENT`,
`INTENTIONALLY_REDESIGNED`, or `OMITTED_WITH_APPROVAL`.

Use ranges and invariants instead of unnecessary exact constants or source
ordering. Resolve Bedrock-native lifecycle and safety behavior explicitly and
label it as product policy rather than source equivalence.

## Freeze two oracle surfaces

Keep the private semantic oracle outside production. Include hidden edge cases,
mutation tests, tolerances, exceptional transitions, and failure
classifications.

Give production only the oracle interface needed to implement safely:

- Required states, outcomes, and public timing ranges.
- Multiplayer ownership and lifecycle rules.
- Performance, cleanup, persistence, and compatibility limits.
- Original presentation requirements.

When custom visual production is required, also freeze a typed visual contract:

- Class-specific scale, bounds, silhouette, rig, animation, texture/material,
  performance, and proof-render sections.
- Semantic bone and locator roles without source bone names.
- Timing ranges and state requirements without unnecessary exact source values.
- Prohibited resemblance cues expressed abstractly.
- Automated heuristic thresholds and the public art-direction rubric.

The producer must not receive private test cases or source-facing rationale.

## Sanitize the contract

Reject or remove:

- Source project, feature, class, method, namespace, and asset names.
- Java paths, prose, comments, localization, screenshots, and sounds.
- Distinctive layouts, visual descriptions, identifiers, and ordering.
- Unnecessary exact timings, coordinates, or implementation structure.
- Evidence references, hashes, and private-oracle material.

Require original Bedrock identity and presentation. Hash the product selection,
equivalence table, private oracle, production interface, and contract
independently.

Keep exact control geometry, texture, palette, animation timings, and
originality comparison cases private. If a later audit detects a collision,
issue only an opaque finding with the public contract range and affected gates;
never pass the control value or evidence back to production.

## Transfer and stop

Create a hash-bound transfer receipt and a production assignment packet that
contains only approved production inputs, baseline commit, allowed paths,
budgets, and stop states. Return `CONTRACT_SANITIZED` only when leakage scans and
lineage checks pass. Stop before implementation with
`CONTRACT_REPAIR_REQUIRED`, `EXPRESSION_LEAK_DETECTED`,
`SEMANTIC_ORACLE_UNDERDEFINED`, or `PILOT_READY_FOR_CLEANROOM_PRODUCTION`.
