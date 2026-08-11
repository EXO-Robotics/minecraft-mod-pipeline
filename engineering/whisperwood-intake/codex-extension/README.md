# Whisperwood Codex extension lane

This lane maps the missing Part 3 Codex coverage at exact G8 commit `00840aaae36a0cfb83955ca7b416c1d2886a6261`.

It adds no shipping behavior. The JSON map binds the 10 Packet 001 structures, 21 Whisperwood-facing Packet 006 entries, Thorn Court, the Whisperwood chapter page, and the Ashen rumor page to exact Creative phrases and ratified terminal semantics. The Markdown twin is generated for review.

Run:

```sh
python3 engineering/whisperwood-intake/codex-extension/build_codex_extension_map.py --check
python3 -m unittest engineering/whisperwood-intake/codex-extension/test_codex_extension_map.py -v
```

The runtime integrator must resolve every listed conflict compositionally. In particular, a regular ecology Thorn Stalker cannot grant the chapter seal or complete boss/trophy/progression pages, and the Ashen rumor remains Codex/structure-state presentation rather than a map-scrap item.
