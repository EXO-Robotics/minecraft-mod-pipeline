# Crystal Marsh Structure Assembly Lane

This lane deterministically authors the ten Packet 003 landmark IDs as distinct little-endian Bedrock `.mcstructure` block assemblies plus stable structure-template features and feature rules.

Run:

```sh
python3 engineering/crystal-marsh-intake/structure-assemblies/author_crystal_marsh_structures.py
python3 engineering/crystal-marsh-intake/structure-assemblies/validate_crystal_marsh_structures.py
python3 engineering/crystal-marsh-intake/structure-assemblies/validate_crystal_marsh_structures.py --check
```

All anchors are inert ordinary blocks with no block-entity metadata. Loot, reward, boss, seal, recovery, entity, and script bindings remain excluded until their separate Crystal authorities are ratified.

The generated report proves only deterministic static source/byte structure. It does not prove Bedrock client or BDS load, wetland terrain affinity, discovery pacing, loot, encounter behavior, or candidate readiness.
