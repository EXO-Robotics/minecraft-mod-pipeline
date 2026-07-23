from __future__ import annotations

import hashlib
import json
import copy
from pathlib import Path
from typing import Any

from .model import DEFAULT_PROGRESSION_STAGES, FEASIBILITY_DIMENSIONS, NEGATIVE_DIMENSIONS, POSITIVE_DIMENSIONS, RIGHTS_DIMENSIONS, STRATEGIES
from .inventory import distillation_input_from_modir
from .reports import canonical_json, render_reports, write_text_atomic
from .scoring import score_system
from .selector import classify_strategy, select_scope
from .validation import schema_contracts, validate_distillation_output, validate_with_schema


class DistillationError(ValueError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DistillationError(f"Cannot read distillation input {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DistillationError("Distillation input must be a JSON object")
    return value


def load_distillation_input(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    if source.is_file():
        document = _read_json(source)
        if isinstance(document.get("systems"), list):
            return document
        if isinstance(document.get("content"), list) and isinstance(document.get("behaviors"), list):
            return distillation_input_from_modir(document)
        raise DistillationError("JSON input is neither distillation input nor ModIR")
    candidates = (
        source / "distillation-input.json",
        source / "analysis/distillation-input.json",
        source / "distillation-metadata.json",
    )
    for candidate in candidates:
        if candidate.is_file():
            return _read_json(candidate)
    modir = source / "analysis/modir.json"
    if modir.is_file():
        return distillation_input_from_modir(_read_json(modir))
    if source.exists():
        from mccompiler.scan import scan_path
        return distillation_input_from_modir(scan_path(source))
    raise DistillationError(f"Input path does not exist: {source}")


def _weights() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "capabilities/distillation-weights-1.0.0.json"
    return _read_json(path)


def _validate_input(document: dict[str, Any]) -> None:
    schema_errors = validate_with_schema(document, schema_contracts()["distillation-input-1.0.0.json"])
    if schema_errors:
        raise DistillationError("Distillation input schema errors: " + "; ".join(schema_errors))
    if document.get("schema_version") != "1.0.0":
        raise DistillationError("distillation input schema_version must be 1.0.0")
    identity = document.get("identity")
    if (
        not isinstance(identity, dict)
        or not isinstance(identity.get("summary"), str)
        or not identity["summary"].strip()
        or not isinstance(identity.get("load_bearing_systems"), list)
        or not all(isinstance(value, str) and value for value in identity["load_bearing_systems"])
    ):
        raise DistillationError("identity requires a non-empty summary and load_bearing_systems string array")
    console_limit = document.get("console_limit_units")
    if isinstance(console_limit, bool) or not isinstance(console_limit, int) or console_limit < 1:
        raise DistillationError("console_limit_units must be a positive integer")
    systems = document.get("systems")
    if not isinstance(systems, list) or not systems:
        raise DistillationError("distillation input requires a non-empty systems array")
    identifiers: set[str] = set()
    all_dimensions = POSITIVE_DIMENSIONS + FEASIBILITY_DIMENSIONS + RIGHTS_DIMENSIONS + NEGATIVE_DIMENSIONS
    for system in systems:
        if not isinstance(system, dict):
            raise DistillationError("Every system must be an object")
        identifier = system.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise DistillationError("Every system requires a non-empty id")
        if identifier in identifiers:
            raise DistillationError(f"Duplicate system id: {identifier}")
        identifiers.add(identifier)
        if not isinstance(system.get("name"), str) or not system["name"]:
            raise DistillationError(f"System {identifier} requires name")
        for key in ("effort_units", "console_cost_units"):
            value = system.get(key)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise DistillationError(f"System {identifier} {key} must be a non-negative integer")
        if system.get("strategy", "DIRECT_RECONSTRUCTION") not in STRATEGIES:
            raise DistillationError(f"System {identifier} has invalid strategy")
        if system.get("stable_api_status") not in {"COMPATIBLE", "UNKNOWN", "UNSUPPORTED"}:
            raise DistillationError(f"System {identifier} requires stable_api_status")
        for key in ("prerequisites", "unlocks", "categories", "progression_stages", "feature_ids", "patterns"):
            values = system.get(key, [])
            if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
                raise DistillationError(f"System {identifier} {key} must be an array of non-empty strings")
        for key in ("encounter", "reward", "unlock", "future_support", "removable_without_breaking_progression"):
            if key not in system:
                raise DistillationError(f"System {identifier} requires progression field {key}")
        for key in ("encounter", "reward", "unlock", "future_support"):
            if not isinstance(system[key], str) or not system[key].strip():
                raise DistillationError(f"System {identifier} {key} must be a non-empty string")
        if not isinstance(system["removable_without_breaking_progression"], bool):
            raise DistillationError(f"System {identifier} removable_without_breaking_progression must be boolean")
        dimensions = system.get("dimensions")
        if not isinstance(dimensions, dict):
            raise DistillationError(f"System {identifier} requires dimensions")
        missing = sorted(set(all_dimensions) - set(dimensions))
        if missing:
            raise DistillationError(f"System {identifier} missing dimensions: {', '.join(missing)}")
    for system in systems:
        dangling = sorted(set(system.get("prerequisites", [])) - identifiers)
        if dangling:
            raise DistillationError(f"System {system['id']} has dangling prerequisites: {', '.join(dangling)}")
        dangling_unlocks = sorted(set(system.get("unlocks", [])) - identifiers)
        if dangling_unlocks:
            raise DistillationError(f"System {system['id']} has dangling unlocks: {', '.join(dangling_unlocks)}")
    by_id = {system["id"]: system for system in systems}
    for system in systems:
        for required in system["prerequisites"]:
            if system["id"] not in by_id[required]["unlocks"]:
                raise DistillationError(f"Progression edge {required} -> {system['id']} is missing from {required}.unlocks")
        for unlocked in system["unlocks"]:
            if system["id"] not in by_id[unlocked]["prerequisites"]:
                raise DistillationError(f"Progression edge {system['id']} -> {unlocked} is missing from {unlocked}.prerequisites")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visiting:
            raise DistillationError(f"Progression dependency cycle detected at {identifier}")
        if identifier in visited:
            return
        visiting.add(identifier)
        for required in by_id[identifier]["prerequisites"]:
            visit(required)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in sorted(by_id):
        visit(identifier)


def _normalize_document(document: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(document)
    defaults = normalized.pop("default_dimensions", {})
    default_originality = normalized.pop("default_originality_evidence", [])
    default_stable_api = normalized.pop("default_stable_api_status", None)
    if defaults and not isinstance(defaults, dict):
        raise DistillationError("default_dimensions must be an object")
    if default_originality and (
        not isinstance(default_originality, list)
        or not all(isinstance(value, str) and value for value in default_originality)
    ):
        raise DistillationError("default_originality_evidence must be an array of non-empty strings")
    systems = normalized.get("systems", [])
    if isinstance(systems, list):
        for system in systems:
            if isinstance(system, dict):
                dimensions = system.get("dimensions", {})
                if not isinstance(dimensions, dict):
                    continue
                system["dimensions"] = {**copy.deepcopy(defaults), **dimensions}
                if default_originality and "originality_evidence" not in system:
                    system["originality_evidence"] = copy.deepcopy(default_originality)
                    system["original_content"] = True
                if default_stable_api is not None and "stable_api_status" not in system:
                    system["stable_api_status"] = default_stable_api
                for key in ("prerequisites", "unlocks", "categories", "progression_stages", "feature_ids", "patterns", "console_risks", "rights_risks", "benchmarks_required"):
                    if isinstance(system.get(key), list):
                        system[key] = sorted(system[key], key=str)
                for value in system["dimensions"].values():
                    if isinstance(value, dict) and isinstance(value.get("evidence"), list):
                        value["evidence"] = sorted(value["evidence"], key=str)
        systems.sort(key=lambda row: str(row.get("id")) if isinstance(row, dict) else "")
    for key in ("evidence_gaps", "required_inputs", "required_progression_stages"):
        if isinstance(normalized.get(key), list):
            normalized[key] = sorted(normalized[key], key=str)
    identity = normalized.get("identity")
    if isinstance(identity, dict) and isinstance(identity.get("load_bearing_systems"), list):
        identity["load_bearing_systems"] = sorted(identity["load_bearing_systems"], key=str)
    return normalized


def _load_adjustments(path: str | Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    document = _read_json(Path(path).expanduser().resolve())
    schema_errors = validate_with_schema(document, schema_contracts()["distillation-review-adjustments-1.0.0.json"])
    if schema_errors:
        raise DistillationError("Review adjustment schema errors: " + "; ".join(schema_errors))
    if document.get("schema_version") != "1.0.0" or not isinstance(document.get("adjustments"), list):
        raise DistillationError("Review adjustments must use schema_version 1.0.0 and an adjustments array")
    required = {"id", "author", "author_type", "reason", "evidence", "change"}
    identifiers: set[str] = set()
    for row in document["adjustments"]:
        if not isinstance(row, dict) or not required.issubset(row):
            raise DistillationError("Every review adjustment needs id, author, author_type, reason, evidence, and change")
        if not all(isinstance(row.get(key), str) and row[key].strip() for key in ("id", "author", "reason")):
            raise DistillationError("Review adjustment id, author, and reason must be non-empty strings")
        if row["id"] in identifiers:
            raise DistillationError(f"Duplicate review adjustment id: {row['id']}")
        identifiers.add(row["id"])
        if row.get("author_type") not in {"HUMAN", "AI"}:
            raise DistillationError("Review adjustment author_type must be HUMAN or AI")
        if not isinstance(row.get("evidence"), list) or not row["evidence"] or not all(isinstance(value, str) and value for value in row["evidence"]):
            raise DistillationError("Review adjustment evidence must be a non-empty array of strings")
        if not isinstance(row.get("change"), dict):
            raise DistillationError("Review adjustment change must be an object")
        if row["change"].get("replacement") == "MARKETPLACE_CLEARED":
            raise DistillationError("Review adjustments cannot grant Marketplace clearance")
    return list(document["adjustments"])


def _apply_review_selection(result: dict[str, Any], adjustments: list[dict[str, Any]]) -> None:
    result["review_adjustments"] = adjustments
    result["review_adjustments_applied"] = bool(adjustments)
    result["reviewed_selection"] = None
    selection_changes = [row for row in adjustments if row.get("change", {}).get("kind") == "selection"]
    if selection_changes:
        result["reviewed_selection"] = {
            "status": "SEPARATE_REVIEW_ONLY_NOT_DETERMINISTIC_SCORE",
            "adjustments": selection_changes,
        }


def distill_modpack(
    input_path: str | Path,
    output_path: str | Path,
    *,
    target: str = "MARKETPLACE_ADDON_STABLE",
    effort_budget_basis_points: int = 2500,
    review_adjustments: str | Path | None = None,
) -> dict[str, Any]:
    if target != "MARKETPLACE_ADDON_STABLE":
        raise DistillationError("Distillation currently supports only MARKETPLACE_ADDON_STABLE")
    if not 1 <= effort_budget_basis_points <= 10_000:
        raise DistillationError("effort budget must be greater than 0 and at most 1")
    document = _normalize_document(load_distillation_input(input_path))
    _validate_input(document)
    weights = _weights()
    systems = sorted(document["systems"], key=lambda row: row["id"])
    try:
        scores = [score_system(row, weights) for row in systems]
        selection = select_scope(
            systems,
            scores,
            effort_budget_basis_points,
            int(document.get("console_limit_units", 100)),
            list(document.get("required_progression_stages", [])) or None,
        )
    except ValueError as exc:
        raise DistillationError(str(exc)) from exc
    decisions: dict[str, dict[str, Any]] = {}
    feature_scores: list[dict[str, Any]] = []
    for system in systems:
        evidence_by_id = {
            str(row.get("id")): row
            for row in system.get("features", [])
            if isinstance(row, dict) and row.get("id")
        }
        for feature_id in system.get("feature_ids", []):
            feature = evidence_by_id.get(str(feature_id), {})
            feature_score = score_system(
                {"id": str(feature_id), "dimensions": feature.get("dimensions", {})},
                weights,
            )
            feature_scores.append({
                "feature_id": str(feature_id),
                "system_id": system["id"],
                "raw_score_milli": feature_score["raw_score_milli"],
                "confidence_basis_points": feature_score["confidence_basis_points"],
                "basis": "FEATURE_SPECIFIC_EVIDENCE" if feature else "UNKNOWN_FEATURE_EVIDENCE_SCORED_FAIL_CLOSED",
                "evidence_gaps": feature_score["evidence_gaps"],
            })
    selected = set(selection["ids"])
    for system in systems:
        classification, blockers = classify_strategy(system)
        reasons = list(blockers)
        if system["id"] in selected:
            reasons.append("selected by deterministic value, constraint, and prerequisite analysis")
        else:
            if not reasons:
                reasons.append("deferred by deterministic budget/value optimization")
            classification = classification if classification in {"RIGHTS_BLOCKED", "UNSUPPORTED"} else "DEFER"
        decisions[system["id"]] = {"classification": classification, "reasons": reasons}
    result: dict[str, Any] = {
        "schema_version": "1.0.0",
        "target": target,
        "analysis_status": document.get("analysis_status", "EVIDENCE_BACKED"),
        "weights_version": weights["version"],
        "effort_budget_basis_points": effort_budget_basis_points,
        "console_limit_units": int(document.get("console_limit_units", 100)),
        "identity": document.get("identity", {"summary": "Identity evidence not supplied.", "load_bearing_systems": []}),
        "evidence_gaps": sorted(str(row) for row in document.get("evidence_gaps", [])),
        "required_inputs": sorted(str(row) for row in document.get("required_inputs", [])),
        "required_progression_stages": list(document.get("required_progression_stages", [])) or list(DEFAULT_PROGRESSION_STAGES),
        "systems": systems,
        "scores": scores,
        "feature_scores": feature_scores,
        "selection": selection,
        "decisions": decisions,
        "source_digest": hashlib.sha256(canonical_json(document).encode()).hexdigest(),
    }
    _apply_review_selection(result, _load_adjustments(review_adjustments))
    artifacts = render_reports(result, Path(output_path).expanduser().resolve())
    manifest = {
        "schema_version": "1.0.0",
        "tool": "mccompiler distill-modpack",
        "target": target,
        "weights_version": weights["version"],
        "source_digest": result["source_digest"],
        "effort_budget_basis_points": effort_budget_basis_points,
        "review_adjustments_applied": result["review_adjustments_applied"],
        "artifacts": artifacts,
    }
    manifest_text = canonical_json(manifest)
    manifest_path = Path(output_path).expanduser().resolve() / "distillation/distillation-manifest.json"
    write_text_atomic(manifest_path, manifest_text)
    output_errors = validate_distillation_output(output_path, require_complete=False)
    if output_errors:
        raise DistillationError("Generated distillation output failed validation: " + "; ".join(output_errors))
    result["artifacts"] = artifacts + [{"path": "distillation/distillation-manifest.json", "sha256": hashlib.sha256(manifest_text.encode()).hexdigest()}]
    result["result_digest"] = hashlib.sha256(canonical_json({
        "selection": selection,
        "scores": scores,
        "feature_scores": feature_scores,
        "decisions": decisions,
        "review_adjustments": result["review_adjustments"],
        "reviewed_selection": result["reviewed_selection"],
        "artifacts": result["artifacts"],
        "source_digest": result["source_digest"],
    }).encode()).hexdigest()
    return result
