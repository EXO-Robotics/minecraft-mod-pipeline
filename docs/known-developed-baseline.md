# Known Developed Baseline

This document records what we can responsibly adopt, reference, or build around
as of 2026-07-22. “Direct” means a dependency or output can plausibly be used
without importing the project’s entire runtime. “Reference” means the design or
data is valuable, but it solves a different problem.

| Subsystem | Existing project or source | Baseline decision | Confidence |
|---|---|---|---|
| Java/Bedrock protocol model | [Geyser](https://github.com/GeyserMC/Geyser) | Reference translation tables and edition-difference conventions; do not reuse the protocol runtime for pack compilation | High |
| Bedrock account bridge | [Floodgate](https://github.com/GeyserMC/Floodgate) | Reference only; authentication is outside the compiler | High |
| Minecraft protocol transport | [MCProtocolLib](https://github.com/GeyserMC/MCProtocolLib) | Optional future runtime-test adapter, not part of the first compiler | High |
| Modded Java server compatibility | [Hydraulic](https://github.com/GeyserMC/Hydraulic) | Reference compatibility strategies and supported-content boundaries | Medium |
| Java resource conversion | [PackConverter / Thunder](https://github.com/GeyserMC/PackConverter) | Candidate resource frontend; first baseline only preserves/copies safe assets | High |
| Geyser custom item mappings | [Rainbow](https://github.com/GeyserMC/Rainbow) | Reference mapping and attachable ideas; not the native Bedrock backend | High |
| Java source AST | [JavaParser](https://javaparser.org/) | Preferred source frontend once Java dependencies are introduced | High |
| Java source analysis/transformation | [Spoon](https://spoon.gforge.inria.fr/) | Alternative when source rewriting and model completeness matter | High |
| Java bytecode | [ASM](https://asm.ow2.io/) | Preferred bytecode facts frontend | High |
| Java decompilation | [CFR](https://github.com/leibnitz27/cfr), [Vineflower](https://github.com/Vineflower/vineflower) | Fallback evidence sources, never treated as authoritative source | High |
| Bedrock pack manifests | [Microsoft manifest docs](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/manifestreference/packmanifestdocument?view=minecraft-bedrock-stable) | Direct backend contract | High |
| Bedrock data-driven content | [Behavior Pack docs](https://learn.microsoft.com/en-us/minecraft/creator/documents/behaviorpackfromscratch?view=minecraft-bedrock-stable) | Direct backend contract for recipes, entities, loot, spawn rules, and related content | High |
| Bedrock scripting | [Script API docs](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/?view=minecraft-bedrock-stable) | Generated runtime backend for behavior that is not expressible in pack JSON | High |
| Bedrock gameplay tests | [GameTest docs](https://learn.microsoft.com/en-us/minecraft/creator/documents/gametestbuildyourfirstgametest?view=minecraft-bedrock-stable) | Validation backend; version/experimental status must be pinned | High |
| Compiler IR design | [LLVM IR](https://llvm.org/docs/LangRef.html), [Babel plugins](https://babel.dev/docs/plugins), [Roslyn SDK](https://learn.microsoft.com/en-us/dotnet/csharp/roslyn-sdk/) | Architecture references for stable IR, pluggable frontends, and semantic models | High |

## What is genuinely missing

The existing projects cover transport, protocol understanding, resource conversion,
custom mappings, Java parsing, bytecode inspection, and Bedrock pack/script
surfaces. The novel compiler work is still:

- Evidence-backed Gameplay Intent extraction
- Edition-neutral Behavior IR
- Bedrock capability matching and strategy planning
- Reconstruction of machines, GUIs, packets, mixins, and custom dimensions
- Fidelity scoring tied to tests rather than file counts

## Baseline implementation

The local tool implements a conservative version of the missing pipeline now:

```text
mod/JAR/modpack
  -> inventory frontend
  -> evidence-backed ModIR
  -> capability strategy planner
  -> Bedrock pack scaffold
  -> validation/report
```

