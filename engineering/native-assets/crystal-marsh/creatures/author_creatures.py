#!/usr/bin/env python3
"""Author the seven remaining Packet 003 creature projects in native Blockbench."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPRESENTATIVE = HERE.parent / "representative"
sys.path.insert(0, str(REPRESENTATIVE))
import author_representatives as engine  # noqa: E402


INTEGRATION_COMMIT = "13c24ac77fe4383e0a1be52671424c0fdf82eaf0"
INTEGRATION_TREE = "08d0721a29192991a63be908735b447ccbef91b6"
RECEIPT_NAME = "crystal-marsh-creature-native-receipt.json"
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
    "crystal_newt": {
        "class": "neutral_amphibious_ground_creature",
        "clips": {
            "idle": clip(3.2, True, 0.8, {
                "head": [frames("rotation", (0.0, ZERO), (0.8, [3.0, -6.0, 0.0]), (1.6, ZERO), (2.4, [2.0, 5.0, 0.0]), (3.2, ZERO))],
                "tail": [frames("rotation", (0.0, [0.0, -5.0, 0.0]), (1.6, [0.0, 6.0, 0.0]), (3.2, [0.0, -5.0, 0.0]))],
            }),
            "walk": clip(1.15, True, 0.2875, gait(1.15, 15.0) | {
                "tail": [frames("rotation", (0.0, [0.0, -7.0, 0.0]), (0.575, [0.0, 7.0, 0.0]), (1.15, [0.0, -7.0, 0.0]))],
            }),
            "frill_raise": clip(0.85, False, 0.42, {
                "head": [frames("rotation", (0.0, ZERO), (0.42, [-11.0, 0.0, 0.0]), (0.85, ZERO))],
                "body": [frames("position", (0.0, ZERO), (0.42, [0.0, 0.3, 0.0]), (0.85, ZERO))],
            }),
            "bite": clip(0.62, False, 0.3, {
                "head": [frames("rotation", (0.0, ZERO), (0.18, [-10.0, 0.0, 0.0]), (0.32, [19.0, 0.0, 0.0]), (0.62, ZERO))],
            }),
            "hurt": clip(0.42, False, 0.17, {"body": [frames("rotation", (0.0, ZERO), (0.17, [0.0, 0.0, -9.0]), (0.42, ZERO))]}),
            "death": clip(1.0, False, 1.0, {"body": [frames("rotation", (0.0, ZERO), (1.0, [0.0, 0.0, -86.0]))]}),
        },
    },
    "prism_frog": {
        "class": "ambient_amphibious_hopper",
        "clips": {
            "idle": clip(3.0, True, 0.75, {
                "body": [frames("scale", (0.0, [1.0, 1.0, 1.0]), (0.75, [1.025, 0.975, 1.025]), (1.5, [1.0, 1.0, 1.0]), (2.25, [0.985, 1.02, 0.985]), (3.0, [1.0, 1.0, 1.0]))],
            }),
            "hop": clip(0.8, False, 0.38, {
                "body": [frames("position", (0.0, ZERO), (0.18, [0.0, -0.25, 0.25]), (0.42, [0.0, 1.5, -1.0]), (0.8, ZERO))],
                "leg_bl": [frames("rotation", (0.0, ZERO), (0.18, [28.0, 0.0, 0.0]), (0.42, [-18.0, 0.0, 0.0]), (0.8, ZERO))],
                "leg_br": [frames("rotation", (0.0, ZERO), (0.18, [28.0, 0.0, 0.0]), (0.42, [-18.0, 0.0, 0.0]), (0.8, ZERO))],
            }),
            "swim_pose": clip(0.9, True, 0.225, gait(0.9, 18.0)),
            "hurt": clip(0.38, False, 0.15, {"body": [frames("rotation", (0.0, ZERO), (0.15, [0.0, 0.0, 12.0]), (0.38, ZERO))]}),
            "death": clip(0.85, False, 0.85, {"body": [frames("rotation", (0.0, ZERO), (0.85, [0.0, 0.0, 88.0]))]}),
        },
    },
    "glass_heron": {
        "class": "neutral_tall_wading_bird",
        "clips": {
            "idle": clip(3.6, True, 0.9, {
                "head": [frames("rotation", (0.0, ZERO), (0.9, [4.0, -8.0, 0.0]), (1.8, ZERO), (2.7, [3.0, 7.0, 0.0]), (3.6, ZERO))],
            }),
            "walk_wade": clip(1.3, True, 0.325, {
                "leg_l": [frames("rotation", (0.0, [20.0, 0.0, 0.0]), (0.65, [-20.0, 0.0, 0.0]), (1.3, [20.0, 0.0, 0.0]))],
                "leg_r": [frames("rotation", (0.0, [-20.0, 0.0, 0.0]), (0.65, [20.0, 0.0, 0.0]), (1.3, [-20.0, 0.0, 0.0]))],
                "body": [frames("position", (0.0, ZERO), (0.325, [0.0, 0.22, 0.0]), (0.65, ZERO), (0.975, [0.0, 0.16, 0.0]), (1.3, ZERO))],
            }),
            "spear_strike": clip(0.78, False, 0.36, {
                "head": [frames("rotation", (0.0, ZERO), (0.2, [-18.0, 0.0, 0.0]), (0.4, [33.0, 0.0, 0.0]), (0.78, ZERO))],
                "body": [frames("position", (0.0, ZERO), (0.4, [0.0, 0.0, -0.75]), (0.78, ZERO))],
            }),
            "flap": clip(0.75, True, 0.1875, {
                "wing_l": [frames("rotation", (0.0, [0.0, 0.0, -20.0]), (0.1875, [0.0, 0.0, 42.0]), (0.375, [0.0, 0.0, 20.0]), (0.5625, [0.0, 0.0, -42.0]), (0.75, [0.0, 0.0, -20.0]))],
                "wing_r": [frames("rotation", (0.0, [0.0, 0.0, 20.0]), (0.1875, [0.0, 0.0, -42.0]), (0.375, [0.0, 0.0, -20.0]), (0.5625, [0.0, 0.0, 42.0]), (0.75, [0.0, 0.0, 20.0]))],
            }),
            "hurt": clip(0.45, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, -8.0]), (0.45, ZERO))]}),
            "death": clip(1.15, False, 1.15, {"body": [frames("rotation", (0.0, ZERO), (1.15, [0.0, 0.0, -87.0]))]}),
        },
    },
    "mire_turtle": {
        "class": "neutral_armored_amphibious_creature",
        "clips": {
            "idle": clip(3.8, True, 0.95, {
                "head": [frames("position", (0.0, ZERO), (0.95, [0.0, 0.0, -0.14]), (1.9, ZERO), (2.85, [0.0, 0.0, 0.11]), (3.8, ZERO))],
            }),
            "walk": clip(1.55, True, 0.3875, gait(1.55, 11.0)),
            "swim": clip(1.0, True, 0.25, gait(1.0, 17.0) | {
                "body": [frames("rotation", (0.0, [0.0, -2.5, 0.0]), (0.5, [0.0, 2.5, 0.0]), (1.0, [0.0, -2.5, 0.0]))],
            }),
            "withdraw": clip(0.92, False, 0.5, {
                "head": [frames("position", (0.0, ZERO), (0.5, [0.0, 0.0, 1.2]), (0.92, ZERO))],
                "leg_fl": [frames("rotation", (0.0, ZERO), (0.5, [-17.0, 0.0, 0.0]), (0.92, ZERO))],
                "leg_fr": [frames("rotation", (0.0, ZERO), (0.5, [-17.0, 0.0, 0.0]), (0.92, ZERO))],
            }),
            "hurt": clip(0.48, False, 0.2, {"body": [frames("rotation", (0.0, ZERO), (0.2, [0.0, 0.0, 6.0]), (0.48, ZERO))]}),
            "death": clip(1.2, False, 1.2, {"body": [frames("rotation", (0.0, ZERO), (1.2, [0.0, 0.0, 82.0]))]}),
        },
    },
    "bloom_crab": {
        "class": "neutral_crustacean_ground_creature",
        "clips": {
            "idle": clip(3.0, True, 0.75, {
                "claw_l": [frames("rotation", (0.0, ZERO), (0.75, [0.0, -5.0, -3.0]), (1.5, ZERO), (2.25, [0.0, 4.0, 2.0]), (3.0, ZERO))],
                "claw_r": [frames("rotation", (0.0, ZERO), (0.75, [0.0, 5.0, 3.0]), (1.5, ZERO), (2.25, [0.0, -4.0, -2.0]), (3.0, ZERO))],
            }),
            "scuttle": clip(0.7, True, 0.175, gait(0.7, 22.0, ("leg_a", "leg_b", "leg_c", "leg_d")) | {
                "body": [frames("position", (0.0, ZERO), (0.175, [0.18, 0.1, 0.0]), (0.35, ZERO), (0.525, [-0.18, 0.08, 0.0]), (0.7, ZERO))],
            }),
            "claw_snap": clip(0.58, False, 0.28, {
                "claw_l": [frames("rotation", (0.0, ZERO), (0.16, [0.0, -18.0, -14.0]), (0.3, [0.0, 10.0, 12.0]), (0.58, ZERO))],
                "claw_r": [frames("rotation", (0.0, ZERO), (0.16, [0.0, 18.0, 14.0]), (0.3, [0.0, -10.0, -12.0]), (0.58, ZERO))],
            }),
            "hurt": clip(0.4, False, 0.16, {"body": [frames("rotation", (0.0, ZERO), (0.16, [0.0, 0.0, 10.0]), (0.4, ZERO))]}),
            "death": clip(0.95, False, 0.95, {"body": [frames("rotation", (0.0, ZERO), (0.95, [0.0, 0.0, 88.0]))]}),
        },
    },
    "reed_serpent": {
        "class": "hostile_aquatic_serpent",
        "clips": {
            "idle_undulate": clip(3.2, True, 0.8, {
                "mid": [frames("rotation", (0.0, [0.0, -5.0, 0.0]), (0.8, [0.0, 6.0, 0.0]), (1.6, [0.0, 5.0, 0.0]), (2.4, [0.0, -6.0, 0.0]), (3.2, [0.0, -5.0, 0.0]))],
                "tail": [frames("rotation", (0.0, [0.0, 8.0, 0.0]), (0.8, [0.0, -9.0, 0.0]), (1.6, [0.0, -8.0, 0.0]), (2.4, [0.0, 9.0, 0.0]), (3.2, [0.0, 8.0, 0.0]))],
            }),
            "swim": clip(0.9, True, 0.225, {
                "body": [frames("rotation", (0.0, [0.0, -4.0, 0.0]), (0.45, [0.0, 4.0, 0.0]), (0.9, [0.0, -4.0, 0.0]))],
                "mid": [frames("rotation", (0.0, [0.0, 13.0, 0.0]), (0.45, [0.0, -13.0, 0.0]), (0.9, [0.0, 13.0, 0.0]))],
                "tail": [frames("rotation", (0.0, [0.0, -19.0, 0.0]), (0.45, [0.0, 19.0, 0.0]), (0.9, [0.0, -19.0, 0.0]))],
            }),
            "lunge": clip(0.72, False, 0.34, {
                "body": [frames("position", (0.0, ZERO), (0.18, [0.0, 0.0, 0.55]), (0.38, [0.0, 0.0, -1.35]), (0.72, ZERO))],
                "head": [frames("rotation", (0.0, ZERO), (0.34, [-13.0, 0.0, 0.0]), (0.72, ZERO))],
            }),
            "hurt": clip(0.42, False, 0.17, {"body": [frames("rotation", (0.0, ZERO), (0.17, [0.0, 0.0, -10.0]), (0.42, ZERO))]}),
            "death": clip(1.05, False, 1.05, {"body": [frames("rotation", (0.0, ZERO), (1.05, [0.0, 0.0, -86.0]))]}),
        },
    },
    "bog_watcher": {
        "class": "hostile_stalking_marsh_creature",
        "clips": {
            "idle": clip(3.4, True, 0.85, {
                "eye_stalk": [frames("rotation", (0.0, ZERO), (0.85, [2.0, -8.0, 0.0]), (1.7, ZERO), (2.55, [1.0, 7.0, 0.0]), (3.4, ZERO))],
            }),
            "crawl": clip(1.15, True, 0.2875, gait(1.15, 15.0, ("leg_a", "leg_b", "leg_c", "leg_d")) | {
                "body": [frames("position", (0.0, ZERO), (0.2875, [0.0, 0.18, 0.0]), (0.575, ZERO), (0.8625, [0.0, 0.12, 0.0]), (1.15, ZERO))],
            }),
            "eye_focus": clip(0.9, False, 0.45, {
                "eye_stalk": [frames("rotation", (0.0, ZERO), (0.22, [-6.0, -12.0, 0.0]), (0.45, [4.0, 13.0, 0.0]), (0.68, [-2.0, -5.0, 0.0]), (0.9, ZERO))],
            }),
            "lunge": clip(0.78, False, 0.38, {
                "body": [frames("position", (0.0, ZERO), (0.2, [0.0, -0.25, 0.4]), (0.42, [0.0, 0.65, -1.15]), (0.78, ZERO))],
                "head": [frames("rotation", (0.0, ZERO), (0.38, [-12.0, 0.0, 0.0]), (0.78, ZERO))],
            }),
            "hurt": clip(0.44, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, 9.0]), (0.44, ZERO))]}),
            "death": clip(1.1, False, 1.1, {"body": [frames("rotation", (0.0, ZERO), (1.1, [0.0, 0.0, 87.0]))]}),
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
    receipt["schema"] = "aionforge.wave1.crystal_marsh.creature_native.v1"
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
