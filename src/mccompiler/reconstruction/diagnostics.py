from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any, Iterable, Mapping, Sequence


TRANSFORMATION_DISPOSITIONS = frozenset({
    "DIRECT", "SCRIPTED", "RECONSTRUCTED", "REDESIGNED", "DEFERRED",
    "RIGHTS_BLOCKED", "UNSUPPORTED",
})
EXPRESSION_DISPOSITIONS = frozenset({
    "LICENSED_REUSE", "ANALYSIS_ONLY", "ABSTRACT_PATTERN_RETAINED",
    "CLEAN_ROOM_REPLACEMENT", "OMIT_PENDING_LICENSE",
})
READINESS_STATUSES = frozenset({
    "READY_TO_EXECUTE", "READY_WITH_REDESIGN", "MORE_EVIDENCE_REQUIRED",
    "RIGHTS_BLOCKED", "BEDROCK_STRATEGY_UNRESOLVED", "DEPENDENCY_BLOCKED",
    "PS4_BUDGET_BLOCKED",
})
CLAIM_STATES = frozenset({"observed", "inferred", "unknown", "contradicted"})
COST_CLASSIFICATIONS = frozenset({
    "MEASURED_FROM_EXISTING_EVIDENCE", "DERIVED", "ESTIMATED", "UNKNOWN",
    "PHYSICAL_TEST_REQUIRED",
})
DEPENDENCY_TYPES = frozenset({
    "must_exist", "must_be_qualified", "must_be_unlocked",
    "may_reuse_template", "may_spawn", "may_reward",
})
GATE_STATUSES = frozenset({"REQUIRED", "PENDING", "BLOCKED", "NOT_APPLICABLE"})
DECOMPOSITION_CATEGORIES = (
    "identity", "name_and_branding", "visual_presentation", "model", "texture",
    "animation", "audio", "registration", "recipe_or_acquisition", "item_use",
    "block_interaction", "entity_behavior", "navigation", "combat",
    "projectile_behavior", "event_subscriptions", "world_generation",
    "structure_layout", "loot", "spawn_rules", "progression",
    "state_ownership", "persistence", "migration", "multiplayer_behavior",
    "failure_handling", "cleanup", "dependencies", "performance_characteristics",
)
EXPRESSION_CATEGORIES = (
    "names", "logos", "character_identities", "models", "textures",
    "animations", "sounds", "lore", "localization", "structure_layouts",
    "reward_identities", "elite_staging", "progression_combinations",
)
PS4_DIMENSIONS = (
    "script_tick_workload", "active_entities", "pathfinding_pressure",
    "projectiles", "particles", "texture_memory", "geometry_complexity",
    "animation_controller_complexity", "persistence_growth",
    "multiplayer_multiplier", "cleanup_latency", "worst_credible_scene",
)
DIAGNOSTIC_REPORT_FILENAMES = (
    "forest-wave-1-evidence-inventory.json",
    "forest-wave-1-feature-decomposition.json",
    "forest-wave-1-transformation-plan.json",
    "forest-wave-1-expression-disposition.json",
    "forest-wave-1-dependency-graph.json",
    "forest-wave-1-rights-report.json",
    "forest-wave-1-runtime-architecture-plan.json",
    "forest-wave-1-ps4-cost-preview.json",
    "forest-wave-1-artifact-manifest-preview.json",
    "forest-wave-1-qualification-plan.json",
    "forest-wave-1-open-questions.json",
    "forest-wave-1-execution-readiness.json",
    "forest-wave-1-execution-manifest.json",
)
_SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_PROHIBITED_OUTPUT_PARTS = frozenset({
    "bedrock", "behavior_pack", "resource_pack", "worlds", "world_templates",
    "dist", "runtime", "data", "snapshots", "backups", "prototypes",
})


class DiagnosticError(ValueError):
    def __init__(self, code: str, message: str, findings: Sequence[Mapping[str, str]] = ()):
        super().__init__(message)
        self.code = code
        self.findings = tuple(dict(row) for row in findings)


