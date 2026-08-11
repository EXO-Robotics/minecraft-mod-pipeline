# Wave 1 Engineering Decision Ledger

Status: **RATIFIED_FOR_NONBLOCKED_ENGINEERING_WITH_EXPLICIT_SUPPORT_TICKETS**

This ledger resolves or support-tickets the implementation ambiguities found between the five immutable warehouse packets, Creative Layer v1, and the G7 engineering substrate. It does not redesign Aionbound and does not supersede packet art identities or Creative gameplay roles.

## Authority order

1. Immutable packet asset IDs and visual identity remain Creative authority.
2. Creative Markdown remains authority for fantasy, roles, relationships, and named content.
3. This ledger is authority only for Phase 0 engineering classifications, runtime namespace normalization, bounded tuning authority, deferrals, and support-ticket boundaries.
4. Existing G7 code is reusable evidence, not authority over newer Creative decisions.

The existing Creative JSON is a lossy index, not a complete executable twin. The JSON sibling of this ledger is the machine-readable authority for the decisions below.

## Runtime identity decision

- Shipping namespace: `aionbound`.
- Every approved warehouse ID remains unchanged as the path portion: `<warehouse_id>` → `aionbound:<warehouse_id>`.
- Packet namespace intents such as `aionforge_ww` are provenance labels mapped to the product-standard runtime namespace; they do not authorize alternate cast IDs.
- No G7 identifier is renamed in place. Successor mappings are explicit and migration-aware.
- Equipment sidegrades may not introduce sibling IDs until support ticket `W1-CREATIVE-005` is resolved. The initial engineering path preserves the approved base item IDs and separates behavior configuration from identity.
- Accessory concurrent maximum is fixed at **2**, inside the Creative-approved `2–3` range, to preserve console and UI clarity.

## Non-warehouse term classifications

### Existing asset aliases

These terms do not create new inventory IDs:

| Creative term | Canonical warehouse identity |
|---|---|
| Soft Moss Scrap | `moss_resin` |
| Star Seeds | `star_grass` |
| Briar Vine Length | `briar_vine` |
| mite_resin language | `ember_resin` |
| Glass Algae Film | `glass_algae` |
| Flood Crystal Shard | `flood_crystal` |
| Wind Silk strand / bundle | `wind_silk` with quantity context |
| aether_stone / cliff_crystal chips | base warehouse ID with quantity context |
| sky_feather bulk / ×n | `sky_feather` with quantity context |
| resource dust/chip/bundle wording | base warehouse ID only when the source row names that ID unambiguously |

No other prose term may be treated as an alias by similarity alone. Ambiguous terms such as Char Hide / Char Pelt / Cinder Pelt remain ticketed.

### Approved derived components

These names already exist in Creative crafting authority. Engineering may create the listed canonical runtime IDs as derived inventory components; it may not change their role or invent additional ingredients.

| Creative name | Runtime ID |
|---|---|
| Moss Bind Glue | `aionbound:moss_bind_glue` |
| Amber Core | `aionbound:amber_core` |
| Thorn Cord | `aionbound:thorn_cord` |
| Cleaver Blank | `aionbound:cleaver_blank` |
| Living Root Focus | `aionbound:living_root_focus` |
| Heat Core | `aionbound:heat_core` |
| Heavy Head | `aionbound:heavy_head` |
| Chitin Plate | `aionbound:chitin_plate` |
| Ember Heart | `aionbound:ember_heart` |
| Crystal Pole | `aionbound:crystal_pole` |
| Living Crystal Core | `aionbound:living_crystal_core` |
| Wet Plate | `aionbound:wet_plate` |
| Twin Mineral Lens | `aionbound:twin_mineral_lens` |
| Climbing Rope | `aionbound:climbing_rope` |
| Climbing Hook Head | `aionbound:climbing_hook_head` |
| Glider Panel | `aionbound:glider_panel` |
| Glider Frame | `aionbound:glider_frame` |
| Soft Landing Pad | `aionbound:soft_landing_pad` |
| Lift Tonic | `aionbound:lift_tonic` |
| Aether Bind | `aionbound:aether_bind` |
| Edge Blank / Inert Edge | `aionbound:trophy_edge_blank` |
| Trophy Edge | preserve/refine G7 item `aionbound:trophy_edge`; retain `trophy_edge_assembled` as its geometry identity |
| Memory of Four Lands | `aionbound:memory_of_four_lands` — finale support dependency |
| Pathfinder Pair | `aionbound:pathfinder_pair` — utility narrative component |

