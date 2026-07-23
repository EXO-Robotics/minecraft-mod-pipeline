# What is currently convertible

## A. Convert now with strong confidence

- Basic items, blocks, and bounded recipes into structurally valid packs.
- DoorLock-style canonical persistent location records, revisioned migrations, recovery, ownership decisions, cleanup, and bounded reconciliation—subject to physical gameplay qualification.
- Stable event primitives for item use/use-on-block, projectile entity/block impacts, entity hit/hurt/death, entity spawning/lifecycle, and bounded scheduled state transitions.
- Bedrock-native projectile launch/collision/cleanup, direct effect invocation, one bounded machine cycle, growing-entity phase transition, progression checkpoint, and three boss-phase transitions.
- Deterministic package/world creation, schemas, static/API/assets/performance checks, Creator Tools invocation, and BDS diagnostic receipts.

“Strong confidence” here means repository-proven bounded patterns, not complete physical-client features.

## B. Convert with AI reconstruction and targeted testing

- Special weapons, explosions, durability, area effects, cooldown feedback, and combat attribution.
- Persistent player/entity progression, machines, multiplayer ownership, shared credentials, forms and in-world controller controls.
- Custom mobs, minibosses, full bosses, pets, spawn ecology, structures, encounters, portals-as-teleports, and controlled random events.
- Textures, sounds, models, animations, localization, complex loot, and original presentation.
- Java packets/keybindings as server-authoritative Bedrock interactions.

These have evidence, scaffolding, or reusable patterns, but require intent recovery, protected implementation, native redesign, and physical/client/multiplayer/performance tests.

## C. Not yet ready

- Arbitrary mixins/coremods: detected but not semantically converted.
- Native/JVM libraries: cannot execute in Bedrock Add-Ons.
- Java custom renderers: require original Bedrock presentation.
- Dimensions and arbitrary custom world generation: no robust proven pipeline.
- Custom inventory screens and arbitrary Java GUIs: no general stable replacement.
- Mounts/vehicles and complex Java AI: no qualified runtime pattern.
- Arbitrary Java networking and cross-mod API semantics: inventory/intent only.
- Console/Realm/Marketplace claims: missing physical device, delivery, rights, and publisher evidence.
- Full focused generation for projectile, loot, spawn rule, animation, form, and script scaffold: callable handlers are deliberately blocked even where full-pack/custom paths exist.
