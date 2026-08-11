# Crystal Marsh creature runtime

This lane binds all ten Packet 003 creature identities to their exact existing native pass-2 geometry and animation exports and native-project texture bytes. It authors dedicated behavior entities, client entities, animation controllers, render controllers, stable vanilla placeholder sound mappings, and nine natural spawn rules.

The ecology is specific to Crystal Marsh: surface roles are restricted to Overworld swamp/river proxies, Reed Serpent and Silt Crocodile use underwater placement and swim navigation, and groups, weights, distances, and per-type density remain console-bounded. No Whisperwood or Ashen biome tuning is copied.

Marsh Wight is an arena-only base shell. It is not naturally spawnable and has no spawn-rule file, loot component, chapter-seal drop, Pearl Depths state, persistence, completion, entitlement, or terminal-reward semantics in this lane.

At exact base commit `6a10cd8a82635299ae62ab8f6b9095c9b793c7a3`, the ratified Crystal economy tables were not present. To avoid dangling references, this lane omits every `minecraft:loot` component and records the exact expected `behavior_pack/loot_tables/entities/crystal/<asset>.json` integration paths in its report. The economy owner must bind those components only after the tables coexist in the integration line.

Run targeted checks:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 engineering/crystal-marsh-intake/entity-runtime/build_crystal_entity_runtime.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest engineering/crystal-marsh-intake/entity-runtime/test_crystal_entity_runtime.py -v
```

These checks establish deterministic static files, exact native-byte binding, PNG decode, JSON parsing, and local cross-reference closure only. They do not establish Bedrock runtime motion, client rendering, BDS loading, multiplayer behavior, console performance, PS4, Marketplace, or release readiness.
