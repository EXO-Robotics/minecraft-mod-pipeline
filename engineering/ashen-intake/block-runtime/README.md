# Ashen full-cube block runtime slice

Status: static BP/RP source complete for the ten Packet 002 block warehouse
IDs. Runtime, world-generation, and client presentation qualification were not
run in this focused lane.

The exact base is integration commit
`e9eeb3dd9bfbd8b50fdd29babd09247552bfbe7b`, tree
`20fa2c37e1ed3e6efcd5a74edbbbb54aafcc86c4`. The packet manifest and every
brief, editable model, exported geometry, exported animation, and texture input
are hash-bound in `ASHEN_BLOCK_RUNTIME_AUTHORITY.json`.

## Runtime form

- Runtime namespace: `aionbound`.
- Geometry: `minecraft:geometry.full_block` for all ten IDs.
- Textures: byte-identical copies of each Packet 002 32 x 32 RGBA PNG under
  `textures/aionbound/ashen/blocks/`.
- Material pipeline: one opaque material instance on every face.
- Registries: behavior blocks, `terrain_texture.json`, `blocks.json`, and
  `en_US.lang` are closed by targeted tests.
- Blockbench: `NOT_APPLICABLE`. These approved shipping forms are ordinary
  full cubes and need no custom geometry, UV editing, locators, rig, or
  animation. The packet's generic custom geometry and animations are retained
  as hash-bound intake evidence but are not promoted or represented as native
  shipping proof.

The source Volcanic Glass PNG is fully opaque. Its runtime therefore remains
opaque; this lane does not invent alpha values. The packet also supplies no
separately authorized directional face textures for Ash Log or Basalt Pillar,
so axis/pillar appearance variants are withheld instead of deriving new crops.

Mining times, sound families, and creative-menu groups are conservative
engineering defaults. They do not ratify loot, recipes, acquisition,
world-generation, or Creative identity beyond the packet.

## Bounded validation

```sh
python3 engineering/ashen-intake/block-runtime/author_ashen_blocks.py
python3 engineering/ashen-intake/block-runtime/test_ashen_blocks.py -v
python3 tools/validate_wave1.py
```

Static parse, reference closure, byte equality, and PNG decoding do not prove
Bedrock client rendering, readability, Stable BDS, packaging, physical PS4, or
Marketplace acceptance.
