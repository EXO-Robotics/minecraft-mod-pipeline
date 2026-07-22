# Minecraft Compiler Baseline

This is the first runnable baseline for the Java-to-Bedrock reconstruction compiler.

It is intentionally dependency-free: the scanner and pack generator use Python's
standard library so the baseline can run before we choose JavaParser, ASM, a
resource converter, or a Bedrock schema package as production dependencies.

The baseline currently does four things:

1. Scans a Java mod JAR, source tree, or modpack directory.
2. Produces a normalized, evidence-backed ModIR JSON document.
3. Plans a Bedrock strategy for the discovered content and risk signals.
4. Generates a behavior-pack/resource-pack scaffold and `.mcaddon` archive.

It is not yet a semantic Java compiler. It deliberately reports unknown behavior
instead of inventing it.

## Quick start

From this directory:

```sh
PYTHONPATH=src python3 -m mccompiler scan \
  --input /path/to/mod-or-modpack \
  --output out/scan.json \
  --bedrock-server /Users/blakegrove/Desktop/bedrock-server

PYTHONPATH=src python3 -m mccompiler compile \
  --input /path/to/mod-or-modpack \
  --output out/generated \
  --bedrock-server /Users/blakegrove/Desktop/bedrock-server

PYTHONPATH=src python3 -m mccompiler validate --path out/generated
```

The compiler command writes:

```text
out/generated/
├── behavior_pack/
├── resource_pack/
├── conversion_ir.json
├── conversion_plan.json
├── conversion_report.md
└── generated.mcaddon
```

## Current scope

The scanner recognizes Fabric, Quilt, Forge/NeoForge TOML, legacy Forge
`mcmod.info`, CurseForge-style modpacks, and Modrinth indexes. It inventories
registries and assets from paths, extracts dependency metadata, detects source
signals, and preserves evidence paths for every result.

The generator creates valid pack manifests, links behavior and resource packs,
adds a configurable Script API module, copies safe texture/sound assets into a
namespaced source area, and emits a report describing what still needs semantic
reconstruction.

## Design rule

The JSON IR is the contract between frontends and backends. The first frontend is
small and conservative. Later frontends can add JavaParser source facts, ASM
bytecode facts, decompiler output, runtime traces, and human-reviewed behavior
intents without changing the Bedrock backend contract.

## Target profile

The local Bedrock server is used only as a read-only target profile. Its current
world pack UUIDs, server properties, content logging settings, and version marker
are included in scans when `--bedrock-server` is supplied. The generator still
uses its own UUIDs and never edits the live world.

