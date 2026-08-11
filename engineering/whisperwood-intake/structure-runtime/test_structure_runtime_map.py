import json
import subprocess
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
JSON_PATH = HERE / "WHISPERWOOD_STRUCTURE_RUNTIME_MAP.json"


class StructureRuntimeMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", str(HERE / "build_structure_runtime_map.py")], check=True)
        cls.document = json.loads(JSON_PATH.read_text())
        cls.assets = {asset["id"]: asset for asset in cls.document["assets"]}

    def test_exact_packet_inventory_and_classes(self):
        self.assertEqual(len(self.assets), 10)
        self.assertEqual(self.document["summary"]["class_counts"], {
            "AUTHORED_MCSTRUCTURE_ASSEMBLY": 3,
            "CUSTOM_GEOMETRY_BLOCK_PROP": 2,
            "LANDMARK_ENCOUNTER": 5,
        })

    def test_prop_models_do_not_masquerade_as_structure_bytes(self):
        direct = {"lantern_post", "moss_cairn"}
        missing = {asset_id for asset_id, asset in self.assets.items() if asset["missing_authored_structure_bytes"]}
        self.assertEqual(set(self.assets) - direct, missing)
        self.assertEqual(self.document["summary"]["missing_authored_structure_byte_count"], 8)
        for asset_id in missing:
            target = self.assets[asset_id]["targets"]["behavior_pack"]["structure_bytes"]
            self.assertFalse((REPO / target).exists(), target)

    def test_exact_targets_and_withheld_state(self):
        for asset_id, asset in self.assets.items():
            self.assertEqual(asset["targets"]["behavior_pack"]["anchor_block"], f"behavior_pack/blocks/{asset_id}.block.json")
            self.assertIn(f"landmark:{asset_id}", asset["targets"]["codex"])
            self.assertEqual(asset["disposition"]["status"], "WITHHELD_FROM_PACK_UNTIL_DEPENDENCIES_CLOSE")
            self.assertIn("W1-CREATIVE-004_FINAL_LOOT_VALUES", asset["disposition"]["blockers"])

    def test_no_invented_numeric_distribution_or_loot_values(self):
        serialized = JSON_PATH.read_text()
        for forbidden in ('"denominator"', '"numerator"', '"chance"', '"rolls"', '"min"', '"max"'):
            self.assertNotIn(forbidden, serialized)

    def test_referenced_g7_patterns_exist(self):
        for asset in self.assets.values():
            for path in asset["dependencies"]["g7_reusable_patterns"]:
                self.assertTrue((REPO / path).is_file(), path)

    def test_generator_is_deterministic(self):
        before = JSON_PATH.read_bytes()
        subprocess.run(["python3", str(HERE / "build_structure_runtime_map.py")], check=True)
        self.assertEqual(before, JSON_PATH.read_bytes())


if __name__ == "__main__":
    unittest.main()
