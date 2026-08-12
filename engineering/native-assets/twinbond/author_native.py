#!/usr/bin/env python3
"""Run a native-only Blockbench repair gate for the exact Twinbond art trio.

This lane preserves packet geometry, UVs, locators, and texture bytes. The
ratified W1-003-TWINBOND contract requires four visually distinct encounter
phases. A native assessment proved the two generic source clips insufficient,
so this repair retains them and adds the minimum four presentation-only clips
for each wyrm. The relic brief declares exactly ``dual_pulse``; that one clip
is preserved unchanged.
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


INTEGRATION_COMMIT = "50b683dfc3e390b19fc7900b88523c90bcc6a31d"
INTEGRATION_TREE = "6dd2cd6547bfcb061083baa2a87e168f86b5d479"
RECEIPT_NAME = "twinbond-native-receipt.json"
ZERO = engine.ZERO
frames = engine.frames
clip = engine.clip


def phase_ready_wyrm_clips(mirror: int):
    """Retain generic clips and add four readable, non-combat phase poses.

    ``mirror`` gives the paired aspects opposite lateral emphasis while all
    durations, translations, and rotations remain purely presentational.
    """
    return {
        "idle": clip(2.8, True, 1.4, {
            "body": [frames("rotation", (0.0, [0.0, -2.0, 0.0]), (1.4, [0.0, 2.0, 0.0]), (2.8, [0.0, -2.0, 0.0]))],
        }),
        "action": clip(0.8, False, 0.35, {
            "body": [frames("rotation", (0.0, ZERO), (0.15, [-20.0, 8.0, -6.0]), (0.35, [35.0, -10.0, 12.0]), (0.8, ZERO))],
        }),
        "split_approach": clip(2.8, True, 0.7, {
            "body": [frames("rotation", (0.0, [0.0, -2.0 * mirror, 0.0]), (0.7, [1.5, 3.0 * mirror, 1.5 * mirror]), (1.4, [0.0, 2.0 * mirror, 0.0]), (2.1, [1.0, -3.0 * mirror, -1.0 * mirror]), (2.8, [0.0, -2.0 * mirror, 0.0]))],
            "head": [frames("rotation", (0.0, [0.0, -5.0 * mirror, 0.0]), (0.7, [2.0, 6.0 * mirror, 0.0]), (1.4, [0.0, 5.0 * mirror, 0.0]), (2.1, [1.0, -6.0 * mirror, 0.0]), (2.8, [0.0, -5.0 * mirror, 0.0]))],
            "wing_l": [frames("rotation", (0.0, [0.0, 0.0, -4.0]), (1.4, [0.0, 0.0, -7.0]), (2.8, [0.0, 0.0, -4.0]))],
            "wing_r": [frames("rotation", (0.0, [0.0, 0.0, 4.0]), (1.4, [0.0, 0.0, 7.0]), (2.8, [0.0, 0.0, 4.0]))],
        }),
        "concord_pressure": clip(1.8, True, 0.45, {
            "body": [frames("rotation", (0.0, [-5.0, 0.0, 0.0]), (0.45, [-8.0, 2.0 * mirror, 0.0]), (0.9, [-5.0, 0.0, 0.0]), (1.35, [-8.0, -2.0 * mirror, 0.0]), (1.8, [-5.0, 0.0, 0.0]))],
            "neck": [frames("rotation", (0.0, [7.0, 0.0, 0.0]), (0.45, [11.0, 0.0, 0.0]), (0.9, [7.0, 0.0, 0.0]), (1.35, [10.0, 0.0, 0.0]), (1.8, [7.0, 0.0, 0.0]))],
            "wing_l": [frames("rotation", (0.0, [0.0, 0.0, -12.0]), (0.45, [0.0, 0.0, -22.0]), (0.9, [0.0, 0.0, -12.0]), (1.35, [0.0, 0.0, -19.0]), (1.8, [0.0, 0.0, -12.0]))],
            "wing_r": [frames("rotation", (0.0, [0.0, 0.0, 12.0]), (0.45, [0.0, 0.0, 22.0]), (0.9, [0.0, 0.0, 12.0]), (1.35, [0.0, 0.0, 19.0]), (1.8, [0.0, 0.0, 12.0]))],
        }),
        "relic_trial": clip(2.4, True, 0.6, {
            "body": [frames("position", (0.0, [0.0, 0.0, 0.0]), (0.6, [0.0, 0.18, 0.0]), (1.2, [0.0, 0.0, 0.0]), (1.8, [0.0, 0.12, 0.0]), (2.4, [0.0, 0.0, 0.0])), frames("rotation", (0.0, [8.0, 5.0 * mirror, 0.0]), (0.6, [10.0, 2.0 * mirror, 0.0]), (1.2, [8.0, -5.0 * mirror, 0.0]), (1.8, [10.0, -2.0 * mirror, 0.0]), (2.4, [8.0, 5.0 * mirror, 0.0]))],
            "head": [frames("rotation", (0.0, [-12.0, -8.0 * mirror, 0.0]), (0.6, [-16.0, -4.0 * mirror, 0.0]), (1.2, [-12.0, 8.0 * mirror, 0.0]), (1.8, [-16.0, 4.0 * mirror, 0.0]), (2.4, [-12.0, -8.0 * mirror, 0.0]))],
            "wing_l": [frames("rotation", (0.0, [0.0, 0.0, 18.0]), (1.2, [0.0, 0.0, 13.0]), (2.4, [0.0, 0.0, 18.0]))],
            "wing_r": [frames("rotation", (0.0, [0.0, 0.0, -18.0]), (1.2, [0.0, 0.0, -13.0]), (2.4, [0.0, 0.0, -18.0]))],
        }),
        "finale_ignition": clip(5.0, False, 3.75, {
            "body": [frames("position", (0.0, [0.0, 0.0, 0.0]), (1.25, [0.0, 0.35, 0.0]), (2.5, [0.0, 0.8, 0.0]), (3.75, [0.0, 1.35, 0.0]), (5.0, [0.0, 1.8, 0.0])), frames("rotation", (0.0, [8.0, 5.0 * mirror, 0.0]), (1.25, [3.0, 3.0 * mirror, 0.0]), (2.5, [-3.0, 0.0, 0.0]), (3.75, [-8.0, -3.0 * mirror, 0.0]), (5.0, [-12.0, -5.0 * mirror, 0.0]))],
            "head": [frames("rotation", (0.0, [-12.0, -8.0 * mirror, 0.0]), (1.25, [-5.0, -4.0 * mirror, 0.0]), (2.5, [2.0, 0.0, 0.0]), (3.75, [8.0, 4.0 * mirror, 0.0]), (5.0, [14.0, 8.0 * mirror, 0.0]))],
            "wing_l": [frames("rotation", (0.0, [0.0, 0.0, 18.0]), (1.25, [0.0, 0.0, 4.0]), (2.5, [0.0, 0.0, -10.0]), (3.75, [0.0, 0.0, -24.0]), (5.0, [0.0, 0.0, -34.0]))],
            "wing_r": [frames("rotation", (0.0, [0.0, 0.0, -18.0]), (1.25, [0.0, 0.0, -4.0]), (2.5, [0.0, 0.0, 10.0]), (3.75, [0.0, 0.0, 24.0]), (5.0, [0.0, 0.0, 34.0]))],
            "tail": [frames("rotation", (0.0, [0.0, 0.0, 0.0]), (1.25, [3.0, 3.0 * mirror, 0.0]), (2.5, [6.0, 0.0, 0.0]), (3.75, [9.0, -3.0 * mirror, 0.0]), (5.0, [12.0, -5.0 * mirror, 0.0]))],
        }),
    }


SPECS = {
    "ash_sovereign_wyrm": {"class": "apex_wyrm_phase_presentation", "clips": phase_ready_wyrm_clips(1), "clip_authority": "RATIFIED_W1_003_TWINBOND_PHASE_PRESENTATION_REPAIR"},
    "tide_empress_wyrm": {"class": "apex_wyrm_phase_presentation", "clips": phase_ready_wyrm_clips(-1), "clip_authority": "RATIFIED_W1_003_TWINBOND_PHASE_PRESENTATION_REPAIR"},
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
    elif expected_original not in (None, ["idle", "action"]):
        raise engine.RepresentativeError("WYRM_SOURCE_CLIP_AUTHORITY_CHANGED")
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
    receipt["proof_scope"] = "BLOCKBENCH_NATIVE_PHASE_PRESENTATION_REPAIR_ONLY"
    receipt["portfolio_class"] = receipt.pop("representative_class")
    receipt["integration_authority"] = {"commit": INTEGRATION_COMMIT, "tree": INTEGRATION_TREE}
    receipt["original_brief"] = {
        "path": str(args.brief),
        "sha256": engine.native.sha256_file(args.brief),
        "animations_field": expected_original if expected_original is not None else "ABSENT",
        "locators": original.get("locators"),
    }
    receipt["clip_authority"] = SPECS[args.asset]["clip_authority"]
    receipt["phase_ready"] = True if args.asset != "twinbond_relic" else "NOT_APPLICABLE_RELIC"
    receipt["phase_presentation"] = list(("split_approach", "concord_pressure", "relic_trial", "finale_ignition")) if args.asset != "twinbond_relic" else []
    receipt["preservation_contract"] = {"geometry": True, "uv": True, "texture_bytes": True, "locators": True, "balance": True, "new_attack_identity": False, "damage_effect_radius_change": False}
    receipt["non_claims"] = ["GAMEPLAY", "BDS", "BEDROCK_CLIENT", "MULTIPLAYER", "PHYSICAL_PS4", "MARKETPLACE", "RELEASE"]
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
