# Crystal Marsh Structure Economy Binding

Status: **STATIC_STRUCTURE_LOOT_BINDING_PASS**

Seven ordinary Crystal Marsh barrel anchors now carry exact ratified loot-table paths. `marsh_totem` and `sunken_shrine` remain inert because they have no approved chest identity. The `deep_pool_entrance` cache remains empty and synchronously guardable by the Pearl Depths encounter service.

No structure table contains `aionbound:marsh_wight_mask`; no structure grants seal credit or encounter completion.

| Structure | Binding | Anchor | Loot table |
|---|---|---|---|
| `flooded_dock` | `STATIC_ORDINARY_LOOT_TABLE_NBT` | `flooded_dock_cache` | `loot_tables/chests/crystal/flooded_dock.json` |
| `ancient_boat` | `STATIC_ORDINARY_LOOT_TABLE_NBT` | `ancient_boat_locker` | `loot_tables/chests/crystal/ancient_boat.json` |
| `marsh_broken_bridge` | `STATIC_ORDINARY_LOOT_TABLE_NBT` | `marsh_bridge_cache` | `loot_tables/chests/crystal/marsh_broken_bridge.json` |
| `pearl_cairn` | `STATIC_ORDINARY_LOOT_TABLE_NBT` | `pearl_cairn_cache` | `loot_tables/chests/crystal/pearl_cairn.json` |
| `marsh_totem` | `INERT_NO_APPROVED_CHEST_IDENTITY` | `-` | `-` |
| `crystal_arch` | `STATIC_ORDINARY_LOOT_TABLE_NBT` | `crystal_arch_cache` | `loot_tables/chests/crystal/crystal_arch.json` |
| `crystal_obelisk` | `STATIC_ORDINARY_LOOT_TABLE_NBT` | `crystal_obelisk_cache` | `loot_tables/chests/crystal/crystal_obelisk.json` |
| `sunken_shrine` | `INERT_NO_APPROVED_CHEST_IDENTITY` | `-` | `-` |
| `ruined_observatory` | `STATIC_ORDINARY_LOOT_TABLE_NBT` | `ruined_observatory_cache` | `loot_tables/chests/crystal/ruined_observatory.json` |
| `deep_pool_entrance` | `PROTECTED_EMPTY_SYNCHRONOUS_ENCOUNTER_CACHE` | `-` | `-` |

The machine receipt records predecessor and bound hashes plus four-cardinal rotation closure for every bound anchor. Feature and feature-rule files are not outputs of this author.

No BDS, build, client, encounter-runtime, reward, or candidate claim is made.
