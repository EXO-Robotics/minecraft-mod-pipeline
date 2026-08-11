#!/usr/bin/env python3
"""Generate append-only Ashen Codex registry data from the bound intake map."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "engineering/ashen-intake/codex/ASHEN_CODEX_PROGRESSION_INTAKE_MAP.json"
TARGET = ROOT / "behavior_pack/scripts/wave1_codex_ashen_data.js"


def event_rows(rows: list[dict]) -> list[dict]:
    return [{"id": row["id"], "state": 1 if row["stage"] == "partial" else 2, "event": row["action"]} for row in rows]


def packet_entry(row: dict) -> dict:
    safe = row["relationships"]["safe_now"]
    kind = "block" if row["source_category"] == "blocks" else row["codex_category"]
    return {
        "id": row["id"], "warehouseId": row["warehouse_id"], "runtimeId": row["runtime_id"],
        "region": "ah", "kind": kind, "category": row["codex_category"],
        "categoryIndex": row["category_index"], "events": event_rows(row["discovery_routes"]),
        "authorityText": {
            "where_to_find": safe["acquisition"],
            "crafting_and_progression": safe["crafting_and_progression_links"],
            "equipment_links": safe["equipment_links"],
        },
    }


def build() -> list[dict]:
    source = json.loads(SOURCE.read_text())
    rows = [packet_entry(row) for row in source["packet_002_entries"]]
    for row in source["packet_006_ashen_links"]:
        if not row["append_new_entry"]:
            continue
        rows.append({
            "id": row["id"], "warehouseId": row["id"], "runtimeId": row["runtime_id"],
            "region": "ah", "kind": "equipment", "category": "equipment",
            "categoryIndex": row["category_index"], "events": event_rows(row["discovery_routes"]),
            "authorityText": {"role": row["equipment_subtype"], "provenance": "Ashen Highlands"},
        })
    boss = source["kiln_sky"]
    rows.append({
        "id": boss["id"], "warehouseId": boss["id"], "runtimeId": boss["runtime_id"],
        "region": "ah", "kind": "boss", "category": "boss", "categoryIndex": boss["category_index"],
        "events": event_rows(boss["events"]),
        "authorityText": {"phases": boss["phase_names"], "attacks": boss["attack_names"],
                          "chapter_seal": boss["seal_runtime_id"],
                          "optional_mastery_reward": boss["secondary_trophy_runtime_id"]},
    })
    for contract in source["transition_contract"].values():
        if "events" not in contract:
            continue
        rows.append({
            "id": contract["id"], "warehouseId": contract["id"], "runtimeId": contract["runtime_id"],
            "region": "ah", "kind": "progression", "category": "progression",
            "categoryIndex": contract["category_index"], "events": event_rows(contract["events"]),
            "authorityText": {"soft_gate": True, "next_region": "Crystal Marsh" if "crystal" in contract["id"] else "Complete Kiln Sky for the Ashen chapter seal."},
        })
    return rows


def main() -> None:
    rows = build()
    text = "// Generated from ASHEN_CODEX_PROGRESSION_INTAKE_MAP.json.\n"
    text += "// Append-only region-local category indices; schema v4 is unchanged.\n"
    text += "export const ASHEN_CODEX_ENTRIES = Object.freeze(" + json.dumps(rows, indent=2, ensure_ascii=False) + ");\n"
    TARGET.write_text(text)


if __name__ == "__main__":
    main()
