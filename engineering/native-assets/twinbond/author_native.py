#!/usr/bin/env python3
"""Run a native-only Blockbench repair gate for the exact Twinbond art trio.

This lane preserves packet geometry, UVs, and texture bytes. The two wyrm
briefs declare locators but no clip list, so their existing source idle/action
clips are round-tripped without claiming phase readiness. The relic brief
declares exactly ``dual_pulse``; that one clip is authored here.
"""

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
RECEIPT_NAME = "twinbond-native-receipt.json"
ZERO = engine.ZERO
frames = engine.frames
clip = engine.clip


def existing_wyrm_clips():
    return {
        "idle": clip(2.8, True, 1.4, {
            "body": [frames("rotation", (0.0, [0.0, -2.0, 0.0]), (1.4, [0.0, 2.0, 0.0]), (2.8, [0.0, -2.0, 0.0]))],
        }),
        "action": clip(0.8, False, 0.35, {
            "body": [frames("rotation", (0.0, ZERO), (0.15, [-20.0, 8.0, -6.0]), (0.35, [35.0, -10.0, 12.0]), (0.8, ZERO))],
        }),
    }


SPECS = {
    "ash_sovereign_wyrm": {"class": "apex_wyrm_native_source", "clips": existing_wyrm_clips(), "clip_authority": "EXISTING_SOURCE_CLIPS_BRIEF_HAS_NO_ANIMATIONS_FIELD"},
    "tide_empress_wyrm": {"class": "apex_wyrm_native_source", "clips": existing_wyrm_clips(), "clip_authority": "EXISTING_SOURCE_CLIPS_BRIEF_HAS_NO_ANIMATIONS_FIELD"},
    "twinbond_relic": {
        "class": "finale_relic_display",
        "clip_authority": "EXACT_BRIEF_DECLARED_CLIP",
        "clips": {
            "dual_pulse": clip(2.4, True, 0.6, {
                "display": [
                    frames("scale", (0.0, [1.0, 1.0, 1.0]), (0.6, [1.035, 1.035, 1.035]), (1.2, [1.0, 1.0, 1.0]), (1.8, [1.025, 1.025, 1.025]), (2.4, [1.0, 1.0, 1.0])),
                    frames("rotation", (0.0, ZERO), (0.6, [0.0, 5.0, 0.0]), (1.2, ZERO), (1.8, [0.0, -5.0, 0.0]), (2.4, ZERO)),
                ],
                "mount": [frames("scale", (0.0, [1.0, 1.0, 1.0]), (0.6, [1.01, 1.015, 1.01]), (1.2, [1.0, 1.0, 1.0]), (1.8, [1.008, 1.012, 1.008]), (2.4, [1.0, 1.0, 1.0]))],
            }),
        },
    },
}


def execute(args):
    args.bbmodel = args.bbmodel.resolve()
    args.texture = args.texture.resolve()
    args.geometry = args.geometry.resolve()
    args.brief = args.brief.resolve()
    args.output_dir = args.output_dir.resolve()
    original = json.loads(args.brief.read_text())
    expected_original = original.get("animations")
    if args.asset == "twinbond_relic":
        if expected_original != ["dual_pulse"]:
            raise engine.RepresentativeError("RELIC_BRIEF_CLIP_SET_CHANGED")
    elif "animations" in original:
        raise engine.RepresentativeError("WYRM_BRIEF_ANIMATION_AUTHORITY_CHANGED")
    derived = dict(original)
    derived["model_identifier"] = f"geometry.aionforge_sr.{args.asset}"
    derived["animations"] = list(SPECS[args.asset]["clips"])
    with tempfile.TemporaryDirectory(prefix="twinbond-native-brief-") as directory:
        derived_path = Path(directory) / f"{args.asset}.native-binding.brief.json"
        derived_path.write_text(json.dumps(derived, sort_keys=True, separators=(",", ":")) + "\n")
        engine.SPECS = SPECS
        engine.INTEGRATION_COMMIT = INTEGRATION_COMMIT
        engine.RECEIPT_NAME = RECEIPT_NAME
        code, receipt = engine.execute(engine.Inputs(args.asset, args.bbmodel, args.texture, args.geometry, derived_path, args.output_dir, args.cdp_endpoint))
    receipt["schema"] = "aionforge.wave1.twinbond.native.v1"
    receipt["proof_scope"] = "BLOCKBENCH_NATIVE_ASSET_REPAIR_ONLY_NO_PRODUCT_SEMANTICS"
    receipt["portfolio_class"] = receipt.pop("representative_class")
    receipt["integration_authority"] = {"commit": INTEGRATION_COMMIT, "tree": INTEGRATION_TREE}
    receipt["original_brief"] = {
        "path": str(args.brief),
        "sha256": engine.native.sha256_file(args.brief),
        "animations_field": expected_original if expected_original is not None else "ABSENT",
        "locators": original.get("locators"),
    }
    receipt["clip_authority"] = SPECS[args.asset]["clip_authority"]
    receipt["phase_ready"] = False if args.asset != "twinbond_relic" else "NOT_APPLICABLE_RELIC"
    receipt["non_claims"] = ["BP_RP", "PRODUCT_SEMANTICS", "PHASE_READY_WYRM_ANIMATION", "GAMEPLAY", "BDS", "BEDROCK_CLIENT", "MULTIPLAYER", "PHYSICAL_PS4", "MARKETPLACE", "RELEASE"]
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
