from __future__ import annotations

import unittest

from mccompiler.quality import QUALITY_DIMENSIONS, validate_quality_record


def dimensions(score: float = 1.0) -> dict[str, float]:
    return {name: score for name in QUALITY_DIMENSIONS}


class QualityTests(unittest.TestCase):
    def test_parity_requires_evidence_and_invariants(self) -> None:
        record = {
            "feature_id": "fixture:ability",
            "classification": "PARITY",
            "dimensions": dimensions(),
            "evidence": ["gameplay-test:item-use"],
            "invariants": {
                "critical_behavior_omissions": 0,
                "silent_failures": 0,
                "crash_causing_script_errors": 0,
                "unbounded_tick_loops": 0,
            },
        }
        self.assertEqual(validate_quality_record(record), [])

    def test_parity_cannot_hide_missing_evidence_or_low_fidelity(self) -> None:
        record = {
            "feature_id": "fixture:machine",
            "classification": "PARITY",
            "dimensions": dimensions(0.5),
            "invariants": {},
        }
        errors = validate_quality_record(record)
        self.assertTrue(any("requires validation evidence" in error for error in errors))
        self.assertTrue(any("gameplay_fidelity threshold" in error for error in errors))
        self.assertTrue(any("invariant silent_failures is required" in error for error in errors))

    def test_degraded_requires_explicit_approval_and_losses(self) -> None:
        record = {
            "feature_id": "fixture:renderer",
            "classification": "DEGRADED_WITH_APPROVAL",
            "dimensions": dimensions(0.7),
            "invariants": {
                "critical_behavior_omissions": 0,
                "silent_failures": 0,
                "crash_causing_script_errors": 0,
                "unbounded_tick_loops": 0,
            },
        }
        errors = validate_quality_record(record)
        self.assertTrue(any("explicit approval" in error for error in errors))
        self.assertTrue(any("must list preserved and lost behavior" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
