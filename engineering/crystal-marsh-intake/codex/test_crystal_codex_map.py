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
BUILDER = HERE / "build_crystal_codex_map.py"
MAP = HERE / "CRYSTAL_CODEX_PROGRESSION_INTAKE_MAP.json"
SPEC = importlib.util.spec_from_file_location("crystal_codex", BUILDER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CrystalCodexMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MAP.read_text())

    def test_exact_base_and_authority_hashes(self):
        self.assertEqual(MODULE.BASE_COMMIT, self.data["base"]["commit"])
        self.assertEqual(MODULE.BASE_TREE, self.data["base"]["tree"])
        for row in self.data["authority"]:
            path = REPO / row["path"]
            self.assertEqual(row["sha256"], hashlib.sha256(path.read_bytes()).hexdigest(), row["path"])

    def test_exact_page_coverage(self):
        coverage = self.data["coverage"]
        self.assertEqual(50, coverage["packet003_pages"])
        self.assertEqual({key: 10 for key in ["creatures", "resources", "blocks", "plants", "structures"]}, coverage["packet003_by_category"])
        self.assertEqual(11, coverage["direct_equipment_pages"])
        self.assertEqual(2, coverage["adjacent_equipment_references_without_cm_address"])
        self.assertEqual(64, coverage["new_registry_entries"])
        self.assertEqual(204, coverage["registry_entries_after"])

    def test_region_local_indices_and_append_ordinals(self):
        rows = self.data["packet003_entries"]
        grouped = {}
        for row in rows:
            grouped.setdefault(row["codex_category"], []).append(row["category_index"])
        self.assertEqual(list(range(10)), grouped["creature"])
        self.assertEqual(list(range(20)), grouped["resource"])
        self.assertEqual(list(range(10)), grouped["plant"])
        self.assertEqual(list(range(10)), grouped["structure"])
        self.assertEqual(list(range(140, 190)), [row["global_append_ordinal"] for row in rows])
        equipment = self.data["packet006_direct_equipment_pages"]
        self.assertEqual(list(range(11)), [row["category_index"] for row in equipment])
        self.assertEqual(list(range(190, 201)), [row["global_append_ordinal"] for row in equipment])
        self.assertEqual(201, self.data["pearl_depths"]["global_append_ordinal"])
        self.assertEqual([202, 203], [row["global_append_ordinal"] for row in self.data["progression_pages"]])

    def test_prefix_caps_schema_and_budget(self):
        migration = self.data["registry_migration_proposal"]
        self.assertEqual({"before": 3, "after": 4}, migration["registry_version"])
        self.assertEqual({"before": 4, "after": 4}, migration["state_schema_version"])
        self.assertEqual(migration["category_caps_before"], migration["category_caps_after"])
        self.assertFalse(migration["cap_change_required"])
        self.assertIn("Never reorder", migration["index_rule"])
        self.assertEqual(449, self.data["budget"]["fully_populated_three_region_discovery_json_bytes"])
        self.assertEqual(596, self.data["budget"]["fully_populated_four_region_discovery_json_bytes"])
        self.assertEqual(8192, self.data["budget"]["player_dynamic_property_bytes"])
        self.assertEqual(0, self.data["budget"]["growth_from_registry_append"])

    def test_safe_and_gated_routes(self):
        packet_routes = [route for row in self.data["packet003_entries"] for route in row["discovery_routes"]]
        self.assertTrue(any(route["authority"] == "SAFE_NOW" for route in packet_routes))
        wight = next(row for row in self.data["packet003_entries"] if row["id"] == "marsh_wight")
        self.assertTrue(all(route["authority"] == "WITHHELD" for route in wight["discovery_routes"]))
        self.assertTrue(all(row["page_scaffolding_authority"] == "SAFE_NOW" for row in self.data["packet006_direct_equipment_pages"]))
        self.assertTrue(all(row["discovery_routes"][0]["authority"] == "WITHHELD" for row in self.data["packet006_direct_equipment_pages"]))
        self.assertEqual("DEFERRED_BY_USER; no sidegrade/upgraded page, event, ID, or runtime representation is allocated.", self.data["authority_partition"]["W1-CREATIVE-005"])

    def test_progression_boss_and_ashen_boundary(self):
        boss = self.data["pearl_depths"]
        self.assertEqual(["Fog Rise", "Choir Below", "Mask Unsealed", "Flood Claim"], boss["phase_names"])
        self.assertTrue(all(route["authority"] == "WITHHELD" for route in boss["discovery_routes"]))
        chapter, rumor = self.data["progression_pages"]
        self.assertEqual("aionbound:marsh_wight_mask", chapter["seal_identity"])
        self.assertEqual("Sky maps at ruined observatory", rumor["source_hint"])
        self.assertTrue(all(route["authority"] == "SAFE_NOW" for route in rumor["events"]))
        self.assertEqual("REFERENCE_ONLY_NO_CM_ADDRESS", self.data["adjacent_equipment_references"][0]["codex_treatment"])
        self.assertFalse(self.data["ashen_runtime_dependency"]["crystal_dependency"])

    def test_deterministic_regeneration(self):
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            for output in (one, two):
                subprocess.run(["python3", str(BUILDER), "--repo-root", str(REPO), "--output-dir", output], check=True)
            for name in ("CRYSTAL_CODEX_PROGRESSION_INTAKE_MAP.json", "CRYSTAL_CODEX_PROGRESSION_INTAKE_MAP.md"):
                self.assertEqual((Path(one) / name).read_bytes(), (Path(two) / name).read_bytes())
                self.assertEqual((HERE / name).read_bytes(), (Path(one) / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
