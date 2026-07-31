from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from mccompiler.orchestration.workload import (
    ACCEPTANCE_OWNERS,
    ALLOWED_RECONSTRUCTION_STRATEGIES,
    SanitizedWorkloadError,
    WORKLOAD_IDS,
    build_skyfactory4_workload_catalog,
    build_skyfactory4_workloads,
    build_workload_dependency_graph,
    canonical_workload_bytes,
    validate_sanitized_workload,
    validate_sanitized_workload_catalog,
)


def _packet() -> dict:
    return copy.deepcopy(build_skyfactory4_workloads()[0])


def _codes(error: SanitizedWorkloadError) -> set[str]:
    return {finding["code"] for finding in error.findings}


def test_catalog_is_complete_safe_and_deterministic() -> None:
    first = build_skyfactory4_workload_catalog()
    second = build_skyfactory4_workload_catalog()
    assert first == second
    assert canonical_workload_bytes(first["workloads"]) == canonical_workload_bytes(second["workloads"])
    assert [packet["workload_id"] for packet in first["workloads"]] == list(WORKLOAD_IDS)
    assert all(packet["source_expression_included"] is False for packet in first["workloads"])
    serialized = json.dumps(first, sort_keys=True).lower()
    for prohibited in ("skyfactory", "darkosto", "curseforge", ".jar", ".class", "/users/", "decompiled"):
        assert prohibited not in serialized


def test_json_schema_declares_the_exact_packet_surface() -> None:
    schema_path = Path(__file__).parents[1] / "src/mccompiler/schemas/sanitized-workload-1.0.0.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    packet = _packet()
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(packet)
    assert schema["properties"]["source_expression_included"] == {"const": False}
    assert set(schema["properties"]["allowed_reconstruction_strategies"]["items"]["enum"]) == set(ALLOWED_RECONSTRUCTION_STRATEGIES)


def test_catalog_has_original_product_facing_scopes_and_shared_interfaces() -> None:
    packets = {packet["workload_id"]: packet for packet in build_skyfactory4_workloads()}
    assert "runtime.advancement-ledger" in packets["SF-T9"]["inputs_produced_by_other_workloads"]
    assert "product.endgame-path" in packets["SF-T9"]["outputs_consumed_by_other_workloads"]
    assert "runtime.test-hooks" in packets["SF-T11"]["outputs_consumed_by_other_workloads"]
    assert "runtime.migrations" in packets["SF-T11"]["shared_runtime_requirements"]
    assert packets["SF-T10"]["title"] == "Original asset requirement contracts"
    assert packets["SF-T11"]["title"] == "Shared Bedrock runtime requirements"


def test_dependency_graph_is_deterministic_complete_and_acyclic() -> None:
    graph = build_workload_dependency_graph()
    assert graph == build_workload_dependency_graph()
    assert graph["nodes"] == list(WORKLOAD_IDS)
    assert graph["root_workloads"] == ["SF-T10", "SF-T11"]
    order = {node: index for index, node in enumerate(graph["topological_order"])}
    assert set(order) == set(WORKLOAD_IDS)
    assert all(order[edge["from"]] < order[edge["to"]] for edge in graph["edges"])
    assert any(edge["from"] == "SF-T11" and edge["to"] == "SF-T9" for edge in graph["edges"])
    assert any(edge["from"] == "SF-T9" and edge["to"] == "SF-T12" for edge in graph["edges"])


def test_acceptance_contracts_separate_local_validation_from_external_gates() -> None:
    for packet in build_skyfactory4_workloads():
        by_class = {test["class"]: test for test in packet["acceptance_tests"]}
        assert by_class["WORKER_LOCAL"]["owner"] == "feature_producer"
        assert by_class["WORKER_LOCAL"]["candidate_publication_prerequisite"] is True
        for test_class, test in by_class.items():
            assert test["owner"] == ACCEPTANCE_OWNERS[test_class]
            if test_class != "WORKER_LOCAL":
                assert test["candidate_publication_prerequisite"] is False
        assert {"T1_MECHANICAL_PREFLIGHT", "STABLE_BDS", "T10_PRIVATE_AUDIT", "CONTROLLER", "PHYSICAL_PS4"} <= set(by_class)


@pytest.mark.parametrize("field", sorted(_packet()))
def test_missing_required_field_is_rejected(field: str) -> None:
    packet = _packet()
    del packet[field]
    with pytest.raises(SanitizedWorkloadError) as caught:
        validate_sanitized_workload(packet)
    assert "REQUIRED_FIELD_MISSING" in _codes(caught.value)


@pytest.mark.parametrize(
    "leaked_text,expected_code",
    [
        ("Read /Users/operator/private-evidence/file.dat before implementing.", "ABSOLUTE_PATH_PROHIBITED"),
        (r"Read C:\\private-evidence\\file.dat before implementing.", "ABSOLUTE_PATH_PROHIBITED"),
        ("Use oracle/server/config/example.cfg as the authority.", "SOURCE_LOCATOR_PROHIBITED"),
        ("Input is located in component.jar.", "SOURCE_LOCATOR_PROHIBITED"),
        ("Reproduce the behavior from Thing.class.", "SOURCE_LOCATOR_PROHIBITED"),
        ("Use SHA256 3d45 as the locator.", "HASH_OR_SOURCE_LOCATOR_PROHIBITED"),
        ("Use aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.", "HASH_OR_SOURCE_LOCATOR_PROHIBITED"),
        ("Decompile the classfile and follow its control flow.", "SOURCE_LOCATOR_PROHIBITED"),
        ("Execute INVOKEVIRTUAL and then PUTFIELD.", "JAVA_EXPRESSION_PROHIBITED"),
        ("Use net.minecraft.world.World for state.", "JAVA_EXPRESSION_PROHIBITED"),
        ("Copy the source texture into the product.", "SOURCE_REPRODUCTION_DIRECTION_PROHIBITED"),
        ("Recreate the original artwork pixel-for-pixel.", "SOURCE_REPRODUCTION_DIRECTION_PROHIBITED"),
        ("Install the supplied source image asset.png.", "SOURCE_LOCATOR_PROHIBITED"),
        ("Display the SkyFactory logo on every screen.", "BRANDING_OR_PROSE_PROHIBITED"),
        ("Reuse the original quest prose verbatim.", "BRANDING_OR_PROSE_PROHIBITED"),
        ("Match the Twilight Forest encounter branding.", "BRANDING_OR_PROSE_PROHIBITED"),
    ],
)
def test_private_expression_and_locator_leakage_is_rejected(leaked_text: str, expected_code: str) -> None:
    packet = _packet()
    packet["product_scope"][0] = leaked_text
    with pytest.raises(SanitizedWorkloadError) as caught:
        validate_sanitized_workload(packet)
    assert expected_code in _codes(caught.value)


