import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = json.loads((HERE / "SKYREACH_DEFERRED_SOURCE_EXIT.json").read_text())
CURRENT = json.loads((ROOT / "engineering/validation/wave1/WAVE_1_SKYREACH_IMPLEMENTED_CLOSURE.json").read_text())


class SkyreachDeferredSourceExitTest(unittest.TestCase):
    def test_status_and_exact_authority_boundary(self):
        self.assertEqual(DATA["status"], "SKYREACH_PRODUCT_FOUNDATION_COMPLETE_AUTHORITY_GATED_SURFACES_DEFERRED")
        self.assertEqual(set(DATA["authority_deferred"]), {"W1-001-SR", "W1-003-STORM-NEST", "W1-004-SR", "W1-CREATIVE-005"})

    def test_partial_implementation_is_exact(self):
        self.assertIn("all 10", DATA["implemented"]["creatures"])
        self.assertIn("all 10", DATA["implemented"]["plants"])
        self.assertIn("all 30", DATA["implemented"]["native_assets"])
        self.assertEqual(DATA["technical_deferred"], {})

    def test_historical_dormancy_is_preserved_and_current_successor_is_reconciled(self):
        codex = (ROOT / "behavior_pack/scripts/wave1_codex_data.js").read_text()
        runtime = (ROOT / "behavior_pack/scripts/runtime.js").read_text()
        self.assertIn("wave1_codex_skyreach_data", codex)
        self.assertIn('from "./storm_nest.js"', runtime)
        self.assertIn("stormNest.reconcile()", runtime)
        self.assertIn("stormNest.tick()", runtime)
        self.assertIn("stormNest.bossDeath(event)", runtime)
        self.assertEqual("SKYREACH_VERTICAL_SOURCE_COMPLETE_TARGETED_LOCAL_PASS", CURRENT["status"])
        self.assertEqual("DEFERRED_BY_USER_NO_SIDEGRADE_IDENTITIES", CURRENT["pending_follow_up"]["W1-CREATIVE-005"])
        self.assertEqual("DEFERRED_TO_FINAL_INTEGRATED_GATE", CURRENT["pending_follow_up"]["runtime_qualification"])

    def test_no_runtime_claim(self):
        self.assertIn("NO BDS", DATA["proof_boundary"])
        self.assertIn("before candidate freeze", " ".join(DATA["acceptance_criteria"]))
        self.assertIn("NO PACKAGE, BDS", CURRENT["proof_boundary"])


if __name__ == "__main__":
    unittest.main()
