import json
import subprocess
import unittest
from pathlib import Path

from author_ashen_creature_loot import ROOT, TABLES


class AshenCreatureLootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(
            ["python3", str(Path(__file__).with_name("author_ashen_creature_loot.py"))],
            check=True,
            cwd=ROOT,
        )
        cls.out = ROOT / "behavior_pack/loot_tables/entities/ashen"

    def test_exact_table_set(self):
        self.assertEqual({p.stem for p in self.out.glob("*.json")}, set(TABLES))

    def test_all_ids_are_ratified_inventory_aliases(self):
        allowed = {
            "aionbound:basalt_core", "aionbound:charbone", "aionbound:drake_scale",
            "aionbound:ember_resin", "aionbound:fire_bloom_seed",
            "aionbound:furnace_chitin", "aionbound:heatstone",
            "aionbound:volcanic_glass_shard",
        }
        found = set()
        for path in self.out.glob("*.json"):
            data = json.loads(path.read_text())
            found.update(pool["entries"][0]["name"] for pool in data["pools"])
        self.assertLessEqual(found, allowed)

    def test_probability_and_quantity_envelopes(self):
        allowed_chances = {
            1.0, 0.80, 0.85, 0.90, 0.28, 0.30, 0.32, 0.35, 0.40,
            0.45, 0.48, 0.50, 0.10, 0.12,
        }
        for path in self.out.glob("*.json"):
            for pool in json.loads(path.read_text())["pools"]:
                chance = pool.get("conditions", [{}])[0].get("chance", 1.0)
                self.assertIn(chance, allowed_chances)
                count = pool["entries"][0]["functions"][0]["count"]
                low = count if isinstance(count, int) else count["min"]
                high = count if isinstance(count, int) else count["max"]
                self.assertGreaterEqual(low, 1)
                self.assertLessEqual(high, 4)

    def test_ecology_drake_never_contains_critical_or_optional_trophy(self):
        raw = (self.out / "ash_drake_ecology.json").read_text()
        self.assertNotIn("ash_drake_horn", raw)
        self.assertNotIn("ember_forge_core", raw)

    def test_narrative_curiosities_are_not_inventory_loot(self):
        raw = "\n".join(p.read_text() for p in self.out.glob("*.json"))
        for forbidden in (
            "message_tube", "pack_cinder_mark", "lynx_eye_gem",
            "slow_stone", "smiths_notes",
        ):
            self.assertNotIn(forbidden, raw)


if __name__ == "__main__":
    unittest.main()
