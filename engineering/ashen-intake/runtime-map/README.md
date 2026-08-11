# Packet 002 runtime map

Source-only, ratified ownership artifacts for the Ashen Highlands vertical implementation.

- `ASHEN_RUNTIME_IMPLEMENTATION_MAP.json` is the machine authority.
- `ASHEN_RUNTIME_IMPLEMENTATION_MAP.md` is the human handoff.
- `build_ashen_runtime_map.py` regenerates the JSON from the exact base commit.
- `test_ashen_runtime_map.py` validates IDs, ratified proposal snapshots, dispositions, ownership, asset/proof gaps, budgets, hashes, and determinism.

Run:

```sh
python3 engineering/ashen-intake/runtime-map/build_ashen_runtime_map.py
python3 -m unittest engineering/ashen-intake/runtime-map/test_ashen_runtime_map.py -v
```

No BP/RP edits, build, BDS, client, or console evidence belongs to this lane. `W1-CREATIVE-005` and Ashen regrowth remain deferred; no Whisperwood tuning transfers.
