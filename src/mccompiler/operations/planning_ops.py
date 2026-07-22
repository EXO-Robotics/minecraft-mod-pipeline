from __future__ import annotations

from typing import Any

from mccompiler.overrides import ALLOWED_STRATEGIES
from mccompiler.project.store import ProjectError, ProjectStore


STRATEGY_DESCRIPTIONS = {
    "DIRECT": "Native Bedrock data or stable API equivalent with no known semantic redesign",
    "SCRIPTED_EQUIVALENT": "Stable Script API implementation preserving the mechanic",
    "RECONSTRUCTED": "Different Bedrock implementation intended to preserve behavior",
    "BEHAVIORAL_APPROXIMATION": "Partial gameplay approximation requiring explicit approval",
    "VISUAL_APPROXIMATION": "Presentation-only approximation requiring explicit approval",
    "MANUAL_REDESIGN": "Custom reconstruction work is required",
    "UNSUPPORTED": "No approved implementation is currently available",
}


def _known_target(store: ProjectStore, target: Any) -> str:
    if not isinstance(target, str) or not target:
        raise ProjectError("INVALID_PARAMETERS", "operation requires target")
    ir = store.read("analysis/modir.json", {}) or {}
    known = {row.get("id") for row in ir.get("behaviors", [])} | {row.get("identifier") for row in ir.get("content", [])} | {row.get("id") for row in ir.get("state", [])} | {row.get("id") for row in ir.get("ui_intent", [])} | {row.get("id") for row in ir.get("networking_intent", [])} | {row.get("feature") or row.get("id") for row in ir.get("unsupported_hooks", [])}
    if target not in known:
        raise ProjectError("TARGET_NOT_FOUND", f"Decision target not found: {target}")
    return target


def _provenance(parameters: dict[str, Any]) -> dict[str, Any]:
    value = parameters.get("provenance")
    if not isinstance(value, dict) or not value.get("author") or not value.get("reason"):
        raise ProjectError("INVALID_PROVENANCE", "operation requires provenance.author and provenance.reason")
    return dict(value)


