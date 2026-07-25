# Animation and pathing

## Provenance

Author keyframes from the asset's own proportions and pivots. Record whether each clip is authored, generated, commissioned, or licensed. Do not copy keyframe arrays or distinctive motion from a mod or Marketplace pack.

Use official Bedrock schemas and vanilla-like engineering patterns as technical references. Component names such as `minecraft:navigation.walk` are platform APIs, not creative assets.

Official references:

- Entity modeling and animation: https://learn.microsoft.com/en-us/minecraft/creator/documents/entitymodelingandanimation
- Animation controllers: https://learn.microsoft.com/en-us/minecraft/creator/documents/introductiontoanimationcontrollers
- Entity components guide: https://learn.microsoft.com/en-us/minecraft/creator/documents/entitycomponentsguide
- Walking navigation: https://learn.microsoft.com/en-us/minecraft/creator/reference/content/entityreference/examples/entitycomponents/minecraftcomponent_navigation.walk

## Conservative console recipe

Start with:

- One idle loop of 3-5 seconds.
- One locomotion loop of 0.8-1.2 seconds.
- One inexpensive look animation driven by target rotations.
- At most one state controller for basic movement.
- A base movement speed around passive vanilla creatures.
- A restrained turn rate.
- Random stroll with a nonzero interval.
- Small look and path-search distances.
- No natural spawn rule until population stress testing.

Tune for the creature; these are starting points, not guarantees.

## Test ladder

1. **Parse:** Validate every JSON document.
2. **Resolve:** Check that animation bones exist, client aliases resolve to clips/controllers, and controller aliases resolve.
3. **Preview:** Load geometry, texture, and animation JSON in Blockbench. Scrub every keyframe, inspect loop seams, and play at slow and normal speed.
4. **Runtime:** Import the resource and behavior packs into Bedrock. Summon the entity and trigger idle, walking, stopping, turning, damage/panic, water-edge, and obstruction cases.
5. **Persistence:** Save/reload and reconnect a second client.
6. **Stress:** Test 1, 10, 20, then the intended maximum entity count. Watch frame rate and simulation behavior.
7. **Console:** Repeat the worst cases on physical PS4.

Static and Blockbench tests cannot prove pathfinding. Desktop runtime tests cannot prove PS4 performance.

## Stable BDS qualification

Server-console commands act only in loaded chunks. Before summoning at fixed coordinates, create a small bounded ticking area, for example:

```text
tickingarea add circle 0 70 0 1 asset_test true
```

Use an allowlisted command set. Put repeatable stress in bounded function files, such as exactly 20 summon entries, and provide a separate cleanup function. Record selector counts and the function completion output. Restart the server and repeat summon, stress, cleanup, and count checks.

When the candidate contains scripts and the qualification adapter requires
script initialization, a harmless stable startup marker may prove the runtime
loaded. For asset-only packs, configure the harness with
`require_script_runtime: false`; never invent gameplay or a marker script only
to satisfy an inappropriate harness default.

BDS proves pack loading and server-side command/adapter behavior for the exercised path. It does not prove client rendering, animation playback, controller behavior, combat feel, Realm transfer, split screen, or physical-console performance.
