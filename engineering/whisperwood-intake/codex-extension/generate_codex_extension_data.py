#!/usr/bin/env python3
"""Generate the Bedrock-safe Whisperwood Codex extension data module."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).with_name("WHISPERWOOD_CODEX_EXTENSION_MAP.json")
TARGET = ROOT / "behavior_pack" / "scripts" / "wave1_codex_extension_data.js"


def compact_entry(entry: dict) -> dict:
    return {
        "id": entry["id"],
        "runtimeId": entry["runtime_id"],
        "region": entry["region"],
        "kind": entry["kind"],
        "category": entry["codex_category"],
        "categoryIndex": entry["category_index"],
        "importance": entry["importance"],
        "authorityText": entry["authority_text"],
        "events": [
            {
                "id": event["id"],
                "state": 1 if event["stage"] == "partial" else 2,
                "action": event["action"],
            }
            for event in entry["discovery_events"]
        ],
        **({"equipmentSubtype": entry["equipment_subtype"]} if "equipment_subtype" in entry else {}),
        **({"optionalMastery": entry["optional_mastery"]} if "optional_mastery" in entry else {}),
        **({"chapterSealIdentity": entry["chapter_seal_identity"]} if "chapter_seal_identity" in entry else {}),
    }


def render(source: dict) -> str:
    ordered = []
    for category in ("structures", "equipment", "bosses", "progression"):
        ordered.extend(compact_entry(entry) for entry in source["entries"][category])
    payload = json.dumps(ordered, indent=2, ensure_ascii=False)
    return (
        "// Generated from WHISPERWOOD_CODEX_EXTENSION_MAP.json. Do not hand edit.\n"
        "// Authority text is copied byte-for-byte at the string level; runtime code\n"
        "// may label fields but must not synthesize replacement lore.\n"
        f"const rows = {payload};\n\n"
        "const freezeEntry = entry => Object.freeze({\n"
        "  ...entry,\n"
        "  authorityText: Object.freeze({ ...entry.authorityText }),\n"
        "  events: Object.freeze(entry.events.map(event => Object.freeze(event))),\n"
        "});\n\n"
        "export const WHISPERWOOD_CODEX_EXTENSION_ENTRIES = Object.freeze(rows.map(freezeEntry));\n"
    )


def main() -> None:
    source = json.loads(SOURCE.read_text())
    TARGET.write_text(render(source))


if __name__ == "__main__":
    main()
