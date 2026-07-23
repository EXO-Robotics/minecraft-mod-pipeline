from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mccompiler.cleanroom import (
    CleanRoomError,
    audit_consumer_package,
    build_gameplay_intent,
    evaluate_rights_strategy,
    export_clean_room_contract,
    reject_unknown_schema,
    screen_similarity,
    validate_material_ledger,
    validate_originality_record,
    validate_production_artifact,
)
from mccompiler.project.layout import PROJECT_DIRECTORIES


FIXTURES = Path(__file__).parent / "fixtures" / "cleanroom_rights"
SCHEMAS = Path(__file__).parents[1] / "src" / "mccompiler" / "schemas"


def fixture(case: int) -> dict[str, Any]:
    path = next(FIXTURES.glob(f"case-{case:02d}-*.json"))
    return json.loads(path.read_text(encoding="utf-8"))


def material(
    *,
    material_type: str = "source_code",
    direct_reuse: str = "prohibited",
    ambiguous: bool = False,
    noncommercial: bool = False,
    third_party: bool = False,
    permissions: dict[str, str] | None = None,
) -> dict[str, Any]:
    granted = {
        "analysis": "allowed",
        "redistribution": "allowed",
        "commercial_use": "allowed",
        "derivatives": "allowed",
        "marketplace_distribution": "allowed",
        "attribution_required": "not_applicable",
        "source_disclosure_required": "not_applicable",
    }
    granted.update(permissions or {})
    return {
        "material_id": f"fixture:{material_type}",
        "source_id": "fixture:source",
        "material_type": material_type,
        "ownership": {
            "asserted_owner": "Fixture Author",
            "verified_owner": None if ambiguous else "Fixture Author",
            "evidence_refs": ["rights://fixture/declaration"],
        },
        "permissions": granted,
        "restrictions": {
            "noncommercial": noncommercial,
            "share_alike": False,
            "trademark_restriction": False,
            "third_party_content_present": third_party,
            "ambiguous_ownership": ambiguous,
        },
        "production_disposition": {
            "direct_reuse": direct_reuse,
            "production_reference": "prohibited",
            "abstract_mechanic_extraction": "allowed",
            "clean_room_replacement": "allowed",
            "authorized_adaptation_eligible": "allowed",
        },
    }


def clean_strategy() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "mode": "clean_room_originalization",
        "inspiration_scope": "abstract_gameplay_patterns_only",
        "direct_source_expression_reuse": "prohibited",
        "third_party_assets_allowed": False,
        "third_party_names_allowed": False,
        "third_party_branding_allowed": False,
        "distinctive_expression_allowed": False,
        "commercial_marketplace_rights_required": True,
    }


def intent_input(*, transition: str = "ABSTRACT_PATTERN_RETAINED") -> dict[str, Any]:
    evidence_ref = "evidence://fixture/entity/charge"
    return {
        "intent_id": "intent:territorial_charger",
        "intent_type": "regional_creature_role",
        "experience_family": "forest_progression",
        "abstract_role": "territorial charger with a recovery window",
        "player_fantasy": "read and counter a regional threat",
        "gameplay_loop": ["observe warning", "evade charge", "counter during recovery"],
        "combat_pattern": {
            "warning": "territorial_display",
            "primary_attack": "short_charge",
            "vulnerability": "recovery_window",
        },
        "exploration_pattern": "regional territory",
        "reward_function": "generic progression material function",
        "progression_role": "early_mid escalation",
        "multiplayer_requirements": ["server authoritative targeting", "bounded ownership"],
        "persistence_requirements": ["no instance persistence required"],
        "cleanup_requirements": ["bounded population", "despawn policy"],
        "performance_expectations": {"pathfinding": "bounded", "ps4_planning_profile": "conservative"},
        "dependencies": [],
        "claims": [{
            "claim": "short acceleration is followed by a recovery interval",
            "disposition": "inferred",
            "confidence": 0.84,
            "evidence_refs": [evidence_ref],
            "rationale": "Repeated bounded acceleration and recovery were observed in the synthetic fixture.",
            "source_type": "runtime_observation",
            "rights_constraints": ["analysis only", "expression excluded"],
            "selection_rationale": "Retain only the generic encounter rhythm.",
        }],
        "rights": {
            "source_access": "analysis_only",
            "reusable_expression": "prohibited",
            "abstract_mechanic_reuse": "allowed",
            "direct_reconstruction": "RIGHTS_BLOCKED_DIRECT_RECONSTRUCTION",
            "commercial_asset_rights": "unknown",
            "transition": transition,
        },
    }


