# Benchmark A: Original Marketplace showcase

Status: `EXECUTABLE_STATIC_BENCHMARK`, expanded two-cycle Preview diagnostic `PASSED`, and physical-platform qualification `UNVERIFIED`.

This benchmark contains a legally original source fixture that executes through the compiler's scanner, planner, Bedrock generator, and static validator. A separate experimental Preview world independently verifies item use/use-on-block, block interaction, projectile creation and entity/block impact, effect API invocation plus immediate/delayed observation, progression-state storage, one bounded machine cycle, entity spawn/growth, hit/hurt/death, three generated boss phases, cleanup, and a diagnostic checkpoint across restart. The normal-entity comparison proves that SimulatedPlayer can expose the tested speed effect; the generated player-owned launcher chain remains unavailable across the separate pack boundary and is not claimed. These narrow diagnostics do not claim a player-ready Add-On, physical-player gameplay, Marketplace clearance, or console verification.

Required features are defined in `project.yaml` and `expected-behavior.yaml`. A feature passes only when its named static, real-action, persistence, multiplayer, migration, controller, performance, and platform obligations have artifact-bound evidence.

The showcase must include one data-driven mechanic, one stable-script mechanic, one approved redesign, and one deliberately unsupported mechanic so reporting is tested across success and rejection paths.

Executable entrypoint: `fixture/`. Machine-readable quality, decision, rights, multiplayer, migration, and test contracts sit alongside it. Run:

```sh
PYTHONPATH=src python3 -m unittest tests.test_showcase_benchmark -v
```

Build the deterministic production artifacts with `tools/build_benchmark_a.py`. Build the excluded Preview-only world with `tools/build_simulated_player_diagnostic.py`; its GameTest pack and experiment must never appear in `dist/marketplace-candidate`.
