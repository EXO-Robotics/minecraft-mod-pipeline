#!/usr/bin/env python3
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent


class WhisperwoodReadinessV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((HERE / "WHISPERWOOD_READINESS_V2.json").read_text())

    def test_audit_is_bound_and_checkpoint_stays_closed(self):
        self.assertEqual(self.report["audited_head"], "1d424aed1182e910eb82a143bd3c2c947ac226ed")
        self.assertFalse(self.report["checkpoint_1_authorized"])
        self.assertEqual(
            set(self.report["checkpoint_1_questions"].values()),
            {"UNPROVEN_CLIENT_OR_BDS"},
        )

    def test_minimum_ratification_path_is_exact(self):
        self.assertEqual(
            self.report["minimum_ratification_path"],
            ["W1-001-WW", "W1-003-THORN-COURT", "W1-004-WW-CH1"],
        )
        self.assertIn("W1-CREATIVE-005", self.report["deferrable_for_checkpoint_1"])
        self.assertIn("W1-ASSET-AUDIO-001", self.report["deferrable_for_checkpoint_1"])

    def test_report_records_source_failure_without_overstating_proof(self):
        evidence = self.report["source_evidence"]
        self.assertEqual(evidence["combined_node_semantics"], "47_PASS_0_FAIL")
        self.assertEqual(evidence["bounded_python_static_commands"], "24_PASS_1_FAIL")
        self.assertEqual(evidence["failing_test_error_count"], 6)
        forbidden = ["BDS", "package", "client", "console", "release"]
        boundary = self.report["proof_boundary"]
        for term in forbidden:
            self.assertIn(term, boundary)


if __name__ == "__main__":
    unittest.main()
