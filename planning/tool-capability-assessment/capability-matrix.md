# Proven-conversion capability matrix

No row implies physical-client, multiplayer, console, rights, or Marketplace approval.

Evidence levels and outcomes are defined canonically in `capability-matrix.json`. Runtime wording is deliberately narrower than the classification.

## Content and assets

| Feature | Level / outcome | Java → Bedrock | Evidence / runtime | Fidelity / AI | Risk / suitability |
|---|---|---|---|---|---|
| Items | `PROVEN_ORIGINAL_BENCHMARK` / `DIRECT` | Item registration and properties → Bedrock item JSON plus components | `GENERATOR`, `CLOCKWORK_BDS`, `CLOCKWORK_CREATOR_TOOLS`; BDS pack load; no physical use | High for basic identity/properties; Supply components and cleared assets | Client behavior and assets; Marketplace: Conditional; console: LOW |
| Blocks | `PROVEN_REAL_MOD` / `DIRECT` | Block registration and properties → Bedrock block JSON plus custom handlers | `GENERATOR`, `DOORLOCK_BDS`; BDS pack load and bounded adapters | High for basic definitions; Reconstruct custom state | Physical interaction untested; Marketplace: Conditional; console: LOW |
| Recipes | `PROVEN_REAL_MOD` / `DIRECT` | Shaped/shapeless registration → Bedrock recipe JSON | `GENERATOR`, `DOORLOCK_BDS`; Static/Creator Tools only | High for bounded recipes; Resolve ingredients/tags | Crafting gameplay untested; Marketplace: Conditional; console: LOW |
| Loot tables | `STATIC_ONLY` / `DIRECT` | Drops and reward pools → Bedrock loot JSON | `GENERATOR`, `VALIDATION`; Static only | Simple pools only; Author complex conditions | Focused generator blocked; Marketplace: Conditional; console: LOW |
| Textures | `STATIC_ONLY` / `MANUAL_REDESIGN` | Resource textures → Original/cleared Bedrock textures | `GENERATOR`, `LIMITATIONS`; Asset validation only | No semantic conversion proof; Create/map assets | Rights and atlas budget; Marketplace: Rights blocked until reviewed; console: MEDIUM |
| Localization | `STATIC_ONLY` / `DIRECT` | Language resources → Bedrock lang files | `GENERATOR`, `VALIDATION`; Static only | Structural, not translation quality; Review wording/locales | Coverage; Marketplace: Conditional; console: LOW |
| Sounds | `STATIC_ONLY` / `MANUAL_REDESIGN` | Sound resources and calls → Mapped/original Bedrock sounds | `CAPABILITY_CATALOG`, `GENERATOR`; Static only | Mapping unproved; Author definitions and cleared audio | Rights/concurrency; Marketplace: Rights blocked until reviewed; console: MEDIUM |
| Models | `ARCHITECTURAL_SUPPORT` / `MANUAL_REDESIGN` | Java models/renderers → Original Bedrock geometry/controllers | `GENERATOR`, `LIMITATIONS`; Placeholder/static only | Low without reauthoring; Model and animate | Geometry/render budgets; Marketplace: Conditional; console: HIGH |
| Structures | `STATIC_ONLY` / `BEDROCK_NATIVE_RECONSTRUCTION` | Templates/placement code → Rebuilt Bedrock structure and placement | `GENERATOR`, `LIMITATIONS`; Placeholder/static only | Not source-equivalent yet; Rebuild content and placement | Current generated structure is placeholder; Marketplace: Conditional; console: HIGH |
| Spawn rules | `STATIC_ONLY` / `DIRECT` | Biome/density conditions → Bedrock spawn rules | `GENERATOR`, `CAPABILITY_CATALOG`; Static only | Generic rules; Java semantics not preserved; Balance ecology | Density/despawn; Marketplace: Conditional; console: MEDIUM |
## Item and combat

