# Java mod and JAR inputs

Accessed: **2026-07-22**

## Loader metadata

| Ecosystem | Discovery file | What it establishes | Source |
|---|---|---|---|
| Fabric | `fabric.mod.json` at JAR root | Mod identity/version, environment, entrypoints, mixins, dependencies, nested JAR declarations and license metadata | [Fabric metadata reference](https://docs.fabricmc.net/develop/loader/fabric-mod-json), [Fabric Loader overview](https://docs.fabricmc.net/develop/loader/) |
| Quilt | `quilt.mod.json` at JAR root | Quilt loader identity, metadata, entrypoints, dependencies and provided capabilities; a Fabric metadata file may also be relevant to compatibility | [Quilt Loader JSON schema](https://github.com/QuiltMC/quilt-json-schemas/blob/master/quilt_mod_json/quilt_mod_json.schema.json), [Quilt Loader repository](https://github.com/QuiltMC/quilt-loader) |
| Forge | `META-INF/mods.toml` | Mod-file and mod metadata, dependencies, loader requirements, side constraints; Java entrypoint convention is `@Mod` | [Forge mod files](https://docs.minecraftforge.net/en/latest/gettingstarted/modfiles/) |
| NeoForge | `META-INF/neoforge.mods.toml` | Mod-file/mod metadata, dependencies and loader constraints; `@Mod` classes remain relevant entrypoint evidence | [NeoForge mod files](https://docs.neoforged.net/docs/gettingstarted/modfiles/) |
| Legacy Forge/FML | commonly `mcmod.info`, manifest attributes, annotations | Historical identity and dependency hints; conventions vary by Minecraft/Forge generation | [Forge 1.12 mod information](https://docs.minecraftforge.net/en/1.12.x/gettingstarted/structuring/) |

The scanner should preserve the raw metadata document and record the exact archive path. It must not normalize away unknown keys: loader extensions and version-specific fields can be valuable evidence. A modpack is a dependency graph, not merely a directory of independent JARs; duplicate IDs, side-only mods, embedded JARs, ordering constraints and optional dependencies need explicit findings.

## Archive and resource evidence

A JAR is ZIP-based and may contain class files, loader metadata, `META-INF/MANIFEST.MF`, service descriptors, access wideners/transformers, mixin configurations, data packs, assets and nested libraries. The JDK `jar` tool is the authoritative archive utility reference: [Oracle `jar` command](https://docs.oracle.com/en/java/javase/21/docs/specs/man/jar.html).

Resource paths are strong evidence for declarative content. Typical Java assets include `assets/<namespace>/textures`, models, blockstates, sounds and language files; data commonly includes recipes, loot tables, tags, structures and world-generation JSON. Paths and JSON are evidence only: registrations or runtime code may replace, mutate or conditionally expose them.

## Source analysis

The deterministic source frontend should retain:

- package/import/type/member declarations and source line spans;
- annotations and their arguments;
- constructor and registration calls, including deferred registries and event subscriptions;
- call graphs and literal/data flow needed to identify triggers, conditions, actions and state;
- loader APIs, mixins, access transformers/wideners and reflection as explicit uncertainty signals;
- resource identifiers linked to registrations;
- conflicts when multiple analyses imply incompatible behavior.

Regex matches may seed candidates but are not sufficient semantic evidence. Findings should cite source file, type, method/field, line range, extraction rule and analyzer version.

## Bytecode fallback

`javap` is a JDK disassembler. `-c` emits bytecode, `-p` includes private members, `-s` emits descriptors, `-l` emits line/local-variable tables when present, `-v` exposes classfile details, and `--multi-release` selects a versioned class from a multi-release JAR. See [Oracle JDK 21 `javap`](https://docs.oracle.com/en/java/javase/21/docs/specs/man/javap.html).

Recommended deterministic invocation profile:

```text
javap -c -p -s -l -v --multi-release <target-java-release> <class>
```

The fallback can recover type/member signatures, annotations, constants, invoked methods/fields, control-flow instructions and optional debug line mappings. It generally cannot recover comments, original local names without debug tables, generic source constructs after erasure/desugaring, or the author's intent. Obfuscation, shading, generated classes, lambdas, mixins, reflection and custom class loaders reduce confidence. Therefore bytecode findings carry `source_mode=bytecode` and may not silently receive source-level confidence.

Multi-release JAR selection must be explicit. Oracle notes that classpath-form `javap` handling can otherwise show the base entry; the compiler must record the selected release and hash every analyzed archive entry.

