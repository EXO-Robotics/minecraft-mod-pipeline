# Corpus and evaluation methodology

The corpus must be legally clean, loader-diverse, behavior-representative, and split before tuning. Synthetic fixtures isolate facts; real mods test ecological validity. Inputs and expected results are content-addressed.

## Partitions

- Development fixtures: small authentic API shapes and adverse cases.
- Validation corpus: unseen variants used during development.
- Final holdout: frozen before tuning and evaluated once per declared release candidate.
- Benchmark A: original backend/product showcase.
- Benchmark B: one rights-cleared real Java reconstruction, not yet selected.

## Metrics

Measure registration precision/recall, behavior precision, recoverable behavior recall, unsupported-hook detection, fabrication rate, deterministic regeneration, source/JAR agreement, reconstruction fidelity, manual redesign effort, rights completeness, and measured console performance.

Initial targets are 95% registration precision, 90% registration recall, 90% behavior precision, 70% recoverable behavior recall, 95% unsupported detection, 0% fabricated behavior, 100% deterministic regeneration, and 95% source/JAR agreement on declared supported patterns.

Every metric publishes numerator, denominator, exclusion rules, confidence/uncertainty, corpus revision, and failures. Unsupported and ambiguous cases remain in denominators according to a predeclared policy. Do not tune against final holdout results.

