from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pytest

from mccompiler.cli import RECONSTRUCTION_COMMANDS
from mccompiler.operations.registry import OperationRegistry
from mccompiler.project.layout import PROJECT_DIRECTORIES
from mccompiler.project.store import ProjectStore
from mccompiler.reconstruction import ReconstructionWaveError, build_reconstruction_wave


ROOT = Path(__file__).parents[1]
GATES = (
    "rights_and_provenance", "gameplay_intent", "clean_room_contract",
    "behavior_and_asset_contracts", "implementation", "deterministic_package",
    "creator_tools", "stable_bds", "multiplayer", "persistence", "cleanup",
    "desktop_presentation", "ps4_planning", "physical_ps4",
)
CATEGORIES = (
    "regional_creature", "ranged_item", "structure", "elite_encounter",
    "additive_unlock", "bounded_event",
)


def feature(feature_id: str, category: str) -> dict[str, object]:
    return {
        "feature_id": feature_id,
        "category": category,
        "abstract_role": f"abstract {category} role",
        "authorized_evidence_refs": [],
        "evidence_state": "PENDING_AUTHORIZED_EVIDENCE",
        "gameplay_intent_ref": f"intent-{feature_id}-v1",
        "clean_room_contract_ref": f"production/design-contracts/{feature_id}.json",
        "bedrock_outputs": ["behavior_definition"],
        "gates": {gate: "PENDING" for gate in GATES},
    }


def document() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "wave_id": "wave-1",
        "title": "Wave 1",
        "target_profile": "PS4_MARKETPLACE_CANDIDATE",
        "rights_mode": "clean_room_originalization",
        "preserve_vanilla_gameplay": True,
        "mandatory_campaign": False,
        "required_categories": list(CATEGORIES),
        "features": [feature(f"feature-{index}", category) for index, category in enumerate(CATEGORIES)],
    }


def test_layout_and_operation_surface_exist() -> None:
    assert "analysis/reconstruction-waves" in PROJECT_DIRECTORIES
    assert "production/reconstruction-waves" in PROJECT_DIRECTORIES
    assert RECONSTRUCTION_COMMANDS["prepare-reconstruction-wave"] == "prepare_reconstruction_wave"
    assert OperationRegistry().catalog()["prepare_reconstruction_wave"] == {
        "category": "reconstruction",
        "status": "AVAILABLE",
    }


def test_wave_separates_analysis_evidence_from_consumer_record() -> None:
    raw = document()
    analysis, production = build_reconstruction_wave(raw)
    assert analysis["source_expression_boundary"]["consumer_package_access"] == "prohibited"
    assert analysis["features"][0]["authorized_evidence_refs"] == []
    serialized = json.dumps(production, sort_keys=True)
    assert "authorized_evidence_refs" not in serialized
    assert "analysis/" not in serialized
    assert "evidence://" not in serialized
    assert production["product_kind"] == "minecraft_bedrock_addon"
    assert production["preserve_vanilla_gameplay"] is True
    assert production["mandatory_campaign"] is False
    assert production["claims"] == {
        "marketplace_approved": False,
        "physical_ps4_pending": True,
        "ps4_compatible": False,
    }


def test_non_pending_state_requires_authorized_evidence() -> None:
    raw = document()
    raw["features"][0]["evidence_state"] = "INTENT_DISTILLED"  # type: ignore[index]
    with pytest.raises(ReconstructionWaveError) as caught:
        build_reconstruction_wave(raw)
    assert any(row["code"] == "EVIDENCE_REQUIRED" for row in caught.value.findings)


def test_missing_required_mod_category_fails_closed() -> None:
    raw = document()
    raw["features"] = raw["features"][:-1]  # type: ignore[index]
    with pytest.raises(ReconstructionWaveError) as caught:
        build_reconstruction_wave(raw)
    assert any(
        row["code"] == "REQUIRED_CATEGORY_MISSING" and row["message"] == "bounded_event"
        for row in caught.value.findings
    )


def test_physical_ps4_claim_requires_matching_evidence_state() -> None:
    raw = document()
    raw["features"][0]["gates"]["physical_ps4"] = "PASSED"  # type: ignore[index]
    with pytest.raises(ReconstructionWaveError) as caught:
        build_reconstruction_wave(raw)
    assert any(row["code"] == "PHYSICAL_EVIDENCE_STATE_MISMATCH" for row in caught.value.findings)


def test_operation_commits_both_records_atomically() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "project"
        store = ProjectStore.create(root, name="wave")
        response = OperationRegistry().execute({
            "schema_version": "1.0.0",
            "request_id": "prepare-wave",
            "operation": "prepare_reconstruction_wave",
            "project": str(root),
            "parameters": document(),
            "expected_revision": store.revision,
        })
        assert response["ok"], response
        assert response["result"]["status"] == "BASELINE_PREPARED"
        assert response["result"]["physical_ps4_pending"] is True
        assert (root / "analysis/reconstruction-waves/wave-1.json").is_file()
        production_path = root / "production/reconstruction-waves/wave-1/baseline.json"
        assert production_path.is_file()
        assert "authorized_evidence_refs" not in production_path.read_text(encoding="utf-8")


def test_checked_in_wave_one_is_exactly_the_requested_baseline() -> None:
    analysis = json.loads(
        (ROOT / "analysis/reconstruction-waves/java-mod-reconstruction-wave-1-forest.json").read_text()
    )
    production = json.loads(
        (ROOT / "production/reconstruction-waves/java-mod-reconstruction-wave-1-forest/baseline.json").read_text()
    )
    ids = [row["feature_id"] for row in production["features"]]
    assert ids == [
        "bramblehorn", "mossback_forager", "resonance_sling", "signal_ruin",
        "thornwarden_elite", "forest_attunement", "sporefall_event",
    ]
    assert all(
        row["evidence_state"] == "PENDING_AUTHORIZED_EVIDENCE"
        for row in analysis["features"] if row["feature_id"] != "bramblehorn"
    )
    assert production["claims"]["physical_ps4_pending"] is True
    assert "authorized_evidence_refs" not in json.dumps(production)
