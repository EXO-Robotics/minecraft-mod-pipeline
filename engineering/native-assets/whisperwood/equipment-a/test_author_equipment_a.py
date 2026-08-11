#!/usr/bin/env python3
"""Contract tests for Whisperwood equipment native lane A."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
TOOL = HERE / "author_equipment_a.py"
spec = importlib.util.spec_from_file_location("equipment_a_tool", TOOL)
assert spec and spec.loader
tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tool
spec.loader.exec_module(tool)


EXPECTED = {
    "mossfang_spear": ["idle_hold", "thrust_pose", "sweep_pose"],
    "widow_fang_dagger": ["idle_hold", "stab_pose"],
    "thorn_whip": ["idle_coil", "crack_pose", "extend_pose"],
    "briar_cleaver": ["idle_hold", "chop_pose"],
    "moon_sap_staff": ["idle_hold", "cast_raise", "pulse"],
    "root_knife": ["hold"],
    "whisperwood_hatchet": ["hold", "chop"],
    "lantern_hook": ["hold", "hang"],
}


class EquipmentANativeContractTests(unittest.TestCase):
    def test_exact_lane_and_clip_sets(self):
        self.assertEqual(set(tool.EQUIPMENT_SPECS), set(EXPECTED))
        self.assertEqual(sum(len(value) for value in EXPECTED.values()), 18)
        for asset, clips in EXPECTED.items():
            self.assertEqual(list(tool.EQUIPMENT_SPECS[asset]["clips"]), clips)

    def test_all_clip_specs_pass_fail_closed_validator(self):
        for asset, record in tool.EQUIPMENT_SPECS.items():
            tool.lane.validate_spec(asset, record)

    def test_only_existing_four_bone_hierarchy_is_animated(self):
        allowed = {"root", "grip", "head", "chassis"}
        for record in tool.EQUIPMENT_SPECS.values():
            for clip_record in record["clips"].values():
                self.assertTrue(set(clip_record["bones"]) <= allowed)

    def test_normalization_changes_namespace_not_shape(self):
        source = {
            "model_identifier": "geometry.aionforge_eq.mossfang_spear",
            "animations": [{"name": "animation.aionforge_eq.mossfang_spear.idle"}],
            "elements": [{"uuid": "same", "from": [0, 0, 0], "to": [1, 1, 1]}],
        }
        normalized = tool.normalized_json(source, "aionforge_eq.mossfang_spear", "aionbound.mossfang_spear")
        self.assertEqual(normalized["model_identifier"], "geometry.aionbound.mossfang_spear")
        self.assertEqual(normalized["elements"], source["elements"])

    def test_packet_texture_staging_is_byte_identical_and_32_square(self):
        packet_root = tool.DEFAULT_PACKET_ROOT
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp:
            for asset in sorted(EXPECTED):
                normalized, canonical_hashes = tool.stage_normalized_inputs(packet_root, asset, Path(temp) / asset)
                self.assertEqual(tool.native.sha256_file(normalized["texture"]), canonical_hashes["texture"])
                png = normalized["texture"].read_bytes()
                self.assertEqual(int.from_bytes(png[16:20], "big"), 32)
                self.assertEqual(int.from_bytes(png[20:24], "big"), 32)

    def test_canonical_locator_authority_is_effect_on_chassis(self):
        for asset in sorted(EXPECTED):
            geometry = json.loads(tool.canonical_paths(tool.DEFAULT_PACKET_ROOT, asset)["geometry"].read_text())
            locators = tool.native.exported_locator_specs(geometry, ["effect"])
            self.assertEqual(locators["effect"]["source_parent"], "chassis")


if __name__ == "__main__":
    unittest.main()
