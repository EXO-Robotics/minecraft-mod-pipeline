import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "behavior_pack" / "recipes"

EXPECTED = {
    "barkling_token.recipe.json": (
        "aionbound:barkling_token",
        ("minecraft:stick", "minecraft:apple"),
    ),
    "prismglass_chest.recipe.json": (
        "minecraft:chest",
        ("minecraft:glass", "minecraft:amethyst_shard"),
    ),
    "starter_codex_bookmark.recipe.json": (
        "aionbound:starter_codex_bookmark",
        ("minecraft:paper", "minecraft:string"),
    ),
    "stripvein_charge.recipe.json": (
        "aionbound:stripvein_charge",
        ("minecraft:paper", "minecraft:gunpowder", "minecraft:amethyst_shard"),
    ),
    "trophy_codex.recipe.json": (
        "aionbound:trophy_codex",
        ("minecraft:book", "minecraft:amethyst_shard"),
    ),
}


class Checkpoint1RecipeReconciliationTest(unittest.TestCase):
    def _recipe(self, name):
        document = json.loads((RECIPES / name).read_text())
        return document["minecraft:recipe_shapeless"]

    def test_g7_authored_recipe_relations_are_restored(self):
        for name, (result, ingredients) in EXPECTED.items():
            with self.subTest(name=name):
                recipe = self._recipe(name)
                self.assertEqual(recipe["result"]["item"], result)
                self.assertEqual(
                    tuple(entry["item"] for entry in recipe["ingredients"]),
                    ingredients,
                )
                self.assertEqual(recipe["unlock"], [{"item": ingredients[0]}])

    def test_no_duplicate_ingredient_multiset_remains(self):
        seen = {}
        for name in EXPECTED:
            recipe = self._recipe(name)
            key = tuple(sorted(entry["item"] for entry in recipe["ingredients"]))
            self.assertNotIn(key, seen, f"{name} duplicates {seen.get(key)}")
            seen[key] = name

    def test_reconciliation_does_not_touch_whisperwood_seal_semantics(self):
        for name in EXPECTED:
            self.assertNotIn(
                "aionbound:thorn_stalker_skull",
                (RECIPES / name).read_text(),
            )


if __name__ == "__main__":
    unittest.main()
