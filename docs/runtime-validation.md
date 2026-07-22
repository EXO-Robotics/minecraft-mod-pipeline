# Runtime validation record

Date: 2026-07-22. Target: local Dockerized Bedrock Dedicated Server 1.26.33.2, world `Bedrock level`.

The representative behavior and resource packs were installed in isolated `mccompiler_representative_bp` and `mccompiler_representative_rp` directories and referenced by deterministic UUID from the existing world pack lists.

Observed gates:

- Pack activation: BDS reported `representative reconstructed behavior` at pack-stack position 06.
- Content schemas: after correcting manifest metadata, current block components, and recipe unlock data, no `representative` content error appeared during startup.
- Script execution: BDS emitted `[Scripting] [mccompiler] runtime initialized behaviors=10 persistent_boot=1`.
- Persistence and reload: after a full server restart, BDS emitted `persistent_boot=2`, proving a generated world dynamic property survived reload.
- Content exposure: in a temporary ticking area, console smoke tests reported `Block placed` for `representative:aether_machine`, `Object successfully summoned` for `representative:clockwork_golem` and `representative:rift_boss`, and `Replaced slot.container slot 0 with 1 * item.representative:phase_blade`.
- Cleanup: the two test entities, machine block, test chest/item, and temporary ticking area were removed after the probe.

The server contains pre-existing errors from unrelated packs such as Just Biome, Underground Biomes, and Immersive Fauna. Those errors were isolated by pack path and were not attributed to generated output.

This record proves import/discovery, activation, generated content registration, Script API startup, and state persistence. It does not claim that every extracted player interaction has been exercised by a real client; those mechanics remain in the generated behavioral test plan.