Icons and final inventory visibility for the last two finale/narrative components remain bound to `W1-CREATIVE-001` and `W1-CREATIVE-002`.

### New required item candidates — support-ticketed

The following named loot identities occur in approved loot prose but are absent from the 250-ID warehouse. They are not aliases and may not be silently collapsed. Their exact ID, inventory visibility, icon requirement, and craft home are blocked on `W1-CREATIVE-001`:

- Whisperwood: Boar Tusk Shard / Boar Tusk, Root Plate, Thick Hide, Briar Crown, Rot Fang, Tainted Pelt, Marrow Scrap, Thorn Barb, Stalker Claw, Hollow Venom Sac, Chitin Shard, Wraith Mask Fragment, Mosskip Crown Fragment, Hardened Moss Plate, Glow Soft Pellet, Lantern-adjacent hide scrap.
- Ashen: Ash Dust, Ash Wool, Beetle Core Fragment, Char Feather, Char Hide, Char Pelt, Cinder Beak, Cinder Pelt, Drake Scale, Ember Fang, Ember Sinew, Heat Scale, Lynx Claw, Mite Mandible, Pack Cinder Mark, Ram Horn Curve, Shell Plate, Smolder Gland, Soot Antler, Stag Heart Cinder, Swarm Queen Scale, Warm Blood Vial.
- Crystal Marsh: Algae Scrap, Bog Tendril, Crab Pearl Grain, Croc Eye Pearl, Croc Hide, Glass Feather, Heron Nest Token, Iridescent Dust, Long Beak Shard, Marsh Resin Blob, Mire Shell Plate, Newt Tail Crystal, Prism Mucus, Prism Wing, Serpent Scale, Shed Skin Ribbon, Silt Fang, Tiny Prism Chip, Venom Crystal, Watcher Lens, Wight Shroud Cloth.
- Skyreach: Cliff Hoof Keratin, Dense Muscle Strip, Drake Membrane, Fox Whisker Cord, Gale Membrane, Glide Scale, Hawk Talon, Navigation Oil, Nest Crown Plume, Nest Twig, Ram Horn Spiral, Roc Primary Feather, Ropewing Membrane, Ruin Talon, Sky Ruin Key Fragment, Soft Sky Fur, Stone Beak, Storm Salt, Vulture Crop Stone, Wing Bone Stay.
- Finale/boss: Concord Spark, Drowned Choir Tablet, Hunter's Final Page, Perfect Prism Pearl, Sky Ruin Master Key, Surviving Smith's Notes, Wight Shroud, and any mastery sigil not already one of the packet trophies.

Curiosity terms are narrative/Codex discoveries by default and do not become inventory items unless `W1-CREATIVE-001` explicitly promotes them. Generic crates, bundles, pattern scraps, and quantity words are containers/roll context, not new identities.

## Twinbond dependency decision

Twinbond is `DEFERRED_WITH_BLOCKING_SUPPORT_TICKET` under `W1-CREATIVE-002`.

Engineering may implement the pilgrimage handoff, inert Trophy Edge, finale entry state, and `twinbond_relic` persistence hooks. It may not implement the encounter, dual aspects, arena art, ignition reward, or final completion semantics until the ticket binds:

- exact aspect entity IDs and existing mesh/texture/animation inputs, or an explicit no-new-mesh composition using named existing entities;
- arena and approach asset IDs/locations;
- Concord Spark, Memory of Four Lands, and mastery-sigil dispositions;
- whether Twinbond completion is mandatory for Wave 1 machine exit (current ledger assumes yes).

## Boss behavior envelope decision

