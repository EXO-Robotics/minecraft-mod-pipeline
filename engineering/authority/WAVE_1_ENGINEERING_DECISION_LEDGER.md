# Wave 1 Engineering Decision Ledger

Status: **RATIFIED_WHISPERWOOD_AND_ASHEN_IMPLEMENTATION_AUTHORITY_WITH_DEFERRED_LATER_TICKETS**

This ledger resolves or support-tickets the implementation ambiguities found between the five immutable warehouse packets, Creative Layer v1, and the G7 engineering substrate. It does not redesign Aionbound and does not supersede packet art identities or Creative gameplay roles.

## Whisperwood ratification event

The primary human authority approved the following proposal tranches exactly as written:

- `W1-001-WW` — Whisperwood term dispositions and four new inventory identities only;
- `W1-003-THORN-COURT` — the complete Thorn Court behavior, reset, multiplayer, persistence, and terminal envelope;
- `W1-004-WW-CH1` — Whisperwood/Thorn Court rarity intervals, chest bands, seal guards, recovery, repeat-clear, and mastery-only trophy semantics;
- `W1-006-WW-SAPLING` — one bounded existing-palette standing-tree assembly and its growth envelope.

`W1-CREATIVE-005`, the Crystal Marsh/Skyreach portions of `W1-CREATIVE-001`, and the Crystal Marsh/Skyreach portions of `W1-CREATIVE-004` are explicitly deferred. The proposal files remain byte-preserved and are bound by SHA-256 in the JSON ledger. Engineering may implement only the approved tranches and may not broaden, rewrite, or reinterpret them.

This ratification authorizes completion of the Whisperwood vertical slice. Checkpoint 1 remains unauthorized until the slice satisfies its exit criteria, and Ashen may not begin until Checkpoint 1 establishes that the pattern is sound.

## Ashen ratification event

After the exact Whisperwood Checkpoint 1 replacement request passed its bounded Stable BDS smoke, the primary human authority approved these refined Ashen proposals exactly as written:

- `W1-001-AH` — the existing Ashen identity subset, including `aionbound:drake_scale`, without sidegrade authority;
- `W1-003-KILN-SKY` — the complete Kiln Sky behavior, scaling, reset, multiplayer, persistence, and terminal envelope;
- `W1-004-AH` — Ashen rarity intervals, chest bands, the sole critical `aionbound:ash_drake_horn` seal, ecology-form prohibition, recovery, repeat-clear, and optional mastery reward semantics.

The refined proposal bytes are preserved unchanged and SHA-256-bound in the JSON ledger. `W1-CREATIVE-005` remains deferred: Ashen may reuse approved base equipment identities but may not create or apply the deferred sidegrade identities or behaviors. This ratification authorizes the Ashen vertical under G8, preserves G7 and the passed Whisperwood lineage, and keeps Crystal Marsh gated until Ashen satisfies its vertical exit criteria. It does not authorize a new BDS checkpoint.

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

### New required item candidates — Whisperwood and Ashen partially ratified

`W1-001-WW` ratifies exactly four new Whisperwood inventory identities: `aionbound:mosskip_crown_fragment`, `aionbound:thorn_barb`, `aionbound:stalker_claw`, and `aionbound:hollow_venom_sac`. All other Whisperwood terms use the aliases, narrative-only dispositions, or removals in the preserved proposal. `W1-001-AH` separately ratifies the exact refined Ashen dispositions and only the existing proposed `aionbound:drake_scale` inventory identity; it grants no `W1-CREATIVE-005` sidegrade authority. Crystal Marsh and Skyreach identities remain deferred.

The following named loot identities occur in approved loot prose but are absent from the 250-ID warehouse. Outside the approved Whisperwood tranche they remain unratified and may not be silently collapsed:

- Whisperwood: Boar Tusk Shard / Boar Tusk, Root Plate, Thick Hide, Briar Crown, Rot Fang, Tainted Pelt, Marrow Scrap, Thorn Barb, Stalker Claw, Hollow Venom Sac, Chitin Shard, Wraith Mask Fragment, Mosskip Crown Fragment, Hardened Moss Plate, Glow Soft Pellet, Lantern-adjacent hide scrap.
- Ashen: Ash Dust, Ash Wool, Beetle Core Fragment, Char Feather, Char Hide, Char Pelt, Cinder Beak, Cinder Pelt, Drake Scale, Ember Fang, Ember Sinew, Heat Scale, Lynx Claw, Mite Mandible, Pack Cinder Mark, Ram Horn Curve, Shell Plate, Smolder Gland, Soot Antler, Stag Heart Cinder, Swarm Queen Scale, Warm Blood Vial.
- Crystal Marsh: Algae Scrap, Bog Tendril, Crab Pearl Grain, Croc Eye Pearl, Croc Hide, Glass Feather, Heron Nest Token, Iridescent Dust, Long Beak Shard, Marsh Resin Blob, Mire Shell Plate, Newt Tail Crystal, Prism Mucus, Prism Wing, Serpent Scale, Shed Skin Ribbon, Silt Fang, Tiny Prism Chip, Venom Crystal, Watcher Lens, Wight Shroud Cloth.
- Skyreach: Cliff Hoof Keratin, Dense Muscle Strip, Drake Membrane, Fox Whisker Cord, Gale Membrane, Glide Scale, Hawk Talon, Navigation Oil, Nest Crown Plume, Nest Twig, Ram Horn Spiral, Roc Primary Feather, Ropewing Membrane, Ruin Talon, Sky Ruin Key Fragment, Soft Sky Fur, Stone Beak, Storm Salt, Vulture Crop Stone, Wing Bone Stay.
- Finale/boss: Concord Spark, Drowned Choir Tablet, Hunter's Final Page, Perfect Prism Pearl, Sky Ruin Master Key, Surviving Smith's Notes, Wight Shroud, and any mastery sigil not already one of the packet trophies.

