from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_json


def match_patterns(ir: dict[str, Any]) -> list[dict[str, Any]]:
    database = read_json(Path(__file__).with_name("patterns.json")) or {"patterns": []}
    triggers = {b.get("trigger", {}).get("type") for b in ir.get("behaviors", [])}
    actions = {a.get("type") for b in ir.get("behaviors", []) for a in b.get("actions", [])}
    matches = []
    for pattern in database["patterns"]:
        required = pattern.get("requires", {})
        wanted_triggers, wanted_actions = set(required.get("triggers", [])), set(required.get("actions", []))
        if wanted_triggers <= triggers and wanted_actions <= actions:
            matches.append({"id": pattern["id"], "classification": pattern["classification"], "matched": {"triggers": sorted(wanted_triggers), "actions": sorted(wanted_actions)}, "version": database["schema_version"]})
    return matches