| Feature | Level / outcome | Java → Bedrock | Evidence / runtime | Fidelity / AI | Risk / suitability |
|---|---|---|---|---|---|
| Item use | `PROVEN_ORIGINAL_BENCHMARK` / `STABLE_SCRIPT_EQUIVALENT` | Use callback → Stable item-use event handler | `CLOCKWORK_BDS`; Preview SimulatedPlayer adapter | Event primitive proven; Implement feature behavior | Physical launcher chain pending; Marketplace: Conditional; console: LOW |
| Item use on block | `PROVEN_ORIGINAL_BENCHMARK` / `STABLE_SCRIPT_EQUIVALENT` | Use-on context → Stable before-use-on handler | `CLOCKWORK_BDS`; Preview adapter | Primitive proven; Implement semantics | Physical/controller pending; Marketplace: Conditional; console: LOW |
| Melee hit | `PROVEN_ORIGINAL_BENCHMARK` / `STABLE_SCRIPT_EQUIVALENT` | Attack callback → Entity-hit event | `CLOCKWORK_BDS`; Preview SimulatedPlayer adapter | Primitive proven; Map attribution/effects | Physical multiplayer pending; Marketplace: Conditional; console: LOW |
| Entity hurt | `PROVEN_ORIGINAL_BENCHMARK` / `STABLE_SCRIPT_EQUIVALENT` | Damage callback → Entity-hurt event | `CLOCKWORK_BDS`; Preview adapter | Primitive proven; Map source semantics | Damage-source edge cases; Marketplace: Conditional; console: LOW |
| Entity death | `PROVEN_ORIGINAL_BENCHMARK` / `STABLE_SCRIPT_EQUIVALENT` | Death callback → Entity-die event | `CLOCKWORK_BDS`; Preview adapter | Primitive proven; Integrate loot/progression | Attribution; Marketplace: Conditional; console: LOW |
| Projectiles | `PROVEN_ORIGINAL_BENCHMARK` / `BEDROCK_NATIVE_RECONSTRUCTION` | Custom projectile class → Bedrock projectile entity and scripted launch | `CLOCKWORK_BDS`, `CAPABILITY_CATALOG`; Preview launch/collision/cleanup | Mechanic primitive proven; Author damage/visuals | Physical aiming and load; Marketplace: Conditional; console: MEDIUM |
| Projectile entity impact | `PROVEN_ORIGINAL_BENCHMARK` / `STABLE_SCRIPT_EQUIVALENT` | Entity impact callback → Projectile-hit-entity event | `CLOCKWORK_BDS`; Preview adapter | Primitive proven; Implement outcome | Ownership/damage; Marketplace: Conditional; console: MEDIUM |
| Projectile block impact | `PROVEN_ORIGINAL_BENCHMARK` / `STABLE_SCRIPT_EQUIVALENT` | Block impact callback → Projectile-hit-block event | `CLOCKWORK_BDS`; Preview adapter | Primitive proven; Implement block policy | Griefing/state; Marketplace: Conditional; console: MEDIUM |
| Explosions | `STATIC_ONLY` / `STABLE_SCRIPT_EQUIVALENT` | Explosion calls → Stable createExplosion equivalent | `GENERATOR`, `CAPABILITY_CATALOG`; Handler/static tests only | API path only; Set ownership/griefing policy | Multiplayer and spikes; Marketplace: Conditional; console: HIGH |
| Status effects | `PROVEN_RUNTIME_PRIMITIVE` / `STABLE_SCRIPT_EQUIVALENT` | Potion/effect application → Stable addEffect | `CLOCKWORK_BDS`; Direct Preview API and observations | Primitive proven; Map stacking/duration | Physical player pending; Marketplace: Conditional; console: LOW |
| Cooldowns | `PROVEN_RUNTIME_PRIMITIVE` / `STABLE_SCRIPT_EQUIVALENT` | Cooldown manager → Stable cooldown component/state | `CLOCKWORK_BDS`, `GENERATOR`; Internal/instrumented path | Primitive only; Design feedback/isolation | Physical observation pending; Marketplace: Conditional; console: LOW |
| Tool durability | `STATIC_ONLY` / `STABLE_SCRIPT_EQUIVALENT` | Item damage → Durability component/mutation | `GENERATOR`; Static/handler tests | Basic mutation only; Handle enchants/breakage | Inventory synchronization; Marketplace: Conditional; console: LOW |
| Area effects | `ARCHITECTURAL_SUPPORT` / `MANUAL_REDESIGN` | Radius query and fan-out → Bounded server-side target query | `CAPABILITY_CATALOG`, `LIMITATIONS`; No general pattern proof | Feature-specific; Design bounded targeting | Entity-loop spikes; Marketplace: Conditional; console: HIGH |
## State and progression

