#!/usr/bin/env python3
"""Run the bounded native Blockbench repair gate for eight Ashen plants."""

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPRESENTATIVE = HERE.parent / "representative"
sys.path.insert(0, str(REPRESENTATIVE))
import author_representatives as native_gate  # noqa: E402


ASSETS = (
    "cinder_grass",
    "ash_fern",
    "char_shrub",
    "soot_mushroom",
    "magma_moss",
    "glow_root",
    "basalt_flower",
    "ember_vine",
)
SPECS = {
    asset: {"class": "static_custom_geometry_plant", "clips": {}}
    for asset in ASSETS
}
INTEGRATION_COMMIT = "4b4118869e95e9699bd1f480feca573c3e3dca9f"
RECEIPT_NAME = "ashen-plant-native-receipt.json"


def configure_gate() -> None:
    native_gate.SPECS = SPECS
    native_gate.INTEGRATION_COMMIT = INTEGRATION_COMMIT
    native_gate.RECEIPT_NAME = RECEIPT_NAME


def execute(inputs: native_gate.Inputs) -> tuple[int, dict]:
    configure_gate()
    code, receipt = native_gate.execute(inputs)
    receipt["schema"] = "aionforge.wave1.ashen.plant_native.v1"
    receipt["asset_class"] = "static_custom_geometry_plant"
    receipt["proof_scope"] = "BLOCKBENCH_5_1_6_NATIVE_ASHEN_PLANT_SOURCE_AND_CODEC_EXPORT_ONLY"
    receipt["scope_enforcement"] = {
        "exact_lane_assets": list(ASSETS),
        "representative_fire_bloom_edited": False,
        "representative_smoke_reed_edited": False,
        "bp_rp_gameplay_or_authority_edited": False,
    }
    receipt["brief_declared_clips"] = []
    receipt["authored_clip_names"] = []
    receipt["non_claims"] = [
        "BP_RP_RUNTIME_BINDING",
        "GAMEPLAY",
        "BDS",
        "BEDROCK_CLIENT",
        "MULTIPLAYER",
        "PHYSICAL_PS4",
        "MARKETPLACE",
        "RELEASE",
    ]
    (inputs.output / RECEIPT_NAME).write_bytes(
        native_gate.native.canonical_json_bytes(receipt)
    )
    return code, receipt


def parser():
    configure_gate()
    return native_gate.parser()


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        code, receipt = execute(
            native_gate.Inputs(
                args.asset,
                args.bbmodel.resolve(),
                args.texture.resolve(),
                args.geometry.resolve(),
                args.brief.resolve(),
                args.output_dir.resolve(),
                args.cdp_endpoint,
            )
        )
    except (native_gate.RepresentativeError, native_gate.native.NativeToolError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {"status": receipt["status"], "receipt": str(args.output_dir / RECEIPT_NAME)},
            sort_keys=True,
        )
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
