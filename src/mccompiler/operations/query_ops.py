from __future__ import annotations

from typing import Any

from mccompiler.pattern_catalog import marketplace_patterns
from mccompiler.project.store import ProjectStore
from mccompiler.quality import validate_quality_record

from .envelope import OperationError


def _calls(store: ProjectStore) -> list[dict[str, Any]]:
    document = store.read("analysis/source-index/calls.json", {"calls": []})
    calls = document.get("calls", []) if isinstance(document, dict) else []
    return [row for row in calls if isinstance(row, dict)]


def _trace(store: ProjectStore, parameters: dict[str, Any], direction: str) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    symbol = parameters.get("symbol")
    if not isinstance(symbol, str) or not symbol:
        raise OperationError("INVALID_PARAMETERS", "symbol must be a non-empty string")
    key = "callee" if direction == "callers" else "caller"
    selected = [row for row in _calls(store) if row.get(key) == symbol]
    selected.sort(key=lambda row: (str(row.get("caller")), str(row.get("callee")), str(row.get("source_file")), int(row.get("line", 0))))
    return {direction: selected, "count": len(selected), "symbol": symbol}, store, []


def trace_callers(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _trace(store, parameters, "callers")


def trace_callees(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _trace(store, parameters, "callees")


def compare_source_and_jar(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    document = store.read("analysis/source-jar-comparison.json")
    if not isinstance(document, dict):
        raise OperationError("EVIDENCE_NOT_AVAILABLE", "analysis/source-jar-comparison.json has not been produced")
    required = {"schema_version", "source_facts", "jar_facts", "agreements", "source_only", "jar_only"}
    missing = sorted(required - set(document))
    if missing:
        raise OperationError("INVALID_COMPARISON", "Missing comparison fields: " + ", ".join(missing))
    return {"comparison": document}, store, []


def select_pattern(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    pattern_id = parameters.get("pattern_id")
    target = parameters.get("target")
    provenance = parameters.get("provenance")
    if not isinstance(pattern_id, str) or not isinstance(target, str) or not isinstance(provenance, dict):
        raise OperationError("INVALID_PARAMETERS", "pattern_id, target, and provenance are required")
    pattern = next((row for row in marketplace_patterns() if row["id"] == pattern_id), None)
    if pattern is None:
        raise OperationError("UNKNOWN_PATTERN", f"Unknown Marketplace pattern: {pattern_id}")
    if not provenance.get("author") or not provenance.get("reason"):
        raise OperationError("INVALID_PROVENANCE", "Pattern selection requires author and reason")
    document = store.read("decisions/patterns.json", {"schema_version": "1.0.0", "selections": []})
    selections = list(document.get("selections", [])) if isinstance(document, dict) else []
    selections = [row for row in selections if row.get("target") != target]
    selections.append({"target": target, "pattern_id": pattern_id, "pattern_version": pattern["version"], "provenance": provenance, "status": "SELECTED_PENDING_VALIDATION"})
    selections.sort(key=lambda row: str(row["target"]))
    updated = {"schema_version": "1.0.0", "selections": selections}
    revision = store.commit({"decisions/patterns.json": updated}, expected_revision=expected_revision)
    return {"selection": selections[-1], "pattern": pattern, "revision": revision}, store, [{"path": "decisions/patterns.json", "kind": "pattern_selection"}]


def estimate_fidelity(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    feature_id = parameters.get("feature_id")
    records = store.read("reports/fidelity.json", {"mechanics": []})
    mechanics = records.get("mechanics", []) if isinstance(records, dict) else []
    selected = [row for row in mechanics if isinstance(row, dict) and (feature_id is None or row.get("feature_id") == feature_id)]
    errors = [error for row in selected for error in validate_quality_record(row)]
    return {"records": selected, "errors": errors, "evidence_based": True, "estimated_without_evidence": False}, store, []


def estimate_performance(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    report = store.read("dist/reports/performance-report.json")
    if not isinstance(report, dict):
        raise OperationError("EVIDENCE_NOT_AVAILABLE", "No measured or static performance report is persisted")
    return {"performance": report, "measured": bool(report.get("runtime_measurements")), "approval_implied": False}, store, []
