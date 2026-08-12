# Packet 002 Ashen Highlands — Engineering Authority Intake

**Status:** `PACKET_002_AUTHORITY_RATIFIED_IMPLEMENTATION_AUTHORIZED`
**Base:** `9acf1b0f62ade90b59ba65e0a9e0618852ff3159`
**Authority digest:** `a648049441766365213d8b0fe9015027f97d78f92daf55d055e6d80f968e2e8f`
**Scope:** Authority intake only. This does not implement BP/RP content or prove runtime behavior.

## Locked boundaries

- All 50 Packet 002 warehouse identities normalize to `aionbound:<warehouse_id>`.
- Packet 002 art is visual-production evidence only.
- Exact refined Ashen identity, loot/reward, and Kiln Sky envelopes are ratified and hash-bound.
- Kiln Sky damage values, attack-effect radii, and a new arena-radius number remain outside the ratified proposal.
- `W1-CREATIVE-005` remains `DEFERRED_BY_USER`; no sidegrade representation is selected.

## Exact roster and dependency summary

| Category | Warehouse ID | Acquisition / placement | Loot / harvest identity | Progression / equipment dependency |
|---|---|---|---|---|
| creatures | `ash_mite` | vents; caves | Ash Dust; Mite Mandible; ember_resin; Swarm Queen Scale | heatstone locator hint; hazard economy; forge flux; ore_chisel; heat binding; ashen_boots; ore_chisel; ashen_boots |
| creatures | `ember_crow` | sky; towers | Char Feather; Cinder Beak; Scorched Message Tube | ash_repeater path; cooled-kill discovery hint; ash_repeater fletching; small tool tips; Codex traveler notes; ash_repeater |
| creatures | `magma_lizard` | hot rock | Heat Scale; volcanic_glass_shard; Warm Blood Vial | safe-path environmental hint; ranged and tool path; ashen_legs padding; edges and panes; heat-resist precursor; ashen_legs; ash_repeater |
| creatures | `furnace_beetle` | forge-language areas | furnace_chitin; Smolder Gland; Beetle Core Fragment | ashen armor set; ember accessory path; ashen_chest plates; ember_totem fuel; basalt_hammer face inlay; ashen_chest; ember_totem; basalt_hammer; ore_chisel |
| creatures | `char_wolf` | night ash | Char Pelt; Ember Fang; Pack Cinder Mark | AH hostile ecology; tower story link; ashen lining; dagger or axe teeth; Codex pack record; ashen_helmet; ashen_chest; ashen_legs; ashen_boots |
| creatures | `cinder_lynx` | ridges | Cinder Pelt; Lynx Claw; heatstone; Lynx Eye Gem | ash_repeater path; elite heatstone source; silent boot pads; ash_repeater mechanism; heatstone path; talisman curiosity; ashen_boots; ash_repeater |
| creatures | `ash_ram` | plateaus | basalt_core; Ash Wool; Ram Horn Curve | basalt force path; basalt_hammer haft ring; armor padding; trophy mount or helmet crest; basalt_hammer |
| creatures | `soot_stag` | high plateaus | Soot Antler; Char Hide; fire_bloom_seed; Stag Heart Cinder | ember_great_axe path; fire_bloom path; staff or hammer ornament; armor; planting; ember_great_axe catalyst; ember_great_axe |
| creatures | `basalt_tortoise` | basalt fields | basalt_core; Shell Plate; Slow Stone | force path; heavy weapon origin; heavy weapons and tools; ashen chest or shield-analogue plate; Codex geology; basalt_hammer; basalt_pick; ashen_chest |
| creatures | `ash_drake` | arena or nest sky; ember_forge encounter link | Drake Scale; Ember Sinew; volcanic_glass_shard; ash_drake_horn; heatstone; ember_resin; ember_forge_core | Chapter 2 seal; CM maps unlock harder; Pilgrim assembly; ashen set finish; ember_great_axe binding; bulk glass; chapter seal; forge materials; ashen_helmet; ashen_chest; ashen_legs; ashen_boots; ember_great_axe; ash_drake_horn |
| resources | `smolder_bark` | ash logs or harvest | none specified | AH wood language; char_planks; heat-safe handles; basalt_hammer; basalt_pick; ash_repeater |
| resources | `charbone` | creatures or ash fields | none specified | grim craft; tool spines; ore_chisel; grim inlays; ember_hammer; ore_chisel |
| resources | `sulfur_cluster` | crust nodes | none specified | hazard economy; flux; heat crafts |
| resources | `volcanic_glass_shard` | cooled flows or magma_lizard | none specified | ranged and tool path; edges; tips; ash_repeater; basalt_hammer; basalt_pick; ash_repeater |
| resources | `ember_resin` | beetles or nodes | none specified | ember path; Ember Heart; ember_great_axe; ember_totem; regional repair binder; ember_great_axe; ember_hammer; ember_totem; ashen_helmet; ashen_chest; ashen_legs; ashen_boots |
| resources | `heatstone` | vents or elites | none specified | tool path; Heat Core; basalt_pick; ember_hammer; basalt_pick; ember_hammer |
| resources | `furnace_chitin` | furnace_beetle | none specified | set path; Chitin Plate; ashen armor; ore_chisel tip; ashen_helmet; ashen_chest; ashen_legs; ashen_boots; ore_chisel |
| resources | `basalt_core` | basalt_tortoise, deep stone, or basalt_arch cache | none specified | force path and Pilgrim assembly; Heavy Head; basalt_hammer; basalt_pick; Trophy Edge catalyst bundle; basalt_hammer; basalt_pick; ashen_helmet; ashen_chest; ashen_legs; ashen_boots |
| resources | `ash_crystal` | rare nodes or ash_watchtower | none specified | Crystal Marsh bridge hybrid; Twin Mineral Lens with flood_crystal |
| resources | `fire_bloom_seed` | fire_bloom or soot_stag | none specified | heat salve path; planting; consumable; heat salve |
| blocks | `ash_log` | craft or natural terrain as Creative specifies | none specified | dead heat wood; char forest; char_planks |
| blocks | `char_planks` | craft or natural terrain as Creative specifies | none specified | worked ash wood; worked ash; builds; handles; furniture; ash_repeater stock; basalt_hammer; basalt_pick; ash_repeater |
| blocks | `ash_soil` | craft or natural terrain as Creative specifies | none specified | ground cover; ash fields; terrain |
| blocks | `cinder_gravel` | craft or natural terrain as Creative specifies | none specified | paths and hazards; cinder waste; terrain |
| blocks | `smolder_stone` | craft or natural terrain as Creative specifies | none specified | stone body; hot stone; builds |
| blocks | `basalt_brick` | craft or natural terrain as Creative specifies | none specified | structures; civilization; kiln pads; forge pads; bridge repair |
| blocks | `basalt_pillar` | craft or natural terrain as Creative specifies | none specified | landmarks; vertical basalt; massing |
| blocks | `heat_bark` | craft or natural terrain as Creative specifies | none specified | accent; heat bark; detail |
| blocks | `ember_moss` | craft or natural terrain as Creative specifies | none specified | hazard or accent flora block; living heat; detail |
| blocks | `volcanic_glass_block` | craft or natural terrain as Creative specifies | none specified | luxury and windows; cooled fire; glass builds |
| plants | `cinder_grass` | fields | cinder_grass | fiber and tinder; early AH craft |
| plants | `ash_fern` | ash understory | ash_fern | bandage under ash; soft materials |
| plants | `smoke_reed` | near vents | smoke_reed | arrow or repeater shafts; ash_repeater; ash_repeater |
| plants | `char_shrub` | scrub | char_shrub | fuel; camp craft |
| plants | `soot_mushroom` | shade ash | soot_mushroom | risky food; consumable |
| plants | `magma_moss` | hot rock | magma_moss | heat dye or resist salve; heat resist path |
| plants | `glow_root` | caves | glow_root | cave light; cave navigation |
| plants | `basalt_flower` | rare stone | basalt_flower | rare catalyst; rare craft |
| plants | `ember_vine` | cliffs and heat | ember_vine | heat rope; binding |
| plants | `fire_bloom` | flower patches | fire_bloom | consumable and seed; fire_bloom_seed |
| structures | `fire_totem` | uncommon clusters | ember_resin; sulfur_cluster; First Fire prayer strip | ember_totem path; ambient AH; ember_totem |
| structures | `burned_camp` | uncommon edges | charred tools; Char Pelt; CM teaser map; ashen_boots pattern scraps | AH onboarding; CM rumor; ashen_boots |
| structures | `char_wagon` | uncommon routes | trade slag; sulfur_cluster; volcanic_glass_shard; ash_repeater stock wood | mid-AH economy; CM map reward identity; ash_repeater |
| structures | `broken_bridge` | ravine-gated | basalt_brick; char_planks; volcanic_glass_shard; furnace_chitin | traversal or gear check |
| structures | `basalt_arch` | rare landmark | basalt_core chance | route spoiler toward nest or forge |
| structures | `ash_watchtower` | rare ridges | survey notes; trail_compass calibration; ash_crystal | long-sight Codex stamp; drake watch; trail_compass |
| structures | `ancient_kiln` | rare | slag; heatstone; ember_forge_core rare; unfinished basalt tool heads | pre-boss forge language; ember_forge_core; basalt_hammer; basalt_pick |
| structures | `ember_forge` | very rare goal; design says one per highlands realm | slag; heatstone; ember_forge_core; unfinished basalt tool heads | primary AH structure goal; Ash Drake co-requisite; ember_forge_core; basalt_hammer; basalt_pick; ember_hammer; ore_chisel |
| structures | `lava_shrine` | rare vents | ritual curios; ember_totem component | accessory and heat-ward story; ember_totem |
| structures | `ash_cave` | uncommon faces | heatstone veins; ash_mite nests; basalt_core rare | mid-late AH; Drake juvenile tease |

