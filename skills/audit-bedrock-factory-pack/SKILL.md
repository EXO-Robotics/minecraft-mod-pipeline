---
name: audit-bedrock-factory-pack
description: Own the FINAL_MOD_MILESTONE for one exact final Bedrock candidate or frozen portfolio. Use only immediately before the mod is classified complete, never as a repeating per-slice or per-activation validation job.
---

# Validate the final-mod milestone

Run broad final validation exactly once immediately before completion, unless
one of its bound hashes changed or the prior receipt is missing/invalid. It
consolidates final-package binding, required BDS receipts, calibrated
observation, independent T10, integration/persistence, lineage/originality,
claim boundaries, and final bundle-manifest coverage.

Use `$audit-bedrock-shipped-gameplay` for an exact `.mcaddon` and
`$audit-bedrock-portfolio-freeze` for a frozen multi-pack portfolio. Bind the
candidate generation, artifact hashes, production authority, and audit input
authority before evaluation.

If final candidate bytes and all final-milestone authority hashes are unchanged,
reuse the PASS rather than dispatching another auditor. Remain independent: do not edit candidate bytes, production repositories,
contracts, mailbox history, or worker tasks. Do not reveal private oracle cases
to production. Report findings through opaque requirement/finding IDs with
reproducible evidence and a clear proof boundary.

Evaluate contracts through declared semantic modes and acceptable evidence
classes. Structural record inequality alone is not `FAIL_SEMANTIC`. A missing
or unsupported field yields insufficient, client-required, or inconclusive
evidence. Internal hooks, packaged test doubles, and mutation harnesses prove
only their calibrated paths, not ordinary network-player delivery.

Separate product failures from missing audit authority or infrastructure. A
product failure goes to the overseer/mailbox owner for consolidation with other
same-generation findings; do not directly wake or instruct the producer. A PASS
does not prove client, Realms, controller, split-screen, PS4, Marketplace, or
release readiness unless those exact gates were separately executed.
