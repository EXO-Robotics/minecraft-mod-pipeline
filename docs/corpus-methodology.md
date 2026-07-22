# Corpus and evaluation methodology

The corpus must be legally clean, loader-diverse, behavior-representative, and split before tuning. Synthetic fixtures isolate facts; real mods test ecological validity. Inputs and expected results are content-addressed.

## Partitions

- Development fixtures: small authentic API shapes and adverse cases.
- Validation corpus: unseen variants used during development.
- Final holdout: frozen before tuning and evaluated once per declared release candidate.
- Benchmark A: original backend/product showcase.
- Benchmark B: DoorLock is a pinned technical candidate with real-source scan evidence, a partial clean-room reconstruction, complete unresolved fidelity records, and hash-bound Creator Tools/BDS boot evidence. It is not selected as rights-cleared and has not passed real-action reconstruction fidelity, multiplayer, migration-runtime, or console gates.

## Metrics

Measure registration precision/recall, behavior precision, recoverable behavior recall, unsupported-hook detection, fabrication rate, deterministic regeneration, source/JAR agreement, reconstruction fidelity, manual redesign effort, rights completeness, and measured console performance.

Initial targets are 95% registration precision, 90% registration recall, 90% behavior precision, 70% recoverable behavior recall, 95% unsupported detection, 0% fabricated behavior, 100% deterministic regeneration, and 95% source/JAR agreement on declared supported patterns.

Every metric publishes numerator, denominator, exclusion rules, confidence/uncertainty, corpus revision, and failures. Unsupported and ambiguous cases remain in denominators according to a predeclared policy. Do not tune against final holdout results.

The executable evaluator and fixed thresholds live under `benchmarks/corpus/`. Empty or unlabeled samples, missing evidence, zero denominators, and holdout-policy violations fail closed. Synthetic evaluator tests do not imply completion of a legally reviewed real corpus.
