#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BUILDER = HERE / "build_crystal_equipment_intake.py"
MAP = HERE / "CRYSTAL_EQUIPMENT_INTAKE.json"
BEDROCK_ROOT = Path("/Users/blakegrove/Desktop/bedrock-server")
SPEC = importlib.util.spec_from_file_location("crystal_equipment", BUILDER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CrystalEquipmentIntakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MAP.read_text())

    def test_exact_base(self):
        self.assertEqual(MODULE.BASE_COMMIT, self.data["base"]["commit"])
        self.assertEqual(MODULE.BASE_TREE, self.data["base"]["tree"])

    def test_exact_eleven_plus_two(self):
        direct = self.data["direct_packet003_links"]
        adjacent = self.data["adjacent_cross_region_links"]
        self.assertEqual(11, len(direct))
        self.assertEqual(11, len({row["id"] for row in direct}))
        self.assertEqual({"surveyor_staff", "trail_compass"}, {row["id"] for row in adjacent})
        self.assertTrue(all(row["codex_page_allocation"] == "CM_EQUIPMENT_PAGE" for row in direct))
        self.assertTrue(all(row["codex_page_allocation"] == "REFERENCE_ONLY_NO_CM_ADDRESS" for row in adjacent))

    def test_sources_and_base_target_scan(self):
        for row in self.data["direct_packet003_links"] + self.data["adjacent_cross_region_links"]:
            for source in row["source_files"].values():
                path = BEDROCK_ROOT / source["path"]
                self.assertEqual(source["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertFalse(row["target_status_at_base"]["identity_specific_targets_present"])
            self.assertTrue(row["target_status_at_base"]["identity_specific_targets_missing"])

    def test_recipe_and_authority_partition(self):
        rows = {row["id"]: row for row in self.data["direct_packet003_links"] + self.data["adjacent_cross_region_links"]}
        self.assertIn("Crystal Pole", rows["crystal_pike"]["recipe_acquisition_provenance"]["source_formula"])
        self.assertIn("W1-CREATIVE-005", rows["prism_bow"]["recipe_acquisition_provenance"]["sidegrade_boundary"])
        self.assertEqual(["W1-003-PEARL-DEPTHS", "W1-004-CM"], rows["marsh_wight_mask"]["gated_semantics"]["blockers"])
        self.assertEqual("DEFERRED_BY_USER; blocks only distinct Gale-strung prism_bow and other sidegrade representations, not the base prism_bow identity.", self.data["authority_partition"]["W1-CREATIVE-005"])
        for ticket in ("W1-001-CM", "W1-003-PEARL-DEPTHS", "W1-004-CM"):
            self.assertEqual("RATIFIED_EXACT_PROPOSAL_BYTES_PRESERVED", self.data["authority_partition"][ticket])

    def test_current_authority_hash_is_receipt_only(self):
        authority = self.data["authority"][0]
        path = REPO / authority["path"]
        self.assertEqual("e90e9683e730235beae6dd08688426558140fdee962d4c3bdbf7aa54e6095660", authority["sha256"])
        self.assertEqual(authority["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertIn("without authority mutation", authority["role"])

    def test_ashen_is_not_crystal_dependency(self):
        dependency = self.data["ashen_runtime_dependency"]
        self.assertEqual("FINAL_INTEGRATION_DEPENDENCY_ONLY", dependency["relationship"])
        self.assertFalse(dependency["crystal_dependency"])

    def test_deterministic_regeneration(self):
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            for output in (one, two):
                subprocess.run(["python3", str(BUILDER), "--repo-root", str(REPO), "--bedrock-root", str(BEDROCK_ROOT), "--output-dir", output], check=True)
            for name in ("CRYSTAL_EQUIPMENT_INTAKE.json", "CRYSTAL_EQUIPMENT_INTAKE.md"):
                self.assertEqual((Path(one) / name).read_bytes(), (Path(two) / name).read_bytes())
                self.assertEqual((HERE / name).read_bytes(), (Path(one) / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
