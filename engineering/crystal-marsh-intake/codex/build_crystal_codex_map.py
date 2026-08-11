#!/usr/bin/env python3
"""Build the append-only Crystal Marsh Codex/progression intake map."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


BASE_COMMIT = "b4005112cf7ad347433ec3aa42bf7a761359b95d"
BASE_TREE = "6a2008f2a4f68859ef330a5b984af5eb8d9692c8"
BASE_REGISTRY_VERSION = 3
PROPOSED_REGISTRY_VERSION = 4
STATE_SCHEMA_VERSION = 4
REGISTRY_ENTRIES_BEFORE = 140
PLAYER_BUDGET_BYTES = 8192
REGIONS = ["ww", "ah", "cm", "sr"]
CATEGORY_CAPS = {
    "resource": 20,
    "plant": 10,
    "creature": 10,
    "structure": 10,
    "equipment": 21,
    "boss": 1,
    "progression": 2,
}

AUTHORITY_REL = Path("engineering/crystal-marsh-intake/authority/CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.json")
EQUIPMENT_REL = Path("engineering/crystal-marsh-intake/equipment/CRYSTAL_EQUIPMENT_INTAKE.json")
ASHEN_MAP_REL = Path("engineering/ashen-intake/codex/ASHEN_CODEX_PROGRESSION_INTAKE_MAP.json")
CODEX_DATA_REL = Path("behavior_pack/scripts/wave1_codex_data.js")
ASHEN_DATA_REL = Path("behavior_pack/scripts/wave1_codex_ashen_data.js")
STATE_REL = Path("behavior_pack/scripts/state.js")
BUDGETS_REL = Path("behavior_pack/scripts/budgets.js")
LEDGER_REL = Path("engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json")

CREATURE_ACTIONS = {
    "prism_frog": ("observe_nearby", False),
    "crystal_newt": ("observe_nearby", False),
    "crystal_dragonfly": ("observe_airborne", False),
    "bloom_crab": ("observe_nearby", True),
    "mire_turtle": ("observe_nearby", True),
    "glass_heron": ("observe_rare", True),
    "reed_serpent": ("hostile_contact", True),
    "silt_crocodile": ("hostile_contact", True),
    "bog_watcher": ("hostile_contact", True),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event(event_id: str, action: str, stage: str, authority: str = "SAFE_NOW", blockers: list[str] | None = None, note: str | None = None) -> dict:
    row = {"id": event_id, "action": action, "stage": stage, "authority": authority}
    if blockers:
        row["blockers"] = blockers
    if note:
        row["note"] = note
    return row


def category_for(source_category: str) -> str:
    if source_category in {"resources", "blocks"}:
        return "resource"
    return source_category[:-1]


def packet_events(asset: dict) -> list[dict]:
    item_id = asset["warehouse_id"]
    source_category = asset["category"]
    prefix = f"codex:cm:{category_for(source_category)}:{item_id}"
    if source_category == "creatures":
        if item_id == "marsh_wight":
            blockers = ["W1-003-PEARL-DEPTHS", "W1-004-CM"]
            return [
                event(f"{prefix}:encountered", "valid_pearl_depths_pull", "partial", "WITHHELD", ["W1-003-PEARL-DEPTHS"]),
                event(f"{prefix}:defeated", "valid_pearl_depths_terminal", "complete", "WITHHELD", blockers),
            ]
        action, complete_on_defeat = CREATURE_ACTIONS[item_id]
        rows = [event(f"{prefix}:{action}", action, "partial")]
        if complete_on_defeat:
            rows.append(event(f"{prefix}:defeated", "defeat", "complete"))
        return rows
    if source_category == "resources":
        return [event(f"{prefix}:obtained", "first_obtain", "complete")]
    if source_category == "blocks":
        return [event(f"{prefix}:obtained", "first_obtain_or_recognized_harvest", "complete")]
    if source_category == "plants":
        return [event(f"{prefix}:harvested", "first_harvest", "complete")]
    return [event(f"{prefix}:visited", "recognized_structure_visit", "complete")]


def relationship_partition(asset: dict) -> dict:
    deps = asset["dependencies"]
    blockers = asset["classification"]["blocked_until"]
    return {
        "SAFE_NOW": {
            "where_or_acquisition_source": deps.get("acquisition", []),
            "nonnumeric_crafting_roles": deps.get("crafting", []),
            "progression_links": deps.get("progression", []),
            "equipment_links": deps.get("equipment", []),
        },
        "GATED": {
            "blockers": blockers,
            "source_loot_terms_not_promoted_by_this_map": deps.get("loot", []),
            "rule": "Source relationship prose may be displayed, but no deferred term becomes an item, recipe predicate, numeric loot route, boss completion, or reward grant.",
        },
    }


def packet_entries(authority: dict) -> list[dict]:
    indices = {key: 0 for key in CATEGORY_CAPS}
    rows = []
    for asset in authority["assets"]:
        category = category_for(asset["category"])
        row = {
            "id": asset["warehouse_id"],
            "warehouse_id": asset["warehouse_id"],
            "runtime_id": asset["runtime_id"],
            "region": "cm",
            "source_category": asset["category"],
            "codex_category": category,
            "category_index": indices[category],
            "global_append_ordinal": REGISTRY_ENTRIES_BEFORE + len(rows),
            "importance": "critical_path" if asset["warehouse_id"] in {"marsh_wight", "ruined_observatory", "deep_pool_entrance"} else "required_coverage",
            "page_scaffolding_authority": "SAFE_NOW",
            "discovery_routes": packet_events(asset),
            "relationships": relationship_partition(asset),
        }
        indices[category] += 1
        rows.append(row)
    return rows


def equipment_entries(equipment: dict, start_ordinal: int) -> list[dict]:
    rows = []
    for index, source in enumerate(equipment["direct_packet003_links"]):
        item_id = source["id"]
        blockers = list(source["gated_semantics"]["blockers"])
        rows.append({
            "id": item_id,
            "runtime_id": source["runtime_id"],
            "region": "cm",
            "codex_category": "equipment",
            "category_index": index,
            "global_append_ordinal": start_ordinal + index,
            "equipment_group": source["group"],
            "page_scaffolding_authority": "SAFE_NOW",
            "role": source["gameplay_role"],
            "provenance": source["recipe_acquisition_provenance"]["provenance"],
            "discovery_routes": [event(
                f"codex:cm:equipment:{item_id}:obtained",
                "first_owned",
                "complete",
                "WITHHELD",
                blockers,
                "Page address and identity are safe now; live completion waits for the ratified acquisition/reward path.",
            )],
            "recipe_boundary": {
                "source_formula": source["recipe_acquisition_provenance"]["source_formula"],
                "blockers": blockers,
            },
            "chapter_seal_identity": item_id == "marsh_wight_mask",
            "optional_mastery_reward": item_id in {"moon_pearl_pedestal", "crystal_obelisk_fragment"},
        })
    return rows


def full_discovery_json_bytes(registry_version: int, active_regions: list[str]) -> int:
    def hex_length(cap: int) -> int:
        return ((cap + 3) // 4) * 2
    value = {"rv": registry_version}
    for region in active_regions:
        value[region] = {category: "f" * hex_length(cap) for category, cap in CATEGORY_CAPS.items()}
    return len(json.dumps(value, separators=(",", ":"), ensure_ascii=False))


def ref(repo: Path, rel: Path, role: str) -> dict:
    return {"path": rel.as_posix(), "sha256": sha256(repo / rel), "role": role}


def build(repo: Path) -> dict:
    authority = json.loads((repo / AUTHORITY_REL).read_text())
    equipment = json.loads((repo / EQUIPMENT_REL).read_text())
    packet = packet_entries(authority)
    equipment_pages = equipment_entries(equipment, REGISTRY_ENTRIES_BEFORE + len(packet))
    boss_ordinal = REGISTRY_ENTRIES_BEFORE + len(packet) + len(equipment_pages)
    progression_ordinal = boss_ordinal + 1
    boss = {
        "id": "pearl_depths",
        "runtime_id": "aionbound:pearl_depths",
        "entity_runtime_id": "aionbound:marsh_wight",
        "region": "cm",
        "codex_category": "boss",
        "category_index": 0,
        "global_append_ordinal": boss_ordinal,
        "page_scaffolding_authority": "SAFE_NOW",
        "phase_names": ["Fog Rise", "Choir Below", "Mask Unsealed", "Flood Claim"],
        "attack_names": ["Silt Grasp", "Prism Lance", "Wail", "Reed Serpent Call", "Pearl Orbit", "Drown Hymn"],
        "arena_identity": "sunken_shrine / deep_pool hybrid",
        "discovery_routes": [
            event("codex:cm:boss:pearl_depths:encountered", "valid_pearl_depths_pull", "partial", "WITHHELD", ["W1-003-PEARL-DEPTHS"]),
            event("codex:cm:boss:pearl_depths:defeated", "valid_pearl_depths_terminal", "complete", "WITHHELD", ["W1-003-PEARL-DEPTHS", "W1-004-CM"]),
        ],
        "seal_rule": "marsh_wight_mask is the sole Chapter 3 seal identity; executable seal, entitlement, recovery, and repeat-clear semantics remain proposed, not ratified.",
    }
    progression = [
        {
            "id": "crystal_marsh_chapter",
            "runtime_id": "aionbound:codex_progression_crystal_marsh_chapter",
            "region": "cm",
            "codex_category": "progression",
            "category_index": 0,
            "global_append_ordinal": progression_ordinal,
            "soft_gate": True,
            "page_scaffolding_authority": "SAFE_NOW",
            "events": [
                event("codex:cm:progression:crystal_marsh_chapter:entered", "first_safe_cm_discovery", "partial"),
                event("codex:cm:progression:crystal_marsh_chapter:seal_credit", "durable_marsh_wight_mask_seal_credit", "complete", "WITHHELD", ["W1-003-PEARL-DEPTHS", "W1-004-CM"]),
            ],
            "seal_identity": "aionbound:marsh_wight_mask",
        },
        {
            "id": "skyreach_rumor",
            "runtime_id": "aionbound:codex_progression_skyreach_rumor",
            "region": "cm",
            "codex_category": "progression",
            "category_index": 1,
            "global_append_ordinal": progression_ordinal + 1,
            "page_scaffolding_authority": "SAFE_NOW",
            "source_hint": "Sky maps at ruined observatory",
            "presentation": "Codex/recognized-structure state only",
            "events": [
                event("codex:cm:progression:skyreach_rumor:ancient_boat_visited", "recognized_ancient_boat_visit", "partial", note="Tease only; no physical map is granted."),
                event("codex:cm:progression:skyreach_rumor:ruined_observatory_visited", "recognized_ruined_observatory_visit", "complete", note="Hard pointer to Skyreach knowledge; no physical chart identity or loot route is created."),
            ],
            "physical_chart_or_loot_route": {"authority": "WITHHELD", "blockers": ["W1-001-CM", "W1-004-CM"]},
        },
    ]
    new_entries = len(packet) + len(equipment_pages) + 1 + len(progression)
    references = [
        ref(repo, AUTHORITY_REL, "exact 50-ID Packet 003 authority and blocker partition"),
        ref(repo, EQUIPMENT_REL, "exact 11 direct plus two adjacent Packet 006 intake"),
        ref(repo, ASHEN_MAP_REL, "existing append-only WW/AH indexing authority"),
        ref(repo, CODEX_DATA_REL, "current registry v3 implementation and 140-entry prefix"),
        ref(repo, ASHEN_DATA_REL, "existing AH address payload"),
        ref(repo, STATE_REL, "schema v4 compact regional discovery and category caps"),
        ref(repo, BUDGETS_REL, "8192-byte player dynamic-property budget"),
        ref(repo, LEDGER_REL, "current ratified/deferred authority boundary"),
    ]
    return {
        "schema": "aionbound.wave1.crystal-marsh-codex-progression-intake.v1.0.0",
        "status": "APPEND_ONLY_CM_CODEX_INTAKE_SAFE_ROUTES_SEPARATED",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE, "g7_immutable": True},
        "scope": "Read-only Crystal Codex/progression intake; no BP/RP/runtime/ledger/BDS mutation.",
        "authority": references,
        "coverage": {
            "packet003_pages": 50,
            "packet003_by_category": {key: sum(row["source_category"] == key for row in packet) for key in ["creatures", "resources", "blocks", "plants", "structures"]},
            "direct_equipment_pages": 11,
            "adjacent_equipment_references_without_cm_address": 2,
            "boss_pages": 1,
            "progression_pages": 2,
            "new_registry_entries": new_entries,
            "registry_entries_before": REGISTRY_ENTRIES_BEFORE,
            "registry_entries_after": REGISTRY_ENTRIES_BEFORE + new_entries,
        },
        "registry_migration_proposal": {
            "registry_version": {"before": BASE_REGISTRY_VERSION, "after": PROPOSED_REGISTRY_VERSION},
            "state_schema_version": {"before": STATE_SCHEMA_VERSION, "after": STATE_SCHEMA_VERSION},
            "category_caps_before": CATEGORY_CAPS,
            "category_caps_after": CATEGORY_CAPS,
            "cap_change_required": False,
            "existing_prefix_entries": REGISTRY_ENTRIES_BEFORE,
            "existing_prefix_authority": "Current WW/AH registry module and address data are hash-bound above and remain untouched; CM rows append globally at ordinals 140-203 with region-local category indices.",
            "index_rule": "Never reorder, renumber, reinterpret, or overwrite any ww/ah address. CM indices are local to region cm and append only after the exact 140-entry prefix.",
            "migration": "Idempotently normalize registry rv 1/2/3 to rv 4 while preserving every existing region/category byte; absent CM categories remain zero-state; state schema stays v4.",
        },
        "budget": {
            "player_dynamic_property_bytes": PLAYER_BUDGET_BYTES,
            "fully_populated_three_region_discovery_json_bytes": full_discovery_json_bytes(PROPOSED_REGISTRY_VERSION, ["ww", "ah", "cm"]),
            "fully_populated_four_region_discovery_json_bytes": full_discovery_json_bytes(PROPOSED_REGISTRY_VERSION, REGIONS),
            "bytes_remaining_at_full_four_region_discovery_only": PLAYER_BUDGET_BYTES - full_discovery_json_bytes(PROPOSED_REGISTRY_VERSION, REGIONS),
            "growth_from_registry_append": 0,
            "reason": "Compact storage capacity was already allocated per category for all four regions; CM registry rows consume existing region-local bit addresses without increasing caps.",
        },
        "packet003_entries": packet,
        "packet006_direct_equipment_pages": equipment_pages,
        "adjacent_equipment_references": [
            {"id": row["id"], "runtime_id": row["runtime_id"], "codex_treatment": "REFERENCE_ONLY_NO_CM_ADDRESS", "future_owner": "SKYREACH_OR_PILGRIM"}
            for row in equipment["adjacent_cross_region_links"]
        ],
        "pearl_depths": boss,
        "progression_pages": progression,
        "authority_partition": {
            "SAFE_NOW": [
                "append-only CM page addresses and identity scaffolding",
                "ordinary non-apex observation/defeat/obtain/harvest/recognized-visit discovery identities",
                "nonnumeric relationship and equipment-link text",
                "Crystal chapter entry and Codex-only Skyreach rumor from recognized structures",
                "Pearl Depths phase and attack names as identity text only",
            ],
            "W1-001-CM": "Proposed term dispositions and acquisition/recipe identity closure have no effect until ratified.",
            "W1-003-PEARL-DEPTHS": "Proposed encounter thresholds, timing, reset, multiplayer, persistence, and terminal semantics have no effect until ratified.",
            "W1-004-CM": "Proposed numeric loot, seal, entitlement, recovery, repeat-clear, and mastery-reward semantics have no effect until ratified.",
            "W1-CREATIVE-005": "DEFERRED_BY_USER; no sidegrade/upgraded page, event, ID, or runtime representation is allocated.",
        },
        "ashen_runtime_dependency": {
            "status": "MANAGED_REVIEWER_ACTIVATION_BLOCKED",
            "relationship": "FINAL_INTEGRATION_DEPENDENCY_ONLY",
            "crystal_dependency": False,
            "rule": "No CM page or event calls dormant Ashen equipment-role or Kiln Sky services. Final chapter-chain reconciliation remains required before candidate freeze.",
        },
        "proof_boundary": {
            "proven": ["exact page/link coverage", "hash-bound 140-entry prefix", "append-only regional addresses", "unchanged caps/schema and computed budget", "safe/gated route separation", "deterministic regeneration"],
            "not_proven": ["runtime registry append", "event wiring", "Codex UI", "live acquisition", "boss gameplay", "persistence migration implementation", "BP/RP", "BDS", "client", "multiplayer", "console", "candidate readiness"],
        },
    }


def markdown(data: dict) -> str:
    safe = sum(route["authority"] == "SAFE_NOW" for row in data["packet003_entries"] for route in row["discovery_routes"])
    withheld = sum(route["authority"] == "WITHHELD" for row in data["packet003_entries"] for route in row["discovery_routes"])
    return "\n".join([
        "# Crystal Marsh Codex / Progression Intake",
        "",
        f"Status: `{data['status']}`",
        "",
        f"Base: `{data['base']['commit']}` / tree `{data['base']['tree']}`.",
        "",
        "This is a deterministic intake map only. It changes no BP, RP, runtime, decision ledger, or qualification state.",
        "",
        "## Exact append",
        "",
        "| Page class | Count | Address treatment |",
        "|---|---:|---|",
        "| Packet 003 | 50 | CM-local category indices |",
        "| Direct Packet 006 equipment | 11 | CM equipment indices 0-10 |",
        "| Adjacent Packet 006 references | 2 | No CM address |",
        "| Pearl Depths | 1 | CM boss index 0 |",
        "| Chapter + Skyreach rumor | 2 | CM progression indices 0-1 |",
        f"| Packet discovery routes | {safe} safe / {withheld} withheld | Decision-separated |",
        "",
        "The exact 140-entry WW/AH prefix stays unchanged. Crystal appends 64 rows at global ordinals 140-203, yielding 204 registry entries. Registry version advances 3→4; state schema remains v4; all indices are region-local.",
        "",
        "## Budget",
        "",
        f"No cap grows. Fully populated three-region compact discovery is {data['budget']['fully_populated_three_region_discovery_json_bytes']} JSON bytes; all four preallocated regions remain {data['budget']['fully_populated_four_region_discovery_json_bytes']} bytes, leaving {data['budget']['bytes_remaining_at_full_four_region_discovery_only']} bytes inside the {data['budget']['player_dynamic_property_bytes']}-byte player budget. Registry append growth in compact discovery storage is zero bytes.",
        "",
        "## Boundaries",
        "",
        "SAFE_NOW covers page/address scaffolding, ordinary discovery identities, nonnumeric relationship text, chapter entry, and a Codex-only Skyreach pointer from the ruined observatory. Physical maps/charts, final recipes/acquisition, Pearl Depths gameplay, numeric loot, seal/recovery semantics, and mastery rewards remain withheld behind the named Crystal proposals until ratified.",
        "",
        "`W1-CREATIVE-005` remains deferred and receives no sidegrade page or event. The two dormant Ashen services remain final-integration dependencies only; no Crystal page or event calls them.",
        "",
        "## Proof boundary",
        "",
        "Tests prove exact 50+11+1+2 coverage, the hash-bound 140-entry prefix, append-only CM indices, unchanged caps/schema, computed budget, blocker separation, and byte-deterministic regeneration. They do not prove runtime append/wiring, UI, acquisition, boss behavior, persistence migration, BP/RP integration, BDS, client, multiplayer, or console behavior.",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = build(args.repo_root)
    (args.output_dir / "CRYSTAL_CODEX_PROGRESSION_INTAKE_MAP.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    (args.output_dir / "CRYSTAL_CODEX_PROGRESSION_INTAKE_MAP.md").write_text(markdown(data))


if __name__ == "__main__":
    main()
