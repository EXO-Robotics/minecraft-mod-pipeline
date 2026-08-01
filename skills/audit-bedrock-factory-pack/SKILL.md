---
name: audit-bedrock-factory-pack
description: Perform an independent post-freeze audit of one exact Bedrock factory candidate or frozen portfolio. Use for T10/private semantic review, shipped-gameplay inspection, originality and lineage checks, hidden-case evaluation, or audit findings that must remain separated from production and candidate mutation.
---

# Audit one Bedrock factory pack

Use `$audit-bedrock-shipped-gameplay` for an exact `.mcaddon` and
`$audit-bedrock-portfolio-freeze` for a frozen multi-pack portfolio. Bind the
candidate generation, artifact hashes, production authority, and audit input
authority before evaluation.

Remain independent: do not edit candidate bytes, production repositories,
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
