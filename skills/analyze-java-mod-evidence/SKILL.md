---
name: analyze-java-mod-evidence
description: Analyze an authorized Java mod feature inside an evidence-only lane and produce traceable behavior claims, contradictions, dependency boundaries, rights annotations, and Bedrock feasibility notes. Use when a subagent is assigned source intake, static or runtime Java analysis, or feature decomposition for a clean-room Java-to-Bedrock conversion. Never use this skill in a Bedrock production lane.
---

# Analyze Java Mod Evidence

Require a standardized assignment for role `evidence_analyst`, skill
`analyze-java-mod-evidence`, and lane `EVIDENCE`. Validate it with
`$translate-java-mods-to-bedrock`'s
`references/role-contract-standard.md` and validator before analysis.

Operate only as the evidence analyst. Do not implement Bedrock content or make
final product-selection decisions.

## Start from the assignment packet

Require one assignment JSON containing:

- `assignment_id`, `role`, `lane_root`, and allowed output paths.
- Immutable source identity, commit/archive hash, and feature IDs.
- Rights-operation matrix and permitted analysis methods.
- Dependency-closure limit and requested evidence questions.
- Prohibited paths, stop states, and expected deliverables.

Fail closed when the source identity, required analysis right, or lane boundary
is unresolved. Do not expand from the assigned feature into the whole mod merely
because related files are interesting.

## Establish the evidence boundary

1. Verify source and license hashes before analysis.
2. Record every source file, runtime capture, document, and dependency inspected.
3. Use only analysis methods explicitly permitted by the rights matrix.
4. Keep Java names, assets, paths, prose, screenshots, and implementation notes
   inside the evidence lane.
5. Never open or modify a Bedrock production repository.

## Extract behavior

Separate observations from inference. Record:

- Player-visible role and trigger.
- State transitions, timing, cooldown, and failure behavior.
- Placement, interaction, collision, inventory, redstone, or entity behavior.
- Persistence, reload, restart, unload, and cleanup.
- Multiplayer authority and ownership.
- Required dependency closure.
- Contradictions, uncertainty, and missing runtime evidence.
- Construction-quality observations that can be abstracted into budgets or
  semantic articulation without transferring shape, palette, UV, bone names,
  exact proportions, or animation data.

Use epistemic states such as `OBSERVED`, `STATICALLY_INFERRED`,
`DOCUMENTED`, `OBSERVED_AND_STATICALLY_SUPPORTED`, `CONTRADICTED`, and
`MORE_EVIDENCE_REQUIRED`. Attach evidence references and confidence to every
claim. Do not silently convert a guess into a requirement.

## Produce analysis outputs

Write only analysis-lane or control-plane artifacts:

- Evidence inventory and manifest.
- Operation-level rights matrix.
- Feature/dependency graph.
- Evidence claims and contradictions.
- Initial abstract state model.
- Bedrock feasibility and expression-risk assessment.
- Recommended mapping class: `NATIVE_MAPPING`, `STABLE_SCRIPT_REDESIGN`,
  `ORIGINAL_SUBSTITUTE`, `CONSOLIDATE`, `DEFER`, or `BLOCKED`.

Mark production visibility for every claim. Prefer `ABSTRACT_ONLY`; use
`PRODUCTION_PROHIBITED` for distinctive expression.

For visual evidence, keep model files, geometry signatures, textures, exact
clip timings, keyframes, palette structure, and screenshots in the evidence or
post-freeze audit lane. Output only class, scale range, semantic articulation,
gameplay states, readability, collision/locator needs, and performance-relevant
observations for later product selection. Label construction benchmarks
`CONTROL_ONLY`; they are never production templates.

## Stop correctly

Use a controlled stop for `SOURCE_IDENTITY_UNRESOLVED`,
`REQUIRED_ANALYSIS_RIGHTS_UNRESOLVED`, `MORE_EVIDENCE_REQUIRED`, or
`FEATURE_UNSUITABLE_FOR_CLEANROOM`. Do not draft a sanitized contract and do not
claim legal, commercial, Marketplace, client, or PS4 clearance.
