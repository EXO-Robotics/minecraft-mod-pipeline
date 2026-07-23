from __future__ import annotations

from itertools import combinations
from typing import Any

from .model import CORE_CATEGORIES, DEFAULT_PROGRESSION_STAGES, RIGHTS_DIMENSIONS


def prerequisite_closure(ids: set[str], systems: dict[str, dict[str, Any]]) -> set[str]:
    result = set(ids)
    pending = list(sorted(ids))
    while pending:
        identifier = pending.pop()
        for required in systems[identifier].get("prerequisites", []):
            if required not in systems:
                raise ValueError(f"Dangling prerequisite {required!r} from {identifier!r}")
            if required not in result:
                result.add(required)
                pending.append(required)
    return result


def _rights_clear(system: dict[str, Any]) -> bool:
    dimensions = system["dimensions"]
    return all(
        isinstance(dimensions.get(name), dict)
        and dimensions[name].get("status") == "KNOWN"
        and dimensions[name].get("value") == (0 if name == "branding_trademark_risk" else 100)
        for name in RIGHTS_DIMENSIONS
    )


def classify_strategy(system: dict[str, Any]) -> tuple[str, list[str]]:
    requested = str(system.get("strategy", "DIRECT_RECONSTRUCTION"))
    reasons: list[str] = []
    stable_api = system.get("stable_api_status", "UNKNOWN")
    if stable_api == "UNSUPPORTED":
        return "UNSUPPORTED", ["system relies on APIs unavailable to MARKETPLACE_ADDON_STABLE"]
    if stable_api != "COMPATIBLE":
        return "DEFER", ["Marketplace-stable API compatibility is unknown"]
    if bool(system.get("unsupported")):
        return "UNSUPPORTED", ["unsupported Bedrock/engine reliance"]
    original_evidence = system.get("originality_evidence")
    original_content = system.get("original_content") is True and isinstance(original_evidence, list) and bool(original_evidence)
    if requested == "ORIGINAL_REPLACEMENT":
        if original_content:
            return requested, ["original replacement supported by explicit originality evidence; human Marketplace review remains required"]
        return "RIGHTS_BLOCKED", ["original replacement requires explicit original_content and originality_evidence"]
    if requested in {"DIRECT_RECONSTRUCTION", "BEDROCK_NATIVE_REDESIGN"} and not _rights_clear(system):
        if requested == "BEDROCK_NATIVE_REDESIGN" and original_content:
            return requested, ["original Bedrock-native system supported by explicit originality evidence; human Marketplace review remains required"]
        if bool(system.get("original_replacement_available")) and original_content:
            return "ORIGINAL_REPLACEMENT", ["direct reconstruction rights are not fully clear; original replacement required"]
        return "RIGHTS_BLOCKED", [f"{requested.lower()} rights are not fully clear"]
    return requested, reasons


def _candidate(
    selected: set[str],
    systems: dict[str, dict[str, Any]],
    scores: dict[str, dict[str, Any]],
    effort_limit: int,
    console_limit: int,
) -> dict[str, Any] | None:
    closed = prerequisite_closure(selected, systems)
    rows = [systems[key] for key in sorted(closed)]
    strategies = {row["id"]: classify_strategy(row)[0] for row in rows}
    if any(value in {"RIGHTS_BLOCKED", "UNSUPPORTED", "DEFER"} for value in strategies.values()):
        return None
    effort = sum(int(row["effort_units"]) for row in rows)
    console = sum(int(row["console_cost_units"]) for row in rows)
    if effort > effort_limit or console > console_limit:
        return None
    value = sum(int(scores[row["id"]]["raw_score_milli"]) for row in rows)
    stages = sorted({stage for row in rows for stage in row.get("progression_stages", [])})
    categories = sorted({category for row in rows for category in row.get("categories", [])})
    return {
        "ids": sorted(closed),
        "effort_units": effort,
        "console_cost_units": console,
        "value_milli": value,
        "stages": stages,
        "categories": categories,
        "strategies": strategies,
    }


def _large_candidate_search(
    feasible_ids: list[str],
    systems: dict[str, dict[str, Any]],
    scores: dict[str, dict[str, Any]],
    effort_limit: int,
    console_limit: int,
    required_stages: list[str],
) -> dict[tuple[str, ...], dict[str, Any]]:
    stage_bits = {stage: 1 << index for index, stage in enumerate(required_stages)}
    category_bits = {category: 1 << index for index, category in enumerate(CORE_CATEGORIES)}
    empty = _candidate(set(), systems, scores, effort_limit, console_limit) or {
        "ids": [], "effort_units": 0, "console_cost_units": 0, "value_milli": 0,
        "stages": [], "categories": [], "strategies": {},
    }
    states: dict[tuple[str, ...], dict[str, Any]] = {(): empty}
    for identifier in feasible_ids:
        additions: dict[tuple[str, ...], dict[str, Any]] = {}
        for row in list(states.values()):
            attempt = _candidate(set(row["ids"]) | {identifier}, systems, scores, effort_limit, console_limit)
            if attempt is not None:
                additions[tuple(attempt["ids"])] = attempt
        states.update(additions)
        best_by_signature: dict[tuple[int, int, int, int], dict[str, Any]] = {}
        for row in states.values():
            stage_mask = sum(stage_bits.get(stage, 0) for stage in set(row["stages"]))
            category_mask = sum(category_bits.get(category, 0) for category in set(row["categories"]))
            signature = (int(row["effort_units"]), int(row["console_cost_units"]), stage_mask, category_mask)
            incumbent = best_by_signature.get(signature)
            if incumbent is None or (int(row["value_milli"]), tuple(row["ids"])) > (int(incumbent["value_milli"]), tuple(incumbent["ids"])):
                best_by_signature[signature] = row
        ranked = sorted(
            best_by_signature.values(),
            key=lambda row: (
                -len(set(required_stages).intersection(row["stages"])),
                -len(set(CORE_CATEGORIES).intersection(row["categories"])),
                -int(row["value_milli"]),
                int(row["effort_units"]),
                int(row["console_cost_units"]),
                tuple(row["ids"]),
            ),
        )
        states = {tuple(row["ids"]): row for row in ranked[:50_000]}
    return states


