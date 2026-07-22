from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib

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
        for module in item.get("custom_script_modules", []):
            if not isinstance(module, dict) or not module.get("destination") or not isinstance(module.get("source"), str):
                raise ValueError("Custom script modules need destination and inline source")
            if not str(module["destination"]).startswith("scripts/custom/") or ".." in Path(str(module["destination"])).parts:
                raise ValueError("Custom script module destination must stay under scripts/custom")
            digest = hashlib.sha256(module["source"].encode()).hexdigest()
            if module.get("sha256") != digest:
                raise ValueError("Custom script module sha256 does not match inline source")
    return data


def apply_overrides(ir: dict[str, Any], document: dict[str, Any]) -> None:
    index = {b.get("id"): b for b in ir.get("behaviors", [])}
    for override in document.get("overrides", []):
        target = override["target"]
        mapped = override.get("map_identifier")
        if mapped:
            for content in ir.get("content", []):
                if content.get("identifier") == target:
                    content["identifier"] = mapped
                    content.setdefault("override_provenance", []).append(override["provenance"])
            for behavior_row in ir.get("behaviors", []):
                if behavior_row.get("owner", {}).get("identifier") == target:
                    behavior_row["owner"]["identifier"] = mapped
                for action in behavior_row.get("actions", []):
                    for field in ("entity", "item", "block", "structure", "behavior"):
                        if action.get(field) == target:
                            action[field] = mapped
            target = mapped
        resolution = override.get("dependency_resolution")
        if isinstance(resolution, dict):
            for dependency in ir.get("dependencies", []):
                if dependency.get("to") == override["target"] or dependency.get("id") == override["target"]:
                    dependency.update(resolution)
        if override.get("state_storage"):
            for state in ir.get("state", []):
                if state.get("id") == override["target"]:
                    state["storage_strategy"] = override["state_storage"]
        behavior = index.get(target)
        if behavior and isinstance(override.get("behavior_patch"), dict):
            for key in ("trigger", "conditions", "actions", "stateReads", "stateWrites", "feedback", "presentationRequirements"):
                if key in override["behavior_patch"]:
                    behavior[key] = override["behavior_patch"][key]
            behavior.setdefault("override_provenance", []).append(override["provenance"])
        applied = dict(override)
        applied["target"] = target
        if applied.get("omit"):
            applied["strategy"] = "UNSUPPORTED"
        ir.setdefault("applied_overrides", []).append(applied)
