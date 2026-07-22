from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mccompiler.operations import validation_ops
from mccompiler.operations.envelope import OperationError
from mccompiler.project.store import ProjectStore


class ValidationOperationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.store = ProjectStore.create(Path(temporary.name) / "project")

    def write(self, relative: str, value: object) -> None:
        self.store.write(relative, value)

    def test_profile_rights_api_and_performance_reuse_existing_validators(self) -> None:
        self.write("reports/api-usage.json", {"complete": True, "symbols": [], "uncatalogued_symbols": []})
        api, _, _ = validation_ops.validate_api_symbols(self.store, {})
        self.assertTrue(api["valid"])

        rights = {
            "schema_version": "1.0.0", "records": [{
                "content_id": "demo:owned", "content_type": "code", "evidence": [{"kind": "authorship"}],
                "decision": {"status": "MARKETPLACE_CLEARED", "reviewer_type": "human", "reviewed_by": "Test Reviewer", "reviewer_id": "test:reviewer", "reviewed_at": "2026-07-22T12:00:00Z"},
            }],
        }
        self.write("rights/rights-manifest.yaml", rights)
        result, _, _ = validation_ops.validate_rights(self.store, {})
        self.assertTrue(result["marketplace_candidate_allowed"])
        self.assertFalse(result["legal_clearance_implied"])

        pack = self.store.resolve("dist/marketplace-candidate")
        pack.mkdir(parents=True, exist_ok=True)
        (pack / "tiny.txt").write_text("ok", encoding="utf-8")
        performance, _, _ = validation_ops.validate_performance(self.store, {"build_root": "dist/marketplace-candidate"})
        self.assertTrue(performance["passed"])
        self.assertEqual("NOT_AVAILABLE", performance["runtime_measurement_status"])

        profile, _, _ = validation_ops.validate_marketplace_profile(self.store, {})
        self.assertTrue(profile["valid"])
        self.assertFalse(profile["marketplace_approval_implied"])

    def test_expected_behavior_and_content_log_use_persisted_artifacts(self) -> None:
        self.write("tests/expected-behavior.json", {"behaviors": [{"id": "demo:use"}, {"id": "demo:save"}]})
        self.write("runtime/behavior-results.json", {"behaviors": [{"id": "demo:use", "passed": True}, {"id": "demo:save", "passed": False}, {"id": "extra", "passed": True}]})
        comparison, _, artifacts = validation_ops.compare_expected_behavior(self.store, {})
        self.assertFalse(comparison["matches"])
        self.assertEqual(["demo:save"], comparison["failed"])
        self.assertEqual(["extra"], comparison["unexpected"])
        self.assertFalse(comparison["runtime_execution_implied"])
        self.assertEqual(2, len(artifacts))

        log = self.store.resolve("runtime/content.log")
        log.write_text("loaded\nERROR broken component\n", encoding="utf-8")
        inspected, _, _ = validation_ops.inspect_content_log(self.store, {})
        self.assertFalse(inspected["clean"])
        self.assertEqual(1, len(inspected["critical_lines"]))

    def test_external_runtime_operations_are_honest_and_read_only(self) -> None:
        revision = self.store.revision
        handlers = (
            validation_ops.install_test_pack, validation_ops.start_test_runtime,
            validation_ops.run_behavior_test, validation_ops.run_multiplayer_test,
        )
        for handler in handlers:
            with self.subTest(handler=handler.__name__), self.assertRaises(OperationError) as raised:
                handler(self.store, {})
            self.assertEqual("NOT_AVAILABLE", raised.exception.code)
            self.assertFalse(raised.exception.details["mutated"])
            self.assertFalse(raised.exception.details["success_implied"])
            self.assertEqual(revision, self.store.revision)

    def test_missing_evidence_is_not_reported_as_validation_success(self) -> None:
        for handler in (validation_ops.validate_static, validation_ops.verify_persistence, validation_ops.compare_expected_behavior):
            with self.subTest(handler=handler.__name__):
                with self.assertRaises(OperationError) as raised:
                    handler(self.store, {})
                self.assertEqual("NOT_AVAILABLE", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
