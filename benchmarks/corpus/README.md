# Legally clean corpus measurement foundation

This directory defines measurement inputs; it is not a completed corpus and it
contains no third-party mod content. `manifest-template.json` intentionally has
no samples and therefore cannot qualify. Populate a separate revision only with
content-addressed inputs whose rights evidence has been reviewed.

Each atomic registration, behavior, and unsupported-hook observation requires a
boolean ground-truth `label`, boolean `prediction`, and evidence for both. A
behavior additionally declares whether it is recoverable and whether its source
evidence supports an emitted prediction. Determinism uses two independently
generated artifact hashes. Source/JAR agreement is scored only for patterns
declared supported before evaluation.

The fixed split policy is:

- `development`: tuning permitted.
- `validation`: evaluation during development and tuning permitted.
- `final_holdout`: frozen before tuning, never used for tuning, and evaluated
  once for each declared release candidate.

Unsupported and ambiguous labeled facts are not silently excluded. Missing
labels, evidence, legal-clean declarations, content hashes, observations, or
metric denominators cause a non-qualifying report. Passing these measurement
thresholds does not establish Marketplace approval, legal clearance, runtime
fidelity, console verification, or completion of a real corpus.

