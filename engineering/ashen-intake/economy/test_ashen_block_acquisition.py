import json
import subprocess
import unittest
from pathlib import Path

from author_ashen_block_acquisition import BLOCKS, LOOT, ROOT, TABLES


class AshenBlockAcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", str(Path(__file__).with_name("author_ashen_block_acquisition.py"))], check=True, cwd=ROOT)

    def test_all_ten_blocks_bind_exact_tables(self):
        self.assertEqual(len(TABLES), 10)
        for block in TABLES:
            data = json.loads((BLOCKS / f"{block}.block.json").read_text())
            self.assertEqual(data["minecraft:block"]["components"]["minecraft:loot"], f"loot_tables/blocks/ashen/{block}.json")

    def test_resource_acquisition_closes_all_non_creature_resources(self):
        required = {
            "aionbound:smolder_bark", "aionbound:charbone", "aionbound:sulfur_cluster",
            "aionbound:volcanic_glass_shard", "aionbound:ember_resin", "aionbound:heatstone",
            "aionbound:basalt_core", "aionbound:ash_crystal",
        }
        found = set()
        for block in TABLES:
            data = json.loads((LOOT / f"{block}.json").read_text())
            found.update(p["entries"][0]["name"] for p in data["pools"])
        self.assertLessEqual(required, found)

    def test_volcanic_glass_is_shard_source_not_duplication_loop(self):
        raw = (LOOT / "volcanic_glass_block.json").read_text()
        self.assertIn("volcanic_glass_shard", raw)
        self.assertNotIn('"aionbound:volcanic_glass_block"', raw)

    def test_values_stay_inside_ratified_envelopes(self):
        for block in TABLES:
            for p in json.loads((LOOT / f"{block}.json").read_text())["pools"]:
                chance = p.get("conditions", [{}])[0].get("chance", 1)
                self.assertTrue(chance == 1 or 0.08 <= chance <= 0.55)
                count = p["entries"][0]["functions"][0]["count"]
                high = count if isinstance(count, int) else count["max"]
                self.assertLessEqual(high, 4)


if __name__ == "__main__":
    unittest.main()
