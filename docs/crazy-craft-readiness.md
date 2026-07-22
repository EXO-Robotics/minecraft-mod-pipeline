# Crazy Craft readiness

Assessment date: **2026-07-22**  
Status: **Not ready for a full Crazy Craft conversion; ready to define the qualification gates.**

Crazy Craft is an integration target, not a single representative mod. A modpack can combine different loaders/generations, inter-mod APIs, configs, scripts, assets, dimensions/world generation, client rendering, custom networking and behavior that exists only through interactions. The compiler must prove itself on controlled fixtures and a legally reviewable modpack inventory before attempting conversion.

## Entry requirements

- Exact pack name/version/distribution source and Minecraft/loader version are identified.
- Every JAR/config/script/resource is hashed and inventoried, including nested JARs and duplicate mod IDs.
- Licenses and redistribution/transformation permissions are classified per artifact; unknown or blocked assets are excluded from packaging.
- Dependency, ordering, side-only, mixin/coremod/access-transformer and custom networking relationships are mapped.
- Source availability is recorded. JAR-only modules receive bytecode confidence limits.
- The target BDS profile and client requirements are frozen and runtime-probed.

## Compiler qualification gates

| Gate | Required evidence |
|---|---|
| Frontend | Fabric/Quilt/Forge/NeoForge/legacy metadata fixtures; source and JAR equivalence fixtures; deterministic repeated scans |
| Semantics | Representative item/block/recipe/loot/resource interactions; projectiles/effects/cooldowns; persistent player/entity/block-location state; machines; entities; multiphase boss; spawns; structures; forms |
| Planning | Every unit assigned an allowed strategy with separate confidence/fidelity/risk values and override persistence |
| Backend | Deterministic BP/RP/script generation, reference closure, stable UUIDs, modular runtime and provenance coverage |
| Runtime | Import/activation on exact BDS, no critical content errors, mechanics execute, save/restart/reload passes, multiplayer ownership checked |
| Scale | Mini-modpack dependency/identifier conflict handling; bounded scheduler and entity load tests; report remains navigable |
| Honesty | At least one approximation and one unsupported feature are accurately reported and remain blocked from false equivalence claims |

## Inventory triage classes

- **Likely direct:** conventional recipes, loot tables, tags, textures, sounds, language assets, simple items/blocks and some structures.
- **Likely scripted/reconstructed:** event-driven item interactions, cooldowns, projectiles/explosions, persistent machines, forms, custom entity state and boss phases.
- **High risk/manual:** custom dimensions, complex world generation, advanced rendering/shaders, Java GUIs, capability systems, cross-mod energy/inventory APIs and loader-driven configuration.
- **Usually unsupported without redesign:** arbitrary JVM/native libraries, coremods/mixins that rewrite engine internals, custom packets requiring Java clients, and rendering behavior with no Bedrock surface.

## Recommended pilot

Select 3–5 legally clear mods spanning declarative content, event behavior, persistence/machines, entities/bosses and one known unsupported primitive. Compile them together as a mini-modpack, resolve identifier/dependency conflicts, run fresh-world and reload tests, then compare the generated report against a human behavior inventory. Only expand when discrepancies are categorized and fixtures added.

## Stop conditions

Do not begin bulk conversion if provenance is incomplete, the target BDS Script API profile has not executed a probe pack, source/JAR results are nondeterministic, state fails restart/reload, pack interactions are not represented in IR, or unsupported features are being hidden as cosmetic success.

Primary references: [Fabric metadata](https://docs.fabricmc.net/develop/loader/fabric-mod-json), [Forge mod files](https://docs.minecraftforge.net/en/latest/gettingstarted/modfiles/), [NeoForge mod files](https://docs.neoforged.net/docs/gettingstarted/modfiles/), [Bedrock behavior packs](https://learn.microsoft.com/en-us/minecraft/creator/documents/behaviorpackfromscratch?view=minecraft-bedrock-stable), [Script API](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server/minecraft-server?view=minecraft-bedrock-stable), [latest platform guidance](https://learn.microsoft.com/en-us/minecraft/creator/documents/practices/latestplatformversion?view=minecraft-bedrock-stable), [Minecraft EULA](https://www.minecraft.net/en-us/eula). All accessed 2026-07-22.
