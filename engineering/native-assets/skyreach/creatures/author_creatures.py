#!/usr/bin/env python3
"""Author the seven remaining Packet 004 creature projects in native Blockbench."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPRESENTATIVE = HERE.parent / "representative"
sys.path.insert(0, str(REPRESENTATIVE))
import author_representatives as engine  # noqa: E402


INTEGRATION_COMMIT = "b65424610976a76ee6507917235d68f048ae249b"
INTEGRATION_TREE = "3f21de0ea75e4fe3344a1bac86e7d3c521129647"
RECEIPT_NAME = "skyreach-creature-native-receipt.json"
ZERO = engine.ZERO
frames = engine.frames
clip = engine.clip


def gait(duration: float, amount: float, names: tuple[str, ...] = ("leg_fl", "leg_fr", "leg_bl", "leg_br")):
    result = {}
    for index, name in enumerate(names):
        lead = amount if index % 2 == 0 else -amount
        result[name] = [frames("rotation", (0.0, [lead, 0.0, 0.0]), (duration / 2, [-lead, 0.0, 0.0]), (duration, [lead, 0.0, 0.0]))]
    return result


def wings(duration: float, amount: float):
    quarter = duration / 4
    return {
        "wing_l": [frames("rotation", (0.0, [0.0, 0.0, -amount]), (quarter, [0.0, 0.0, amount]), (quarter * 2, [0.0, 0.0, amount]), (quarter * 3, [0.0, 0.0, -amount]), (duration, [0.0, 0.0, -amount]))],
        "wing_r": [frames("rotation", (0.0, [0.0, 0.0, amount]), (quarter, [0.0, 0.0, -amount]), (quarter * 2, [0.0, 0.0, -amount]), (quarter * 3, [0.0, 0.0, amount]), (duration, [0.0, 0.0, amount]))],
    }


SPECS = {
    "cliff_ram": {
        "class": "heavy_ledge_charger",
        "clips": {
            "idle": clip(3.4, True, 0.85, {
                "head": [frames("rotation", (0.0, ZERO), (0.85, [4.0, -5.0, 0.0]), (1.7, ZERO), (2.55, [-2.0, 4.0, 0.0]), (3.4, ZERO))],
                "body": [frames("position", (0.0, ZERO), (0.85, [0.0, 0.12, 0.0]), (1.7, ZERO), (2.55, [0.0, -0.08, 0.0]), (3.4, ZERO))],
            }),
            "walk": clip(1.1, True, 0.275, gait(1.1, 17.0)),
            "charge_pose": clip(0.8, False, 0.38, {
                "head": [frames("rotation", (0.0, ZERO), (0.38, [22.0, 0.0, 0.0]), (0.8, ZERO))],
                "body": [frames("position", (0.0, ZERO), (0.38, [0.0, -0.25, -0.75]), (0.8, ZERO))],
            }),
            "hurt": clip(0.45, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, -9.0]), (0.45, ZERO))]}),
            "death": clip(1.15, False, 1.15, {"body": [frames("rotation", (0.0, ZERO), (1.15, [0.0, 0.0, -86.0]))]}),
        },
    },
    "glide_drake": {
        "class": "hostile_ridge_glider",
        "clips": {
            "idle": clip(3.2, True, 0.8, {
                "head": [frames("rotation", (0.0, ZERO), (0.8, [2.0, -6.0, 0.0]), (1.6, ZERO), (2.4, [1.0, 5.0, 0.0]), (3.2, ZERO))],
                "tail": [frames("rotation", (0.0, [0.0, -5.0, 0.0]), (1.6, [0.0, 6.0, 0.0]), (3.2, [0.0, -5.0, 0.0]))],
            }),
            "glide": clip(1.6, True, 0.4, {
                "wing_l": [frames("rotation", (0.0, [0.0, 0.0, -10.0]), (0.4, [0.0, 0.0, -17.0]), (0.8, [0.0, 0.0, -10.0]), (1.2, [0.0, 0.0, -4.0]), (1.6, [0.0, 0.0, -10.0]))],
                "wing_r": [frames("rotation", (0.0, [0.0, 0.0, 10.0]), (0.4, [0.0, 0.0, 17.0]), (0.8, [0.0, 0.0, 10.0]), (1.2, [0.0, 0.0, 4.0]), (1.6, [0.0, 0.0, 10.0]))],
                "tail": [frames("rotation", (0.0, [0.0, -4.0, 0.0]), (0.8, [0.0, 4.0, 0.0]), (1.6, [0.0, -4.0, 0.0]))],
            }),
            "dive_attack": clip(0.85, False, 0.4, {
                "body": [frames("rotation", (0.0, ZERO), (0.4, [-28.0, 0.0, 0.0]), (0.85, ZERO))],
                "wing_l": [frames("rotation", (0.0, ZERO), (0.4, [0.0, 0.0, 32.0]), (0.85, ZERO))],
                "wing_r": [frames("rotation", (0.0, ZERO), (0.4, [0.0, 0.0, -32.0]), (0.85, ZERO))],
            }),
            "hurt": clip(0.45, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, 10.0]), (0.45, ZERO))]}),
            "death": clip(1.2, False, 1.2, {"body": [frames("rotation", (0.0, ZERO), (1.2, [48.0, 0.0, 86.0]))]}),
        },
    },
    "ropewing": {
        "class": "membrane_shelf_glider",
        "clips": {
            "idle_perch": clip(3.0, True, 0.75, {
                "head": [frames("rotation", (0.0, ZERO), (0.75, [2.0, -7.0, 0.0]), (1.5, ZERO), (2.25, [1.0, 6.0, 0.0]), (3.0, ZERO))],
                "body": [frames("position", (0.0, ZERO), (0.75, [0.0, 0.1, 0.0]), (1.5, ZERO), (2.25, [0.0, -0.06, 0.0]), (3.0, ZERO))],
            }),
            "glide": clip(1.4, True, 0.35, {
                "wing_l": [frames("rotation", (0.0, [0.0, 0.0, -9.0]), (0.7, [0.0, 0.0, -16.0]), (1.4, [0.0, 0.0, -9.0]))],
                "wing_r": [frames("rotation", (0.0, [0.0, 0.0, 9.0]), (0.7, [0.0, 0.0, 16.0]), (1.4, [0.0, 0.0, 9.0]))],
            }),
            "bank": clip(0.75, False, 0.35, {
                "body": [frames("rotation", (0.0, ZERO), (0.35, [0.0, 0.0, 24.0]), (0.75, ZERO))],
                "wing_l": [frames("rotation", (0.0, ZERO), (0.35, [0.0, 0.0, -15.0]), (0.75, ZERO))],
            }),
            "hurt": clip(0.4, False, 0.16, {"body": [frames("rotation", (0.0, ZERO), (0.16, [0.0, 0.0, -10.0]), (0.4, ZERO))]}),
            "death": clip(0.95, False, 0.95, {"body": [frames("rotation", (0.0, ZERO), (0.95, [0.0, 0.0, 88.0]))]}),
        },
    },
    "ruin_harpy": {
        "class": "hostile_biped_ruin_flyer",
        "clips": {
            "idle_perch": clip(3.1, True, 0.775, {
                "head": [frames("rotation", (0.0, ZERO), (0.775, [3.0, -7.0, 0.0]), (1.55, ZERO), (2.325, [1.0, 6.0, 0.0]), (3.1, ZERO))],
                "torso": [frames("position", (0.0, ZERO), (0.775, [0.0, 0.12, 0.0]), (1.55, ZERO), (2.325, [0.0, -0.08, 0.0]), (3.1, ZERO))],
            }),
            "fly": clip(0.8, True, 0.2, wings(0.8, 24.0)),
            "dive_slash": clip(0.72, False, 0.32, {
                "torso": [frames("rotation", (0.0, ZERO), (0.32, [-25.0, 0.0, 0.0]), (0.72, ZERO))],
                "leg_l": [frames("rotation", (0.0, ZERO), (0.32, [27.0, 0.0, 0.0]), (0.72, ZERO))],
                "leg_r": [frames("rotation", (0.0, ZERO), (0.32, [27.0, 0.0, 0.0]), (0.72, ZERO))],
            }),
            "hurt": clip(0.42, False, 0.17, {"torso": [frames("rotation", (0.0, ZERO), (0.17, [0.0, 0.0, 10.0]), (0.42, ZERO))]}),
            "death": clip(1.05, False, 1.05, {"torso": [frames("rotation", (0.0, ZERO), (1.05, [42.0, 0.0, 87.0]))]}),
        },
    },
    "sky_fox": {
        "class": "agile_cliff_path_runner",
        "clips": {
            "idle": clip(3.2, True, 0.8, {
                "head": [frames("rotation", (0.0, ZERO), (0.8, [3.0, -6.0, 0.0]), (1.6, ZERO), (2.4, [1.0, 5.0, 0.0]), (3.2, ZERO))],
                "tail": [frames("rotation", (0.0, [0.0, -6.0, 0.0]), (1.6, [0.0, 7.0, 0.0]), (3.2, [0.0, -6.0, 0.0]))],
            }),
            "trot": clip(0.8, True, 0.2, gait(0.8, 21.0) | {
                "tail": [frames("rotation", (0.0, [0.0, -8.0, 0.0]), (0.4, [0.0, 8.0, 0.0]), (0.8, [0.0, -8.0, 0.0]))],
            }),
            "leap": clip(0.8, False, 0.38, {
                "body": [frames("position", (0.0, ZERO), (0.18, [0.0, -0.2, 0.3]), (0.42, [0.0, 1.35, -1.0]), (0.8, ZERO))],
                "leg_fl": [frames("rotation", (0.0, ZERO), (0.38, [-26.0, 0.0, 0.0]), (0.8, ZERO))],
                "leg_fr": [frames("rotation", (0.0, ZERO), (0.38, [-26.0, 0.0, 0.0]), (0.8, ZERO))],
            }),
            "hurt": clip(0.4, False, 0.16, {"body": [frames("rotation", (0.0, ZERO), (0.16, [0.0, 0.0, -10.0]), (0.4, ZERO))]}),
            "death": clip(1.0, False, 1.0, {"body": [frames("rotation", (0.0, ZERO), (1.0, [0.0, 0.0, -87.0]))]}),
        },
    },
    "stone_vulture": {
        "class": "ruin_scavenger_flyer",
        "clips": {
            "idle_perch": clip(3.5, True, 0.875, {
                "head": [frames("rotation", (0.0, ZERO), (0.875, [4.0, -8.0, 0.0]), (1.75, ZERO), (2.625, [2.0, 7.0, 0.0]), (3.5, ZERO))],
                "body": [frames("position", (0.0, ZERO), (0.875, [0.0, 0.1, 0.0]), (1.75, ZERO), (2.625, [0.0, -0.06, 0.0]), (3.5, ZERO))],
            }),
            "fly": clip(0.9, True, 0.225, wings(0.9, 22.0)),
            "feed_pose": clip(0.8, False, 0.38, {
                "head": [frames("rotation", (0.0, ZERO), (0.22, [18.0, 0.0, 0.0]), (0.42, [34.0, 0.0, 0.0]), (0.8, ZERO))],
                "body": [frames("position", (0.0, ZERO), (0.38, [0.0, -0.18, -0.25]), (0.8, ZERO))],
            }),
            "hurt": clip(0.42, False, 0.17, {"body": [frames("rotation", (0.0, ZERO), (0.17, [0.0, 0.0, 9.0]), (0.42, ZERO))]}),
            "death": clip(1.0, False, 1.0, {"body": [frames("rotation", (0.0, ZERO), (1.0, [0.0, 0.0, 87.0]))]}),
        },
    },
    "storm_gull": {
        "class": "ambient_shelf_scavenger_flyer",
        "clips": {
            "idle_perch": clip(3.0, True, 0.75, {
                "head": [frames("rotation", (0.0, ZERO), (0.75, [2.0, -8.0, 0.0]), (1.5, ZERO), (2.25, [1.0, 7.0, 0.0]), (3.0, ZERO))],
                "body": [frames("position", (0.0, ZERO), (0.75, [0.0, 0.08, 0.0]), (1.5, ZERO), (2.25, [0.0, -0.05, 0.0]), (3.0, ZERO))],
            }),
            "fly": clip(0.7, True, 0.175, wings(0.7, 26.0)),
            "glide": clip(1.5, True, 0.375, {
                "wing_l": [frames("rotation", (0.0, [0.0, 0.0, -9.0]), (0.75, [0.0, 0.0, -15.0]), (1.5, [0.0, 0.0, -9.0]))],
                "wing_r": [frames("rotation", (0.0, [0.0, 0.0, 9.0]), (0.75, [0.0, 0.0, 15.0]), (1.5, [0.0, 0.0, 9.0]))],
            }),
            "land": clip(0.75, False, 0.35, {
                "body": [frames("rotation", (0.0, [-12.0, 0.0, 0.0]), (0.35, [8.0, 0.0, 0.0]), (0.75, ZERO))],
                "leg_l": [frames("rotation", (0.0, [-18.0, 0.0, 0.0]), (0.35, [16.0, 0.0, 0.0]), (0.75, ZERO))],
                "leg_r": [frames("rotation", (0.0, [-18.0, 0.0, 0.0]), (0.35, [16.0, 0.0, 0.0]), (0.75, ZERO))],
            }),
            "hurt": clip(0.38, False, 0.15, {"body": [frames("rotation", (0.0, ZERO), (0.15, [0.0, 0.0, -10.0]), (0.38, ZERO))]}),
            "death": clip(0.9, False, 0.9, {"body": [frames("rotation", (0.0, ZERO), (0.9, [0.0, 0.0, -88.0]))]}),
        },
    },
}


def configure_engine() -> None:
    engine.SPECS = SPECS
    engine.INTEGRATION_COMMIT = INTEGRATION_COMMIT
    engine.RECEIPT_NAME = RECEIPT_NAME


def execute(inputs: engine.Inputs):
    configure_engine()
    code, receipt = engine.execute(inputs)
    receipt["schema"] = "aionforge.wave1.skyreach.creature_native.v1"
    receipt["proof_scope"] = "BLOCKBENCH_NATIVE_CREATURE_EDITABLE_AND_CODEC_REPAIR_ONLY"
    receipt["portfolio_class"] = receipt.pop("representative_class")
    receipt["integration_authority"]["tree"] = INTEGRATION_TREE
    (inputs.output / RECEIPT_NAME).write_bytes(engine.native.canonical_json_bytes(receipt))
    return code, receipt


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--asset", required=True, choices=sorted(SPECS))
    result.add_argument("--bbmodel", required=True, type=Path)
    result.add_argument("--texture", required=True, type=Path)
    result.add_argument("--geometry", required=True, type=Path)
    result.add_argument("--brief", required=True, type=Path)
    result.add_argument("--output-dir", required=True, type=Path)
    result.add_argument("--cdp-endpoint", required=True)
    return result


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        code, receipt = execute(engine.Inputs(args.asset, args.bbmodel.resolve(), args.texture.resolve(), args.geometry.resolve(), args.brief.resolve(), args.output_dir.resolve(), args.cdp_endpoint))
    except (engine.RepresentativeError, engine.native.NativeToolError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"status": receipt["status"], "receipt": str(args.output_dir / RECEIPT_NAME)}, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
