#!/usr/bin/env python3

import json
import unittest
from pathlib import Path

from author_ashen_ecology import REPO, SPECS, outputs


class AshenEcologyTests(unittest.TestCase):
    def test_exact_distinct_roster_and_budget(self):
        files, manifest = outputs()
        self.assertEqual(len(SPECS), 10)
        self.assertEqual(len(files), 21)
        self.assertLessEqual(manifest["density"]["aggregate_attempts_per_chunk_before_filters"], 1.1)
        self.assertEqual(manifest["density"]["cap_change"], "NONE")

    def test_every_rule_is_ashen_scoped_and_not_whisperwood_tuned(self):
        for spec in SPECS:
            rule = json.loads((REPO / f"behavior_pack/feature_rules/ah_ecology_{spec.asset}.feature_rule.json").read_text())["minecraft:feature_rules"]
            self.assertEqual(rule["description"]["places_feature"], f"aionbound:ah_ecology_{spec.asset}")
            filters = json.dumps(rule["conditions"]["minecraft:biome_filter"])
            self.assertIn("mountain", filters)
            self.assertIn("mesa", filters)
            self.assertNotIn("forest", filters)
            self.assertEqual(rule["distribution"]["iterations"], spec.iterations)
            self.assertEqual(rule["distribution"]["scatter_chance"]["denominator"], spec.denominator)

    def test_features_place_only_registered_ashen_plants(self):
        for spec in SPECS:
            feature = json.loads((REPO / f"behavior_pack/features/ah_ecology_{spec.asset}.feature.json").read_text())["minecraft:single_block_feature"]
            self.assertEqual(feature["places_block"], f"aionbound:{spec.asset}")
            self.assertTrue((REPO / f"behavior_pack/blocks/{spec.asset}.block.json").is_file())


if __name__ == "__main__":
    unittest.main()