def compare_bedrock_strategies(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    target = _known_target(store, parameters.get("target") or parameters.get("id"))
    selected = next((row for row in store.read("decisions/strategies.yaml", {"strategies": []}).get("strategies", []) if row.get("target") == target), None)
    candidates = [{"strategy": name, "description": STRATEGY_DESCRIPTIONS[name], "requires_approval": name in {"BEHAVIORAL_APPROXIMATION", "VISUAL_APPROXIMATION", "MANUAL_REDESIGN", "UNSUPPORTED"}} for name in sorted(ALLOWED_STRATEGIES)]
    return {"target": target, "selected": selected, "candidates": candidates, "recommendation": None, "recommendation_reason": "Current project artifacts do not prove a single best strategy; AI review is required"}, store, []


def plan_feature(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return compare_bedrock_strategies(store, parameters, expected_revision)


def _record(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None, *, path: str, field: str, decision_type: str, extra: dict[str, Any] | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    target = _known_target(store, parameters.get("target") or parameters.get("id"))
    decision = {"target": target, "decision": decision_type, "provenance": _provenance(parameters), **(extra or {})}
    if parameters.get("recorded_at"):
        decision["recorded_at"] = parameters["recorded_at"]
    document = store.read(path, {"schema_version": "1.0.0", field: []})
    rows = [row for row in document.get(field, []) if not (row.get("target") == target and row.get("decision") == decision_type)]
    rows.append(decision)
    document[field] = sorted(rows, key=lambda row: (str(row.get("target")), str(row.get("decision"))))
    revision = store.commit({path: document}, expected_revision=expected_revision)
    return {"decision": decision, "revision": revision}, store, [{"path": path, "kind": "decision"}]


def accept_approximation(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    preserved, lost = parameters.get("preserved"), parameters.get("lost")
    if not isinstance(preserved, list) or not isinstance(lost, list):
        raise ProjectError("INVALID_PARAMETERS", "accept_approximation requires preserved and lost arrays")
    return _record(store, parameters, expected_revision, path="decisions/approvals.yaml", field="approvals", decision_type="APPROXIMATION_ACCEPTED", extra={"preserved": preserved, "lost": lost})


def reject_approximation(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _record(store, parameters, expected_revision, path="decisions/approvals.yaml", field="approvals", decision_type="APPROXIMATION_REJECTED")


def record_manual_redesign(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    design = parameters.get("design")
    if not isinstance(design, dict) or not design:
        raise ProjectError("INVALID_PARAMETERS", "record_manual_redesign requires a non-empty design object")
    return _record(store, parameters, expected_revision, path="decisions/redesigns.yaml", field="redesigns", decision_type="MANUAL_REDESIGN", extra={"design": design})


def apply_override(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    override = parameters.get("override")
    if not isinstance(override, dict) or not override:
        raise ProjectError("INVALID_PARAMETERS", "apply_override requires override")
    target = _known_target(store, override.get("target") or parameters.get("target"))
    provenance = override.get("provenance") or parameters.get("provenance")
    merged = {**override, "target": target, "provenance": provenance}
    _provenance({"provenance": provenance})
    unknown = sorted(set(merged) - {"target", "provenance", "strategy", "map_identifier", "dependency_resolution", "state_storage", "behavior_patch", "omit"})
    if unknown:
        raise ProjectError("INVALID_OVERRIDE", f"Unsupported override fields: {', '.join(unknown)}")
    if merged.get("strategy") is not None and merged["strategy"] not in ALLOWED_STRATEGIES:
        raise ProjectError("INVALID_STRATEGY", f"Unsupported strategy: {merged['strategy']}")
    document = store.read("decisions/overrides.yaml", {"schema_version": "1.0.0", "overrides": []})
    rows = [row for row in document.get("overrides", []) if row.get("target") != target]
    rows.append(merged)
    document["overrides"] = sorted(rows, key=lambda row: str(row.get("target")))
    revision = store.commit({"decisions/overrides.yaml": document}, expected_revision=expected_revision)
    return {"override": merged, "revision": revision}, store, [{"path": "decisions/overrides.yaml", "kind": "decision"}]


def set_strategy(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    target, strategy, provenance = parameters.get("target"), parameters.get("strategy"), parameters.get("provenance")
    if not isinstance(target, str) or not target:
        raise ProjectError("INVALID_PARAMETERS", "set_strategy requires target")
    if strategy not in ALLOWED_STRATEGIES:
        raise ProjectError("INVALID_STRATEGY", f"Unsupported strategy: {strategy}")
    if not isinstance(provenance, dict) or not provenance.get("author") or not provenance.get("reason"):
        raise ProjectError("INVALID_PROVENANCE", "set_strategy requires provenance.author and provenance.reason")
    behaviors = store.read("ir/behaviors.json", {"behaviors": []}).get("behaviors", [])
    content = store.read("ir/content.json", {"content": []}).get("content", [])
    unsupported = (store.read("analysis/modir.json", {}) or {}).get("unsupported_hooks", [])
    known = {row.get("id") for row in behaviors} | {row.get("identifier") for row in content} | {row.get("feature") or row.get("id") for row in unsupported}
    if target not in known:
        raise ProjectError("TARGET_NOT_FOUND", f"Strategy target not found: {target}")
    document = store.read("decisions/strategies.yaml", {"schema_version": "1.0.0", "strategies": []})
    decision = {"target": target, "strategy": strategy, "provenance": dict(provenance)}
    if parameters.get("recorded_at"):
        decision["recorded_at"] = parameters["recorded_at"]
    rows = [row for row in document.get("strategies", []) if row.get("target") != target]
    rows.append(decision)
    document["strategies"] = sorted(rows, key=lambda row: str(row.get("target")))
    revision = store.commit({"decisions/strategies.yaml": document}, expected_revision=expected_revision)
    return {"decision": decision, "revision": revision}, store, [{"path": "decisions/strategies.yaml", "kind": "decision"}]
