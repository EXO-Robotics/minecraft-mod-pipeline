# Minecraft Reconstruction Compiler

An evidence-backed assisted compiler that reconstructs validated Java mod intent as deterministic Minecraft Bedrock add-ons. It does not translate Java byte-for-byte and it never hides unsupported behavior behind arbitrary generated code.

## Proven baseline

The currently tested semantic profile accepts the included dependency-free Fabric-style Java source fixture. It extracts registrations, triggers, actions, persistent state, boss phases, form intent, approximations, unsupported hooks, and full source provenance into versioned ModIR/BehaviorIR. Loader metadata inventory supports Fabric, Quilt, modern/legacy Forge, NeoForge, CurseForge, Modrinth, and the compiler's directory-modpack manifest; those metadata readers are not claims of full semantic loader support.

The planner gives every feature one explicit strategy: `DIRECT`, `SCRIPTED_EQUIVALENT`, `RECONSTRUCTED`, `BEHAVIORAL_APPROXIMATION`, `VISUAL_APPROXIMATION`, `MANUAL_REDESIGN`, or `UNSUPPORTED`. Persistent JSON overrides survive regeneration.

## Run

```sh
PYTHONPATH=src python3 -m mccompiler scan \
  --input tests/fixtures/representative_mod \
  --output out/representative-ir.json \
  --bedrock-server /Users/blakegrove/Desktop/bedrock-server

PYTHONPATH=src python3 -m mccompiler compile \
  --input tests/fixtures/representative_mod \
  --output out/representative \
  --overrides overrides.json

PYTHONPATH=src python3 -m mccompiler validate --path out/representative
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Compilation writes:

```text
out/representative/
├── behavior_pack/
├── resource_pack/
├── scripts/
├── tests/
├── reports/
├── conversion-manifest.json
└── converted-mod.mcaddon
```

Pack UUIDs, JSON ordering, generated modules, ZIP member ordering, timestamps, and archive bytes are deterministic for the same semantic input, target, capability database, and overrides.

## Architecture

The boundaries are scanner → loader/source/bytecode analyzers → evidence → intent/ModIR/BehaviorIR → fingerprints → capability/pattern planner → Bedrock backend → layered validator → runtime harness → report. Published schemas live in `src/mccompiler/schemas`; architectural decisions and current primary-source research live in `docs/adr` and `docs/research`.

The compiled-JAR profile uses `javap` from a local OpenJDK to reconstruct the tested annotation-and-call vocabulary with lower-confidence bytecode provenance. The representative source-free JAR must produce the same 15 behavior fingerprints and state declarations as source mode. Without `javap`, class constants remain inventory evidence and no semantic bytecode support is claimed.

See [docs/user-guide.md](docs/user-guide.md) for IR contracts, adapters, patterns, overrides, generation, validation, runtime reproduction, and current limitations.
