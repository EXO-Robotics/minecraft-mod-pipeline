---
name: audit-java-bedrock-cleanroom
description: Independently audit a frozen Java-to-Bedrock candidate after production freeze, including semantic oracle execution, mutation tests, contamination and originality review, lineage and isolation proof, deterministic rebuild, and authoritative Stable/Preview BDS qualification. Use only for a fresh read-only auditor with authorized post-freeze access to all required lanes.
---

# Audit a Java-Bedrock Clean Room

Operate as a fresh post-freeze auditor. Do not implement or modify the evidence,
control, production, or frozen candidate repositories.

## Verify audit authority

Require an audit packet containing:

- Frozen candidate commit and package hashes.
- Evidence, rights, product-selection, contract, oracle, and transfer hashes.
- Production baseline, prompt/context, sandbox, and isolation receipts.
- Read-only paths for all authorized lanes.
- Expected qualification binaries and server hashes.

Refuse a mutable candidate or incomplete lineage.

## Audit separate dimensions

### Semantic integrity

Run the private oracle and mutation suite against the exact candidate. Score
`EXACT_INVARIANT`, `RANGE_EQUIVALENT`, `FUNCTIONALLY_EQUIVALENT`,
`INTENTIONALLY_REDESIGNED`, and `OMITTED_WITH_APPROVAL` separately. Do not reward
presentation similarity where redesign was required.

Cover triggers, timing, invalid states, duplicates, stale callbacks,
multiplayer, persistence, restart, unload, cleanup, caps, stress, and
cross-feature behavior.

### Contamination and originality

Inspect identifiers, strings, comments, localization, filenames, commits,
textures, geometry, animation, audio, layouts, build outputs, caches, prompts,
and Git objects. Determine both whether copying was technically prevented and
whether prohibited expression is absent. Record uncertainty honestly.

For visual candidates, invoke `$audit-golden-blockbench-asset`. Include exact
identifier and byte-collision checks, geometry signatures, animation timing
patterns, silhouette/material structure, proof integrity, and the native
round-trip receipt. Treat a construction benchmark as `CONTROL_ONLY`, never as
a production-quality template.

### Lineage and isolation

Verify ancestry, hashes, transfer receipts, remotes, alternates, symlinks,
caches, environment manifests, canary denial, production access logs, repair
receipts, and absence of pre-transfer implementation.

For every authoring and repair commit, verify that the recorded PID and command
were actually launched through the hashed sandbox executor with lane-local
environment roots. Report separately whether prohibited expression was not
detected and whether copying was technically prevented. Missing process
receipts fail the second conclusion and therefore fail clean-room success. A
later sandboxed rebuild cannot retroactively prove an earlier authoring process.

### Bedrock qualification

Run `CURRENT_SCHEMA_BDS_GATE`, disposition historical tests explicitly, and
refresh all final statuses from receipts bound to the exact final candidate.

Rebuild the exact frozen candidate twice. Run static and asset validation,
Creator Tools where available, Stable BDS, Preview BDS, multiplayer, restart,
persistence, cleanup, and worst-credible stress. Inspect content logs. A marker
pack proves Script API availability, not candidate gameplay callbacks.

If the candidate is asset-only, require the qualification receipt to say that
script runtime was not required. A clean asset-only BDS run proves pack/entity
load and the exercised server probes, not client rendering or animation.

## Return safe defects

When repair is possible, send production only an opaque requirement ID,
observable failure, allowed expected outcome, affected public interface, and
invalidated gates. Never reveal source expression, evidence paths, private test
logic, or hidden canaries. Re-audit every affected dimension after a new freeze.

## Classify narrowly

Use a proven classification only when rights, evidence, sanitization, isolation,
lineage, semantics, originality, deterministic packaging, Stable BDS, and
required Preview BDS gates pass. Keep desktop client, Realm, controller,
split-screen, physical PS4, distribution, and Marketplace pending unless
independently executed. Never use a limitations result to hide a failed core
clean-room or Stable-BDS gate.
