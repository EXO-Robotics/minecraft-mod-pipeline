#!/usr/bin/env python3
import importlib.util
import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location("ww_economy_author", HERE / "author_whisperwood_economy.py")
author = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = author
SPEC.loader.exec_module(author)


def load(path: Path) -> dict:
    return json.loads(path.read_text())


class WhisperwoodEconomyTests(unittest.TestCase):
    def test_exact_ratified_items_and_no_later_region_ids(self):
        self.assertEqual({
            "mosskip_crown_fragment", "thorn_barb", "stalker_claw", "hollow_venom_sac",
            "moss_bind_glue", "amber_core", "thorn_cord", "cleaver_blank", "living_root_focus",
        }, set(author.NEW_ITEMS))
        for item_id in author.NEW_ITEMS:
            item = load(ROOT / "behavior_pack/items" / f"{item_id}.item.json")["minecraft:item"]
            self.assertEqual(f"aionbound:{item_id}", item["description"]["identifier"])
            self.assertEqual(item_id, item["components"]["minecraft:icon"]["textures"]["default"])
        for later_region in ("drake_scale", "prism_wing", "watcher_lens", "wight_shroud"):
            item = load(ROOT / "behavior_pack/items" / f"{later_region}.item.json")["minecraft:item"]
            self.assertEqual(f"aionbound:{later_region}", item["description"]["identifier"])
        self.assertFalse((ROOT / "behavior_pack/items/wing_bone_stay.item.json").exists())

    def test_exact_twenty_six_recipe_graph_and_optional_mastery(self):
        self.assertEqual(26, len(author.RECIPES))
        self.assertNotIn("thorn_stalker_skull", author.RECIPES)
        for recipe_id, (expected_inputs, result) in author.RECIPES.items():
            body = load(ROOT / "behavior_pack/recipes" / f"{recipe_id}.recipe.json")["minecraft:recipe_shapeless"]
            self.assertEqual(f"aionbound:{recipe_id}_recipe", body["description"]["identifier"])
            expanded = [{"item": value["item"]} for value in expected_inputs for _ in range(value.get("count", 1))]
            self.assertEqual(expanded, body["ingredients"])
            self.assertEqual(result, body["result"]["item"])
        self.assertEqual([author.ingredient("aionbound:mosskip_crown_fragment", 3)], author.RECIPES["mosskip_trophy"][0])
        self.assertEqual({"mosskip_trophy", "briar_elk_trophy", "ancient_acorn_display"}, {key for key in author.RECIPES if key.endswith("trophy") or key == "ancient_acorn_display"})
        self.assertEqual("aionbound:waystone_ration", author.RECIPES["waystone_ration"][1])

    def test_all_ten_resources_have_acquisition_and_craft_purpose(self):
        resources = {"whisper_bark", "moss_resin", "glow_spore", "hollow_amber", "lantern_fur", "moon_sap", "root_heart", "briar_antler", "widow_silk", "ancient_acorn"}
        all_drops = {name.split(":", 1)[1] for drops in author.ENTITY_LOOT.values() for name, _chance, _minimum, _maximum in drops if name.startswith("aionbound:")}
        all_drops |= {name.split(":", 1)[1] for spec in author.CHESTS.values() for name, _weight in spec["entries"] if name.startswith("aionbound:")}
        all_inputs = {entry["item"].split(":", 1)[1] for inputs, _result in author.RECIPES.values() for entry in inputs if entry["item"].startswith("aionbound:")}
        self.assertTrue(resources.issubset(all_drops))
        self.assertTrue(resources.issubset(all_inputs))

    def test_every_new_or_derived_identity_has_an_exact_craft_home(self):
        all_inputs = {entry["item"].split(":", 1)[1] for inputs, _result in author.RECIPES.values() for entry in inputs if entry["item"].startswith("aionbound:")}
        self.assertTrue(set(author.NEW_ITEMS).issubset(all_inputs), sorted(set(author.NEW_ITEMS) - all_inputs))

    def test_natural_thorn_stalker_is_mechanically_seal_free(self):
        table = load(ROOT / "behavior_pack/loot_tables/entities/thorn_stalker.json")
        encoded = json.dumps(table)
        self.assertNotIn("thorn_stalker_skull", encoded)
        self.assertEqual({"aionbound:briar_vine", "aionbound:thorn_barb", "aionbound:stalker_claw"}, {entry["name"] for pool in table["pools"] for entry in pool["entries"]})
        entity = load(ROOT / "behavior_pack/entities/thorn_stalker.entity.json")
        self.assertEqual("loot_tables/entities/thorn_stalker.json", entity["minecraft:entity"]["components"]["minecraft:loot"]["table"])
        for path in (ROOT / "behavior_pack/loot_tables").rglob("*.json"):
            self.assertNotIn("aionbound:thorn_stalker_skull", path.read_text(), path)

    def test_entity_probabilities_are_inside_ratified_intervals(self):
        for entity_id, drops in author.ENTITY_LOOT.items():
            elite = entity_id in {"briar_elk", "thorn_stalker", "hollow_widow_spider", "bark_wraith"}
            for _name, chance, minimum, maximum in drops:
                self.assertLessEqual(1, minimum)
                self.assertLessEqual(maximum, 4)
                allowed = chance == 1.0 or .25 <= chance <= .55 or (.35 <= chance <= .65 if elite else .08 <= chance <= .20) or (elite and .08 <= chance <= .20)
                self.assertTrue(allowed, (entity_id, chance))

    def test_chest_bands_and_seal_exclusion(self):
        bands = {"minor_cache": (2, 3, 1), "standard_structure": (3, 5, 1), "landmark_structure": (4, 6, 2)}
        for structure_id, spec in author.CHESTS.items():
            total = spec["guaranteed"] + spec["random"]
            low, high, guaranteed = bands[spec["band"]]
            self.assertLessEqual(low, total)
            self.assertLessEqual(total, high)
            self.assertGreaterEqual(spec["guaranteed"], guaranteed)
            table = ROOT / "behavior_pack/loot_tables/chests/whisperwood" / f"{structure_id}.json"
            self.assertNotIn("thorn_stalker_skull", table.read_text())
        apex = load(ROOT / "behavior_pack/loot_tables/chests/whisperwood/thorn_court.json")
        self.assertEqual(5, sum(pool["rolls"] for pool in apex["pools"]))
        self.assertNotIn("thorn_stalker_skull", json.dumps(apex))

    def test_bindings_repairs_and_deterministic_outputs(self):
        for entity_id in author.ENTITY_LOOT:
            entity = load(ROOT / "behavior_pack/entities" / f"{entity_id}.entity.json")
            self.assertEqual(f"loot_tables/entities/{entity_id}.json", entity["minecraft:entity"]["components"]["minecraft:loot"]["table"])
        for item_id, (repair_item, amount) in author.REPAIR.items():
            item = load(ROOT / "behavior_pack/items" / f"{item_id}.item.json")["minecraft:item"]
            self.assertEqual([{"items": [repair_item], "repair_amount": amount}], item["components"]["minecraft:repairable"]["repair_items"])
        for block_id in [*author.PLANT_IDS, *author.BLOCK_SELF_IDS, "lantern_post", "moss_cairn"]:
            block = load(ROOT / "behavior_pack/blocks" / f"{block_id}.block.json")["minecraft:block"]
            self.assertEqual(f"loot_tables/blocks/{block_id}.json", block["components"]["minecraft:loot"])
        for path, expected in author.expected_outputs().items():
            self.assertEqual(expected, path.read_bytes(), path)


if __name__ == "__main__":
    unittest.main()
