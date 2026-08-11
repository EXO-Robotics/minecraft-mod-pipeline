# Whisperwood Codex mapping lane

Run:

```sh
python3 engineering/whisperwood-intake/codex/build_whisperwood_codex_map.py
python3 -m unittest engineering/whisperwood-intake/codex/test_whisperwood_codex_map.py -v
```

The generator and test are intentionally local to this evidence lane. They do not mutate behavior-pack or resource-pack content.
