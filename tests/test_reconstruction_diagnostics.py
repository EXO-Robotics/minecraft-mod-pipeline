from __future__ import annotations

from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import pytest

from mccompiler.cli import main
from mccompiler.distillation.validation import validate_with_schema
from mccompiler.operations.registry import OperationRegistry
from mccompiler.reconstruction import (
    DIAGNOSTIC_REPORT_FILENAMES,
    DiagnosticError,
    diagnose_reconstruction_wave,
    validate_diagnostic_bundle,
)
from mccompiler.reconstruction.diagnostics import (
    DECOMPOSITION_CATEGORIES,
    EXPRESSION_CATEGORIES,
    PS4_DIMENSIONS,
)
from mccompiler.reconstruction.forest_wave_1 import (
    build_forest_wave_1_spec,
    render_forest_wave_1_diagnosis,
)


ROOT = Path(__file__).parents[1]
PLAN = Path("production/planning/controlled-chaos-forest/controlled-chaos-forest-production-plan.json")


def spec() -> dict[str, object]:
    return build_forest_wave_1_spec(ROOT)


def codes(exc: DiagnosticError) -> set[str]:
    return {row["code"] for row in exc.findings}


def make_repo(target: Path) -> Path:
    target.mkdir(parents=True)
    (target / "pyproject.toml").write_text("[project]\nname='diagnostic-fixture'\nversion='1.0.0'\n", encoding="utf-8")
    (target / "src/mccompiler").mkdir(parents=True)
    plan_target = target / PLAN
    plan_target.parent.mkdir(parents=True)
    shutil.copy2(ROOT / PLAN, plan_target)
    (target / "production/sentinel").write_text("unchanged\n", encoding="utf-8")
    (target / "prototypes/blockbench").mkdir(parents=True)
    (target / "prototypes/blockbench/user.bbmodel").write_text("user-owned\n", encoding="utf-8")
    return target


def tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    if not path.exists():
        return digest.hexdigest()
    for child in sorted(row for row in path.rglob("*") if row.is_file()):
        digest.update(str(child.relative_to(path)).encode())
        digest.update(child.read_bytes())
    return digest.hexdigest()


def test_checked_in_spec_has_complete_decomposition_and_expression_coverage() -> None:
    raw = spec()
    assert [row["feature_id"] for row in raw["features"]] == [
        "mossback_forager", "resonance_sling", "signal_ruin",
        "thornwarden_elite", "forest_attunement", "sporefall_event",
    ]
    for feature in raw["features"]:
        assert {row["category"] for row in feature["parts"]} == set(DECOMPOSITION_CATEGORIES)
        assert {row["category"] for row in feature["expressions"]} == set(EXPRESSION_CATEGORIES)
        assert set(feature["ps4_cost"]) == set(PS4_DIMENSIONS)
        assert feature["readiness"]["autonomous_production_may_proceed"] is False


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("disposition", "COPY_JAVA", "INVALID_TRANSFORMATION_DISPOSITION"),
        ("readiness", "ALMOST_READY", "INVALID_READINESS_STATUS"),
        ("confidence", 2.0, "INVALID_EVIDENCE_CONFIDENCE"),
    ],
)
def test_invalid_enums_and_confidence_fail_closed(field: str, value: object, expected: str) -> None:
    raw = deepcopy(spec())
    if field == "disposition":
        raw["features"][0]["parts"][0]["disposition"] = value
    elif field == "readiness":
        raw["features"][0]["readiness"]["status"] = value
    else:
        raw["features"][0]["claims"][0]["confidence"] = value
    with pytest.raises(DiagnosticError) as caught:
        diagnose_reconstruction_wave(raw)
    assert expected in codes(caught.value)


def test_contradictory_evidence_is_retained_as_auditable_claim_state() -> None:
    raw = deepcopy(spec())
    raw["features"][0]["claims"][0]["classification"] = "contradicted"
    reports = diagnose_reconstruction_wave(raw)
    claims = reports["forest-wave-1-evidence-inventory.json"]["features"][0]["claims"]
    assert claims[0]["classification"] == "contradicted"