Curiosity terms are narrative/Codex discoveries by default and do not become inventory items unless `W1-CREATIVE-001` explicitly promotes them. Generic crates, bundles, pattern scraps, and quantity words are containers/roll context, not new identities.

## Twinbond dependency decision

Twinbond is `PARTIALLY_RATIFIED_WITH_NARROWED_BLOCKING_SUPPORT_TICKET` under `W1-CREATIVE-002`. The evidence binding is recorded in `engineering/authority/twinbond/TWINBOND_EXISTING_AUTHORITY_AUDIT.{md,json}`.

The exact aspects are `aionbound:ash_sovereign_wyrm` and `aionbound:tide_empress_wyrm`. Engineering may reuse the prepared 128×48×128 `twinbond_slice_v1` massing and the existing `twin_thrones`, `twinbond_obelisk_site`, `ceremony_anvil_site`, `twinbond_obsidian_ring`, and `twinbond_approach_marker` inputs. The current primary reward identity is `twinbond_relic` followed by Trophy Edge ignition. The old `trophy_concord_scale`, finale-key, and concord-equipment reward path is superseded for Wave 1.

Engineering may normalize and repair those exact assets, preserve the pilgrimage handoff, implement inert Trophy Edge/finale-entry state, and build nonnumeric encounter architecture. It may not choose the finale container or declare terminal completion until the narrowed ticket binds:

- isolated logical container versus same-world placement;
- Concord Spark, Memory of Four Lands presentation, and any unbound mastery-sigil disposition;
- whether Twinbond completion is mandatory for Wave 1 machine exit (current ledger assumes yes).

Boss numeric, multiplayer, persistence, and reward-guard semantics remain separately blocked by `W1-CREATIVE-003` and `W1-CREATIVE-004`. Existing wyrm/relic animations still require native repair and do not constitute phase-ready shipping art.

## Boss behavior envelope decision

Thorn Court numeric and ownership semantics are ratified exactly by `W1-003-THORN-COURT`. Kiln Sky semantics are ratified exactly by `W1-003-KILN-SKY`. Crystal Marsh, Skyreach, and finale apex encounters remain deferred under `W1-CREATIVE-003` and require separate ratification.

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

Creative loot identities and qualitative roles remain binding. The complete probability, quantity, chest-band, arena-guard, recovery, repeat-clear, and alternate-seal model is ratified for Whisperwood/Thorn Court under `W1-004-WW-CH1` and for Ashen/Kiln Sky under `W1-004-AH`. Crystal Marsh and Skyreach remain deferred.

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
| `W1-CREATIVE-001` | Whisperwood and Ashen tranches ratified; Crystal Marsh/Skyreach glossary deferred | Creative + Asset support | Implement exact approved WW and AH dispositions only |
| `W1-CREATIVE-002` | Narrowed: finale container, secondary reward presentation, mastery-sigil disposition, and machine-exit dependency | Creative + Asset support | Exact dual-wyrm/arena asset repair, pilgrimage handoff, inert finale hooks, and nonnumeric encounter architecture |
| `W1-CREATIVE-003` | Thorn Court and Kiln Sky ratified; later boss envelopes deferred | Creative support | Implement the two approved encounter envelopes exactly as proposed |
| `W1-CREATIVE-004` | Whisperwood/Chapter 1 and Ashen ratified; Crystal Marsh/Skyreach loot deferred | Creative support | Implement exact approved WW/AH intervals, guards, recovery, and optional mastery semantics |
| `W1-CREATIVE-005` | Explicitly deferred equipment sidegrade identity | Creative support | Base packet IDs and behavior interface only |
| `W1-CREATIVE-006` | Whisperwood sapling regrowth ratified | Creative support | Implement one exact-envelope existing-palette assembly and growth behavior |

Whisperwood Checkpoint 1 passed its bounded replacement smoke and its lineage remains immutable. Ashen vertical engineering may now proceed. No new checkpoint is authorized here; Crystal Marsh remains gated on Ashen vertical exit, and final Wave 1 freeze remains blocked on later-region and finale authority not covered by this ratification.

## Advisory review disposition

A read-only Grok red-team was attempted under the required safety profile and reached its turn cap after producing partial advice. Accepted: keep per-term source binding, distinguish ledger authority from Creative authority, make Twinbond exit dependency explicit, and separate phase-kit implementation from numeric boss tuning. Rejected: allowing provisional loot values without approved ranges, because the Engineering brief explicitly requires tuning inside approved ranges. Adjusted: native Blockbench gating is representative and risk-class based during scaling, with full native proof reserved for hero/locator/repaired assets and failed templates.
