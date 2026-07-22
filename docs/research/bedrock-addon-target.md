# Bedrock add-on target

Accessed: **2026-07-22**

## Pack identity and composition

Every behavior/resource pack needs a manifest with a unique UUID, version, and modules. Modules identify `data`, `resources`, or `script`; dependencies may reference another pack by UUID/version or native Script API modules by name/version. See Microsoft's [pack manifest document](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/manifestreference/packmanifestdocument?view=minecraft-bedrock-stable), [dependency reference](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/manifestreference/dependency?view=minecraft-bedrock-stable), and [scripting introduction](https://learn.microsoft.com/en-us/minecraft/creator/documents/scripting/introduction?view=minecraft-bedrock-stable).

Compiler policy:

- deterministically derive UUIDs from compiler namespace, input fingerprint, target profile and module role;
- link behavior and resource packs explicitly;
- declare script dependencies with exact stable module versions;
- make `min_engine_version` and every content `format_version` target-profile decisions;
- emit a `.mcaddon` as an archive of complete packs, never as a substitute for validation.

## Content surfaces

Behavior packs carry gameplay definitions including entities, items, blocks, recipes, loot tables and spawn rules. Resource packs carry textures, models, sounds, client entity definitions and localization. Microsoft's [behavior-pack introduction](https://learn.microsoft.com/en-us/minecraft/creator/documents/behaviorpackfromscratch?view=minecraft-bedrock-stable), [custom items guide](https://learn.microsoft.com/en-us/minecraft/creator/documents/addcustomitems?view=minecraft-bedrock-stable), [custom block guide](https://learn.microsoft.com/en-us/minecraft/creator/documents/addcustomdieblock?view=minecraft-bedrock-stable), and [custom sounds guide](https://learn.microsoft.com/en-us/minecraft/creator/documents/addcustomsounds?view=minecraft-bedrock-stable) provide current pack layout examples.

The target profile follows Microsoft's [latest platform version guidance](https://learn.microsoft.com/en-us/minecraft/creator/documents/practices/latestplatformversion?view=minecraft-bedrock-stable). Different file families have different format-version rules; there is no sound global version string that can be stamped on every JSON document.

## Script API and forms

The stable `@minecraft/server` API supplies world, dimension, block, item, entity, event and scheduler surfaces. Forms are asynchronous builders from `@minecraft/server-ui`; `ActionFormData.show` can throw, cannot run in restricted-execution mode, and a form may be canceled when chat is open. Sources: [`@minecraft/server` reference](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server/minecraft-server?view=minecraft-bedrock-stable), [`System.runInterval`](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server/system?view=minecraft-bedrock-stable), [`ActionFormData`](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server-ui/actionformdata?view=minecraft-bedrock-stable).

Generated runtime code should subscribe centrally to world events, dispatch by identifiers/fingerprints, defer writes out of restricted before-event contexts, bound work per tick, and isolate form errors/cancellation. Preview or beta APIs are excluded unless a target profile explicitly opts in.

## Persistent state

World, entity and item-stack dynamic properties provide durable key/value storage through methods such as `getDynamicProperty` and `setDynamicProperty`. Sources: [`World` API](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server/world?view=minecraft-bedrock-stable), [`Entity` API](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server/entity?view=minecraft-bedrock-stable), [`ItemStack` API](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server/itemstack?view=minecraft-bedrock-stable).

Compiler policy: namespace every key; version stored records; validate type/size; provide migration; distinguish world/player/entity/block-location state; and test save/restart/reload. Block-location state generally needs a compiler-managed world-level index because a block is not a durable entity identity.

## Ticking and machines

`system.runInterval` can drive a bounded scheduler, but loaded/simulated world state remains a gameplay constraint. Ticking areas remain active outside nearby players, carry performance cost, and are limited; Microsoft documents up to 10 ticking areas with up to 100 chunks each. See [simulation distance and ticking areas](https://learn.microsoft.com/en-us/minecraft/creator/documents/simulationrenderdistanceguide?view=minecraft-bedrock-stable) and the [`/tickingarea` command](https://learn.microsoft.com/en-us/minecraft/creator/commands/commands/tickingarea?view=minecraft-bedrock-stable).

A compiler must not create one interval or ticking area per machine. Use a shared scheduler, chunk/location indexes, work budgets, invalidation on block changes, and explicit inactive/unloaded behavior. Persistent progress requires timestamps or stored counters plus a declared offline-progress policy.

## Entities, spawning and structures

Data-driven entities combine always-active components, component groups, and events that add/remove groups. Re-adding a group can reinitialize components such as timers. See [entity behavior introduction](https://learn.microsoft.com/en-us/minecraft/creator/documents/entitybehaviorintroduction?view=minecraft-bedrock-stable) and [entity events](https://learn.microsoft.com/en-us/minecraft/creator/documents/entityevents?view=minecraft-bedrock-stable).

Spawn rules bind to an entity identifier and express population control and condition sets; spawning is also affected by population caps, simulation distance, biome/light/block conditions and nearby players. See [entity spawning deep dive](https://learn.microsoft.com/en-us/minecraft/creator/documents/spawning/entityspawningdeepdive?view=minecraft-bedrock-stable).

`.mcstructure` templates live in behavior packs and may contain blocks and entities. Structures can be saved/loaded using structure blocks or commands and can participate in world-generation features. See [world generation overview](https://learn.microsoft.com/en-us/minecraft/creator/documents/world-generation?view=minecraft-bedrock-stable) and [structure blocks](https://learn.microsoft.com/en-us/minecraft/creator/documents/structureblockstutorial?view=minecraft-bedrock-stable).

## Known representation boundaries

Arbitrary Java bytecode, client render hooks, custom networking protocols, JVM libraries, loader mixins/coremods and native code cannot be directly hosted by Bedrock. The planner must choose among data-driven direct output, scripted equivalent, reconstruction, approximation, manual redesign and unsupported. Visual similarity and behavioral similarity must be scored separately.

