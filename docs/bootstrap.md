# Bootstrap a new Java-to-Bedrock pipeline

This repository contains the compiler, schemas, capability catalogs, runtime
harness, tests, benchmark fixtures, and the complete repository-tracked Codex
skill pack. A fresh clone does not require skill files from the original
developer's home directory.

## Requirements

- Python 3.11 or newer
- Git
- Codex for skill-driven reconstruction
- Docker for Stable/Preview Bedrock Dedicated Server qualification
- A local OpenJDK `javap` for compiled-JAR semantic analysis
- Blockbench and Creator Tools only for the gates that use them

## Install

From the repository root:

```sh
python3 tools/bootstrap_pipeline.py --check-only --json
python3 tools/bootstrap_pipeline.py --json
```

The second command installs `mccompiler` into the active Python environment and
copies every directory under `skills/` into `${CODEX_HOME:-~/.codex}/skills`.
The bootstrap writes a repository-path `.pth` file and two small command
launchers into the active Python environment. It does not invoke `pip` or
download Python packages.
Use a virtual environment if the compiler should remain isolated:

```sh
python3 -m venv .venv
.venv/bin/python tools/bootstrap_pipeline.py --json
```

Existing divergent skills are never overwritten by default. Pass
`--replace-skills` to preserve them under
`${CODEX_HOME:-~/.codex}/skill-backups/<timestamp>/` and install the repository
copies.

## Verify

```sh
mccompiler --help
python3 -m unittest tests.test_pipeline_bootstrap -v
```

The complete development suite uses `pytest`; install it in the development
environment and run `PYTHONPATH=.:src pytest -q`. Runtime conversion and the
bootstrap installer themselves have no third-party Python dependency.

Docker BDS remains qualification infrastructure, not physical-console evidence.
The portable pipeline may report BDS and simulated-player gates while keeping
client, Realm, controller, split-screen, PS4, and Marketplace approval statuses
separate.

## Start a reconstruction

Invoke `$translate-java-mods-to-bedrock` with an authorized Java source tree,
JAR, or modpack inventory. The controller skill routes bounded production,
integration, Blockbench authoring, independent audit, deterministic packaging,
and exact-artifact BDS qualification through the other vendored skills.

Do not copy `.venv`, Docker volumes, downloaded BDS binaries, private source
evidence, credentials, or local runtime caches between pipeline installations.