## Safe now

- Normalize all 50 source identities from aionforge_ah to aionbound without changing visual identity.
- Copy hash-bound source/export bytes into the canonical shipping target families.
- Author schema and reference-closure scaffolding for the 50 ratified warehouse IDs.
- Bind Creative-approved acquisition sources, roles, Codex relationships, progression relationships, and equipment dependency edges without inventing values or identities.
- Implement Kiln Sky exactly inside the ratified W1-003-KILN-SKY behavior, ownership, persistence, reset, and terminal envelope.
- Implement Ashen loot, recipes, reward guards, and recovery exactly inside W1-001-AH and W1-004-AH.
- Use Packet 006 equipment IDs as dependency targets without choosing sidegrade representation.

## Withheld

- Any identity or numeric value outside the exact refined Ashen proposals.
- Any gameplay item for curiosity prose unless separately promoted.
- Kiln Sky damage values, attack-effect radii, or arena-radius numbers not created by the refined proposal.
- Any claim that ash_drake naturally spawns; Creative binds it to an arena or nest-sky apex path.
- Any sidegrade identity or representation covered by deferred W1-CREATIVE-005.
- Checkpoint, candidate, BDS, client, console, or gameplay proof from this intake map.

## Authority notes

- Ratified derived components: `heat_core`, `heavy_head`, `chitin_plate`, `ember_heart`.
- Ratified alias: mite-resin language resolves to `aionbound:ember_resin`.
- Ashen non-warehouse terms follow the exact W1-001-AH alias, narrative, context-only, and `drake_scale` dispositions.
- Curiosity prose remains narrative/Codex-only unless Creative separately promotes it.
- Canonical file targets are planning destinations. Their presence or validation is not claimed by this document.

