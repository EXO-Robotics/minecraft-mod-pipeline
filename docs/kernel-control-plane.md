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
nonportable execution projection or process receipt.

## Queue-aware qualification funnel

The default ordered funnel is:

1. producer T1 shadow;
2. independent T1;
3. one-cycle BDS entrypoint smoke;
4. Stable restart and persistence;
5. Preview only when required;
6. calibrated observation;
7. parallel read-only T10 component audits;
8. one deterministic T10 final adjudication.

A failed entrypoint smoke terminates the deeper sequence. BDS capacity is not
reserved while authority or package binding is unresolved. Prior gate evidence
may be reused only when candidate bytes, gate implementation, runtime image,
configuration, and probe authority hashes are all unchanged.

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
