#!/usr/bin/env python3
"""Build the deterministic native-only Twinbond asset report."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import author_native as author


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "TWINBOND_NATIVE_REPORT.json"
ASSETS = tuple(author.SPECS)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    rows = []
    for asset in ASSETS:
        receipt_path = HERE / "evidence" / asset / author.RECEIPT_NAME
        receipt = json.loads(receipt_path.read_text())
        rows.append({
            "asset": asset,
            "status": receipt["status"],
            "clip_authority": receipt["clip_authority"],
            "clips": receipt["brief_declared_clips"],
            "locators": receipt["required_locators"],
            "phase_ready": receipt["phase_ready"],
            "blockbench_version": receipt["native_result"]["blockbench_version"],
            "warnings": receipt["native_result"]["warning_count"],
            "errors": receipt["native_result"]["error_count"],
            "screenshots": len(receipt["screenshots"]),
            "texture_bytes_preserved": receipt["texture_bytes_preserved"],
            "two_cycle_geometry_equivalent": receipt["native_exports"]["geometry"]["canonical_equivalent"],
            "two_cycle_animation_equivalent": receipt["native_exports"]["animations"]["canonical_equivalent"],
            "receipt_sha256": sha256(receipt_path),
            "native_project_sha256": receipt["native_project"]["sha256"],
            "pass_2_geometry_sha256": receipt["native_exports"]["geometry"]["pass_2"]["sha256"],
            "pass_2_animation_sha256": receipt["native_exports"]["animations"]["pass_2"]["sha256"],
        })
    passed = all(row["status"] == "PASS_NATIVE_REPAIR_GATE" and row["warnings"] == 0 and row["errors"] == 0 and row["texture_bytes_preserved"] and row["two_cycle_geometry_equivalent"] and row["two_cycle_animation_equivalent"] for row in rows)
    return {
        "schema": "aionforge.wave1.twinbond.native.aggregate.v2",
        "status": "PASS_PHASE_READY_NATIVE_REPAIR" if passed else "FAIL",
        "integration_authority": {"commit": author.INTEGRATION_COMMIT, "tree": author.INTEGRATION_TREE},
        "scope": list(ASSETS),
        "assets": rows,
        "totals": {
            "assets": len(rows),
            "clips": sum(len(row["clips"]) for row in rows),
            "true_native_locators": sum(len(row["locators"]) for row in rows),
            "screenshots": sum(row["screenshots"] for row in rows),
            "warnings": sum(row["warnings"] for row in rows),
            "errors": sum(row["errors"] for row in rows),
        },
        "phase_assessment": {
            "existing_generic_clips_sufficient": False,
            "reason": "The prior idle and action pair exposed no independently selectable presentation for four ratified phases, and the RP bound only idle.",
            "repair": "Four original presentation-only clips per wyrm, selected by the client-synchronized aionbound:twinbond_phase enum set alongside existing phase tags.",
            "required_phases": ["split_approach", "concord_pressure", "relic_trial", "finale_ignition"],
            "new_attack_identity": False,
            "damage_effect_radius_or_knockback_change": False,
            "gameplay_authority": "UNCHANGED_SERVER_AUTHORITATIVE_TWINBOND_SERVICE",
        },
        "proof_boundary": {
            "proves": ["BLOCKBENCH_5_1_6_NATIVE_EDITABLE_ROUNDTRIP", "TRUE_NATIVE_LOCATORS", "TWO_NATIVE_EXPORT_CYCLES_CANONICALLY_EQUIVALENT", "TEXTURE_BYTES_PRESERVED", "FOUR_DISTINCT_WYRM_PHASE_PRESENTATION_CLIPS", "STATIC_BP_RP_PHASE_BINDING", "EXACT_RELIC_BRIEF_CLIP_AUTHORING"],
            "does_not_prove": ["BEDROCK_CLIENT_PLAYBACK", "GAMEPLAY", "BDS", "MULTIPLAYER", "PHYSICAL_PS4", "MARKETPLACE", "RELEASE"],
        },
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build(), sort_keys=True, separators=(",", ":")) + "\n")