def finding_codes(report: dict[str, Any]) -> set[str]:
    return {row["code"] for row in report["findings"]}


def test_required_schemas_and_structural_boundary_exist() -> None:
    expected = {
        "rights-strategy-1.0.0.json",
        "rights-material-record-1.0.0.json",
        "gameplay-intent-ir-1.0.0.json",
        "clean-room-design-contract-1.0.0.json",
        "originality-record-1.0.0.json",
        "similarity-screening-report-1.0.0.json",
    }
    assert expected <= {path.name for path in SCHEMAS.glob("*.json")}
    for name in expected:
        assert json.loads((SCHEMAS / name).read_text(encoding="utf-8"))["$schema"].endswith("2020-12/schema")
    assert {
        "analysis/evidence", "analysis/rights-ledger", "analysis/gameplay-intent",
        "production/design-contracts", "production/originality",
        "production/similarity-screening", "production/production-plans",
    } <= set(PROJECT_DIRECTORIES)


def test_all_twelve_numbered_fixtures_are_present_and_unique() -> None:
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(FIXTURES.glob("case-*.json"))]
    assert [row["case"] for row in rows] == list(range(1, 13))
    assert len({row["name"] for row in rows}) == 12


def test_case_01_abstract_pattern_crosses_only_as_audited_abstraction() -> None:
    case = fixture(1)
    built = build_gameplay_intent(intent_input(), allowed_evidence_refs=[case["evidence_ref"]])
    contract = export_clean_room_contract(built, contract_id="product:forest_regional_charger_v1")
    serialized = json.dumps(contract, sort_keys=True)
    assert contract["combat_pattern"]["primary_attack"] == "short_charge"
    assert contract["provenance"]["taint"] == ["ABSTRACTED_MECHANIC", "CLEAN_ROOM_ORIGINAL"]
    assert "evidence://" not in serialized
    assert "claims" not in contract
    assert "source_access" not in serialized


@pytest.mark.parametrize(
    ("case_number", "expected_code"),
    [
        (2, "DIRECT_PRODUCTION_REUSE_BLOCKED"),
        (5, "UNKNOWN_OWNERSHIP_PRODUCTION_BLOCKED"),
        (6, "NONCOMMERCIAL_MARKETPLACE_REUSE_BLOCKED"),
    ],
)
def test_cases_02_05_06_material_rights_fail_closed(case_number: int, expected_code: str) -> None:
    case = fixture(case_number)
    permissions: dict[str, str] = {}
    if case_number == 2:
        permissions = case["permissions"]
    row = material(
        material_type=case["material_type"],
        direct_reuse=case["direct_reuse"],
        ambiguous=case.get("ambiguous_ownership", False),
        noncommercial=case.get("noncommercial", False),
        permissions=permissions,
    )
    result = validate_material_ledger({"schema_version": "1.0.0", "records": [row]})
    assert not result["valid"]
    assert expected_code in finding_codes(result)
    assert not result["records"][0]["direct_reuse_allowed"]
    if case_number == 6:
        assert result["records"][0]["analysis_allowed"]


def test_case_03_restricted_expression_requires_clean_room_redesign() -> None:
    case = fixture(3)
    built = build_gameplay_intent(
        intent_input(transition=case["transition"]),
        allowed_evidence_refs=["evidence://fixture/entity/charge"],
    )
    contract = export_clean_room_contract(built, contract_id="product:forest_regional_charger_v1")
    assert built["rights"]["direct_reconstruction"] == "RIGHTS_BLOCKED_DIRECT_RECONSTRUCTION"
    assert built["rights"]["transition"] == "CLEAN_ROOM_REDESIGN_REQUIRED"
    assert contract["design_constraints"]["source_asset_access"] == "prohibited"


