#!/usr/bin/env python3
"""Native-only Blockbench gate for the four unbound Packet 006 assets."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REP = HERE.parent / "skyreach" / "representative"
sys.path.insert(0, str(REP))
import author_representatives as engine  # noqa: E402


INTEGRATION_COMMIT = "edbdf01143e994cae8e77414951d07ae3c95ed63"
INTEGRATION_TREE = "9685cd17539999419d3f8e32272261e585cde0c6"
RECEIPT_NAME = "packet006-missing-native-receipt.json"
ZERO = engine.ZERO
frames = engine.frames
clip = engine.clip


SPECS = {
    "surveyor_medallion": {"class": "static_explorer_accessory", "clips": {}},
    "surveyor_staff": {"class": "held_explorer_tool", "clips": {
        "hold": clip(2.4, True, 0.6, {
            "head": [frames("rotation", (0.0, [0.0, -1.5, 0.0]), (0.6, [0.0, 1.5, 0.0]), (1.2, [0.0, -1.5, 0.0]), (1.8, [0.0, 1.0, 0.0]), (2.4, [0.0, -1.5, 0.0]))],
        }),
    }},
    "trail_compass": {"class": "held_navigation_tool", "clips": {
        "needle_idle": clip(3.2, True, 0.8, {
            "head": [frames("rotation", (0.0, [0.0, -4.0, 0.0]), (0.8, [0.0, 5.0, 0.0]), (1.6, [0.0, -2.0, 0.0]), (2.4, [0.0, 3.0, 0.0]), (3.2, [0.0, -4.0, 0.0]))],
        }),
    }},
    "warden_sigil": {"class": "cross_biome_accessory", "clips": {
        "pulse": clip(2.4, True, 0.6, {
            "head": [
                frames("scale", (0.0, [1.0, 1.0, 1.0]), (0.6, [1.035, 1.035, 1.035]), (1.2, [1.0, 1.0, 1.0]), (1.8, [1.025, 1.025, 1.025]), (2.4, [1.0, 1.0, 1.0])),
                frames("rotation", (0.0, ZERO), (0.6, [0.0, 4.0, 0.0]), (1.2, ZERO), (1.8, [0.0, -4.0, 0.0]), (2.4, ZERO)),
            ],
        }),
    }},
}


def execute(args):
    args.bbmodel = args.bbmodel.resolve()
    args.texture = args.texture.resolve()
    args.geometry = args.geometry.resolve()
    args.brief = args.brief.resolve()
    args.output_dir = args.output_dir.resolve()
    brief = json.loads(args.brief.read_text())
    if brief.get("animations") != list(SPECS[args.asset]["clips"]):
        raise engine.RepresentativeError("BRIEF_CLIP_SET_UNBOUND")
    engine.SPECS = SPECS
    engine.INTEGRATION_COMMIT = INTEGRATION_COMMIT
    engine.RECEIPT_NAME = RECEIPT_NAME
    derived = dict(brief)
    derived["model_identifier"] = f"geometry.aionforge_sr.{args.asset}"
    with tempfile.TemporaryDirectory(prefix="packet006-native-brief-") as directory:
        derived_path = Path(directory) / f"{args.asset}.native-binding.brief.json"
        derived_path.write_text(json.dumps(derived, sort_keys=True, separators=(",", ":")) + "\n")
        code, receipt = engine.execute(engine.Inputs(args.asset, args.bbmodel, args.texture, args.geometry, derived_path, args.output_dir, args.cdp_endpoint))
    receipt["schema"] = "aionforge.wave1.packet006.missing_native.v1"
    receipt["proof_scope"] = "BLOCKBENCH_NATIVE_ASSET_REPAIR_ONLY_NO_PRODUCT_SEMANTICS"
    receipt["portfolio_class"] = receipt.pop("representative_class")
    receipt["integration_authority"] = {"commit": INTEGRATION_COMMIT, "tree": INTEGRATION_TREE}
    receipt["clip_authority"] = "EXACT_BRIEF_DECLARED_CLIP_SET"
    receipt["original_brief"] = {"path": str(args.brief), "sha256": engine.native.sha256_file(args.brief), "animations": brief.get("animations"), "locators": brief.get("locators")}
    receipt["non_claims"] = ["BP_RP", "ITEM_REGISTRATION", "RECIPES", "RUNTIME", "PRODUCT_SEMANTICS", "AUTHORITY", "GAMEPLAY", "BDS", "BEDROCK_CLIENT", "MULTIPLAYER", "PHYSICAL_PS4", "MARKETPLACE", "RELEASE"]
    (args.output_dir / RECEIPT_NAME).write_bytes(engine.native.canonical_json_bytes(receipt))
    return code, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True, choices=sorted(SPECS))
    parser.add_argument("--bbmodel", required=True, type=Path)
    parser.add_argument("--texture", required=True, type=Path)
    parser.add_argument("--geometry", required=True, type=Path)
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--cdp-endpoint", required=True)
    args = parser.parse_args()
    try:
        code, receipt = execute(args)
    except (engine.RepresentativeError, engine.native.NativeToolError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"asset": args.asset, "status": receipt["status"], "receipt": str(args.output_dir / RECEIPT_NAME)}, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
