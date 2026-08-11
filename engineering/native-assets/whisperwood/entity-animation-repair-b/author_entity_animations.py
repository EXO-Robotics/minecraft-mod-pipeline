#!/usr/bin/env python3
"""Author the second five Packet 001 creature clip sets in native Blockbench.

This is a narrow visual-motion lane. Clip lengths are editor presentation
lengths only; they do not define hit frames, damage, boss phases, multiplayer
ownership, reset policy, persistence, or rewards.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
LANE_A = HERE.parent / "entity-animation-repair-a" / "author_entity_animations.py"
SPEC = importlib.util.spec_from_file_location("whisperwood_entity_animation_lane_a", LANE_A)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("ENTITY_ANIMATION_LANE_A_IMPORT_FAILED")
lane = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lane
SPEC.loader.exec_module(lane)

frames = lane.frames
clip = lane.clip
ZERO = lane.ZERO

TOOL_VERSION = "1.0.0-b"
PROOF_SCOPE = "BLOCKBENCH_NATIVE_ENTITY_ANIMATION_AUTHORING_AND_CODEC_EXPORT_ONLY"
RUNTIME_MAP = "engineering/whisperwood-intake/entity-runtime/WHISPERWOOD_ENTITY_RUNTIME_IMPLEMENTATION_MAP.json"
BRIEF_ROOT = "program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-001-whisperwood/assets/briefs"


ENTITY_SPECS: dict[str, dict[str, Any]] = {
    "bark_wraith": {
        "role": "elite_spectral",
        "runtime_class": "hostile",
        "movement_intent": "spectral phase-drift",
        "brief_role": "Hostile hollow tree spirit biped",
        "clips": {
            "idle_sway": clip(4.0, True, 1.0, {
                "torso": [frames("rotation", (0.0, ZERO), (1.0, [0.0, 0.0, 3.0]), (2.0, ZERO), (3.0, [0.0, 0.0, -3.0]), (4.0, ZERO)), frames("position", (0.0, ZERO), (1.0, [0.0, 0.3, 0.0]), (2.0, ZERO), (3.0, [0.0, -0.2, 0.0]), (4.0, ZERO))],
                "arm_l": [frames("rotation", (0.0, [4.0, 0.0, -5.0]), (2.0, [-5.0, 0.0, -9.0]), (4.0, [4.0, 0.0, -5.0]))],
                "arm_r": [frames("rotation", (0.0, [-4.0, 0.0, 5.0]), (2.0, [5.0, 0.0, 9.0]), (4.0, [-4.0, 0.0, 5.0]))],
            }),
            "drift_walk": clip(1.2, True, 0.3, {
                "torso": [frames("position", (0.0, ZERO), (0.3, [0.0, 0.35, 0.0]), (0.6, ZERO), (0.9, [0.0, -0.2, 0.0]), (1.2, ZERO))],
                "leg_l": [frames("rotation", (0.0, [10.0, 0.0, 0.0]), (0.6, [-10.0, 0.0, 0.0]), (1.2, [10.0, 0.0, 0.0]))],
                "leg_r": [frames("rotation", (0.0, [-10.0, 0.0, 0.0]), (0.6, [10.0, 0.0, 0.0]), (1.2, [-10.0, 0.0, 0.0]))],
                "arm_l": [frames("rotation", (0.0, [-8.0, 0.0, -4.0]), (0.6, [8.0, 0.0, -7.0]), (1.2, [-8.0, 0.0, -4.0]))],
                "arm_r": [frames("rotation", (0.0, [8.0, 0.0, 4.0]), (0.6, [-8.0, 0.0, 7.0]), (1.2, [8.0, 0.0, 4.0]))],
            }),
            "reach_attack": clip(0.9, False, 0.55, {
                "torso": [frames("rotation", (0.0, ZERO), (0.25, [-7.0, 0.0, 0.0]), (0.55, [12.0, 0.0, 0.0]), (0.9, ZERO))],
                "arm_l": [frames("rotation", (0.0, ZERO), (0.25, [-18.0, 0.0, -10.0]), (0.55, [-62.0, 0.0, -7.0]), (0.9, ZERO))],
                "arm_r": [frames("rotation", (0.0, ZERO), (0.25, [-18.0, 0.0, 10.0]), (0.55, [-62.0, 0.0, 7.0]), (0.9, ZERO))],
                "head": [frames("rotation", (0.0, ZERO), (0.55, [9.0, 0.0, 0.0]), (0.9, ZERO))],
            }),
            "hurt": clip(0.45, False, 0.18, {"torso": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, 9.0]), (0.45, ZERO))]}),
            "death_collapse": clip(1.3, False, 1.3, {
                "torso": [frames("position", (0.0, ZERO), (0.65, [0.0, -1.2, 0.0]), (1.3, [0.0, -3.5, 0.0])), frames("rotation", (0.0, ZERO), (1.3, [0.0, 0.0, 78.0]))],
                "arm_l": [frames("rotation", (0.0, ZERO), (1.3, [20.0, 0.0, -22.0]))],
                "arm_r": [frames("rotation", (0.0, ZERO), (1.3, [-20.0, 0.0, 22.0]))],
            }),
        },
    },
    "briar_elk": {
        "role": "elite_grazer_mini_apex",
        "runtime_class": "neutral",
        "movement_intent": "ground stag gait",
        "brief_role": "Tall neutral grazer with briar cage antlers",
        "clips": {
            "idle": clip(3.6, True, 0.9, {
                "head": [frames("rotation", (0.0, ZERO), (0.9, [5.0, -7.0, 0.0]), (1.8, ZERO), (2.7, [4.0, 6.0, 0.0]), (3.6, ZERO))],
                "tail": [frames("rotation", (0.0, ZERO), (0.9, [0.0, 0.0, 7.0]), (1.8, ZERO), (2.7, [0.0, 0.0, -6.0]), (3.6, ZERO))],
            }),
            "walk": clip(1.1, True, 0.275, {
                "leg_fl": [frames("rotation", (0.0, [18.0, 0.0, 0.0]), (0.55, [-18.0, 0.0, 0.0]), (1.1, [18.0, 0.0, 0.0]))],
                "leg_fr": [frames("rotation", (0.0, [-18.0, 0.0, 0.0]), (0.55, [18.0, 0.0, 0.0]), (1.1, [-18.0, 0.0, 0.0]))],
                "leg_bl": [frames("rotation", (0.0, [-16.0, 0.0, 0.0]), (0.55, [16.0, 0.0, 0.0]), (1.1, [-16.0, 0.0, 0.0]))],
                "leg_br": [frames("rotation", (0.0, [16.0, 0.0, 0.0]), (0.55, [-16.0, 0.0, 0.0]), (1.1, [16.0, 0.0, 0.0]))],
            }),
            "trot": clip(0.8, True, 0.2, {
                "body": [frames("position", (0.0, ZERO), (0.2, [0.0, 0.3, 0.0]), (0.4, ZERO), (0.6, [0.0, 0.3, 0.0]), (0.8, ZERO))],
                "leg_fl": [frames("rotation", (0.0, [25.0, 0.0, 0.0]), (0.4, [-25.0, 0.0, 0.0]), (0.8, [25.0, 0.0, 0.0]))],
                "leg_fr": [frames("rotation", (0.0, [-25.0, 0.0, 0.0]), (0.4, [25.0, 0.0, 0.0]), (0.8, [-25.0, 0.0, 0.0]))],
                "leg_bl": [frames("rotation", (0.0, [-22.0, 0.0, 0.0]), (0.4, [22.0, 0.0, 0.0]), (0.8, [-22.0, 0.0, 0.0]))],
                "leg_br": [frames("rotation", (0.0, [22.0, 0.0, 0.0]), (0.4, [-22.0, 0.0, 0.0]), (0.8, [22.0, 0.0, 0.0]))],
            }),
            "antler_shake": clip(0.9, False, 0.45, {
                "head": [frames("rotation", (0.0, ZERO), (0.2, [-7.0, -12.0, 0.0]), (0.45, [-4.0, 14.0, 0.0]), (0.7, [-6.0, -8.0, 0.0]), (0.9, ZERO))],
                "antler_l": [frames("rotation", (0.0, ZERO), (0.45, [0.0, 0.0, 5.0]), (0.9, ZERO))],
                "antler_r": [frames("rotation", (0.0, ZERO), (0.45, [0.0, 0.0, -5.0]), (0.9, ZERO))],
            }),
            "hurt": clip(0.5, False, 0.2, {"body": [frames("rotation", (0.0, ZERO), (0.2, [0.0, 0.0, -8.0]), (0.5, ZERO))]}),
            "death": clip(1.3, False, 1.3, {"body": [frames("rotation", (0.0, ZERO), (1.3, [0.0, 0.0, -87.0]))]}),
        },
    },
    "hollow_widow_spider": {
        "role": "hostile_elite",
        "runtime_class": "hostile",
        "movement_intent": "ground plus climb",
        "brief_role": "Hostile bark-plate spider with moon-sap abdomen",
        "clips": {
            "idle": clip(3.2, True, 0.8, {
                "abdomen": [frames("position", (0.0, ZERO), (0.8, [0.0, 0.2, 0.0]), (1.6, ZERO), (2.4, [0.0, 0.15, 0.0]), (3.2, ZERO))],
                "leg_fl": [frames("rotation", (0.0, ZERO), (0.8, [0.0, 0.0, -3.0]), (1.6, ZERO), (3.2, ZERO))],
                "leg_fr": [frames("rotation", (0.0, ZERO), (1.6, ZERO), (2.4, [0.0, 0.0, 3.0]), (3.2, ZERO))],
            }),
            "walk_skitter": clip(0.7, True, 0.175, {
                "leg_fl": [frames("rotation", (0.0, [14.0, -7.0, 0.0]), (0.35, [-14.0, 7.0, 0.0]), (0.7, [14.0, -7.0, 0.0]))],
                "leg_fr": [frames("rotation", (0.0, [-14.0, 7.0, 0.0]), (0.35, [14.0, -7.0, 0.0]), (0.7, [-14.0, 7.0, 0.0]))],
                "leg_ml": [frames("rotation", (0.0, [-12.0, -6.0, 0.0]), (0.35, [12.0, 6.0, 0.0]), (0.7, [-12.0, -6.0, 0.0]))],
                "leg_mr": [frames("rotation", (0.0, [12.0, 6.0, 0.0]), (0.35, [-12.0, -6.0, 0.0]), (0.7, [12.0, 6.0, 0.0]))],
                "leg_bl": [frames("rotation", (0.0, [10.0, -5.0, 0.0]), (0.35, [-10.0, 5.0, 0.0]), (0.7, [10.0, -5.0, 0.0]))],
                "leg_br": [frames("rotation", (0.0, [-10.0, 5.0, 0.0]), (0.35, [10.0, -5.0, 0.0]), (0.7, [-10.0, 5.0, 0.0]))],
            }),
            "rear_threat": clip(0.8, False, 0.8, {
                "body": [frames("rotation", (0.0, ZERO), (0.4, [-16.0, 0.0, 0.0]), (0.8, [-24.0, 0.0, 0.0]))],
                "abdomen": [frames("position", (0.0, ZERO), (0.8, [0.0, 1.1, 0.0]))],
                "leg_fl": [frames("rotation", (0.0, ZERO), (0.8, [-24.0, 0.0, -8.0]))],
                "leg_fr": [frames("rotation", (0.0, ZERO), (0.8, [-24.0, 0.0, 8.0]))],
            }),
            "bite": clip(0.55, False, 0.3, {
                "head": [frames("position", (0.0, ZERO), (0.18, [0.0, 0.0, 0.25]), (0.3, [0.0, 0.0, -0.8]), (0.55, ZERO)), frames("rotation", (0.0, ZERO), (0.3, [14.0, 0.0, 0.0]), (0.55, ZERO))],
            }),
            "hurt": clip(0.45, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, 10.0]), (0.45, ZERO))]}),
            "death": clip(1.0, False, 1.0, {
                "body": [frames("rotation", (0.0, ZERO), (1.0, [0.0, 0.0, 84.0]))],
                "leg_fl": [frames("rotation", (0.0, ZERO), (1.0, [28.0, 0.0, -18.0]))],
                "leg_fr": [frames("rotation", (0.0, ZERO), (1.0, [-28.0, 0.0, 18.0]))],
            }),
        },
    },
    "rot_wolf": {
        "role": "hostile_pack",
        "runtime_class": "hostile",
        "movement_intent": "ground pack-run",
        "brief_role": "Hostile pack wolf with moss-rot flanks",
        "clips": {
            "idle": clip(3.4, True, 0.85, {
                "head": [frames("rotation", (0.0, ZERO), (0.85, [4.0, -6.0, 0.0]), (1.7, ZERO), (2.55, [3.0, 6.0, 0.0]), (3.4, ZERO))],
                "tail": [frames("rotation", (0.0, ZERO), (0.85, [0.0, 0.0, 6.0]), (1.7, ZERO), (2.55, [0.0, 0.0, -5.0]), (3.4, ZERO))],
            }),
            "walk": clip(1.1, True, 0.275, {
                "leg_fl": [frames("rotation", (0.0, [18.0, 0.0, 0.0]), (0.55, [-18.0, 0.0, 0.0]), (1.1, [18.0, 0.0, 0.0]))],
                "leg_fr": [frames("rotation", (0.0, [-18.0, 0.0, 0.0]), (0.55, [18.0, 0.0, 0.0]), (1.1, [-18.0, 0.0, 0.0]))],
                "leg_bl": [frames("rotation", (0.0, [-16.0, 0.0, 0.0]), (0.55, [16.0, 0.0, 0.0]), (1.1, [-16.0, 0.0, 0.0]))],
                "leg_br": [frames("rotation", (0.0, [16.0, 0.0, 0.0]), (0.55, [-16.0, 0.0, 0.0]), (1.1, [16.0, 0.0, 0.0]))],
            }),
            "run": clip(0.7, True, 0.175, {
                "body": [frames("position", (0.0, ZERO), (0.175, [0.0, 0.35, 0.0]), (0.35, ZERO), (0.525, [0.0, 0.35, 0.0]), (0.7, ZERO))],
                "leg_fl": [frames("rotation", (0.0, [29.0, 0.0, 0.0]), (0.35, [-29.0, 0.0, 0.0]), (0.7, [29.0, 0.0, 0.0]))],
                "leg_fr": [frames("rotation", (0.0, [-29.0, 0.0, 0.0]), (0.35, [29.0, 0.0, 0.0]), (0.7, [-29.0, 0.0, 0.0]))],
                "leg_bl": [frames("rotation", (0.0, [-26.0, 0.0, 0.0]), (0.35, [26.0, 0.0, 0.0]), (0.7, [-26.0, 0.0, 0.0]))],
                "leg_br": [frames("rotation", (0.0, [26.0, 0.0, 0.0]), (0.35, [-26.0, 0.0, 0.0]), (0.7, [26.0, 0.0, 0.0]))],
            }),
            "snarl_attack": clip(0.75, False, 0.42, {
                "head": [frames("rotation", (0.0, ZERO), (0.2, [12.0, 0.0, 0.0]), (0.42, [-16.0, 0.0, 0.0]), (0.75, ZERO))],
                "body": [frames("position", (0.0, ZERO), (0.2, [0.0, -0.2, 0.15]), (0.42, [0.0, 0.15, -0.65]), (0.75, ZERO))],
            }),
            "hurt": clip(0.45, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, -9.0]), (0.45, ZERO))]}),
            "death": clip(1.0, False, 1.0, {"body": [frames("rotation", (0.0, ZERO), (1.0, [0.0, 0.0, -86.0]))]}),
        },
    },
    "thorn_stalker": {
        "role": "hostile_elite_chapter_apex",
        "runtime_class": "boss",
        "movement_intent": "ground stalk/lunge",
        "brief_role": "Hero hostile; briar ambusher defining dusk threat",
        "boss_motion_boundary": "visual presentation only; no hit, phase, damage, reset, multiplayer, persistence, or reward timing",
        "clips": {
            "idle_crouch": clip(3.8, True, 0.95, {
                "body": [frames("position", (0.0, ZERO), (0.95, [0.0, -0.25, 0.0]), (1.9, ZERO), (2.85, [0.0, -0.18, 0.0]), (3.8, ZERO))],
                "head": [frames("rotation", (0.0, ZERO), (0.95, [4.0, -6.0, 0.0]), (1.9, ZERO), (2.85, [3.0, 6.0, 0.0]), (3.8, ZERO))],
                "tail": [frames("rotation", (0.0, [0.0, -4.0, 0.0]), (1.9, [0.0, 4.0, 0.0]), (3.8, [0.0, -4.0, 0.0]))],
            }),
            "stalk_walk": clip(1.3, True, 0.325, {
                "body": [frames("position", (0.0, ZERO), (0.325, [0.0, 0.16, 0.0]), (0.65, ZERO), (0.975, [0.0, 0.16, 0.0]), (1.3, ZERO))],
                "leg_fl": [frames("rotation", (0.0, [13.0, 0.0, 0.0]), (0.65, [-13.0, 0.0, 0.0]), (1.3, [13.0, 0.0, 0.0]))],
                "leg_fr": [frames("rotation", (0.0, [-13.0, 0.0, 0.0]), (0.65, [13.0, 0.0, 0.0]), (1.3, [-13.0, 0.0, 0.0]))],
                "leg_bl": [frames("rotation", (0.0, [-12.0, 0.0, 0.0]), (0.65, [12.0, 0.0, 0.0]), (1.3, [-12.0, 0.0, 0.0]))],
                "leg_br": [frames("rotation", (0.0, [12.0, 0.0, 0.0]), (0.65, [-12.0, 0.0, 0.0]), (1.3, [12.0, 0.0, 0.0]))],
            }),
            "pounce_pose": clip(0.7, False, 0.7, {
                "body": [frames("position", (0.0, ZERO), (0.3, [0.0, -0.35, 0.2]), (0.7, [0.0, 1.0, -1.2])), frames("rotation", (0.0, ZERO), (0.7, [-13.0, 0.0, 0.0]))],
                "leg_fl": [frames("rotation", (0.0, ZERO), (0.7, [-28.0, 0.0, 0.0]))],
                "leg_fr": [frames("rotation", (0.0, ZERO), (0.7, [-28.0, 0.0, 0.0]))],
                "leg_bl": [frames("rotation", (0.0, ZERO), (0.7, [25.0, 0.0, 0.0]))],
                "leg_br": [frames("rotation", (0.0, ZERO), (0.7, [25.0, 0.0, 0.0]))],
            }),
            "attack_slash": clip(0.75, False, 0.42, {
                "body": [frames("rotation", (0.0, ZERO), (0.2, [0.0, -11.0, 0.0]), (0.42, [0.0, 15.0, 0.0]), (0.75, ZERO))],
                "head": [frames("rotation", (0.0, ZERO), (0.2, [-7.0, -12.0, 0.0]), (0.42, [9.0, 14.0, 0.0]), (0.75, ZERO))],
                "leg_fl": [frames("rotation", (0.0, ZERO), (0.2, [-20.0, 0.0, -5.0]), (0.42, [24.0, 0.0, 8.0]), (0.75, ZERO))],
                "tail": [frames("rotation", (0.0, ZERO), (0.42, [0.0, -16.0, 0.0]), (0.75, ZERO))],
            }),
            "hurt": clip(0.45, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, 8.0]), (0.45, ZERO))]}),
            "death": clip(1.2, False, 1.2, {"body": [frames("rotation", (0.0, ZERO), (1.2, [0.0, 0.0, 88.0]))]}),
        },
    },
}


_base_execute = lane.execute


def execute(inputs: Any) -> tuple[int, dict[str, Any]]:
    code, receipt = _base_execute(inputs)
    spec = ENTITY_SPECS[inputs.asset]
    receipt["tool_version"] = TOOL_VERSION
    receipt["authority_binding"] = {
        "runtime_map": RUNTIME_MAP,
        "runtime_approved_role": spec["role"],
        "runtime_class": spec["runtime_class"],
        "movement_intent": spec["movement_intent"],
        "packet_brief": f"{BRIEF_ROOT}/{inputs.asset}.json",
        "packet_brief_role": spec["brief_role"],
        "clip_names_from_packet_brief": list(spec["clips"]),
        "locator_transforms_from_canonical_static_export": True,
    }
    if "boss_motion_boundary" in spec:
        receipt["boss_motion_boundary"] = spec["boss_motion_boundary"]
    (inputs.output / lane.RECEIPT_NAME).write_bytes(lane.native.canonical_json_bytes(receipt))
    return code, receipt


lane.ENTITY_SPECS = ENTITY_SPECS
lane.TOOL_VERSION = TOOL_VERSION
lane.PROOF_SCOPE = PROOF_SCOPE
lane.execute = execute


if __name__ == "__main__":
    raise SystemExit(lane.main())
