from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from mccompiler.creator_tools import discover_creator_tools, invoke_creator_tools, normalize_creator_tools_output
from mccompiler.performance import audit_static_performance
from mccompiler.rights import evaluate_marketplace_rights


FIXTURES = Path(__file__).parent / "fixtures" / "creator_tools"


def rights(status: str, *, reviewer_type: str | None = None) -> dict:
    decision = {"status": status}
    if reviewer_type:
        decision.update({"reviewer_type": reviewer_type, "reviewed_by": "Alex Reviewer", "reviewer_id": "reviewer:alex", "reviewed_at": "2026-07-22T12:00:00Z"})
    return {"schema_version": "1.0.0", "records": [{"content_id": "demo:texture", "content_type": "texture", "source": {}, "rights": {}, "evidence": ["LICENSE-ASSETS"], "decision": decision}]}


class RightsTests(unittest.TestCase):
    def test_unknown_and_review_required_block_candidate(self) -> None:
        for status in ("UNKNOWN", "REVIEW_REQUIRED"):
            with self.subTest(status=status):
                result = evaluate_marketplace_rights(rights(status))
                self.assertFalse(result["marketplace_candidate_allowed"])
                self.assertEqual(["demo:texture"], result["blocking_content_ids"])

    def test_only_attributable_human_may_clear(self) -> None:
        for reviewer_type in (None, "ai", "automated"):
            with self.subTest(reviewer_type=reviewer_type):
                result = evaluate_marketplace_rights(rights("MARKETPLACE_CLEARED", reviewer_type=reviewer_type))
                self.assertFalse(result["marketplace_candidate_allowed"])
                self.assertTrue(any("attributable human" in error for error in result["errors"]))
        cleared = evaluate_marketplace_rights(rights("MARKETPLACE_CLEARED", reviewer_type="human"))
        self.assertTrue(cleared["marketplace_candidate_allowed"])
        self.assertFalse(cleared["legal_clearance_implied"])


class PerformanceTests(unittest.TestCase):
    def test_pack_file_and_texture_budgets_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.png").write_bytes(b"1234")
            (root / "b.txt").write_bytes(b"12")
            catalog = {"catalog_version": "test", "target": "MARKETPLACE_ADDON_STABLE", "static_budgets": {"pack_bytes": 5, "file_count": 1, "texture_count": 0}}
            result = audit_static_performance(root, catalog=catalog)
            self.assertFalse(result["passed"])
            self.assertEqual({"pack_bytes", "file_count", "texture_count"}, {check["metric"] for check in result["checks"] if not check["passed"]})

    def test_exceeded_budget_requires_explicit_attributable_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "a.png").write_bytes(b"1234")
            catalog = {"catalog_version": "test", "target": "MARKETPLACE_ADDON_STABLE", "static_budgets": {"pack_bytes": 1, "file_count": 1, "texture_count": 1}}
            weak = [{"metric": "pack_bytes", "approved_by_type": "ai", "approved_by": "bot", "approver_id": "bot", "approved_at": "2026-07-22T12:00:00Z", "reason": "fine"}]
            self.assertFalse(audit_static_performance(root, catalog=catalog, approved_exceptions=weak)["passed"])
            approved = [{"metric": "pack_bytes", "approved_by_type": "human", "approved_by": "Alex", "approver_id": "reviewer:alex", "approved_at": "2026-07-22T12:00:00Z", "reason": "Measured on target hardware"}]
            self.assertTrue(audit_static_performance(root, catalog=catalog, approved_exceptions=approved)["passed"])


class CreatorToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lock = {"version": "0.17.6", "version_args": ["--version"], "global_validate_args": ["--offline", "--json", "--yes"], "required_suites": ["addon", "currentplatform"], "allowed_suites": ["addon", "currentplatform"]}
        self.policy = {"severity_map": {"error": "error", "warn": "warning", "info": "info"}}

    def test_recorded_output_normalizes_deterministically(self) -> None:
        payload = json.loads((FIXTURES / "recorded-findings.json").read_text())
        first = normalize_creator_tools_output(payload, version="1.0.0", suites=["scripts", "addon"], policy=self.policy)
        second = normalize_creator_tools_output(payload, version="1.0.0", suites=["addon", "scripts"], policy=self.policy)
        self.assertEqual(first, second)
        report = first["creator_tools"]
        self.assertEqual("1.0.0", report["version"])
        self.assertEqual(["addon", "scripts"], report["suites"])
        self.assertEqual((1, 1, False), (report["errors"], report["warnings"], report["marketplace_approval_implied"]))

    def test_real_cli_shape_is_normalized_without_counting_test_fail_twice(self) -> None:
        payload = {"projects": [{"items": [
            {"type": "testFail", "message": "Found one error", "generatorId": "CADDONREQ"},
            {"type": "error", "message": "Bad identifier", "path": "/manifest.json", "generatorId": "CADDONREQ"},
            {"type": "testPass", "message": "Texture passed", "generatorId": "TEXTURE"},
        ]}], "errors": 2, "warnings": 0}
        result = normalize_creator_tools_output(payload, version="0.17.6", suites=["addon"], policy=self.policy)
        self.assertEqual(1, result["creator_tools"]["errors"])
        self.assertEqual(0, result["creator_tools"]["warnings"])
        self.assertFalse(result["passed"])

    def test_discovery_uses_only_pinned_executable_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "mct"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            found = discover_creator_tools({"executables": ["mct"]}, search_path=directory)
            self.assertEqual(executable.resolve(), found)
            self.assertIsNone(discover_creator_tools({"executables": ["not-pinned"]}, search_path=directory))

    def test_invocation_uses_pinned_version_and_recorded_json_without_network(self) -> None:
        payload = (FIXTURES / "recorded-clean.json").read_text()
        calls = []
        def fake_runner(command, **kwargs):
            calls.append(command)
            if "--version" in command:
                return subprocess.CompletedProcess(command, 0, stdout="0.17.6\n", stderr="")
            return subprocess.CompletedProcess(command, 0, stdout=payload, stderr="")
        result = invoke_creator_tools("/fake/mct", ".", lock=self.lock, policy=self.policy, runner=fake_runner)
        self.assertTrue(result["passed"])
        self.assertEqual(3, len(calls))
        self.assertIn("currentplatform", calls[2])
        self.assertFalse(result["creator_tools"]["marketplace_approval_implied"])

    def test_archive_uses_hash_named_copy_and_rejects_stale_cache_paths(self) -> None:
        payload = {"projects": [{"items": [{"type": "error", "message": "old cache", "path": "/resource_pack/old.png", "generatorId": "STALE"}]}]}
        seen_inputs = []
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "converted-mod.mcaddon"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("behavior_pack/manifest.json", "{}")
            digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
            def fake_runner(command, **kwargs):
                if "--version" in command:
                    return subprocess.CompletedProcess(command, 0, stdout="0.17.6\n", stderr="")
                input_path = Path(command[command.index("--input-file") + 1])
                self.assertTrue(input_path.is_file())
                seen_inputs.append(input_path.name)
                return subprocess.CompletedProcess(command, 4, stdout=json.dumps(payload), stderr="")
            result = invoke_creator_tools("/fake/mct", archive_path, lock=self.lock, policy=self.policy, runner=fake_runner)
        self.assertEqual([f"artifact-{digest}.mcaddon"] * 2, seen_inputs)
        self.assertEqual(digest, result["creator_tools"]["validated_input"]["sha256"])
        self.assertTrue(any(row["code"] == "STALE_CACHE_PATH" for row in result["creator_tools"]["findings"]))
        self.assertFalse(result["passed"])

    def test_timestamped_debug_prelude_is_preserved_before_complete_json(self) -> None:
        clean = json.loads((FIXTURES / "recorded-clean.json").read_text())
        stdout = "[2026-07-22T20:26:36.999Z] [DEBUG] offline lookup unavailable\n" + json.dumps(clean)
        def fake_runner(command, **kwargs):
            if "--version" in command:
                return subprocess.CompletedProcess(command, 0, stdout="0.17.6\n", stderr="")
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")
        result = invoke_creator_tools("/fake/mct", ".", lock=self.lock, policy=self.policy, runner=fake_runner)
        self.assertTrue(result["passed"])
        self.assertEqual(2, len(result["creator_tools"]["cli_stdout_prelude"]))
        self.assertTrue(all("offline lookup unavailable" in row["lines"][0] for row in result["creator_tools"]["cli_stdout_prelude"]))

    def test_version_mismatch_and_unknown_suite_fail(self) -> None:
        def bad_version(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, stdout="9.9.9\n", stderr="")
        with self.assertRaisesRegex(RuntimeError, "version mismatch"):
            invoke_creator_tools("/fake/mctools", ".", lock=self.lock, policy=self.policy, runner=bad_version)
        with self.assertRaisesRegex(ValueError, "Unsupported Creator Tools suites"):
            invoke_creator_tools("/fake/mctools", ".", lock=self.lock, policy=self.policy, suites=["mystery"], runner=bad_version)


if __name__ == "__main__":
    unittest.main()
