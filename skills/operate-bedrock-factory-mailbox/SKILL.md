---
name: operate-bedrock-factory-mailbox
description: Reconstruct and route the Studio Bedrock factory's durable semantic state across its SQLite ledger, independent Git mailbox, immutable candidate generations, repair messages, and thread-dispatch outbox. Use for mailbox reconciliation, candidate publication, repair routing, duplicate prevention, status reporting, or restart recovery.
---

# Operate the Bedrock factory mailbox

Treat committed messages and immutable candidate records as authority. Runtime
JSON projections are diagnostic and may be stale.

## Reconcile

1. Verify the configured mailbox is an independent clean Git repository on its
   configured ref and has no inherited campaign history or remotes.
2. Read SQLite mailbox messages/candidates and Git mailbox commits without
   rewriting either history.
3. Resolve authority by exact message/candidate identity, source mailbox commit
   and message hash, source authority commit/tree, then declared explanatory
   fields.
4. Enforce one authoritative superseder per message and idempotency per semantic
   event.
5. Allocate generations transactionally. First publication is generation 1;
   every replacement is exactly the latest generation plus one.

Use the Studio CLI surfaces:

```bash
.venv/bin/bedrock-factory --db DB mailbox-messages --campaign ID
.venv/bin/bedrock-factory --db DB candidates --campaign ID
.venv/bin/bedrock-factory dispatch-pending --outbox OUTBOX
.venv/bin/bedrock-factory dispatch-ack --outbox OUTBOX \
  --request REQUEST_ID --state SENT --worker-task-id TASK_ID
```

Acknowledge dispatch only after successful delivery. Replaying an acknowledged
identity must return history, not send another worker.

## Repair routing

Combine all same-generation product findings into one structured repair message.
Bind its rejected generation, required `N+1`, exact failed receipts, allowed
write scope, prohibited scope, and completion condition. Keep infrastructure
failures separate from product repairs. Do not modify or delete the failed
candidate, and do not route unchanged bytes back to qualification.

Return a machine-readable frontier: current generation, authoritative message,
candidate hash, active owner, pending dispatches, downstream results, repairs,
and narrow stop code.
