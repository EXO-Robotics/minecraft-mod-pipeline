#!/usr/bin/env python3
"""Build the evidence-bound Whisperwood Codex implementation map."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent

AUTHORITY = [
    {"path": "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json", "sha256": "aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5"},
    {"path": "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md", "sha256": "3116c217e06afe1fd0cd56ee742c537f948a4c91193ec831fd1b3ec362837bfc"},
    {"path": "program/crazycraft-pack-production-v1/studio-prep/creative/08_codex/CODEX_DESIGN.md", "sha256": "cc89b22d1dc548f2563c4b20d33faf8020eab9dafdbfab262321c35739a9b546"},
    {"path": "program/crazycraft-pack-production-v1/studio-prep/creative/08_codex/CODEX_ENTRIES_CREATURES.md", "sha256": "fd07694eee0c8d478b44363e822e0116f4ca09c92775661350ed8468342b01bf"},
    {"path": "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_WHISPERWOOD.md", "sha256": "c6846ecfcf51c1bdbe62b3ef81f37e7e86e6466a62b46f72cb3685516a216f24"},
    {"path": "program/crazycraft-pack-production-v1/studio-prep/creative/03_crafting/CRAFTING_TREE.md", "sha256": "1f3482ba3dd9f916e08aa544153cc841871a729a2e82d9e75601715f4b5ee807"},
    {"path": "program/crazycraft-pack-production-v1/studio-prep/creative/06_world_gen/WORLD_GENERATION.md", "sha256": "bc18a1e1f73d6045ab7e583afe910ca13d4776d439c8f3dfb45dae5784372f4b"},
]

G7_EVIDENCE = [
    {"path": "behavior_pack/scripts/codex.js", "sha256": "dff90e98c497fe7e1773e9f0be09a61cecd5098d1b4cf4955b43b78484467890"},
    {"path": "behavior_pack/scripts/state.js", "sha256": "3ab5e27385eed680cf5c4349e41cb19ddf61d00d7bde9b769ae3f68cf1ff37af"},
    {"path": "behavior_pack/scripts/catalog.js", "sha256": "5d1d4bccf60b21f439daee51b82b9418fd2356ab54459ee6a51849566d22c238"},
]

# id, rarity, found, make, next, importance, blockers
RESOURCES = [
    ("whisper_bark", "common", "Bark gathered from Whisperwood logs; also carried by boars and bark wraiths.", "Whisperwood planks, handles, stocks, hatchet parts, and armor wrap.", "Use the first forest wood currency to establish the Whisperwood craft loop.", "craft_core", ["loot_probability:W1-CREATIVE-004", "world_distribution:WORLDGEN_RUNTIME"]),
    ("moss_resin", "common", "Binder gathered from moss floors and the mosskip family.", "Moss Bind Glue, moss charms, and repair kits.", "Pair it with glow spore for the forest binder path.", "craft_core", ["loot_probability:W1-CREATIVE-004", "equipment_closure:PACKET-006"]),
    ("glow_spore", "uncommon", "A soft-light spore from mushrooms, caves, and lantern posts.", "Light crafts, Moss Bind Glue, lantern badges, and lantern hooks.", "Night paths and bloom patches lead toward the utility-light line.", "craft_core", ["loot_probability:W1-CREATIVE-004", "equipment_closure:PACKET-006"]),
    ("hollow_amber", "uncommon_rare", "Amber found in hollow wood, caves, and bark wraith encounters.", "Amber Core, weapon cores, the moon-sap staff, and root-knife refinement.", "Search hollow wood and root caves for the mid-forest catalyst.", "craft_core", ["loot_probability:W1-CREATIVE-004", "component_presentation:W1-CREATIVE-001"]),
    ("lantern_fur", "uncommon", "Glow-bearing fur from lantern hares and bloom fields.", "Lantern badges, lantern-hook light heads, and utility trim.", "Follow safe night trails and lantern blooms toward light utility.", "craft_core", ["loot_probability:W1-CREATIVE-004", "equipment_closure:PACKET-006"]),
    ("moon_sap", "rare", "Night sap associated with trees, lily pools, and bark wraiths.", "Moon-sap staff, moon-sap pendant, and Amber Core.", "Lily pools and deep-night forest open the soft-power path.", "critical_path", ["loot_probability:W1-CREATIVE-004", "equipment_closure:PACKET-006"]),
    ("root_heart", "rare", "A deep-root catalyst, with a rare route through rootback boars.", "Living Root Focus and late Whisperwood staff or bracelet refinement.", "Investigate deep roots once the early binder loop is established.", "critical_path", ["loot_probability:W1-CREATIVE-004", "component_presentation:W1-CREATIVE-001"]),
    ("briar_antler", "uncommon_rare", "Antler material from briar elk and briar thickets.", "Cleaver blanks, briar cleavers, whips, and trophy displays.", "Rare meadows lead into the elite equipment and trophy path.", "craft_core", ["loot_probability:W1-CREATIVE-004", "equipment_closure:PACKET-006"]),
    ("widow_silk", "uncommon_rare", "Light-drinking silk from widow dens beneath giant roots.", "Thorn Cord, armor stitching, thorn whips, and widow-fang daggers.", "Caves beneath roots connect silk to the elite craft line.", "craft_core", ["loot_probability:W1-CREATIVE-004", "component_presentation:W1-CREATIVE-001"]),
    ("ancient_acorn", "epic_curiosity", "A prestige curiosity found at giant trees or very rarely through briar elk.", "Ancient Acorn Display with pedestal wood.", "Its approved role is curiosity and Twinbond foreshadow, not a required finale key.", "exploration", ["loot_probability:W1-CREATIVE-004", "twinbond_presentation:W1-CREATIVE-002"]),
]

# id, found, make, next, importance, blockers
BLOCKS = [
    ("whisperwood_log", "Primary canopy trunk and common bark source.", "Whisperwood planks, bark harvest, handles, and stocks.", "Turn the forest silhouette into the first building and crafting material.", "craft_core", ["world_distribution:WORLDGEN_RUNTIME"]),
    ("stripped_whisperwood_log", "Worked Whisperwood timber.", "Intermediate timber for player builds.", "Use crafted forest wood to extend camps and bases.", "craft_core", []),
    ("whisperwood_wood", "Bark-on-all-sides timber used for deep-woods massing.", "Structural builds and forest massing.", "Carry deep-forest identity into player construction.", "exploration", []),
    ("whisperwood_planks", "Safe-forest building timber made from Whisperwood wood.", "Furniture, handles, camps, and trophy bases.", "Planks connect gathered bark and logs to tools and shelter.", "craft_core", []),
    ("whisperwood_leaves", "The green canopy cover of Whisperwood.", "Compost or decay relationships where runtime rules support them.", "Canopy density marks the living forest and its clearings.", "exploration", ["world_distribution:WORLDGEN_RUNTIME"]),
    ("whisperwood_sapling", "The regrowth form of Whisperwood trees.", "Renewable tree growth and future logs.", "Replanting closes the forest sustainability loop.", "craft_core", ["world_distribution:WORLDGEN_RUNTIME"]),
    ("whisperwood_roots", "Root flooring and ravine footing in the forest.", "Harvest fantasy and traversal footing.", "Root paths lead toward ravines, caves, and deeper resources.", "exploration", ["world_distribution:WORLDGEN_RUNTIME"]),
    ("moss_bark", "Moss-covered accent bark from the forest floor language.", "Binding materials and build detail.", "Moss identity points back to resin and the early binder loop.", "craft_core", ["world_distribution:WORLDGEN_RUNTIME"]),
    ("hollow_wood", "Cave-adjacent timber associated with amber nodes.", "Mystery builds and hollow-amber source fantasy.", "Search hollows and caves for the mid-forest catalyst.", "exploration", ["world_distribution:WORLDGEN_RUNTIME"]),
    ("forest_brick", "Built stone language used by ruins and waystone pads.", "Structure construction and shrine-language builds.", "Civilization scars point toward shrines, waystones, and discovery.", "exploration", ["structure_runtime:STRUCTURE_BYTES_NOT_PRESENT"]),
]

PLANTS = [
    ("star_grass", "common", "Ground cover gathered in clearings.", "Early fiber and fodder.", "Use the common clearing plant to begin the fiber line.", "craft_core", ["world_distribution:WORLDGEN_RUNTIME"]),
    ("whisper_fern", "common", "Understory fern gathered beneath the canopy.", "Bandage analogue and soft materials.", "The understory supplies early recovery materials.", "craft_core", ["world_distribution:WORLDGEN_RUNTIME"]),
    ("pale_reed", "common", "Reed gathered at wet forest edges.", "Spear shafts, especially the mossfang spear.", "Wet edges connect early gathering to the first weapon path.", "critical_path", ["equipment_closure:PACKET-006"]),
    ("glow_moss", "uncommon", "Soft-glowing moss found in caves and at night.", "Light material, dye, and moss charm.", "Caves turn night comfort into the charm path.", "craft_core", ["equipment_closure:PACKET-006"]),
    ("mooncap_mushroom", "uncommon", "A shade-and-night mushroom from Whisperwood patches.", "Food and minor-buff consumables.", "Night gathering supports longer forest expeditions.", "exploration", ["loot_tuning:W1-CREATIVE-004"]),
    ("lantern_bloom", "uncommon", "Path flower clustered near lantern posts and lantern hares.", "Light materials and the lantern equipment path.", "Bloom patches and hare trails identify safer night routes.", "exploration", ["equipment_closure:PACKET-006"]),
    ("hollow_lily", "rare", "Pool flower associated with moon sap.", "Moon-sap catalyst helper.", "Lily pools point toward the forest soft-power line.", "critical_path", ["loot_tuning:W1-CREATIVE-004"]),
    ("root_flower", "uncommon", "Colored flower gathered in root zones.", "Dye and the root bracelet.", "Root zones lead toward bracelet materials and deeper catalysts.", "craft_core", ["equipment_closure:PACKET-006"]),
    ("briar_vine", "uncommon", "Binding vine gathered in thorn thickets.", "Thorn Cord and thorn whips.", "Thickets connect binding material to the forest combat line.", "craft_core", ["component_presentation:W1-CREATIVE-001", "equipment_closure:PACKET-006"]),
    ("ember_thistle", "uncommon", "Transition plant at the forest edge toward ash.", "Minor heat-resistance seed.", "Heat waits beyond the forest edge; this plant is the approved Ashen foreshadow.", "critical_path", ["loot_tuning:W1-CREATIVE-004", "ashen_runtime:SLICE-B"]),
]

# id, rarity, role, discovery action, found, make, next, importance, blockers
CREATURES = [
    ("mosskip_fawn", "common", "ambient_young", "observe", "A curious young mosskip seen in sun-flecked clearings.", "Its soft moss scraps feed early Moss Bind Glue.", "Fawns point toward does and crowned bucks.", "exploration", ["loot_probability:W1-CREATIVE-004"]),
    ("mosskip_doe", "common", "ambient_adult", "observe", "The quiet center of Whisperwood herds, observed along dusk paths.", "Moss resin and soft hide support binding and early armor padding.", "Dusk paths lead toward lantern blooms.", "exploration", ["loot_probability:W1-CREATIVE-004"]),
    ("mosskip_buck", "uncommon", "neutral_territorial", "observe_then_defeat", "A branch-antlered herd guardian near calves and clearings.", "Crown fragments form the mosskip trophy; moss plates support armor.", "Crowned bucks open the forest trophy path.", "craft_core", ["loot_probability:W1-CREATIVE-004", "alternate_seal:W1-CREATIVE-004"]),
    ("lantern_hare", "uncommon", "ambient_curiosity", "observe", "A glow-furred hare seen at night near blooms.", "Lantern fur supports badges, hooks, and light trim.", "Its trails mark safer night ground.", "exploration", ["loot_probability:W1-CREATIVE-004"]),
    ("rootback_boar", "uncommon", "neutral_provoked", "observe_then_defeat", "A bark-plated understory animal that fights when provoked.", "Tusks and root plates feed cleavers and armor; a rare root heart feeds staff cores.", "Deep rooters reveal hollow amber and late forest catalysts.", "craft_core", ["loot_probability:W1-CREATIVE-004", "ingredient_identity:W1-CREATIVE-001"]),
    ("briar_elk", "rare", "elite_grazer_mini_apex", "observe_then_defeat", "A rare meadow grazer with living thorn antlers.", "Briar antler and crown materials support cleavers and the briar-elk trophy.", "Rare meadows lead to the elite trophy path.", "craft_core", ["loot_probability:W1-CREATIVE-004", "alternate_seal:W1-CREATIVE-004"]),
    ("rot_wolf", "uncommon", "hostile_pack", "defeat", "A hostile pack hunter on deep trails, especially at night.", "Fangs and pelts support dagger and early armor relationships.", "Pack howls warn that a thorn stalker may be near.", "exploration", ["loot_probability:W1-CREATIVE-004", "ingredient_identity:W1-CREATIVE-001"]),
    ("thorn_stalker", "legendary", "hostile_elite_chapter_apex", "defeat", "Whisperwood's chapter-one apex, encountered in deep briar and its approved arena path.", "Barbs and claws feed forest weapons; the thorn-stalker skull is the chapter seal and display trophy.", "Defeating the forest's first true trial supports the Ashen handoff and later pilgrimage.", "critical_path", ["boss_envelope:W1-CREATIVE-003", "loot_probability:W1-CREATIVE-004", "ingredient_identity:W1-CREATIVE-001"]),
    ("hollow_widow_spider", "rare", "hostile_elite", "defeat", "A cave elite found in widow dens beneath giant roots.", "Widow silk supports armor stitching, Thorn Cord, whips, and daggers.", "Root caves connect discovery to the forest's elite craft line.", "craft_core", ["loot_probability:W1-CREATIVE-004", "ingredient_identity:W1-CREATIVE-001"]),
    ("bark_wraith", "rare", "elite_spectral", "defeat", "A deep-night spectral elite associated with ancient totems.", "Hollow amber and moon sap support staff, pendant, and late forest crafting.", "Totems and night deepen the soft-power and mystery paths.", "exploration", ["loot_probability:W1-CREATIVE-004", "structure_runtime:STRUCTURE_BYTES_NOT_PRESENT"]),
]


def stamp(kind: str, item_id: str, action: str) -> str:
    return f"codex:ww:{kind}:{item_id}:{action}"


def base_entry(kind: str, item_id: str, rarity: str, found: str, make: str, nxt: str, importance: str, blockers: list[str]) -> dict:
    action = "harvested" if kind in {"resource", "plant"} else "discovered"
    acquisition_blockers = [b for b in blockers if b.startswith(("loot_", "world_", "structure_", "ashen_"))]
    crafting_blockers = [b for b in blockers if b.startswith(("equipment_", "component_", "ingredient_", "alternate_"))]
    progression_blockers = [b for b in blockers if b.startswith(("boss_", "twinbond_", "alternate_", "ashen_", "structure_"))]
    question = lambda text, blocked: {
        "text": text,
        "data_status": "SAFE_AUTHORED_GUIDANCE_DATA",
        "live_status": "BLOCKED_RUNTIME_COMPLETION" if blocked else "SAFE_FOR_TARGET_INTEGRATION",
        "blocked_by": blocked,
    }
    return {
        "id": item_id,
        "warehouse_id": item_id,
        "runtime_id": f"aionbound:{item_id}",
        "entry_kind": kind,
        "codex_category": "resource" if kind == "block" else kind,
        "region": "ww",
        "rarity_feel": rarity,
        "importance": importance,
        "importance_assignment": "ENGINEERING_INDEX_DERIVATION_FROM_APPROVED_RELATIONSHIP",
        "discovery_order_action": "harvest_resource_plant" if kind in {"resource", "plant"} else "observe_ambient",
        "discovery_stamps": [{"stage": "complete", "id": stamp(kind, item_id, action), "event": action}],
        "player_questions": {
            "what_did_i_find": question(found, acquisition_blockers),
            "what_can_i_make": question(make, crafting_blockers),
            "what_should_i_investigate_next": question(nxt, progression_blockers),
        },
        "integration": {
            "data_target": "behavior_pack/scripts/catalog.js::CODEX_ENTRY_REGISTRY",
            "presentation_target": "non_chat_codex_surface",
            "primary_chat_ux_allowed": False,
            "persistence": "successor_v4_compact_codex_discovery",
        },
        "readiness": {
            "discovery_entry_and_stamp_contract": "SAFE_NOW",
            "guidance_data": "SAFE_NOW",
            "live_acquisition_progression_completion": "SAFE_NOW" if not blockers else "BLOCKED_BY_LISTED_DEPENDENCIES",
        },
        "runtime_completion_blocked_by": blockers,
    }


def build() -> dict:
    entries = []
    for item_id, rarity, found, make, nxt, importance, blockers in RESOURCES:
        entries.append(base_entry("resource", item_id, rarity, found, make, nxt, importance, blockers))
    for item_id, found, make, nxt, importance, blockers in BLOCKS:
        entry = base_entry("block", item_id, "not_assigned_by_creative", found, make, nxt, importance, blockers)
        crafted = item_id in {"stripped_whisperwood_log", "whisperwood_wood", "whisperwood_planks", "forest_brick"}
        event = "crafted" if crafted else "harvested"
        entry["discovery_order_action"] = "harvest_resource_plant"
        entry["discovery_stamps"] = [{"stage": "complete", "id": stamp("block", item_id, event), "event": event}]
        entries.append(entry)
    for item_id, rarity, found, make, nxt, importance, blockers in PLANTS:
        entries.append(base_entry("plant", item_id, rarity, found, make, nxt, importance, blockers))
    for item_id, rarity, role, action, found, make, nxt, importance, blockers in CREATURES:
        entry = base_entry("creature", item_id, rarity, found, make, nxt, importance, blockers)
        entry["role"] = role
        if action == "observe":
            entry["discovery_order_action"] = "observe_ambient"
            entry["discovery_stamps"] = [{"stage": "partial", "id": stamp("creature", item_id, "observed"), "event": "observe_nearby"}]
        elif action == "observe_then_defeat":
            entry["discovery_order_action"] = "observe_ambient_then_defeat_hostile"
            entry["discovery_stamps"] = [{"stage": "partial", "id": stamp("creature", item_id, "observed"), "event": "observe_nearby"}]
            entry["detail_events"] = [{"stage": "complete", "id": f"codex_detail:ww:creature:{item_id}:defeated", "event": "defeat"}]
        else:
            entry["discovery_order_action"] = "defeat_hostile"
            entry["discovery_stamps"] = [{"stage": "complete", "id": stamp("creature", item_id, "defeated"), "event": "defeat"}]
        entries.append(entry)

    return {
        "schema": "aionbound.wave1.whisperwood-codex-implementation-map.v1.0.0",
        "status": "EVIDENCE_BOUND_DATA_MAP_NO_RUNTIME_IMPLEMENTATION",
        "base_commit": "c4d77b6ae11672d1a62f2be3b83153692cd5c5a9",
        "scope": {"region": "ww", "categories": ["resources", "blocks", "plants", "creatures"], "counts": {"resources": 10, "blocks": 10, "plants": 10, "creatures": 10, "total": 40}},
        "authority": AUTHORITY,
        "g7_schema_evidence": G7_EVIDENCE,
        "creative_rules": {
            "no_lore_rewrite": True,
            "discovery_order": ["observe_ambient", "harvest_resource_plant", "defeat_hostile", "activate_structure", "craft_equipment", "defeat_boss", "collect_curiosity"],
            "importance_vocabulary": ["critical_path", "craft_core", "exploration", "finale"],
            "page_questions": ["what_did_i_find", "what_can_i_make", "what_should_i_investigate_next"],
            "partial_then_complete": True,
            "importance_derivation": {
                "critical_path": "explicit chapter, seal, transition, or progression-role relationship",
                "craft_core": "explicit material-to-component or equipment relationship",
                "exploration": "explicit ecology, curiosity, landmark, or optional-discovery relationship",
                "finale": "reserved; no Whisperwood entry is promoted to finale solely from foreshadowing",
            },
        },
        "block_category_compatibility": {
            "decision": "MAP_AS_RESOURCE_CATEGORY_WITH_BLOCK_ENTRY_KIND",
            "reason": "Creative's frozen page-category vocabulary does not include block; this preserves all ten block identities without inventing a new Creative category.",
        },
        "minimal_successor_integration": {
            "keep": [
                "G7's idempotent migration pattern and all existing gameplay stamps",
                "bounded deduplicated strings in player.stamps for legacy and non-Codex progression",
                "composed discovery and action routing so a stamp never suppresses another action",
            ],
            "successor_schema_extension": {
                "version": 4,
                "shape": "player.codex.discovery.<region>.<category> as registry-versioned compact two-bit states: locked, partial, complete",
                "event_contract": "exact discovery stamp IDs in this map are canonical event keys translated by the Codex service; they are not appended indefinitely to legacy player.stamps",
                "migration": "idempotently preserve v3 stamps/topic/goals and initialize empty compact discovery maps; translate any recognized Codex stamps if present",
                "why": "G7 caps stamps at 128 and player JSON at 8192 bytes; four regions already imply 160 pages before structures, equipment, and bosses, so raw per-page stamp persistence cannot be the final Wave 1 format.",
            },
            "replace_content_keep_patterns": [
                "Replace G7 CODEX_TOPICS content with a registry/view-model fed by these entries.",
                "Resolve entry visibility from compact discovery state; do not persist copied entry content.",
                "Keep codex.topic as a backward-compatible navigation fallback; new UI selection may remain session-local until a separately authorized migration.",
            ],
            "presentation": {
                "primary": "Bedrock form/book-style Codex surface that renders locked, partial, and complete views",
                "fallback": "bounded diagnostic message only",
                "forbidden_primary": "chat-spam page navigation",
            },
            "migration_required": True,
            "reason": "A compact additive successor migration preserves G7 semantics while avoiding the proven 128-stamp and 8192-byte Wave 1 capacity conflict.",
        },
        "readiness_legend": {
            "SAFE_NOW": "Creative identity, stamp contract, and authored relationship data can be registered now.",
            "BLOCKED_BY_LISTED_DEPENDENCIES": "The live acquisition or progression claim cannot be completed until the entry's explicit runtime dependencies close.",
        },
        "not_proven": ["BP or RP integration", "Codex UI", "event wiring", "loot or world generation", "Stable BDS", "client rendering", "candidate readiness"],
        "entries": entries,
    }


def render_md(data: dict) -> str:
    lines = [
        "# Whisperwood Codex implementation map",
        "",
        "Status: **evidence-bound data map only**. This does not edit BP/RP content, implement UI, or claim runtime proof.",
        "",
        "## Integration decision",
        "",
        "Preserve G7's migration pattern and existing gameplay stamps, but add a minimal v4 Codex discovery field using registry-versioned compact two-bit states (locked/partial/complete). G7 caps the raw stamp array at 128 and player JSON at 8192 bytes, while four regions already imply 160 pages before structures, equipment, and bosses. The exact IDs below are canonical discovery event keys translated into compact state, not an indefinitely growing stamp array. The existing chat-driven Codex is a schema predecessor, not the target UX; Wave 1 should render a book/form surface and reserve chat for bounded diagnostics.",
        "",
        "Creative's frozen category vocabulary has no `block` category. The map therefore retains `entry_kind=block` while using `codex_category=resource`, avoiding a lore/schema invention.",
        "",
        "## Entry matrix",
        "",
        "| Kind | ID | Importance | Unlock stamp(s) | Readiness | Blockers |",
        "|---|---|---|---|---|---|",
    ]
    for e in data["entries"]:
        stamps = "<br>".join(s["id"] for s in e["discovery_stamps"])
        blockers = "<br>".join(e["runtime_completion_blocked_by"]) or "none"
        readiness = e["readiness"]["live_acquisition_progression_completion"]
        lines.append(f"| {e['entry_kind']} | `{e['id']}` | {e['importance']} | `{stamps}` | {readiness} | {blockers} |")
    lines += [
        "",
        "## Player-facing answer contract",
        "",
        "Every JSON entry binds three concise fields: what the player found, what the material or creature connects to, and the next approved investigation. These are relationship summaries from Creative authority, not new lore. Creature prose remains owned by `CODEX_ENTRIES_CREATURES.md`.",
        "",
        "## Proof boundary",
        "",
        "This map proves deterministic coverage and schema compatibility only. It does not prove event delivery, loot probabilities, world distribution, equipment behavior, boss semantics, UI quality, BDS load, or client behavior.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    data = build()
    (HERE / "WHISPERWOOD_CODEX_IMPLEMENTATION_MAP.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    (HERE / "WHISPERWOOD_CODEX_IMPLEMENTATION_MAP.md").write_text(render_md(data))


if __name__ == "__main__":
    main()
