import json
import unittest
from pathlib import Path

import author_native as author
import build_report


HERE = Path(__file__).resolve().parent


class Packet006MissingNativeTest(unittest.TestCase):
    def test_scope_and_clip_sets_are_exact(self):
        self.assertEqual(list(author.SPECS), ["surveyor_medallion", "surveyor_staff", "trail_compass", "warden_sigil"])
        self.assertEqual({asset: list(spec["clips"]) for asset, spec in author.SPECS.items()}, {
            "surveyor_medallion": [], "surveyor_staff": ["hold"], "trail_compass": ["needle_idle"], "warden_sigil": ["pulse"],
        })

    def test_native_receipts_are_exact_and_clean(self):
        for asset, spec in author.SPECS.items():
            with self.subTest(asset=asset):
                root = HERE / "evidence" / asset
                receipt = json.loads((root / author.RECEIPT_NAME).read_text())
                self.assertEqual(receipt["status"], "PASS_NATIVE_REPAIR_GATE")
                self.assertEqual(receipt["integration_authority"], {"commit": author.INTEGRATION_COMMIT, "tree": author.INTEGRATION_TREE})
                self.assertEqual(receipt["original_brief"]["animations"], list(spec["clips"]))
                self.assertEqual(receipt["brief_declared_clips"], list(spec["clips"]))
                self.assertEqual(receipt["required_locators"], ["effect"])
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

    def test_report_is_deterministic(self):
        report = json.loads(build_report.OUTPUT.read_text())
        self.assertEqual(report, build_report.build())
        self.assertEqual(report["status"], "PASS_NATIVE_REPAIR_GATE")
        self.assertEqual(report["totals"], {"assets": 4, "clips": 3, "true_native_locators": 4, "screenshots": 35, "warnings": 0, "errors": 0})


if __name__ == "__main__":
    unittest.main()
