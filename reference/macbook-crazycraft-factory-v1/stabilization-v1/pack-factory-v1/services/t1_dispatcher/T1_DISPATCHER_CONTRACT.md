# Durable T1 Dispatcher Contract

The dispatcher is the single persistent executor for semantic actions prepared
by the factory router. The router remains the append-only mailbox consumer and
does not execute semantic actions.

Each cycle:

1. Reconstruct actions and worker frontiers from the mailbox, router projection,
   and SQLite journal.
2. Recover an expired lease only within the configured attempt bound.
3. Execute the existing mechanical gate against exact immutable Git and
   artifact authority.
4. Publish each result and downstream intake once through the canonical
   mailbox publisher.
5. Route Stable BDS passes to T10, T10 passes to T2 integration, and
   machine-routable failures to the original durable owner through one
   consolidated repair message.
6. Emit idempotent resume requests for the Codex heartbeat to send to the
   existing durable task ID.

The dispatcher never edits a pack repository, candidate artifact, shared
runtime implementation, tester state, T10 result, or integration product.

Runtime authority is stored in `runtime/t1-state.sqlite3` using SQLite WAL mode
and `synchronous=FULL`. Runtime JSON projections are diagnostic views; the
database and immutable mailbox remain authoritative after restart.

The recurring Codex heartbeat runs `t1_dispatcher.py --run-once`, sends only
pending resume requests to their exact existing task IDs, acknowledges each
successful send with `--ack-resume`, and leaves packs waiting on downstream
evidence paused.
