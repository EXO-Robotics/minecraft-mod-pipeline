import hashlib
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MAP_PATH = HERE / "ASHEN_CODEX_PROGRESSION_INTAKE_MAP.json"
BUILDER = HERE / "build_ashen_codex_map.py"

SPEC = importlib.util.spec_from_file_location("ashen_codex_builder", BUILDER)
BUILDER_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER_MODULE)


class AshenCodexMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MAP_PATH.read_text(encoding="utf-8"))

    def test_exact_base_and_authority_hashes(self):
        self.assertEqual(self.data["base"]["commit"], "faf8bab1785b3b847a70268c37ef813afd0495b4")
        self.assertEqual(self.data["base"]["tree"], "3162be09bb1cb1b4ca10f1bf8132fbbf5e595282")
        for row in self.data["authority"][:5]:
            path = ROOT / row["path"]
            self.assertTrue(path.is_file(), row["path"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["sha256"])

    def test_exact_packet_roster_and_category_indices(self):
        rows = self.data["packet_002_entries"]
        self.assertEqual(len(rows), 50)
        expected = [item for category in ["creatures", "resources", "blocks", "plants", "structures"] for item in BUILDER_MODULE.PACKET_ORDER[category]]
        self.assertEqual([row["id"] for row in rows], expected)
        self.assertEqual(len({row["id"] for row in rows}), 50)
        grouped = {}
        for row in rows:
            grouped.setdefault(row["codex_category"], []).append(row["category_index"])
        self.assertEqual(grouped["creature"], list(range(10)))
        self.assertEqual(grouped["resource"], list(range(20)))
        self.assertEqual(grouped["plant"], list(range(10)))
        self.assertEqual(grouped["structure"], list(range(10)))

    def test_fourteen_equipment_links_without_briar_duplication(self):
        links = self.data["packet_006_ashen_links"]
        self.assertEqual([row["id"] for row in links], BUILDER_MODULE.EQUIPMENT_ORDER)
        self.assertEqual(len(links), 14)
        appended = [row for row in links if row["append_new_entry"]]
        self.assertEqual(len(appended), 13)
        self.assertEqual([row["category_index"] for row in appended], list(range(13)))
        briar = next(row for row in links if row["id"] == "briar_ring")
        self.assertEqual(briar["existing_registry_reference"], {"region": "ww", "category": "equipment", "category_index": 16})
        self.assertEqual(briar["withheld_routes"][0]["blockers"], ["W1-CREATIVE-005"])

    def test_append_only_version_caps_and_budget(self):
        migration = self.data["registry_migration_proposal"]
        self.assertEqual(migration["registry_version"], {"before": 2, "after": 3})
        self.assertEqual(migration["state_schema_version"], {"before": 4, "after": 4})
        self.assertEqual(migration["category_caps_before"], migration["category_caps_after"])
        self.assertFalse(migration["cap_change_required"])
        self.assertEqual(migration["fully_populated_four_region_discovery_json_bytes_before"], 596)
        self.assertEqual(migration["fully_populated_four_region_discovery_json_bytes_after"], 596)
        self.assertEqual(migration["player_budget_bytes"], 8192)
        self.assertEqual(self.data["coverage"]["registry_entries_after"], 140)

    def test_safe_and_withheld_routes_are_explicit(self):
        routes = [route for row in self.data["packet_002_entries"] for route in row["discovery_routes"]]
        self.assertTrue(any(route["authority"] == "SAFE_NOW" for route in routes))
        self.assertTrue(any(route["authority"] == "WITHHELD" for route in routes))
        drake = next(row for row in self.data["packet_002_entries"] if row["id"] == "ash_drake")
        self.assertTrue(all(route["authority"] == "WITHHELD" for route in drake["discovery_routes"]))
        self.assertEqual({row["id"] for row in self.data["blockers"]}, set(BUILDER_MODULE.BLOCKERS))

    def test_progression_rumors_and_primary_seal(self):
        transition = self.data["transition_contract"]
        self.assertEqual(transition["ww_to_ah"]["exact_safe_hint"], "Heat waits east of the burned wagons.")
        self.assertEqual(transition["ww_to_ah"]["consumption"], "invitation_only")
        self.assertTrue(transition["ah_chapter"]["soft_gate"])
        self.assertIn("ash_drake_horn", transition["ah_chapter"]["seal_rule"])
        self.assertEqual([row["category_index"] for row in [transition["ah_chapter"], transition["ah_to_cm"]]], [0, 1])
        self.assertEqual(transition["ah_to_cm"]["presentation"], "Codex/recognized-structure state only")
        kiln = self.data["kiln_sky"]
        self.assertEqual(kiln["seal_semantics"]["primary_critical_seal"], "aionbound:ash_drake_horn")
        self.assertFalse(kiln["seal_semantics"]["ember_forge_core_is_substitute_seal"])
        self.assertTrue(all(row["authority"] == "WITHHELD" for row in kiln["events"]))

    def test_deterministic_regeneration(self):
        before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in [MAP_PATH, HERE / "ASHEN_CODEX_PROGRESSION_INTAKE_MAP.md"]}
        subprocess.run(["python3", str(BUILDER)], cwd=ROOT, check=True)
        after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in [MAP_PATH, HERE / "ASHEN_CODEX_PROGRESSION_INTAKE_MAP.md"]}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
