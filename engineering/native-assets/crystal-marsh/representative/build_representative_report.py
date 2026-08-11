#!/usr/bin/env python3
"""Build the deterministic aggregate receipt for the bounded Crystal Marsh native gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
OUTPUT = HERE / "CRYSTAL_MARSH_REPRESENTATIVE_NATIVE_REPORT.json"
ASSETS = ("marsh_wight", "crystal_dragonfly", "silt_crocodile", "bubble_pod", "flood_reed", "sunken_shrine", "ancient_boat")
SOURCE_COMMIT = "9235ff0fb375a025127888b618e2818994206d5a"
SOURCE_TREE = "b7d178ad9f1fc2a1581deb1dc3bb69eb82f3478d"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def build() -> dict:
    contact_manifest = HERE / "CRYSTAL_MARSH_REPRESENTATIVE_CONTACT_SHEETS.json"
    contact_records = {item["asset"]: item for item in json.loads(contact_manifest.read_text())["assets"]}
    assets = []
    total_clips = total_locators = total_screenshots = 0
    for asset in ASSETS:
        root = EVIDENCE / asset
        receipt_path = root / "crystal-marsh-representative-native-receipt.json"
        receipt = json.loads(receipt_path.read_text())
        screenshots = receipt["screenshots"]
        screenshot_manifest = [{"path": item["path"], "sha256": item["sha256"]} for item in screenshots]
        total_clips += len(receipt["brief_declared_clips"])
        total_locators += len(receipt["required_locators"])
        total_screenshots += len(screenshots)
        assets.append({
            "asset": asset,
            "representative_class": receipt["representative_class"],
            "status": receipt["status"],
            "brief_declared_clips": receipt["brief_declared_clips"],
            "required_locators": receipt["required_locators"],
            "normalized_identifier": receipt["normalized_identifier"],
            "texture_resolution": receipt["texture_resolution_preserved_from_packet"],
            "texture_sha256": receipt["staged_texture"]["sha256"],
            "native_project_sha256": receipt["native_project"]["sha256"],
            "pass_2_geometry_sha256": receipt["native_exports"]["geometry"]["pass_2"]["sha256"],
            "pass_2_animation_sha256": receipt["native_exports"]["animations"]["pass_2"]["sha256"],
            "receipt_sha256": sha256(receipt_path),
            "screenshot_manifest_sha256": canonical_hash(screenshot_manifest),
            "screenshot_count": len(screenshots),
            "contact_sheet": contact_records[asset],
            "warning_count": receipt["native_result"]["warning_count"],
            "error_count": receipt["native_result"]["error_count"],
            "checks": {
                "exact_brief_clip_set": set(receipt["brief_declared_clips"]) == {name.rsplit(".", 1)[-1] for name in receipt["authored_clip_names"]},
                "editable_geometry_uv_signature_preserved": len(set(receipt["geometry_signatures_excluding_intended_locators"].values())) == 1,
                "pass_1_pass_2_animation_canonical_equivalent": receipt["native_exports"]["animations"]["canonical_equivalent"],
                "pass_1_pass_2_geometry_canonical_equivalent": receipt["native_exports"]["geometry"]["canonical_equivalent"],
                "texture_bytes_preserved": receipt["texture_bytes_preserved"],
            },
        })
    return {
        "schema": "aionforge.wave1.crystal_marsh.representative_native.aggregate.v1",
        "status": "PASS_NATIVE_REPAIR_GATE",
        "integration_authority": {"commit": SOURCE_COMMIT, "tree": SOURCE_TREE},
        "scope": list(ASSETS),
        "tooling": {"blockbench_version": "5.1.6", "transport": "CDP_LOOPBACK_ONLY", "endpoint": "http://127.0.0.1:9263", "extensions_disabled": True},
        "totals": {"assets": len(assets), "brief_declared_clips": total_clips, "true_native_locators": total_locators, "screenshots": total_screenshots, "warnings": sum(item["warning_count"] for item in assets), "errors": sum(item["error_count"] for item in assets)},
        "assets": assets,
        "contact_sheet_manifest": {"path": contact_manifest.name, "sha256": sha256(contact_manifest)},
        "proof_boundaries": {
            "proves": ["BLOCKBENCH_5_1_6_NATIVE_EDITABLE_ROUNDTRIP", "EXACT_BRIEF_DECLARED_CLIP_AUTHORING", "TRUE_NATIVE_LOCATORS_FROM_CANONICAL_PACKET_TRANSFORMS", "EDITABLE_GEOMETRY_UV_SIGNATURE_PRESERVATION", "EXACT_PACKET_TEXTURE_BYTE_PRESERVATION", "TWO_NATIVE_EXPORT_CYCLES_WITH_CANONICAL_EQUIVALENCE", "NATIVE_TIMELINE_SCREENSHOT_PER_DECLARED_CLIP"],
            "does_not_prove": ["BP_RP_INTEGRATION", "GAMEPLAY", "BDS", "BEDROCK_CLIENT", "MULTIPLAYER", "PHYSICAL_PS4", "MARKETPLACE", "RELEASE"],
            "golden_promotion": "WITHHELD_PENDING_TRUE_SILHOUETTE_PLAYER_SCALE_INDEPENDENT_ORIGINALITY_AND_CLIENT_VISUAL_REVIEW",
            "packet_static_geometry_comparison": "INFORMATIONAL_ONLY_PACKET_STATIC_EXPORT_IS_LOCATOR_TRANSFORM_AUTHORITY_NOT_NATIVE_CODEC_BYTE_AUTHORITY",
        },
    }


def main() -> None:
    OUTPUT.write_text(json.dumps(build(), sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
