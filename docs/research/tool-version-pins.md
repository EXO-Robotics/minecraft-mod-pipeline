# Tool and target version pins

Accessed: **2026-07-22**

Pins are compatibility inputs and belong in the emitted report. A moving `latest` is prohibited in reproducible compilation.

## Baseline pins

| Component | Baseline | Policy and source |
|---|---:|---|
| Compiler language | Python `>=3.11,<3.15` | Use only documented language/library behavior within this range. Local research host is Python 3.14.6. [Python version status](https://devguide.python.org/versions/) |
| Bytecode fallback | JDK 21 `javap` | Require a detected executable matching major 21 for canonical bytecode evidence; fail or downgrade with an explicit diagnostic if absent. [JDK 21 `javap`](https://docs.oracle.com/en/java/javase/21/docs/specs/man/javap.html) |
| Target server profile | Bedrock Dedicated Server `1.21.132.3` | Workspace target pin; runtime must report its actual version before activation tests. Microsoft downloads are mutable, so retain acquired-artifact hash and license record. [Bedrock server download](https://www.minecraft.net/en-us/download/server/bedrock) |
| Manifest | format `2` for the BDS 1.21 profile | Use the stable profile accepted by the pinned server; do not adopt manifest v3 merely because reference pages describe it. [manifest overview](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/manifestreference/packmanifestdocument?view=minecraft-bedrock-stable) |
| `@minecraft/server` | `1.18.0` initially; runtime-probe before freezing release profile | Exact stable dependency only. The implementation must maintain a tested profile table because API/package releases continue to move. [npm package](https://www.npmjs.com/package/@minecraft/server), [script versioning](https://learn.microsoft.com/en-us/minecraft/creator/documents/scripting/script-versioning?view=minecraft-bedrock-stable) |
| `@minecraft/server-ui` | `1.3.0` initially; runtime-probe before freezing release profile | Exact stable dependency only, paired with the target BDS profile. [npm package](https://www.npmjs.com/package/@minecraft/server-ui), [stable API reference](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server-ui/minecraft-server-ui?view=minecraft-bedrock-stable) |
| Node/npm | validation tooling only; Node 24 LTS target | Generated Bedrock JavaScript runs in Minecraft, not Node. Local research host Node 25.6.1/npm 11.12.0 is not a runtime compatibility claim. [Node releases](https://nodejs.org/en/about/previous-releases) |

The Script API values above are conservative candidate pins for the local 1.21.132 profile, not claims about the newest registry packages. Before implementation declares the profile production-ready, a probe pack must import and execute each dependency on the exact BDS build. The probe result then becomes a checked-in profile fixture.

## Content format policy

Microsoft's [latest platform version guidance](https://learn.microsoft.com/en-us/minecraft/creator/documents/practices/latestplatformversion?view=minecraft-bedrock-stable) applies different minimum rules to blocks, items, recipes, spawn rules, entities, loot tables, resource entities, sounds and other families. The compiler therefore maintains a version table keyed by `(target_profile, content_kind)` and records the selected value in every generated-file provenance record.

## Reproducibility record

Each build report should include compiler version/commit, schema versions, analyzer versions, Python/JDK versions, target profile, API dependencies, platform, input and override hashes, capability/pattern catalog hashes, generated tree hash, and validator/runtime versions. Network lookups are forbidden during normal deterministic compilation.