## Source bindings

| Source | SHA-256 | Role |
|---|---|---|
| `program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-002-ashen-highlands/MANIFEST_FULL.json` | `6cb3bd25a1ef473e60e5ed0ebf78288bcc4d53db1ff4ec74db4d22ddb036c738` | exact Packet 002 visual roster and visual-only claim boundary |
| `program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-002-ashen-highlands/SPRINT_002_COMPLETE.md` | `cd62a92f44313bc0b7cea5c2dac08f2a96e04ecf59f8264977eb584e146d264a` | 50/50 category receipt and canonical source layout |
| `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json` | `aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5` | machine-readable Packet 002 inventory and completion contract |
| `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md` | `3116c217e06afe1fd0cd56ee742c537f948a4c91193ec831fd1b3ec362837bfc` | human implementation authority and per-asset relationships |
| `program/crazycraft-pack-production-v1/studio-prep/creative/01_progression/PLAYER_JOURNEY.md` | `42ba75d9518977c71397826aa9f4daa3864df942019c809b04830fef654a1fa7` | chapter order and soft-gate progression |
| `program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_ASHEN.md` | `f5b2ff909a6e7b7669da561cc2659439819227f99d15d221dbea0147750d3727` | loot identities and purposes, with values bounded by ratified W1-004-AH |
| `program/crazycraft-pack-production-v1/studio-prep/creative/03_crafting/CRAFTING_TREE.md` | `1f3482ba3dd9f916e08aa544153cc841871a729a2e82d9e75601715f4b5ee807` | material-to-component-to-equipment graph |
| `program/crazycraft-pack-production-v1/studio-prep/creative/04_equipment/EQUIPMENT_PROGRESSION.md` | `7ecf57e6af099ae3cda8a7432228fb5ee996f20b02b76888a82c0c1a3e3c891d` | equipment roles and sidegrade philosophy |
| `program/crazycraft-pack-production-v1/studio-prep/creative/05_structures/STRUCTURES_DESIGN.md` | `9e62ae9ba6c1da33b64ff0bfa4ac4799b083c6de995585424864d5cf2b0cb076` | structure purpose, visit, loot identity, story, and progression |
| `program/crazycraft-pack-production-v1/studio-prep/creative/06_world_gen/WORLD_GENERATION.md` | `bc18a1e1f73d6045ab7e583afe910ca13d4776d439c8f3dfb45dae5784372f4b` | ecology, placement, and rarity intent |
| `program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md` | `5ef85e1e0b29973a617f7dca4a8b119443c01644ba33f0e11166ef8d417d5a6f` | Kiln Sky identity, phase kit, attacks, and reward identities |
| `program/crazycraft-pack-production-v1/studio-prep/creative/08_codex/CODEX_ENTRIES_CREATURES.md` | `fd07694eee0c8d478b44363e822e0116f4ca09c92775661350ed8468342b01bf` | ten creature discovery/crafting/hint entries |
| `engineering/authority/support-proposals/ashen/W1-001-AH.json` | `dd26a683f7f3e5301b66d7f2861454b5bf6b79818d12e0e8e1b22b6f07217774` | ratified refined Ashen identity dispositions |
| `engineering/authority/support-proposals/ashen/W1-003-KILN-SKY.json` | `1b2d5f77185a1461040d7559d0d8ecdaf803d7727e419ceac32636865be85d7c` | ratified refined Kiln Sky encounter envelope |
| `engineering/authority/support-proposals/ashen/W1-004-AH.json` | `93736ff800b1c90c8a6547d84336a6650f8ae32750f262de8e460385a7a26889` | ratified refined Ashen loot and reward envelope |
| `engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json` | `cf7e1cd8b81b4a8088d136e1f9f2cb4ee3e245cfa71259f2a957d6e4f55ccff9` | ratified and deferred engineering decision state |
