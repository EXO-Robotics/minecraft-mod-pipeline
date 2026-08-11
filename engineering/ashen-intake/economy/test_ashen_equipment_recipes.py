import json
import subprocess
import unittest
from pathlib import Path

from author_ashen_equipment_recipes import OUT, RECIPES, REPORT, ROOT


class AshenEquipmentRecipeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", str(Path(__file__).with_name("author_ashen_equipment_recipes.py"))], cwd=ROOT, check=True)

    def test_exact_graph_and_results(self):
        self.assertEqual(len(RECIPES), 15)
        for result in RECIPES:
            data = json.loads((OUT / f"ashen_{result}.recipe.json").read_text())["minecraft:recipe_shaped"]
            self.assertEqual(data["result"], {"item": f"aionbound:{result}", "count": 1})

    def test_four_ratified_derived_components_have_craft_homes(self):
        self.assertTrue({"heat_core", "heavy_head", "chitin_plate", "ember_heart"} <= set(RECIPES))

    def test_every_equipment_recipe_uses_regional_or_derived_inputs(self):
        allowed = {
            "aionbound:heatstone", "aionbound:sulfur_cluster", "aionbound:volcanic_glass_shard",
            "aionbound:basalt_core", "aionbound:furnace_chitin", "aionbound:ember_resin",
            "aionbound:char_planks", "aionbound:charbone", "aionbound:smoke_reed",
            "aionbound:smolder_bark", "aionbound:heat_core", "aionbound:heavy_head",
            "aionbound:chitin_plate", "aionbound:ember_heart",
        }
        for _result, (_pattern, key) in RECIPES.items():
            self.assertLessEqual(set(key.values()), allowed)

    def test_deferred_and_guarded_outputs_are_absent(self):
        self.assertNotIn("briar_ring", RECIPES)
        self.assertNotIn("ash_drake_horn", RECIPES)
        self.assertNotIn("ember_forge_core", RECIPES)

    def test_ratified_aliases_do_not_gain_unapproved_sulfur_inputs(self):
        self.assertNotIn("aionbound:sulfur_cluster", RECIPES["ember_heart"][1].values())
        self.assertNotIn("aionbound:sulfur_cluster", RECIPES["ember_totem"][1].values())
        self.assertIn("aionbound:charbone", RECIPES["ember_totem"][1].values())

    def test_evidence_receipt_binds_every_recipe_and_proof_boundary(self):
        report = json.loads(REPORT.read_text())
        self.assertEqual(report["status"], "PASS_SOURCE_CRAFTING_CLOSURE")
        self.assertEqual(len(report["recipes"]), len(RECIPES))
        self.assertEqual(report["guarded_outputs_absent"], ["aionbound:ash_drake_horn", "aionbound:ember_forge_core"])
        self.assertIn("aionbound:briar_ring", report["deferred_outputs_absent"])

    def test_author_is_deterministic(self):
        before = REPORT.read_bytes()
        subprocess.run(["python3", str(Path(__file__).with_name("author_ashen_equipment_recipes.py"))], cwd=ROOT, check=True)
        self.assertEqual(REPORT.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
