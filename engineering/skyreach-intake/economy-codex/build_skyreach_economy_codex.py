#!/usr/bin/env python3
"""Build the safe-now Skyreach economy/Codex authority scaffold."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AUTHORITY = ROOT / "engineering/skyreach-intake/authority/SKYREACH_VERTICAL_INTAKE_MAP.json"
STATIC = ROOT / "engineering/skyreach-intake/static-foundations/SKYREACH_STATIC_FOUNDATIONS_AUTHORITY.json"
LEDGER = ROOT / "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json"
CRYSTAL_CODEX = ROOT / "behavior_pack/scripts/wave1_codex_crystal_data.js"
STATE = ROOT / "behavior_pack/scripts/state.js"
OUTPUT_JSON = HERE / "SKYREACH_ECONOMY_CODEX_SCAFFOLD.json"
OUTPUT_MD = HERE / "SKYREACH_ECONOMY_CODEX_SCAFFOLD.md"

BASE_COMMIT = "10e60dfb4ae95996286d455473612b58c234ec9b"
BASE_TREE = "57088d0df2e3ccdf4a8e463ee09d3d6fbe7bd4bf"
PREFIX_COUNT = 204

CATEGORY = {"creatures": "creature", "resources": "resource", "blocks": "resource", "plants": "plant", "structures": "structure"}
ACTION = {"creatures": "observe_nearby", "resources": "first_obtain", "blocks": "first_obtain_or_recognized_harvest", "plants": "first_harvest", "structures": "recognized_structure_visit"}

RESOURCE_PURPOSES = {
    "sky_feather": ["glider_panel"],
    "cloud_wool": ["soft_landing_pad"],
    "updraft_reed_item": ["lift_tonic"],
    "sky_vine_item": ["climbing_rope"],
    "wind_silk": ["climbing_rope", "glider_panel"],
    "cliff_crystal": ["climbing_hook_head"],
    "float_resin": ["soft_landing_pad", "lift_tonic"],
    "lift_bloom_item": ["lift_tonic"],
    "storm_pinion": ["trophy_edge_blank", "display"],
    "aether_stone": ["aether_bind", "surveyor_staff", "pilgrimage"],
}

PURPOSE_GATES = {
    "glider_panel": ["W1-001-SR"],
    "climbing_hook_head": ["W1-001-SR"],
    "trophy_edge_blank": ["W1-003-STORM-NEST", "W1-004-SR"],
    "display": ["W1-004-SR"],
}

PACKET006 = {
    "tools_utility": ["surveyor_staff", "trail_compass", "lantern_hook_grapnel_upgrade"],
    "accessories": ["surveyor_medallion", "warden_sigil"],
    "trophies_seals": ["storm_pinion"],
    "sidegrades": ["summit_hammer", "skywidow_whip", "gale_prism_bow", "nest_talon_dagger", "stormcloak"],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    authority = json.loads(AUTHORITY.read_text())
    category_indices: dict[str, int] = {}
    rows = []
    for ordinal, asset in enumerate(authority["assets"], PREFIX_COUNT):
        source_category = asset["category"]
        category = CATEGORY[source_category]
        index = category_indices.get(category, 0)
        category_indices[category] = index + 1
        asset_id = asset["id"]
        event_id = f"codex:sr:{category}:{asset_id}:{ACTION[source_category]}"
        row = {
            "id": asset_id,
            "runtime_id": f"aionbound:{asset_id}",
            "region": "sr",
            "source_category": source_category,
            "codex_category": category,
            "category_index": index,
            "global_append_ordinal": ordinal,
            "discovery_event": {"id": event_id, "action": ACTION[source_category], "state": 1 if source_category == "creatures" else 2},
            "implementation": "SAFE_NOW_IDENTITY_AND_DISCOVERY_TARGET_ONLY",
        }
        if source_category == "resources":
            purposes = RESOURCE_PURPOSES[asset_id]
            row["economy_relationships"] = [
                {"purpose": purpose, "status": "DEFERRED_RELATIONSHIP" if purpose in PURPOSE_GATES else "SAFE_NOW_NONNUMERIC_RELATIONSHIP", "blockers": PURPOSE_GATES.get(purpose, [])}
                for purpose in purposes
            ]
        rows.append(row)

    references = [
        {"path": str(AUTHORITY.relative_to(ROOT)), "sha256": sha(AUTHORITY), "role": "exact 50-ID and blocker authority"},
        {"path": str(STATIC.relative_to(ROOT)), "sha256": sha(STATIC), "role": "safe-now static resource/block bindings"},
        {"path": str(LEDGER.relative_to(ROOT)), "sha256": sha(LEDGER), "role": "ratified/deferred decision boundary"},
        {"path": str(CRYSTAL_CODEX.relative_to(ROOT)), "sha256": sha(CRYSTAL_CODEX), "role": "exact existing 204-entry append-only prefix"},
        {"path": str(STATE.relative_to(ROOT)), "sha256": sha(STATE), "role": "schema-v4 SR region and category capacities"},
    ]
    return {
        "schema": "aionbound.wave1.skyreach-economy-codex-scaffold.v1.0.0",
        "status": "SKYREACH_SAFE_NOW_ECONOMY_CODEX_SCAFFOLD_COMPLETE",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE, "g7_immutable": True},
        "scope": "Engineering authority scaffold only; no BP/RP/runtime/ledger/BDS/build mutation.",
        "authority": references,
        "registry": {
            "state_schema_before": 4,
            "state_schema_after": 4,
            "prefix_entries": PREFIX_COUNT,
            "skyreach_entries": len(rows),
            "entries_after": PREFIX_COUNT + len(rows),
            "append_rule": "Keep exact WW/AH/CM prefix ordinals 0-203; append SR ordinals 204-253 with region-local indices.",
            "entries": rows,
        },
        "packet006_relationships": {
            "safe_now_reference_only": {key: value for key, value in PACKET006.items() if key != "sidegrades"},
            "deferred_no_identity_or_page_allocation": {"items": PACKET006["sidegrades"], "blocker": "W1-CREATIVE-005"},
            "rule": "References do not create recipes, acquisition routes, item identities, runtime effects, or completion events.",
        },
        "progression_handoffs": {
            "cm_to_skyreach": {
                "existing_event": "codex:cm:progression:skyreach_rumor:ruined_observatory_visited",
                "skyreach_entry_target": "codex:sr:structure:ancient_sky_arch:recognized_structure_visit",
                "status": "STRUCTURAL_ONLY_NO_NEW_RUNTIME_COMPOSITION",
            },
            "skyreach_to_pilgrimage": {
                "source_relationships": ["aionbound:storm_pinion", "aionbound:aether_stone", "aionbound:observation_tower"],
                "target": "pilgrimage",
                "status": "STRUCTURAL_ONLY_TERMINAL_AND_REWARD_GUARDS_DEFERRED",
                "blockers": ["W1-003-STORM-NEST", "W1-004-SR"],
            },
        },
        "deferred_matrix": [
            {"id": "W1-001-SR", "surface": "nonwarehouse identities and executable acquisition/recipe closure", "disposition": "DEFERRED_FOR_LATER_INTERPRETATION"},
            {"id": "W1-003-STORM-NEST", "surface": "Storm Nest thresholds, timing, reset, multiplayer, persistence, terminal semantics", "disposition": "DEFERRED_FOR_LATER_INTERPRETATION"},
            {"id": "W1-004-SR", "surface": "numeric loot, quantities, chest rolls, seal/recovery/repeat-clear semantics", "disposition": "DEFERRED_FOR_LATER_INTERPRETATION"},
            {"id": "W1-CREATIVE-005", "surface": "five sidegrade identities and representations", "disposition": "DEFERRED_BY_USER"},
        ],
        "guards": {"pack_edits": False, "runtime_edits": False, "new_subscriptions": False, "new_intervals": False, "new_schema": False, "new_numeric_values": False, "new_item_identities": False, "bds": False, "build": False},
    }


def markdown(data: dict) -> str:
    lines = [
        "# Skyreach Economy and Codex Scaffold", "",
        f"Status: `{data['status']}`", "",
        "This is a deterministic engineering authority scaffold. It allocates no pack or runtime behavior.", "",
        "## Safe now", "",
        "- 50 Skyreach Codex identities and exact discovery targets append after the immutable 204-entry WW/AH/CM prefix.",
        "- Packet 006 equipment relationships are reference-only.",
        "- CM to Skyreach and Skyreach to Pilgrimage handoffs are structural only.",
        "- Every safe static resource has a nonnumeric purpose or an explicit deferred relationship.", "",
        "## Deferred", "",
    ]
    for row in data["deferred_matrix"]:
        lines.append(f"- `{row['id']}` — {row['surface']} (`{row['disposition']}`).")
    lines += ["", "No loot probabilities, quantities, recipes, terminal grants, sidegrade identities, shared handlers, BDS run, or build are authorized or claimed.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = build()
    json_text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    md_text = markdown(data)
    if args.check:
        if OUTPUT_JSON.read_text() != json_text or OUTPUT_MD.read_text() != md_text:
            raise SystemExit("stale Skyreach economy/Codex scaffold")
    else:
        OUTPUT_JSON.write_text(json_text)
        OUTPUT_MD.write_text(md_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
