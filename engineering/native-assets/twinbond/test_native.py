import json
import unittest
from pathlib import Path

import author_native as author
import build_report


HERE = Path(__file__).resolve().parent


class TwinbondNativeTest(unittest.TestCase):
    def test_scope_and_authority_are_exact(self):
        self.assertEqual(list(author.SPECS), ["ash_sovereign_wyrm", "tide_empress_wyrm", "twinbond_relic"])
        self.assertEqual(author.INTEGRATION_COMMIT, "edbdf01143e994cae8e77414951d07ae3c95ed63")
        self.assertEqual(author.INTEGRATION_TREE, "9685cd17539999419d3f8e32272261e585cde0c6")

    def test_native_receipts(self):
        for asset, spec in author.SPECS.items():
            with self.subTest(asset=asset):
                root = HERE / "evidence" / asset
                receipt = json.loads((root / author.RECEIPT_NAME).read_text())
                self.assertEqual(receipt["status"], "PASS_NATIVE_REPAIR_GATE")
                self.assertEqual(receipt["brief_declared_clips"], list(spec["clips"]))
                self.assertEqual(receipt["native_result"]["blockbench_version"], "5.1.6")
                self.assertEqual(receipt["native_result"]["warning_count"], 0)
                self.assertEqual(receipt["native_result"]["error_count"], 0)
                self.assertEqual(receipt["diagnostics"], [])
                self.assertTrue(receipt["texture_bytes_preserved"])
                self.assertTrue(receipt["native_exports"]["geometry"]["canonical_equivalent"])
                self.assertTrue(receipt["native_exports"]["animations"]["canonical_equivalent"])
                self.assertEqual(receipt["proof_inventory"], {"native_views": 7, "atlas_uv": 1, "timeline": len(spec["clips"])})
                for screenshot in receipt["screenshots"]:
                    path = root / screenshot["path"]
                    self.assertEqual(author.engine.native.sha256_file(path), screenshot["sha256"])
                    self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_clip_authority_is_fail_closed(self):
        for asset in ("ash_sovereign_wyrm", "tide_empress_wyrm"):
            receipt = json.loads((HERE / "evidence" / asset / author.RECEIPT_NAME).read_text())
            self.assertEqual(receipt["original_brief"]["animations_field"], "ABSENT")
            self.assertEqual(receipt["phase_ready"], False)
            self.assertEqual(receipt["clip_authority"], "EXISTING_SOURCE_CLIPS_BRIEF_HAS_NO_ANIMATIONS_FIELD")
        relic = json.loads((HERE / "evidence" / "twinbond_relic" / author.RECEIPT_NAME).read_text())
        self.assertEqual(relic["original_brief"]["animations_field"], ["dual_pulse"])
        self.assertEqual(relic["brief_declared_clips"], ["dual_pulse"])

    def test_report_is_deterministic(self):
        report = json.loads(build_report.OUTPUT.read_text())
        self.assertEqual(report, build_report.build())
        self.assertEqual(report["status"], "PASS_NATIVE_REPAIR_GATE")
        self.assertEqual(report["totals"], {"assets": 3, "clips": 5, "true_native_locators": 7, "screenshots": 29, "warnings": 0, "errors": 0})


if __name__ == "__main__":
    unittest.main()
