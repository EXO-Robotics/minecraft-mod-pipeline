from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

from mccompiler.cleanroom import (
    CleanRoomError,
    build_gameplay_intent as build_intent_ir,
    evaluate_rights_strategy,
    export_clean_room_contract as export_contract,
    screen_similarity,
    validate_material_ledger,
)
from mccompiler.forest_planning import (
    AcceptanceGraph,
    AcceptanceNode,
    Budget,
    EvidenceState,
    ForestElement,
    ProductionWavePlanner,
)
from mccompiler.operations.envelope import OperationError
from mccompiler.project.store import ProjectError, ProjectStore


HandlerResult = tuple[Any, ProjectStore, list[dict[str, Any]]]
_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")


def _slug(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OperationError("INVALID_PARAMETERS", f"{field} must be non-empty")
    return _SAFE_ID.sub("_", value.strip()).strip("._") or "record"


def _artifact(store: ProjectStore, relative: str, kind: str) -> dict[str, Any]:
    path = store.resolve(relative)
    return {"path": relative, "kind": kind, "size": path.stat().st_size}


def _policy_error(exc: Exception, remediation: str) -> OperationError:
    if isinstance(exc, CleanRoomError):
        return OperationError(
            exc.code,
            str(exc),
            details={"findings": list(exc.findings), "remediation": remediation, "mutated": False},
        )
    return OperationError(
        "MILESTONE_VALIDATION_FAILED",
        str(exc),
        details={"remediation": remediation, "mutated": False},
    )


def _commit(
    store: ProjectStore,
    relative: str,
    document: Mapping[str, Any],
    kind: str,
    expected_revision: int | None,
) -> HandlerResult:
    revision = store.commit({relative: dict(document)}, expected_revision=expected_revision)
    return {"status": "RECORDED", "path": relative, "document": dict(document), "revision": revision}, store, [
        _artifact(store, relative, kind)
    ]


def create_rights_strategy(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    mode = parameters.get("mode", "clean_room_originalization")
    if mode == "clean_room_originalization":
        strategy = {
            "schema_version": "1.0.0",
            "mode": mode,
            "inspiration_scope": "abstract_gameplay_patterns_only",
            "direct_source_expression_reuse": "prohibited",
            "third_party_assets_allowed": False,
            "third_party_names_allowed": False,
            "third_party_branding_allowed": False,
            "distinctive_expression_allowed": False,
            "commercial_marketplace_rights_required": True,
        }
    elif mode == "authorized_adaptation":
        supplied = parameters.get("strategy")
        if not isinstance(supplied, Mapping):
            raise OperationError(
                "AUTHORIZED_ADAPTATION_EVIDENCE_REQUIRED",
                "authorized_adaptation requires a complete strategy object and material ledger",
                details={"remediation": "Register material-level permissions, then supply strategy.", "mutated": False},
            )
        strategy = {"schema_version": "1.0.0", **dict(supplied), "mode": mode}
    else:
        raise OperationError("INVALID_RIGHTS_MODE", f"Unsupported rights strategy mode: {mode}")
    ledger = store.read("analysis/rights-ledger/materials.json", {"schema_version": "1.0.0", "records": []})
    assessment = evaluate_rights_strategy(strategy, ledger)
    if mode == "authorized_adaptation" and not assessment["production_allowed"]:
        raise OperationError(
            "AUTHORIZED_ADAPTATION_EVIDENCE_REQUIRED",
            "Authorized-adaptation permissions are incomplete",
            details={"findings": assessment["findings"], "remediation": "Complete every applicable material permission.", "mutated": False},
        )
    strategy["assessment"] = assessment
    return _commit(store, "analysis/rights-ledger/strategy.json", strategy, "rights_strategy", expected_revision)


def register_rights_material(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    record = parameters.get("record")
    if not isinstance(record, Mapping):
        raise OperationError("INVALID_PARAMETERS", "record must be an object")
    ledger = store.read("analysis/rights-ledger/materials.json", {"schema_version": "1.0.0", "records": []})
    records = list(ledger.get("records", [])) if isinstance(ledger, Mapping) else []
    material_id = record.get("material_id")
    records = [row for row in records if not isinstance(row, Mapping) or row.get("material_id") != material_id]
    records.append(dict(record))
    updated = {"schema_version": "1.0.0", "records": sorted(records, key=lambda row: str(row.get("material_id")))}
    result = validate_material_ledger(updated)
    if not result["valid"]:
        raise OperationError(
            "RIGHTS_MATERIAL_INVALID",
            "Material rights record failed validation",
            details={"findings": result["findings"], "remediation": "Correct the material-level ownership, permission, restriction, and disposition fields.", "mutated": False},
        )
    return _commit(store, "analysis/rights-ledger/materials.json", updated, "rights_material_ledger", expected_revision)


def inspect_rights_material(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    material_id = parameters.get("material_id")
    ledger = store.read("analysis/rights-ledger/materials.json", {"schema_version": "1.0.0", "records": []})
    record = next((row for row in ledger.get("records", []) if isinstance(row, Mapping) and row.get("material_id") == material_id), None)
    if record is None:
        raise OperationError("RIGHTS_MATERIAL_NOT_FOUND", f"Rights material not found: {material_id}", details={"remediation": "Register the material first.", "mutated": False})
    normalized = next(row for row in validate_material_ledger(ledger)["records"] if row["material_id"] == material_id)
    return {"record": record, "assessment": normalized, "legal_clearance_implied": False}, store, []


def _allowed_evidence(store: ProjectStore) -> list[str]:
    index = store.read("analysis/evidence/index.json", {"evidence": []})
    refs: list[str] = []
    for row in index.get("evidence", []) if isinstance(index, Mapping) else []:
        if isinstance(row, Mapping):
            value = row.get("uri") or row.get("id")
            if isinstance(value, str):
                refs.append(value)
    return sorted(set(refs))


def build_gameplay_intent(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    intent = parameters.get("intent")
    if not isinstance(intent, Mapping):
        raise OperationError("INVALID_PARAMETERS", "intent must be an object")
    try:
        output = build_intent_ir(intent, allowed_evidence_refs=_allowed_evidence(store))
    except (CleanRoomError, ValueError) as exc:
        raise _policy_error(exc, "Use registered evidence references and complete every audited claim and rights disposition.") from exc
    relative = f"analysis/gameplay-intent/{_slug(output.get('intent_id'), 'intent.intent_id')}.json"
    return _commit(store, relative, output, "gameplay_intent_ir", expected_revision)


def _intent(store: ProjectStore, parameters: Mapping[str, Any]) -> Mapping[str, Any]:
    supplied = parameters.get("intent")
    if isinstance(supplied, Mapping):
        return supplied
    intent_id = _slug(parameters.get("intent_id"), "intent_id")
    document = store.read(f"analysis/gameplay-intent/{intent_id}.json")
    if not isinstance(document, Mapping):
        raise OperationError("GAMEPLAY_INTENT_NOT_FOUND", f"Gameplay intent not found: {intent_id}")
    return document


def validate_gameplay_intent(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    intent = _intent(store, parameters)
    try:
        validated = build_intent_ir(intent, allowed_evidence_refs=_allowed_evidence(store))
    except (CleanRoomError, ValueError) as exc:
        raise _policy_error(exc, "Repair the stored intent; validation never advances the revision.") from exc
    return {"valid": True, "intent_id": validated["intent_id"], "semantic_hash": validated["semantic_hash"]}, store, []


def export_clean_room_contract(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    intent = _intent(store, parameters)
    contract_id = parameters.get("contract_id")
    if not isinstance(contract_id, str):
        raise OperationError("INVALID_PARAMETERS", "contract_id must be non-empty")
    try:
        output = export_contract(
            intent,
            contract_id=contract_id,
            blocked_names=parameters.get("blocked_names", []),
            blocked_hashes=parameters.get("blocked_hashes", []),
        )
    except (CleanRoomError, ValueError) as exc:
        raise _policy_error(exc, "Remove restricted expression or omit the concept pending license.") from exc
    relative = f"production/design-contracts/{_slug(contract_id, 'contract_id')}.json"
    return _commit(store, relative, output, "clean_room_design_contract", expected_revision)


def screen_product_similarity(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    candidate = parameters.get("candidate")
    references = parameters.get("restricted_references", [])
    if not isinstance(candidate, Mapping) or not isinstance(references, list) or not all(isinstance(row, Mapping) for row in references):
        raise OperationError("INVALID_PARAMETERS", "candidate must be an object and restricted_references an array of objects")
    report = screen_similarity(
        candidate,
        references,
        blocked_names=parameters.get("blocked_names", []),
        blocked_hashes=parameters.get("blocked_hashes", []),
    )
    relative = f"production/similarity-screening/{_slug(report.get('product_id'), 'candidate.product_id')}.json"
    return _commit(store, relative, report, "similarity_screening_report", expected_revision)


def _graph(parameters: Mapping[str, Any]) -> AcceptanceGraph:
    rows = parameters.get("nodes")
    if not isinstance(rows, list):
        raise ValueError("nodes must be an array")
    return AcceptanceGraph(AcceptanceNode(
        str(row["node_id"]),
        int(row["weight"]),
        tuple(map(str, row.get("dependencies", []))),
        EvidenceState(str(row.get("evidence", "CONTRACT_ONLY"))),
        EvidenceState(str(row.get("required", "SERVER_QUALIFIED"))),
    ) for row in rows if isinstance(row, Mapping))


def build_experience_graph(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    try:
        graph = _graph(parameters)
    except (KeyError, TypeError, ValueError) as exc:
        raise _policy_error(exc, "Provide an acyclic graph with known dependencies and valid evidence states.") from exc
    document = {
        "schema_version": "1.0.0",
        "nodes": [{
            "node_id": row.node_id, "weight": row.weight, "dependencies": list(row.dependencies),
            "evidence": row.evidence.value, "required": row.required.value,
        } for row in sorted(graph.nodes.values(), key=lambda item: item.node_id)],
    }
    return _commit(store, "production/experience/acceptance-graph.json", document, "experience_acceptance_graph", expected_revision)


def calculate_experience_coverage(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    document = store.read("production/experience/acceptance-graph.json")
    if not isinstance(document, Mapping):
        raise OperationError("EXPERIENCE_GRAPH_NOT_FOUND", "Build the experience graph first")
    graph = _graph(document)
    report = {"schema_version": "1.0.0", "coverage": graph.weighted_coverage(), "blockers": graph.blockers()}
    return _commit(store, "production/experience/coverage-report.json", report, "experience_coverage_report", expected_revision)


def plan_production_wave(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    try:
        budget_row = parameters["budget"]
        rows = parameters["elements"]
        if not isinstance(budget_row, Mapping) or not isinstance(rows, list):
            raise ValueError("budget must be an object and elements an array")
        budget = Budget(budget_row["hard_caps"], budget_row["reserves"])
        elements = [ForestElement(
            element_id=str(row["id"]),
            priority=int(row["priority"]),
            costs=row["costs"],
            scope_units=int(row.get("scope_units", 0)),
            dependencies=tuple(map(str, row.get("dependencies", []))),
            evidence=EvidenceState(str(row.get("evidence", "CONTRACT_ONLY"))),
            contract_ref=str(row.get("contract_ref", "")),
            qualification_ref=str(row["qualification_ref"]) if row.get("qualification_ref") is not None else None,
        ) for row in rows if isinstance(row, Mapping)]
        plan = ProductionWavePlanner(budget, max_waves=int(parameters.get("max_waves", 8))).plan(elements)
    except (KeyError, TypeError, ValueError) as exc:
        raise _policy_error(exc, "Correct dependencies, PS4 budget dimensions, costs, reserves, or wave limit.") from exc
    return _commit(store, "production/production-plans/forest-wave-plan.json", plan, "production_wave_plan", expected_revision)


def validate_production_wave(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    plan = store.read("production/production-plans/forest-wave-plan.json")
    if not isinstance(plan, Mapping):
        raise OperationError("PRODUCTION_PLAN_NOT_FOUND", "Plan a production wave first")
    findings: list[dict[str, str]] = []
    if plan.get("schema_version") != "1.0.0":
        findings.append({"code": "UNSUPPORTED_SCHEMA", "message": "plan must use schema 1.0.0"})
    if plan.get("deferred"):
        findings.append({"code": "DEFERRED_ELEMENTS", "message": "not every requested element fits the bounded plan"})
    report = {
        "schema_version": "1.0.0", "valid": not findings, "findings": findings,
        "physical_ps4_verified": False, "production_authorized": False,
        "remediation": "Resolve deferred elements and complete required qualification before production.",
    }
    return _commit(store, "production/production-plans/validation-report.json", report, "production_plan_validation_report", expected_revision)


def show_production_wave(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    plan = store.read("production/production-plans/forest-wave-plan.json")
    if not isinstance(plan, Mapping):
        raise OperationError("PRODUCTION_PLAN_NOT_FOUND", "Plan a production wave first")
    validation = store.read("production/production-plans/validation-report.json")
    return {"plan": plan, "validation": validation, "production_authorized": False}, store, []
