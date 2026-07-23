# DoorLock case study

DoorLock is the strongest real-mod reconstruction evidence in the repository. Source scanning extracted the Java mod's registrations, lock intent, interaction surfaces, persistence requirements, ownership behavior, and unsupported mixin boundary. The Bedrock implementation was then authored clean-room in protected scripts rather than translated line-for-line.

## Preserved behavior and native replacements

- Persistent locks are keyed by canonical world locations, including lower-door and paired-container canonicalization.
- Owner and credential authorization replaces Java-side access hooks with server-authoritative checks.
- Credentials persist as digests, not plaintext.
- Stable forms are the proposed controller-first replacement for Java configuration UI.
- Successful block breaks clean up lock records.
- A bounded reconciliation pass replaces Java redstone interception.
- Revisioned schemas, migration journals, interrupted-write recovery, and fail-closed malformed-state handling replace Java save mechanics.

The authoritative receipt is `benchmarks/rights-cleared-java-mod/reconstruction/technical-build-validation.json`. It binds deterministic `.mcaddon` and `.mcworld` hashes, Creator Tools results, stable BDS boot, three restart cycles, a nonempty migration, interrupted-write recovery, migrated-record survival, redstone reconciliation, and a Preview SimulatedPlayer block-break adapter.

It explicitly does **not** prove physical lock/unlock/forms/crafting/break gameplay, player-created feature persistence, real two-player authorization, controller operation, Windows/Realm/console behavior, rights clearance, quality acceptance, or Marketplace suitability.

## Reusable patterns

Crazy Craft-style machines, encounter gates, player bases, elite arenas, progression shrines, shared party devices, world-event anchors, and portal substitutes can reuse canonical location identity, ownership, credential/permission policy, revision checks, cleanup, reconciliation, migrations, and fail-closed recovery. Each reuse still needs feature-specific gameplay and multiplayer evidence.
