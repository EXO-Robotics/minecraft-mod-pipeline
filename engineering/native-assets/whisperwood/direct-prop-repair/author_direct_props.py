#!/usr/bin/env python3
"""Author the two Packet 001 direct-prop native sources in Blockbench.

This thin, fail-closed lane reuses the already-validated multi-clip native
authoring transaction. It replaces packet preview clips with exactly the brief
clip set, repairs ``effect`` from the canonical geometry authority, and emits
two save/close/reopen native codec exports. The evidence does not prove custom
block animation playback in Bedrock.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


WHISPERWOOD_DIR = Path(__file__).resolve().parents[1]
ENTITY_TOOL = WHISPERWOOD_DIR / "entity-animation-repair-a" / "author_entity_animations.py"


def load_lane():
    spec = importlib.util.spec_from_file_location("whisperwood_multi_clip_native", ENTITY_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"CANNOT_LOAD_NATIVE_LANE:{ENTITY_TOOL}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


lane = load_lane()

ZERO = [0.0, 0.0, 0.0]


def frames(channel: str, *entries: tuple[float, list[float]]):
    return lane.frames(channel, *entries)


def clip(duration: float, proof_time: float, bones):
    return lane.clip(duration, True, proof_time, bones)


lane.ENTITY_SPECS = {
    "lantern_post": {
        "role": "direct_prop_path_light",
        "clips": {
            "idle_sway": clip(4.0, 1.0, {
                "lantern": [frames(
                    "rotation",
                    (0.0, ZERO),
                    (1.0, [0.8, 0.0, 2.2]),
                    (2.0, ZERO),
                    (3.0, [-0.6, 0.0, -1.8]),
                    (4.0, ZERO),
                )],
            }),
            "glow": clip(3.2, 1.6, {
                "chassis": [frames(
                    "scale",
                    (0.0, [1.0, 1.0, 1.0]),
                    (0.8, [1.015, 1.025, 1.015]),
                    (1.6, [1.03, 1.04, 1.03]),
                    (2.4, [1.015, 1.025, 1.015]),
                    (3.2, [1.0, 1.0, 1.0]),
                )],
            }),
        },
    },
    "moss_cairn": {
        "role": "direct_prop_wayfinding_cairn",
        "clips": {},
    },
}

original_validate_spec = lane.validate_spec


def validate_direct_prop_spec(asset, record):
    if asset == "moss_cairn" and record.get("clips") == {}:
        return
    original_validate_spec(asset, record)


lane.validate_spec = validate_direct_prop_spec
lane.TOOL_VERSION = "direct-prop-1.0.0"
lane.RECEIPT_NAME = "direct-prop-native-receipt.json"
lane.PROOF_SCOPE = "BLOCKBENCH_5_1_6_NATIVE_DIRECT_PROP_SOURCE_AND_CODEC_EXPORT_ONLY"
lane.NON_CLAIMS = [
    "CUSTOM_BLOCK_ANIMATION_PLAYBACK",
    "BEDROCK_CLIENT",
    "STABLE_BDS",
    "PHYSICAL_PS4",
    "MARKETPLACE",
]


if __name__ == "__main__":
    raise SystemExit(lane.main())