Creative phase names, attack fantasies, placement, and reward identities are implementable now. Numeric and ownership semantics are `DEFERRED_WITH_BLOCKING_SUPPORT_TICKET` under `W1-CREATIVE-003`.

The ticket must bind for each apex:

- phase thresholds and transition predicates;
- telegraph, attack, recovery, and cooldown ranges;
- leash, timeout, wipe, reset, re-entry, and add caps;
- solo/multiplayer ownership, late join, disconnect, and scaling;
- persisted completion domain;
- per-player versus world reward authority;
- idempotent terminal grant and repeat-clear semantics.

No boss may ship with Engineering-invented values outside that ticket.

## Loot and rarity envelope decision

Creative loot identities and qualitative roles remain binding. Engineering may wire table structure and reward guards, but final probabilities and quantities are `DEFERRED_WITH_BLOCKING_SUPPORT_TICKET` under `W1-CREATIVE-004`.

The ticket must provide approved min/max chance and quantity ranges for C/U/R/E/T/Q roles, chest roll counts, guaranteed boss semantics, arena-form reward guards, and the disposition of `briar_elk_trophy` as an alternate/soft seal. Regular `thorn_stalker` ecology may not award the chapter seal; the seal is guarded to the chapter-apex encounter unless Creative explicitly says otherwise.

## Native Blockbench inspection requirement

Canonical editable packet sources are the 50-file `assets/editable/` roots inside each sprint. Category-folder copies are mirrors and must hash-match or be classified before production use.

The shipping-use gate is bounded by asset class:

1. Native open/save/reopen plus native export equivalence is mandatory for every boss/hero asset, every asset with custom locators or role-specific animation, and every repaired source.
2. Before scaling a class, run representative native gates for the four chapter apexes, the multipart spider, aerial/gliding creatures, one ambient/neutral/hostile creature per ecosystem, hero weapon classes, representative armor, all chapter-seal displays, `twinbond_relic`, and one complex prop per ecosystem.
3. If a representative fails, all members produced by that template require native round-trip before shipping.
4. Ordinary full-cube blocks, flat icons/resources, cross-plane plants implemented with native JSON, and props converted to authored block-based `.mcstructure` assemblies are `NOT_APPLICABLE` for Blockbench when documented as such.
5. Static parser success, proof renders, or generated geometry do not prove native export, Bedrock client rendering, or PS4 rendering.

This gate is a shipping-use requirement, not a reason to run BDS per asset.

## Support tickets

| ID | Blocking scope | Owner | Work allowed while open |
|---|---|---|---|
| `W1-CREATIVE-001` | Complete non-warehouse glossary, canonical IDs, inventory visibility, icon/craft homes | Creative + Asset support | Existing aliases and approved derived components; no unresolved new item publication |
| `W1-CREATIVE-002` | Twinbond aspects, art, arena, finale rewards and exit dependency | Creative + Asset support | Pilgrimage handoff and inert finale hooks only |
| `W1-CREATIVE-003` | Boss numeric, reset, multiplayer, persistence, terminal reward envelopes | Creative support | Phase kits and nonnumeric behavior architecture |
| `W1-CREATIVE-004` | Loot numeric ranges, chest rolls, reward guards, alternate-seal semantics | Creative support | Structural loot wiring with no final values |
| `W1-CREATIVE-005` | Equipment sidegrade identity: same base ID behavior versus approved sibling IDs | Creative support | Base packet IDs and behavior interface only |

Broad engineering may proceed only in the explicitly allowed columns. Final Wave 1 freeze remains blocked until all five tickets are resolved and committed into a replacement ledger revision.

## Advisory review disposition

A read-only Grok red-team was attempted under the required safety profile and reached its turn cap after producing partial advice. Accepted: keep per-term source binding, distinguish ledger authority from Creative authority, make Twinbond exit dependency explicit, and separate phase-kit implementation from numeric boss tuning. Rejected: allowing provisional loot values without approved ranges, because the Engineering brief explicitly requires tuning inside approved ranges. Adjusted: native Blockbench gating is representative and risk-class based during scaling, with full native proof reserved for hero/locator/repaired assets and failed templates.
