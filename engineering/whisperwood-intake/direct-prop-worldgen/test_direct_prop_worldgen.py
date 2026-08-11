import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("direct_prop_author", HERE / "author_direct_prop_worldgen.py")
author = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = author
SPEC.loader.exec_module(author)

class DirectPropWorldgenTests(unittest.TestCase):
    def setUp(self):
        self.outputs, self.manifest = author.expected_outputs()

    def test_exact_scope(self):
        self.assertEqual(2, len(author.SPECS))
        self.assertEqual(6, len(self.outputs))
        self.assertEqual({"aionbound:lantern_post", "aionbound:moss_cairn"}, {row["block"] for row in self.manifest["registrations"]})

    def test_block_closure(self):
        defined = set()
        for path in (author.BP / "blocks").glob("*.json"):
            defined.add(json.loads(path.read_text())["minecraft:block"]["description"]["identifier"])
        self.assertTrue({row["block"] for row in self.manifest["registrations"]}.issubset(defined))

    def test_identifier_filename_and_target_closure(self):
        for spec in author.SPECS:
            feature_path = author.BP / "features" / f"{spec['id']}.feature.json"
            rule_path = author.BP / "feature_rules" / f"{spec['id']}.feature_rule.json"
            feature = json.loads(self.outputs[feature_path])["minecraft:single_block_feature"]
            rule = json.loads(self.outputs[rule_path])["minecraft:feature_rules"]
            self.assertEqual(f"aionbound:{spec['id']}", feature["description"]["identifier"])
            self.assertEqual(f"aionbound:{spec['id']}.feature_rule", rule["description"]["identifier"])
            self.assertEqual(feature["description"]["identifier"], rule["description"]["places_feature"])

    def test_density_accounts_for_existing_ecology(self):
        density = self.manifest["density_accounting"]
        self.assertEqual(1.151042, density["existing_ecology_attempts_per_chunk"])
        self.assertEqual(0.078125, density["added_direct_prop_attempts_per_chunk"])
        self.assertEqual(1.229167, density["combined_attempts_per_chunk"])
        self.assertLessEqual(density["combined_attempts_per_chunk"], density["ceiling"])
        self.assertEqual("NONE", density["cap_change"])

    def test_stable_forest_surface_filters(self):
        for spec in author.SPECS:
            path = author.BP / "feature_rules" / f"{spec['id']}.feature_rule.json"
            body = json.loads(self.outputs[path])["minecraft:feature_rules"]
            self.assertEqual("surface_pass", body["conditions"]["placement_pass"])
            values = {item["value"] for item in body["conditions"]["minecraft:biome_filter"]["all_of"]}
            self.assertEqual({"overworld", "forest", "ocean"}, values)

    def test_no_forbidden_scope(self):
        text = "\n".join(data.decode(errors="ignore") for data in self.outputs.values())
        for forbidden in ("loot_tables", "minecraft:structure_template_feature", "minecraft:entity", "@minecraft/server"):
            self.assertNotIn(forbidden, text)

    def test_deterministic(self):
        self.assertEqual(self.outputs, author.expected_outputs()[0])

if __name__ == "__main__":
    unittest.main()
