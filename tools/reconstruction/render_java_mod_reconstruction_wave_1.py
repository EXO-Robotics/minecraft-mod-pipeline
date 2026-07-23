from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mccompiler.reconstruction import build_reconstruction_wave  # noqa: E402


GATES = (
    "rights_and_provenance", "gameplay_intent", "clean_room_contract",
    "behavior_and_asset_contracts", "implementation", "deterministic_package",
    "creator_tools", "stable_bds", "multiplayer", "persistence", "cleanup",
    "desktop_presentation", "ps4_planning", "physical_ps4",
)


def pending_gates() -> dict[str, str]:
    return {gate: "PENDING" for gate in GATES}


def feature(
    feature_id: str,
    category: str,
    role: str,
    outputs: list[str],
    *,
    existing: bool = False,
) -> dict[str, object]:
    contract = (
        "prototypes/blockbench/bramblehorn/asset-manifest.json"
        if existing
        else f"production/planning/controlled-chaos-forest/contracts/{feature_id}/clean-room-design.json"
    )
    intent = f"intent-{feature_id}-v1"
    gates = pending_gates()
    evidence: list[str] = []
    state = "PENDING_AUTHORIZED_EVIDENCE"
    if existing:
        evidence = ["bramblehorn-original-authoring-v1", "bramblehorn-stable-bds-v1"]
        state = "BDS_QUALIFIED"
        for gate in (
            "rights_and_provenance", "gameplay_intent", "clean_room_contract",
            "behavior_and_asset_contracts", "implementation",
            "deterministic_package", "creator_tools", "stable_bds",
            "cleanup", "ps4_planning",
        ):
            gates[gate] = "PASSED"
    return {
        "feature_id": feature_id,
        "category": category,
        "abstract_role": role,
        "authorized_evidence_refs": evidence,
        "evidence_state": state,
        "gameplay_intent_ref": intent,
        "clean_room_contract_ref": contract,
        "bedrock_outputs": outputs,
        "gates": gates,
    }


DOCUMENT = {
    "schema_version": "1.0.0",
    "wave_id": "java-mod-reconstruction-wave-1-forest",
    "title": "Java Mod Reconstruction Wave 1 - Forest Systems",
    "target_profile": "PS4_MARKETPLACE_CANDIDATE",
    "rights_mode": "clean_room_originalization",
    "preserve_vanilla_gameplay": True,
    "mandatory_campaign": False,
    "required_categories": sorted({
        "regional_creature", "ranged_item", "structure", "elite_encounter",
        "additive_unlock", "bounded_event",
    }),
    "features": [
        feature(
            "bramblehorn", "regional_creature",
            "existing bounded hostile regional creature and qualification fixture",
            ["behavior_entity", "client_entity", "geometry", "texture", "animations"],
            existing=True,
        ),
        feature(
            "mossback_forager", "regional_creature",
            "second regional creature proving reusable original asset and behavior templates",
            ["behavior_entity", "spawn_rules", "loot", "client_entity", "geometry", "texture", "animations"],
        ),
        feature(
            "resonance_sling", "ranged_item",
            "controller-usable unusual ranged tool with bounded projectile and cooldown",
            ["item", "attachable", "projectile_entity", "recipe", "loot", "geometry", "texture"],
        ),
        feature(
            "signal_ruin", "structure",
            "compact discoverable structure with restart-safe initialization and loot",
            ["mcstructure", "structure_placement", "loot", "initialization_state"],
        ),
        feature(
            "thornwarden_elite", "elite_encounter",
            "bounded elite encounter proving rig reuse, orchestration, and higher-tier loot",
            ["behavior_entity", "encounter_controller", "loot", "client_entity", "geometry", "texture", "animations"],
        ),
        feature(
            "forest_attunement", "additive_unlock",
            "versioned persistent unlock connecting reconstructed systems without replacing vanilla progression",
            ["progression_state", "migration", "recipes", "loot_conditions"],
        ),
        feature(
            "sporefall_event", "bounded_event",
            "optional controlled-chaos event with explicit spawn, workload, and cleanup caps",
            ["event_controller", "spawn_budget", "cleanup_function", "multiplayer_state"],
        ),
    ],
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    analysis, production = build_reconstruction_wave(DOCUMENT)
    analysis_path = ROOT / "analysis/reconstruction-waves/java-mod-reconstruction-wave-1-forest.json"
    production_path = ROOT / "production/reconstruction-waves/java-mod-reconstruction-wave-1-forest/baseline.json"
    write_json(analysis_path, analysis)
    write_json(production_path, production)
    print(json.dumps({
        "analysis": str(analysis_path.relative_to(ROOT)),
        "analysis_hash": analysis["record_hash"],
        "production": str(production_path.relative_to(ROOT)),
        "production_hash": production["record_hash"],
        "physical_ps4_pending": production["claims"]["physical_ps4_pending"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
