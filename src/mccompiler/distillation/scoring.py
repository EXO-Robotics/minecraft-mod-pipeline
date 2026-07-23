from __future__ import annotations

from typing import Any

from .model import FEASIBILITY_DIMENSIONS, NEGATIVE_DIMENSIONS, POSITIVE_DIMENSIONS, RIGHTS_DIMENSIONS


FEASIBILITY_COST_DIMENSIONS = {
    "asset_production_effort",
    "testing_effort",
    "multiplayer_complexity",
    "persistence_complexity",
    "maintenance_cost",
}


def _dimension(record: dict[str, Any], name: str) -> tuple[int, str, list[str]]:
    raw = record.get(name)
    if not isinstance(raw, dict):
        return 0, "UNKNOWN", [f"{name}: missing evidence"]
    status = raw.get("status")
    value = raw.get("value")
    evidence = raw.get("evidence")
    if status != "KNOWN" or isinstance(value, bool) or not isinstance(value, int):
        reason = str(raw.get("reason") or "unknown evidence")
        return 0, "UNKNOWN", [f"{name}: {reason}"]
    if not 0 <= value <= 100:
        raise ValueError(f"{name}.value must be an integer from 0 through 100")
    if not isinstance(evidence, list) or not evidence:
        return 0, "UNKNOWN", [f"{name}: KNOWN requires non-empty evidence"]
    return value, "KNOWN", []


def score_system(system: dict[str, Any], weights: dict[str, Any]) -> dict[str, Any]:
    dimensions = system.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError(f"System {system.get('id')} dimensions must be an object")
    contributions: dict[str, int] = {}
    normalized: dict[str, dict[str, Any]] = {}
    gaps: list[str] = []
    positive_total = 0
    feasibility_total = 0
    negative_total = 0
    known = 0
    all_names = POSITIVE_DIMENSIONS + FEASIBILITY_DIMENSIONS + RIGHTS_DIMENSIONS + NEGATIVE_DIMENSIONS
    for name in all_names:
        value, status, found_gaps = _dimension(dimensions, name)
        normalized[name] = {"status": status, "value": value}
        gaps.extend(found_gaps)
        if status == "KNOWN":
            known += 1
        if name in RIGHTS_DIMENSIONS:
            contributions[name] = 0
            continue
        group = "positive" if name in POSITIVE_DIMENSIONS else "feasibility" if name in FEASIBILITY_DIMENSIONS else "negative"
        weight = int(weights[group][name])
        weighted_value = 100 - value if name in FEASIBILITY_COST_DIMENSIONS else value
        contribution = weighted_value * weight
        contributions[name] = contribution
        if group == "positive":
            positive_total += contribution
        elif group == "feasibility":
            feasibility_total += contribution
        else:
            negative_total += contribution
    raw = positive_total + feasibility_total - negative_total
    return {
        "system_id": system["id"],
        "raw_score_milli": raw,
        "positive_milli": positive_total,
        "feasibility_milli": feasibility_total,
        "negative_milli": negative_total,
        "confidence_basis_points": known * 10_000 // len(all_names),
        "dimensions": normalized,
        "weighted_contributions": contributions,
        "evidence_gaps": sorted(gaps),
    }