def _progression_transitions(
    selected_ids: set[str],
    systems: dict[str, dict[str, Any]],
    required_stages: list[str],
) -> list[str]:
    missing: list[str] = []
    for previous, current in zip(required_stages, required_stages[1:]):
        current_systems = [
            identifier for identifier in selected_ids
            if current in systems[identifier].get("progression_stages", [])
        ]
        connected = False
        for identifier in current_systems:
            ancestors = prerequisite_closure({identifier}, systems)
            if any(
                previous in systems[ancestor].get("progression_stages", [])
                for ancestor in ancestors
            ):
                connected = True
                break
        if not connected:
            missing.append(f"{previous}->{current}")
    return missing


def select_scope(
    systems_list: list[dict[str, Any]],
    score_rows: list[dict[str, Any]],
    effort_budget_basis_points: int,
    console_limit: int,
    required_stages: list[str] | None = None,
) -> dict[str, Any]:
    systems = {str(row["id"]): row for row in systems_list}
    if len(systems) != len(systems_list):
        raise ValueError("System ids must be unique")
    scores = {str(row["system_id"]): row for row in score_rows}
    full_effort = sum(int(row["effort_units"]) for row in systems_list)
    effort_limit = full_effort * effort_budget_basis_points // 10_000
    feasible_ids = [
        key for key in sorted(systems)
        if classify_strategy(systems[key])[0] not in {"RIGHTS_BLOCKED", "UNSUPPORTED", "DEFER"}
    ]
    candidates: dict[tuple[str, ...], dict[str, Any]] = {}
    if len(feasible_ids) <= 20:
        for count in range(len(feasible_ids) + 1):
            for subset in combinations(feasible_ids, count):
                candidate = _candidate(set(subset), systems, scores, effort_limit, console_limit)
                if candidate is not None:
                    candidates[tuple(candidate["ids"])] = candidate
    stages_required = list(required_stages or DEFAULT_PROGRESSION_STAGES)
    if len(feasible_ids) > 20:
        candidates = _large_candidate_search(feasible_ids, systems, scores, effort_limit, console_limit, stages_required)
    candidate_rows = list(candidates.values())
    frontier = [
        row for row in candidate_rows
        if not any(
            other is not row
            and int(other["effort_units"]) <= int(row["effort_units"])
            and int(other["console_cost_units"]) <= int(row["console_cost_units"])
            and int(other["value_milli"]) >= int(row["value_milli"])
            and len(set(stages_required).intersection(other["stages"])) >= len(set(stages_required).intersection(row["stages"]))
            and len(set(CORE_CATEGORIES).intersection(other["categories"])) >= len(set(CORE_CATEGORIES).intersection(row["categories"]))
            and (
                int(other["effort_units"]) < int(row["effort_units"])
                or int(other["console_cost_units"]) < int(row["console_cost_units"])
                or int(other["value_milli"]) > int(row["value_milli"])
                or len(set(stages_required).intersection(other["stages"])) > len(set(stages_required).intersection(row["stages"]))
                or len(set(CORE_CATEGORIES).intersection(other["categories"])) > len(set(CORE_CATEGORIES).intersection(row["categories"]))
            )
            for other in candidate_rows
        )
    ]
    for row in frontier:
        row["missing_progression_transitions"] = _progression_transitions(set(row["ids"]), systems, stages_required)
    complete = [
        row for row in frontier
        if set(stages_required).issubset(row["stages"]) and not row["missing_progression_transitions"]
    ]
    pool = complete or frontier
    chosen = sorted(
        pool,
        key=lambda row: (
            -int(row["value_milli"]),
            -len(set(stages_required).intersection(row["stages"])),
            -len(set(CORE_CATEGORIES).intersection(row["categories"])),
            int(row["effort_units"]),
            tuple(row["ids"]),
        ),
    )[0]
    chosen.setdefault("missing_progression_transitions", _progression_transitions(set(chosen["ids"]), systems, stages_required))
    chosen["progression_complete"] = set(stages_required).issubset(chosen["stages"]) and not chosen["missing_progression_transitions"]
    chosen["missing_progression_stages"] = sorted(set(stages_required) - set(chosen["stages"]))
    chosen["missing_core_categories"] = sorted(set(CORE_CATEGORIES) - set(chosen["categories"]))
    chosen["effort_limit_units"] = effort_limit
    chosen["full_effort_units"] = full_effort
    chosen["effort_budget_basis_points"] = effort_budget_basis_points
    chosen["evaluated_candidate_count"] = len(candidates)
    chosen["pareto_candidate_count"] = len(frontier)
    return chosen
