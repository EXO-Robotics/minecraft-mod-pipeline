#!/usr/bin/env python3
"""Generate the hash-bound Ashen Codex/progression intake map.

This is an intake authority artifact only. It does not edit or generate runtime
JavaScript, BP/RP content, Creative authority, or qualification evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AUTHORITY_PATH = ROOT / "engineering/ashen-intake/authority/ASHEN_HIGHLANDS_VERTICAL_INTAKE_MAP.json"
RUNTIME_PATH = ROOT / "engineering/ashen-intake/runtime-map/ASHEN_RUNTIME_IMPLEMENTATION_MAP.json"
WW_EXTENSION_PATH = ROOT / "engineering/whisperwood-intake/codex-extension/WHISPERWOOD_CODEX_EXTENSION_MAP.json"
CODEX_DATA_PATH = ROOT / "behavior_pack/scripts/wave1_codex_data.js"
STATE_PATH = ROOT / "behavior_pack/scripts/state.js"
OUTPUT_JSON = HERE / "ASHEN_CODEX_PROGRESSION_INTAKE_MAP.json"
OUTPUT_MD = HERE / "ASHEN_CODEX_PROGRESSION_INTAKE_MAP.md"

BASE_COMMIT = "faf8bab1785b3b847a70268c37ef813afd0495b4"
BASE_TREE = "3162be09bb1cb1b4ca10f1bf8132fbbf5e595282"

PACKET_ORDER = {
    "creatures": ["ash_mite", "ember_crow", "magma_lizard", "furnace_beetle", "char_wolf", "cinder_lynx", "ash_ram", "soot_stag", "basalt_tortoise", "ash_drake"],
    "resources": ["smolder_bark", "charbone", "sulfur_cluster", "volcanic_glass_shard", "ember_resin", "heatstone", "furnace_chitin", "basalt_core", "ash_crystal", "fire_bloom_seed"],
    "blocks": ["ash_log", "char_planks", "ash_soil", "cinder_gravel", "smolder_stone", "basalt_brick", "basalt_pillar", "heat_bark", "ember_moss", "volcanic_glass_block"],
    "plants": ["cinder_grass", "ash_fern", "smoke_reed", "char_shrub", "soot_mushroom", "magma_moss", "glow_root", "basalt_flower", "ember_vine", "fire_bloom"],
    "structures": ["fire_totem", "burned_camp", "char_wagon", "broken_bridge", "basalt_arch", "ash_watchtower", "ancient_kiln", "ember_forge", "lava_shrine", "ash_cave"],
}

EQUIPMENT_ORDER = [
    "basalt_hammer", "ember_great_axe", "ash_repeater",
    "ashen_helmet", "ashen_chest", "ashen_legs", "ashen_boots",
    "basalt_pick", "ember_hammer", "ore_chisel",
    "ember_totem", "briar_ring", "ash_drake_horn", "ember_forge_core",
]

BLOCKERS = {
    "W1-CREATIVE-001-AH": "non-warehouse Ashen ingredient/drop identities and promoted curiosity items",
    "W1-CREATIVE-003-KILN-SKY": "executable Kiln Sky thresholds, timing, reset, multiplayer ownership, persistence, terminal grants, recovery, and repeat-clear semantics",
    "W1-CREATIVE-004-AH": "Ashen loot quantities/probabilities/rolls, boss guarantees, and alternate-seal semantics",
    "W1-CREATIVE-005": "briar_ring heat-tempered sidegrade identity or representation",
}

CREATURE_STAGE = {
    "ash_mite": ("swarm_contact", "partial"),
    "ember_crow": ("observe_sky", "partial"),
    "magma_lizard": ("defeat_on_basalt", "complete"),
    "furnace_beetle": ("defeat", "complete"),
    "char_wolf": ("pack_fight", "complete"),
    "cinder_lynx": ("elite_hunt", "complete"),
    "ash_ram": ("territorial_clash", "complete"),
    "soot_stag": ("rare_plateau_sighting", "partial"),
    "basalt_tortoise": ("patient_engagement", "partial"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def boss_identity_names(runtime: dict) -> tuple[list[str], list[str]]:
    phases = runtime["boss_boundary"].get("phases", [])
    phase_names = [row["id"].replace("_", " ").title() for row in phases]
    attack_names = []
    for phase in phases:
        for attack in phase.get("available_attacks", []):
            display = attack.replace("_", " ").title()
            if display not in attack_names:
                attack_names.append(display)
    return phase_names, attack_names


def event(event_id: str, action: str, stage: str = "complete", authority: str = "SAFE_NOW", blockers=None, note=None):
    row = {"id": event_id, "action": action, "stage": stage, "authority": authority}
    if blockers:
        row["blockers"] = blockers
    if note:
        row["note"] = note
    return row


def relationship_partition(asset: dict) -> dict:
    deps = asset["dependencies"]
    return {
        "safe_now": {
            "acquisition": deps.get("acquisition", []),
            "crafting_and_progression_links": deps.get("codex", {}).get("relationship_links", []),
            "equipment_links": deps.get("equipment", []),
        },
        "withheld": {
            "W1-CREATIVE-001-AH": deps.get("loot", []),
            "W1-CREATIVE-004-AH": "no probabilities, quantities, rolls, or guarantees are bound by this map",
        },
        "rule": "Warehouse identities and approved relationship prose may be indexed; non-warehouse terms remain prose-only and cannot become item IDs, acquisition completion predicates, or shipping loot.",
    }


def packet_entry(asset: dict, category_index: int) -> dict:
    warehouse_id = asset["warehouse_id"]
    source_category = asset["category"]
    codex_category = "resource" if source_category == "blocks" else source_category[:-1]
    if source_category == "creatures":
        if warehouse_id == "ash_drake":
            events = [
                event(f"codex:ah:creature:{warehouse_id}:encountered", "valid_kiln_sky_pull", "partial", "WITHHELD", ["W1-CREATIVE-003-KILN-SKY"]),
                event(f"codex:ah:creature:{warehouse_id}:defeated", "valid_kiln_sky_terminal", "complete", "WITHHELD", ["W1-CREATIVE-003-KILN-SKY", "W1-CREATIVE-004-AH"]),
            ]
        else:
            action, stage = CREATURE_STAGE[warehouse_id]
            events = [event(f"codex:ah:creature:{warehouse_id}:{action}", action, stage)]
    elif source_category == "resources":
        events = [event(f"codex:ah:resource:{warehouse_id}:obtained", "first_obtain")]
    elif source_category == "blocks":
        events = [event(f"codex:ah:block:{warehouse_id}:obtained", "first_obtain_or_recognized_harvest")]
    elif source_category == "plants":
        events = [event(f"codex:ah:plant:{warehouse_id}:harvested", "first_harvest")]
    else:
        events = [event(f"codex:ah:structure:{warehouse_id}:visited", "recognized_structure_visit")]
    return {
        "id": warehouse_id,
        "runtime_id": asset["runtime_id"],
        "warehouse_id": warehouse_id,
        "region": "ah",
        "source_category": source_category,
        "codex_category": codex_category,
        "category_index": category_index,
        "importance": "critical_path" if warehouse_id in {"ash_drake", "ember_forge"} else "required_coverage",
        "discovery_routes": events,
        "relationships": relationship_partition(asset),
    }


def equipment_entry(item_id: str, category_index: int | None, existing_ww_index: int | None = None) -> dict:
    subtype = (
        "weapon" if item_id in EQUIPMENT_ORDER[:3] else
        "armor" if item_id in EQUIPMENT_ORDER[3:7] else
        "tool" if item_id in EQUIPMENT_ORDER[7:10] else
        "accessory" if item_id in EQUIPMENT_ORDER[10:12] else "trophy"
    )
    if item_id == "briar_ring":
        return {
            "id": item_id,
            "runtime_id": f"aionbound:{item_id}",
            "region": "ww",
            "equipment_subtype": subtype,
            "existing_registry_reference": {"region": "ww", "category": "equipment", "category_index": existing_ww_index},
            "append_new_entry": False,
            "safe_now_link": "Reference the existing base briar_ring page and its WW craft completion without changing its address.",
            "withheld_routes": [event("codex:ah:equipment:briar_ring:heat_tempered", "heat_tempered_finish", "complete", "WITHHELD", ["W1-CREATIVE-005"])],
        }
    blockers = []
    authority = "SAFE_NOW"
    note = "First-owned completion is identity-only and does not choose a recipe, reward probability, or non-warehouse ingredient."
    if item_id == "ash_drake_horn":
        authority = "WITHHELD"
        blockers = ["W1-CREATIVE-003-KILN-SKY", "W1-CREATIVE-004-AH"]
        note = "Primary critical Chapter 2 seal page completes from durable seal credit after ratification, not from ecology death or physical-item presence."
    return {
        "id": item_id,
        "runtime_id": f"aionbound:{item_id}",
        "region": "ah",
        "codex_category": "equipment",
        "category_index": category_index,
        "equipment_subtype": subtype,
        "append_new_entry": True,
        "chapter_seal_identity": item_id == "ash_drake_horn",
        "non_seal_secondary_trophy": item_id == "ember_forge_core",
        "discovery_routes": [event(
            f"codex:ah:equipment:{item_id}:{'seal_credit' if item_id == 'ash_drake_horn' else 'obtained'}",
            "durable_chapter_two_seal_credit" if item_id == "ash_drake_horn" else "first_owned",
            "complete", authority, blockers, note,
        )],
        "acquisition_boundary": {
            "safe_now": "Approved Packet 006 identity, region, role, and relationship may be indexed.",
            "withheld": ["W1-CREATIVE-001-AH", "W1-CREATIVE-004-AH"] + (["W1-CREATIVE-005"] if item_id == "briar_ring" else []),
        },
    }


def build() -> dict:
    authority = load(AUTHORITY_PATH)
    runtime = load(RUNTIME_PATH)
    phase_names, attack_names = boss_identity_names(runtime)
    ww = load(WW_EXTENSION_PATH)
    assets = {asset["warehouse_id"]: asset for asset in authority["assets"]}

    packet_entries = []
    per_codex_index = {"creature": 0, "resource": 0, "plant": 0, "structure": 0}
    for source_category in ["creatures", "resources", "blocks", "plants", "structures"]:
        for warehouse_id in PACKET_ORDER[source_category]:
            asset = assets[warehouse_id]
            codex_category = "resource" if source_category in {"resources", "blocks"} else source_category[:-1]
            packet_entries.append(packet_entry(asset, per_codex_index[codex_category]))
            per_codex_index[codex_category] += 1

    existing_briar = next(row for row in ww["entries"]["equipment"] if row["id"] == "briar_ring")
    equipment_entries = []
    append_index = 0
    for item_id in EQUIPMENT_ORDER:
        if item_id == "briar_ring":
            equipment_entries.append(equipment_entry(item_id, None, existing_briar["category_index"]))
        else:
            equipment_entries.append(equipment_entry(item_id, append_index))
            append_index += 1

    current_caps = ww["compact_v4_extension"]["category_caps_after"]
    authority_refs = [
        {"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "role": role}
        for path, role in [
            (AUTHORITY_PATH, "exact 50-ID authority and blocker partition"),
            (RUNTIME_PATH, "G7/Whisperwood reuse and ownership map"),
            (WW_EXTENSION_PATH, "append-only registry v2 indices and approved WW-to-AH rumor"),
            (CODEX_DATA_PATH, "current registry v2 implementation"),
            (STATE_PATH, "current schema v4 compact discovery implementation"),
        ]
    ]
    for row in authority["source_authorities"]:
        if row["path"] not in {ref["path"] for ref in authority_refs}:
            authority_refs.append({"path": row["path"], "sha256": row["sha256"], "role": row["role"]})

    return {
        "schema": "aionbound.wave1.ashen-codex-progression-intake.v1.0.0",
        "status": "HASH_BOUND_INTAKE_MAP_SAFE_ROUTES_SEPARATED",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE, "g7_immutable": True, "checkpoint_1_passed": True},
        "scope": "Deterministic Ashen Codex/progression intake only; no runtime, BP/RP, Creative, build, BDS, or candidate mutation.",
        "authority": authority_refs,
        "coverage": {
            "packet_002_ids": 50,
            "packet_002_by_category": {key: len(value) for key, value in PACKET_ORDER.items()},
            "packet_006_ashen_links": 14,
            "new_equipment_pages": 13,
            "existing_cross_region_equipment_links": 1,
            "boss_pages": 1,
            "progression_pages": 2,
            "new_registry_entries": 66,
            "registry_entries_before": 74,
            "registry_entries_after": 140,
        },
        "blockers": [{"id": key, "scope": value} for key, value in BLOCKERS.items()],
        "registry_migration_proposal": {
            "registry_version": {"before": 2, "after": 3},
            "state_schema_version": {"before": 4, "after": 4},
            "category_caps_before": current_caps,
            "category_caps_after": current_caps,
            "cap_change_required": False,
            "fully_populated_four_region_discovery_json_bytes_before": ww["compact_v4_extension"]["fully_populated_four_region_discovery_json_bytes"],
            "fully_populated_four_region_discovery_json_bytes_after": ww["compact_v4_extension"]["fully_populated_four_region_discovery_json_bytes"],
            "player_budget_bytes": ww["compact_v4_extension"]["player_budget_bytes"],
            "index_rule": "Append Ashen registry rows after all 74 existing rows; use region-local category indices. Never reorder, renumber, or reinterpret any existing ww address.",
            "runtime_integration_note": "Change later registry validation/counting from category-only to region+category before appending AH rows; this is a future integrator edit, not performed by this intake map.",
            "migration": "Idempotently normalize rv 1/2 state to rv 3 while preserving every existing category byte and state; absent AH categories remain zero-state; never downgrade.",
        },
        "transition_contract": {
            "ww_to_ah": {
                "source_entry": {"region": "ww", "category": "progression", "category_index": 1, "id": "ashen_rumor"},
                "exact_safe_hint": "Heat waits east of the burned wagons.",
                "consumption": "invitation_only",
                "forbidden_claims": ["AH implementation proof", "inventory map-scrap", "unlock token", "mandatory gate"],
            },
            "ah_chapter": {
                "id": "ashen_chapter",
                "runtime_id": "aionbound:codex_progression_ashen_chapter",
                "region": "ah",
                "codex_category": "progression",
                "category_index": 0,
                "soft_gate": True,
                "events": [
                    event("codex:ah:progression:ashen_chapter:entered", "first_safe_now_ah_discovery", "partial"),
                    event("codex:ah:progression:ashen_chapter:seal_credit", "durable_ash_drake_horn_seal_credit", "complete", "WITHHELD", ["W1-CREATIVE-003-KILN-SKY", "W1-CREATIVE-004-AH"]),
                ],
                "seal_rule": "ash_drake_horn is the primary critical Chapter 2 seal. ember_forge_core cannot substitute for it.",
            },
            "ah_to_cm": {
                "id": "crystal_marsh_rumor",
                "runtime_id": "aionbound:codex_progression_crystal_marsh_rumor",
                "region": "ah",
                "codex_category": "progression",
                "category_index": 1,
                "presentation": "Codex/recognized-structure state only",
                "events": [
                    event("codex:ah:progression:crystal_marsh_rumor:burned_camp_visited", "recognized_burned_camp_visit", "partial", note="No teaser-map item is granted."),
                    event("codex:ah:progression:crystal_marsh_rumor:char_wagon_visited", "recognized_char_wagon_visit", "complete", note="Binds the exact Creative chase 'Marsh pearl maps in char wagons' as a Codex hint only."),
                ],
                "physical_map_or_loot_route": {"authority": "WITHHELD", "blockers": ["W1-CREATIVE-001-AH", "W1-CREATIVE-004-AH"]},
            },
        },
        "kiln_sky": {
            "id": "kiln_sky",
            "runtime_id": "aionbound:kiln_sky",
            "region": "ah",
            "codex_category": "boss",
            "category_index": 0,
            "entity_runtime_id": "aionbound:ash_drake",
            "structure_runtime_id": "aionbound:ember_forge",
            "seal_runtime_id": "aionbound:ash_drake_horn",
            "secondary_trophy_runtime_id": "aionbound:ember_forge_core",
            "phase_names": phase_names,
            "attack_names": attack_names,
            "identity_data_authority": "SAFE_NOW",
            "events": [
                event("codex:ah:boss:kiln_sky:encountered", "valid_kiln_sky_pull", "partial", "WITHHELD", ["W1-CREATIVE-003-KILN-SKY"]),
                event("codex:ah:boss:kiln_sky:defeated", "valid_kiln_sky_terminal", "complete", "WITHHELD", ["W1-CREATIVE-003-KILN-SKY", "W1-CREATIVE-004-AH"]),
            ],
            "terminal_rule": "No boss, creature, trophy, or chapter completion may be wired until ratification. Later terminal ordering must persist durable ash_drake_horn seal credit before recoverable physical fulfillment.",
            "seal_semantics": {"primary_critical_seal": "aionbound:ash_drake_horn", "ember_forge_core_is_substitute_seal": False, "ember_forge_core_role": "secondary trophy/structure reward and approved pilgrim-part identity; never a Chapter 2 seal substitute"},
        },
        "packet_002_entries": packet_entries,
        "packet_006_ashen_links": equipment_entries,
        "safe_now_summary": [
            "Index the exact 50 warehouse IDs and approved relationships without inventing item identities or values.",
            "Index 13 new Packet 006 pages and reference the existing briar_ring page without duplication.",
            "Record ordinary non-apex observation, defeat, obtain, harvest, and structure-visit event identities.",
            "Use the existing WW Ashen rumor only as a non-gating invitation.",
            "Record Ashen chapter entry and Codex-only Crystal Marsh rumor routes.",
            "Record Kiln Sky phase/attack names as identity data only.",
        ],
        "proof_boundary": {
            "proven": ["exact roster/link coverage", "hash-bound authority inputs", "append-only index and budget proposal", "decision-blocker separation", "byte-deterministic regeneration"],
            "not_proven": ["runtime wiring", "live discovery", "Codex UI", "loot or recipes", "Kiln Sky gameplay", "persistence migration implementation", "BP/RP", "build", "BDS", "client", "multiplayer", "console", "candidate readiness"],
        },
    }


def markdown(data: dict) -> str:
    safe = sum(1 for row in data["packet_002_entries"] for route in row["discovery_routes"] if route["authority"] == "SAFE_NOW")
    withheld = sum(1 for row in data["packet_002_entries"] for route in row["discovery_routes"] if route["authority"] == "WITHHELD")
    return "\n".join([
        "# Ashen Codex / Progression Intake Map",
        "",
        f"Status: `{data['status']}`",
        "",
        "This is a deterministic intake map only. It adds no runtime, BP/RP, Creative decision, build, BDS, or candidate evidence.",
        "",
        "## Exact coverage",
        "",
        "| Scope | Count | Disposition |",
        "|---|---:|---|",
        "| Packet 002 warehouse IDs | 50 | Indexed exactly |",
        "| Packet 006 Ashen links | 14 | 13 new pages; existing `briar_ring` page referenced |",
        "| Kiln Sky | 1 boss page | Identity only; executable events withheld |",
        "| Progression | 2 pages | Ashen chapter + Crystal Marsh rumor |",
        f"| Packet event routes | {safe} safe / {withheld} withheld | Decision-separated |",
        "",
        "## Append-only proposal",
        "",
        "Registry version advances from 2 to 3; state schema remains v4. Existing 74 rows and all Whisperwood addresses stay byte-identical. Ashen adds 66 rows, producing 140 total. Category indices become explicitly region-local when runtime data is later appended.",
        "",
        "No cap grows: resource 20 already covers 10 resources plus 10 blocks; equipment 21 covers the 14 links; creature/plant/structure 10, boss 1, and progression 2 already fit. The fully populated four-region discovery object remains 596 JSON bytes under the 8192-byte player budget.",
        "",
        "## Progression invariants",
        "",
        "- The existing Whisperwood hint remains exactly: “Heat waits east of the burned wagons.” It is an invitation only.",
        "- Ashen chapter entry is soft and sandbox-compatible.",
        "- `ash_drake_horn` is the primary critical Chapter 2 seal.",
        "- `ember_forge_core` remains a secondary trophy/structure reward and approved pilgrim-part identity; it never substitutes for the chapter seal.",
        "- The Crystal Marsh rumor is Codex/recognized-structure state only; physical teaser-map loot is withheld.",
        "",
        "## Blocking boundary",
        "",
        "- `W1-CREATIVE-001-AH`: no deferred non-warehouse term becomes an item or acquisition predicate.",
        "- `W1-CREATIVE-003-KILN-SKY`: no executable boss thresholds, timing, reset, ownership, persistence, terminal, recovery, or repeat semantics.",
        "- `W1-CREATIVE-004-AH`: no numeric loot/reward route or alternate-seal behavior.",
        "- `W1-CREATIVE-005`: no `briar_ring` temper sidegrade identity or representation.",
        "",
        "## Proof boundary",
        "",
        "The tests prove roster/link coverage, authority hashes, append-only address rules, unchanged caps/budget, blocker separation, seal semantics, and deterministic regeneration. They do not prove runtime wiring, live gameplay, persistence migration, packaging, BDS, client, multiplayer, or console behavior.",
        "",
    ])


def main() -> None:
    data = build()
    OUTPUT_JSON.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(markdown(data), encoding="utf-8")


if __name__ == "__main__":
    main()
