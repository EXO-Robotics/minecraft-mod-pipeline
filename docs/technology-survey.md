# Technology Survey

## Interoperability

### Geyser

Geyser translates Java and Bedrock protocol traffic. It is valuable evidence that
edition-specific translation tables, registries, packet translators, and runtime
boundaries can be maintained at scale. It does not turn a Java mod into native
Bedrock content; its own FAQ describes client-side mod content as unsupported in
the general case. The compiler should study its translation philosophy rather
than embed Geyser.

### Hydraulic

Hydraulic is a companion to Geyser for Bedrock players joining modded Java servers.
It is useful for compatibility boundaries and content discovery, but it preserves
the Java server as the authoritative runtime. Our compiler has the opposite goal:
produce a Bedrock-native runtime.

### Floodgate

Floodgate handles Bedrock-account authentication into Java server networks. It is
not part of the content compiler.

### MCProtocolLib

MCProtocolLib is a Java client/server communication library. It may become useful
for a future black-box runtime probe, but protocol transport should stay outside
the ModIR and backend compiler.

## Resource and mapping conversion

PackConverter/Thunder is the clearest candidate for a resource frontend. Its
repository describes itself as a Java resource-pack-to-Bedrock converter and
explicitly says it does not fully create custom item mappings. Rainbow fills a
different Geyser custom-item mapping problem. We should use adapters or borrowed
concepts, not assume either produces native Bedrock gameplay behavior.

## Java analysis

- JavaParser: rich Java AST and a business-friendly dual-license model; preferred
  source frontend for recognized registration and event patterns.
- Spoon: a complete source model and source transformation API; useful if we need
  source-level provenance or transformations, with MIT/CeCILL-C licensing.
- ASM: bytecode visitor/tree analysis; preferred low-level JAR facts frontend.
- CFR/Vineflower: decompilers for readable fallback evidence; decompiled output
  must be marked lower-confidence than original source or bytecode facts.

The baseline scanner currently has no Java dependency. It uses metadata, archive
paths, and conservative source signals so the IR contract can be tested first.

## Bedrock backend

Microsoft's pack manifest documentation makes the pack identity, module type,
dependencies, and script entry point explicit. Behavior packs cover data-driven
gameplay such as entities, loot, spawn rules, recipes, and trade tables. Script API
extends this with JavaScript/TypeScript control over gameplay. GameTest provides a
possible validation backend, but its experimental/versioned surface must be
treated as a target-profile concern.

The local server confirms this backend shape in practice: its live world uses
behavior/resource pack UUID references, custom entities, spawn rules, recipes,
features, structures, models, animations, and resource assets.

## Compiler architecture references

- LLVM demonstrates a stable intermediate representation shared by analysis and
  multiple code-generation backends.
- Babel demonstrates plugin/preset transformation boundaries.
- Roslyn demonstrates exposing syntax and semantic models as a compiler platform.

Our ModIR should borrow these boundaries without pretending gameplay semantics are
equivalent to a conventional typed language compiler.

