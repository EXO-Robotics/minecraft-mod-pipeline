# Runtime validation record

Date: 2026-07-22. Target: local Dockerized Bedrock Dedicated Server 1.26.33.2, world `Bedrock level`.

The representative behavior and resource packs were installed in isolated `mccompiler_representative_bp` and `mccompiler_representative_rp` directories and referenced by deterministic UUID from the existing world pack lists.

Observed gates:

- Pack activation: BDS reported `representative reconstructed behavior` at pack-stack position 06.
- Content schemas: after correcting manifest metadata, current block components, and recipe unlock data, no `representative` content error appeared during startup.
- Script execution: BDS emitted `[Scripting] [mccompiler] contract tests passed behaviors=15` and `[Scripting] [mccompiler] runtime initialized behaviors=15 persistent_boot=1`.
- Persistence and reload: after a full server restart, BDS emitted `persistent_boot=2`, proving a generated world dynamic property survived reload.
- Content exposure: in a temporary ticking area, console smoke tests reported `Block placed` for `representative:aether_machine`, `Object successfully summoned` for `representative:clockwork_golem` and `representative:rift_boss`, and `Replaced slot.container slot 0 with 1 * item.representative:phase_blade`.
- Stateful machine behavior: the generated ScriptEvent harness seeded the extracted `energy >= 10` precondition, dispatched `representative:aether_machine/tick`, and BDS reported `behavioral test passed ... energy=0,progress=1`.
- Multi-phase boss behavior: live damage probes advanced the generated boss phase state through 1, 2, and 3 without a generated-pack error.
- Compiled input parity: the regression suite compiles the source-free representative JAR with `javac`, analyzes it with `javap`, and requires all 15 behavior fingerprints to match source analysis exactly.
- Cleanup: the two test entities, machine block, test chest/item, and temporary ticking area were removed after the probe.

The server contains pre-existing errors from unrelated packs such as Just Biome, Underground Biomes, and Immersive Fauna. Those errors were isolated by pack path and were not attributed to generated output.

This record proves import/discovery, activation, generated content registration, Script API startup, persistent state, state-gated machine processing, and boss phase transitions. It does not claim that every extracted player interaction has been exercised by a real client; those mechanics remain in the generated behavioral test plan.

Run `mccompiler validate --path <output> --runtime` to require a structured runtime evidence artifact in addition to static and integration validation.

## Managed isolated BDS adapter

The structured `start_test_runtime` operation supports an explicitly authorized `BDS_DOCKER` adapter. It accepts only a project-relative `.mcworld`, requires an immutable container-image digest unless the caller explicitly allows weaker diagnostic evidence, publishes no ports, bounds execution time, preserves the raw content log and result, and removes its named container. A fresh wrapper volume may use bridge networking only when the caller explicitly authorizes downloading an exact requested BDS version; that bootstrap is recorded and is not an Add-On runtime dependency.

The adapter proves only generated-world loading, behavior-pack activation, stable script initialization, clean startup, and graceful shutdown. Gameplay, persistence, multiplayer, Windows, Realm, controller, console, and Marketplace claims remain false.

With `restart_count` set to 2 or 3, the adapter reuses the same isolated BDS data volume and records each boot independently. A generated diagnostic marker may prove that one named world dynamic property survived restart; this is reported as `diagnostic_state_persistence_verified`. It never sets the broader `persistence_verified` claim, which still requires feature-specific state, migration, reload, and reconnect checks.

For upgrade diagnostics, `upgrade_world` supplies a second project-relative `.mcworld` and requires at least two cycles. After the first clean shutdown, the adapter verifies the same level name and a traversal-safe archive, preserves the world database and `level.dat`, and replaces only embedded behavior/resource packs plus their world bindings. The result records both artifact hashes and every overlaid file hash. Benchmark B uses a fixture-only legacy pack to seed one v0 lock, upgrades to the production pack, verifies one imported record, and confirms that record remains readable on a third boot. This is BDS migration evidence, not a player-action, Windows, Realm, or console test.

Preview-only action diagnostics are isolated from consumer artifacts. Setting `preview_channel=true` requires an exact `bds_version`; the harness then passes both `VERSION=<exact>` and `PREVIEW=true` to the pinned wrapper. Benchmark B can build a separate GameTest-enabled world containing `@minecraft/server-gametest`, spawn a SimulatedPlayer, and classify observed actions only as `simulated_player_integration`. Positive claims require every cycle, log probe, console probe, and content-log cleanliness check to pass. This experimental route cannot establish physical-player gameplay, stable-API suitability, Marketplace suitability, Realm behavior, or console behavior.

Preview 1.26.50.20 synthetic `useItemOnBlock` testing exposed a module-version limitation: the test pack's `@minecraft/server` 2.10 subscriber received the SimulatedPlayer, while the production pack's declared stable 2.0 subscriber received an interaction object without the contract-required `player`. The production handler now denies such malformed interactions without throwing. This synthetic interaction is not accepted as production adapter evidence; a physical stable client is still required.
