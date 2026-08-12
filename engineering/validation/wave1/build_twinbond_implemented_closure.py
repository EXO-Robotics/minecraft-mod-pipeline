#!/usr/bin/env python3
"""Build exact source-hash closure for the ratified Twinbond finale slice."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGET = Path(__file__).with_name("WAVE_1_TWINBOND_IMPLEMENTED_CLOSURE.json")


def rows(paths: list[str]) -> list[dict[str, str]]:
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate source path")
    result = []
    for relative in paths:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        result.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return result


def build() -> dict:
    authority = [
        "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
        "engineering/authority/support-proposals/finale/W1-002-TWINBOND.json",
        "engineering/authority/support-proposals/finale/W1-003-TWINBOND.json",
        "engineering/authority/support-proposals/finale/W1-004-TWINBOND.json",
        "engineering/final-reconciliation/FINAL_WAVE1_RATIFICATION_RECEIPT.json",
    ]
    product = [
        "behavior_pack/scripts/twinbond.js", "behavior_pack/scripts/runtime.js", "behavior_pack/scripts/state.js", "behavior_pack/scripts/catalog.js",
        "behavior_pack/items/memory_of_four_lands.item.json", "behavior_pack/items/trophy_edge_blank.item.json",
        "behavior_pack/blocks/ceremony_anvil_site.block.json", "behavior_pack/blocks/twin_thrones.block.json",
        "behavior_pack/blocks/twinbond_approach_marker.block.json", "behavior_pack/blocks/twinbond_obsidian_ring.block.json",
        "behavior_pack/features/twinbond_approach_marker.feature.json",
        "behavior_pack/feature_rules/twinbond_approach_marker.feature_rule.json",
        "behavior_pack/structures/aionbound/twinbond_slice_v1.mcstructure",
        "tests/wave1_twinbond.test.mjs",
    ]
    presentation = [
        "resource_pack/blocks.json", "resource_pack/texts/en_US.lang", "resource_pack/textures/item_texture.json", "resource_pack/textures/terrain_texture.json",
    ]
    presentation += [f"resource_pack/models/aionbound/{value}.geo.json" for value in ["ceremony_anvil_site", "twin_thrones", "twinbond_approach_marker", "twinbond_obsidian_ring"]]
    presentation += [f"resource_pack/animations/aionbound/{value}.animation.json" for value in ["ceremony_anvil_site", "twin_thrones", "twinbond_approach_marker", "twinbond_obsidian_ring"]]
    native = ["engineering/native-assets/twinbond/TWINBOND_NATIVE_REPORT.json"]
    groups = {
        "ratified_authority": rows(authority),
        "finale_existing_handler_persistence_and_recovery": rows(product),
        "site_and_inventory_presentation": rows(presentation),
        "native_editable_asset_aggregate": rows(native),
    }
    all_paths = [row["path"] for group in groups.values() for row in group]
    if len(all_paths) != len(set(all_paths)):
        raise ValueError("duplicate path across groups")
    return {
        "schema": "aionbound.wave1.twinbond.implemented_source_closure.v1",
        "status": "TWINBOND_SOURCE_SEMANTICS_COMPLETE_PHASE_PRESENTATION_QUALIFICATION_DEFERRED",
        "groups": groups,
        "invariants": {
            "persistence_schema": 4,
            "new_global_subscription_classes": 0,
            "new_recurring_interval_classes": 0,
            "four_seal_gate": True,
            "full_pilgrimage_gate": True,
            "forbidden_finale_ignition_key_path": False,
            "forbidden_concord_scale_path": False,
            "once_per_player_recovery": True,
        },
        "pending_follow_up": {
            "wyrm_phase_presentation": "NATIVE_REPORT_PHASE_READY_FALSE_REQUIRES_SEPARATE_QUALIFIED_REPAIR_OR_EXPLICIT_SUFFICIENCY_DECISION",
            "runtime_qualification": "DEFERRED_TO_FINAL_INTEGRATED_GATE",
            "W1-CREATIVE-005": "DEFERRED_BY_USER_NO_SIDEGRADE_IDENTITIES",
        },
        "proof_boundary": "EXACT SOURCE PATH AND HASH CLOSURE WITH TARGETED LOCAL SEMANTIC TESTS ONLY; NO PACKAGE, BDS, CLIENT, MULTIPLAYER, CONSOLE, MARKETPLACE, OR RELEASE CLAIM",
    }


def main() -> None:
    TARGET.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