| Feature | Level / outcome | Java → Bedrock | Evidence / runtime | Fidelity / AI | Risk / suitability |
|---|---|---|---|---|---|
| Persistent player state | `STATIC_ONLY` / `STABLE_SCRIPT_EQUIVALENT` | Player capability/NBT → Dynamic properties with schema | `GENERATOR`, `IR_SCHEMAS`; Static only | Model exists; Define keys/migrations | Reconnect/isolation unproved; Marketplace: Conditional; console: MEDIUM |
| Persistent entity state | `PROVEN_ORIGINAL_BENCHMARK` / `STABLE_SCRIPT_EQUIVALENT` | Entity NBT → Entity dynamic properties | `CLOCKWORK_BDS`; Preview phase write/read and restart checkpoint | Bounded state proven; Define lifecycle policy | Unload/reload; Marketplace: Conditional; console: MEDIUM |
| Persistent block/location state | `PROVEN_REAL_MOD` / `BEDROCK_NATIVE_RECONSTRUCTION` | Tile/block state → Canonical world location records | `DOORLOCK_BDS`, `DOORLOCK_CONTRACTS`, `DOORLOCK_HANDLER`; Stable BDS adapter/restart | Strong bounded reconstruction; Map domain schema | Player-created state not proven; Marketplace: Conditional; console: MEDIUM |
| Versioned migrations | `PROVEN_REAL_MOD` / `BEDROCK_NATIVE_RECONSTRUCTION` | Save schema upgrades → Revisioned journaled migrations | `DOORLOCK_BDS`, `DOORLOCK_CONTRACTS`; Three boots, nonempty migration, interrupted recovery | Strong bounded proof; Author each migration | More interruption boundaries; Marketplace: Conditional; console: MEDIUM |
| Progression unlocks | `PROVEN_ORIGINAL_BENCHMARK` / `STABLE_SCRIPT_EQUIVALENT` | Advancement/capability flags → Versioned dynamic-property progression | `CLOCKWORK_BDS`; Preview adapter/checkpoint | Bounded primitive; Design progression graph | Player isolation; Marketplace: Conditional; console: MEDIUM |
| Ownership and permissions | `PROVEN_REAL_MOD` / `BEDROCK_NATIVE_RECONSTRUCTION` | Owner UUID/access checks → Server-authoritative identity records | `DOORLOCK_CONTRACTS`, `DOORLOCK_HANDLER`; Internal decisions and BDS adapters | Logic strong; gameplay pending; Define policy | Two-player test absent; Marketplace: Conditional; console: LOW |
| Shared credentials | `PROVEN_REAL_MOD` / `ACCEPTABLE_REDESIGN` | Passwords/access tokens → Digest-only credential authorization | `DOORLOCK_CONTRACTS`, `DOORLOCK_HANDLER`; Internal/static | Bedrock-native redesign; Design/security review | Human approval required; Marketplace: Conditional; console: LOW |
| Machine progress | `PROVEN_ORIGINAL_BENCHMARK` / `BEDROCK_NATIVE_RECONSTRUCTION` | Ticking tile entity → Batched persistent processing state | `CLOCKWORK_BDS`, `CAPABILITY_CATALOG`; One Preview machine cycle | Bounded cycle only; Design inventory/scheduler | Unload, contention, scale; Marketplace: Conditional; console: HIGH |
| Boss phases | `PROVEN_ORIGINAL_BENCHMARK` / `BEDROCK_NATIVE_RECONSTRUCTION` | Health/state phase logic → Scripted persistent state machine | `CLOCKWORK_BDS`; Three scheduled Preview phases | Transition primitive proven; Author encounter | Full combat/performance pending; Marketplace: Conditional; console: HIGH |
## Entities

