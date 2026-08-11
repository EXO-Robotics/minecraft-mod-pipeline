# Ashen Structure Assemblies

Status: **STATIC_AUTHORING_PASS_ONLY**

Ten deterministic little-endian Bedrock structure templates are authored as distinct Ashen block-built silhouettes. Seven ordinary barrel anchors bind exact Ashen chest tables; the Ember Forge arena cache remains empty before a valid clear.

| ID | Size | Occupied | Rarity / chance | Terrain role |
|---|---:|---:|---|---|
| `fire_totem` | `9x12x9` | 69 | `uncommon_cluster` / `1:640` | open ash shelf prayer cluster |
| `burned_camp` | `13x6x11` | 147 | `uncommon_edge` / `1:896` | mountain-to-mesa edge onboarding |
| `char_wagon` | `15x6x9` | 106 | `uncommon_route` / `1:1152` | dry mesa route breadcrumb |
| `broken_bridge` | `19x8x9` | 104 | `ravine_gated` / `1:1408` | mountain cut traversal check |
| `basalt_arch` | `13x13x7` | 159 | `rare_landmark` / `1:2304` | high saddle route spoiler |
| `ash_watchtower` | `11x18x11` | 382 | `rare_ridge` / `1:2816` | exposed mountain ridge sightline |
| `ancient_kiln` | `15x11x15` | 851 | `rare_kiln` / `1:3328` | sheltered caldera bench |
| `ember_forge` | `23x14x23` | 1136 | `exceptionally_rare_goal` / `1:16384` | highlands goal proxy; exact realm uniqueness unproven |
| `lava_shrine` | `11x10x13` | 333 | `rare_vent` / `1:3584` | mesa vent and heat seam |
| `ash_cave` | `17x10x15` | 1019 | `uncommon_face` / `1:1024` | mountain or mesa face proxy |

## Boundaries

- Feature rules use stable `minecraft:structure_template_feature` with overworld, non-ocean, and mountain-or-mesa surface proxies.
- `ember_forge` uses an exceptionally rare `1:16384` proxy. Feature rules cannot enforce or prove exactly one per highlands realm; that obligation remains open in the machine manifest.
- Ordinary barrel anchors contain only exact LootTable path metadata. No structure contains reward items, boss activation, entities, or scripts.
- The Ember Forge barrel contains no LootTable NBT and remains guarded for command-free post-clear population owned by the Kiln Sky service.
- Packet/native visual models are evidence only and are not the assembly bytes.
- No BDS, client load, terrain affinity, encounter, or candidate claim is made.