def _finding(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_relative(path: str, *, output: bool = False) -> bool:
    if "\\" in path or "\x00" in path:
        return False
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        return False
    if output and any(part in _PROHIBITED_OUTPUT_PARTS for part in candidate.parts):
        return False
    return True


def _cycle(edges: Iterable[Mapping[str, Any]]) -> list[str]:
    graph: dict[str, list[str]] = {}
    for edge in edges:
        if edge.get("required") is True:
            graph.setdefault(str(edge["source"]), []).append(str(edge["target"]))
    visiting: set[str] = set()
    visited: set[str] = set()
    path: list[str] = []

    def visit(node: str) -> list[str]:
        if node in visiting:
            start = path.index(node)
            return [*path[start:], node]
        if node in visited:
            return []
        visiting.add(node)
        path.append(node)
        for target in sorted(graph.get(node, [])):
            found = visit(target)
            if found:
                return found
        path.pop()
        visiting.remove(node)
        visited.add(node)
        return []

    for node in sorted(graph):
        found = visit(node)
        if found:
            return found
    return []


def _report(report_type: str, wave_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    document = {
        "schema_version": "1.0.0",
        "report_type": report_type,
        "wave_id": wave_id,
        "diagnostic_only": True,
        "execution_not_authorized": True,
        **dict(payload),
    }
    document["record_hash"] = _hash(document)
    return document


def _validate_feature(feature: Mapping[str, Any], index: int, findings: list[dict[str, str]]) -> None:
    path = f"$.features[{index}]"
    feature_id = feature.get("feature_id")
    if not isinstance(feature_id, str) or not _SAFE_ID.fullmatch(feature_id):
        findings.append(_finding("INVALID_FEATURE_ID", f"{path}.feature_id", str(feature_id)))
    claims = feature.get("claims")
    if not isinstance(claims, list) or not claims:
        findings.append(_finding("CLAIMS_REQUIRED", f"{path}.claims", "non-empty claims required"))
    else:
        for claim_index, claim in enumerate(claims):
            claim_path = f"{path}.claims[{claim_index}]"
            if not isinstance(claim, Mapping) or claim.get("classification") not in CLAIM_STATES:
                findings.append(_finding("INVALID_CLAIM_CLASSIFICATION", claim_path, str(claim)))
            confidence = claim.get("confidence") if isinstance(claim, Mapping) else None
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                findings.append(_finding("INVALID_EVIDENCE_CONFIDENCE", f"{claim_path}.confidence", str(confidence)))
    parts = feature.get("parts")
    if not isinstance(parts, list):
        findings.append(_finding("DECOMPOSITION_REQUIRED", f"{path}.parts", "array required"))
        parts = []
    categories = {part.get("category") for part in parts if isinstance(part, Mapping)}
    for category in DECOMPOSITION_CATEGORIES:
        if category not in categories:
            findings.append(_finding("DECOMPOSITION_CATEGORY_MISSING", f"{path}.parts", category))
    for part_index, part in enumerate(parts):
        part_path = f"{path}.parts[{part_index}]"
        if not isinstance(part, Mapping):
            findings.append(_finding("INVALID_PART", part_path, "object required"))
            continue
        if part.get("disposition") not in TRANSFORMATION_DISPOSITIONS:
            findings.append(_finding("INVALID_TRANSFORMATION_DISPOSITION", f"{part_path}.disposition", str(part.get("disposition"))))
        for required in (
            "evidence_basis", "rights_basis", "bedrock_implementation",
            "fidelity_impact", "risks", "required_tests", "execution_may_proceed",
        ):
            if required not in part:
                findings.append(_finding("INCOMPLETE_TRANSFORMATION_PART", f"{part_path}.{required}", "required"))
    expressions = feature.get("expressions")
    if not isinstance(expressions, list):
        findings.append(_finding("EXPRESSION_CLASSIFICATION_REQUIRED", f"{path}.expressions", "array required"))
        expressions = []
    expression_categories = {row.get("category") for row in expressions if isinstance(row, Mapping)}
    for category in EXPRESSION_CATEGORIES:
        if category not in expression_categories:
            findings.append(_finding("EXPRESSION_CATEGORY_MISSING", f"{path}.expressions", category))
    for expression_index, expression in enumerate(expressions):
        expression_path = f"{path}.expressions[{expression_index}]"
        if not isinstance(expression, Mapping) or expression.get("disposition") not in EXPRESSION_DISPOSITIONS:
            findings.append(_finding("INVALID_EXPRESSION_DISPOSITION", expression_path, str(expression)))
    readiness = feature.get("readiness")
    if not isinstance(readiness, Mapping) or readiness.get("status") not in READINESS_STATUSES:
        findings.append(_finding("INVALID_READINESS_STATUS", f"{path}.readiness.status", str(readiness)))
    costs = feature.get("ps4_cost")
    if not isinstance(costs, Mapping):
        findings.append(_finding("PS4_COST_REQUIRED", f"{path}.ps4_cost", "object required"))
    else:
        for dimension in PS4_DIMENSIONS:
            cell = costs.get(dimension)
            if not isinstance(cell, Mapping):
                findings.append(_finding("PS4_DIMENSION_MISSING", f"{path}.ps4_cost.{dimension}", "object required"))
                continue
            value = cell.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                findings.append(_finding("INVALID_PS4_COST", f"{path}.ps4_cost.{dimension}.value", str(value)))
            if cell.get("classification") not in COST_CLASSIFICATIONS:
                findings.append(_finding("INVALID_COST_CLASSIFICATION", f"{path}.ps4_cost.{dimension}.classification", str(cell.get("classification"))))
    for artifact_index, artifact in enumerate(feature.get("artifacts", [])):
        artifact_path = f"{path}.artifacts[{artifact_index}].path"
        if not isinstance(artifact, Mapping) or not isinstance(artifact.get("path"), str) or not _safe_relative(str(artifact.get("path"))):
            findings.append(_finding("UNSAFE_ARTIFACT_PATH", artifact_path, str(artifact)))


def validate_diagnostic_spec(spec: Mapping[str, Any]) -> None:
    findings: list[dict[str, str]] = []
    if spec.get("schema_version") != "1.0.0":
        findings.append(_finding("UNSUPPORTED_SCHEMA", "$.schema_version", "must equal 1.0.0"))
    wave_id = spec.get("wave_id")
    if not isinstance(wave_id, str) or not _SAFE_ID.fullmatch(wave_id):
        findings.append(_finding("INVALID_WAVE_ID", "$.wave_id", str(wave_id)))
    features = spec.get("features")
    if not isinstance(features, list) or not features:
        findings.append(_finding("FEATURES_REQUIRED", "$.features", "non-empty array required"))
        features = []
    seen: set[str] = set()
    for index, feature in enumerate(features):
        if not isinstance(feature, Mapping):
            findings.append(_finding("INVALID_FEATURE", f"$.features[{index}]", "object required"))
            continue
        feature_id = str(feature.get("feature_id"))
        if feature_id in seen:
            findings.append(_finding("DUPLICATE_FEATURE_ID", f"$.features[{index}].feature_id", feature_id))
        seen.add(feature_id)
        _validate_feature(feature, index, findings)
    dependency_nodes = seen | {
        str(node) for node in spec.get("dependency_nodes", [])
        if isinstance(node, str)
    } | {"bramblehorn", "renewed_trail_loop"}
    edges = spec.get("dependencies")
    if not isinstance(edges, list):
        findings.append(_finding("DEPENDENCIES_REQUIRED", "$.dependencies", "array required"))
        edges = []
    for index, edge in enumerate(edges):
        path = f"$.dependencies[{index}]"
        if not isinstance(edge, Mapping) or edge.get("type") not in DEPENDENCY_TYPES:
            findings.append(_finding("INVALID_DEPENDENCY", path, str(edge)))
            continue
        if edge.get("source") not in dependency_nodes or edge.get("target") not in dependency_nodes:
            findings.append(_finding("UNKNOWN_DEPENDENCY_NODE", path, str(edge)))
    cycle = _cycle(edges)
    if cycle:
        findings.append(_finding("DEPENDENCY_CYCLE", "$.dependencies", " -> ".join(cycle)))
    for path in spec.get("diagnostic_output_paths", []):
        if not isinstance(path, str) or not _safe_relative(path, output=True) or not path.startswith("analysis/reconstruction-waves/"):
            findings.append(_finding("PRODUCTION_WRITE_PROHIBITED", "$.diagnostic_output_paths", str(path)))
    if spec.get("execution_authorized") is not False:
        findings.append(_finding("UNAUTHORIZED_EXECUTION", "$.execution_authorized", "must remain false"))
    if findings:
        raise DiagnosticError("DIAGNOSTIC_SPEC_INVALID", "diagnostic specification failed validation", findings)


def diagnose_reconstruction_wave(spec: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    validate_diagnostic_spec(spec)
    wave_id = str(spec["wave_id"])
    features = [dict(row) for row in spec["features"]]
    dependencies = [dict(row) for row in spec["dependencies"]]
    feature_ids = [str(row["feature_id"]) for row in features]

    evidence_inventory = _report("evidence_inventory", wave_id, {
        "repository_evidence_policy": dict(spec["evidence_policy"]),
        "features": [{
            "feature_id": row["feature_id"],
            "evidence": row["evidence"],
            "claims": row["claims"],
            "evidence_gaps": row["evidence_gaps"],
        } for row in features],
    })
    decomposition = _report("feature_decomposition", wave_id, {
        "features": [{"feature_id": row["feature_id"], "parts": row["parts"]} for row in features],
    })
    transformation = _report("transformation_plan", wave_id, {
        "features": [{
            "feature_id": row["feature_id"],
            "summary": row["transformation_summary"],
            "parts": row["parts"],
        } for row in features],
    })
    expressions = _report("expression_disposition", wave_id, {
        "consumer_boundary": "blocked source expression may not enter production-facing contracts",
        "features": [{"feature_id": row["feature_id"], "expressions": row["expressions"]} for row in features],
    })
    dependency_graph = _report("dependency_graph", wave_id, {
        "nodes": sorted(set(feature_ids) | {
            str(node) for node in spec.get("dependency_nodes", [])
        } | {"bramblehorn", "renewed_trail_loop"}),
        "edges": dependencies,
        "cycles": [],
        "cycle_check": "PASSED",
    })
    rights_report = _report("rights_report", wave_id, {
        "strategy": spec["rights_strategy"],
        "features": [{
            "feature_id": row["feature_id"],
            "rights_status": row["readiness"]["rights_status"],
            "materials": row["rights_materials"],
            "expression_summary": row["expressions"],
        } for row in features],
        "legal_clearance_implied": False,
    })
    runtime_plan = _report("runtime_architecture_plan", wave_id, {
        "stable_release_only": True,
        "preview_apis_allowed": False,
        "features": [{"feature_id": row["feature_id"], **row["runtime"]} for row in features],
    })

    hard_caps = dict(spec["ps4"]["hard_caps"])
    reserves = dict(spec["ps4"]["required_reserves"])
    totals: dict[str, int] = {}
    for dimension in PS4_DIMENSIONS:
        totals[dimension] = int(spec["ps4"]["bramblehorn_cost"][dimension]["value"]) + sum(
            int(row["ps4_cost"][dimension]["value"]) for row in features
        )
    upper_bound_exceedances = [
        {
            "dimension": dimension,
            "connected_wave_upper_bound": totals[dimension],
            "hard_cap": hard_caps[dimension],
            "required_reserve": reserves[dimension],
        }
        for dimension in PS4_DIMENSIONS
        if totals[dimension] + reserves[dimension] > hard_caps[dimension]
    ]
    connected_model_valid = spec["ps4"].get("connected_additive_model_valid") is True
    hard_cap_failures = upper_bound_exceedances if connected_model_valid else []
    ps4_preview = _report("ps4_cost_preview", wave_id, {
        "classification_notice": "uncalibrated planning proxy; physical testing required",
        "current_plan_total_units": spec["ps4"]["current_plan_total_units"],
        "planning_ceiling_units": spec["ps4"]["planning_ceiling_units"],
        "hard_ceiling_units": spec["ps4"]["hard_ceiling_units"],
        "protected_reserve_units": spec["ps4"]["protected_reserve_units"],
        "current_reserve_units": spec["ps4"]["current_reserve_units"],
        "reserve_consumption_proposed": False,
        "bramblehorn": spec["ps4"]["bramblehorn_cost"],
        "features": [{"feature_id": row["feature_id"], "dimensions": row["ps4_cost"]} for row in features],
        "connected_wave_upper_bound": totals,
        "hard_caps": hard_caps,
        "required_reserves": reserves,
        "hard_cap_failures": hard_cap_failures,
        "uncalibrated_upper_bound_exceedances": upper_bound_exceedances,
        "connected_additive_model_valid": connected_model_valid,
        "aggregation_remediation": spec["ps4"]["aggregation_remediation"],
        "reserve_after_expected_execution": "UNKNOWN_PENDING_CONCURRENCY_REDESIGN",
        "physical_ps4_compatibility_claimed": False,
    })
    artifact_preview = _report("artifact_manifest_preview", wave_id, {
        "preview_only": True,
        "files_created_during_diagnosis": [],
        "features": [{"feature_id": row["feature_id"], "artifacts": row["artifacts"]} for row in features],
        "protected_custom_regions": list(spec["protected_custom_regions"]),
        "collision_policy": "fail on identifier or path collision",
    })
    qualification_plan = _report("qualification_plan", wave_id, {
        "creator_tools_rerun_required_now": False,
        "bds_rerun_required_now": False,
        "features": [{"feature_id": row["feature_id"], "checks": row["qualification"]} for row in features],
        "connected_wave_checks": list(spec["connected_wave_checks"]),
        "physical_pending": list(spec["physical_checks"]),
    })
    open_questions = _report("open_questions", wave_id, {
        "questions": [
            {"feature_id": row["feature_id"], "questions": row["open_questions"]}
            for row in features
        ],
    })
    readiness_rows = [{
        "feature_id": row["feature_id"],
        **row["readiness"],
        "proposed_transformation_summary": row["transformation_summary"],
        "estimated_planning_cost": row["ps4_cost"],
        "qualification_requirements": row["qualification"],
    } for row in features]
    aggregate_status = "PS4_BUDGET_BLOCKED" if hard_cap_failures else (
        "MORE_EVIDENCE_REQUIRED"
        if any(row["status"] == "MORE_EVIDENCE_REQUIRED" for row in readiness_rows)
        else "READY_WITH_REDESIGN"
    )
    readiness = _report("execution_readiness", wave_id, {
        "features": readiness_rows,
        "aggregate": {
            "status": aggregate_status,
            "blocking_findings": [
                "authorized Java evidence is absent for all six selected reconstruction features",
                *(
                    ["conservative connected-wave upper bound violates PS4 planning hard caps or reserves"]
                    if hard_cap_failures else []
                ),
            ],
            "autonomous_production_may_proceed": False,
            "execution_authorized": False,
        },
    })
    execution_manifest = _report("execution_manifest", wave_id, {
        "execution_authorized": False,
        "authorization_is_immutable_in_diagnostic_operation": True,
        "authorized_features": [],
        "blocked_or_deferred_features": feature_ids,
        "transformation_dispositions": {
            row["feature_id"]: {
                part["category"]: part["disposition"] for part in row["parts"]
            } for row in features
        },
        "original_assets_to_generate": {
            row["feature_id"]: [
                artifact["path"] for artifact in row["artifacts"]
                if artifact["ownership"] == "AUTHORED_ORIGINAL"
            ] for row in features
        },
        "behavior_and_script_systems": {
            row["feature_id"]: row["runtime"]["planned_systems"] for row in features
        },
        "structures_to_create": [
            artifact["path"] for row in features for artifact in row["artifacts"]
            if artifact["kind"] == "structure"
        ],
        "files_to_create": [
            artifact["path"] for row in features for artifact in row["artifacts"]
            if artifact["action"] == "CREATE"
        ],
        "files_to_modify": [
            artifact["path"] for row in features for artifact in row["artifacts"]
            if artifact["action"] == "MODIFY"
        ],
        "protected_custom_regions": list(spec["protected_custom_regions"]),
        "planned_blockbench_operations": spec["planned_blockbench_operations"],
        "planned_cost": {
            "connected_wave_upper_bound": totals,
            "hard_cap_failures": hard_cap_failures,
            "reserve_consumption_proposed": False,
        },
        "planned_tests": list(spec["connected_wave_checks"]),
        "known_limitations": list(spec["known_limitations"]),
        "rights_restrictions": list(spec["rights_restrictions"]),
        "rollback_point": spec["rollback_point"],
        "expected_package_outputs": list(spec["expected_package_outputs"]),
        "maximum_autonomous_repair_iterations": int(spec["maximum_autonomous_repair_iterations"]),
        "stop_conditions": list(spec["stop_conditions"]),
        "failure_conditions": list(spec["failure_conditions"]),
        "physical_checks_remaining": list(spec["physical_checks"]),
    })
    reports = {
        DIAGNOSTIC_REPORT_FILENAMES[0]: evidence_inventory,
        DIAGNOSTIC_REPORT_FILENAMES[1]: decomposition,
        DIAGNOSTIC_REPORT_FILENAMES[2]: transformation,
        DIAGNOSTIC_REPORT_FILENAMES[3]: expressions,
        DIAGNOSTIC_REPORT_FILENAMES[4]: dependency_graph,
        DIAGNOSTIC_REPORT_FILENAMES[5]: rights_report,
        DIAGNOSTIC_REPORT_FILENAMES[6]: runtime_plan,
        DIAGNOSTIC_REPORT_FILENAMES[7]: ps4_preview,
        DIAGNOSTIC_REPORT_FILENAMES[8]: artifact_preview,
        DIAGNOSTIC_REPORT_FILENAMES[9]: qualification_plan,
        DIAGNOSTIC_REPORT_FILENAMES[10]: open_questions,
        DIAGNOSTIC_REPORT_FILENAMES[11]: readiness,
        DIAGNOSTIC_REPORT_FILENAMES[12]: execution_manifest,
    }
    validate_diagnostic_bundle(reports)
    return reports


def validate_diagnostic_bundle(reports: Mapping[str, Mapping[str, Any]]) -> None:
    findings: list[dict[str, str]] = []
    if set(reports) != set(DIAGNOSTIC_REPORT_FILENAMES):
        findings.append(_finding("INCOMPLETE_DIAGNOSTIC_BUNDLE", "$", "required report set mismatch"))
    for filename, report in reports.items():
        if report.get("schema_version") != "1.0.0":
            findings.append(_finding("UNSUPPORTED_SCHEMA", filename, "must equal 1.0.0"))
        if report.get("diagnostic_only") is not True or report.get("execution_not_authorized") is not True:
            findings.append(_finding("DIAGNOSTIC_BOUNDARY_MISSING", filename, "diagnostic-only markers required"))
        expected_hash = report.get("record_hash")
        unhashed = {key: value for key, value in report.items() if key != "record_hash"}
        if expected_hash != _hash(unhashed):
            findings.append(_finding("RECORD_HASH_MISMATCH", filename, str(expected_hash)))
        serialized = json.dumps(report, sort_keys=True)
        if filename == "forest-wave-1-execution-manifest.json" and '"execution_authorized": false' not in serialized:
            findings.append(_finding("UNAUTHORIZED_EXECUTION", filename, "manifest must default false"))
    if findings:
        raise DiagnosticError("DIAGNOSTIC_BUNDLE_INVALID", "diagnostic bundle failed validation", findings)
