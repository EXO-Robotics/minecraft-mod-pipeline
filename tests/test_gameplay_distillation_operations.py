from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from mccompiler.cli import MILESTONE_COMMANDS, main
from mccompiler.operations.registry import OperationRegistry
from mccompiler.project.store import ProjectStore
from mccompiler.forest_planning.waves import DIMENSIONS


class GameplayDistillationOperationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "project"
        self.store = ProjectStore.create(self.root, name="forest")
        self.registry = OperationRegistry()

    def request(self, operation: str, parameters: dict[str, object] | None = None) -> dict[str, object]:
        return self.registry.execute({
            "schema_version": "1.0.0",
            "request_id": f"test-{operation}",
            "operation": operation,
            "project": str(self.root),
            "parameters": parameters or {},
            "expected_revision": ProjectStore.open(self.root).revision,
        })

    def test_every_milestone_operation_is_available(self) -> None:
        catalog = self.registry.catalog()
        for operation in MILESTONE_COMMANDS.values():
            self.assertIn(operation, catalog)
            self.assertEqual("AVAILABLE", catalog[operation]["status"])
            self.assertEqual("gameplay_distillation", catalog[operation]["category"])

    def test_new_project_has_explicit_versioned_clean_room_default(self) -> None:
        strategy = self.store.read("analysis/rights-ledger/strategy.json")
        self.assertEqual("1.0.0", strategy["schema_version"])
        self.assertEqual("clean_room_originalization", strategy["mode"])
        self.assertEqual("abstract_gameplay_patterns_only", strategy["inspiration_scope"])
        self.assertEqual("prohibited", strategy["direct_source_expression_reuse"])
        self.assertFalse(strategy["third_party_assets_allowed"])
        self.assertFalse(strategy["third_party_names_allowed"])
        self.assertFalse(strategy["third_party_branding_allowed"])
        self.assertFalse(strategy["distinctive_expression_allowed"])
        self.assertTrue(strategy["commercial_marketplace_rights_required"])

    def test_cli_json_uses_operation_envelope_and_stable_exit(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            code = main([
                "create-rights-strategy", "--project", str(self.root),
                "--expected-revision", str(self.store.revision), "--json",
            ])
        response = json.loads(output.getvalue())
        self.assertEqual(0, code)
        self.assertTrue(response["ok"])
        self.assertEqual("create_rights_strategy", response["operation"])
        self.assertEqual("analysis/rights-ledger/strategy.json", response["artifacts"][0]["path"])
        self.assertEqual("clean_room_originalization", response["result"]["document"]["mode"])

    def test_experience_graph_coverage_and_wave_plan_are_persisted(self) -> None:
        graph = self.request("build_experience_graph", {"nodes": [
            {"node_id": "ruin", "weight": 40, "evidence": "SERVER_QUALIFIED"},
            {"node_id": "elite", "weight": 60, "dependencies": ["ruin"]},
        ]})
        self.assertTrue(graph["ok"], graph)
        coverage = self.request("calculate_experience_coverage")
        self.assertTrue(coverage["ok"], coverage)
        self.assertEqual(4000, coverage["result"]["document"]["coverage"]["basis_points"])

        plan = self.request("plan_production_wave", {
            "budget": {
                "hard_caps": {name: 20 for name in DIMENSIONS},
                "reserves": {name: 4 for name in DIMENSIONS},
            },
            "elements": [
                {"id": "ruin", "priority": 2, "scope_units": 2, "costs": {name: 1 for name in DIMENSIONS}},
                {"id": "elite", "priority": 1, "scope_units": 2, "costs": {name: 1 for name in DIMENSIONS}, "dependencies": ["ruin"]},
            ],
        })
        self.assertTrue(plan["ok"], plan)
        shown = self.request("show_production_wave")
        self.assertTrue(shown["ok"])
        self.assertEqual(["ruin"], shown["result"]["plan"]["waves"][0]["elements"])
        self.assertFalse(shown["result"]["production_authorized"])


if __name__ == "__main__":
    unittest.main()
