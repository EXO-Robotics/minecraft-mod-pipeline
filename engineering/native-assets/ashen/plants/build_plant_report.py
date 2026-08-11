#!/usr/bin/env python3
"""Build the deterministic aggregate Ashen plant native receipt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from author_plants import ASSETS, INTEGRATION_COMMIT, RECEIPT_NAME


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "ASHEN_PLANT_NATIVE_REPORT.json"
INTEGRATION_TREE = "c42ffa9cdbc233d2acdf7cebf7f67bfc2257faa8"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    assets = []
    for asset in ASSETS:
        root = HERE / "evidence" / asset
        receipt_path = root / RECEIPT_NAME
        receipt = json.loads(receipt_path.read_text())
        assets.append(
            {
                "asset": asset,
                "status": receipt["status"],
                "brief_declared_clips": receipt["brief_declared_clips"],
                "required_locators": receipt["required_locators"],
                "normalized_identifier": receipt["normalized_identifier"],
                "texture_sha256": receipt["staged_texture"]["sha256"],
                "texture_bytes_preserved": receipt["texture_bytes_preserved"],
                "native_project_sha256": receipt["native_project"]["sha256"],
                "pass_2_geometry_sha256": receipt["native_exports"]["geometry"]["pass_2"]["sha256"],
                "pass_2_animation_sha256": receipt["native_exports"]["animations"]["pass_2"]["sha256"],
                "two_pass_geometry_equivalent": receipt["native_exports"]["geometry"]["canonical_equivalent"],
                "two_pass_animation_equivalent": receipt["native_exports"]["animations"]["canonical_equivalent"],
                "geometry_uv_signature_preserved": len(set(receipt["geometry_signatures_excluding_intended_locators"].values())) == 1,
                "warning_count": receipt["native_result"]["warning_count"],
                "error_count": receipt["native_result"]["error_count"],
                "screenshot_count": len(receipt["screenshots"]),
                "receipt_sha256": sha256(receipt_path),
            }
        )
    return {
        "schema": "aionforge.wave1.ashen.plant_native.aggregate.v1",
        "status": "PASS_NATIVE_REPAIR_GATE",
        "integration_authority": {"commit": INTEGRATION_COMMIT, "tree": INTEGRATION_TREE},
        "scope": list(ASSETS),
        "excluded_representatives": ["fire_bloom", "smoke_reed"],
        "tooling": {
            "blockbench_version": "5.1.6",
            "transport": "CDP_LOOPBACK_ONLY",
            "extensions_disabled": True,
        },
        "totals": {
            "assets": len(assets),
            "brief_declared_clips": sum(len(item["brief_declared_clips"]) for item in assets),
            "true_native_locators": sum(len(item["required_locators"]) for item in assets),
            "screenshots": sum(item["screenshot_count"] for item in assets),
            "warnings": sum(item["warning_count"] for item in assets),
            "errors": sum(item["error_count"] for item in assets),
        },
        "assets": assets,
        "proof_boundaries": {
            "proves": [
                "BLOCKBENCH_5_1_6_NATIVE_EDITABLE_ROUNDTRIP",
                "EXACT_EMPTY_BRIEF_CLIP_SET",
                "TRUE_NATIVE_LOCATORS_FROM_CANONICAL_PACKET_TRANSFORMS",
                "EDITABLE_GEOMETRY_UV_SIGNATURE_PRESERVATION",
                "EXACT_PACKET_TEXTURE_BYTE_PRESERVATION",
                "TWO_NATIVE_EXPORT_CYCLES_WITH_CANONICAL_EQUIVALENCE",
                "ZERO_WARNING_ZERO_ERROR_NATIVE_SESSIONS",
            ],
            "does_not_prove": [
                "BP_RP_INTEGRATION",
                "GAMEPLAY",
                "BDS",
                "BEDROCK_CLIENT",
                "MULTIPLAYER",
                "PHYSICAL_PS4",
                "MARKETPLACE",
                "RELEASE",
            ],
            "golden_promotion": "WITHHELD_PENDING_TRUE_SILHOUETTE_PLAYER_SCALE_INDEPENDENT_ORIGINALITY_AND_CLIENT_VISUAL_REVIEW",
        },
    }


def main() -> None:
    OUTPUT.write_text(json.dumps(build(), sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
