# Compiler contracts and reproduction guide

> This guide describes the current research baseline. The planned Marketplace product architecture, target profiles, console protocol, agent workflow, and implementation-status matrix are indexed in [documentation-index.md](documentation-index.md). Do not interpret planned contracts as current compiler features.

## Supported profiles and boundaries

The production-tested semantic profile is the legally clean Fabric-style fixture vocabulary in `tests/fixtures`. `SOURCE_PROJECT`, source-free `COMPILED_JAR` with OpenJDK `javap`, and `MODPACK_DIRECTORY` are tested input modes. Fabric metadata and this profile are semantic support; Quilt, Forge, NeoForge, legacy Forge, CurseForge, and Modrinth readers are inventory-only until dedicated semantic fixtures pass.

The stage boundary is scanner → frontend → evidence/intent → ModIR/BehaviorIR → planner → backend → validator/runtime evidence → reports. JSON is the frontend/backend boundary. No backend rule is permitted to invent semantic behavior without evidence or an explicit override.

## ModIR and BehaviorIR

ModIR 1.0.0 is defined by `src/mccompiler/schemas/modir-1.0.0.json`. It is edition-neutral and contains metadata, dependency graph inputs, content, assets, registries, behavior, scoped state, presentation, world/UI/network intent, unsupported hooks, diagnostics, tests, and evidence. Migration from 0.1.0 is deterministic and fail-closed.

BehaviorIR 1.0.0 is defined by `src/mccompiler/schemas/behavior-ir-1.0.0.json`. Each behavior has an owner, constrained trigger/condition/action vocabulary, state reads/writes, feedback and presentation requirements, evidence, confidence, diagnostics, and a versioned normalized fingerprint. There is deliberately no arbitrary-code action.

## Frontend adapters

`src/mccompiler/semantics.py` implements the tested Java-common source profile. `frontends/javap_analyzer.py` implements its compiled-JAR equivalent; `frontends/jar_bytecode.py` retains conservative class-constant evidence. Loader metadata discovery remains separate in `scan.py`. New adapters must emit the same IR and evidence fields, add source/JAR fixtures, and avoid claiming loaders based only on metadata parsing.

## Capabilities and patterns

`capabilities.json` is a versioned target catalog. A capability records stable/native/scripted support, modules, performance, multiplayer and persistence properties, limitations, reference implementation, and tests. `patterns.json` contains deterministic semantic predicates, never source-text guesses. To add a pattern, give it a namespaced family ID, constrained trigger/action requirements, an explicit strategy, a positive fixture, and a near-miss fixture proving it does not overmatch.

## Overrides

Overrides use `schemas/overrides-1.0.0.json`. Every entry requires a target and human provenance. A reviewer may select a strategy, patch constrained behavior fields, map identifiers or dependencies, select state storage, accept/reject or omit an approximation, configure extracted cooldown/projectile actions through a behavior patch, attach licensing notes, or declare a reviewed custom module. Overrides are stored separately from upstream mods and participate in deterministic identity. AI proposals remain advisory until represented by a separate human override.

## Backend

The backend writes linked Behavior and Resource Packs, modular event/runtime/UI/test scripts, generated resources, provenance and conversion reports, then packages lexicographically with fixed ZIP timestamps and UUID5 identities. Unsupported, manually redesigned, conflicted, or evidence-free features are omitted and reported. The scheduler uses active-object registration, bounded work, lifecycle cleanup, and a per-tick budget rather than global scans.

## Validation and runtime testing

Static validation covers JSON, schemas, state/dependencies, manifests/API modules, JavaScript syntax/imports, identifiers, semantic content references, resources, localization, components, and deterministic archive metadata. Integration validation checks plan coverage and behavior provenance. Runtime never passes by inference: it requires `reports/runtime-evidence.json` with logs and structured checks.

The generated `mccompiler:test` ScriptEvent harness exercises state conditions/actions in BDS. Runtime evidence records pack activation, contract tests, persistent reload state, machine processing, and boss phases. Pre-existing errors from unrelated server packs must be isolated by pack path and must never be copied into a passing evidence artifact.

## Exact reproduction

```sh
PYTHONPATH=src MCCOMPILER_JAVAP=/opt/homebrew/opt/openjdk/bin/javap \
  python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
PYTHONPATH=src python3 -m mccompiler compile \
  --input tests/fixtures/representative_mod --output out/representative
PYTHONPATH=src python3 -m mccompiler validate \
  --path out/representative
# After the BDS harness has written reports/runtime-evidence.json:
PYTHONPATH=src python3 -m mccompiler validate \
  --path out/representative --runtime --record
```

An AI agent can run the isolated boot diagnostic through the structured operation interface with `adapter: "BDS_DOCKER"`, `execute: true`, a project-relative `world`, an image pinned by `@sha256`, and an exact `bds_version`. If the wrapper must download that exact server build into a fresh volume, both `network_mode: "bridge"` and `allow_bootstrap_network: true` are required. The operation never publishes gameplay ports and does not claim action-driven behavior validation.

Compile twice into separate directories and compare `sha256sum` of `converted-mod.mcaddon` to verify regeneration. The committed tests do this automatically.

## Current limitations

- Semantic Java support is a constrained, tested fixture profile rather than general Fabric/Forge API understanding.
- Complex Java AI, dimensions/world generation, vehicles, arbitrary GUIs, native libraries, custom protocols, shaders, mixins, and coremods require new patterns, manual redesign, or rejection.
- Generated textures/geometry are explicit placeholders when legally reusable source binaries are absent.
- BDS proves server-side behavior; real-client visuals, form ergonomics, and multiplayer ownership need client/multi-user qualification before a public conversion claim.
- A full Crazy Craft conversion is intentionally out of scope; `crazy-craft-readiness.md` defines the later profile gates and legal constraints.
