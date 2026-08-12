# Skyreach static foundations

This lane normalizes only Packet 004's ten resource icons and ten ordinary
full-cube blocks from warehouse namespace `aionforge_sr` to runtime namespace
`aionbound`. It copies approved packet PNG bytes without visual changes and
binds BP definitions, RP atlases, the block registry, and English names.

Blockbench is `NOT_APPLICABLE` to these selected shipping forms: resources are
flat inventory icons and blocks use `minecraft:geometry.full_block`. Packet
custom geometry and animations are deliberately not promoted by this lane.

Run `author_skyreach_static.py`, `test_skyreach_static.py`, then
`tools/validate_wave1.py`. This proves static source and exact-texture closure
only; it does not prove acquisition, loot, recipes, world generation, scripts,
packaging, BDS, client, console, or Marketplace behavior.
