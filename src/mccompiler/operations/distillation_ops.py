from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Callable

from mccompiler.distillation import DistillationError, distill_modpack
from mccompiler.project.store import ProjectError, ProjectStore


def _parameters(parameters: dict[str, Any]) -> tuple[str, int]:
    target = parameters.get("target", "MARKETPLACE_ADDON_STABLE")
    budget = parameters.get("effort_budget_basis_points", 2500)
    if target != "MARKETPLACE_ADDON_STABLE":
        raise ProjectError("INVALID_PARAMETERS", "target must be MARKETPLACE_ADDON_STABLE")
    if isinstance(budget, bool) or not isinstance(budget, int) or not 1 <= budget <= 10_000:
        raise ProjectError("INVALID_PARAMETERS", "effort_budget_basis_points must be an integer from 1 through 10000")
    return target, budget


def _run(store: ProjectStore, parameters: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    target, budget = _parameters(parameters)
    requested = str(parameters.get("input", "analysis/distillation-input.json"))
    input_path = store.resolve(requested)
    if not input_path.exists():
        input_path = store.root
    temporary = tempfile.TemporaryDirectory(prefix="mccompiler-distillation-operation-")
    adjustment_path = store.resolve("decisions/distillation/review-adjustments.json")
    adjustment_document = store.read("decisions/distillation/review-adjustments.json", {"adjustments": []})
    applied_adjustments: Path | None = adjustment_path if adjustment_document.get("adjustments") else None
    try:
        result = distill_modpack(
            input_path,
            temporary.name,
            target=target,
            effort_budget_basis_points=budget,
            review_adjustments=applied_adjustments,
        )
    except DistillationError as exc:
        temporary.cleanup()
        raise ProjectError("INVALID_DISTILLATION_INPUT", str(exc)) from exc
    root = Path(temporary.name)
    result["_temporary"] = temporary
    return result, root


def _query(
    store: ProjectStore,
    parameters: dict[str, Any],
    project: Callable[[dict[str, Any]], Any],
) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    result, _ = _run(store, parameters)
    temporary = result.pop("_temporary")
    try:
        return project(result), store, []
    finally:
        temporary.cleanup()


def analyze_modpack_identity(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _query(store, parameters, lambda result: {"identity": result["identity"], "source_digest": result["source_digest"]})


def cluster_gameplay_systems(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _query(store, parameters, lambda result: {"systems": [{"id": row["id"], "name": row["name"], "feature_ids": row.get("feature_ids", []), "categories": row.get("categories", [])} for row in result["systems"]]})


def score_feature_value(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _query(store, parameters, lambda result: {"system_scores": result["scores"], "feature_scores": result["feature_scores"], "weights_version": result["weights_version"]})


def estimate_conversion_effort(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _query(store, parameters, lambda result: {"systems": [{"id": row["id"], "effort_units": row["effort_units"]} for row in result["systems"]], "full_effort_units": result["selection"]["full_effort_units"], "effort_limit_units": result["selection"]["effort_limit_units"]})


def estimate_console_cost(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _query(store, parameters, lambda result: {"systems": [{"id": row["id"], "console_cost_units": row["console_cost_units"], "risks": row.get("console_risks", [])} for row in result["systems"]], "limit_units": result["console_limit_units"], "evidence_level": "STATIC_ESTIMATE_ONLY"})


def estimate_pattern_reuse(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _query(store, parameters, lambda result: {"systems": [{"id": row["id"], "patterns": row.get("patterns", [])} for row in result["systems"]]})


def identify_progression_dependencies(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _query(store, parameters, lambda result: {"required_stages": result["required_progression_stages"], "systems": [{"id": row["id"], "prerequisites": row.get("prerequisites", []), "stages": row.get("progression_stages", [])} for row in result["systems"]]})


def select_quarter_scope(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    result, root = _run(store, parameters)
    temporary = result.pop("_temporary")
    try:
        documents: dict[str, Any] = {}
        text_documents: dict[str, str] = {}
        artifacts: list[dict[str, Any]] = []
        for path in sorted((root / "distillation").iterdir()):
            relative = f"distillation/{path.name}"
            if path.suffix in {".json", ".yaml"}:
                documents[relative] = json.loads(path.read_text(encoding="utf-8"))
            else:
                text_documents[relative] = path.read_text(encoding="utf-8")
            artifacts.append({"path": relative, "kind": "distillation"})
        if expected_revision is not None and expected_revision != store.revision:
            raise ProjectError("REVISION_CONFLICT", f"Expected project revision {expected_revision}, found {store.revision}")
        for relative, text in text_documents.items():
            store.write_text(relative, text)
        revision = store.commit(documents, expected_revision=expected_revision)
        return {"selection": result["selection"], "result_digest": result["result_digest"], "revision": revision}, store, artifacts
    finally:
        temporary.cleanup()


def explain_selection(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    persisted = store.read("distillation/quarter-scope.json")
    deferred = store.read("distillation/deferred-scope.yaml")
    if persisted is not None and deferred is not None:
        return {"selection": persisted.get("selection"), "selected": persisted.get("systems", []), "deferred": deferred.get("systems", [])}, store, []
    return _query(store, parameters, lambda result: {"selection": result["selection"], "decisions": result["decisions"]})


def generate_conversion_roadmap(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    path = store.resolve("distillation/conversion-roadmap.md")
    if not path.is_file():
        raise ProjectError("DISTILLATION_NOT_RUN", "Run select_quarter_scope before requesting the roadmap")
    return {"roadmap": path.read_text(encoding="utf-8")}, store, [{"path": "distillation/conversion-roadmap.md", "kind": "distillation"}]


def record_distillation_adjustment(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    required = ("id", "author", "author_type", "reason", "evidence", "change")
    missing = [key for key in required if key not in parameters]
    if missing:
        raise ProjectError("INVALID_PARAMETERS", f"Missing adjustment fields: {', '.join(missing)}")
    if parameters["author_type"] not in {"HUMAN", "AI"}:
        raise ProjectError("INVALID_PARAMETERS", "author_type must be HUMAN or AI")
    if not all(isinstance(parameters[key], str) and parameters[key].strip() for key in ("id", "author", "reason")):
        raise ProjectError("INVALID_PARAMETERS", "id, author, and reason must be non-empty strings")
    if not isinstance(parameters["evidence"], list) or not parameters["evidence"] or not all(isinstance(value, str) and value for value in parameters["evidence"]):
        raise ProjectError("INVALID_PARAMETERS", "evidence must be a non-empty array of strings")
    change = parameters["change"]
    if not isinstance(change, dict):
        raise ProjectError("INVALID_PARAMETERS", "change must be an object")
    if change.get("replacement") == "MARKETPLACE_CLEARED":
        raise ProjectError("RIGHTS_AUTHORITY_REQUIRED", "Distillation review adjustments cannot grant Marketplace clearance")
    path = "decisions/distillation/review-adjustments.json"
    document = store.read(path, {"schema_version": "1.0.0", "adjustments": []})
    adjustments = list(document.get("adjustments", []))
    if any(row.get("id") == parameters["id"] for row in adjustments):
        raise ProjectError("DUPLICATE_ADJUSTMENT", f"Adjustment id already exists: {parameters['id']}")
    record = {key: parameters[key] for key in required}
    record["authority"] = "ADVISORY_ONLY"
    adjustments.append(record)
    revision = store.commit({path: {"schema_version": "1.0.0", "adjustments": adjustments}}, expected_revision=expected_revision)
    return {"adjustment": record, "revision": revision}, store, [{"path": path, "kind": "distillation_review"}]
