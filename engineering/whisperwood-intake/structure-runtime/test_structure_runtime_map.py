import hashlib
import json
import subprocess
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
JSON_PATH = HERE / "WHISPERWOOD_STRUCTURE_RUNTIME_MAP.json"
MD_PATH = HERE / "WHISPERWOOD_STRUCTURE_RUNTIME_MAP.md"


class StructureRuntimeMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
        historical_assembly_targets = {
            asset_id: asset["historical_missing_authored_structure_target"]
            for asset_id, asset in self.assets.items()
            if asset["historical_missing_authored_structure_target"]
        }
        self.assertEqual(set(self.assets) - direct, set(historical_assembly_targets))
        self.assertEqual(self.document["summary"]["historical_missing_authored_structure_byte_count"], 8)
        self.assertEqual(self.document["summary"]["current_integrated_structure_byte_count"], 8)
        for asset_id, target in historical_assembly_targets.items():
            self.assertEqual(target, self.assets[asset_id]["historical_targets"]["behavior_pack"]["structure_bytes"])
            self.assertEqual(Path(target).suffix, ".mcstructure")
            self.assertTrue((REPO / target).is_file(), target)
            self.assertGreater((REPO / target).stat().st_size, 0, target)

    def test_historical_targets_and_current_integrated_state_are_separate(self):
        for asset_id, asset in self.assets.items():
            self.assertEqual(asset["historical_targets"]["behavior_pack"]["anchor_block"], f"behavior_pack/blocks/{asset_id}.block.json")
            self.assertIn(f"landmark:{asset_id}", asset["historical_targets"]["codex"])
            self.assertEqual(asset["historical_planning_disposition"]["status_at_base_commit"], "WITHHELD_FROM_PACK_UNTIL_DEPENDENCIES_CLOSE")
            self.assertIn("W1-CREATIVE-004_FINAL_LOOT_VALUES", asset["historical_planning_disposition"]["blockers"])
            current = asset["current_integration"]
            self.assertEqual(current["status"], "INTEGRATED_SOURCE_BYTES_PRESENT_STATIC_ONLY")
            self.assertEqual(current["ratified_dependencies"]["W1-CREATIVE-004"], "WHISPERWOOD_CHAPTER_1_RATIFIED_LATER_REGIONS_DEFERRED")
            self.assertNotIn("WITHHELD", current["status"])
            self.assertNotIn("UNRESOLVED", json.dumps(current))

    def test_current_source_footprints_are_hash_bound(self):
        self.assertEqual(self.document["summary"]["current_integrated_asset_count"], 10)
        for asset in self.assets.values():
            files = asset["current_integration"]["source_files"]
            self.assertTrue(files)
            for entry in files:
                path = REPO / entry["path"]
                self.assertTrue(path.is_file(), entry["path"])
                self.assertEqual(entry["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_no_invented_numeric_distribution_or_loot_values(self):
        serialized = JSON_PATH.read_text()
        for forbidden in ('"denominator"', '"numerator"', '"chance"', '"rolls"', '"min"', '"max"'):
            self.assertNotIn(forbidden, serialized)

    def test_referenced_g7_patterns_exist(self):
        for asset in self.assets.values():
            for path in asset["historical_dependencies"]["g7_reusable_patterns"]:
                self.assertTrue((REPO / path).is_file(), path)

    def test_generator_matches_both_committed_outputs_deterministically(self):
        before_json = JSON_PATH.read_bytes()
        before_md = MD_PATH.read_bytes()
        subprocess.run(["python3", str(HERE / "build_structure_runtime_map.py")], check=True)
        self.assertEqual(before_json, JSON_PATH.read_bytes())
        self.assertEqual(before_md, MD_PATH.read_bytes())


if __name__ == "__main__":
    unittest.main()
