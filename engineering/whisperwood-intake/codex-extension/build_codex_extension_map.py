#!/usr/bin/env python3
"""Build the evidence-bound Whisperwood Codex extension map.

This generator intentionally emits planning data only. It does not alter the
shipping registry, persistence code, UI, event router, packs, or authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
JSON_OUT = HERE / "WHISPERWOOD_CODEX_EXTENSION_MAP.json"
MD_OUT = HERE / "WHISPERWOOD_CODEX_EXTENSION_MAP.md"

BASE_COMMIT = "00840aaae36a0cfb83955ca7b416c1d2886a6261"

AUTHORITY = [
    ("program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json", "aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md", "3116c217e06afe1fd0cd56ee742c537f948a4c91193ec831fd1b3ec362837bfc"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/08_codex/CODEX_DESIGN.md", "cc89b22d1dc548f2563c4b20d33faf8020eab9dafdbfab262321c35739a9b546"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/05_structures/STRUCTURES_DESIGN.md", "9e62ae9ba6c1da33b64ff0bfa4ac4799b083c6de995585424864d5cf2b0cb076"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/04_equipment/EQUIPMENT_PROGRESSION.md", "7ecf57e6af099ae3cda8a7432228fb5ee996f20b02b76888a82c0c1a3e3c891d"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/03_crafting/CRAFTING_TREE.md", "1f3482ba3dd9f916e08aa544153cc841871a729a2e82d9e75601715f4b5ee807"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md", "5ef85e1e0b29973a617f7dca4a8b119443c01644ba33f0e11166ef8d417d5a6f"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md", "4d80925a113bb0cca67e2405047cd228a2df2ccd2c680e1e51ccd04b6f2d63d8"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/01_progression/PLAYER_JOURNEY.md", "42ba75d9518977c71397826aa9f4daa3864df942019c809b04830fef654a1fa7"),
    ("engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json", "3e2b64785da9310b098e06981ebc95777ddc7e5d2666f803b79ce374470a9561"),
    ("engineering/authority/support-proposals/W1-CREATIVE-003/thorn_court_behavior_proposal.json", "04f7b9a75be6ac542d3488bd7563a601dcb94603905479b7c3e766c94b9d48c1"),
    ("engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json", "4412b24ad680a30e5548c731f8acba94e8fd858e4bb94f701a16eb17141f5ab7"),
]

STRUCTURES = [
    ("lantern_post", "Path lighting language; harvest node", "Light mats; navigation at night", "glow_spore, oil, badge scrap", "Old path network of the Owl faithful", "Supports lantern_badge / hook fantasy", "craft_core"),
    ("moss_cairn", "Quiet memorial / rest", "Curiosities; codex; low combat", "Q heavy, small amber", "Travelers stack moss for those lost to bark wraiths", "Emotional texture; optional stamp", "exploration"),
    ("hunter_camp", "Safe-ish tutorial structure; craft teaching", "Early gear, food, journal", "Camp mid mats, knife components, journal Q", "Rangers tracked rot wolves; left in a hurry when thorn stalkers came", "`ww` early; teaches base-return via leftover trophies on racks", "exploration"),
    ("broken_wagon", "Linear trail breadcrumbs", "Free mats + **Ashen rumor map**", "Planks, resin jars, map scrap", "Merchants fled heat rumors east; one wheel burned already", "Soft pointer WW→AH", "critical_path"),
    ("root_bridge", "Traversal landmark; photo", "Cross ravines; under-bridge silk", "Repair / under cache", "Roots grew where a wooden bridge failed", "Teaches vertical thinking pre-Skyreach", "exploration"),
    ("owl_shrine", "Soft power structure; staff path", "moon_sap, pendant rite", "Catalysts, Owl Token", "Pre-human forest worship; eyes still watch", "Unique staff finish; moon path", "craft_core"),
    ("forest_waystone", "Chapter travel / return", "Unlock network stamp", "Activation reward only (compass needle)", "Stones older than hunters; moss grows in circuit patterns", "Hub return; multiplayer meet", "critical_path"),
    ("hollow_cave_entrance", "Vertical danger pocket", "Amber, silk, elites", "Cave table", "Widow dens under giant roots", "Mid WW skill check", "craft_core"),
    ("ancient_totem", "Deep forest mystery; warden foreshadow", "root_heart, glyphs", "R catalysts, warden_sigil seed", "Bound something under roots; cracks show amber light", "Late WW; pilgrim seed", "critical_path"),
    ("fallen_giant_tree", "Massive identity prop; acorn chase", "Bulk bark, rare acorn, hollow chest", "Resource + explorer leather", "Something large pushed it — not weather", "Late WW wonder; Twinbond distant echo", "exploration"),
]

WEAPONS = [
    ("mossfang_spear", "Reach, safe poke", "Starter reliable", "Glass tip (AH), crystal tip (CM)", "reed + barb + bind"),
    ("widow_fang_dagger", "Speed, venom narrative", "Ambush / caves", "Harpy talon hybrid (SR)", "silk + fang"),
    ("thorn_whip", "Control, pull fantasy", "Anti-pack", "Skywidow cord longer reach", "cord + barb"),
    ("briar_cleaver", "Heavy forest finisher", "Elite killer", "Summit face (cliff_crystal)", "antler + claw + bind"),
    ("moon_sap_staff", "Soft power, light, support", "Non-brute path", "Pearl / aether focuses", "root shaft + amber core + moon_sap"),
]

ARMOR = [
    ("whisperwood_helmet", "Leaf/moss crown", "Quiet, grow, blend"),
    ("whisperwood_chest", "Bark + silk", "Survival forest"),
    ("whisperwood_legs", "Vine wrap", "Mobility underbrush"),
    ("whisperwood_boots", "Root grip", "Soft terrain"),
]

TOOLS = [
    ("root_knife", "spawn", "Multi-tool early", "Amber tip", "root_knife + hollow_amber tip ⇒ root_knife+ (same ID fantasy upgrade narrative)"),
    ("whisperwood_hatchet", "ww", "Wood / vine clear", "Firestitched edge", "whisperwood_planks + Moss Bind + stone"),
    ("lantern_hook", "ww", "Light + pull / climb seed", "Cliff grapnel (SR)", "planks + lantern_fur + iron-analogue scrap"),
]

ACCESSORIES = [
    ("moss_charm", "Early sustain / forest luck", "WW", "resin + glow_moss"),
    ("root_bracelet", "Gather bonus narrative", "WW", "root_flower + root fiber + small amber"),
    ("lantern_badge", "Light radius / fear soft", "WW", "lantern_fur + brass scrap"),
    ("moon_sap_pendant", "Night comfort / staff synergy", "Late WW", "moon_sap + silk thread"),
    ("briar_ring", "Thorn offense chip; temper in AH", "WW→AH", "thorn + antler chip (can finish in AH heat)"),
]

TROPHIES = [
    ("thorn_stalker_skull", "chapter_seal", "thorn_stalker_skull → display mount (already trophy mesh)", False, "Skull on plaque; thorns still living; amber eyesockets."),
    ("briar_elk_trophy", "ww_alternate", "Briar Crown + planks → briar_elk_trophy", True, None),
    ("mosskip_trophy", "ww_soft_seal", "Mosskip Crown Fragment ×3 → mosskip_trophy", True, None),
    ("ancient_acorn_display", "prestige", "ancient_acorn + pedestal wood → ancient_acorn_display", True, None),
]


def event(event_id: str, action: str, stage: str = "complete", predicate: str | None = None) -> dict:
    result = {"id": event_id, "action": action, "stage": stage}
    if predicate:
        result["predicate"] = predicate
    return result


def structure_entries() -> list[dict]:
    result = []
    for index, (identifier, purpose, visit, loot, story, progression, importance) in enumerate(STRUCTURES):
        result.append({
            "id": identifier,
            "runtime_id": f"aionbound:{identifier}",
            "region": "ww",
            "kind": "structure",
            "codex_category": "structure",
            "category_index": index,
            "importance": importance,
            "authority_text": {"purpose": purpose, "reason_to_visit": visit, "loot_identity": loot, "environmental_story": story, "progression_role": progression},
            "text_source": "creative/05_structures/STRUCTURES_DESIGN.md#whisperwood-sprint-001-props",
            "discovery_events": [
                event(f"codex:ww:structure:{identifier}:activated", "first_successful_activation"),
                event(f"codex:ww:structure:{identifier}:proximity_10s", "recognized_structure_proximity", predicate="same player remains within the bounded recognized structure site for 200 accumulated consecutive ticks"),
            ],
            "unlock_semantics": "either event completes the page; no reward or loot claim is implied",
            "runtime_dependency": "canonical authored structure recognizer plus bounded per-player proximity accumulator",
        })
    return result


def equipment_entry(identifier: str, subtype: str, index: int, authority_text: dict, craft: str, optional_mastery: bool = False) -> dict:
    if identifier == "thorn_stalker_skull":
        events = [event(
            "codex:ww:equipment:thorn_stalker_skull:earned",
            "valid_thorn_court_terminal_credit",
            predicate="active arena session + apex tag + valid death; durable seal credit and entitlement exist before page transition",
        )]
    else:
        events = [event(f"codex:ww:equipment:{identifier}:crafted", "successful_craft_output")]
    return {
        "id": identifier,
        "runtime_id": f"aionbound:{identifier}",
        "region": "ww",
        "kind": "equipment",
        "equipment_subtype": subtype,
        "codex_category": "equipment",
        "category_index": index,
        "importance": "critical_path" if identifier == "thorn_stalker_skull" else ("exploration" if optional_mastery else "craft_core"),
        "authority_text": authority_text,
        "crafting_relationship": craft,
        "discovery_events": events,
        "optional_mastery": optional_mastery,
        "chapter_seal_identity": identifier == "thorn_stalker_skull",
        "physical_item_progression_blocker": False,
        "mastery_progression_blocker": False,
    }


def equipment_entries() -> list[dict]:
    entries: list[dict] = []
    for identifier, feel, role, next_hint, craft in WEAPONS:
        entries.append(equipment_entry(identifier, "weapon", len(entries), {"how_it_feels": feel, "branch_role": role, "what_it_wants_next": next_hint, "where_born": "ww"}, craft))
    for identifier, read, theme in ARMOR:
        entries.append(equipment_entry(identifier, "armor", len(entries), {"how_it_reads": read, "set_theme": theme, "where_born": "Whisperwood set (full 4)", "what_it_wants_next": "Each piece: optional hollow_amber stud (R) for set identity glow."}, "Thick Hide / moss plates + widow_silk + Moss Bind"))
    for identifier, stage, job, upgrade, craft in TOOLS:
        entries.append(equipment_entry(identifier, "tool", len(entries), {"stage": stage, "job": job, "what_it_wants_next": upgrade, "where_born": "ww" if stage == "ww" else "spawn"}, craft))
    for identifier, fantasy, progression, craft in ACCESSORIES:
        entries.append(equipment_entry(identifier, "accessory", len(entries), {"fantasy_slot": fantasy, "progression": progression, "where_born": "ww", "what_it_wants_next": progression}, craft))
    for identifier, trophy_type, craft, optional, identity in TROPHIES:
        text = {"type": trophy_type, "where_born": "ww", "what_it_wants_next": "display / mastery" if optional else "chapter seal / display / Edge part"}
        if identity:
            text["trophy_identity"] = identity
        entries.append(equipment_entry(identifier, "trophy", len(entries), text, craft, optional))
    return entries


def build() -> dict:
    structures = structure_entries()
    equipment = equipment_entries()
    boss = {
        "id": "thorn_court",
        "runtime_id": "aionbound:thorn_court",
        "entity_runtime_id": "aionbound:thorn_stalker",
        "region": "ww",
        "kind": "boss",
        "codex_category": "boss",
        "category_index": 0,
        "importance": "critical_path",
        "authority_text": {
            "thesis": "The forest fights back with patience and thorns.",
            "placement": "late `ww`",
            "soft_requirement": "WW weapon + armor pieces",
            "arena_language": "Root circle / totem / briar",
            "phase_field_notes": ["Briar Rise", "Widow Wire", "Crown of Thorns", "Forest Scream"],
            "attack_names": ["Lunge Barb", "Thorn Fan", "Root Snare", "Silk Spit", "Howl Call", "Death Bloom"],
            "trophy_identity": "Skull on plaque; thorns still living; amber eyesockets.",
            "progression_role": "Opens AH soft gate; pilgrim seal 1; WW codex boss stamp.",
        },
        "text_sources": [
            "creative/07_bosses/BOSS_PROGRESSION.md#chapter-1-thorn-court",
            "creative/02_loot/LOOT_BOSSES.md#chapter-1-thorn-court-apex",
        ],
        "discovery_events": [
            event("codex:ww:boss:thorn_court:encountered", "valid_arena_pull", "partial", "encounter session active and entity tagged aionbound.thorn_court_apex"),
            event("codex:ww:boss:thorn_court:defeated", "valid_arena_terminal", "complete", "active arena session + apex tag + valid death event"),
        ],
        "field_note_rule": "phase names are hidden at partial state and revealed only after valid victory",
        "ecology_form_can_unlock_complete": False,
    }
    progression = [
        {
            "id": "whisperwood_chapter",
            "runtime_id": "aionbound:codex_progression_whisperwood_chapter",
            "region": "ww",
            "kind": "progression",
            "codex_category": "progression",
            "category_index": 0,
            "importance": "critical_path",
            "authority_text": {"primary_fantasy": "Living forest", "must_do": "Kill apex or complete shrine trial", "should_do": "Full WW armor", "chase": "Ashen rumors at kiln-burned wagons"},
            "text_source": "creative/01_progression/PLAYER_JOURNEY.md#chapter-goals-player-facing-intent",
            "discovery_events": [
                event("codex:ww:progression:whisperwood_chapter:entered", "first_whisperwood_discovery", "partial"),
                event("codex:ww:progression:whisperwood_chapter:seal_credit", "durable_chapter_one_seal_credit", "complete", "aionbound.player.thorn_court.seal_credit.v1 is true"),
            ],
            "shrine_trial_note": "Creative permits shrine-trial completion, but no exact shrine terminal state is ratified; do not invent one in this slice.",
        },
        {
            "id": "ashen_rumor",
            "runtime_id": "aionbound:codex_progression_ashen_rumor",
            "region": "ww",
            "kind": "progression",
            "codex_category": "progression",
            "category_index": 1,
            "importance": "critical_path",
            "authority_text": {"safe_spoiler": "Heat waits east of the burned wagons.", "structure_story": "Merchants fled heat rumors east; one wheel burned already", "progression_role": "Soft pointer WW→AH"},
            "text_sources": ["creative/08_codex/CODEX_DESIGN.md#progression-hints-language-safe-spoilers", "creative/05_structures/STRUCTURES_DESIGN.md#broken_wagon"],
            "discovery_events": [event("codex:ww:progression:ashen_rumor:broken_wagon_activated", "broken_wagon_structure_state", "complete", "recognized broken_wagon activation records landmark:broken_wagon")],
            "presentation": "Codex/structure-state page only",
            "forbidden_representation": ["map-scrap item", "inventory grant", "Ashen unlock item"],
        },
    ]
    caps_before = {"resource": 20, "plant": 10, "creature": 10}
    caps_after = {**caps_before, "structure": 10, "equipment": 21, "boss": 1, "progression": 2}
    return {
        "schema": "aionbound.wave1.whisperwood-codex-extension-map.v1.0.0",
        "status": "DETERMINISTIC_IMPLEMENTATION_MAP_ONLY",
        "base_commit": BASE_COMMIT,
        "authority": [{"path": path, "sha256": digest} for path, digest in AUTHORITY],
        "ratification_rule": "W1-003-THORN-COURT and W1-004-WW-CH1 proposal bytes remain unchanged; the ratified ledger makes their exact hashes binding.",
        "scope": {"adds_pages": 34, "existing_pages_unchanged": 40, "whisperwood_total_after_integration": 74, "edits_shipping_runtime": False},
        "coverage": {"structures": 10, "equipment": 21, "equipment_breakdown": {"weapons": 5, "armor": 4, "tools": 3, "accessories": 5, "trophies": 4}, "bosses": 1, "progression": 2},
        "compact_v4_extension": {
            "state_schema_version": {"before": 4, "after": 4},
            "registry_version": {"before": 1, "after": 2},
            "category_caps_before": caps_before,
            "category_caps_after": caps_after,
            "additional_encoded_bytes_per_populated_region": 11,
            "fully_populated_four_region_discovery_json_bytes": 596,
            "player_budget_bytes": 8192,
            "migration": "idempotently normalize absent new categories to zero-state; preserve all existing category bytes and stamps; never downgrade a state",
            "index_rule": "append categories; within each category retain the exact array order in this map",
            "future_boundary": "multi and twinbond region allocation remains outside this Whisperwood-only extension and requires a later reviewed registry migration",
        },
        "entries": {"structures": structures, "equipment": equipment, "bosses": [boss], "progression": progression},
        "cross_page_semantics": {
            "thorn_court_terminal_order": ["validate active arena terminal", "persist world completion", "persist per-player completion", "persist durable seal credit", "persist reward entitlement", "transition Thorn Court boss page complete", "transition Thorn Stalker Skull trophy page complete", "attempt recoverable physical trophy fulfillment"],
            "ecology_stalker_seal_prohibition": "ordinary thorn_stalker death may update the creature page only; it cannot complete boss/trophy/progression pages or grant seal credit/trophy",
            "mastery_trophies": {"briar_elk_trophy": "optional mastery and Codex credit", "mosskip_trophy": "optional mastery, vanity, and Codex credit", "progression_blockers": False},
            "repeat_clear": "may award the approved material package and arena chest; never reissue seal credit, trophy entitlement, or first-clear Codex transitions",
            "recovery": "Codex completion follows durable seal credit, not physical item presence; an unfulfilled trophy entitlement may reopen recovery without duplicating progression",
        },
        "runtime_integration_conflicts": [
            {"file": "behavior_pack/scripts/wave1_codex_data.js", "conflict": "registry contains only 40 entries and registry version 1", "needed": "append this map's 34 entries and bump registry version to 2 without reordering the original 40"},
            {"file": "behavior_pack/scripts/state.js", "conflict": "category caps omit structure/equipment/boss/progression", "needed": "add exact caps from compact_v4_extension; retain STATE_VERSION 4 and idempotent normalization"},
            {"file": "behavior_pack/scripts/codex.js", "conflict": "UI exposes only resource/plant/creature and has no boss field-note gating", "needed": "add four categories and state-gated exact authority fields without making chat the primary UX"},
            {"file": "behavior_pack/scripts/wave1_codex_ui_data.js", "conflict": "question rows cover only the original 40 entries", "needed": "bind exact authority_text fields from this map; do not synthesize missing lore"},
            {"file": "behavior_pack/scripts/catalog.js", "conflict": "Codex routes only block/plant/creature events; structure registry recognizes only two Whisperwood progression sites", "needed": "add compositional routes for all 10 recognized structures, 21 equipment outputs, Thorn Court terminal events, and two progression pages"},
            {"file": "behavior_pack/scripts/structures.js", "conflict": "only forest_waystone and broken_wagon have progression activation hooks; no 10-second proximity service exists", "needed": "reuse canonical site recognizers and a bounded per-player 200-tick accumulator; activation/proximity must not claim loot implicitly"},
            {"file": "behavior_pack/scripts/runtime.js", "conflict": "no exact successful-craft output event is currently routed", "needed": "select and Stable-API-audit an exact craft-completion signal before implementation; first possession is not silently equivalent to craft"},
            {"file": "Thorn Court runtime integration lane", "conflict": "boss, trophy, seal-credit, and progression transitions share one terminal event", "needed": "one compositional terminal transaction in the exact cross_page_semantics order; no early-return suppression"},
        ],
        "proof_boundary": ["map coverage and deterministic bytes", "exact authority text binding", "trigger and persistence contract", "state budget arithmetic"],
        "not_proven": ["runtime event delivery", "structure recognition", "craft event support", "UI rendering", "boss behavior", "physical trophy fulfillment", "loot", "BDS", "client", "console", "Checkpoint 1 readiness"],
    }


def markdown(data: dict) -> str:
    lines = [
        "# Whisperwood Codex extension implementation map",
        "",
        f"Base: `{data['base_commit']}`. Status: **{data['status']}**.",
        "",
        "This is a deterministic map and bounded test surface only. It does not edit or prove the shipping runtime.",
        "",
        "## Coverage",
        "",
        "| Category | Added | Result |",
        "|---|---:|---|",
        "| Structures | 10 | One page for every Packet 001 prop ID |",
        "| Equipment | 21 | 5 weapons, 4 armor, 3 tools, 5 accessories, 4 trophies |",
        "| Bosses | 1 | Thorn Court with victory-only phase field notes |",
        "| Progression | 2 | Whisperwood chapter and Ashen rumor |",
        "| **Total** | **34** | 74 Whisperwood pages after the existing 40 |",
        "",
        "## Structure pages",
        "",
        "Each structure completes on either its first recognized activation or 200 consecutive ticks of recognized-site proximity. Neither event claims loot.",
        "",
        "| ID | Importance | Story text (exact Creative text) |",
        "|---|---|---|",
    ]
    for entry in data["entries"]["structures"]:
        story = entry["authority_text"]["environmental_story"].replace("|", "\\|")
        lines.append(f"| `{entry['id']}` | `{entry['importance']}` | {story} |")
    lines += ["", "## Equipment and trophy pages", "", "| Subtype | IDs | Unlock |", "|---|---|---|"]
    for subtype in ("weapon", "armor", "tool", "accessory", "trophy"):
        group = [entry for entry in data["entries"]["equipment"] if entry["equipment_subtype"] == subtype]
        ids = ", ".join(f"`{entry['id']}`" for entry in group)
        unlock = "Valid Thorn Court terminal credit for `thorn_stalker_skull`; successful craft for the other entries" if subtype == "trophy" else "Successful craft output"
        lines.append(f"| {subtype} | {ids} | {unlock} |")
    lines += [
        "",
        "`briar_elk_trophy`, `mosskip_trophy`, and `ancient_acorn_display` remain optional. The first two are explicitly mastery-only and never fill the chapter-seal slot.",
        "",
        "## Thorn Court and progression",
        "",
        "The Thorn Court page becomes partial only on a valid arena pull and complete only on a valid arena-form terminal event. Ecology-form Thorn Stalkers cannot complete it. Victory reveals the exact phase names `Briar Rise`, `Widow Wire`, `Crown of Thorns`, and `Forest Scream`.",
        "",
        "The trophy page follows durable seal credit, not physical-item presence. This preserves once-per-player credit and recoverable best-effort physical delivery. Repeat clears cannot repeat the page, seal credit, or trophy entitlement.",
        "",
        "The Ashen rumor is a Codex/recognized-structure-state page with the exact safe hint: “Heat waits east of the burned wagons.” It is not a map-scrap item, inventory grant, or Ashen unlock token.",
        "",
        "## Compact v4 extension",
        "",
        "Keep state schema v4 and bump only the registry version from 1 to 2. Append `structure:10`, `equipment:21`, `boss:1`, and `progression:2`; never reorder the existing categories or their 40 entries. This adds 11 encoded bytes per populated region. A fully populated four-region discovery object is 596 JSON bytes against the existing 8192-byte player budget.",
        "",
        "## Runtime conflicts",
        "",
    ]
    for conflict in data["runtime_integration_conflicts"]:
        lines.append(f"- `{conflict['file']}` — {conflict['conflict']}. Needed: {conflict['needed']}.")
    lines += [
        "",
        "## Proof boundary",
        "",
        "This map proves deterministic coverage, exact authority phrase binding, trigger semantics, and state-budget arithmetic. It does not prove runtime hooks, BDS, client UI, loot, trophy delivery, boss behavior, console behavior, or Checkpoint 1 readiness.",
        "",
    ]
    return "\n".join(lines)


def encoded(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = build()
    expected = {JSON_OUT: encoded(data), MD_OUT: markdown(data)}
    if args.check:
        mismatches = [str(path) for path, content in expected.items() if not path.exists() or path.read_text() != content]
        if mismatches:
            raise SystemExit("stale generated outputs: " + ", ".join(mismatches))
        return 0
    for path, content in expected.items():
        path.write_text(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