| Feature | Level / outcome | Java → Bedrock | Evidence / runtime | Fidelity / AI | Risk / suitability |
|---|---|---|---|---|---|
| Custom mobs | `STATIC_ONLY` / `BEDROCK_NATIVE_RECONSTRUCTION` | Entity registration/class → Bedrock entity plus authored components | `GENERATOR`, `CAPABILITY_CATALOG`; Minimal shell/BDS load | Low until authored; Behavior/assets/animation | Aggregate entity load; Marketplace: Conditional; console: HIGH |
| Entity spawning | `PROVEN_RUNTIME_PRIMITIVE` / `STABLE_SCRIPT_EQUIVALENT` | Spawn calls/rules → Spawn rules or stable spawnEntity | `CLOCKWORK_BDS`, `GENERATOR`; Preview spawn/lifecycle | Primitive proven; Density/despawn policy | Entity count; Marketplace: Conditional; console: MEDIUM |
| Growth stages | `PROVEN_ORIGINAL_BENCHMARK` / `BEDROCK_NATIVE_RECONSTRUCTION` | Age/stage state → Scripted entity phase transition | `CLOCKWORK_BDS`; Preview growth stage | Bounded transition; Design timing/visuals | Unload/long duration; Marketplace: Conditional; console: MEDIUM |
| Basic AI | `ARCHITECTURAL_SUPPORT` / `BEDROCK_NATIVE_RECONSTRUCTION` | Java goals → Authored Bedrock behavior components | `CAPABILITY_CATALOG`, `GENERATOR`; No meaningful AI proof | Requires reauthoring; Design components | Behavior/performance; Marketplace: Conditional; console: HIGH |
| Lifecycle events | `PROVEN_ORIGINAL_BENCHMARK` / `STABLE_SCRIPT_EQUIVALENT` | Spawn/hit/hurt/death hooks → Stable Bedrock events | `CLOCKWORK_BDS`; Preview adapters | Primitives proven; Connect systems | Attribution; Marketplace: Conditional; console: MEDIUM |
| Multiphase bosses | `PROVEN_ORIGINAL_BENCHMARK` / `BEDROCK_NATIVE_RECONSTRUCTION` | Boss class/AI/phases → Bedrock entity plus scripted phase machine | `CLOCKWORK_BDS`; Three transitions only | Partial encounter proof; Author AI/telegraphs/loot | Multiplayer and console load; Marketplace: Conditional; console: HIGH |
| Minibosses | `ARCHITECTURAL_SUPPORT` / `BEDROCK_NATIVE_RECONSTRUCTION` | Elite entity variants → Reusable boss/entity archetype | `CAPABILITY_CATALOG`; No independent benchmark | Unproven integration; Author encounter | Needs benchmark; Marketplace: Conditional; console: HIGH |
| Pets | `ARCHITECTURAL_SUPPORT` / `MANUAL_REDESIGN` | Tameable companion → Original Bedrock companion design | `CAPABILITY_CATALOG`, `LIMITATIONS`; No companion benchmark | Feature-specific; Design ownership/follow/persistence | Multiplayer/teleport; Marketplace: Conditional; console: HIGH |
| Mounts | `NOT_SUPPORTED` / `UNSUPPORTED` | Rider/vehicle entity → No current pattern | `LIMITATIONS`; None | None; Reject or new benchmark | Controls/sync; Marketplace: Not ready; console: HIGH |
| Complex Java AI | `NOT_SUPPORTED` / `MANUAL_REDESIGN` | Goals/brains/pathfinding → Manual Bedrock reauthoring | `LIMITATIONS`; None | Cannot translate generally; Redesign per creature | High CPU/design; Marketplace: Not ready; console: HIGH |
## Interaction and UI

