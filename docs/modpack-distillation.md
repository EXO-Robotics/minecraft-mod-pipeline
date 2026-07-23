# Modpack distillation

`mccompiler distill-modpack` selects a small, coherent Bedrock product scope from
an evidence-inventoried Java modpack. It does not translate Java or select a
percentage of files. It optimizes prerequisite-closed player-facing systems
within conversion-effort, Marketplace-stable API, rights, progression, and
static console-cost constraints.

```bash
mccompiler distill-modpack \
  --input analysis/distillation-input.json \
  --target MARKETPLACE_ADDON_STABLE \
  --effort-budget 0.25 \
  --output planning-output
```

The input contract is
`src/mccompiler/schemas/distillation-input-1.0.0.json`. Every score uses integer
units and evidence. Unknown evidence contributes no favorable value. Unknown
rights block direct reconstruction. A high-level fantasy may instead be planned
as an original replacement without copying names, characters, assets,
structures, lore, branding, or distinctive expression.

The command emits fourteen required reports and a digest manifest under
`distillation/`. JSON-compatible YAML is intentional so the repository remains
dependency-light. `distillation-manifest.json` records source, weight-policy, and
artifact digests.

The deterministic engine scores feature records from feature-specific evidence
and clustered systems from system evidence. Missing feature evidence receives a
fail-closed zero score and explicit gaps; it never inherits a favorable parent
score. Selection occurs at system level so filler item volume cannot dominate.
Prerequisite closure is calculated before budget checks; defining category
omissions are warnings rather than forced quotas. The standard progression path
runs from early survival through a final chaos encounter and postgame, but an
input may declare another evidence-backed path.

Structured project operations expose identity, clusters, feature/system scores,
effort, console estimates, pattern reuse, progression dependencies, selection,
explanation, roadmap generation, and separate review adjustments. Review
records are advisory and cannot grant rights or Marketplace clearance.

When input is a raw mod/JAR/modpack path or a conversion project containing
`analysis/modir.json`, the command first uses the existing scanner, preserves
the dependency graph, inventories content and behaviors, and forms deterministic
kind/trigger clusters. Automated scanning deliberately leaves identity,
progression, rights, and most feasibility dimensions unknown. It emits an
incomplete preliminary report and exits `1` until attributable analysis
metadata is supplied.

The legally fictional test fixture is
`tests/fixtures/fictional_large_modpack/`. The first metadata-only CrazyCraft
planning application is `planning/crazycraft-preliminary/`. No third-party
assets or packages are included.
