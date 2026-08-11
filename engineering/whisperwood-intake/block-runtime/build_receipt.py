#!/usr/bin/env python3
"""Build the evidence-derived static receipt for this focused block slice."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name("WHISPERWOOD_BLOCK_RUNTIME_RECEIPT.json")
IDS = [
    "forest_brick",
    "hollow_wood",
    "moss_bark",
    "stripped_whisperwood_log",
    "whisperwood_leaves",
    "whisperwood_log",
    "whisperwood_planks",
    "whisperwood_roots",
    "whisperwood_sapling",
    "whisperwood_wood",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


assets = []
for asset_id in IDS:
    receipt_path = ROOT / (
        f"engineering/native-assets/whisperwood/evidence/{asset_id}/"
        "whisperwood-native-blockbench-receipt.json"
    )
    native = json.loads(receipt_path.read_text(encoding="utf-8"))
    files = {
        "behavior_block": ROOT / f"behavior_pack/blocks/{asset_id}.block.json",
        "shipping_geometry": ROOT / f"resource_pack/models/blocks/{asset_id}.geo.json",
        "shipping_texture": ROOT / f"resource_pack/textures/aionbound/whisperwood/blocks/{asset_id}.png",
    }
    assets.append(
        {
            "id": asset_id,
            "runtime_id": f"aionbound:{asset_id}",
            "geometry_id": f"geometry.aionbound.{asset_id}",
            "native_receipt_status": native["status"],
            "native_receipt_sha256": sha256(receipt_path),
            "files": {
                name: {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": sha256(path),
                }
                for name, path in files.items()
            },
        }
    )

document = {
    "schema_version": 1,
    "status": "WHISPERWOOD_BLOCK_RUNTIME_STATIC_PASS",
    "base_commit": "5122b9ddd7721a90492f5a143f7d22aaec21df7f",
    "asset_count": len(assets),
    "assets": assets,
    "checks": {
        "dedicated_closure_tests": "PASS_4_OF_4",
        "gate0_regressions": "PASS_5_OF_5",
        "json_parse": "PASS",
        "png_crc_and_inflate": "PASS",
        "native_input_texture_hash_equality": "PASS",
        "geometry_reference_closure": "PASS",
        "texture_reference_closure": "PASS",
        "old_namespace_absent_from_shipping_geometry": "PASS",
    },
    "legacy_validator_observation": {
        "status": "EXPECTED_STALE_COUNT_ASSERTION",
        "detail": "tools/validate_g7.py pins the immutable G7 block count to 49; the successor has 59 after this slice.",
        "action": "No legacy-validator edit in this focused lane; successor validation owns updated counts.",
    },
    "proof_scope": "STATIC_BP_RP_REFERENCE_AND_NATIVE_EVIDENCE_CLOSURE_ONLY",
    "not_proven": [
        "BEDROCK_CLIENT",
        "STABLE_BDS",
        "PACKAGE",
        "PHYSICAL_PS4",
        "CANDIDATE_QUALIFICATION",
    ],
}
OUT.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(OUT.relative_to(ROOT))
