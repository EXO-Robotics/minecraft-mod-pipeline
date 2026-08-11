# Crystal Marsh Structure Assemblies

Status: **STATIC_AUTHORING_PASS_ONLY**

Ten deterministic little-endian Bedrock structure templates are authored as distinct Crystal Marsh block-built silhouettes. Every machine-recorded anchor is inert and every structure has empty block-position data.

| ID | Size | Occupied | Rarity / chance | Terrain role |
|---|---:|---:|---|---|
| `flooded_dock` | `17x6x13` | 241 | `uncommon_shore` / `1:704` | swamp or river shore discovery proxy |
| `ancient_boat` | `19x8x9` | 114 | `rare_stranded` / `1:1216` | stranded wetland shelf proxy |
| `marsh_broken_bridge` | `21x7x7` | 93 | `channel_crossing` / `1:1472` | river and swamp channel proxy |
| `pearl_cairn` | `9x8x9` | 119 | `uncommon_islet` / `1:832` | small wetland islet proxy |
| `marsh_totem` | `11x13x9` | 92 | `uncommon_ritual` / `1:1088` | open swamp islet proxy |
| `crystal_arch` | `15x15x7` | 187 | `rare_landmark` / `1:2432` | open wetland sightline proxy |
| `crystal_obelisk` | `13x18x13` | 554 | `rare_network` / `1:3072` | isolated marsh rise proxy |
| `sunken_shrine` | `17x11x17` | 569 | `rare_flooded` / `1:3712` | low swamp basin proxy |
| `ruined_observatory` | `23x19x21` | 790 | `very_rare_height` / `1:6656` | rare elevated wetland shelf proxy |
| `deep_pool_entrance` | `19x12x19` | 1553 | `rare_dark_water` / `1:4352` | swamp waterline cave-mouth proxy |

## Boundaries

- Feature rules use stable `minecraft:structure_template_feature` with overworld, non-ocean, and swamp-or-river surface proxies.
- Wetland proxy placement does not prove shoreline fit, underwater depth, regional affinity, separation distance, or successful game load.
- Barrel, lodestone, and lectern blocks carry no block-entity data. No structure binds loot, rewards, bosses, seals, recovery, entities, or scripts.
- `W1-004-CM` is required before loot/reward binding and `W1-003` before encounter activation.
- Packet/native landmark models are visual evidence only, not assembly proof.
- No BDS, client, build, gameplay, or candidate claim is made.
