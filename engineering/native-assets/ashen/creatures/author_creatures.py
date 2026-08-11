#!/usr/bin/env python3
"""Author the seven remaining Packet 002 creature projects in native Blockbench."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPRESENTATIVE = HERE.parent / "representative"
sys.path.insert(0, str(REPRESENTATIVE))
import author_representatives as engine  # noqa: E402


INTEGRATION_COMMIT = "4b4118869e95e9699bd1f480feca573c3e3dca9f"
RECEIPT_NAME = "ashen-creature-native-receipt.json"
ZERO = engine.ZERO
frames = engine.frames
clip = engine.clip


def gait(duration: float, amount: float, names: tuple[str, ...] = ("leg_fl", "leg_fr", "leg_bl", "leg_br")):
    result = {}
    for index, name in enumerate(names):
        lead = amount if index % 2 == 0 else -amount
        result[name] = [frames("rotation", (0.0, [lead, 0.0, 0.0]), (duration / 2, [-lead, 0.0, 0.0]), (duration, [lead, 0.0, 0.0]))]
    return result


SPECS = {
    "ash_mite": {
        "class": "ambient_ground_creature",
        "clips": {
            "idle": clip(2.8, True, 0.7, {"body": [frames("rotation", (0.0, ZERO), (0.7, [1.5, 0.0, 0.0]), (1.4, ZERO), (2.1, [-1.0, 0.0, 0.0]), (2.8, ZERO))]}),
            "skitter": clip(0.6, True, 0.15, gait(0.6, 24.0, ("leg_a", "leg_b", "leg_c", "leg_d"))),
            "hurt": clip(0.35, False, 0.14, {"body": [frames("rotation", (0.0, ZERO), (0.14, [0.0, 0.0, 13.0]), (0.35, ZERO))]}),
            "death": clip(0.7, False, 0.7, {"body": [frames("rotation", (0.0, ZERO), (0.7, [0.0, 0.0, 88.0]))]}),
        },
    },
    "magma_lizard": {
        "class": "neutral_ground_creature",
        "clips": {
            "idle": clip(3.2, True, 0.8, {"head": [frames("rotation", (0.0, ZERO), (0.8, [3.0, -6.0, 0.0]), (1.6, ZERO), (2.4, [2.0, 5.0, 0.0]), (3.2, ZERO))], "tail": [frames("rotation", (0.0, ZERO), (0.8, [0.0, 6.0, 0.0]), (1.6, ZERO), (2.4, [0.0, -5.0, 0.0]), (3.2, ZERO))]}),
            "walk": clip(1.1, True, 0.275, gait(1.1, 16.0) | {"tail": [frames("rotation", (0.0, [0.0, -5.0, 0.0]), (0.55, [0.0, 5.0, 0.0]), (1.1, [0.0, -5.0, 0.0]))]}),
            "lunge_bite": clip(0.75, False, 0.36, {"body": [frames("position", (0.0, ZERO), (0.2, [0.0, 0.0, 0.4]), (0.4, [0.0, 0.0, -1.2]), (0.75, ZERO))], "head": [frames("rotation", (0.0, ZERO), (0.2, [-10.0, 0.0, 0.0]), (0.4, [20.0, 0.0, 0.0]), (0.75, ZERO))]}),
            "hurt": clip(0.42, False, 0.17, {"body": [frames("rotation", (0.0, ZERO), (0.17, [0.0, 0.0, -9.0]), (0.42, ZERO))]}),
            "death": clip(1.0, False, 1.0, {"body": [frames("rotation", (0.0, ZERO), (1.0, [0.0, 0.0, -86.0]))]}),
        },
    },
    "furnace_beetle": {
        "class": "hostile_armored_ground_creature",
        "clips": {
            "idle": clip(3.0, True, 0.75, {"head": [frames("rotation", (0.0, ZERO), (0.75, [2.0, -4.0, 0.0]), (1.5, ZERO), (2.25, [1.0, 4.0, 0.0]), (3.0, ZERO))]}),
            "walk": clip(1.0, True, 0.25, gait(1.0, 17.0, ("leg_fl", "leg_fr", "leg_ml", "leg_mr", "leg_bl", "leg_br"))),
            "charge": clip(0.65, True, 0.16, gait(0.65, 27.0, ("leg_fl", "leg_fr", "leg_ml", "leg_mr", "leg_bl", "leg_br")) | {"body": [frames("rotation", (0.0, [-6.0, 0.0, 0.0]), (0.325, [-9.0, 0.0, 0.0]), (0.65, [-6.0, 0.0, 0.0]))]}),
            "mandible_clamp": clip(0.55, False, 0.26, {"head": [frames("rotation", (0.0, ZERO), (0.16, [-12.0, 0.0, 0.0]), (0.28, [14.0, 0.0, 0.0]), (0.55, ZERO))]}),
            "hurt": clip(0.4, False, 0.16, {"body": [frames("rotation", (0.0, ZERO), (0.16, [0.0, 0.0, 8.0]), (0.4, ZERO))]}),
            "death": clip(1.05, False, 1.05, {"body": [frames("rotation", (0.0, ZERO), (1.05, [0.0, 0.0, 87.0]))]}),
        },
    },
    "char_wolf": {
        "class": "hostile_pack_predator",
        "clips": {
            "idle": clip(3.4, True, 0.85, {"head": [frames("rotation", (0.0, ZERO), (0.85, [4.0, -7.0, 0.0]), (1.7, ZERO), (2.55, [2.0, 6.0, 0.0]), (3.4, ZERO))], "tail": [frames("rotation", (0.0, ZERO), (0.85, [0.0, 0.0, 7.0]), (1.7, ZERO), (2.55, [0.0, 0.0, -6.0]), (3.4, ZERO))]}),
            "walk": clip(1.0, True, 0.25, gait(1.0, 18.0)),
            "run": clip(0.7, True, 0.175, gait(0.7, 30.0) | {"body": [frames("position", (0.0, ZERO), (0.175, [0.0, 0.25, 0.0]), (0.35, ZERO), (0.525, [0.0, -0.15, 0.0]), (0.7, ZERO))]}),
            "snarl_attack": clip(0.7, False, 0.34, {"head": [frames("rotation", (0.0, ZERO), (0.2, [-13.0, 0.0, 0.0]), (0.38, [18.0, 0.0, 0.0]), (0.7, ZERO))], "body": [frames("position", (0.0, ZERO), (0.38, [0.0, 0.0, -1.0]), (0.7, ZERO))]}),
            "hurt": clip(0.42, False, 0.17, {"body": [frames("rotation", (0.0, ZERO), (0.17, [0.0, 0.0, -10.0]), (0.42, ZERO))]}),
            "death": clip(1.05, False, 1.05, {"body": [frames("rotation", (0.0, ZERO), (1.05, [0.0, 0.0, -88.0]))]}),
        },
    },
    "cinder_lynx": {
        "class": "hostile_stalking_predator",
        "clips": {
            "idle": clip(3.3, True, 0.825, {"head": [frames("rotation", (0.0, ZERO), (0.825, [3.0, 6.0, 0.0]), (1.65, ZERO), (2.475, [2.0, -7.0, 0.0]), (3.3, ZERO))], "tail": [frames("rotation", (0.0, [0.0, -4.0, 0.0]), (1.65, [0.0, 5.0, 0.0]), (3.3, [0.0, -4.0, 0.0]))]}),
            "stalk": clip(1.25, True, 0.3125, gait(1.25, 12.0) | {"body": [frames("position", (0.0, [0.0, -0.35, 0.0]), (0.625, [0.0, -0.5, 0.0]), (1.25, [0.0, -0.35, 0.0]))]}),
            "pounce_pose": clip(0.85, False, 0.44, {"body": [frames("position", (0.0, ZERO), (0.28, [0.0, -0.35, 0.45]), (0.48, [0.0, 0.85, -1.1]), (0.85, ZERO))], "head": [frames("rotation", (0.0, ZERO), (0.28, [-8.0, 0.0, 0.0]), (0.48, [12.0, 0.0, 0.0]), (0.85, ZERO))]}),
            "hurt": clip(0.4, False, 0.16, {"body": [frames("rotation", (0.0, ZERO), (0.16, [0.0, 0.0, 10.0]), (0.4, ZERO))]}),
            "death": clip(1.0, False, 1.0, {"body": [frames("rotation", (0.0, ZERO), (1.0, [0.0, 0.0, 87.0]))]}),
        },
    },
    "soot_stag": {
        "class": "neutral_large_ground_creature",
        "clips": {
            "idle": clip(3.6, True, 0.9, {"head": [frames("rotation", (0.0, ZERO), (0.9, [5.0, -5.0, 0.0]), (1.8, ZERO), (2.7, [3.0, 6.0, 0.0]), (3.6, ZERO))], "tail": [frames("rotation", (0.0, ZERO), (0.9, [0.0, 0.0, 5.0]), (1.8, ZERO), (2.7, [0.0, 0.0, -4.0]), (3.6, ZERO))]}),
            "walk": clip(1.15, True, 0.2875, gait(1.15, 17.0)),
            "trot": clip(0.78, True, 0.195, gait(0.78, 27.0) | {"body": [frames("position", (0.0, ZERO), (0.195, [0.0, 0.3, 0.0]), (0.39, ZERO), (0.585, [0.0, -0.18, 0.0]), (0.78, ZERO))]}),
            "antler_shake": clip(0.9, False, 0.45, {"head": [frames("rotation", (0.0, ZERO), (0.2, [-5.0, -13.0, -4.0]), (0.45, [3.0, 14.0, 5.0]), (0.7, [-2.0, -7.0, -2.0]), (0.9, ZERO))]}),
            "hurt": clip(0.45, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, -8.0]), (0.45, ZERO))]}),
            "death": clip(1.15, False, 1.15, {"body": [frames("rotation", (0.0, ZERO), (1.15, [0.0, 0.0, -86.0]))]}),
        },
    },
    "basalt_tortoise": {
        "class": "neutral_armored_ground_creature",
        "clips": {
            "idle": clip(3.8, True, 0.95, {"head": [frames("position", (0.0, ZERO), (0.95, [0.0, 0.0, -0.15]), (1.9, ZERO), (2.85, [0.0, 0.0, 0.12]), (3.8, ZERO))]}),
            "slow_walk": clip(1.5, True, 0.375, gait(1.5, 12.0)),
            "withdraw_pose": clip(0.9, False, 0.5, {"head": [frames("position", (0.0, ZERO), (0.5, [0.0, 0.0, 1.1]), (0.9, ZERO))], "leg_fl": [frames("rotation", (0.0, ZERO), (0.5, [-18.0, 0.0, 0.0]), (0.9, ZERO))], "leg_fr": [frames("rotation", (0.0, ZERO), (0.5, [-18.0, 0.0, 0.0]), (0.9, ZERO))]}),
            "hurt": clip(0.48, False, 0.2, {"body": [frames("rotation", (0.0, ZERO), (0.2, [0.0, 0.0, 6.0]), (0.48, ZERO))]}),
            "death": clip(1.2, False, 1.2, {"body": [frames("rotation", (0.0, ZERO), (1.2, [0.0, 0.0, 82.0]))]}),
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
    receipt["schema"] = "aionforge.wave1.ashen.creature_native.v1"
    receipt["proof_scope"] = "BLOCKBENCH_NATIVE_CREATURE_EDITABLE_AND_CODEC_REPAIR_ONLY"
    receipt["portfolio_class"] = receipt.pop("representative_class")
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
