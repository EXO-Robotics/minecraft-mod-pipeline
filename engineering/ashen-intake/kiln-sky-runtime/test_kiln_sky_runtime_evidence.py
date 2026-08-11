import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location("kiln_sky_evidence", HERE / "build_kiln_sky_runtime_evidence.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class KilnSkyEvidenceTest(unittest.TestCase):
    def test_checked_in_evidence_is_deterministic(self):
        checked = json.loads((HERE / "KILN_SKY_RUNTIME_EVIDENCE.json").read_text())
        self.assertEqual(checked, MODULE.build())
        self.assertTrue(all(row["verified"] for row in checked["authority"]))

    def test_shared_runtime_activation_is_absent(self):
        runtime = (ROOT / "behavior_pack/scripts/runtime.js").read_text()
        self.assertNotIn("./kiln_sky.js", runtime)
        self.assertNotIn("createKilnSkyService", runtime)
        self.assertFalse(MODULE.build()["proof"]["shared_runtime_activation"])


if __name__ == "__main__":
    unittest.main()
