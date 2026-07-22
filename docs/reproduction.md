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

Runtime validation requires separately generated, artifact-bound evidence. Do not create or copy a passing evidence document by hand. Creator Tools and physical-console commands are intentionally absent because no pinned installation or hardware automation is currently established.

