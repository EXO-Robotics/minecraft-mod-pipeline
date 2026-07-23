from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from mccompiler.distillation import DistillationError, distill_modpack
from mccompiler.distillation.model import (
    FEASIBILITY_DIMENSIONS,
    NEGATIVE_DIMENSIONS,
    POSITIVE_DIMENSIONS,
    RIGHTS_DIMENSIONS,
)
from mccompiler.distillation.validation import schema_contracts, validate_distillation_output
from mccompiler.distillation.selector import classify_strategy, select_scope
from mccompiler.operations.registry import REQUIRED_OPERATION_CATALOG, OperationRegistry, execute_request
from mccompiler.project.store import ProjectStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/fictional_large_modpack"
INPUT = FIXTURE / "distillation-input.json"
ADJUSTMENTS = FIXTURE / "review-adjustments.json"
REQUIRED_SELECTED = {
    "odd_survival",
    "regional_ecology",
    "relic_ruins",
    "elite_hunts",
    "forge_colossus",
    "chaos_nexus",
    "postgame_mutators",
}


def _files(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted((root / "distillation").iterdir())
        if path.is_file()
    }


def test_fictional_selector_preserves_identity_progression_and_constraints(tmp_path: Path) -> None:
    result = distill_modpack(INPUT, tmp_path)
    selection = result["selection"]
    assert set(selection["ids"]) == REQUIRED_SELECTED
    assert selection["progression_complete"]
    assert selection["effort_units"] <= selection["effort_limit_units"]
    assert selection["console_cost_units"] <= result["console_limit_units"]
    assert not selection["missing_core_categories"]
    assert validate_distillation_output(tmp_path) == []


def test_filler_duplicates_expensive_and_rights_blocked_content_are_not_selected(tmp_path: Path) -> None:
    result = distill_modpack(INPUT, tmp_path)
    selected = set(result["selection"]["ids"])
    assert "filler_decor" not in selected
    assert "duplicate_weapons" not in selected
    assert "cinematic_renderer" not in selected
    assert "vehicle_dimension" not in selected
    assert result["decisions"]["restricted_crossover"]["classification"] == "RIGHTS_BLOCKED"
    assert result["decisions"]["cinematic_renderer"]["classification"] == "UNSUPPORTED"
    assert all(result["decisions"][identifier]["reasons"] for identifier in result["decisions"])


def test_prerequisite_chain_is_closed(tmp_path: Path) -> None:
    result = distill_modpack(INPUT, tmp_path)
    systems = {row["id"]: row for row in result["systems"]}
    selected = set(result["selection"]["ids"])
    assert all(set(systems[identifier].get("prerequisites", [])) <= selected for identifier in selected)


