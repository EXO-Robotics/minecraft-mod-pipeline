# Crystal Marsh creature runtime validation

Exact source base:

- Commit: `6a10cd8a82635299ae62ab8f6b9095c9b793c7a3`
- Tree: `689fa214ae21ab9739a8b6710fdbb5bb00ebeaeb`

Targeted checks run on 2026-08-11:

1. `PYTHONDONTWRITEBYTECODE=1 python3 engineering/crystal-marsh-intake/entity-runtime/build_crystal_entity_runtime.py`
   - PASS
   - Report SHA-256: `243c0c0087378c47a97a9d1a60c93a4d13bee5a2156577804d04a3ad6df6b30a`
2. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest engineering/crystal-marsh-intake/entity-runtime/test_crystal_entity_runtime.py -v`
   - PASS: 12 tests
3. `PYTHONDONTWRITEBYTECODE=1 python3 tools/validate_wave1.py`
   - PASS
   - Source-mechanical scope only
   - Inventory observed: 54 BP entities, 54 client entities, 38 spawn rules, 31 animation controllers, 31 render controllers, 321 animation clips, and 1,156 JSON files

Stable Bedrock component shapes were checked against current official Microsoft Learn references for `minecraft:movement.amphibious`, `minecraft:navigation.generic`, `minecraft:navigation.swim`, `minecraft:behavior.random_swim`, `minecraft:breathable`, and underwater spawn-rule placement. This documentation check does not replace exact-package schema or Stable BDS qualification.

Verified locally:

- exact native pass-2 geometry and animation bytes plus native-project texture bytes for all ten creatures;
- PNG CRC/decompression and nonzero dimensions;
- geometry, animation bone, client alias, animation-controller, and render-controller closure;
- role-specific ambient, neutral, hostile, flying, amphibious, aquatic, wader, and arena-shell source components;
- exactly nine natural spawn rules, with bounded group size, density, weight, and distance;
- Marsh Wight has no natural spawn, loot component, chapter-seal drop, Pearl Depths session state, persistence, or terminal reward semantics;
- no dangling loot-table reference was authored before the parallel ratified economy tables exist;
- ten stable vanilla placeholder entity-sound mappings and no custom audio bytes;
- deterministic report regeneration;
- broader Wave 1 source-mechanical validator PASS.

Not run or proven: package build, Bedrock schema ingestion, Stable BDS, gameplay pathfinding, client rendering or animation playback, loot delivery, Pearl Depths encounter behavior, persistence, multiplayer, performance, controller, PS4, Marketplace, or release.