| Feature | Level / outcome | Java → Bedrock | Evidence / runtime | Fidelity / AI | Risk / suitability |
|---|---|---|---|---|---|
| Forms | `STATIC_ONLY` / `ACCEPTABLE_REDESIGN` | GUI/config screen → Stable server-ui forms | `GENERATOR`, `DOORLOCK_CONTRACTS`; Internal/static only | Not pixel-equivalent; Design controller flow | Physical display untested; Marketplace: Conditional; console: LOW |
| Controller-accessible configuration | `STATIC_ONLY` / `ACCEPTABLE_REDESIGN` | Keyboard/mouse config → Forms/in-world controls | `DOORLOCK_CONTRACTS`; Design only | Proposed; UX design | Controller/accessibility gate; Marketplace: Conditional; console: LOW |
| Java keybinding replacement | `STATIC_ONLY` / `BEDROCK_NATIVE_RECONSTRUCTION` | Keybind plus packet → Item use/use-on-block/form | `FRONTENDS`, `CAPABILITY_CATALOG`; Static extraction only | Control changes; Propose replacement | Human/controller approval; Marketplace: Conditional; console: LOW |
| Custom Java GUI replacement | `ARCHITECTURAL_SUPPORT` / `MANUAL_REDESIGN` | Custom Screen/Menu → Forms, containers, or in-world controls | `FRONTENDS`, `LIMITATIONS`; Inventory only | No arbitrary translation; Redesign UX | Usability/sync; Marketplace: Conditional; console: MEDIUM |
| Inventory screens | `NOT_SUPPORTED` / `MANUAL_REDESIGN` | Custom container screen → No general implementation | `LIMITATIONS`; None | None generally; Create alternative | Controller/synchronization; Marketplace: Not ready; console: MEDIUM |
| In-world controls | `PROVEN_ORIGINAL_BENCHMARK` / `BEDROCK_NATIVE_RECONSTRUCTION` | Block/entity interaction → Stable interaction events | `CLOCKWORK_BDS`; Preview block/use adapters | Primitive proven; Design control language | Physical controller pending; Marketplace: Conditional; console: LOW |
| Multiplayer authorization | `PROVEN_REAL_MOD` / `BEDROCK_NATIVE_RECONSTRUCTION` | Server access checks → Authoritative ownership policy | `DOORLOCK_CONTRACTS`, `DOORLOCK_HANDLER`; Internal/adapter only | Logic implemented; Define policy | No two-player session; Marketplace: Conditional; console: LOW |
## World systems

| Feature | Level / outcome | Java → Bedrock | Evidence / runtime | Fidelity / AI | Risk / suitability |
|---|---|---|---|---|---|
| Structures | `STATIC_ONLY` / `BEDROCK_NATIVE_RECONSTRUCTION` | Structure generation/placement → Rebuilt Bedrock templates and placement | `GENERATOR`; Placeholder/static only | Not source-equivalent; Build and place | Size/density; Marketplace: Conditional; console: HIGH |
| Encounter placement | `ARCHITECTURAL_SUPPORT` / `BEDROCK_NATIVE_RECONSTRUCTION` | World encounter hooks → Bounded structure/spawn controller | `CAPABILITY_CATALOG`; None | Unproven; Design distribution | Density/chunk load; Marketplace: Conditional; console: HIGH |
| Spawn management | `STATIC_ONLY` / `BEDROCK_NATIVE_RECONSTRUCTION` | Spawn/despawn manager → Rules plus bounded scheduler | `GENERATOR`, `CAPABILITY_CATALOG`; Generic definitions only | Partial; Set caps/ecology | Entity budget; Marketplace: Conditional; console: HIGH |
| Controlled random events | `ARCHITECTURAL_SUPPORT` / `BEDROCK_NATIVE_RECONSTRUCTION` | Random world events → Budgeted deterministic event table | `CAPABILITY_CATALOG`, `DISTILLATION_OUTPUT`; No integrated chaos benchmark | Original redesign; Design limits/cooldowns | Highest selected scope risk; Marketplace: Conditional; console: HIGH |
| Portals | `ARCHITECTURAL_SUPPORT` / `ACCEPTABLE_REDESIGN` | Portal/dimension transfer → Structure plus teleport approximation | `CAPABILITY_CATALOG`; No lifecycle proof | Approximation; Design destination/safety | Persistence/client; Marketplace: Conditional; console: MEDIUM |
| Dimensions | `NOT_SUPPORTED` / `UNSUPPORTED` | Custom dimension → No robust equivalent | `LIMITATIONS`; None | None; Original replacement or defer | Platform blocker; Marketplace: Not ready; console: HIGH |
| Custom world generation | `ARCHITECTURAL_SUPPORT` / `MANUAL_REDESIGN` | Biomes/features/noise → Manual Bedrock-native design | `FRONTENDS`, `LIMITATIONS`; Inventory only | Unproven; Reauthor | Major engine/performance work; Marketplace: Not ready; console: HIGH |
| Global simulation | `PROVEN_RUNTIME_PRIMITIVE` / `BEDROCK_NATIVE_RECONSTRUCTION` | Always-on world ticks → Strictly batched scheduler | `CLOCKWORK_BDS`, `CAPABILITY_CATALOG`; Bounded machine/boss scheduling | Only bounded work; Budget and redesign | Scaling; Marketplace: Conditional; console: HIGH |
## Java architecture