def test_reports_are_byte_deterministic_and_input_order_independent(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    reordered_path = tmp_path / "reordered.json"
    document = json.loads(INPUT.read_text(encoding="utf-8"))
    document["systems"] = list(reversed(document["systems"]))
    reordered_path.write_text(json.dumps(document, indent=1), encoding="utf-8")
    first_result = distill_modpack(INPUT, first)
    second_result = distill_modpack(reordered_path, second)
    assert first_result["result_digest"] == second_result["result_digest"]
    assert _files(first) == _files(second)


def test_large_inventory_search_finds_complete_progression_instead_of_greedy_filler() -> None:
    clear_rights = {
        name: {"status": "KNOWN", "value": 0 if name == "branding_trademark_risk" else 100, "evidence": ["synthetic selector test"]}
        for name in RIGHTS_DIMENSIONS
    }
    systems = []
    scores = []
    for index in range(19):
        identifier = f"filler-{index:02d}"
        systems.append({
            "id": identifier, "effort_units": 1, "console_cost_units": 1,
            "strategy": "DIRECT_RECONSTRUCTION", "stable_api_status": "COMPATIBLE",
            "dimensions": clear_rights, "prerequisites": [], "progression_stages": [], "categories": [],
        })
        scores.append({"system_id": identifier, "raw_score_milli": 1000})
    systems.extend([
        {
            "id": "stage-one", "effort_units": 1, "console_cost_units": 1,
            "strategy": "DIRECT_RECONSTRUCTION", "stable_api_status": "COMPATIBLE",
            "dimensions": clear_rights, "prerequisites": [], "progression_stages": ["one"], "categories": [],
        },
        {
            "id": "stage-two", "effort_units": 1, "console_cost_units": 1,
            "strategy": "DIRECT_RECONSTRUCTION", "stable_api_status": "COMPATIBLE",
            "dimensions": clear_rights, "prerequisites": ["stage-one"], "progression_stages": ["two"], "categories": [],
        },
    ])
    scores.extend([
        {"system_id": "stage-one", "raw_score_milli": 1},
        {"system_id": "stage-two", "raw_score_milli": 1},
    ])
    selected = select_scope(systems, scores, 1000, 2, ["one", "two"])
    assert selected["progression_complete"]
    assert selected["ids"] == ["stage-one", "stage-two"]


def test_redesign_with_unknown_rights_requires_originality_evidence() -> None:
    unknown = {name: {"status": "UNKNOWN"} for name in RIGHTS_DIMENSIONS}
    blocked, reasons = classify_strategy({
        "strategy": "BEDROCK_NATIVE_REDESIGN",
        "stable_api_status": "COMPATIBLE",
        "dimensions": unknown,
    })
    assert blocked == "RIGHTS_BLOCKED"
    assert reasons
    allowed, allowed_reasons = classify_strategy({
        "strategy": "ORIGINAL_REPLACEMENT",
        "stable_api_status": "COMPATIBLE",
        "dimensions": unknown,
        "original_content": True,
        "originality_evidence": ["original design brief"],
    })
    assert allowed == "ORIGINAL_REPLACEMENT"
    assert allowed_reasons
    deferred, stable_reasons = classify_strategy({
        "strategy": "ORIGINAL_REPLACEMENT",
        "stable_api_status": "UNKNOWN",
        "dimensions": unknown,
        "original_content": True,
        "originality_evidence": ["original design brief"],
    })
    assert deferred == "DEFER"
    assert stable_reasons


def test_review_adjustments_remain_separate_from_deterministic_scores(tmp_path: Path) -> None:
    base = distill_modpack(INPUT, tmp_path / "base")
    reviewed = distill_modpack(INPUT, tmp_path / "reviewed", review_adjustments=ADJUSTMENTS)
    assert base["scores"] == reviewed["scores"]
    assert base["selection"] == reviewed["selection"]
    assert reviewed["review_adjustments_applied"]
    assert reviewed["reviewed_selection"]["status"] == "SEPARATE_REVIEW_ONLY_NOT_DETERMINISTIC_SCORE"
    assert base["result_digest"] != reviewed["result_digest"]
    review_artifact = tmp_path / "reviewed/distillation/review-adjustments.json"
    assert json.loads(review_artifact.read_text())["adjustments"][0]["author"] == "fixture-review-agent"


def test_unknown_evidence_cannot_improve_score_or_clear_rights(tmp_path: Path) -> None:
    result = distill_modpack(INPUT, tmp_path)
    score = next(row for row in result["scores"] if row["system_id"] == "restricted_crossover")
    assert score["dimensions"]["asset_license_clarity"] == {"status": "UNKNOWN", "value": 0}
    assert any("asset_license_clarity" in gap for gap in score["evidence_gaps"])
    assert result["decisions"]["restricted_crossover"]["classification"] == "RIGHTS_BLOCKED"


def test_invalid_budget_and_dangling_dependencies_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(DistillationError, match="effort budget"):
        distill_modpack(INPUT, tmp_path / "budget", effort_budget_basis_points=0)
    document = json.loads(INPUT.read_text(encoding="utf-8"))
    document["systems"][0]["prerequisites"] = ["does-not-exist"]
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(DistillationError, match="dangling prerequisites"):
        distill_modpack(invalid, tmp_path / "dangling")


def test_cycles_schema_violations_and_output_symlinks_fail_closed(tmp_path: Path) -> None:
    document = json.loads(INPUT.read_text(encoding="utf-8"))
    document["console_limit_units"] = 0
    invalid = tmp_path / "schema-invalid.json"
    invalid.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(DistillationError, match="schema"):
        distill_modpack(invalid, tmp_path / "invalid-output")
    document = json.loads(INPUT.read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in document["systems"]}
    by_id["odd_survival"]["prerequisites"] = ["postgame_mutators"]
    by_id["postgame_mutators"]["unlocks"] = ["odd_survival"]
    cyclic = tmp_path / "cyclic.json"
    cyclic.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(DistillationError, match="cycle"):
        distill_modpack(cyclic, tmp_path / "cycle-output")
    output = tmp_path / "symlink-output"
    outside = tmp_path / "outside"
    output.mkdir()
    outside.mkdir()
    (output / "distillation").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        distill_modpack(INPUT, output)


def test_raw_mod_input_is_scanned_clustered_and_reported_without_false_completion(tmp_path: Path) -> None:
    result = distill_modpack(ROOT / "tests/fixtures/representative_mod", tmp_path)
    assert result["analysis_status"] == "PRELIMINARY_EVIDENCE_GAPS"
    assert result["systems"]
    assert not result["selection"]["progression_complete"]
    assert validate_distillation_output(tmp_path, require_complete=False) == []
    completed = subprocess.run(
        [
            sys.executable, "-m", "mccompiler", "distill-modpack",
            "--input", str(ROOT / "tests/fixtures/representative_mod"),
            "--output", str(tmp_path / "cli"),
        ],
        cwd=ROOT,
        env={"PYTHONPATH": f"{ROOT}:{ROOT / 'src'}"},
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1, completed.stderr
    assert json.loads(completed.stdout)["missing_progression_stages"]


def test_all_scoring_dimensions_and_schema_contracts_are_present() -> None:
    document = json.loads(INPUT.read_text(encoding="utf-8"))
    expected = set(POSITIVE_DIMENSIONS + FEASIBILITY_DIMENSIONS + RIGHTS_DIMENSIONS + NEGATIVE_DIMENSIONS)
    assert set(document["default_dimensions"]) == expected
    contracts = schema_contracts()
    assert set(contracts) == {
        "distillation-input-1.0.0.json",
        "distillation-scoring-1.0.0.json",
        "distillation-output-1.0.0.json",
        "distillation-review-adjustments-1.0.0.json",
    }
    assert all(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema" for schema in contracts.values())


def test_cli_generates_complete_machine_readable_summary(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "mccompiler",
            "distill-modpack",
            "--input",
            str(FIXTURE),
            "--target",
            "MARKETPLACE_ADDON_STABLE",
            "--effort-budget",
            "0.25",
            "--output",
            str(tmp_path),
        ],
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src")},
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary["ok"]
    assert set(summary["selected_systems"]) == REQUIRED_SELECTED
    assert len(summary["artifacts"]) == 15


def test_distillation_agent_operations_are_registered_and_project_bound(tmp_path: Path) -> None:
    expected = {
        "analyze_modpack_identity",
        "cluster_gameplay_systems",
        "score_feature_value",
        "estimate_conversion_effort",
        "estimate_console_cost",
        "estimate_pattern_reuse",
        "identify_progression_dependencies",
        "select_quarter_scope",
        "explain_selection",
        "generate_conversion_roadmap",
        "record_distillation_adjustment",
    }
    registry = OperationRegistry()
    assert set(REQUIRED_OPERATION_CATALOG["distillation"]) == expected
    assert expected <= set(registry.handlers)
    store = ProjectStore.create(tmp_path / "project")
    store.write("analysis/distillation-input.json", json.loads(INPUT.read_text(encoding="utf-8")))
    response = execute_request({
        "schema_version": "1.0.0",
        "request_id": "distill-test",
        "operation": "select_quarter_scope",
        "project": str(store.root),
        "parameters": {"effort_budget_basis_points": 2500},
        "expected_revision": store.revision,
    })
    assert response["ok"], response
    assert (store.root / "distillation/executive-summary.md").read_text().startswith("# Executive summary")
    assert validate_distillation_output(store.root) == []


def test_agent_review_adjustment_is_advisory_and_cannot_clear_marketplace(tmp_path: Path) -> None:
    store = ProjectStore.create(tmp_path / "project")
    request = {
        "schema_version": "1.0.0",
        "request_id": "adjustment-test",
        "operation": "record_distillation_adjustment",
        "project": str(store.root),
        "parameters": {
            "id": "a1",
            "author": "review-agent",
            "author_type": "AI",
            "reason": "Compare build orders.",
            "evidence": ["review note"],
            "change": {"kind": "selection", "prior": "defer", "replacement": "review_candidate"},
        },
        "expected_revision": store.revision,
    }
    response = execute_request(request)
    assert response["ok"]
    saved = store.read("decisions/distillation/review-adjustments.json")
    assert saved["adjustments"][0]["authority"] == "ADVISORY_ONLY"
    request["expected_revision"] = store.revision
    request["parameters"]["id"] = "a2"
    request["parameters"]["change"]["replacement"] = "MARKETPLACE_CLEARED"
    rejected = execute_request(request)
    assert not rejected["ok"]
    assert rejected["diagnostics"][0]["code"] == "RIGHTS_AUTHORITY_REQUIRED"
    store.write("analysis/distillation-input.json", json.loads(INPUT.read_text(encoding="utf-8")))
    rerun = execute_request({
        "schema_version": "1.0.0",
        "request_id": "review-consumption",
        "operation": "select_quarter_scope",
        "project": str(store.root),
        "parameters": {"effort_budget_basis_points": 2500},
        "expected_revision": store.revision,
    })
    assert rerun["ok"], rerun
    persisted_review = json.loads((store.root / "distillation/review-adjustments.json").read_text())
    assert persisted_review["adjustments"][0]["id"] == "a1"


def test_skill_structure_and_references_are_valid() -> None:
    skill = ROOT / "skills/crazycraft-quarter-distillation"
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\nname: crazycraft-quarter-distillation\ndescription:")
    assert text.split("---", 2)[1].count("\nname:") == 1
    assert "\nmetadata:" not in text.split("---", 2)[1]
    assert "TODO" not in text
    for name in (
        "methodology.md",
        "scoring.md",
        "output-contract.md",
        "reconstruction-patterns.md",
        "rights-and-originality.md",
    ):
        assert (skill / "references" / name).is_file()
        assert f"references/{name}" in text
    metadata = (skill / "agents/openai.yaml").read_text(encoding="utf-8")
    assert "$crazycraft-quarter-distillation" in metadata
    cases = json.loads((skill / "tests/validation-cases.json").read_text(encoding="utf-8"))
    assert len(cases["cases"]) == 2
    assert not (skill / "README.md").exists()


def test_preliminary_crazycraft_report_is_metadata_only_and_fail_closed() -> None:
    root = ROOT / "planning/crazycraft-preliminary"
    assert validate_distillation_output(root) == []
    summary = (root / "distillation/executive-summary.md").read_text(encoding="utf-8")
    rights = json.loads((root / "distillation/rights-risk.json").read_text(encoding="utf-8"))
    assert "No exact Crazy Craft edition" in summary
    assert "No third-party assets are included" in summary
    assert rights["approval_claimed"] is False
    assert all(record["review_status"] == "HUMAN_LEGAL_AND_MARKETPLACE_REVIEW_REQUIRED" for record in rights["records"])
