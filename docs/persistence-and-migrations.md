# Persistence and migrations

Long-lived worlds require stable identifiers and versioned state. State records namespace, schema version, owner scope, type, default, invariants, storage, and lifecycle.

Updates provide ordered, idempotent migrations with a journal, preconditions, postconditions, failure diagnostics, and retry/rollback policy. Identifiers are never reused for unrelated content. Removal defines orphaned state and missing-content behavior.

Required scenarios include fresh world, save/reload, process restart, player leave/rejoin, two-player isolation, machine index restoration, old-version upgrade, interrupted/failed migration, removed content, and downgrade/rollback handling where supported.

Compiler IR migration and Minecraft world-state migration are separate systems. A dynamic property surviving restart does not prove that scheduled machines, ownership indexes, or all schema migrations recover.

Benchmark B now adds a narrow state-preserving BDS upgrade test: a fixture-only legacy pack writes one v0 lock, the harness overlays the current packs without replacing the world database, the production migration imports and validates the record, and a third boot reads it through the completed journal. A bounded adapter-integration probe creates a loaded trapdoor fixture, forces `open_bit=true`, verifies that production reconciliation restores `open_bit=false`, and verifies that state after restart. This is not player gameplay or console evidence. Malformed/conflicting cases remain pure-logic tests, and interrupted writes, player reconnect, real gameplay-created locks, Realm, and console upgrades remain unverified.
