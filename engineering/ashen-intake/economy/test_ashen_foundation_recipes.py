import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


class AshenFoundationRecipeTests(unittest.TestCase):
    def test_exact_foundation_conversions(self):
        expected = {
            "ashen_ash_log_to_char_planks.recipe.json": "aionbound:ash_log",
            "ashen_smolder_bark_to_char_planks.recipe.json": "aionbound:smolder_bark",
        }
        for filename, source in expected.items():
            recipe = json.loads((ROOT / "behavior_pack/recipes" / filename).read_text())["minecraft:recipe_shapeless"]
            self.assertEqual(recipe["ingredients"], [{"item": source}])
            self.assertEqual(recipe["result"], {"item": "aionbound:char_planks", "count": 4})

    def test_no_sidegrade_or_trophy_route(self):
        raw = "\n".join((ROOT / "behavior_pack/recipes" / f).read_text() for f in (
            "ashen_ash_log_to_char_planks.recipe.json",
            "ashen_smolder_bark_to_char_planks.recipe.json",
        ))
        for forbidden in ("briar_ring", "ash_drake_horn", "ember_forge_core"):
            self.assertNotIn(forbidden, raw)


if __name__ == "__main__":
    unittest.main()
