from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from mccompiler.operations import validation_ops
from mccompiler.operations.envelope import OperationError
from mccompiler.project.store import ProjectStore
from mccompiler.runtime.bds import BDSDiagnosticError, BDSRunRequest, analyze_bds_log, docker_run_command, extract_mcworld


class BDSRuntimeAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def world(self, name: str = "Adapter Fixture") -> Path:
        path = self.root / "fixture.mcworld"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("levelname.txt", name)
            archive.writestr("level.dat", b"fixture")
            archive.writestr("behavior_packs/demo/manifest.json", "{}")
        return path

    def test_world_extraction_and_command_are_isolated(self) -> None:
        request = BDSRunRequest("registry/bds@sha256:" + "a" * 64, self.world(), self.root / "run")
        data = self.root / "data"
        level_name, destination = extract_mcworld(request.mcworld, data)
        self.assertEqual("Adapter Fixture", level_name)
        self.assertTrue((destination / "behavior_packs/demo/manifest.json").is_file())
        command = docker_run_command(request, container_name="mccompiler-bds-test", data_root=data, level_name=level_name)
        self.assertIn("--network", command)
        self.assertIn("none", command)
        self.assertNotIn("-p", command)
        self.assertIn("--pull", command)
        self.assertIn("never", command)
        self.assertIn("ALLOW_LIST=false", command)
        self.assertIn("WHITE_LIST=false", command)
        self.assertIn("CONTENT_LOG_CONSOLE_OUTPUT_ENABLED=true", command)

        networked = BDSRunRequest(request.image, request.mcworld, request.run_root, network_mode="bridge", bds_version="1.26.33.2")
        networked_command = docker_run_command(networked, container_name="mccompiler-bds-net", data_root=data, level_name=level_name)
        self.assertIn("bridge", networked_command)
        self.assertIn("VERSION=1.26.33.2", networked_command)
        self.assertNotIn("-p", networked_command)

    def test_archive_traversal_is_rejected(self) -> None:
        path = self.root / "unsafe.mcworld"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("levelname.txt", "Unsafe")
            archive.writestr("../escape.txt", "no")
        with self.assertRaises(BDSDiagnosticError):
            extract_mcworld(path, self.root / "data")
        self.assertFalse((self.root / "escape.txt").exists())

    def test_log_analysis_requires_boot_script_and_clean_log(self) -> None:
        passed = analyze_bds_log([
            "Version: 1.26.33.2", "Build Id: 47564860", "Server started.",
            "[Scripting] [mccompiler] runtime initialized behaviors=10",
        ])
        self.assertTrue(passed["booted"])
        self.assertTrue(passed["script_initialized"])
        self.assertTrue(passed["clean"])
        self.assertEqual("1.26.33.2", passed["bedrock_version"])
        failed = analyze_bds_log(["Server started.", "[ERROR] script failed to load"])
        self.assertFalse(failed["script_initialized"])
        self.assertFalse(failed["clean"])

    def test_public_operation_requires_explicit_execution_and_digest(self) -> None:
        store = ProjectStore.create(self.root / "project")
        world = store.resolve("dist/test-world/converted-test-world.mcworld")
        world.parent.mkdir(parents=True, exist_ok=True)
        world.write_bytes(self.world().read_bytes())
        with self.assertRaises(OperationError) as unavailable:
            validation_ops.start_test_runtime(store, {})
        self.assertEqual("NOT_AVAILABLE", unavailable.exception.code)
        with self.assertRaises(OperationError) as mutable:
            validation_ops.start_test_runtime(store, {"adapter": "BDS_DOCKER", "execute": True, "image": "registry/bds:latest"})
        self.assertEqual("MUTABLE_RUNTIME_IMAGE", mutable.exception.code)
        with self.assertRaises(OperationError) as network:
            validation_ops.start_test_runtime(store, {
                "adapter": "BDS_DOCKER", "execute": True,
                "image": "registry/bds@sha256:" + "a" * 64, "network_mode": "bridge",
            })
        self.assertEqual("NETWORK_NOT_AUTHORIZED", network.exception.code)

    def test_public_operation_persists_narrow_boot_claims(self) -> None:
        store = ProjectStore.create(self.root / "project")
        world = store.resolve("dist/test-world/converted-test-world.mcworld")
        world.parent.mkdir(parents=True, exist_ok=True)
        world.write_bytes(self.world().read_bytes())

        def fake_run(request: BDSRunRequest) -> dict[str, object]:
            request.run_root.mkdir(parents=True)
            (request.run_root / "content.log").write_text("Server started.\nruntime initialized\n")
            result: dict[str, object] = {
                "status": "BDS_DIAGNOSTIC_BOOT_VERIFIED", "passed": True,
                "runtime": {"image": request.image},
                "claims": {"bds_boot_verified": True, "gameplay_verified": False, "persistence_verified": False, "multiplayer_verified": False, "console_verified": False, "marketplace_approval_implied": False},
            }
            (request.run_root / "result.json").write_text(json.dumps(result))
            return result

        revision = store.revision
        with patch.object(validation_ops, "run_bds_diagnostic", side_effect=fake_run):
            response, _, artifacts = validation_ops.start_test_runtime(store, {
                "adapter": "BDS_DOCKER", "execute": True, "image": "registry/bds@sha256:" + "b" * 64,
            }, revision)
        self.assertEqual(revision + 1, response["revision"])
        self.assertFalse(response["run"]["claims"]["gameplay_verified"])
        self.assertFalse(response["run"]["claims"]["console_verified"])
        self.assertEqual(4, len(artifacts))
        self.assertTrue(store.resolve("reports/bds-diagnostic-validation.json").is_file())


if __name__ == "__main__":
    unittest.main()
