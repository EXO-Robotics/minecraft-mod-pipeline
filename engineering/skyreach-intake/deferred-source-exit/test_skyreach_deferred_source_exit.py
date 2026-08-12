import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = json.loads((HERE / "SKYREACH_DEFERRED_SOURCE_EXIT.json").read_text())


class SkyreachDeferredSourceExitTest(unittest.TestCase):
    def test_status_and_exact_authority_boundary(self):
        self.assertEqual(DATA["status"], "SKYREACH_PARTIAL_SOURCE_INTEGRATION_DEFERRED")
        self.assertEqual(set(DATA["authority_deferred"]), {"W1-001-SR", "W1-003-STORM-NEST", "W1-004-SR", "W1-CREATIVE-005"})

    def test_partial_implementation_is_exact(self):
        self.assertEqual(DATA["implemented"]["creatures"], ["cloud_goat", "gale_hawk", "wind_roc"])
        self.assertEqual(len(DATA["implemented"]["native_representatives"]), 7)
        self.assertEqual(len(DATA["technical_deferred"]["creature_native_and_product_binding"]), 7)
        self.assertEqual(len(DATA["technical_deferred"]["plant_native_and_product_binding"]), 8)
        self.assertEqual(len(DATA["technical_deferred"]["landmark_native_evidence"]), 8)

    def test_dormant_surfaces_are_not_silently_live(self):
        codex = (ROOT / "behavior_pack/scripts/wave1_codex_data.js").read_text()
        runtime = (ROOT / "behavior_pack/scripts/runtime.js").read_text()
        self.assertNotIn("wave1_codex_skyreach_data", codex)
        self.assertNotIn("storm_nest", runtime)
        self.assertNotIn("storm_pinion", runtime)

    def test_no_runtime_claim(self):
        self.assertIn("NO BDS", DATA["proof_boundary"])
        self.assertIn("before candidate freeze", " ".join(DATA["acceptance_criteria"]))


if __name__ == "__main__":
    unittest.main()
