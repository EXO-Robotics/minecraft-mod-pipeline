# Scoring

The authoritative weights are
`src/mccompiler/capabilities/distillation-weights-1.0.0.json`; versioned schemas
under `src/mccompiler/schemas/` are authoritative contracts.

Score positive value (identity, appeal, depth, spectacle, replayability,
progression, exploration, reuse, marketing, and Bedrock opportunity),
feasibility (Java evidence, reconstruction, compiler coverage, assets, tests,
console, multiplayer, persistence, maintenance), rights, and negative costs.

Represent values as integers from 0 through 100 with `KNOWN` evidence, or
`UNKNOWN` with a reason. Unknown values provide no positive value and appear as
evidence gaps. Rights are hard gates for direct reconstruction, not score
bonuses. Scores rank feasible bundles but cannot override constraints.
