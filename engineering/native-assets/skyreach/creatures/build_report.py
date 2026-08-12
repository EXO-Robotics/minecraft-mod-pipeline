#!/usr/bin/env python3
"""Build the deterministic aggregate receipt for remaining Skyreach creatures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import author_creatures as author


HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
OUTPUT = HERE / "SKYREACH_CREATURE_NATIVE_REPORT.json"
ASSETS = tuple(author.SPECS)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build() -> dict:
    assets = []
    totals = {"assets": 0, "brief_declared_clips": 0, "true_native_locators": 0, "screenshots": 0, "warnings": 0, "errors": 0}
    for asset in ASSETS:
        root = EVIDENCE / asset
        receipt_path = root / author.RECEIPT_NAME
        receipt = json.loads(receipt_path.read_text())
        screenshots = receipt["screenshots"]
        item = {
            "asset": asset,
            "portfolio_class": receipt["portfolio_class"],
            "status": receipt["status"],
            "brief_declared_clips": receipt["brief_declared_clips"],
            "required_locators": receipt["required_locators"],
            "normalized_identifier": receipt["normalized_identifier"],
            "texture_sha256": receipt["staged_texture"]["sha256"],
            "native_project_sha256": receipt["native_project"]["sha256"],
            "pass_2_geometry_sha256": receipt["native_exports"]["geometry"]["pass_2"]["sha256"],
            "pass_2_animation_sha256": receipt["native_exports"]["animations"]["pass_2"]["sha256"],
            "receipt_sha256": sha256(receipt_path),
            "screenshot_manifest_sha256": canonical_hash([{"path": row["path"], "sha256": row["sha256"]} for row in screenshots]),
            "screenshot_count": len(screenshots),
            "warning_count": receipt["native_result"]["warning_count"],
            "error_count": receipt["native_result"]["error_count"],
            "checks": {
                "exact_brief_clip_set": set(receipt["brief_declared_clips"]) == {name.rsplit(".", 1)[-1] for name in receipt["authored_clip_names"]},
                "editable_geometry_uv_signature_preserved": len(set(receipt["geometry_signatures_excluding_intended_locators"].values())) == 1,
                "pass_1_pass_2_animation_canonical_equivalent": receipt["native_exports"]["animations"]["canonical_equivalent"],
                "pass_1_pass_2_geometry_canonical_equivalent": receipt["native_exports"]["geometry"]["canonical_equivalent"],
                "texture_bytes_preserved": receipt["texture_bytes_preserved"],
            },
        }
        assets.append(item)
        totals["assets"] += 1
        totals["brief_declared_clips"] += len(item["brief_declared_clips"])
        totals["true_native_locators"] += len(item["required_locators"])
        totals["screenshots"] += item["screenshot_count"]
        totals["warnings"] += item["warning_count"]
        totals["errors"] += item["error_count"]
    return {
        "schema": "aionforge.wave1.skyreach.creature_native.aggregate.v1",
        "status": "PASS_NATIVE_REPAIR_GATE" if all(row["status"] == "PASS_NATIVE_REPAIR_GATE" and all(row["checks"].values()) for row in assets) else "FAIL",
        "integration_authority": {"commit": author.INTEGRATION_COMMIT, "tree": author.INTEGRATION_TREE},
        "scope": list(ASSETS),
        "tooling": {"blockbench_version": "5.1.6", "transport": "CDP_LOOPBACK_ONLY", "endpoint": "http://127.0.0.1:9265", "extensions_disabled": True},
        "totals": totals,
        "assets": assets,
        "proof_boundaries": {
            "proves": ["BLOCKBENCH_5_1_6_NATIVE_EDITABLE_ROUNDTRIP", "EXACT_BRIEF_DECLARED_CLIP_AUTHORING", "TRUE_NATIVE_LOCATORS_FROM_CANONICAL_PACKET_TRANSFORMS", "EDITABLE_GEOMETRY_UV_SIGNATURE_PRESERVATION", "EXACT_PACKET_TEXTURE_BYTE_PRESERVATION", "TWO_NATIVE_EXPORT_CYCLES_WITH_CANONICAL_EQUIVALENCE", "NATIVE_TIMELINE_SCREENSHOT_PER_DECLARED_CLIP"],
            "does_not_prove": ["BP_RP_INTEGRATION", "GAMEPLAY", "BDS", "BEDROCK_CLIENT", "MULTIPLAYER", "PHYSICAL_PS4", "MARKETPLACE", "RELEASE"],
            "golden_promotion": "WITHHELD_PENDING_TRUE_SILHOUETTE_PLAYER_SCALE_INDEPENDENT_ORIGINALITY_AND_CLIENT_VISUAL_REVIEW",
        },
    }


def main() -> None:
    OUTPUT.write_text(json.dumps(build(), sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
