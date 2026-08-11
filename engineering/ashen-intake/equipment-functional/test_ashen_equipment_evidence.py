import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location("ashen_equipment_evidence", HERE / "build_ashen_equipment_evidence.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EvidenceTest(unittest.TestCase):
    def test_checked_in_report_is_deterministic_and_authorized(self):
        checked = json.loads((HERE / "ASHEN_EQUIPMENT_FUNCTIONAL_EVIDENCE.json").read_text())
        self.assertEqual(checked, MODULE.build())
        self.assertTrue(all(row["verified"] for row in checked["authority"]))

    def test_activation_and_sidegrade_remain_absent(self):
        runtime = (ROOT / "behavior_pack/scripts/runtime.js").read_text()
        combat = (ROOT / "behavior_pack/scripts/combat.js").read_text()
        catalog = (ROOT / "behavior_pack/scripts/catalog.js").read_text()
        self.assertNotIn("createAshenEquipmentService", runtime)
        self.assertNotIn("./ashen_equipment.js", combat)
        self.assertNotIn('"aionbound:ash_repeater": "ashen_ranged"', catalog)
        self.assertFalse(MODULE.build()["proof"]["shared_runtime_activation"])


if __name__ == "__main__":
    unittest.main()
