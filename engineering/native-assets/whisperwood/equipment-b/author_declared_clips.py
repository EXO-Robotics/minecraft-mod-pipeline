#!/usr/bin/env python3
"""Invoke the proven native authoring codec for two exact equipment clips."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


ZERO = [0.0, 0.0, 0.0]


def frames(channel, *entries):
    return {"channel": channel, "keyframes": [{"time": t, "interpolation": "linear", "value": v} for t, v in entries]}


def clip(duration, proof_time, bone, channel):
    return {"duration": duration, "loop": True, "proof_time": proof_time, "bones": {bone: [channel]}}


SPECS = {
    "moss_charm": {
        "role": "accessory",
        "clips": {
            "idle_sway": clip(3.0, 0.75, "chassis", frames("rotation", (0.0, ZERO), (0.75, [0.0, 0.0, 4.0]), (1.5, ZERO), (2.25, [0.0, 0.0, -4.0]), (3.0, ZERO)))
        },
    },
    "moon_sap_pendant": {
        "role": "accessory",
        "clips": {
            "pulse": clip(2.4, 1.2, "head", frames("scale", (0.0, [1.0, 1.0, 1.0]), (0.6, [1.04, 1.04, 1.04]), (1.2, [1.08, 1.08, 1.08]), (1.8, [1.04, 1.04, 1.04]), (2.4, [1.0, 1.0, 1.0])))
        },
    },
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True, choices=sorted(SPECS))
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cdp-endpoint", required=True)
    parser.add_argument("--author-tool", required=True, type=Path)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("native_author", args.author_tool.resolve())
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.ENTITY_SPECS = {args.asset: SPECS[args.asset]}
    base = args.inputs.resolve() / args.asset
    inputs = module.Inputs(
        args.asset,
        base / f"{args.asset}.bbmodel",
        base / "textures" / f"{args.asset}.png",
        base / f"{args.asset}.canonical.geo.json",
        base / f"{args.asset}.brief.json",
        args.output.resolve(),
        args.cdp_endpoint,
        True,
    )
    code, receipt = module.execute(inputs)
    print(f"{args.asset}:{receipt['status']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
