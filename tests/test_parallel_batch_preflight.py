from __future__ import annotations

import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "production/batches/forest-wave-1-parallel-batch-1"
FEATURES = (
    "signal_ruin",
    "gloamwing_stalker",
    "forest_attunement",
    "mossback_forager",
    "barkguard_charm",
)


def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_preflight_is_complete_and_honest() -> None:
    preflight = read(BATCH / "batch-preflight.json")
    assert preflight["status"] == "BATCH_PREFLIGHT_READY"
    assert preflight["immutable_base_commit"] == "e9009b70502f4e0db57986ea52cf8d4f7998cc1b"
    assert preflight["production_model"] == "gpt-5.6-sol"
    assert preflight["production_reasoning_effort"] == "light"
    assert preflight["wave_policy"]["maximum_child_concurrency"] == 3
    launched = preflight["wave_policy"]["wave_a"] + preflight["wave_policy"]["wave_b"]
    assert sorted(launched) == sorted(FEATURES)
    assert preflight["acceptance"]["unavailable_gates"]["physical_ps4"] == "PENDING_PHYSICAL_HARDWARE"
    assert "NO_PUSH" in preflight["release_restrictions"]


def test_original_production_contracts_are_authorized_and_isolated() -> None:
    for feature in FEATURES:
        contract = read(
            ROOT
            / "production/reconstruction-waves/forest-wave-1"
            / feature
            / "original-production-manifest.json"
        )
        assert contract["production_lane"] == "ORIGINAL_BEDROCK_NATIVE"
        assert contract["authorship_mode"] == "ORIGINAL_AUTHORSHIP"
        assert contract["java_evidence"] == "NOT_APPLICABLE"
        assert contract["java_fidelity_claimed"] is False
        assert contract["source_expression_used"] is False
        assert contract["execution_authorized"] is True
        assert contract["required_tests"]
        assert contract["explicit_non_goals"]
        assert contract["performance_caps"]
        assert contract["release_status"]["physical_ps4_certified"] is False


def test_reservations_have_unique_valid_uuids_and_disjoint_prefixes() -> None:
    reservations = read(BATCH / "reservations.json")["features"]
    all_uuids: list[str] = []
    all_prefixes: list[str] = []
    all_identifiers: list[str] = []
    for feature in FEATURES:
        row = reservations[feature]
        all_uuids.extend(row["uuids"].values())
        all_prefixes.extend(row["identifier_prefixes"])
        all_identifiers.extend(row["reserved_identifiers"])
    assert len(all_uuids) == len(set(all_uuids)) == 25
    assert all(str(uuid.UUID(value)) == value for value in all_uuids)
    assert len(all_prefixes) == len(set(all_prefixes))
    assert len(all_identifiers) == len(set(all_identifiers))


def test_assignments_have_disjoint_write_scopes_and_required_packet() -> None:
    owned: list[str] = []
    for feature in FEATURES:
        assignment = read(BATCH / "assignments" / f"{feature}.json")
        assert assignment["feature_id"] == feature
        assert assignment["model"] == "gpt-5.6-sol"
        assert assignment["reasoning_effort"] == "light"
        assert assignment["shared_files_may_be_edited"] is False
        assert assignment["authoritative_bds_owner"] == "MAIN_CODEX"
        assert assignment["blockbench_gui_owner"] == "MAIN_CODEX"
        assert "reports/candidate-packet.json" in assignment["required_outputs"]
        owned.extend(assignment["owned_paths"])
    assert len(owned) == len(set(owned))
    assert not any("resonance-sling" in path for path in owned)
    assert not any("phase_anchor_test.bbmodel" in path for path in owned)
