import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REPORT = json.loads((HERE / "WHISPERWOOD_PLANT_PLACEMENT_CLOSURE.json").read_text())


class PlantPlacementClosureTests(unittest.TestCase):
    def test_exact_three_missing_plants_are_registered(self):
        self.assertEqual(
            {row["block"] for row in REPORT["registrations"]},
            {"aionbound:star_grass", "aionbound:pale_reed", "aionbound:ember_thistle"},
        )
        for row in REPORT["registrations"]:
            feature_name = row["feature"].split(":", 1)[1]
            feature = json.loads((REPO / f"behavior_pack/features/{feature_name}.feature.json").read_text())
            rule = json.loads((REPO / f"behavior_pack/feature_rules/{feature_name}.feature_rule.json").read_text())
            self.assertEqual(feature["minecraft:single_block_feature"]["places_block"], row["block"])
            self.assertEqual(rule["minecraft:feature_rules"]["description"]["places_feature"], row["feature"])

    def test_density_stays_under_existing_ceiling(self):
        density = REPORT["density"]
        self.assertAlmostEqual(
            density["combined_attempts_per_chunk_before_filters"],
            density["prior_attempts_per_chunk_before_filters"] + density["added_attempts_per_chunk_before_filters"],
            places=6,
        )
        self.assertLessEqual(density["combined_attempts_per_chunk_before_filters"], density["ceiling"])
        self.assertEqual(density["cap_change"], "NONE")

    def test_every_rule_is_conservative_and_fail_closed(self):
        for row in REPORT["registrations"]:
            name = row["feature"].split(":", 1)[1]
            rule = json.loads((REPO / f"behavior_pack/feature_rules/{name}.feature_rule.json").read_text())["minecraft:feature_rules"]
            self.assertEqual(rule["distribution"]["iterations"], 1)
            self.assertGreaterEqual(rule["distribution"]["scatter_chance"]["denominator"], 256)
            self.assertIn("does not prove", row["proxy_limit"])


if __name__ == "__main__":
    unittest.main()