def test_source_expression_flag_must_be_literal_false() -> None:
    packet = _packet()
    packet["source_expression_included"] = True
    with pytest.raises(SanitizedWorkloadError) as caught:
        validate_sanitized_workload(packet)
    assert "SOURCE_EXPRESSION_BOUNDARY_REQUIRED" in _codes(caught.value)


@pytest.mark.parametrize("strategy", ["DIRECT_PORT", "DECOMPILE_AND_COPY", 3, None])
def test_unknown_reconstruction_strategy_is_rejected(strategy: object) -> None:
    packet = _packet()
    packet["allowed_reconstruction_strategies"] = [strategy]
    with pytest.raises(SanitizedWorkloadError) as caught:
        validate_sanitized_workload(packet)
    assert "UNKNOWN_RECONSTRUCTION_STRATEGY" in _codes(caught.value)


def test_noncanonical_strategy_order_is_rejected() -> None:
    packet = _packet()
    packet["allowed_reconstruction_strategies"] = list(reversed(ALLOWED_RECONSTRUCTION_STRATEGIES))
    with pytest.raises(SanitizedWorkloadError) as caught:
        validate_sanitized_workload(packet)
    assert "NONCANONICAL_STRATEGY_ORDER" in _codes(caught.value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("script_tick_units_max", 101),
        ("active_entities_max", 129),
        ("persistent_records_max", 4097),
        ("network_events_per_tick_max", -1),
        ("cleanup_ticks_max", 0),
    ],
)
def test_performance_contract_is_bounded(field: str, value: int) -> None:
    packet = _packet()
    packet["performance_budget"][field] = value
    with pytest.raises(SanitizedWorkloadError) as caught:
        validate_sanitized_workload(packet)
    assert "UNBOUNDED_PERFORMANCE_VALUE" in _codes(caught.value)


def test_physical_console_claim_is_rejected() -> None:
    packet = _packet()
    packet["performance_budget"]["physical_console_verified"] = True
    with pytest.raises(SanitizedWorkloadError) as caught:
        validate_sanitized_workload(packet)
    assert "PHYSICAL_CONSOLE_OVERCLAIM" in _codes(caught.value)


def test_external_gate_cannot_become_worker_publication_prerequisite() -> None:
    packet = _packet()
    bds = next(test for test in packet["acceptance_tests"] if test["class"] == "STABLE_BDS")
    bds["candidate_publication_prerequisite"] = True
    with pytest.raises(SanitizedWorkloadError) as caught:
        validate_sanitized_workload(packet)
    assert "EXTERNAL_GATE_PREREQUISITE_PROHIBITED" in _codes(caught.value)


def test_external_gate_must_keep_its_owner() -> None:
    packet = _packet()
    bds = next(test for test in packet["acceptance_tests"] if test["class"] == "STABLE_BDS")
    bds["owner"] = "feature_producer"
    with pytest.raises(SanitizedWorkloadError) as caught:
        validate_sanitized_workload(packet)
    assert "WRONG_ACCEPTANCE_OWNER" in _codes(caught.value)


def test_missing_local_t1_or_bds_contract_is_rejected() -> None:
    for test_class, expected in (
        ("WORKER_LOCAL", "WORKER_LOCAL_TEST_MISSING"),
        ("T1_MECHANICAL_PREFLIGHT", "T1_DELEGATION_MISSING"),
        ("STABLE_BDS", "BDS_DELEGATION_MISSING"),
    ):
        packet = _packet()
        packet["acceptance_tests"] = [test for test in packet["acceptance_tests"] if test["class"] != test_class]
        with pytest.raises(SanitizedWorkloadError) as caught:
            validate_sanitized_workload(packet)
        assert expected in _codes(caught.value)


def test_catalog_rejects_missing_and_duplicate_workloads() -> None:
    packets = build_skyfactory4_workloads()
    with pytest.raises(SanitizedWorkloadError):
        validate_sanitized_workload_catalog(packets[:-1])
    packets[-1]["workload_id"] = "SF-T1"
    with pytest.raises(SanitizedWorkloadError):
        validate_sanitized_workload_catalog(packets)


def test_dependency_graph_rejects_unknown_contract_provider() -> None:
    packets = build_skyfactory4_workloads()
    packets[0]["inputs_produced_by_other_workloads"].append("runtime.missing-service")
    with pytest.raises(SanitizedWorkloadError) as caught:
        build_workload_dependency_graph(packets)
    assert "INPUT_PROVIDER_MISSING" in _codes(caught.value)


def test_validator_returns_a_defensive_copy() -> None:
    packet = _packet()
    validated = validate_sanitized_workload(packet)
    validated["product_scope"].append("A new scope entry.")
    assert validated != packet

