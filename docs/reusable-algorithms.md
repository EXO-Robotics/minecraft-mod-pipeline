# Reusable Algorithms and Integration Candidates

| Algorithm or component | Source | Use in compiler | Status |
|---|---|---|---|
| Edition translation tables and protocol boundary isolation | Geyser | Design reference for capability/translation boundaries | Reference |
| Custom Java resource-pack conversion | PackConverter/Thunder | Resource frontend adapter | Adopt candidate |
| Geyser custom item mapping and attachable conventions | Rainbow | Optional mapping/compatibility frontend | Reference |
| Java metadata/dependency discovery | Forge/Fabric/Quilt metadata formats; Hydraulic concepts | Mod inventory frontend | Baseline implemented |
| Java source AST construction | JavaParser | Source frontend | Planned dependency |
| Source model and provenance | Spoon | Optional richer frontend | Planned alternative |
| Bytecode visitor/tree analysis | ASM | JAR frontend | Planned dependency |
| Readable decompilation | CFR/Vineflower | Fallback evidence | Optional adapter |
| Pack manifest generation | Bedrock manifest contract | Backend | Baseline implemented |
| Namespaced pack asset layout | Bedrock behavior/resource pack conventions | Backend | Baseline implemented |
| Script event/schedule runtime | Bedrock Script API | Behavior backend | Scaffold implemented |
| Structure-based gameplay validation | GameTest | Validation backend | Planned |
| Stable IR + multiple backends | LLVM | Core architecture reference | Adopted concept |
| Plugin/preset transforms | Babel | Frontend/backend extension model | Adopted concept |
| Syntax + semantic model exposure | Roslyn | Evidence graph and review tooling | Adopted concept |

The baseline intentionally does not copy source code from these projects. It
records adapters and design references; any future dependency must go through a
license and build-compatibility review.

