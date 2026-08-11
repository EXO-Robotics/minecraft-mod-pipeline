#!/usr/bin/env python3
"""Build the deterministic aggregate receipt for Crystal-facing equipment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import author_equipment as author


HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
OUTPUT = HERE / "CRYSTAL_EQUIPMENT_NATIVE_REPORT.json"
ASSETS = tuple(author.SPECS)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    assets = []
    totals = {"assets": 0, "brief_declared_clips": 0, "true_native_locators": 0, "screenshots": 0, "warnings": 0, "errors": 0}
    for asset in ASSETS:
        root = EVIDENCE / asset
        receipt_path = root / author.RECEIPT_NAME
        receipt = json.loads(receipt_path.read_text())
        row = {
            "asset": asset,
            "portfolio_class": receipt["portfolio_class"],
            "status": receipt["status"],
            "brief_declared_clips": receipt["brief_declared_clips"],
            "required_locators": receipt["required_locators"],
            "texture_sha256": receipt["staged_texture"]["sha256"],
            "native_project_sha256": receipt["native_project"]["sha256"],
            "pass_2_geometry_sha256": receipt["native_exports"]["geometry"]["pass_2"]["sha256"],
            "pass_2_animation_sha256": receipt["native_exports"]["animations"]["pass_2"]["sha256"],
            "receipt_sha256": sha256(receipt_path),
            "screenshot_count": len(receipt["screenshots"]),
            "warning_count": receipt["native_result"]["warning_count"],
            "error_count": receipt["native_result"]["error_count"],
            "checks": {
                "exact_brief_clip_set": set(receipt["brief_declared_clips"]) == {name.rsplit(".", 1)[-1] for name in receipt["authored_clip_names"]},
                "editable_shape_uv_preserved": len(set(receipt["geometry_signatures_excluding_intended_locators"].values())) == 1,
                "geometry_two_pass_equivalent": receipt["native_exports"]["geometry"]["canonical_equivalent"],
                "animation_two_pass_equivalent": receipt["native_exports"]["animations"]["canonical_equivalent"],
                "texture_bytes_preserved": receipt["texture_bytes_preserved"],
            },
        }
        assets.append(row)
        totals["assets"] += 1
        totals["brief_declared_clips"] += len(row["brief_declared_clips"])
        totals["true_native_locators"] += len(row["required_locators"])
        totals["screenshots"] += row["screenshot_count"]
        totals["warnings"] += row["warning_count"]
        totals["errors"] += row["error_count"]
    return {
        "schema": "aionforge.wave1.crystal_marsh.equipment_native.aggregate.v1",
        "status": "PASS_NATIVE_REPAIR_GATE" if all(row["status"] == "PASS_NATIVE_REPAIR_GATE" and all(row["checks"].values()) for row in assets) else "FAIL",
        "integration_authority": {"commit": author.INTEGRATION_COMMIT, "tree": author.INTEGRATION_TREE},
        "scope": list(ASSETS),
        "excluded_and_unchanged": {
            "surveyor_staff": "ADJACENT_CROSS_BIOME_ITEM_OUTSIDE_EXACT_SCOPE",
            "trail_compass": "ADJACENT_CROSS_BIOME_ITEM_OUTSIDE_EXACT_SCOPE",
            "W1-CREATIVE-005": "DEFERRED_NO_SIDEGRADES_AUTHORED",
        },
        "tooling": {"blockbench_version": "5.1.6", "transport": "CDP_LOOPBACK_ONLY", "endpoint": "http://127.0.0.1:9267", "extensions_disabled": True},
        "texture_policy": "EXACT_32X32_PACKET_BYTES_PRESERVED_NO_RESAMPLE_OR_UPSCALE",
        "totals": totals,
        "assets": assets,
        "proof_boundaries": {
            "proves": ["BLOCKBENCH_5_1_6_NATIVE_EDITABLE_ROUNDTRIP", "EXACT_BRIEF_CLIP_SET", "TRUE_NATIVE_EFFECT_LOCATORS_FROM_CANONICAL_EXPORT", "EDITABLE_SHAPE_UV_PRESERVATION", "EXACT_PACKET_TEXTURE_BYTES", "TWO_NATIVE_EXPORT_CYCLES", "TIMELINE_PROOF_PER_DECLARED_CLIP"],
            "does_not_prove": ["BP_RP", "ICONS", "GAMEPLAY", "RECIPES", "LOOT", "AUTHORITY", "BDS", "BEDROCK_CLIENT", "MULTIPLAYER", "PHYSICAL_PS4", "MARKETPLACE", "RELEASE"],
        },
    }


def main() -> None:
    OUTPUT.write_text(json.dumps(build(), sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