def test_missing_evidence_drives_all_features_to_more_evidence_required() -> None:
    reports = diagnose_reconstruction_wave(spec())
    inventory = reports["forest-wave-1-evidence-inventory.json"]
    assert inventory["repository_evidence_policy"]["authorized_java_evidence_found"] is False
    readiness = reports["forest-wave-1-execution-readiness.json"]
    assert {row["status"] for row in readiness["features"]} == {"MORE_EVIDENCE_REQUIRED"}
    assert readiness["aggregate"]["status"] == "MORE_EVIDENCE_REQUIRED"
    assert readiness["aggregate"]["autonomous_production_may_proceed"] is False


def test_rights_blocked_and_clean_room_expression_dispositions_are_separate() -> None:
    reports = diagnose_reconstruction_wave(spec())
    rights = reports["forest-wave-1-rights-report.json"]
    assert all(row["rights_status"] == "UNREGISTERED_SOURCE_MATERIALS" for row in rights["features"])
    expressions = reports["forest-wave-1-expression-disposition.json"]
    dispositions = {
        item["disposition"]
        for feature in expressions["features"] for item in feature["expressions"]
    }
    assert "CLEAN_ROOM_REPLACEMENT" in dispositions
    assert "ABSTRACT_PATTERN_RETAINED" in dispositions
    assert "LICENSED_REUSE" not in dispositions


def test_unsupported_bedrock_mapping_is_valid_but_non_executable() -> None:
    raw = deepcopy(spec())
    part = raw["features"][0]["parts"][0]
    part["disposition"] = "UNSUPPORTED"
    part["execution_may_proceed"] = False
    reports = diagnose_reconstruction_wave(raw)
    output = reports["forest-wave-1-transformation-plan.json"]
    assert output["features"][0]["parts"][0]["disposition"] == "UNSUPPORTED"


def test_required_dependency_cycle_is_rejected() -> None:
    raw = deepcopy(spec())
    raw["dependencies"].append({
        "source": "signal_ruin",
        "target": "thornwarden_elite",
        "type": "must_exist",
        "required": True,
        "dimensions": ["runtime"],
        "failure_behavior": "blocked",
    })
    with pytest.raises(DiagnosticError) as caught:
        diagnose_reconstruction_wave(raw)
    assert "DEPENDENCY_CYCLE" in codes(caught.value)


@pytest.mark.parametrize(
    "path",
    [
        "../escape.json",
        "/absolute/path.json",
        "bedrock\\behavior_pack\\bad.json",
        "bedrock/behavior_pack/bad\u0000.json",
    ],
)
def test_artifact_manifest_rejects_unsafe_paths(path: str) -> None:
    raw = deepcopy(spec())
    raw["features"][0]["artifacts"][0]["path"] = path
    with pytest.raises(DiagnosticError) as caught:
        diagnose_reconstruction_wave(raw)
    assert "UNSAFE_ARTIFACT_PATH" in codes(caught.value)


@pytest.mark.parametrize(
    "path",
    [
        "production/reconstruction-waves/forest-wave-1/bad.json",
        "data/worlds/bad.json",
        "snapshots/bad.json",
        "backups/bad.json",
        "analysis/reconstruction-waves/../escape.json",
    ],
)
def test_diagnostic_output_rejects_production_and_active_world_roots(path: str) -> None:
    raw = deepcopy(spec())
    raw["diagnostic_output_paths"][0] = path
    with pytest.raises(DiagnosticError) as caught:
        diagnose_reconstruction_wave(raw)
    assert "PRODUCTION_WRITE_PROHIBITED" in codes(caught.value)


