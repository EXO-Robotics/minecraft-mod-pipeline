# Benchmark A: Original Marketplace showcase

Status: `EXECUTABLE_STATIC_BENCHMARK` and runtime/platform `UNVERIFIED`.

This benchmark contains a legally original source fixture that executes through the compiler's scanner, planner, Bedrock generator, and static validator. It qualifies static coverage and omission reporting for the Benchmark A feature matrix. It does not claim a player-ready Add-On, runtime behavior, Marketplace clearance, or console verification.

Required features are defined in `project.yaml` and `expected-behavior.yaml`. A feature passes only when its named static, real-action, persistence, multiplayer, migration, controller, performance, and platform obligations have artifact-bound evidence.

The showcase must include one data-driven mechanic, one stable-script mechanic, one approved redesign, and one deliberately unsupported mechanic so reporting is tested across success and rejection paths.

Executable entrypoint: `fixture/`. Machine-readable quality, decision, rights, multiplayer, migration, and test contracts sit alongside it. Run:

```sh
PYTHONPATH=src python3 -m unittest tests.test_showcase_benchmark -v
```
