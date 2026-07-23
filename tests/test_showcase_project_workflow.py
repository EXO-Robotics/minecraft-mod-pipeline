from __future__ import annotations

import tempfile
import unittest
import zipfile
import json
import hashlib
from pathlib import Path

from mccompiler.operations.registry import OperationRegistry
from mccompiler.project.store import ProjectStore
from tools.build_benchmark_a import build


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks/original-marketplace-showcase/fixture"
SHOWCASE = ROOT / "benchmarks/original-marketplace-showcase"


class ShowcaseProjectWorkflowTests(unittest.TestCase):
    def test_reproducible_builder_applies_all_evidence_linked_runtime_overrides(self) -> None:
        override_document = json.loads((SHOWCASE / "runtime-overrides.json").read_text())
        overrides = override_document["overrides"]
        self.assertEqual(10, len(overrides))
        self.assertEqual(10, len({row["target"] for row in overrides}))
        for row in overrides:
            self.assertIn(row["strategy"], {"SCRIPTED_EQUIVALENT", "RECONSTRUCTED"})
            self.assertTrue(row["behavior_patch"]["actions"])
            self.assertTrue(row["provenance"]["author"])
            self.assertTrue(row["provenance"]["reason"])

        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first"
            second = Path(directory) / "second"
            first_result = build(first)
            second_result = build(second)
            self.assertEqual(13, first_result["content_count"])
            self.assertEqual(10, first_result["behavior_count"])
            self.assertTrue(all(first_result["validation"].values()))
            self.assertFalse(first_result["marketplace_candidate"]["passed"])
            first_addon = first / first_result["mcaddon"]["path"]
            second_addon = second / second_result["mcaddon"]["path"]
            self.assertEqual(
                hashlib.sha256(first_addon.read_bytes()).hexdigest(),
                hashlib.sha256(second_addon.read_bytes()).hexdigest(),
            )
            first_world = first / first_result["mcworld"]["path"]
            second_world = second / second_result["mcworld"]["path"]
            self.assertEqual(
                hashlib.sha256(first_world.read_bytes()).hexdigest(),
                hashlib.sha256(second_world.read_bytes()).hexdigest(),
            )
            with zipfile.ZipFile(first_addon) as archive:
                names = archive.namelist()
            self.assertFalse(any("gametest" in name or "diagnostic" in name for name in names))

    def test_public_operations_produce_resumable_clean_showcase_artifacts(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project = Path(temporary.name) / "showcase-project"
        registry = OperationRegistry()

        def call(operation: str, parameters: dict[str, object] | None = None, *, mutate: bool = False) -> dict[str, object]:
            request: dict[str, object] = {
                "schema_version": "1.0.0", "request_id": operation, "operation": operation,
                "project": str(project), "parameters": parameters or {},
            }
            if mutate and project.exists():
                request["expected_revision"] = ProjectStore.open(project).revision
            response = registry.execute(request)
            self.assertTrue(response["ok"], response)
            return response

        call("create_conversion_project", {"name": "Clockwork Gardens", "target_profile": "MARKETPLACE_ADDON_STABLE"})
        scanned = call("scan_mod", {"input": str(FIXTURE)}, mutate=True)
        expected = json.loads((ROOT / "benchmarks/original-marketplace-showcase/expected-ir.json").read_text())
        self.assertEqual(sum(len(rows) for rows in expected["content"].values()), scanned["result"]["content_count"])
        self.assertEqual(len(expected["behaviors"]), scanned["result"]["behavior_count"])

        call("generate_pack", mutate=True)
        static = call("validate_static", {"marketplace": True})
        self.assertTrue(static["result"]["valid"], static["result"])
        scripts = call("validate_scripts")
        self.assertTrue(scripts["result"]["valid"], scripts["result"])
        assets = call("validate_assets")
        self.assertTrue(assets["result"]["valid"], assets["result"])
        performance = call("validate_performance")
        self.assertTrue(performance["result"]["passed"], performance["result"])

        world = call("generate_world", {"world_name": "Clockwork Gardens Validation"}, mutate=True)
        packaged = call("package_mcaddon", mutate=True)
        candidate = call("evaluate_marketplace_candidate", mutate=True)
        self.assertFalse(candidate["result"]["candidate"]["passed"])
        self.assertTrue(candidate["result"]["candidate"]["blockers"]["rights"])
        self.assertTrue(candidate["result"]["candidate"]["blockers"]["creator_tools"])
        call("generate_conversion_report", mutate=True)

        store = ProjectStore.open(project)
        self.assertTrue(store.resolve(world["result"]["world"]["path"]).is_file())
        archive = store.resolve(packaged["result"]["archive"]["path"])
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
        self.assertTrue(names)
        self.assertTrue(all(name.startswith(("behavior_pack/", "resource_pack/")) for name in names))
        self.assertFalse(any("report" in name or "evidence" in name or name.startswith("tests/") for name in names))
        self.assertTrue(store.resolve("dist/reports/conversion-report.html").is_file())
        reopened = registry.execute({"schema_version": "1.0.0", "request_id": "resume", "operation": "open_conversion_project", "project": str(project), "parameters": {}})
        self.assertTrue(reopened["ok"], reopened)
        self.assertTrue(reopened["result"]["scanned"])


if __name__ == "__main__":
    unittest.main()
