from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from mccompiler.agent.stdio_server import serve
from mccompiler.cli import main as cli_main
from mccompiler.operations.registry import OperationRegistry
from mccompiler.project.layout import PROJECT_DIRECTORIES, PROTECTED_DIRECTORIES
from mccompiler.project.store import ProjectStore


ROOT = Path(__file__).parent / "fixtures/representative_mod"


def request(operation: str, project: Path, **parameters):
    return {"schema_version": "1.0.0", "request_id": f"test:{operation}", "operation": operation, "project": str(project), "parameters": parameters}


class ConversionProjectMilestoneTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "conversion-project"
        self.registry = OperationRegistry()

    def tearDown(self):
        self.temporary.cleanup()

    def create(self):
        result = self.registry.execute(request("create_conversion_project", self.project, name="Fixture conversion"))
        self.assertTrue(result["ok"], result)
        return result

    def scan(self):
        result = self.registry.execute(request("scan_mod", self.project, input=str(ROOT)))
        self.assertTrue(result["ok"], result)
        return result

    def test_full_layout_and_protected_custom_directories(self):
        self.create()
        for relative in PROJECT_DIRECTORIES:
            self.assertTrue((self.project / relative).is_dir(), relative)
        marker = self.project / PROTECTED_DIRECTORIES[0] / "reviewed.js"
        marker.write_text("// protected\n", encoding="utf-8")
        self.scan()
        self.assertEqual("// protected\n", marker.read_text(encoding="utf-8"))
        store = ProjectStore.open(self.project)
        with self.assertRaisesRegex(ValueError, "protected"):
            store.commit({"custom/scripts/reviewed.js": "changed"})

    def test_create_scan_resume_query_and_decision(self):
        created = self.create()
        self.assertEqual(1, created["project_revision"])
        scanned = self.scan()
        self.assertGreater(scanned["result"]["behavior_count"], 0)
        self.assertEqual(2, scanned["project_revision"])

        reopened = self.registry.execute(request("open_conversion_project", self.project))
        self.assertTrue(reopened["ok"])
        self.assertTrue(reopened["result"]["scanned"])

        mods = self.registry.execute(request("list_mods", self.project))
        content = self.registry.execute(request("list_content", self.project, kind="item"))
        self.assertTrue(mods["result"]["mods"])
        self.assertTrue(content["result"]["content"])

        unresolved = self.registry.execute(request("list_unresolved_work", self.project))
        target = next(row["target"] for row in unresolved["result"]["work"] if row["kind"] == "behavior_strategy")
        inspected = self.registry.execute(request("inspect_behavior", self.project, id=target))
        self.assertEqual(target, inspected["result"]["behavior"]["id"])
        self.assertTrue(inspected["result"]["evidence_ids"])
        evidence = self.registry.execute(request("show_evidence", self.project, id=target))
        self.assertTrue(evidence["result"]["evidence"])

        decision_request = request("set_strategy", self.project, target=target, strategy="SCRIPTED_EQUIVALENT", provenance={"author": "Test reviewer", "reason": "Evidence reviewed"})
        decision_request["expected_revision"] = scanned["project_revision"]
        decided = self.registry.execute(decision_request)
        self.assertTrue(decided["ok"], decided)
        self.assertEqual(3, decided["project_revision"])
        resumed_store = ProjectStore.open(self.project)
        rows = resumed_store.read("decisions/strategies.yaml")["strategies"]
        self.assertEqual(target, rows[0]["target"])

        status = self.registry.execute(request("get_project_status", self.project))
        blockers = self.registry.execute(request("list_blocking_failures", self.project))
        task = self.registry.execute(request("get_next_recommended_task", self.project))
        self.assertEqual(3, status["result"]["revision"])
        self.assertTrue(blockers["result"]["failures"])
        self.assertEqual("list_blocking_failures", task["result"]["task"]["operation"])

    def test_structured_failures_and_revision_conflict(self):
        missing = self.registry.execute(request("get_project_status", self.project))
        self.assertFalse(missing["ok"])
        self.assertEqual("PROJECT_NOT_FOUND", missing["diagnostics"][0]["code"])
        self.create()
        self.scan()

        absent = self.registry.execute(request("inspect_behavior", self.project, id="missing:behavior"))
        self.assertFalse(absent["ok"])
        self.assertEqual("BEHAVIOR_NOT_FOUND", absent["diagnostics"][0]["code"])
        bad = request("set_strategy", self.project, target="missing:behavior", strategy="DIRECT", provenance={"author": "A", "reason": "B"})
        bad["expected_revision"] = 1
        conflict = self.registry.execute(bad)
        self.assertFalse(conflict["ok"])
        self.assertEqual("TARGET_NOT_FOUND", conflict["diagnostics"][0]["code"])

        target = self.registry.execute(request("list_unresolved_work", self.project))["result"]["work"][0]["target"]
        stale = request("set_strategy", self.project, target=target, strategy="DIRECT", provenance={"author": "A", "reason": "B"})
        stale["expected_revision"] = 1
        conflict = self.registry.execute(stale)
        self.assertFalse(conflict["ok"])
        self.assertEqual("REVISION_CONFLICT", conflict["diagnostics"][0]["code"])
        for key in ("schema_version", "request_id", "operation", "ok", "project_revision", "result", "diagnostics", "artifacts"):
            self.assertIn(key, conflict)

    def test_json_lines_agent_uses_same_registry_contract(self):
        lines = "not-json\n" + json.dumps(request("create_conversion_project", self.project)) + "\n" + json.dumps(request("get_project_status", self.project)) + "\n"
        output = io.StringIO()
        self.assertEqual(0, serve(io.StringIO(lines), output))
        responses = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual("INVALID_JSON", responses[0]["diagnostics"][0]["code"])
        self.assertTrue(responses[1]["ok"])
        self.assertTrue(responses[2]["ok"])
        self.assertEqual(responses[1]["project_revision"], responses[2]["project_revision"])

    def test_structured_cli_emits_only_response_envelope(self):
        request_path = Path(self.temporary.name) / "request.json"
        request_path.write_text(json.dumps(request("create_conversion_project", self.project)), encoding="utf-8")
        output = io.StringIO()
        with redirect_stdout(output):
            code = cli_main(["operation", "--request", str(request_path)])
        response = json.loads(output.getvalue())
        self.assertEqual(0, code)
        self.assertTrue(response["ok"])
        self.assertEqual("create_conversion_project", response["operation"])


if __name__ == "__main__":
    unittest.main()