def test_valid_connected_hard_cap_failure_blocks_readiness() -> None:
    raw = deepcopy(spec())
    raw["ps4"]["connected_additive_model_valid"] = True
    reports = diagnose_reconstruction_wave(raw)
    costs = reports["forest-wave-1-ps4-cost-preview.json"]
    assert costs["hard_cap_failures"]
    readiness = reports["forest-wave-1-execution-readiness.json"]
    assert readiness["aggregate"]["status"] == "PS4_BUDGET_BLOCKED"


def test_current_scope_is_not_double_charged_and_reserve_is_protected() -> None:
    reports = diagnose_reconstruction_wave(spec())
    costs = reports["forest-wave-1-ps4-cost-preview.json"]
    assert costs["current_plan_total_units"] == 62
    assert costs["planning_ceiling_units"] == 64
    assert costs["protected_reserve_units"] == 16
    assert costs["current_reserve_units"] == 18
    assert costs["reserve_consumption_proposed"] is False
    assert costs["reserve_after_expected_execution"] == "UNKNOWN_PENDING_CONCURRENCY_REDESIGN"
    assert costs["hard_cap_failures"] == []
    assert costs["uncalibrated_upper_bound_exceedances"]


def test_execution_manifest_is_immutable_false_and_complete() -> None:
    reports = diagnose_reconstruction_wave(spec())
    manifest = reports["forest-wave-1-execution-manifest.json"]
    assert manifest["execution_authorized"] is False
    assert manifest["authorization_is_immutable_in_diagnostic_operation"] is True
    assert manifest["authorized_features"] == []
    assert len(manifest["blocked_or_deferred_features"]) == 6
    assert manifest["maximum_autonomous_repair_iterations"] == 3
    assert manifest["files_to_create"]
    assert manifest["planned_blockbench_operations"]
    assert manifest["physical_checks_remaining"]


def test_unauthorized_execution_request_is_rejected_before_writes() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repo = make_repo(Path(temporary) / "repo")
        response = OperationRegistry().execute({
            "schema_version": "1.0.0",
            "request_id": "unauthorized",
            "operation": "diagnose_reconstruction_wave",
            "project": str(repo),
            "parameters": {"dry_run": True, "execution_authorized": True},
        })
        assert not response["ok"]
        assert response["diagnostics"][0]["code"] == "UNAUTHORIZED_EXECUTION"
        assert not (repo / "analysis/reconstruction-waves/forest-wave-1").exists()


def test_operation_requires_dry_run() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repo = make_repo(Path(temporary) / "repo")
        response = OperationRegistry().execute({
            "schema_version": "1.0.0",
            "request_id": "missing-dry-run",
            "operation": "diagnose_reconstruction_wave",
            "project": str(repo),
            "parameters": {},
        })
        assert not response["ok"]
        assert response["diagnostics"][0]["code"] == "DRY_RUN_REQUIRED"


def test_integration_renders_only_diagnostics_and_preserves_forbidden_trees() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repo = make_repo(Path(temporary) / "repo")
        before = {
            "production": tree_hash(repo / "production"),
            "prototypes": tree_hash(repo / "prototypes"),
        }
        reports, paths = render_forest_wave_1_diagnosis(repo)
        repo = repo.resolve()
        assert set(reports) == set(DIAGNOSTIC_REPORT_FILENAMES)
        assert len(paths) == 14
        assert all(
            path.is_relative_to(repo / "analysis") or path.is_relative_to(repo / "docs")
            for path in paths
        )
        assert before == {
            "production": tree_hash(repo / "production"),
            "prototypes": tree_hash(repo / "prototypes"),
        }
        preview = reports["forest-wave-1-artifact-manifest-preview.json"]
        assert preview["files_created_during_diagnosis"] == []
        for feature in preview["features"]:
            for artifact in feature["artifacts"]:
                assert not (repo / artifact["path"]).exists()
        assert not list(repo.rglob("*.mcaddon"))
        assert not list(repo.rglob("*.mcworld"))
        assert not list(repo.rglob("*.mcstructure"))


