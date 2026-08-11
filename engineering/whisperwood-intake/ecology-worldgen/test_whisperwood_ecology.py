import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("ww_ecology_author", HERE / "author_whisperwood_ecology.py")
author = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = author
SPEC.loader.exec_module(author)

class EcologyWorldgenTests(unittest.TestCase):
    def setUp(self):
        self.outputs, self.manifest = author.expected_outputs()

    def test_exact_scope_and_unique_identifiers(self):
        self.assertEqual(9, len(author.SPECS))
        self.assertEqual(9, len({spec.identifier for spec in author.SPECS}))
        self.assertEqual(20, len(self.outputs))

    def test_feature_and_rule_filename_identifier_closure(self):
        for spec in author.SPECS:
            feature_path = author.BP / "features" / f"{spec.identifier}.feature.json"
            rule_path = author.BP / "feature_rules" / f"{spec.identifier}.feature_rule.json"
            feature = json.loads(self.outputs[feature_path])
            rule = json.loads(self.outputs[rule_path])
            body = feature["minecraft:single_block_feature"]
            rule_body = rule["minecraft:feature_rules"]
            self.assertEqual(f"aionbound:{spec.identifier}", body["description"]["identifier"])
            self.assertEqual(f"aionbound:{spec.identifier}.feature_rule", rule_body["description"]["identifier"])
            self.assertEqual(body["description"]["identifier"], rule_body["description"]["places_feature"])

    def test_custom_block_reference_closure(self):
        definitions = set()
        for path in (author.BP / "blocks").glob("*.json"):
            document = json.loads(path.read_text())
            definitions.add(document["minecraft:block"]["description"]["identifier"])
        for record in self.manifest["registrations"]:
            self.assertTrue(set(record["custom_block_references"]).issubset(definitions), record["id"])

    def test_density_bounds_and_no_cap_raise(self):
        self.assertLessEqual(self.manifest["density_policy"]["aggregate_expected_attempts_per_chunk_before_filters"], 1.25)
        self.assertEqual("NONE", self.manifest["density_policy"]["cap_change"])
        for spec in author.SPECS:
            self.assertLessEqual(spec.iterations, 4)
            self.assertGreaterEqual(spec.denominator, 8)

    def test_forest_filters_and_passes(self):
        for spec in author.SPECS:
            rule_path = author.BP / "feature_rules" / f"{spec.identifier}.feature_rule.json"
            body = json.loads(self.outputs[rule_path])["minecraft:feature_rules"]
            values = {condition["value"] for condition in body["conditions"]["minecraft:biome_filter"]["all_of"]}
            self.assertTrue({"overworld", "forest", "ocean"}.issubset(values))
            self.assertIn(body["conditions"]["placement_pass"], {"surface_pass", "underground_pass"})

    def test_no_forbidden_content_or_item_proxies(self):
        text = "\n".join(path.as_posix() + self.outputs[path].decode(errors="ignore") for path in self.outputs)
        for forbidden in ("loot_tables", "minecraft:entity", "minecraft:structure_template_feature", "@minecraft/server", "aionbound:moss_resin", "aionbound:hollow_amber", "aionbound:moon_sap"):
            self.assertNotIn(forbidden, text)

    def test_deterministic_regeneration(self):
        second, second_manifest = author.expected_outputs()
        self.assertEqual(self.outputs, second)
        self.assertEqual(self.manifest, second_manifest)

if __name__ == "__main__":
    unittest.main()
