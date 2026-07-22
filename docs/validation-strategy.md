# Validation strategy

Validation is layered and evidence-specific:

1. Input, schema, IR and decision consistency.
2. Target profile and symbol/version compatibility.
3. Generated JSON, scripts, assets, references, manifests and package boundaries.
4. Creator Tools with explicit warning policy.
5. Internal handler tests.
6. Real event-adapter integration tests.
7. Gameplay, persistence, migration and multiplayer tests.
8. Local client, Realm and named physical-device benchmarks.
9. Rights and performance gates.

Runtime evidence binds artifact/build hashes, runtime/game version, world/test identity, harness version, required check IDs, timestamps, and raw log hash. Internal dispatcher calls cannot satisfy event-adapter tests. Bounded BDS console probes may establish server adapter integration, but they are not real player actions. BDS cannot satisfy client, Realm, controller, or console gates.

Required real actions include item use/use-on-block, attacks and damage, block break/interact, projectile impact, boss phase transition, leave/rejoin, world restart, isolated players, and state upgrade. Unknown actions, conditions, required actors, targets, state owners, event signals, and APIs fail closed or become explicit redesign/unsupported outcomes.
