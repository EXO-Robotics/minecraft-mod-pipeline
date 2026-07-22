# Persistence and migrations

Long-lived worlds require stable identifiers and versioned state. State records namespace, schema version, owner scope, type, default, invariants, storage, and lifecycle.

Updates provide ordered, idempotent migrations with a journal, preconditions, postconditions, failure diagnostics, and retry/rollback policy. Identifiers are never reused for unrelated content. Removal defines orphaned state and missing-content behavior.

Required scenarios include fresh world, save/reload, process restart, player leave/rejoin, two-player isolation, machine index restoration, old-version upgrade, interrupted/failed migration, removed content, and downgrade/rollback handling where supported.

Compiler IR migration and Minecraft world-state migration are separate systems. A dynamic property surviving restart does not prove that scheduled machines, ownership indexes, or all schema migrations recover.

