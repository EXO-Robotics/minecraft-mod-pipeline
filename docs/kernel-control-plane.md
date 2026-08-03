# Completion Factory kernel control plane

Updated: 2026-08-03

The portable kernel now distinguishes authoritative lifecycle history from
disposable operational views.

## Canonical lifecycle authority

Every product-lifecycle transition is one chained
`bedrock-factory.canonical-event.v1.0.0` envelope. It binds campaign, workload,
typed candidate and activation identities, optional gate-run identity, input
and output hashes, authority hash, timestamp, payload, prior-event hash, and its
own canonical digest.

The event log is append-only and should be committed through the independent
Git mailbox. SQLite lifecycle tables, frontier JSON, queue views, metrics, and
status output are projections. The orchestration queue's internal SQLite event
table remains scheduler diagnostics; it is not product-lifecycle authority.

Required proof before trusting a retained lifecycle projection:

```bash
.venv/bin/bedrock-factory projection-rebuild \
  --log PATH/canonical-events.jsonl \
  --projection PATH/lifecycle.sqlite3

.venv/bin/bedrock-factory projection-verify \
  --log PATH/canonical-events.jsonl \
  --projection PATH/lifecycle.sqlite3
```

`projection-verify` rebuilds from zero and fails closed on any difference.
Projection schemas and event schemas are versioned separately.

## Content-addressed evidence

Large manifests, log bundles, inventories, and tree evidence are stored once at
`objects/sha256/AA/REST_OF_HASH`. Portable receipts carry the object hash,
object type, relevant delta, disposition, and claim boundary. Merkle manifests
use logical relative paths; machine-local absolute resolution belongs only in a
nonportable execution projection. Per-activation records use the minimal
activation-attestation schema and never repeat full manifests.

## Milestone-only validation

Broad validation is allowed at exactly two reconstruction points:

1. `PRE_BDS_MILESTONE`, immediately before the first BDS run. It consolidates
   deterministic packaging, package structure, entrypoint reachability,
   restricted scans, T1, and MCTools.
2. `FINAL_MOD_MILESTONE`, immediately before the mod is classified complete.
   It consolidates final-package binding, BDS evidence, observation, T10,
   integration/persistence, lineage/originality, claim boundaries, and final
   bundle coverage.

Producers have no T1 shadow and no broad local validation suite. Activations
emit only a small attestation. BDS and ordinary observation are runtime work
between the two milestones. A validator is dispatched only on milestone entry,
when a bound hash changed, or when the previous receipt is missing/invalid.
Otherwise the exact prior PASS is reused.

MCTools output is accepted only from one exact structured validation summary or
one fully anchored plain summary. Missing, malformed, ambiguous, string-valued,
negative, nonzero-error, version-drifted, or log-unbound results fail closed.

## Kernel metrics

`bedrock-factory metrics --log PATH` derives these values from canonical events:

- activation amplification;
- candidate T1 and BDS-smoke first-pass yield;
- infrastructure-blocked share;
- queue age and service time by gate;
- product-byte change and repeated-evidence rates;
- accepted-slice integration lag;
- defect escape stage.

Projection replay integrity remains a hard target of 100%, not an average.
