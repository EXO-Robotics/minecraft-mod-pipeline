from __future__ import annotations

import re
from typing import Any

from .model import FEASIBILITY_DIMENSIONS, NEGATIVE_DIMENSIONS, POSITIVE_DIMENSIONS, RIGHTS_DIMENSIONS


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown"


def _unknown_dimensions() -> dict[str, dict[str, Any]]:
    names = POSITIVE_DIMENSIONS + FEASIBILITY_DIMENSIONS + RIGHTS_DIMENSIONS + NEGATIVE_DIMENSIONS
    return {
        name: {"status": "UNKNOWN", "reason": "Automated scan cannot make this qualitative judgment"}
        for name in names
    }


def distillation_input_from_modir(ir: dict[str, Any]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in ir.get("content", []):
        if isinstance(row, dict):
            key = f"content-{_slug(str(row.get('kind', 'unknown')))}"
            groups.setdefault(key, []).append(row)
    for row in ir.get("behaviors", []):
        if isinstance(row, dict):
            key = f"behavior-{_slug(str(row.get('trigger', 'unknown')))}"
            groups.setdefault(key, []).append(row)
    for row in ir.get("unsupported_hooks", []):
        if isinstance(row, dict):
            groups.setdefault("unsupported-hooks", []).append(row)
    systems: list[dict[str, Any]] = []
    for identifier in sorted(groups):
        rows = groups[identifier]
        feature_ids = sorted(
            {
                str(row.get("id") or row.get("identifier") or row.get("feature") or f"{identifier}-{index}")
                for index, row in enumerate(rows, start=1)
            }
        )
        unsupported = identifier == "unsupported-hooks"
        evidence_count = sum(len(row.get("evidence", [])) for row in rows)
        dimensions = _unknown_dimensions()
        if evidence_count:
            dimensions["java_evidence_confidence"] = {
                "status": "KNOWN",
                "value": min(100, 40 + evidence_count * 5),
                "evidence": [f"{evidence_count} source evidence records retained by ModIR"],
            }
        systems.append({
            "id": identifier,
            "name": identifier.replace("-", " ").title(),
            "effort_units": max(1, len(rows)),
            "console_cost_units": max(1, len(rows)),
            "strategy": "UNSUPPORTED" if unsupported else "DIRECT_RECONSTRUCTION",
            "stable_api_status": "UNSUPPORTED" if unsupported else "UNKNOWN",
            "unsupported": unsupported,
            "prerequisites": [],
            "unlocks": [],
            "categories": [],
            "progression_stages": [],
            "feature_ids": feature_ids,
            "patterns": [],
            "encounter": "Unknown until player-facing inventory review.",
            "reward": "Unknown until player-facing inventory review.",
            "unlock": "Unknown until progression review.",
            "future_support": "Unknown until system clustering review.",
            "removable_without_breaking_progression": True,
            "dimensions": dimensions,
        })
    if not systems:
        systems.append({
            "id": "empty-scan",
            "name": "Empty Scan",
            "effort_units": 1,
            "console_cost_units": 1,
            "strategy": "DEFER",
            "stable_api_status": "UNKNOWN",
            "prerequisites": [],
            "unlocks": [],
            "categories": [],
            "progression_stages": [],
            "feature_ids": [],
            "patterns": [],
            "encounter": "No player-facing content was identified.",
            "reward": "None identified.",
            "unlock": "None identified.",
            "future_support": "Requires additional source or metadata.",
            "removable_without_breaking_progression": True,
            "dimensions": _unknown_dimensions(),
        })
    metadata = ir.get("metadata", {})
    input_record = ir.get("input", {})
    return {
        "schema_version": "1.0.0",
        "analysis_status": "PRELIMINARY_EVIDENCE_GAPS",
        "identity": {
            "summary": "Automated source/metadata inventory only; player-facing identity requires attributable qualitative review.",
            "load_bearing_systems": [],
        },
        "console_limit_units": 100,
        "evidence_gaps": [
            "Player-facing identity and system boundaries require review.",
            "Progression encounters, rewards, unlocks, and stages require review.",
            "Conversion, art, test, console, multiplayer, persistence, maintenance, and rights evidence require review.",
        ],
        "required_inputs": [
            "Attributable player-facing inventory and progression review.",
            "Component-level rights and Marketplace review.",
            "Feature-level effort and console-performance estimates.",
        ],
        "scan_provenance": {
            "input": input_record,
            "metadata": metadata,
            "dependency_graph": ir.get("dependency_graph", {"nodes": [], "edges": []}),
            "mod_count": len(ir.get("mods", [])),
            "content_count": len(ir.get("content", [])),
            "behavior_count": len(ir.get("behaviors", [])),
        },
        "systems": systems,
    }