def test_case_04_distinctive_combination_is_omitted() -> None:
    case = fixture(4)
    built = build_gameplay_intent(
        intent_input(transition=case["transition"]),
        allowed_evidence_refs=["evidence://fixture/entity/charge"],
    )
    with pytest.raises(CleanRoomError) as caught:
        export_clean_room_contract(built, contract_id="product:blocked")
    assert caught.value.code == case["expected_code"]


def test_case_07_authorized_adaptation_is_material_specific_and_incomplete() -> None:
    case = fixture(7)
    ledger = {"schema_version": "1.0.0", "records": [material(material_type="source_code", direct_reuse="allowed")]}
    result = evaluate_rights_strategy(
        {"schema_version": "1.0.0", "mode": case["mode"]},
        ledger,
    )
    assert not result["production_allowed"]
    assert case["expected_code"] in finding_codes(result)
    assert not result["legal_clearance_implied"]


@pytest.mark.parametrize("case_number", [8, 9, 11])
def test_cases_08_09_11_production_reference_name_and_hash_leaks_report_exact_fields(case_number: int) -> None:
    case = fixture(case_number)
    result = validate_production_artifact(
        case["artifact"],
        blocked_names=[case["blocked_name"]] if "blocked_name" in case else [],
        blocked_hashes=[case["blocked_hash"]] if "blocked_hash" in case else [],
    )
    assert not result["valid"]
    match = next(row for row in result["findings"] if row["code"] == case["expected_code"])
    assert match["path"] == case["expected_path"]


def test_case_10_clean_originality_and_similarity_records_are_low_risk_not_clearance() -> None:
    case = fixture(10)
    originality = {
        "schema_version": "1.0.0",
        "product_id": case["product_id"],
        "contract_id": "product:forest_charger_contract",
        "creator_mode": "clean_room_originalization",
        "design_seed": 7305,
        "design_profile_revision": "visual-style-profile-1.0.0",
        "source_restrictions": ["no source asset access"],
        "independently_created_elements": ["name", "silhouette", "palette"],
        "mechanics_retained_at_abstract_level": ["territorial charge and recovery"],
        "expressive_elements_replaced": ["identity", "appearance", "reward", "audio"],
        "name_provenance": {"status": "original_fixture"},
        "visual_provenance": {"status": "original_fixture"},
        "structure_provenance": {"status": "not_applicable"},
        "reward_provenance": {"status": "original_fixture"},
        "progression_provenance": {"status": "original_fixture"},
        "known_similarities": [],
        "revision_history": [{"revision": 1, "reason": "initial synthetic fixture"}],
        "screening_status": case["expected_outcome"],
    }
    validation = validate_originality_record(originality)
    assert validation["valid"]
    first = screen_similarity(case["candidate"], [case["comparison"]])
    second = screen_similarity(case["candidate"], [case["comparison"]])
    assert first == second
    assert first["outcome"] == case["expected_outcome"]
    assert first["notice"] == "Not legal clearance."
    assert not first["legal_clearance_implied"]


def test_case_11_protected_rights_hash_may_remain_outside_production_only() -> None:
    case = fixture(11)
    ledger = {
        "schema_version": "1.0.0",
        "records": [{
            **material(material_type="texture"),
            "protected_hashes": [case["blocked_hash"]],
        }],
    }
    assert validate_material_ledger(ledger)["valid"]
    assert not validate_production_artifact(
        case["artifact"], blocked_hashes=[case["blocked_hash"]]
    )["valid"]


def test_case_12_consumer_package_contamination_is_blocked() -> None:
    case = fixture(12)
    report = audit_consumer_package(case["paths"])
    assert not report["valid"]
    match = next(row for row in report["findings"] if row["code"] == case["expected_code"])
    assert match["path"] == case["expected_path"]
    clean = audit_consumer_package([
        "behavior_pack/manifest.json",
        "resource_pack/textures/product/original.png",
    ])
    assert clean["valid"]


def test_clean_room_strategy_defaults_are_enforced_and_deterministic() -> None:
    ledger = {"schema_version": "1.0.0", "records": [material()]}
    first = evaluate_rights_strategy(clean_strategy(), ledger)
    second = evaluate_rights_strategy(clean_strategy(), ledger)
    assert first == second
    assert first["production_allowed"]
    weakened = {**clean_strategy(), "third_party_assets_allowed": True}
    blocked = evaluate_rights_strategy(weakened, ledger)
    assert not blocked["production_allowed"]
    assert "UNSAFE_CLEAN_ROOM_STRATEGY" in finding_codes(blocked)


