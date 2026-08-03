---
name: audit-bedrock-portfolio-freeze
description: Independently audit a frozen Minecraft Bedrock reconstruction portfolio for exact-package lineage, inventory disposition, private semantic-oracle integrity, mutation validity, Blockbench evidence, MCTools and Stable/Preview BDS qualification, clean-room process isolation, and honest full or partial freeze classification. Use after a Java-to-Bedrock candidate is frozen, after repair and requalification, or before creating a portfolio freeze tag.
---

# Audit a Bedrock Portfolio Freeze

Require a standardized assignment for role `portfolio_auditor`, skill
`audit-bedrock-portfolio-freeze`, and lane `AUDIT`. Validate it with
`$translate-java-mods-to-bedrock`'s
role-contract validator. Failed gates require new production or integration
assignments.

Operate read-only. Do not repair evidence or production while acting as the
final auditor. Report defects to the controller as opaque product findings.

## Bind the candidate

Record:

- Candidate, qualification, and control commits and trees.
- BP, RP, and combined package SHA-256 values.
- Contract, production-oracle interface, private oracle, sandbox profile, and
  activation-attestation hashes.
- Package extraction method and repository cleanliness.

Reject mutable working-tree packages. Accept carried-forward BDS evidence after
a test-only commit only when every package hash remains byte-identical and the
lineage record states that no pack member changed.

## Reconcile scope

Verify every raw inventory entry has one final disposition. Preserve raw counts
separately from logical product-feature counts. Require a counterpart and
qualification reference for implemented, merged, redesigned, or shared-system
entries. Reject difficulty-only deferrals and artifact-only “completion.”

## Run the private oracle

Keep the private oracle outside production. For each requirement:

1. Evaluate the unmutated exact candidate.
2. Record pass, fail, or pending with direct evidence.
3. Run each mutation in a fresh temporary candidate copy.
4. Require an empty target-failure baseline.
5. Scope the detector to the requirement boundary.
6. Count a kill only when that requirement changes from pass to fail.
7. Mark pre-existing or unrelated failures `INCONCLUSIVE`.

Bind the mutation receipt to candidate commit, combined package SHA, oracle SHA,
harness commit, baseline failures, and all case results.

Never weaken a frozen requirement after seeing the implementation. For visual
requirements, distinguish native UI open/proof, deterministic runtime export,
native-export equivalence, Bedrock rendering, and PS4 rendering. A Golden score
does not cure a missing native-export gate.

## Audit qualification

Verify the exact package passed, as applicable:

- JSON/schema and namespace checks
- Current Stable schema regressions
- Production-local and authoritative semantic tests
- Mutation tests
- Deterministic two-build packaging
- MCTools or Creator Tools
- Stable BDS restart cycles
- Preview BDS restart cycles
- Multiplayer, persistence, cleanup, stress, and world-generation probes
- Golden Blockbench proof and rubric

Require the BDS rows to come from `$qualify-bedrock-candidate`. Independently
verify its exact hashes and receipts; do not combine BDS execution and final
portfolio classification in one mutable role.

Treat feature-rule stem mismatches, ranged block-state schema escapes,
deprecated ticking components, invalid recipe unlocks, and manifest dependency
asymmetry as generator defects. Require a regression and mutation for every
BDS-discovered schema escape.

State BDS claims narrowly. BDS does not prove real client event delivery,
rendering, controller input, real multiplayer reconnect, Realm, split-screen,
or physical PS4 behavior.

## Audit clean-room process

Check actual activation attestations, not prompt intent:

- Production and every repair ran inside the frozen sandbox.
- PID, command, profile hash, prompt/context hashes, tool hashes, start/end
  times, exit status, network policy, and denial probes are recorded.
- Evidence, private oracle, canary, control Git objects, shared caches, and
  unrelated paths were unavailable.
- Production context contains no source identity or evidence path.
- Candidate ancestry contains no unsandboxed authorship.

No prohibited expression detected is a narrow package-scan result. Do not
promote it to copying-prevention proven when process isolation or lineage fails.

## Classify

Use full success only when semantic, originality, contamination, isolation,
lineage, deterministic packaging, MCTools, Stable BDS, and Preview BDS all pass.
Classify this as `PORTFOLIO_FREEZE_PROVEN_WITH_PLATFORM_LIMITATIONS` while
client, Realm, controller, split-screen, physical PS4, or Marketplace gates
remain pending.

If technically useful exact artifacts pass but a non-waivable gate fails:

- Create an immutable partial freeze record.
- Preserve exact packages and all evidence.
- Record the hard failure substatus.
- Do not create the full-success tag.

Classify this as `PARTIAL_CANDIDATE_FROZEN`.

Keep desktop, controller, multiplayer reconnect, Realm, split-screen, physical
PS4, Marketplace, distribution, and release statuses separate.

Before classifying, run
`$freeze-bedrock-campaign-bundle`'s bundle validator against the proposed final
bundle. Treat it as packaging-integrity evidence, not as a substitute for this
independent semantic, lineage, isolation, reachability, and qualification
audit.

Deliver a concise matrix containing exact hashes, inventory dispositions,
semantic totals, mutation totals, Golden scores, MCTools/BDS results, process
audit findings, final classification, and explicitly unproven surfaces.
