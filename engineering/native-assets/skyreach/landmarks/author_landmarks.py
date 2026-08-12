#!/usr/bin/env python3
"""Run the bounded native Blockbench repair gate for eight Skyreach landmarks."""

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPRESENTATIVE = HERE.parent / "representative"
sys.path.insert(0, str(REPRESENTATIVE))
import author_representatives as native_gate  # noqa: E402


ASSETS = (
    "ancient_sky_arch",
    "broken_sky_path",
    "cliff_beacon",
    "cliff_outpost",
    "floating_ruin_floor",
    "hanging_lift_frame",
    "nest_platform",
    "rope_bridge",
)
SPECS = {
    asset: {"class": "static_custom_geometry_landmark_visual", "clips": {}}
    for asset in ASSETS
}
SPECS["cliff_beacon"] = {
    "class": "animated_custom_geometry_landmark_visual",
    "clips": {
        "flame_idle": native_gate.clip(
            3.2,
            True,
            0.8,
            {
                "top": [
                    native_gate.frames(
                        "scale",
                        (0.0, [1.0, 1.0, 1.0]),
                        (0.8, [0.94, 1.10, 0.94]),
                        (1.6, [1.05, 0.96, 1.05]),
                        (2.4, [0.97, 1.06, 0.97]),
                        (3.2, [1.0, 1.0, 1.0]),
                    )
                ]
            },
        )
    },
}
INTEGRATION_COMMIT = "9b08e44d82cac7a83a23478c0fd233fecae1540a"
RECEIPT_NAME = "skyreach-landmark-native-receipt.json"


def configure_gate() -> None:
    native_gate.SPECS = SPECS
    native_gate.INTEGRATION_COMMIT = INTEGRATION_COMMIT
    native_gate.RECEIPT_NAME = RECEIPT_NAME


def execute(inputs: native_gate.Inputs) -> tuple[int, dict]:
    configure_gate()
    code, receipt = native_gate.execute(inputs)
    receipt["schema"] = "aionforge.wave1.skyreach.landmark_native.v1"
    receipt["asset_class"] = SPECS[inputs.asset]["class"]
    receipt["proof_scope"] = "BLOCKBENCH_5_1_6_NATIVE_SKYREACH_LANDMARK_VISUAL_SOURCE_AND_CODEC_EXPORT_ONLY"
    receipt["scope_enforcement"] = {
        "exact_lane_assets": list(ASSETS),
        "representative_wind_shrine_edited": False,
        "representative_observation_tower_edited": False,
        "mcstructure_assembly_authored_or_proven": False,
        "bp_rp_gameplay_or_authority_edited": False,
    }
    receipt["non_claims"] = [
        "MCSTRUCTURE_ASSEMBLY",
        "WORLDGEN_PLACEMENT",
        "BP_RP_RUNTIME_BINDING",
        "GAMEPLAY",
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