def test_gameplay_intent_rejects_unregistered_evidence_and_hidden_rationale_is_not_needed() -> None:
    with pytest.raises(CleanRoomError) as caught:
        build_gameplay_intent(intent_input(), allowed_evidence_refs=[])
    assert caught.value.code == "GAMEPLAY_INTENT_INVALID"
    assert "UNAUTHORIZED_EVIDENCE_REFERENCE" in {row["code"] for row in caught.value.findings}


def test_trademark_permission_is_independent_from_other_material_permissions() -> None:
    records = [
        material(material_type=kind, direct_reuse="allowed")
        for kind in (
            "source_code", "model", "texture", "animation", "audio", "writing",
            "character", "structure_layout", "dependency",
        )
    ]
    trademark = material(
        material_type="trademark",
        direct_reuse="allowed",
        permissions={"marketplace_distribution": "unknown"},
    )
    trademark["material_id"] = "fixture:trademark"
    records.append(trademark)
    result = evaluate_rights_strategy(
        {"schema_version": "1.0.0", "mode": "authorized_adaptation"},
        {"schema_version": "1.0.0", "records": records},
    )
    assert not result["production_allowed"]
    assert "BRAND_PERMISSION_INCOMPLETE" in finding_codes(result)


def test_code_license_does_not_authorize_art_assets() -> None:
    code = material(material_type="source_code", direct_reuse="allowed")
    art = material(
        material_type="texture",
        direct_reuse="allowed",
        permissions={
            "redistribution": "unknown",
            "commercial_use": "unknown",
            "derivatives": "unknown",
            "marketplace_distribution": "unknown",
        },
    )
    art["material_id"] = "fixture:texture"
    result = validate_material_ledger({"schema_version": "1.0.0", "records": [code, art]})
    by_type = {row["material_type"]: row for row in result["records"]}
    assert by_type["source_code"]["direct_reuse_allowed"]
    assert not by_type["texture"]["direct_reuse_allowed"]
    assert "DIRECT_PRODUCTION_REUSE_BLOCKED" in finding_codes(result)


@pytest.mark.parametrize(
    "disposition",
    ["observed", "inferred", "selected", "redesigned", "omitted", "unknown"],
)
def test_all_six_gameplay_claim_dispositions_are_valid(disposition: str) -> None:
    source = intent_input()
    source["claims"][0]["disposition"] = disposition
    built = build_gameplay_intent(source, allowed_evidence_refs=["evidence://fixture/entity/charge"])
    assert built["claims"][0]["disposition"] == disposition


@pytest.mark.parametrize("confidence", [0.0, 1.0])
def test_confidence_inclusive_boundaries_are_valid(confidence: float) -> None:
    source = intent_input()
    source["claims"][0]["confidence"] = confidence
    built = build_gameplay_intent(source, allowed_evidence_refs=["evidence://fixture/entity/charge"])
    assert built["claims"][0]["confidence"] == confidence


@pytest.mark.parametrize("confidence", [-0.001, 1.001])
def test_confidence_outside_boundaries_is_rejected(confidence: float) -> None:
    source = intent_input()
    source["claims"][0]["confidence"] = confidence
    with pytest.raises(CleanRoomError) as caught:
        build_gameplay_intent(source, allowed_evidence_refs=["evidence://fixture/entity/charge"])
    assert "INVALID_CONFIDENCE" in {row["code"] for row in caught.value.findings}


