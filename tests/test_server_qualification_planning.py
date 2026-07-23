from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.build_server_qualification_planning import (
    MARKDOWN_NAMES, OUTPUT_NAMES, build_documents, render,
)

ROOT = Path(__file__).resolve().parents[1]


class ServerQualificationPlanningTests(unittest.TestCase):
    def test_ps4_proxy_is_passed_but_never_physically_promoted(self) -> None:
        proxy = build_documents(ROOT)["ps4-planning-proxy.json"]
        self.assertEqual("PS4_PLANNING_PROXY_PASSED", proxy["status"])
        self.assertIn("PS4_PHYSICAL_PENDING", proxy["statuses"])
        self.assertFalse(any(proxy["claims"].values()))
        self.assertEqual("UNCALIBRATED_PS4_PLANNING_WEIGHTS", proxy["weights_label"])

    def test_recalibrated_scope_preserves_reserve(self) -> None:
        result = build_documents(ROOT)["quarter-scope-recalibration.json"]
        self.assertEqual("QUARTER_SCOPE_RECALIBRATED", result["status"])
        self.assertLessEqual(result["selected_planning_units"], result["planning_ceiling"])
        self.assertGreaterEqual(result["reserve"], 16)
        self.assertTrue(result["progression_complete"])
        self.assertFalse(result["implementation_started"])

    def test_all_candidate_patterns_are_frozen_with_evidence(self) -> None:
        result = build_documents(ROOT)["pattern-readiness.json"]
        self.assertEqual(16, len(result["patterns"]))
        self.assertTrue(all(row["evidence"] for row in result["patterns"]))
        self.assertTrue(all(row["client"]["ps4"] == "PENDING" for row in result["patterns"]))

    def test_stress_metrics_do_not_invent_unavailable_values(self) -> None:
        result = build_documents(ROOT)["stress-matrix.json"]
        self.assertEqual("UNAVAILABLE", result["metric_kinds"]["tick_backlog"])
        self.assertIn("maximum_observed_tick_backlog", result["unavailable_metrics"])
        self.assertEqual(5, len(result["profiles"]))

    def test_render_is_deterministic_and_indexes_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "planning/server-qualification"
            first = render(ROOT, output)
            first_bytes = {path.name: path.read_bytes() for path in first}
            second = render(ROOT, output)
            self.assertEqual(first_bytes, {path.name: path.read_bytes() for path in second})
            index = json.loads((output / "evidence-index.json").read_text())
            expected = set(OUTPUT_NAMES) | set(MARKDOWN_NAMES)
            self.assertEqual(expected, {Path(row["path"]).name for row in index["entries"]})
            self.assertFalse(index["physical_evidence_complete"])
            self.assertFalse(index["ps4_verified"])


if __name__ == "__main__":
    unittest.main()
