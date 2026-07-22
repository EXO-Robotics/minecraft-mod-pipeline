# Validation and test limits

Accessed: **2026-07-22**

## Layered gates

1. **Schema/static:** archive safety, JSON parse/schema, manifest graph, UUID/version shape, identifier/path references, texture/localization/sound references, Script API imports, forbidden beta APIs, generated-code lint, provenance coverage.
2. **Package/import:** `.mcaddon` archive opens, both packs are discovered, dependencies resolve, and the exact target runtime imports without pack errors.
3. **Activation:** packs are applied to a fresh test world and the content log contains no critical errors.
4. **Runtime smoke:** generated content can be granted/placed/summoned; event subscriptions initialize; forms and schedulers execute.
5. **Behavioral:** fixture-specific trigger/condition/action assertions, timing tolerance, state transitions, multiplayer ownership, persistence through save/restart/reload, and negative cases.
6. **Performance:** bounded per-tick work, entity/machine scale, scheduler backlog, dynamic-property growth and ticking-area usage.

## GameTest

GameTest provides structure-backed miniature environments, JavaScript registration/setup, and assertions. Microsoft explicitly describes the framework as experimental and warns that APIs can change with limited notice. It is valuable for generated behavioral fixtures but must be isolated behind an adapter and pinned to a target profile. Source: [Building your first GameTest](https://learn.microsoft.com/en-us/minecraft/creator/documents/gametestbuildyourfirstgametest?view=minecraft-bedrock-stable), [GameTest API](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server-gametest/minecraft-server-gametest?view=minecraft-bedrock-stable).

## Limitations requiring independent checks

- Static correctness cannot establish import, activation or actual event timing.
- Import success cannot establish that content is reachable or behaviorally equivalent.
- GameTest experimental status and world assumptions prevent it from being the sole release gate.
- Form UI needs a real player/client and asynchronous cancellation/error handling; dedicated-server automation alone cannot fully judge presentation.
- Natural spawning is probabilistic and constrained by population, biome, light, simulation distance and player proximity. Test deterministic summon behavior separately from statistical spawn-rule behavior.
- Ticking areas change simulation but do not guarantee natural spawning without nearby players; they also have hard limits and performance costs. Source: [simulation/ticking guide](https://learn.microsoft.com/en-us/minecraft/creator/documents/simulationrenderdistanceguide?view=minecraft-bedrock-stable).
- Structures must be tested for placement, rotation/mirroring policy, entities, block states and namespace collisions—not merely archive presence.
- Persistence requires a process restart and world reload. Reading a property immediately after writing it is not a persistence test.
- Dedicated server, Realms, local client and Marketplace environments are not interchangeable compatibility targets.

## Evidence standard

A runtime result records server/client version, world seed/settings/experiments, active pack UUIDs/versions, commands or test entrypoint, timestamps/ticks, content log excerpt, expected/actual assertions and artifact hashes. Unsupported runtime access must be reported as `not_run` with the precise missing prerequisite, never converted into a pass.

