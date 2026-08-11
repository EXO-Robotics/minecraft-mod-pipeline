#!/usr/bin/env python3
"""Generate the append-only Crystal Marsh Codex registry module."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "engineering/crystal-marsh-intake/codex/CRYSTAL_CODEX_PROGRESSION_INTAKE_MAP.json"
OUTPUT = ROOT / "behavior_pack/scripts/wave1_codex_crystal_data.js"


def transition(row: dict) -> dict:
    return {
        "id": row["id"],
        "state": 1 if row["stage"] == "partial" else 2,
        "event": row["action"],
    }


def authority_text(row: dict) -> dict:
    safe = row.get("relationships", {}).get("SAFE_NOW", {})
    result = {
        "where_to_find": safe.get("where_or_acquisition_source", []),
        "crafting_and_progression": sorted(set(
            safe.get("nonnumeric_crafting_roles", []) + safe.get("progression_links", [])
        )),
        "equipment_links": safe.get("equipment_links", []),
    }
    return result


def packet_entry(row: dict) -> dict:
    source_category = row["source_category"]
    kind = "block" if source_category == "blocks" else row["codex_category"]
    return {
        "id": row["id"],
        "warehouseId": row["warehouse_id"],
        "runtimeId": row["runtime_id"],
        "region": "cm",
        "kind": kind,
        "category": row["codex_category"],
        "categoryIndex": row["category_index"],
        "events": [transition(event) for event in row["discovery_routes"]],
        "authorityText": authority_text(row),
    }


def equipment_entry(row: dict) -> dict:
    return {
        "id": row["id"],
        "warehouseId": row["id"],
        "runtimeId": row["runtime_id"],
        "region": "cm",
        "kind": "equipment",
        "category": "equipment",
        "categoryIndex": row["category_index"],
        "events": [transition(event) for event in row["discovery_routes"]],
        "authorityText": {
            "where_to_find": row["provenance"],
            "crafting_and_progression": [row["role"], row["recipe_boundary"]["source_formula"]],
            "equipment_links": [row["id"]],
        },
    }


def boss_entry(row: dict) -> dict:
    return {
        "id": row["id"],
        "warehouseId": "marsh_wight",
        "runtimeId": row["runtime_id"],
        "region": "cm",
        "kind": "boss",
        "category": "boss",
        "categoryIndex": row["category_index"],
        "events": [transition(event) for event in row["discovery_routes"]],
        "authorityText": {
            "where_to_find": row["arena_identity"],
            "phases": row["phase_names"],
            "attacks": row["attack_names"],
            "chapter_reward": "Marsh Wight Mask — Pearl Depths apex only",
        },
    }


def progression_entry(row: dict) -> dict:
    source = row.get("source_hint", "Crystal Marsh living-world discovery")
    reward = row.get("seal_identity", "Codex-only Skyreach rumor; no physical chart")
    return {
        "id": row["id"],
        "warehouseId": row["id"],
        "runtimeId": row["runtime_id"],
        "region": "cm",
        "kind": "progression",
        "category": "progression",
        "categoryIndex": row["category_index"],
        "events": [transition(event) for event in row["events"]],
        "authorityText": {
            "where_to_find": source,
            "crafting_and_progression": reward,
            "equipment_links": [],
        },
    }


def render() -> str:
    source = json.loads(SOURCE.read_text())
    entries = [packet_entry(row) for row in source["packet003_entries"]]
    entries.extend(equipment_entry(row) for row in source["packet006_direct_equipment_pages"])
    entries.append(boss_entry(source["pearl_depths"]))
    entries.extend(progression_entry(row) for row in source["progression_pages"])
    assert len(entries) == 64
    for ordinal, row in enumerate(entries, 140):
        expected = next(
            item["global_append_ordinal"]
            for item in (
                source["packet003_entries"]
                + source["packet006_direct_equipment_pages"]
                + [source["pearl_depths"]]
                + source["progression_pages"]
            )
            if item["id"] == row["id"]
        )
        assert ordinal == expected, (row["id"], ordinal, expected)
    payload = json.dumps(entries, indent=2, ensure_ascii=False)
    return (
        "// Generated from CRYSTAL_CODEX_PROGRESSION_INTAKE_MAP.json.\n"
        "// W1-001-CM, W1-003-PEARL-DEPTHS, and W1-004-CM are ratified;\n"
        "// the exact WW/AH prefix remains untouched and state schema stays v4.\n"
        f"export const CRYSTAL_CODEX_ENTRIES = Object.freeze({payload});\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != expected:
            raise SystemExit(f"stale generated file: {OUTPUT}")
    else:
        OUTPUT.write_text(expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
