# Java frontend adapters

## Adapter contract

Loader adapters emit loader-neutral evidence and IR. Metadata detection is not semantic support. Every fact records input mode, source location, extraction rule and analyzer version, confidence, conflicts, and review state. Unsupported constructs produce diagnostics rather than empty output.

## Modern Fabric target coverage

Fixtures must use authentic, compile-only stubs for representative `ModInitializer` entrypoints, item/block/entity and block-entity registration, callbacks, server ticks, persistent state, networking registration, data components, mixins, resources, and data generation. Source and compiled-JAR modes must agree on the facts each supported pattern proves.

## Forge 1.7.10 target coverage

Fixtures must represent `@Mod` lifecycle handlers, `GameRegistry`, `EntityRegistry`, `TileEntity`, `IWorldGenerator`, `IExtendedEntityProperties`, item/block methods, event and tick handlers, `SimpleNetworkWrapper`, sided proxies, access transformers, coremods, reflection, and custom renderers. Coremods and renderer assumptions generally become risk or unsupported evidence, not invented behavior.

## Compiled-JAR mode

The loader-neutral bytecode fact layer includes class, annotation, field, method, invocation, constant, and resource-reference facts with lower-confidence provenance. It diagnoses unavailable analyzers, missing dependencies, suspected obfuscation, unresolved semantics, unsupported multi-release selection, invalid archives, and `javap` failures. Control-flow reconstruction, decompiler integration, and broader adverse-corpus coverage remain incomplete.

## Current qualification and rule

A loader is semantically supported only after authentic source fixtures, compiled-JAR fixtures, explicit expected facts, source/JAR agreement for supported patterns, and honest degradation tests pass. Defined Fabric and Forge source/JAR facts have parity tests that run when a usable JDK exists; this host currently records an explicit skip because no usable JDK is installed. Conventional nested Fabric source trees and registration helpers are covered. This remains scoped pattern support, not complete loader support; broader APIs, decompiler adapters, adverse bytecode fixtures, and real-corpus qualification remain incomplete.
