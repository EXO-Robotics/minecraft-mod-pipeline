#!/usr/bin/env python3
"""Native Blockbench repair gate for eight remaining Packet 003 plants.

The shared representative gate performs the actual native save/reopen/export
cycles.  This wrapper binds only the frozen plant briefs in this tranche and
authors every declared semantic clip under the public ``aionbound`` identity.
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
    "crystal_lily",
    "prism_bloom",
    "glass_moss",
    "marsh_fern",
    "glow_kelp",
    "mire_orchid",
    "pearl_grass",
    "crystal_vine",
)


def glow_idle():
    return native_gate.clip(
        3.2,
        True,
        0.8,
        {
            "chassis": [
                native_gate.frames(
                    "scale",
                    (0.0, [1.0, 1.0, 1.0]),
                    (0.8, [1.012, 1.02, 1.012]),
                    (1.6, [1.025, 1.035, 1.025]),
                    (2.4, [1.012, 1.02, 1.012]),
                    (3.2, [1.0, 1.0, 1.0]),
                )
            ]
        },
    )


def sway():
    return native_gate.clip(
        4.0,
        True,
        1.0,
        {
            "stem": [
                native_gate.frames(
                    "rotation",
                    (0.0, native_gate.ZERO),
                    (1.0, [0.7, 0.0, 2.5]),
                    (2.0, native_gate.ZERO),
                    (3.0, [-0.5, 0.0, -2.0]),
                    (4.0, native_gate.ZERO),
                )
            ],
            "head": [
                native_gate.frames(
                    "rotation",
                    (0.0, native_gate.ZERO),
                    (1.0, [0.4, 0.0, 1.3]),
                    (2.0, native_gate.ZERO),
                    (3.0, [-0.3, 0.0, -1.0]),
                    (4.0, native_gate.ZERO),
                )
            ],
        },
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
    "crystal_lily": {"class": "animated_custom_geometry_plant", "clips": {"glow_idle": glow_idle()}},
    "prism_bloom": {"class": "animated_custom_geometry_plant", "clips": {"glow_idle": glow_idle()}},
    "glass_moss": {"class": "static_custom_geometry_plant", "clips": {}},
    "marsh_fern": {"class": "animated_custom_geometry_plant", "clips": {"sway": sway()}},
    "glow_kelp": {"class": "animated_custom_geometry_plant", "clips": {"bob": bob()}},
    "mire_orchid": {"class": "static_custom_geometry_plant", "clips": {}},
    "pearl_grass": {"class": "animated_custom_geometry_plant", "clips": {"sway": sway()}},
    "crystal_vine": {"class": "static_custom_geometry_plant", "clips": {}},
}

INTEGRATION_COMMIT = "75b773c6330a3dceb48841c1bebd3b8e1c58da76"
INTEGRATION_TREE = "a5dfbf0b9b3b36dcb9e293264d2a1165cfcad221"
RECEIPT_NAME = "crystal-marsh-plant-native-receipt.json"


def configure_gate() -> None:
    native_gate.SPECS = SPECS
    native_gate.INTEGRATION_COMMIT = INTEGRATION_COMMIT
    native_gate.RECEIPT_NAME = RECEIPT_NAME


def execute(inputs: native_gate.Inputs) -> tuple[int, dict]:
    configure_gate()
    code, receipt = native_gate.execute(inputs)
    receipt["schema"] = "aionforge.wave1.crystal_marsh.plant_native.v1"
    receipt["asset_class"] = SPECS[inputs.asset]["class"]
    receipt["proof_scope"] = "BLOCKBENCH_5_1_6_NATIVE_CRYSTAL_MARSH_PLANT_SOURCE_AND_CODEC_EXPORT_ONLY"
    receipt["scope_enforcement"] = {
        "exact_lane_assets": list(ASSETS),
        "representative_bubble_pod_edited": False,
        "representative_flood_reed_edited": False,
        "bp_rp_gameplay_or_authority_edited": False,
    }
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
