# Crystal Marsh resource-item static foundation

Status: static BP/RP source complete for the ten Packet 003 warehouse resource
IDs. The exact base is G8 commit
`466a061cbe22a01a4e561169df31e4f351edea71`, tree
`1aadcfab635991f6d0fb4647f6ed2a3bb615a7af`.

The deterministic author binds exact `aionbound` identifiers, inert Behavior
Pack item definitions, byte-identical Packet 003 icons, the item atlas, and
English localization. Packet briefs, editable models, exports, animations, and
source textures are hash-bound as intake evidence.

Blockbench is `NOT_APPLICABLE`: the shipping form is a flat inventory icon.
Packet custom geometry and animation are not promoted.

```sh
python3 engineering/crystal-marsh-intake/resource-runtime/author_crystal_resources.py
python3 engineering/crystal-marsh-intake/resource-runtime/test_crystal_resources.py -v
```

This slice does not implement or prove acquisition, loot, recipes, worldgen,
scripts, persistence, client presentation, BDS, packaging, console, or release.
