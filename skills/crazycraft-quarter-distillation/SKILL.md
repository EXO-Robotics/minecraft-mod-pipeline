---
name: crazycraft-quarter-distillation
description: Analyze an oversized Java mod or modpack and select a rights-aware, progression-coherent, console-feasible approximately one-quarter Bedrock reconstruction scope. Use when Codex must inventory and cluster gameplay systems, preserve a modpack's identity, score player value and conversion feasibility, close prerequisite chains, distinguish reconstruction from original redesign, produce a conversion roadmap, or prepare a preliminary CrazyCraft-style Marketplace-candidate plan without copying third-party content or claiming rights clearance.
---

# Distill a large modpack

Use the factory's deterministic intake plan for file identity and hashes. Use
authorized evidence analysis for gameplay facts, then freeze scoring,
constraints, and scope-selection reports as control-lane artifacts. Keep
qualitative review as a separate attributable adjustment.

## Workflow

1. Establish the input evidence.
   - Inventory exact versions, loaders, artifacts, hashes, configs, scripts, nested JARs, source availability, licenses, and dependencies.
   - If exact files are unavailable, create only a metadata-backed preliminary analysis and list every evidence gap.
   - Never fabricate feature confidence.
2. Build `distillation-input.json` under the campaign control lane.
   - Cluster features into player-facing systems; do not optimize file or item count.
   - Record each system's encounter, reward, unlock, downstream support, removability, prerequisites, effort, static console cost, rights state, and evidence.
   - Read [methodology.md](references/methodology.md) for selection rules.
   - Treat intake inventory as incomplete gameplay evidence until an authorized
     evidence worker records player-facing behavior and uncertainty.
3. Freeze the input and create the artifact set defined by
   [output-contract.md](references/output-contract.md). Validate prerequisite
   closure, the 25-percent effort ceiling, rights gates, console estimates, and
   early-game-to-postgame progression. Record every scoring rule and lexical
   tie-break in `scoring-report.json` so another agent can reproduce the
   selection.

   Begin from the factory's hash-bound intake plan:

   ```bash
   .venv/bin/bedrock-factory \
     --db .mccompiler/factory-v1/orchestration.sqlite3 \
     factory-plan \
     --modpack ABSOLUTE_PATH_TO_AUTHORIZED_MODPACK \
     --output-root .mccompiler/factory-v1/campaigns/CAMPAIGN_ID \
     --authority RECORDED_AUTHORITY
   ```

4. Inspect all frozen outputs.
   - Confirm prerequisite closure, progression completeness, effort and console limits, rights blockers, missing defining categories, and evidence gaps.
   - Read [scoring.md](references/scoring.md) when reviewing weighted dimensions.
   - Read [output-contract.md](references/output-contract.md) before accepting the artifact set.
5. Map selected systems to proven reconstruction patterns.
   - Read [reconstruction-patterns.md](references/reconstruction-patterns.md).
   - Mark each pattern as existing, needing extension, novel, Bedrock-limited, and benchmark-required.
6. Apply qualitative review only through an append-only review-adjustment
   record in the control lane.
   - Preserve deterministic scores unchanged.
   - Include reviewer identity, reason, prior and proposed values, and evidence.
   - AI review is advisory and cannot grant rights or Marketplace clearance.
7. Re-run validation and explain identity, selected and deferred systems, progression, redesigns, compiler gaps, benchmarks, console risks, rights gaps, evidence gaps, and build order.

## Non-negotiable boundaries

- Treat 25% as estimated conversion effort, not 25% of files, mods, or item registrations.
- Require a playable early-game-to-postgame loop; reject disconnected popularity lists.
- Treat unknown evidence unfavorably.
- Fail closed on direct-reconstruction rights. Use `ORIGINAL_REPLACEMENT` only for high-level fantasy with original names, models, textures, sounds, structures, branding, and lore.
- Distinguish static console estimates from measured runtime evidence.
- Use only Marketplace-stable APIs for the target.
- Do not redistribute third-party assets or source.
- Do not claim legal approval, Marketplace acceptance, console certification, or exact CrazyCraft coverage without evidence.
- Do not begin mass-producing the add-on during distillation.

## Structured artifact stages

Record these named stages in the distillation manifest: identity analysis,
system clustering, player-value scoring, conversion-effort estimation,
console-cost estimation, pattern-reuse estimation, progression dependency
closure, quarter-scope selection, selection explanation, roadmap generation,
and attributable review adjustments.

Read [rights-and-originality.md](references/rights-and-originality.md) whenever any component rights are unclear.
