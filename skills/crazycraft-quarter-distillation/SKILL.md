---
name: crazycraft-quarter-distillation
description: Analyze an oversized Java mod or modpack and select a rights-aware, progression-coherent, console-feasible approximately one-quarter Bedrock reconstruction scope. Use when Codex must inventory and cluster gameplay systems, preserve a modpack's identity, score player value and conversion feasibility, close prerequisite chains, distinguish reconstruction from original redesign, produce a conversion roadmap, or prepare a preliminary CrazyCraft-style Marketplace-candidate plan without copying third-party content or claiming rights clearance.
---

# Distill a large modpack

Use the deterministic compiler for facts, scoring, constraints, and report generation. Use qualitative review only as a separate attributable adjustment.

## Workflow

1. Establish the input evidence.
   - Inventory exact versions, loaders, artifacts, hashes, configs, scripts, nested JARs, source availability, licenses, and dependencies.
   - If exact files are unavailable, create only a metadata-backed preliminary analysis and list every evidence gap.
   - Never fabricate feature confidence.
2. Build `distillation-input.json` using `src/mccompiler/schemas/distillation-input-1.0.0.json`.
   - Cluster features into player-facing systems; do not optimize file or item count.
   - Record each system's encounter, reward, unlock, downstream support, removability, prerequisites, effort, static console cost, rights state, and evidence.
   - Read [methodology.md](references/methodology.md) for selection rules.
   - A raw modpack command performs deterministic scan, inventory, and clustering, but expect an incomplete result until qualitative evidence is reviewed.
3. Run:

   ```bash
   mccompiler distill-modpack \
     --input <analysis-or-input> \
     --target MARKETPLACE_ADDON_STABLE \
     --effort-budget 0.25 \
     --output <distillation-project>
   ```

4. Inspect all machine outputs.
   - Confirm prerequisite closure, progression completeness, effort and console limits, rights blockers, missing defining categories, and evidence gaps.
   - Read [scoring.md](references/scoring.md) when reviewing weighted dimensions.
   - Read [output-contract.md](references/output-contract.md) before accepting the artifact set.
5. Map selected systems to proven reconstruction patterns.
   - Read [reconstruction-patterns.md](references/reconstruction-patterns.md).
   - Mark each pattern as existing, needing extension, novel, Bedrock-limited, and benchmark-required.
6. Apply qualitative review only through `record_distillation_adjustment` or `--review-adjustments`.
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

## Structured operations

Use these project-bound operations:

- `analyze_modpack_identity`
- `cluster_gameplay_systems`
- `score_feature_value`
- `estimate_conversion_effort`
- `estimate_console_cost`
- `estimate_pattern_reuse`
- `identify_progression_dependencies`
- `select_quarter_scope`
- `explain_selection`
- `generate_conversion_roadmap`
- `record_distillation_adjustment`

Read [rights-and-originality.md](references/rights-and-originality.md) whenever any component rights are unclear.
