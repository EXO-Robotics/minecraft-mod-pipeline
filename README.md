# Minecraft Reconstruction Compiler

An evidence-backed assisted compiler that reconstructs validated Java mod intent as deterministic Minecraft Bedrock add-ons. It does not translate Java byte-for-byte and it never hides unsupported behavior behind arbitrary generated code.

The private GitHub repository is the authoritative project copy; local clones
are working copies. Project software is available under the [MIT License](LICENSE).
Repository processing and external-disclosure boundaries are documented in
[AI_PROCESSING_POLICY.md](AI_PROCESSING_POLICY.md).

## Proven baseline

The currently tested semantic profile accepts the included dependency-free Fabric-style Java source fixture. It extracts registrations, triggers, actions, persistent state, boss phases, form intent, approximations, unsupported hooks, and full source provenance into versioned ModIR/BehaviorIR. Loader metadata inventory supports Fabric, Quilt, modern/legacy Forge, NeoForge, CurseForge, Modrinth, and the compiler's directory-modpack manifest; those metadata readers are not claims of full semantic loader support.

Large, evidence-inventoried modpacks can also be reduced to a deterministic,
progression-coherent planning scope with `mccompiler distill-modpack`. The
distiller treats 25% as estimated conversion effort, enforces prerequisites,
rights and static console constraints, emits the required planning reports, and
keeps qualitative review adjustments separate from deterministic scores. See
`docs/modpack-distillation.md`.

The planner gives every feature one explicit strategy: `DIRECT`, `SCRIPTED_EQUIVALENT`, `RECONSTRUCTED`, `BEHAVIORAL_APPROXIMATION`, `VISUAL_APPROXIMATION`, `MANUAL_REDESIGN`, or `UNSUPPORTED`. Persistent JSON overrides survive regeneration.

## Run

```sh
PYTHONPATH=src python3 -m mccompiler scan \
  --input tests/fixtures/representative_mod \
  --output out/representative-ir.json \
  --bedrock-server /path/to/bedrock-server

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

## Bootstrap another pipeline

The complete Codex reconstruction skill pack is tracked under `skills/`.
Install the compiler and skills from a fresh clone with:

```sh
python3 tools/bootstrap_pipeline.py --check-only --json
python3 tools/bootstrap_pipeline.py --json
```

See [docs/bootstrap.md](docs/bootstrap.md) for prerequisites, safe skill
replacement, verification, and the first reconstruction invocation.

## Automated multi-worker campaigns

The repository includes a durable SQLite-backed orchestration layer for
dependency-aware Java-to-Bedrock campaigns. It provides bounded threaded
workers, transactional claims, retries, leases, dead-worker recovery,
quarantine, append-only events, verified transfers, and process receipts.
Clean-room production commands fail closed without a hash-bound sandbox profile
and a separately validated production-process receipt.
The Studio is the production host; the included clean-room launcher is
Studio-local and does not depend on the MacBook's paths or runtime.

```sh
.venv/bin/mccompiler-orchestrator --db .mccompiler/orchestration.sqlite3 init
.venv/bin/mccompiler-orchestrator --db .mccompiler/orchestration.sqlite3 \
  create --definition /absolute/path/to/campaign.json
.venv/bin/mccompiler-orchestrator --db .mccompiler/orchestration.sqlite3 \
  run --concurrency 4 --runtime-root .mccompiler/runtime
```

For the no-UI, conversation-facing factory workflow, see
[docs/factory-overseer.md](docs/factory-overseer.md). See also
[docs/orchestration.md](docs/orchestration.md) and the editable
`examples/orchestration/java-to-bedrock-campaign.example.json` campaign
definition.
