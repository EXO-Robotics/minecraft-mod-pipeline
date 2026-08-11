#!/usr/bin/env python3

import json
import unittest
from pathlib import Path

from author_crystal_ecology import REPO, SPECS, outputs


class CrystalEcologyTests(unittest.TestCase):
    def test_exact_roster_and_console_budget(self):
        files, manifest = outputs()
        self.assertEqual(len(SPECS), 10)
        self.assertEqual(len(files), 21)
        self.assertLessEqual(manifest["density"]["aggregate_attempts_per_chunk_before_filters"], 1.0)
        self.assertEqual(manifest["density"]["cap_change"], "NONE")

    def test_crystal_regional_proxy_is_not_whisperwood_or_ashen(self):
        for spec in SPECS:
            path = REPO / f"behavior_pack/feature_rules/cm_ecology_{spec.asset}.feature_rule.json"
            rule = json.loads(path.read_text())["minecraft:feature_rules"]
            self.assertEqual(rule["description"]["places_feature"], f"aionbound:cm_ecology_{spec.asset}")
            filters = json.dumps(rule["conditions"]["minecraft:biome_filter"])
            self.assertIn("swamp", filters)
            self.assertIn("river", filters)
            self.assertNotIn("forest", filters)
            self.assertNotIn("mountain", filters)
            self.assertNotIn("mesa", filters)
            self.assertEqual(rule["distribution"]["iterations"], spec.iterations)
            self.assertEqual(rule["distribution"]["scatter_chance"]["denominator"], spec.denominator)

    def test_surface_shallow_and_submerged_ecology_are_distinct(self):
        expected_water = {"bubble_pod", "crystal_lily", "crystal_vine", "flood_reed", "glow_kelp"}
        for spec in SPECS:
            feature_path = REPO / f"behavior_pack/features/cm_ecology_{spec.asset}.feature.json"
            feature = json.loads(feature_path.read_text())["minecraft:single_block_feature"]
            self.assertEqual(feature["places_block"], f"aionbound:{spec.asset}")
            self.assertTrue((REPO / f"behavior_pack/blocks/{spec.asset}.block.json").is_file())
            self.assertEqual(feature["may_replace"], ["minecraft:water"] if spec.asset in expected_water else ["minecraft:air"])

    def test_all_water_replacements_have_containment_component(self):
        for spec in SPECS:
            if not spec.replace_water:
                continue
            block = json.loads((REPO / f"behavior_pack/blocks/{spec.asset}.block.json").read_text())["minecraft:block"]
            rule = block["components"]["minecraft:liquid_detection"]["detection_rules"][0]
            self.assertEqual(rule["liquid_type"], "water")
            self.assertTrue(rule["can_contain_liquid"])

    def test_authoring_is_deterministic(self):
        files, manifest = outputs()
        self.assertEqual(manifest["status"], "PASS_STATIC_SOURCE_REGISTRATION")
        for path, expected in files.items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.read_bytes(), expected, path)


if __name__ == "__main__":
    unittest.main()
