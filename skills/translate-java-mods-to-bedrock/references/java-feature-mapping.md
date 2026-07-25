# Java feature mapping for Bedrock and PS4

Use this reference after evidence extraction and before product selection.

## Decision order

1. State the player-visible invariant without Java names or implementation.
2. Separate gameplay, presentation, collision, persistence, networking, and
   configuration requirements.
3. Select the simplest stable Bedrock representation.
4. Define caps, cleanup, restart, multiplayer ownership, and migration before
   accepting the mapping.
5. Classify unsupported or distinctive expression as an original substitute,
   approved omission, deferment, or block.

## Common mappings

| Java feature family | Preferred Bedrock treatment | Watch for |
|---|---|---|
| Items, recipes, loot, simple blocks | `NATIVE_MAPPING` | Preserve vanilla behavior; avoid scripts without need |
| Block states and metadata | Native states/permutations | State cardinality, collision permutations, migration |
| Tile entities/capabilities | `STABLE_SCRIPT_REDESIGN` with versioned dynamic-property registry | Shard/record byte caps, CAS revisions, quarantine |
| Event buses and callbacks | Stable world/block/item events | Duplicate delivery, stale work, lifecycle cleanup |
| Timers/cooldowns | Bounded generation-token callbacks | One callback per action, restart policy, cancellation |
| Java packets/network sync | Server-authoritative state plus Bedrock events/properties | Never recreate Java packet topology |
| Custom keybinds | Controller-simple use, sneak-use, use-on-block, or native form | Verify actual client event delivery |
| GUIs/config screens | Native container/form if stable; otherwise item interaction or `DEFER` | Controller ergonomics and multiplayer authority |
| Custom renderers/facades | `ORIGINAL_SUBSTITUTE` with original fixed textures/geometry | No runtime texture copying; client visuals pending |
| Ghost/pass-through blocks | Native collision box or bounded state permutation | Rendering does not prove collision |
| One-way visual blocks | Honest two-sided directional substitute | No per-player or true one-way claim |
| Doors/trapdoors/multiblocks | Stable script-paired records and permutations | Atomic placement, partner cleanup, chunk boundaries |
| Redstone producers | `STABLE_SCRIPT_REDESIGN` using a prevalidated vanilla signal cell | Never overwrite non-air; retry unloaded cleanup |
| Redstone networks/wires | `CONSOLIDATE` into vanilla redstone transport | Do not build an unbounded script graph |
| Pressure/presence sensors | Local bounded entity query at a fixed interval | Entity filters, per-dimension active cap |
| Light observers | Stable local light sample and product-selected threshold | Exact Java analog curves are rarely required |
| Inventories/storage | Native container when supported; otherwise `DEFER` | Viewer state, double containers, save compatibility |
| Entities/AI | Native components and bounded goals | Population, pathfinding, spawn, particle budgets |
| Projectiles | Native projectile entity/components first | Simultaneous projectile cap and cleanup |
| World generation/structures | Structures and bounded placement rules | Seed parity is not required unless frozen |
| Dimensions/portals | Original overworld substitute or `DEFER/BLOCKED` | Do not fake unsupported dimension parity |
| Mixins/coremods/reflection | Extract the invariant, then redesign or block | Java hook parity is not a product requirement |
| External services/native libraries | `BLOCKED` unless replaced by offline Bedrock-native behavior | Console and Marketplace prohibit hidden dependencies |

## Persistent block-device pattern

- Key records by dimension and coordinate.
- Store schema version, product feature ID, owner, presentation state, linkage,
  stable state, and monotonic revision.
- Use fixed shard and per-dimension caps.
- Reconcile a fixed number of records at a fixed interval.
- Keep transient pulses, samples, and active caches out of persisted state.
- Clear transient state on script reload/restart.
- Quarantine unsupported records without world mutation.
- Remove a record only after its owned world artifact is cleared. Retain a
  retryable tombstone when the cell or paired block is unloaded or blocked.

## Rendering and asset rules

- Prefer ordinary block JSON and 16x16 original textures when custom geometry
  adds no function; mark Blockbench `NOT_APPLICABLE`.
- Use one render method within every material-instance group and across its
  finish permutations. Fully opaque pixels may remain visually opaque while
  using a common transparent pipeline.
- Keep textures below a cooperative creator/game root, preserve reciprocal pack
  dependencies when required, and validate the exact archive with Creator Tools
  and BDS.
- Treat arbitrary neighbor-texture copying, connected textures, tint/light
  delegation, and per-player rendering as separate unsupported requirements.

## Segment production waves

1. Shared namespace, state, persistence, ownership, cleanup, and event contracts.
2. Independent native/basic blocks and controls.
3. Multiblocks, observers, visual substitutes, and other consumers.
4. Cross-feature signal, lifecycle, restart, and migration integration.
5. Exact-package audit, mutation, Creator Tools, Stable/Preview BDS, and repair.

Require superseded candidates and hashes to remain traceable after every repair.

## PS4-oriented acceptance

- No experiments, keyboard-only interaction, external service, or global scan.
- Cap records, active devices, callbacks, entity queries, particles, projectiles,
  pathfinding entities, and simultaneous effects.
- Keep a lower-cost presentation path for credible worst-case scenes.
- Use BDS for server logic/load evidence only.
- Keep desktop client, Realm, controller, real multiplayer/reconnect,
  split-screen, and physical PS4 pending until executed on the frozen package.
