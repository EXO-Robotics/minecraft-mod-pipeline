#!/usr/bin/env python3
"""Native Blockbench repair gate for eight remaining Packet 004 plants.

The shared Skyreach representative gate performs the native save/reopen/export
cycles. This wrapper binds only this frozen plant tranche and authors every
brief-declared semantic clip under the public ``aionbound`` identity.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPRESENTATIVE = HERE.parent / "representative"
sys.path.insert(0, str(REPRESENTATIVE))
import author_representatives as native_gate  # noqa: E402


ASSETS = (
    "cliff_flower",
    "cloud_moss",
    "cloudpuff_plant",
    "floating_blossom",
    "nest_thatch_tuft",
    "rope_root",
    "shelf_shrub",
    "skybloom",
)


def bob():
    return native_gate.clip(
        3.0,
        True,
        0.75,
        {
            "head": [
                native_gate.frames(
                    "position",
                    (0.0, native_gate.ZERO),
                    (0.75, [0.0, 0.35, 0.0]),
                    (1.5, native_gate.ZERO),
                    (2.25, [0.0, -0.18, 0.0]),
                    (3.0, native_gate.ZERO),
                )
            ]
        },
    )


SPECS = {
    "cliff_flower": {"class": "static_custom_geometry_plant", "clips": {}},
    "cloud_moss": {"class": "static_custom_geometry_plant", "clips": {}},
    "cloudpuff_plant": {"class": "animated_custom_geometry_plant", "clips": {"bob": bob()}},
    "floating_blossom": {"class": "animated_custom_geometry_plant", "clips": {"bob": bob()}},
    "nest_thatch_tuft": {"class": "static_custom_geometry_plant", "clips": {}},
    "rope_root": {"class": "static_custom_geometry_plant", "clips": {}},
    "shelf_shrub": {"class": "static_custom_geometry_plant", "clips": {}},
    "skybloom": {"class": "static_custom_geometry_plant", "clips": {}},
}

INTEGRATION_COMMIT = "b65424610976a76ee6507917235d68f048ae249b"
INTEGRATION_TREE = "3f21de0ea75e4fe3344a1bac86e7d3c521129647"
RECEIPT_NAME = "skyreach-plant-native-receipt.json"


def configure_gate() -> None:
    native_gate.SPECS = SPECS
    native_gate.INTEGRATION_COMMIT = INTEGRATION_COMMIT
    native_gate.RECEIPT_NAME = RECEIPT_NAME


def execute(inputs: native_gate.Inputs) -> tuple[int, dict]:
    configure_gate()
    code, receipt = native_gate.execute(inputs)
    receipt["schema"] = "aionforge.wave1.skyreach.plant_native.v1"
    receipt["asset_class"] = SPECS[inputs.asset]["class"]
    receipt["proof_scope"] = "BLOCKBENCH_5_1_6_NATIVE_SKYREACH_PLANT_SOURCE_AND_CODEC_EXPORT_ONLY"
    receipt["scope_enforcement"] = {
        "exact_lane_assets": list(ASSETS),
        "representative_wind_reed_plant_edited": False,
        "representative_hanging_sky_vine_edited": False,
        "bp_rp_gameplay_or_authority_edited": False,
    }
    receipt["non_claims"] = [
        "BP_RP_RUNTIME_BINDING",
        "GAMEPLAY",
        "CREATOR_TOOLS",
        "BDS",
        "BEDROCK_CLIENT",
        "MULTIPLAYER",
        "PHYSICAL_PS4",
        "MARKETPLACE",
        "RELEASE",
    ]
    (inputs.output / RECEIPT_NAME).write_bytes(native_gate.native.canonical_json_bytes(receipt))
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
    print(json.dumps({"status": receipt["status"], "receipt": str(args.output_dir / RECEIPT_NAME)}, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
