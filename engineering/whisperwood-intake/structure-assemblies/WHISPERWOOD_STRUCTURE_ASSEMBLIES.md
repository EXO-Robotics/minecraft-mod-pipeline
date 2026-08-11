# Whisperwood Structure Assemblies

Status: **STATIC_AUTHORING_PASS_ONLY**

Eight deterministic little-endian Bedrock structure templates are authored with distinct block-built silhouettes. Anchors are inert and empty; loot, rewards, interaction behavior, BDS load, and exact terrain-affinity remain outside this receipt.

Authority is hash-bound in `WHISPERWOOD_STRUCTURE_ASSEMBLIES.json`.

| ID | Size | Occupied | Rarity / chance | Terrain role |
|---|---:|---:|---|---|
| `hunter_camp` | `13x7x11` | 136 | `uncommon` / `1:384` | local forest region cluster |
| `broken_wagon` | `11x5x7` | 52 | `uncommon` / `1:512` | forest road breadcrumb |
| `root_bridge` | `17x7x7` | 91 | `uncommon_ravine` / `1:768` | ravine traversal landmark |
| `owl_shrine` | `11x10x11` | 306 | `rare` / `1:1536` | high-ground forest clearing |
| `forest_waystone` | `9x10x9` | 37 | `rare_expanse` / `1:2048` | major forest expanse |
| `hollow_cave_entrance` | `13x8x11` | 393 | `uncommon_face` / `1:512` | cliff or giant-root face |
| `ancient_totem` | `9x13x9` | 145 | `rare_deep` / `1:2048` | deep Whisperwood core |
| `fallen_giant_tree` | `21x8x11` | 223 | `very_rare_wonder` / `1:4096` | rare forest wonder event |

## Boundaries

- The feature rules use stable `minecraft:structure_template_feature` plus `overworld` + `forest` surface filters.
- Roads, ravines, high ground, cliff faces, deep core, and expanse spacing cannot be proven by these rules alone; the manifest records them as later terrain-integration obligations.
- `lantern_post` and `moss_cairn` are not placed or substituted.
- Empty barrels/lodestones/lecterns are reserved anchor blocks only. No loot identities or contents are authored.
- Deterministic regeneration, NBT decoding, palette/index closure, bounds, IDs/filenames, and anchor coordinates are covered by the lane tests.
