from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mccompiler.operations.registry import OperationRegistry
from mccompiler.project.store import ProjectStore


class IntentAndSafeEditOperationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "project"
        self.registry = OperationRegistry()
        self.call("create_conversion_project", {"name": "Intent fixture"})
        store = ProjectStore.open(self.root)
        evidence = {"source_file": "Example.java", "source_mode": "source", "line_range": [4, 8], "confidence": 0.9}
        store.commit({
            "ir/behaviors.json": {"schema_version": "1.0.0", "behaviors": [{"id": "demo:use", "evidence": [evidence]}]},
            "analysis/source-index/calls.json": {"schema_version": "1.0.0", "calls": [{"caller": "Demo.use", "callee": "Demo.activate", "source_file": "Example.java", "line": 7}]},
        })

    def call(self, operation: str, parameters: dict[str, object] | None = None, revision: int | None = None) -> dict[str, object]:
        request: dict[str, object] = {"schema_version": "1.0.0", "request_id": operation, "operation": operation, "project": str(self.root), "parameters": parameters or {}}
        if revision is not None:
            request["expected_revision"] = revision
        return self.registry.execute(request)

    def test_proposal_review_is_persistent_and_advisory(self) -> None:
        revision = ProjectStore.open(self.root).revision
        proposed = self.call("propose_behavior_intent", {
            "proposal_id": "intent-1", "target": "demo:use", "proposal": {"trigger": "item_use"},
            "evidence": [{"source_file": "Example.java", "source_mode": "source", "line_range": [4, 8]}],
            "prompt_provenance": {"template_id": "intent", "template_version": "1", "prompt_sha256": "abc"},
            "model_provenance": {"provider": "offline-test", "model": "fixture", "adapter_version": "1"},
            "confidence": 0.8,
        }, revision)
        self.assertTrue(proposed["ok"], proposed)
        proposal = proposed["result"]["proposal"]
        self.assertEqual("advisory-only", proposal["authority"])
        accepted = self.call("accept_behavior_intent", {"proposal_id": "intent-1", "reviewer": "human:test", "reviewed_at": "2026-07-22T12:00:00Z", "reason": "Evidence reviewed"}, proposed["project_revision"])
        self.assertTrue(accepted["ok"], accepted)
        self.assertEqual("accepted", accepted["result"]["proposal"]["human_acceptance"]["state"])
        self.assertEqual("intent-1", ProjectStore.open(self.root).read("decisions/intent-reviews.json")["reviews"][0]["proposal_id"])

    def test_queries_pattern_and_safe_edits_are_revision_bound(self) -> None:
        callers = self.call("trace_callers", {"symbol": "Demo.activate"})
        self.assertTrue(callers["ok"], callers)
        self.assertEqual("Demo.use", callers["result"]["callers"][0]["caller"])

        revision = ProjectStore.open(self.root).revision
        selected = self.call("select_pattern", {"target": "demo:use", "pattern_id": "forms/key-binding-replacement", "provenance": {"author": "agent:test", "reason": "controller design"}}, revision)
        self.assertTrue(selected["ok"], selected)
        written = self.call("write_custom_implementation", {"path": "custom/scripts/demo.js", "content": "export const enabled = true;\n", "author": "agent:test", "reason": "accepted custom behavior"}, selected["project_revision"])
        self.assertTrue(written["ok"], written)
        self.assertEqual("export const enabled = true;\n", (self.root / "custom/scripts/demo.js").read_text())

        patched = self.call("patch_ir_with_provenance", {"section": "behaviors", "id": "demo:use", "patch": {"accepted_intent": "item_use"}, "provenance": {"author": "agent:test", "reason": "reviewed", "evidence_ids": ["Example.java:4-8"]}}, written["project_revision"])
        self.assertTrue(patched["ok"], patched)
        stale = self.call("write_custom_implementation", {"path": "custom/scripts/stale.js", "content": "bad", "author": "agent:test", "reason": "stale"}, written["project_revision"])
        self.assertFalse(stale["ok"])
        self.assertEqual("REVISION_CONFLICT", stale["diagnostics"][0]["code"])

    def test_rights_clearance_requires_human_record(self) -> None:
        revision = ProjectStore.open(self.root).revision
        denied = self.call("add_rights_evidence", {"record": {"content_id": "demo:code", "decision": {"status": "MARKETPLACE_CLEARED", "reviewed_by_type": "agent"}}, "provenance": {"author": "agent:test", "reason": "scan"}}, revision)
        self.assertFalse(denied["ok"])
        self.assertEqual("HUMAN_REVIEW_REQUIRED", denied["diagnostics"][0]["code"])


if __name__ == "__main__":
    unittest.main()
