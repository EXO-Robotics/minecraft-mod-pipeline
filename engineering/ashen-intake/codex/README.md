# Ashen Codex intake

Run:

```sh
python3 engineering/ashen-intake/codex/build_ashen_codex_map.py
python3 -m unittest engineering/ashen-intake/codex/test_ashen_codex_map.py -v
```

The builder emits a deterministic JSON authority map and Markdown review twin. The lane is intentionally source-only: it does not edit Script API code, BP/RP content, Creative authority, build output, or BDS evidence.
