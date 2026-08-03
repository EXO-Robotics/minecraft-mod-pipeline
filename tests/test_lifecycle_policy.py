from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bedrock_factory.lifecycle_policy import (
    adjudicate_candidate_outcome,
    assurance_profile,
    full_oracle_authority_reusable,
    integration_train_due,
)
from bedrock_factory.mctools import MCToolsError, parse_mctools_counts, validate_mctools_result


class LifecyclePolicyTests(unittest.TestCase):
    def test_campaign_neutral_regression_fixtures(self) -> None:
        for path in sorted((ROOT / "tests" / "fixtures" / "kernel").glob("*.json")):
            with self.subTest(fixture=path.name):
                fixture = json.loads(path.read_text(encoding="utf-8"))
                result = adjudicate_candidate_outcome(
                    disposition=fixture["disposition"],
                    failure_class=fixture["failure_class"],
                    candidate_id=fixture["candidate_id"],
                    predecessor_candidate_id=fixture["predecessor_candidate_id"],
                    product_bytes_changed=fixture["product_bytes_changed"],
                )
                self.assertEqual(result["rejected_candidates"], fixture["expected_rejected_candidates"])
                self.assertEqual(result["automatic_next_candidate"], fixture["expected_automatic_next_candidate"])

    def test_diagnostic_failure_rejects_only_diagnostic_candidate(self) -> None:
        result = adjudicate_candidate_outcome(
            disposition="EVIDENCE_ENABLING_REPLACEMENT",
            failure_class="DIAGNOSTIC_BEHAVIOR_FAILURE",
            candidate_id="C5",
            predecessor_candidate_id="C4",
            product_bytes_changed=True,
        )
        self.assertEqual(result["rejected_candidates"], ["C5"])
        self.assertTrue(result["predecessor_preserved"])
        self.assertFalse(result["automatic_next_candidate"])

    def test_integration_train_starts_for_three_slices_or_shared_change(self) -> None:
        self.assertFalse(integration_train_due(accepted_since_last_train=2, shared_runtime_interface_changed=False))
        self.assertTrue(integration_train_due(accepted_since_last_train=3, shared_runtime_interface_changed=False))
        self.assertTrue(integration_train_due(accepted_since_last_train=1, shared_runtime_interface_changed=True))

    def test_full_oracle_reuse_is_exactly_bound(self) -> None:
        authority = {
            "status": "PASS",
            "source_sha256": "a" * 64,
            "oracle_implementation_sha256": "b" * 64,
            "comparison_rules_sha256": "c" * 64,
        }
        self.assertTrue(full_oracle_authority_reusable(authority, source_sha256="a" * 64, oracle_implementation_sha256="b" * 64, comparison_rules_sha256="c" * 64))
        self.assertFalse(full_oracle_authority_reusable(authority, source_sha256="a" * 64, oracle_implementation_sha256="b" * 64, comparison_rules_sha256="d" * 64))

    def test_assurance_profiles_do_not_collapse_high_assurance(self) -> None:
        self.assertEqual(assurance_profile("LIGHTWEIGHT")[-1], "MERGE")
        self.assertIn("HIDDEN_EVALUATION", assurance_profile("HIGH_ASSURANCE"))
        self.assertIn("PHYSICAL_HUMAN_RELEASE_AUTHORITY", assurance_profile("HIGH_ASSURANCE"))

    def test_mctools_summary_is_exact_and_fail_closed(self) -> None:
        counts = parse_mctools_counts('{"command":"validate","errors":0,"warnings":2,"recommendations":3}')
        self.assertEqual(counts, {"error_count": 0, "warning_count": 2, "recommendation_count": 3})
        validate_mctools_result({"version": "0.17.6", "exit_code": 0, **counts, "log_sha256": "a" * 64})
        for invalid in (
            '{"command":"validate","errors":"0","warnings":0,"recommendations":0}',
            'Documentation example: errors=0; no validation summary was emitted',
        ):
            with self.subTest(invalid=invalid), self.assertRaises(MCToolsError):
                parse_mctools_counts(invalid)


if __name__ == "__main__":
    unittest.main()