def test_rights_transition_vocabulary_validates_both_required_paths() -> None:
    for transition in ("ABSTRACT_PATTERN_RETAINED", "CLEAN_ROOM_REDESIGN_REQUIRED"):
        built = build_gameplay_intent(
            intent_input(transition=transition),
            allowed_evidence_refs=["evidence://fixture/entity/charge"],
        )
        assert built["rights"]["transition"] == transition
    for transition in ("TOO_DISTINCTIVE_FOR_SAFE_REDIRECTION", "OMIT_PENDING_LICENSE"):
        built = build_gameplay_intent(
            intent_input(transition=transition),
            allowed_evidence_refs=["evidence://fixture/entity/charge"],
        )
        with pytest.raises(CleanRoomError) as caught:
            export_clean_room_contract(built, contract_id="product:omitted")
        assert caught.value.code == "OMIT_PENDING_LICENSE"
    invalid = intent_input(transition="SUPERFICIAL_RENAME")
    with pytest.raises(CleanRoomError) as caught:
        build_gameplay_intent(invalid, allowed_evidence_refs=["evidence://fixture/entity/charge"])
    assert "INVALID_RIGHTS_TRANSITION" in {row["code"] for row in caught.value.findings}


def test_taint_propagates_until_approved_abstraction_and_blocked_taint_never_clears() -> None:
    restricted = intent_input()
    restricted["taint"] = ["ANALYSIS_ONLY", "RESTRICTED_EXPRESSION"]
    built = build_gameplay_intent(
        restricted, allowed_evidence_refs=["evidence://fixture/entity/charge"]
    )
    assert built["taint"] == ["ABSTRACTED_MECHANIC"]
    assert export_clean_room_contract(
        built, contract_id="product:abstracted"
    )["provenance"]["taint"] == ["ABSTRACTED_MECHANIC", "CLEAN_ROOM_ORIGINAL"]

    unauthorized = intent_input()
    unauthorized["taint"] = ["RESTRICTED_EXPRESSION"]
    unauthorized["rights"]["abstract_mechanic_reuse"] = "prohibited"
    with pytest.raises(CleanRoomError) as caught:
        build_gameplay_intent(
            unauthorized, allowed_evidence_refs=["evidence://fixture/entity/charge"]
        )
    assert "TAINT_REMOVAL_NOT_AUTHORIZED" in {row["code"] for row in caught.value.findings}

    blocked = intent_input()
    blocked["taint"] = ["BLOCKED"]
    with pytest.raises(CleanRoomError) as caught:
        build_gameplay_intent(blocked, allowed_evidence_refs=["evidence://fixture/entity/charge"])
    assert "BLOCKED_TAINT_CANNOT_BE_ABSTRACTED" in {row["code"] for row in caught.value.findings}


@pytest.mark.parametrize(
    "artifact",
    [
        "rights-strategy-1.0.0",
        "rights-material-record-1.0.0",
        "gameplay-intent-ir-1.0.0",
        "clean-room-design-contract-1.0.0",
        "originality-record-1.0.0",
        "similarity-screening-report-1.0.0",
    ],
)
def test_every_new_schema_rejects_unknown_version(artifact: str) -> None:
    with pytest.raises(CleanRoomError) as caught:
        reject_unknown_schema({"schema_version": "2.0.0"}, artifact)
    assert caught.value.code == "UNSUPPORTED_SCHEMA"


def test_complete_authorized_adaptation_records_every_material_and_brand_category() -> None:
    records = []
    for kind in (
        "source_code", "compiled_binary", "model", "texture", "animation", "audio",
        "music", "writing", "localization", "logo", "trademark", "character",
        "structure_layout", "progression_design", "dependency", "documentation",
        "runtime_observation",
    ):
        row = material(material_type=kind, direct_reuse="allowed")
        row["material_id"] = f"fixture:{kind}"
        records.append(row)
    result = evaluate_rights_strategy(
        {"schema_version": "1.0.0", "mode": "authorized_adaptation"},
        {"schema_version": "1.0.0", "records": records},
    )
    assert result["production_allowed"], result
    assert not result["legal_clearance_implied"]


def test_bramblehorn_originality_record_is_complete_and_evidence_conservative() -> None:
    path = Path(__file__).parents[1] / "production" / "originality" / "ccoriginal.bramblehorn.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    result = validate_originality_record(record)
    assert result["valid"], result
    assert record["product_id"] == "ccoriginal:creature.bramblehorn"
    assert record["design_seed"] == "unknown"
    assert record["reward_provenance"]["status"] == "unknown"
    assert record["progression_provenance"]["status"] == "unknown"
    assert record["screening_status"] == "SCREENING_INSUFFICIENT"
