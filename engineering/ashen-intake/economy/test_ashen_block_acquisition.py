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

    def test_resource_acquisition_closes_natural_block_resources(self):
        required = {
            "aionbound:smolder_bark", "aionbound:sulfur_cluster",
            "aionbound:volcanic_glass_shard", "aionbound:ember_resin", "aionbound:heatstone",
            "aionbound:basalt_core", "aionbound:ash_crystal",
        }
        found = set()
        for block in TABLES:
            data = json.loads((LOOT / f"{block}.json").read_text())
            found.update(e["name"] for p in data["pools"] for e in p["entries"])
        self.assertLessEqual(required, found)

    def test_volcanic_glass_is_shard_source_not_duplication_loop(self):
        raw = (LOOT / "volcanic_glass_block.json").read_text()
        self.assertIn("volcanic_glass_shard", raw)
        self.assertNotIn('"aionbound:volcanic_glass_block"', raw)

    def test_ash_log_yields_log_or_bark_never_both(self):
        data = json.loads((LOOT / "ash_log.json").read_text())
        self.assertEqual(len(data["pools"]), 1)
        self.assertEqual(
            {e["name"] for e in data["pools"][0]["entries"]},
            {"aionbound:ash_log", "aionbound:smolder_bark"},
        )

    def test_one_outcome_per_break_and_no_bonus_duplication(self):
        for block in TABLES:
            pools = json.loads((LOOT / f"{block}.json").read_text())["pools"]
            self.assertEqual(len(pools), 1)
            self.assertEqual(pools[0]["rolls"], 1)
            self.assertEqual(sum(e["weight"] for e in pools[0]["entries"]), 100)
            for entry in pools[0]["entries"]:
                count = entry["functions"][0]["count"]
                high = count if isinstance(count, int) else count["max"]
                self.assertLessEqual(high, 4)


if __name__ == "__main__":
    unittest.main()
