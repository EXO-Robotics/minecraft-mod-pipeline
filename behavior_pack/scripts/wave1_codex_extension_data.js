// Generated from WHISPERWOOD_CODEX_EXTENSION_MAP.json. Do not hand edit.
// Authority text is copied byte-for-byte at the string level; runtime code
// may label fields but must not synthesize replacement lore.
const rows = [
  {
    "id": "lantern_post",
    "runtimeId": "aionbound:lantern_post",
    "region": "ww",
    "kind": "structure",
    "category": "structure",
    "categoryIndex": 0,
    "importance": "craft_core",
    "authorityText": {
      "environmental_story": "Old path network of the Owl faithful",
      "loot_identity": "glow_spore, oil, badge scrap",
      "progression_role": "Supports lantern_badge / hook fantasy",
      "purpose": "Path lighting language; harvest node",
      "reason_to_visit": "Light mats; navigation at night"
    },
    "events": [
      {
        "id": "codex:ww:structure:lantern_post:activated",
        "state": 2,
        "action": "first_successful_activation"
      },
      {
        "id": "codex:ww:structure:lantern_post:proximity_10s",
        "state": 2,
        "action": "recognized_structure_proximity"
      }
    ]
  },
  {
    "id": "moss_cairn",
    "runtimeId": "aionbound:moss_cairn",
    "region": "ww",
    "kind": "structure",
    "category": "structure",
    "categoryIndex": 1,
    "importance": "exploration",
    "authorityText": {
      "environmental_story": "Travelers stack moss for those lost to bark wraiths",
      "loot_identity": "Q heavy, small amber",
      "progression_role": "Emotional texture; optional stamp",
      "purpose": "Quiet memorial / rest",
      "reason_to_visit": "Curiosities; codex; low combat"
    },
    "events": [
      {
        "id": "codex:ww:structure:moss_cairn:activated",
        "state": 2,
        "action": "first_successful_activation"
      },
      {
        "id": "codex:ww:structure:moss_cairn:proximity_10s",
        "state": 2,
        "action": "recognized_structure_proximity"
      }
    ]
  },
  {
    "id": "hunter_camp",
    "runtimeId": "aionbound:hunter_camp",
    "region": "ww",
    "kind": "structure",
    "category": "structure",
    "categoryIndex": 2,
    "importance": "exploration",
    "authorityText": {
      "environmental_story": "Rangers tracked rot wolves; left in a hurry when thorn stalkers came",
      "loot_identity": "Camp mid mats, knife components, journal Q",
      "progression_role": "`ww` early; teaches base-return via leftover trophies on racks",
      "purpose": "Safe-ish tutorial structure; craft teaching",
      "reason_to_visit": "Early gear, food, journal"
    },
    "events": [
      {
        "id": "codex:ww:structure:hunter_camp:activated",
        "state": 2,
        "action": "first_successful_activation"
      },
      {
        "id": "codex:ww:structure:hunter_camp:proximity_10s",
        "state": 2,
        "action": "recognized_structure_proximity"
      }
    ]
  },
  {
    "id": "broken_wagon",
    "runtimeId": "aionbound:broken_wagon",
    "region": "ww",
    "kind": "structure",
    "category": "structure",
    "categoryIndex": 3,
    "importance": "critical_path",
    "authorityText": {
      "environmental_story": "Merchants fled heat rumors east; one wheel burned already",
      "loot_identity": "Planks, resin jars, map scrap",
      "progression_role": "Soft pointer WW→AH",
      "purpose": "Linear trail breadcrumbs",
      "reason_to_visit": "Free mats + **Ashen rumor map**"
    },
    "events": [
      {
        "id": "codex:ww:structure:broken_wagon:activated",
        "state": 2,
        "action": "first_successful_activation"
      },
      {
        "id": "codex:ww:structure:broken_wagon:proximity_10s",
        "state": 2,
        "action": "recognized_structure_proximity"
      }
    ]
  },
  {
    "id": "root_bridge",
    "runtimeId": "aionbound:root_bridge",
    "region": "ww",
    "kind": "structure",
    "category": "structure",
    "categoryIndex": 4,
    "importance": "exploration",
    "authorityText": {
      "environmental_story": "Roots grew where a wooden bridge failed",
      "loot_identity": "Repair / under cache",
      "progression_role": "Teaches vertical thinking pre-Skyreach",
      "purpose": "Traversal landmark; photo",
      "reason_to_visit": "Cross ravines; under-bridge silk"
    },
    "events": [
      {
        "id": "codex:ww:structure:root_bridge:activated",
        "state": 2,
        "action": "first_successful_activation"
      },
      {
        "id": "codex:ww:structure:root_bridge:proximity_10s",
        "state": 2,
        "action": "recognized_structure_proximity"
      }
    ]
  },
  {
    "id": "owl_shrine",
    "runtimeId": "aionbound:owl_shrine",
    "region": "ww",
    "kind": "structure",
    "category": "structure",
    "categoryIndex": 5,
    "importance": "craft_core",
    "authorityText": {
      "environmental_story": "Pre-human forest worship; eyes still watch",
      "loot_identity": "Catalysts, Owl Token",
      "progression_role": "Unique staff finish; moon path",
      "purpose": "Soft power structure; staff path",
      "reason_to_visit": "moon_sap, pendant rite"
    },
    "events": [
      {
        "id": "codex:ww:structure:owl_shrine:activated",
        "state": 2,
        "action": "first_successful_activation"
      },
      {
        "id": "codex:ww:structure:owl_shrine:proximity_10s",
        "state": 2,
        "action": "recognized_structure_proximity"
      }
    ]
  },
  {
    "id": "forest_waystone",
    "runtimeId": "aionbound:forest_waystone",
    "region": "ww",
    "kind": "structure",
    "category": "structure",
    "categoryIndex": 6,
    "importance": "critical_path",
    "authorityText": {
      "environmental_story": "Stones older than hunters; moss grows in circuit patterns",
      "loot_identity": "Activation reward only (compass needle)",
      "progression_role": "Hub return; multiplayer meet",
      "purpose": "Chapter travel / return",
      "reason_to_visit": "Unlock network stamp"
    },
    "events": [
      {
        "id": "codex:ww:structure:forest_waystone:activated",
        "state": 2,
        "action": "first_successful_activation"
      },
      {
        "id": "codex:ww:structure:forest_waystone:proximity_10s",
        "state": 2,
        "action": "recognized_structure_proximity"
      }
    ]
  },
  {
    "id": "hollow_cave_entrance",
    "runtimeId": "aionbound:hollow_cave_entrance",
    "region": "ww",
    "kind": "structure",
    "category": "structure",
    "categoryIndex": 7,
    "importance": "craft_core",
    "authorityText": {
      "environmental_story": "Widow dens under giant roots",
      "loot_identity": "Cave table",
      "progression_role": "Mid WW skill check",
      "purpose": "Vertical danger pocket",
      "reason_to_visit": "Amber, silk, elites"
    },
    "events": [
      {
        "id": "codex:ww:structure:hollow_cave_entrance:activated",
        "state": 2,
        "action": "first_successful_activation"
      },
      {
        "id": "codex:ww:structure:hollow_cave_entrance:proximity_10s",
        "state": 2,
        "action": "recognized_structure_proximity"
      }
    ]
  },
  {
    "id": "ancient_totem",
    "runtimeId": "aionbound:ancient_totem",
    "region": "ww",
    "kind": "structure",
    "category": "structure",
    "categoryIndex": 8,
    "importance": "critical_path",
    "authorityText": {
      "environmental_story": "Bound something under roots; cracks show amber light",
      "loot_identity": "R catalysts, warden_sigil seed",
      "progression_role": "Late WW; pilgrim seed",
      "purpose": "Deep forest mystery; warden foreshadow",
      "reason_to_visit": "root_heart, glyphs"
    },
    "events": [
      {
        "id": "codex:ww:structure:ancient_totem:activated",
        "state": 2,
        "action": "first_successful_activation"
      },
      {
        "id": "codex:ww:structure:ancient_totem:proximity_10s",
        "state": 2,
        "action": "recognized_structure_proximity"
      }
    ]
  },
  {
    "id": "fallen_giant_tree",
    "runtimeId": "aionbound:fallen_giant_tree",
    "region": "ww",
    "kind": "structure",
    "category": "structure",
    "categoryIndex": 9,
    "importance": "exploration",
    "authorityText": {
      "environmental_story": "Something large pushed it — not weather",
      "loot_identity": "Resource + explorer leather",
      "progression_role": "Late WW wonder; Twinbond distant echo",
      "purpose": "Massive identity prop; acorn chase",
      "reason_to_visit": "Bulk bark, rare acorn, hollow chest"
    },
    "events": [
      {
        "id": "codex:ww:structure:fallen_giant_tree:activated",
        "state": 2,
        "action": "first_successful_activation"
      },
      {
        "id": "codex:ww:structure:fallen_giant_tree:proximity_10s",
        "state": 2,
        "action": "recognized_structure_proximity"
      }
    ]
  },
  {
    "id": "mossfang_spear",
    "runtimeId": "aionbound:mossfang_spear",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 0,
    "importance": "craft_core",
    "authorityText": {
      "branch_role": "Starter reliable",
      "how_it_feels": "Reach, safe poke",
      "what_it_wants_next": "Glass tip (AH), crystal tip (CM)",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:mossfang_spear:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "weapon",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "widow_fang_dagger",
    "runtimeId": "aionbound:widow_fang_dagger",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 1,
    "importance": "craft_core",
    "authorityText": {
      "branch_role": "Ambush / caves",
      "how_it_feels": "Speed, venom narrative",
      "what_it_wants_next": "Harpy talon hybrid (SR)",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:widow_fang_dagger:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "weapon",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "thorn_whip",
    "runtimeId": "aionbound:thorn_whip",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 2,
    "importance": "craft_core",
    "authorityText": {
      "branch_role": "Anti-pack",
      "how_it_feels": "Control, pull fantasy",
      "what_it_wants_next": "Skywidow cord longer reach",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:thorn_whip:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "weapon",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "briar_cleaver",
    "runtimeId": "aionbound:briar_cleaver",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 3,
    "importance": "craft_core",
    "authorityText": {
      "branch_role": "Elite killer",
      "how_it_feels": "Heavy forest finisher",
      "what_it_wants_next": "Summit face (cliff_crystal)",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:briar_cleaver:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "weapon",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "moon_sap_staff",
    "runtimeId": "aionbound:moon_sap_staff",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 4,
    "importance": "craft_core",
    "authorityText": {
      "branch_role": "Non-brute path",
      "how_it_feels": "Soft power, light, support",
      "what_it_wants_next": "Pearl / aether focuses",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:moon_sap_staff:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "weapon",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "whisperwood_helmet",
    "runtimeId": "aionbound:whisperwood_helmet",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 5,
    "importance": "craft_core",
    "authorityText": {
      "how_it_reads": "Leaf/moss crown",
      "set_theme": "Quiet, grow, blend",
      "what_it_wants_next": "Each piece: optional hollow_amber stud (R) for set identity glow.",
      "where_born": "Whisperwood set (full 4)"
    },
    "events": [
      {
        "id": "codex:ww:equipment:whisperwood_helmet:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "armor",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "whisperwood_chest",
    "runtimeId": "aionbound:whisperwood_chest",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 6,
    "importance": "craft_core",
    "authorityText": {
      "how_it_reads": "Bark + silk",
      "set_theme": "Survival forest",
      "what_it_wants_next": "Each piece: optional hollow_amber stud (R) for set identity glow.",
      "where_born": "Whisperwood set (full 4)"
    },
    "events": [
      {
        "id": "codex:ww:equipment:whisperwood_chest:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "armor",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "whisperwood_legs",
    "runtimeId": "aionbound:whisperwood_legs",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 7,
    "importance": "craft_core",
    "authorityText": {
      "how_it_reads": "Vine wrap",
      "set_theme": "Mobility underbrush",
      "what_it_wants_next": "Each piece: optional hollow_amber stud (R) for set identity glow.",
      "where_born": "Whisperwood set (full 4)"
    },
    "events": [
      {
        "id": "codex:ww:equipment:whisperwood_legs:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "armor",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "whisperwood_boots",
    "runtimeId": "aionbound:whisperwood_boots",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 8,
    "importance": "craft_core",
    "authorityText": {
      "how_it_reads": "Root grip",
      "set_theme": "Soft terrain",
      "what_it_wants_next": "Each piece: optional hollow_amber stud (R) for set identity glow.",
      "where_born": "Whisperwood set (full 4)"
    },
    "events": [
      {
        "id": "codex:ww:equipment:whisperwood_boots:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "armor",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "root_knife",
    "runtimeId": "aionbound:root_knife",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 9,
    "importance": "craft_core",
    "authorityText": {
      "job": "Multi-tool early",
      "stage": "spawn",
      "what_it_wants_next": "Amber tip",
      "where_born": "spawn"
    },
    "events": [
      {
        "id": "codex:ww:equipment:root_knife:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "tool",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "whisperwood_hatchet",
    "runtimeId": "aionbound:whisperwood_hatchet",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 10,
    "importance": "craft_core",
    "authorityText": {
      "job": "Wood / vine clear",
      "stage": "ww",
      "what_it_wants_next": "Firestitched edge",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:whisperwood_hatchet:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "tool",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "lantern_hook",
    "runtimeId": "aionbound:lantern_hook",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 11,
    "importance": "craft_core",
    "authorityText": {
      "job": "Light + pull / climb seed",
      "stage": "ww",
      "what_it_wants_next": "Cliff grapnel (SR)",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:lantern_hook:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "tool",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "moss_charm",
    "runtimeId": "aionbound:moss_charm",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 12,
    "importance": "craft_core",
    "authorityText": {
      "fantasy_slot": "Early sustain / forest luck",
      "progression": "WW",
      "what_it_wants_next": "WW",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:moss_charm:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "accessory",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "root_bracelet",
    "runtimeId": "aionbound:root_bracelet",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 13,
    "importance": "craft_core",
    "authorityText": {
      "fantasy_slot": "Gather bonus narrative",
      "progression": "WW",
      "what_it_wants_next": "WW",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:root_bracelet:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "accessory",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "lantern_badge",
    "runtimeId": "aionbound:lantern_badge",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 14,
    "importance": "craft_core",
    "authorityText": {
      "fantasy_slot": "Light radius / fear soft",
      "progression": "WW",
      "what_it_wants_next": "WW",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:lantern_badge:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "accessory",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "moon_sap_pendant",
    "runtimeId": "aionbound:moon_sap_pendant",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 15,
    "importance": "craft_core",
    "authorityText": {
      "fantasy_slot": "Night comfort / staff synergy",
      "progression": "Late WW",
      "what_it_wants_next": "Late WW",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:moon_sap_pendant:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "accessory",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "briar_ring",
    "runtimeId": "aionbound:briar_ring",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 16,
    "importance": "craft_core",
    "authorityText": {
      "fantasy_slot": "Thorn offense chip; temper in AH",
      "progression": "WW→AH",
      "what_it_wants_next": "WW→AH",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:briar_ring:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "accessory",
    "optionalMastery": false,
    "chapterSealIdentity": false
  },
  {
    "id": "thorn_stalker_skull",
    "runtimeId": "aionbound:thorn_stalker_skull",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 17,
    "importance": "critical_path",
    "authorityText": {
      "trophy_identity": "Skull on plaque; thorns still living; amber eyesockets.",
      "type": "chapter_seal",
      "what_it_wants_next": "chapter seal / display / Edge part",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:thorn_stalker_skull:earned",
        "state": 2,
        "action": "valid_thorn_court_terminal_credit"
      }
    ],
    "equipmentSubtype": "trophy",
    "optionalMastery": false,
    "chapterSealIdentity": true
  },
  {
    "id": "briar_elk_trophy",
    "runtimeId": "aionbound:briar_elk_trophy",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 18,
    "importance": "exploration",
    "authorityText": {
      "type": "ww_alternate",
      "what_it_wants_next": "display / mastery",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:briar_elk_trophy:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "trophy",
    "optionalMastery": true,
    "chapterSealIdentity": false
  },
  {
    "id": "mosskip_trophy",
    "runtimeId": "aionbound:mosskip_trophy",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 19,
    "importance": "exploration",
    "authorityText": {
      "type": "ww_soft_seal",
      "what_it_wants_next": "display / mastery",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:mosskip_trophy:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "trophy",
    "optionalMastery": true,
    "chapterSealIdentity": false
  },
  {
    "id": "ancient_acorn_display",
    "runtimeId": "aionbound:ancient_acorn_display",
    "region": "ww",
    "kind": "equipment",
    "category": "equipment",
    "categoryIndex": 20,
    "importance": "exploration",
    "authorityText": {
      "type": "prestige",
      "what_it_wants_next": "display / mastery",
      "where_born": "ww"
    },
    "events": [
      {
        "id": "codex:ww:equipment:ancient_acorn_display:crafted",
        "state": 2,
        "action": "successful_craft_output"
      }
    ],
    "equipmentSubtype": "trophy",
    "optionalMastery": true,
    "chapterSealIdentity": false
  },
  {
    "id": "thorn_court",
    "runtimeId": "aionbound:thorn_court",
    "region": "ww",
    "kind": "boss",
    "category": "boss",
    "categoryIndex": 0,
    "importance": "critical_path",
    "authorityText": {
      "arena_language": "Root circle / totem / briar",
      "attack_names": [
        "Lunge Barb",
        "Thorn Fan",
        "Root Snare",
        "Silk Spit",
        "Howl Call",
        "Death Bloom"
      ],
      "phase_field_notes": [
        "Briar Rise",
        "Widow Wire",
        "Crown of Thorns",
        "Forest Scream"
      ],
      "placement": "late `ww`",
      "progression_role": "Opens AH soft gate; pilgrim seal 1; WW codex boss stamp.",
      "soft_requirement": "WW weapon + armor pieces",
      "thesis": "The forest fights back with patience and thorns.",
      "trophy_identity": "Skull on plaque; thorns still living; amber eyesockets."
    },
    "events": [
      {
        "id": "codex:ww:boss:thorn_court:encountered",
        "state": 1,
        "action": "valid_arena_pull"
      },
      {
        "id": "codex:ww:boss:thorn_court:defeated",
        "state": 2,
        "action": "valid_arena_terminal"
      }
    ]
  },
  {
    "id": "whisperwood_chapter",
    "runtimeId": "aionbound:codex_progression_whisperwood_chapter",
    "region": "ww",
    "kind": "progression",
    "category": "progression",
    "categoryIndex": 0,
    "importance": "critical_path",
    "authorityText": {
      "chase": "Ashen rumors at kiln-burned wagons",
      "must_do": "Kill apex or complete shrine trial",
      "primary_fantasy": "Living forest",
      "should_do": "Full WW armor"
    },
    "events": [
      {
        "id": "codex:ww:progression:whisperwood_chapter:entered",
        "state": 1,
        "action": "first_whisperwood_discovery"
      },
      {
        "id": "codex:ww:progression:whisperwood_chapter:seal_credit",
        "state": 2,
        "action": "durable_chapter_one_seal_credit"
      }
    ]
  },
  {
    "id": "ashen_rumor",
    "runtimeId": "aionbound:codex_progression_ashen_rumor",
    "region": "ww",
    "kind": "progression",
    "category": "progression",
    "categoryIndex": 1,
    "importance": "critical_path",
    "authorityText": {
      "progression_role": "Soft pointer WW→AH",
      "safe_spoiler": "Heat waits east of the burned wagons.",
      "structure_story": "Merchants fled heat rumors east; one wheel burned already"
    },
    "events": [
      {
        "id": "codex:ww:progression:ashen_rumor:broken_wagon_activated",
        "state": 2,
        "action": "broken_wagon_structure_state"
      }
    ]
  }
];

const freezeEntry = entry => Object.freeze({
  ...entry,
  authorityText: Object.freeze({ ...entry.authorityText }),
  events: Object.freeze(entry.events.map(event => Object.freeze(event))),
});

export const WHISPERWOOD_CODEX_EXTENSION_ENTRIES = Object.freeze(rows.map(freezeEntry));
