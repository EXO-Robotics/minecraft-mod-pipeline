from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mccompiler.operations.registry import REQUIRED_OPERATION_CATALOG, OperationRegistry
from mccompiler.project.store import ProjectError, ProjectStore


def evidence() -> list[dict[str, object]]:
    return [{"source_file": "Example.java", "line_range": [1, 2], "source_mode": "test", "confidence": 0.8}]


def modir() -> dict[str, object]:
    behavior = {
        "id": "demo:wand/use", "owner": {"kind": "item", "identifier": "demo:wand"},
        "trigger": {"type": "item_use"}, "conditions": [], "actions": [{"type": "send_player_feedback"}],
        "evidence": evidence(), "confidence": 0.8,
        "diagnostics": [{"severity": "info", "code": "review", "message": "Confirm intent"}],
    }
    return {
        "schema_version": "1.0.0", "metadata": {"id": "demo"},
        "mods": [{"id": "demo", "name": "Demo"}],
        "dependencies": [{"from": "demo", "to": "fabricloader", "kind": "required"}],
        "dependency_graph": {
            "nodes": [{"id": "demo"}, {"id": "fabricloader"}],
            "edges": [{"from": "demo", "to": "fabricloader", "kind": "required"}],
        },
        "content": [
            {"kind": "item", "identifier": "demo:wand", "properties": {}, "evidence": evidence()},
            {"kind": "block", "identifier": "demo:machine", "properties": {}, "evidence": evidence()},
            {"kind": "entity", "identifier": "demo:golem", "properties": {}, "evidence": evidence()},
            {"kind": "recipe", "identifier": "demo:wand_recipe", "properties": {}, "evidence": evidence()},
            {"kind": "structure", "identifier": "demo:arena", "properties": {}, "evidence": evidence()},
        ],
        "assets": [{"kind": "textures", "count": 2, "evidence": ["assets/demo/textures/wand.png"]}],
        "registries": [], "behaviors": [behavior],
        "state": [{"id": "demo:charge", "scope": "player", "value_type": "number", "default": 0, "persistence": "persistent", "evidence": evidence()}],
        "presentation_requirements": [],
        "world_requirements": [{"id": "demo:ore", "kind": "worldgen", "evidence": evidence()}],
        "ui_intent": [{"id": "demo:menu", "title": "Menu", "evidence": evidence()}],
        "networking_intent": [{"id": "demo:activate", "direction": "client_to_server", "evidence": evidence()}],
        "unsupported_hooks": [
            {"feature": "mixin:DemoMixin", "code": "unsupported_hook", "evidence": evidence()},
            {"feature": "coremod:DemoTransformer", "code": "unsupported_hook", "evidence": evidence()},
        ],
        "diagnostics": [], "tests": [], "errors": [],
    }


class AgentOperationCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "conversion"
        self.registry = OperationRegistry()
        created = self.run_operation("create_conversion_project", {"name": "Catalog fixture"})
        self.assertTrue(created["ok"])
        self.store = ProjectStore.open(self.root)
        ir = modir()
        self.store.commit({
            "analysis/modir.json": ir,
            "analysis/inventory.json": {"schema_version": "1.0.0", "mods": ir["mods"], "content": ir["content"], "assets": ir["assets"]},
            "analysis/dependency-graph.json": {"schema_version": "1.0.0", **ir["dependency_graph"]},
            "ir/content.json": {"schema_version": "1.0.0", "content": ir["content"]},
            "ir/behaviors.json": {"schema_version": "1.0.0", "behaviors": ir["behaviors"]},
            "ir/state.json": {"schema_version": "1.0.0", "state": ir["state"]},
            "ir/ui-intent.json": {"schema_version": "1.0.0", "ui_intent": ir["ui_intent"]},
            "ir/networking-intent.json": {"schema_version": "1.0.0", "networking_intent": ir["networking_intent"]},
        }, manifest_updates={"analysis_revision": 2, "input": {"path": "fixture"}})

    def run_operation(self, operation: str, parameters: dict[str, object] | None = None, expected_revision: int | None = None) -> dict[str, object]:
        request: dict[str, object] = {
            "schema_version": "1.0.0", "request_id": f"test-{operation}",
            "operation": operation, "project": str(self.root), "parameters": parameters or {},
        }
        if expected_revision is not None:
            request["expected_revision"] = expected_revision
        return self.registry.execute(request)

    def test_every_required_operation_is_registered_and_classified(self) -> None:
        required = {name for names in REQUIRED_OPERATION_CATALOG.values() for name in names}
        self.assertEqual(required, set(self.registry.catalog()))
        self.assertTrue(required <= set(self.registry.handlers))
        self.assertEqual({"AVAILABLE", "NOT_AVAILABLE"}, {row["status"] for row in self.registry.catalog().values()})

    def test_focused_artifact_inspection_and_tracing(self) -> None:
        cases = {
            "inspect_mod": ({"id": "demo"}, "mods"),
            "inspect_item": ({"id": "demo:wand"}, "content"),
            "inspect_block": ({"id": "demo:machine"}, "content"),
            "inspect_entity": ({"id": "demo:golem"}, "content"),
            "inspect_recipe": ({"id": "demo:wand_recipe"}, "content"),
            "inspect_structure": ({"id": "demo:arena"}, "content"),
            "inspect_state": ({"id": "demo:charge"}, "state"),
            "inspect_asset": ({"kind": "textures"}, "assets"),
            "inspect_gui": ({"id": "demo:menu"}, "ui_intent"),
            "inspect_packet": ({"id": "demo:activate"}, "networking_intent"),
            "inspect_worldgen": ({"id": "demo:ore"}, "world_requirements"),
            "inspect_mixin": ({"id": "mixin:DemoMixin"}, "unsupported_hooks"),
            "inspect_coremod": ({"id": "coremod:DemoTransformer"}, "unsupported_hooks"),
        }
        revision = ProjectStore.open(self.root).revision
        for operation, (parameters, result_key) in cases.items():
            response = self.run_operation(operation, parameters)
            self.assertTrue(response["ok"], response)
            self.assertTrue(response["result"][result_key])
            self.assertEqual(revision, response["project_revision"])

        dependency = self.run_operation("trace_dependency", {"id": "demo", "direction": "outgoing"})
        self.assertTrue(dependency["ok"])
        self.assertEqual("fabricloader", dependency["result"]["outgoing"][0]["to"])
        ambiguous = self.run_operation("list_ambiguous_behaviors")
        self.assertEqual(["demo:wand/use"], [row["id"] for row in ambiguous["result"]["ambiguous_behaviors"]])
        unsupported = self.run_operation("list_unsupported_operations")
        self.assertEqual(2, unsupported["result"]["count"])

    def test_strategy_and_decision_records_resume_with_revision_safety(self) -> None:
        comparison = self.run_operation("compare_bedrock_strategies", {"target": "demo:wand/use"})
        self.assertTrue(comparison["ok"])
        self.assertIsNone(comparison["result"]["recommendation"])
        self.assertIn("MANUAL_REDESIGN", {row["strategy"] for row in comparison["result"]["candidates"]})

        revision = ProjectStore.open(self.root).revision
        provenance = {"author": "agent:test", "reason": "Reviewed fixture evidence"}
        accepted = self.run_operation("accept_approximation", {
            "target": "demo:wand/use", "preserved": ["feedback"], "lost": ["custom renderer"], "provenance": provenance,
        }, revision)
        self.assertTrue(accepted["ok"], accepted)

        stale = self.run_operation("record_manual_redesign", {
            "target": "demo:wand/use", "design": {"interaction": "controller item use"}, "provenance": provenance,
        }, revision)
        self.assertFalse(stale["ok"])
        self.assertEqual("REVISION_CONFLICT", stale["diagnostics"][0]["code"])

        current = ProjectStore.open(self.root).revision
        redesigned = self.run_operation("record_manual_redesign", {
            "target": "demo:wand/use", "design": {"interaction": "controller item use"}, "provenance": provenance,
        }, current)
        self.assertTrue(redesigned["ok"])
        current = redesigned["project_revision"]
        overridden = self.run_operation("apply_override", {
            "override": {"target": "demo:wand/use", "strategy": "MANUAL_REDESIGN", "behavior_patch": {"actions": [{"type": "send_player_feedback"}]}, "provenance": provenance}
        }, current)
        self.assertTrue(overridden["ok"], overridden)

        resumed = ProjectStore.open(self.root)
        self.assertEqual("APPROXIMATION_ACCEPTED", resumed.read("decisions/approvals.yaml")["approvals"][0]["decision"])
        self.assertEqual("controller item use", resumed.read("decisions/redesigns.yaml")["redesigns"][0]["design"]["interaction"])
        self.assertEqual("MANUAL_REDESIGN", resumed.read("decisions/overrides.yaml")["overrides"][0]["strategy"])
        with self.assertRaisesRegex(ProjectError, "protected path"):
            resumed.commit({"custom/scripts/owned.js": "overwritten"})

    def test_validate_report_and_structured_unavailable_are_honest(self) -> None:
        valid = self.run_operation("validate_ir")
        self.assertTrue(valid["ok"])
        self.assertTrue(valid["result"]["valid"])

        revision = ProjectStore.open(self.root).revision
        report = self.run_operation("generate_conversion_report", expected_revision=revision)
        self.assertTrue(report["ok"], report)
        persisted = ProjectStore.open(self.root).read("reports/conversion-project-report.json")
        self.assertEqual(report["result"]["report"], persisted)
        self.assertFalse(persisted["claims"]["marketplace_approval_implied"])
        self.assertFalse(persisted["claims"]["runtime_verified"])
        self.assertFalse(persisted["claims"]["console_verified"])

        current = ProjectStore.open(self.root).revision
        for operation in ("generate_pack", "install_test_pack", "start_test_runtime", "run_multiplayer_test", "verify_persistence"):
            blocked = self.run_operation(operation)
            self.assertFalse(blocked["ok"], blocked)
            self.assertEqual("NOT_AVAILABLE", blocked["diagnostics"][0]["code"])
            details = blocked["diagnostics"][0]["details"]
            self.assertEqual("NOT_AVAILABLE", details["status"])
            self.assertFalse(details["mutated"])
            self.assertFalse(details["success_implied"])
            self.assertTrue(details["blocker"])
            self.assertEqual(current, blocked["project_revision"])
            self.assertEqual(current, ProjectStore.open(self.root).revision)


if __name__ == "__main__":
    unittest.main()