def test_operation_returns_diagnostic_markers_and_blocking_success() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repo = make_repo(Path(temporary) / "repo")
        response = OperationRegistry().execute({
            "schema_version": "1.0.0",
            "request_id": "diagnose",
            "operation": "diagnose_reconstruction_wave",
            "project": str(repo),
            "parameters": {"dry_run": True},
        })
        assert response["ok"], response
        assert response["project_revision"] is None
        assert response["result"]["mode"] == "DIAGNOSTIC_ONLY"
        assert response["result"]["execution_status"] == "EXECUTION_NOT_AUTHORIZED"
        assert response["result"]["execution_authorized"] is False
        assert response["result"]["blocking"] is True
        assert response["result"]["production_writes"] == 0
        assert response["result"]["runtime_mutations"] == 0
        assert len(response["artifacts"]) == 14


def test_cli_human_and_json_modes_return_readiness_exit_code_three() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repo = make_repo(Path(temporary) / "repo")
        human = StringIO()
        with redirect_stdout(human):
            human_code = main([
                "diagnose-reconstruction-wave", "--project", str(repo), "--dry-run",
            ])
        assert human_code == 3
        assert "DIAGNOSTIC_ONLY" in human.getvalue()
        assert "EXECUTION_NOT_AUTHORIZED" in human.getvalue()
        machine = StringIO()
        with redirect_stdout(machine):
            machine_code = main([
                "diagnose-reconstruction-wave", "--project", str(repo), "--dry-run", "--json",
            ])
        assert machine_code == 3
        response = json.loads(machine.getvalue())
        assert response["ok"]
        assert response["result"]["execution_authorized"] is False


def test_repeated_runs_are_byte_identical_despite_request_identity() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        left = make_repo(Path(temporary) / "left")
        right = make_repo(Path(temporary) / "right")
        left_reports, left_paths = render_forest_wave_1_diagnosis(left)
        right_reports, right_paths = render_forest_wave_1_diagnosis(right)
        left = left.resolve()
        right = right.resolve()
        validate_diagnostic_bundle(left_reports)
        validate_diagnostic_bundle(right_reports)
        left_bytes = {
            path.relative_to(left): path.read_bytes() for path in left_paths
        }
        right_bytes = {
            path.relative_to(right): path.read_bytes() for path in right_paths
        }
        assert left_bytes == right_bytes


def test_checked_in_reports_match_the_pure_diagnostic_engine() -> None:
    expected = diagnose_reconstruction_wave(spec())
    output = ROOT / "analysis/reconstruction-waves/forest-wave-1"
    for filename in DIAGNOSTIC_REPORT_FILENAMES:
        assert json.loads((output / filename).read_text(encoding="utf-8")) == expected[filename]


def test_schema_documents_and_report_envelopes_parse() -> None:
    schema_names = (
        "reconstruction-diagnostic-report-1.0.0.json",
        "reconstruction-execution-manifest-1.0.0.json",
    )
    for name in schema_names:
        schema = json.loads((ROOT / "src/mccompiler/schemas" / name).read_text())
        assert schema["$schema"].endswith("2020-12/schema")
    for filename in DIAGNOSTIC_REPORT_FILENAMES:
        report = json.loads(
            (ROOT / "analysis/reconstruction-waves/forest-wave-1" / filename).read_text()
        )
        envelope = json.loads(
            (ROOT / "src/mccompiler/schemas/reconstruction-diagnostic-report-1.0.0.json").read_text()
        )
        assert validate_with_schema(report, envelope) == []
        assert report["schema_version"] == "1.0.0"
        assert report["diagnostic_only"] is True
        assert report["execution_not_authorized"] is True
    manifest = json.loads(
        (ROOT / "analysis/reconstruction-waves/forest-wave-1/forest-wave-1-execution-manifest.json").read_text()
    )
    manifest_schema = json.loads(
        (ROOT / "src/mccompiler/schemas/reconstruction-execution-manifest-1.0.0.json").read_text()
    )
    assert validate_with_schema(manifest, manifest_schema) == []
