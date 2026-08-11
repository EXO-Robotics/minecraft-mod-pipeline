# Whisperwood Ecology Worldgen

Status: STATIC_SOURCE_REGISTRATION_PASS_ONLY

Nine conservative Stable feature registrations place existing Packet 001 vegetation and resource-adjacent block proxies in overworld forest contexts.

| Feature | Role | Pass | Iterations / chance | Expected attempts/chunk |
|---|---|---|---:|---:|
| ww_ecology_whisper_fern | representative understory plant | surface_pass | 4 / 1:8 | 0.5 |
| ww_ecology_lantern_bloom | representative luminous plant | surface_pass | 2 / 1:16 | 0.125 |
| ww_ecology_mooncap | representative shaded fungus | surface_pass | 2 / 1:24 | 0.083333 |
| ww_ecology_root_flower | representative root-associated flower | surface_pass | 1 / 1:32 | 0.03125 |
| ww_ecology_glow_moss_floor | moss/resin-adjacent floor node proxy | surface_pass | 3 / 1:12 | 0.25 |
| ww_ecology_hollow_lily_margin | lily/moon-sap pool-margin plant proxy | surface_pass | 2 / 1:48 | 0.041667 |
| ww_ecology_briar_vine | tree-side vine proxy | surface_pass | 3 / 1:32 | 0.09375 |
| ww_ecology_root_bark_cluster | root/bark/log surface cluster proxy | surface_pass | 2 / 1:128 | 0.015625 |
| ww_ecology_hollow_wood_cave | hollow wood/amber-adjacent cave proxy | underground_pass | 1 / 1:96 | 0.010417 |

## Boundaries

- Aggregate expected attempts before placement filters: 1.151042 per chunk; this does not raise entity or runtime caps.
- Forest, surface, and underground filters are stable registration proxies. They do not prove pool adjacency, tree adjacency, caves, root plates, or biome-wide distribution.
- Resin, amber, and moon sap items are not placed or referenced. Existing moss, hollow wood, and lily blocks provide only the approved resource-adjacent environmental signal.
- No items, drops, loot, entities, structures, scripts, custom biomes, or runtime schedulers are authored.
