#!/usr/bin/env python3

import importlib.util
import json
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("author_direct_props.py")
SPEC = importlib.util.spec_from_file_location("author_direct_props", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
EVIDENCE_ROOT = MODULE_PATH.parents[1] / "evidence"


class DirectPropSpecsTest(unittest.TestCase):
    def test_exact_asset_and_clip_sets(self):
        self.assertEqual(set(MODULE.lane.ENTITY_SPECS), {"lantern_post", "moss_cairn"})
        self.assertEqual(
            list(MODULE.lane.ENTITY_SPECS["lantern_post"]["clips"]),
            ["idle_sway", "glow"],
        )
        self.assertEqual(MODULE.lane.ENTITY_SPECS["moss_cairn"]["clips"], {})

    def test_restrained_existing_bone_channels(self):
        clips = MODULE.lane.ENTITY_SPECS["lantern_post"]["clips"]
        self.assertEqual(set(clips["idle_sway"]["bones"]), {"lantern"})
        self.assertEqual(set(clips["glow"]["bones"]), {"chassis"})
        rotations = clips["idle_sway"]["bones"]["lantern"][0]["keyframes"]
        self.assertLessEqual(max(abs(v) for frame in rotations for v in frame["value"]), 2.2)
        scales = clips["glow"]["bones"]["chassis"][0]["keyframes"]
        self.assertLessEqual(max(abs(v - 1.0) for frame in scales for v in frame["value"]), 0.040001)

    def test_loop_seams_and_specs(self):
        for asset, record in MODULE.lane.ENTITY_SPECS.items():
            MODULE.validate_direct_prop_spec(asset, record)
            for clip in record["clips"].values():
                for channels in clip["bones"].values():
                    for channel in channels:
                        values = [frame["value"] for frame in channel["keyframes"]]
                        self.assertEqual(values[0], values[-1])

    def test_proof_boundary_names_custom_block_playback(self):
        self.assertIn("CUSTOM_BLOCK_ANIMATION_PLAYBACK", MODULE.lane.NON_CLAIMS)

    def test_native_receipts_and_locator_exports(self):
        expected_locators = {
            "lantern_post": [0, 16, -7],
            "moss_cairn": [0, 10, 0],
        }
        for asset, expected_position in expected_locators.items():
            root = EVIDENCE_ROOT / asset
            receipt = json.loads((root / "direct-prop-native-receipt.json").read_text())
            self.assertEqual(receipt["status"], "PASS")
            self.assertEqual(receipt["native_result"]["blockbench_version"], "5.1.6")
            self.assertEqual(receipt["native_result"]["warning_count"], 0)
            self.assertEqual(receipt["native_result"]["error_count"], 0)
            self.assertEqual(receipt["locator_repair_plan"]["effect"]["parent"], "chassis")
            self.assertEqual(receipt["locator_repair_plan"]["effect"]["position"], expected_position)
            geometry = json.loads((root / "native-exports/pass-2.geo.json").read_text())
            chassis = next(bone for bone in geometry["minecraft:geometry"][0]["bones"] if bone["name"] == "chassis")
            self.assertEqual(chassis["locators"]["effect"], expected_position)

    def test_native_animation_exports_are_exact_and_restrained(self):
        lantern_path = EVIDENCE_ROOT / "lantern_post/native-exports/pass-2.animation.json"
        lantern = json.loads(lantern_path.read_text())["animations"]
        self.assertEqual(set(lantern), {
            "animation.aionforge_ww.lantern_post.idle_sway",
            "animation.aionforge_ww.lantern_post.glow",
        })
        sway = lantern["animation.aionforge_ww.lantern_post.idle_sway"]
        self.assertEqual(set(sway["bones"]), {"lantern"})
        rotation = sway["bones"]["lantern"]["rotation"]
        self.assertLessEqual(max(abs(value) for vector in rotation.values() for value in vector), 2.2)
        glow = lantern["animation.aionforge_ww.lantern_post.glow"]
        self.assertEqual(set(glow["bones"]), {"chassis"})
        scale = glow["bones"]["chassis"]["scale"]
        self.assertLessEqual(max(abs(value - 1.0) for vector in scale.values() for value in vector), 0.040001)
        moss_path = EVIDENCE_ROOT / "moss_cairn/native-exports/pass-2.animation.json"
        self.assertEqual(json.loads(moss_path.read_text())["animations"], {})


if __name__ == "__main__":
    unittest.main()
