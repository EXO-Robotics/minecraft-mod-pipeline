from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_json


ALLOWED_STRATEGIES = {"DIRECT", "SCRIPTED_EQUIVALENT", "RECONSTRUCTED", "BEHAVIORAL_APPROXIMATION", "VISUAL_APPROXIMATION", "MANUAL_REDESIGN", "UNSUPPORTED"}


def load_overrides(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {"schema_version": "1.0.0", "overrides": []}
    data = read_json(Path(path).expanduser().resolve())
    if not isinstance(data, dict) or data.get("schema_version") != "1.0.0" or not isinstance(data.get("overrides"), list):
        raise ValueError("Override document must match override schema 1.0.0")
    for item in data["overrides"]:
        if not isinstance(item, dict) or not item.get("target") or not item.get("provenance"):
            raise ValueError("Each override needs target and provenance")
        if item.get("strategy") and item["strategy"] not in ALLOWED_STRATEGIES:
            raise ValueError(f"Invalid override strategy: {item['strategy']}")
    return data


def apply_overrides(ir: dict[str, Any], document: dict[str, Any]) -> None:
    index = {b.get("id"): b for b in ir.get("behaviors", [])}
    for override in document.get("overrides", []):
        target = override["target"]
        behavior = index.get(target)
        if behavior and isinstance(override.get("behavior_patch"), dict):
            for key in ("trigger", "conditions", "actions", "stateReads", "stateWrites", "feedback", "presentationRequirements"):
                if key in override["behavior_patch"]:
                    behavior[key] = override["behavior_patch"][key]
            behavior.setdefault("override_provenance", []).append(override["provenance"])
        ir.setdefault("applied_overrides", []).append(override)

