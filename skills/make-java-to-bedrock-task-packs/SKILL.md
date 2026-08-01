---
name: make-java-to-bedrock-task-packs
description: Freeze an authorized local Java modpack intake and generate deterministic, hash-bound Java-to-Bedrock task separation. Use for JAR, ZIP, or modpack-directory intake; new campaign planning; opaque unit separation; starting-task-pack creation; or repair/recovery activation generation before worker dispatch.
---

# Make Java-to-Bedrock task packs

Work only in the evidence/control lanes. Do not execute or extract Java archive
content during intake, create production output, or grant missing authority.

## Procedure

1. Resolve the source and output paths absolutely. Reject symlinks, special
   files, source/output overlap, unsafe archive paths, duplicate names, and
   portable-name collisions.
2. Record source-inspection authority and exact tree/artifact SHA-256 values.
3. From the Studio repository, run:

```bash
.venv/bin/bedrock-factory \
  --db .mccompiler/factory-v1/orchestration.sqlite3 \
  factory-plan --modpack SOURCE --output-root CAMPAIGN_ROOT \
  --authority AUTHORITY
```

4. Keep source names, paths, hashes, and private observations in the evidence
   lane. Expose only opaque unit IDs and sanitized product contracts to
   production.
5. Generate one machine-readable assignment and activation per ready action.
   Bind pack, repository/ref, exclusive write roots, activation type, current
   and next generation, exact action, local tests, completion, precedence,
   supersession, recovery, and allowed stop codes.
6. Use `NEW_PACK`, `CONTINUE_NONTERMINAL`, `REPAIR_REQUIRED`,
   `T2_ADAPTER_REPAIR`, or `RECOVERY_AFTER_INTERRUPTION` exactly.
7. Dispatch only dependency-ready work. A missing trigger produces structured
   `NO_SPAWN`; it does not justify inventing authority.

For a gameplay slice, declare applicable worker-local cases mechanically:
first use, repeat or redundant use, invalid input, partial or malformed old
state, migration, duplicate delivery, exact resource accounting, restart,
second player, cleanup, and bounded scheduling. Mark non-applicable cases
explicitly. Name admitted shared identity, persistence, reconciliation,
scheduling, telemetry, and idempotency interfaces; prohibit workload-local
duplicates.

For repair, include consolidated finding IDs, rejected generation, required
`N+1`, required worker regression IDs, and the independent gates their owners
must rerun.

Candidate publication requires worker-local validation and freeze, never a
downstream PASS. A repair activation must bind one consolidated authoritative
message, rejected generation `N`, and replacement generation `N+1`.

Finish with plan path/hash, unit count, ready assignments, waiting dependencies,
and structured blocks. Do not spawn workers from this role unless the overseer
explicitly assigns dispatch ownership.