| Feature | Level / outcome | Java → Bedrock | Evidence / runtime | Fidelity / AI | Risk / suitability |
|---|---|---|---|---|---|
| Fabric registrations | `STATIC_ONLY` / `DIRECT` | Fabric metadata/Registry calls → Recognized-fact extraction | `FRONTENDS`; Fixture tests | Bounded vocabulary; Resolve unknowns | Broad ecosystem unproved; Marketplace: Analysis only; console: LOW |
| Forge registrations | `STATIC_ONLY` / `DIRECT` | Forge metadata/registries → Recognized-fact extraction | `FRONTENDS`; Fixture tests | Selected surfaces; Resolve event bodies | Broad modern Forge unproved; Marketplace: Analysis only; console: LOW |
| Legacy Forge registrations | `STATIC_ONLY` / `DIRECT` | 1.7.10 registration/events/packets → Recognized-fact extraction | `FRONTENDS`; Fixture tests | Bounded patterns; Resolve semantics | Dynamic behavior; Marketplace: Analysis only; console: LOW |
| Source analysis | `PROVEN_REAL_MOD` / `DIRECT` | Java source and resources → Static evidence extraction | `FRONTENDS`, `DOORLOCK_BDS`; DoorLock reconstruction plus fixtures | Useful, not arbitrary semantics; Interpret unresolved code | Incomplete/dynamic behavior; Marketplace: Analysis only; console: LOW |
| Compiled-JAR evidence | `STATIC_ONLY` / `DIRECT` | Class files/constants/javap → Bounded bytecode fact extraction | `FRONTENDS`; Parity fixture tests | Bounded vocabulary; Handle obfuscation/dependencies | Not decompilation completeness; Marketplace: Analysis only; console: LOW |
| Mixins | `STATIC_ONLY` / `UNSUPPORTED` | Injected bytecode → Detect and fail closed | `FRONTENDS`, `LIMITATIONS`; Detection tests | No conversion; Recover intent or reject | Hidden engine semantics; Marketplace: Not ready; console: HIGH |
| Coremods | `STATIC_ONLY` / `UNSUPPORTED` | Class transformers → Detect and fail closed | `FRONTENDS`, `LIMITATIONS`; Detection tests | No conversion; Recover intent or reject | Engine patch; Marketplace: Not ready; console: HIGH |
| Java networking | `STATIC_ONLY` / `BEDROCK_NATIVE_RECONSTRUCTION` | Packets/channels → Server-authoritative Bedrock interaction redesign | `FRONTENDS`, `CAPABILITY_CATALOG`; Extraction only | Intent-level, not protocol; Redesign transport/control | Multiplayer tests; Marketplace: Conditional; console: MEDIUM |
| Custom renderers | `STATIC_ONLY` / `UNSUPPORTED` | Renderer/model pipeline → Original Bedrock presentation | `FRONTENDS`, `LIMITATIONS`; Detection only | No translation; Reauthor assets/controllers | Visual/performance; Marketplace: Not ready; console: HIGH |
| Native/JVM libraries | `NOT_SUPPORTED` / `UNSUPPORTED` | JNI/JVM dependency → Cannot execute in Add-On | `LIMITATIONS`; None | None; Replace subsystem or reject | Platform blocker; Marketplace: Not ready; console: HIGH |
| Cross-mod APIs | `ARCHITECTURAL_SUPPORT` / `MANUAL_REDESIGN` | External mod API calls → System-level redesign | `FRONTENDS`, `LIMITATIONS`; Dependency inventory only | No semantic conversion; Rebuild integration | Large dependency surface; Marketplace: Not ready; console: HIGH |

Evidence IDs resolve through `evidence-index.json`.
