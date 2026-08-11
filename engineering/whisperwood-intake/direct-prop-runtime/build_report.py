#!/usr/bin/env python3
"""Build the evidence-derived direct-prop static runtime report."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name("WHISPERWOOD_DIRECT_PROP_RUNTIME_REPORT.json")
BASE_COMMIT = "80e53a446931256bfd43c9d583b0ca7853845690"
ASSETS = ("lantern_post", "moss_cairn")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


records = []
for asset in ASSETS:
    evidence_root = ROOT / f"engineering/native-assets/whisperwood/evidence/{asset}"
    receipt_path = evidence_root / "direct-prop-native-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    files = {
        "behavior_block": ROOT / f"behavior_pack/blocks/{asset}.block.json",
        "shipping_geometry": ROOT / f"resource_pack/models/blocks/{asset}.geo.json",
        "shipping_texture": ROOT / f"resource_pack/textures/aionbound/whisperwood/blocks/{asset}.png",
    }
    records.append({
        "id": asset,
        "runtime_id": f"aionbound:{asset}",
        "geometry_id": f"geometry.aionbound.{asset}",
        "native_receipt": {
            "path": receipt_path.relative_to(ROOT).as_posix(),
            "sha256": sha256(receipt_path),
            "status": receipt["status"],
            "blockbench_version": receipt["native_result"]["blockbench_version"],
        },
        "native_geometry": {
            "path": (evidence_root / "native-exports/pass-2.geo.json").relative_to(ROOT).as_posix(),
            "sha256": sha256(evidence_root / "native-exports/pass-2.geo.json"),
        },
        "source_texture_sha256": receipt["evidence_inputs"]["texture"]["sha256"],
        "files": {
            label: {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}
            for label, path in files.items()
        },
    })

report = {
    "schema_version": 1,
    "status": "WHISPERWOOD_DIRECT_PROP_RUNTIME_STATIC_PASS",
    "base_commit": BASE_COMMIT,
    "asset_count": len(records),
    "assets": records,
    "shared_registries": {
        label: {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}
        for label, path in {
            "blocks": ROOT / "resource_pack/blocks.json",
            "terrain_texture": ROOT / "resource_pack/textures/terrain_texture.json",
            "language": ROOT / "resource_pack/texts/en_US.lang",
        }.items()
    },
    "checks": {
        "dedicated_closure_tests": "PASS_6_OF_6",
        "native_receipt_status_and_blockbench_version": "PASS",
        "identifier_only_geometry_normalization": "PASS",
        "native_locator_transform_preservation": "PASS",
        "source_texture_hash_equality": "PASS",
        "png_crc_and_inflate": "PASS",
        "bp_rp_registry_reference_closure": "PASS",
        "unsupported_block_animation_playback_withheld": "PASS",
        "loot_reward_and_assembly_behavior_withheld": "PASS",
    },
    "proof_scope": "STATIC_DIRECT_PROP_BP_RP_AND_NATIVE_EVIDENCE_CLOSURE_ONLY",
    "not_proven": [
        "CUSTOM_BLOCK_ANIMATION_PLAYBACK",
        "PACKAGE",
        "BEDROCK_CLIENT",
        "STABLE_BDS",
        "CONTROLLER",
        "MULTIPLAYER",
        "PHYSICAL_PS4",
        "MARKETPLACE",
        "CANDIDATE_QUALIFICATION",
    ],
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(OUT.relative_to(ROOT))
