from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mccompiler.bedrock import compile_bedrock
from mccompiler.marketplace import evaluate_marketplace_candidate
from mccompiler.planner import plan_conversion
from mccompiler.quality import QUALITY_DIMENSIONS


def evidence() -> list[dict[str, object]]:
    return [{"source_file": "Original.java", "start_line": 1, "end_line": 2, "extraction_rule": "original-test", "confidence": 1.0}]


def fixture() -> dict:
    return {
        "schema_version": "1.0.0", "metadata": {"id": "original"}, "mods": [{"id": "original"}], "dependencies": [],
        "content": [{"kind": "item", "identifier": "original:wand", "properties": {}, "evidence": evidence()}], "assets": [],
        "behaviors": [], "state": [], "presentation_requirements": [], "ui_intent": [], "networking_intent": [], "unsupported_hooks": [], "tests": [], "target": "MARKETPLACE_ADDON_STABLE",
    }


def quality(feature_id: str) -> dict:
    return {
        "feature_id": feature_id, "classification": "PARITY",
        "dimensions": {name: 1.0 for name in QUALITY_DIMENSIONS}, "evidence": ["static-generation-test"],
        "invariants": {"critical_behavior_omissions": 0, "silent_failures": 0, "crash_causing_script_errors": 0, "unbounded_tick_loops": 0},
    }


def cleared_rights() -> dict:
    return {"schema_version": "1.0.0", "records": [{
        "content_id": "original:wand", "content_type": "code_and_assets", "evidence": ["human-authorship-declaration"],
        "decision": {"status": "MARKETPLACE_CLEARED", "reviewer_type": "human", "reviewed_by": "Test Reviewer", "reviewer_id": "test:reviewer", "reviewed_at": "2026-07-22T12:00:00Z"},
    }]}


def creator_tools(passed: bool = True) -> dict:
    return {"passed": passed, "creator_tools": {"version": "0.17.6", "suites": ["addon", "currentplatform"], "errors": 0 if passed else 1, "warnings": 0, "marketplace_approval_implied": False}}


class MarketplaceCandidateTests(unittest.TestCase):
    def test_all_independent_gates_are_required(self) -> None:
        document = fixture(); plan = plan_conversion(document)
        with tempfile.TemporaryDirectory() as directory:
            compile_bedrock(document, plan, directory)
            report = evaluate_marketplace_candidate(directory, plan=plan, rights_manifest=cleared_rights(), quality_records=[quality("original:wand")], creator_tools_report=creator_tools())
            self.assertTrue(report["passed"], report["blockers"])
            self.assertEqual("MARKETPLACE_CANDIDATE", report["status"])
            self.assertFalse(report["marketplace_approval_implied"])
            self.assertEqual(64, len(report["artifacts"][0]["sha256"]))

    def test_missing_rights_quality_and_official_tools_block(self) -> None:
        document = fixture(); plan = plan_conversion(document)
        with tempfile.TemporaryDirectory() as directory:
            compile_bedrock(document, plan, directory)
            report = evaluate_marketplace_candidate(directory, plan=plan, rights_manifest={"schema_version": "1.0.0", "records": []}, quality_records=[], creator_tools_report=None)
            self.assertFalse(report["passed"])
            self.assertTrue(report["blockers"]["rights"])
            self.assertTrue(report["blockers"]["quality"])
            self.assertTrue(report["blockers"]["creator_tools"])


if __name__ == "__main__":
    unittest.main()
