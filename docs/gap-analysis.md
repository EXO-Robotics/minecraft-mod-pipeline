# Gap Analysis

## Solved or adoptable

- Java mod archive inventory
- Fabric/Quilt/Forge/NeoForge metadata extraction
- Dependency graph construction
- Java source and bytecode tooling candidates
- Resource-pack conversion candidate
- Bedrock manifest generation
- Bedrock behavior/resource pack layout
- Basic recipes, loot, spawn, structure, and asset inventory

## Partially solved

- Custom item mappings
- Models and animations
- Entity conversion
- Custom blocks
- Worldgen and structures
- Runtime Script API integration
- Bedrock GameTest validation

## Missing and novel

- Gameplay Intent extraction
- Cross-edition Behavior IR
- Strategy selection based on actual Bedrock capability/version
- State schema inference and migrations
- GUI reconstruction
- Machine/block-entity reconstruction
- Packet-intent replacement
- Mixin intent extraction
- Fidelity scoring tied to observed behavior
- Pack-level conflict/performance planning

## First engineering risks

1. A file path is evidence of possible content, not proof of behavior.
2. Decompiled code is an interpretation, not authoritative source.
3. Cross-mod behavior can be invisible until runtime.
4. Bedrock APIs and GameTest availability vary by target version.
5. Asset and mod licenses may prohibit redistribution.

