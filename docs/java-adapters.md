# Java frontend adapters

## Adapter contract

Loader adapters emit loader-neutral evidence and IR. Metadata detection is not semantic support. Every fact records input mode, source location, extraction rule and analyzer version, confidence, conflicts, and review state. Unsupported constructs produce diagnostics rather than empty output.

## Modern Fabric target coverage

Fixtures must use authentic, compile-only stubs for representative `ModInitializer` entrypoints, item/block/entity and block-entity registration, callbacks, server ticks, persistent state, networking registration, data components, mixins, resources, and data generation. Source and compiled-JAR modes must agree on the facts each supported pattern proves.

## Forge 1.7.10 target coverage

Fixtures must represent `@Mod` lifecycle handlers, `GameRegistry`, `EntityRegistry`, `TileEntity`, `IWorldGenerator`, `IExtendedEntityProperties`, item/block methods, event and tick handlers, `SimpleNetworkWrapper`, sided proxies, access transformers, coremods, reflection, and custom renderers. Coremods and renderer assumptions generally become risk or unsupported evidence, not invented behavior.

## Compiled-JAR mode

The planned bytecode fact layer includes class, annotation, field, method, invocation, constant, control-flow, and resource-reference facts. It records archive and class hashes, tool/JDK versions, nested archives, missing dependencies, obfuscation, and lower confidence. Adverse fixtures cover stripped debug data, lambdas, nested classes, missing dependencies, multi-release archives, and malformed input.

## Current qualification and rule

A loader is semantically supported only after authentic source fixtures, compiled-JAR fixtures, explicit expected facts, source/JAR agreement for supported patterns, and honest degradation tests pass. The current worktree adds authentic-pattern Fabric and Forge 1.7.10 source fixtures and scoped extractors, with passing metadata/source-evidence tests. This is an initial source-pattern slice, not complete loader support; authentic compiled-JAR parity, broader APIs, adverse bytecode fixtures, and corpus qualification remain missing.
