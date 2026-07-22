# Marketplace capability catalog

The production catalog is separate from general Bedrock knowledge and is versioned with the build. Planned partitions are data-driven, stable Script API, Marketplace stable, Realm/console, console performance, BDS-only, and experimental.

Every generated API/component record must contain:

```yaml
id: script.world_after_events.player_interact_with_block
module: "@minecraft/server"
symbol: WorldAfterEvents.playerInteractWithBlock
minimum_stable_version: unresolved
maximum_known_version: null
engine_range: unresolved
stability: stable
experiments_required: []
marketplace_candidate: unverified
realm_candidate: unverified
bds_only: false
controller_implications: []
persistence_behavior: none
multiplayer_implications: actor-scoped
performance_cost: event-driven
replacement_strategies: []
device_test_history: []
sources: []
last_verified: null
```

`unresolved` and `unverified` are valid honest values during research but block a production strategy. Module-level allowlisting is insufficient: generation inventories every emitted symbol and validation checks catalog presence, stability, module version, engine compatibility, experiments, privilege, profile eligibility, manifest dependency, and required tests.

Catalog entries cite official/primary documentation and record verification dates. Device history records only concrete artifact hash, game version, device, procedure, and result; it cannot be inferred from API stability.

The current worktree includes an initial symbol catalog, independent module-version resolution, target catalogs, and tests for unknown-symbol rejection and independent `server`/`server-ui` resolution. Catalog completeness, primary-source verification for every symbol, engine-range coverage, and device history remain incomplete.
