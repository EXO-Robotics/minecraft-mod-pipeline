# Reproduction commands

Run from the repository root. These commands reproduce only the current baseline; they do not establish Marketplace or console qualification.

```sh
git branch --show-current
git rev-parse HEAD
git status --short
git remote -v
git tag --list

PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests

PYTHONPATH=src python3 -m mccompiler scan \
  --input tests/fixtures/representative_mod \
  --output out/representative-ir.json

PYTHONPATH=src python3 -m mccompiler compile \
  --input tests/fixtures/representative_mod \
  --output out/representative

PYTHONPATH=src python3 -m mccompiler validate \
  --path out/representative
```

If `javap` is not on `PATH`, set `MCCOMPILER_JAVAP` to a local OpenJDK executable. To check deterministic archives, compile into two fresh directories and compare SHA-256 values of the generated `.mcaddon` files.

Runtime validation requires separately generated, artifact-bound evidence. Do not create or copy a passing evidence document by hand. Creator Tools is pinned by `src/mccompiler/creator-tools.lock.json`; use `invoke_creator_tools` against a uniquely named archive because the tool may reuse filename-keyed cache data. Physical-console commands remain absent because no hardware automation is established.

For the isolated Benchmark B Preview action diagnostic, first build the production project, then run `tools/build_benchmark_b_simulated_player.py` separately against both `dist/test-world/legacy-seed-world.mcworld` and `dist/test-world/generated-test-world.mcworld`. Invoke `start_test_runtime` with the pinned image digest, exact `bds_version` `1.26.50.20`, `preview_channel=true`, two cycles, and the checked-in `simulated-player-console-probes.json` and `simulated-player-log-probes.json`. The generated experimental worlds must remain outside `dist/marketplace-candidate`; never substitute their result for physical-player, stable-runtime, Marketplace, Realm, or console evidence.

For Benchmark A, run `tools/build_benchmark_a.py --output <new-project>` to apply the ten checked-in evidence-linked runtime overrides and create deterministic stable artifacts. Build the separate Preview world with `tools/build_simulated_player_diagnostic.py`, the generated stable world, and `diagnostic/simulated-actions`. Run it against exact Preview `1.26.50.20` with the checked-in action probes. The diagnostic observes item use/use-on-block and machine interaction in its GameTest pack because the GameTest-created player's actor is not exposed to the separate stable behavior pack; the stable pack rejects those incomplete player-owned contexts. Entity-spawn, scheduled boss phase, projectile impact, hostile-entity damage, and melee checks remain narrow adapter-integration evidence. Do not put the diagnostic pack, GameTest experiment, logs, or reports in the consumer archive.
