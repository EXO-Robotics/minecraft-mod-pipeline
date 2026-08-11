#!/usr/bin/env python3
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent


class WhisperwoodCheckpoint1AuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((HERE / "WHISPERWOOD_CHECKPOINT_1_AUTHORIZATION.json").read_text())

    def test_authorization_is_source_only_and_bds_questions_are_unrun(self):
        self.assertTrue(self.report["checkpoint_1_authorized"])
        self.assertFalse(self.report["checkpoint_1_pass"])
        self.assertEqual(set(self.report["checkpoint_1_questions"].values()), {"UNRUN"})
        self.assertEqual(
            self.report["authorization_scope"],
            "ONE_BOUNDED_EXACT_PACKAGE_STABLE_BDS_CHECKPOINT_1_SMOKE_ONLY",
        )

    def test_exact_audited_head_and_double_run(self):
        self.assertEqual(self.report["audited_head"], "817a829b1e3ad627cc38f29de928a38f67446449")
        self.assertEqual(self.report["double_run"]["rounds"], 2)
        self.assertEqual(self.report["double_run"]["tracked_diff_after_each_round"], "EMPTY")
        self.assertEqual(self.report["double_run"]["untracked_files_after_each_round"], "EMPTY")

    def test_every_source_exit_criterion_passes_and_ashen_remains_closed(self):
        self.assertEqual(set(self.report["source_exit_criteria"].values()), {"PASS_SOURCE"})
        self.assertEqual(self.report["ashen_implementation"]["status"], "NOT_STARTED")
        self.assertFalse(self.report["ashen_implementation"]["phase_b_authorized"])


if __name__ == "__main__":
    unittest.main()
