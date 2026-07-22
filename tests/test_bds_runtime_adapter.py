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
from mccompiler.runtime.bds import BDSConsoleProbe, BDSDiagnosticError, BDSLogProbe, BDSRunRequest, analyze_bds_log, docker_run_command, extract_mcworld, overlay_mcworld_packs, run_bds_diagnostic, validate_console_probes, validate_log_probes


class BDSRuntimeAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def world(self, name: str = "Adapter Fixture", filename: str = "fixture.mcworld") -> Path:
        path = self.root / filename
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
        self.assertNotIn("-i", command)

        probed = BDSRunRequest(
            request.image, request.mcworld, request.run_root,
            console_probes=(BDSConsoleProbe("probe", 1, 1.0, "testforblock 1 2 3 stone", "Successfully found"),),
        )
        probed_command = docker_run_command(probed, container_name="mccompiler-bds-probed", data_root=data, level_name=level_name)
        self.assertIn("-i", probed_command)

        networked = BDSRunRequest(request.image, request.mcworld, request.run_root, network_mode="bridge", bds_version="1.26.33.2")
        networked_command = docker_run_command(networked, container_name="mccompiler-bds-net", data_root=data, level_name=level_name)
        self.assertIn("bridge", networked_command)
        self.assertIn("VERSION=1.26.33.2", networked_command)
        self.assertNotIn("-p", networked_command)

        preview = BDSRunRequest(
            request.image, request.mcworld, request.run_root,
            network_mode="bridge", bds_version="1.26.50.20", preview_channel=True,
        )
        preview_command = docker_run_command(
            preview, container_name="mccompiler-bds-preview", data_root=data, level_name=level_name,
        )
        self.assertIn("VERSION=1.26.50.20", preview_command)
        self.assertIn("PREVIEW=true", preview_command)
        with self.assertRaisesRegex(BDSDiagnosticError, "exact bds_version"):
            docker_run_command(
                BDSRunRequest(request.image, request.mcworld, request.run_root, preview_channel=True),
                container_name="mccompiler-bds-invalid-preview", data_root=data, level_name=level_name,
            )

    def test_archive_traversal_is_rejected(self) -> None:
        path = self.root / "unsafe.mcworld"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("levelname.txt", "Unsafe")
            archive.writestr("../escape.txt", "no")
        with self.assertRaises(BDSDiagnosticError):
            extract_mcworld(path, self.root / "data")
        self.assertFalse((self.root / "escape.txt").exists())

    def test_upgrade_overlay_replaces_only_packs_and_preserves_world_database(self) -> None:
        initial = self.world(filename="initial.mcworld")
        data = self.root / "data"
        level_name, destination = extract_mcworld(initial, data)
        database = destination / "db/current"
        database.parent.mkdir()
        database.write_bytes(b"persistent-world-state")
        upgrade = self.root / "upgrade.mcworld"
        with zipfile.ZipFile(upgrade, "w") as archive:
            archive.writestr("levelname.txt", "Adapter Fixture")
            archive.writestr("level.dat", b"must-not-replace-world-database")
            archive.writestr("behavior_packs/next/manifest.json", '{"version":2}')
            archive.writestr("resource_packs/next/manifest.json", '{"version":2}')
            archive.writestr("world_behavior_packs.json", "[]")
            archive.writestr("world_resource_packs.json", "[]")
        result = overlay_mcworld_packs(upgrade, destination, expected_level_name=level_name)
        self.assertEqual(b"persistent-world-state", database.read_bytes())
        self.assertFalse((destination / "behavior_packs/demo").exists())
        self.assertTrue((destination / "behavior_packs/next/manifest.json").is_file())
        self.assertTrue((destination / "resource_packs/next/manifest.json").is_file())
        self.assertTrue(result["files"])
        self.assertEqual(64, len(result["artifact"]["sha256"]))

    def test_upgrade_overlay_rejects_name_mismatch_and_traversal(self) -> None:
        initial = self.world(filename="initial.mcworld")
        level_name, destination = extract_mcworld(initial, self.root / "data")
        mismatch = self.world(name="Different", filename="mismatch.mcworld")
        with self.assertRaisesRegex(BDSDiagnosticError, "name mismatch"):
            overlay_mcworld_packs(mismatch, destination, expected_level_name=level_name)
        unsafe = self.root / "unsafe-upgrade.mcworld"
        with zipfile.ZipFile(unsafe, "w") as archive:
            archive.writestr("levelname.txt", level_name)
            archive.writestr("behavior_packs/../../escape.txt", "no")
        with self.assertRaisesRegex(BDSDiagnosticError, "Unsafe path"):
            overlay_mcworld_packs(unsafe, destination, expected_level_name=level_name)
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
        persisted = analyze_bds_log(["runtime initialized persistent_boot=1", "runtime initialized persistent_boot=2"])
        self.assertEqual([1, 2], persisted["persistent_boot_values"])
        migrated = analyze_bds_log(["runtime initialized migration_nonempty_verified=1"])
        self.assertEqual([1], migrated["migrated_lock_values"])
        restarted = analyze_bds_log(["runtime initialized migration_state_records=1"])
        self.assertEqual([1], restarted["migrated_state_records"])
        failed = analyze_bds_log(["Server started.", "[ERROR] script failed to load"])
        self.assertFalse(failed["script_initialized"])
        self.assertFalse(failed["clean"])
        timestamped = analyze_bds_log([
            "Server started.", "runtime initialized",
            "[2026-07-22 22:53:17:568 ERROR] [Scripting] Plugin failed to create context.",
        ])
        self.assertFalse(timestamped["clean"])

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
        with self.assertRaises(OperationError) as preview_type:
            validation_ops.start_test_runtime(store, {
                "adapter": "BDS_DOCKER", "execute": True,
                "image": "registry/bds@sha256:" + "a" * 64,
                "preview_channel": "true",
            })
        self.assertEqual("INVALID_PARAMETERS", preview_type.exception.code)

    def test_restart_count_is_bounded(self) -> None:
        request = BDSRunRequest("registry/bds@sha256:" + "a" * 64, self.world(), self.root / "run", restart_count=0)
        with patch("mccompiler.runtime.bds.shutil.which", return_value="/fake/docker"):
            with self.assertRaisesRegex(BDSDiagnosticError, "restart_count"):
                from mccompiler.runtime.bds import run_bds_diagnostic
                run_bds_diagnostic(request)
        upgrade = BDSRunRequest(
            "registry/bds@sha256:" + "a" * 64, self.world(filename="upgrade-source.mcworld"),
            self.root / "upgrade-run", restart_count=1, upgrade_mcworld=self.world(filename="upgrade-target.mcworld"),
        )
        with patch("mccompiler.runtime.bds.shutil.which", return_value="/fake/docker"):
            with self.assertRaisesRegex(BDSDiagnosticError, "restart_count"):
                from mccompiler.runtime.bds import run_bds_diagnostic
                run_bds_diagnostic(upgrade)

    def test_console_probes_are_bounded_cycle_scoped_and_command_allowlisted(self) -> None:
        valid = (
            BDSConsoleProbe("open-fixture", 2, 1.0, "setblock 1 2 3 stone", "Block placed"),
            BDSConsoleProbe("verify-fixture", 2, 3.0, "testforblock 1 2 3 stone", "Successfully found"),
        )
        validate_console_probes(valid, restart_count=2, boot_grace_seconds=10)
        with self.assertRaisesRegex(BDSDiagnosticError, "disallowed command"):
            validate_console_probes(
                (BDSConsoleProbe("unsafe", 1, 1.0, "op Player", "ok"),),
                restart_count=1, boot_grace_seconds=10,
            )
        with self.assertRaisesRegex(BDSDiagnosticError, "invalid command"):
            validate_console_probes(
                (BDSConsoleProbe("newline", 1, 1.0, "setblock 1 2 3 stone\nstop", "ok"),),
                restart_count=1, boot_grace_seconds=10,
            )
        with self.assertRaisesRegex(BDSDiagnosticError, "outside the boot grace"):
            validate_console_probes(
                (BDSConsoleProbe("late", 1, 10.0, "testforblock 1 2 3 stone", "ok"),),
                restart_count=1, boot_grace_seconds=10,
            )
        with self.assertRaisesRegex(BDSDiagnosticError, "duplicate"):
            validate_console_probes(valid + (valid[0],), restart_count=2, boot_grace_seconds=10)
        with self.assertRaisesRegex(BDSDiagnosticError, "unbounded tickingarea"):
            validate_console_probes(
                (BDSConsoleProbe("large-area", 1, 1.0, "tickingarea add circle 1 2 3 10 unsafe true", "Added"),),
                restart_count=1, boot_grace_seconds=10,
            )
        validate_console_probes(
            (BDSConsoleProbe("small-area", 1, 1.0, "tickingarea add circle 1 2 3 1 safe true", "Added"),),
            restart_count=1, boot_grace_seconds=10,
        )

    def test_log_probes_are_cycle_scoped_and_classified_narrowly(self) -> None:
        valid = (BDSLogProbe(
            "simulated-action", 2, "[mccompiler:test] passed", "simulated_player_integration",
        ),)
        validate_log_probes(valid, restart_count=2)
        with self.assertRaisesRegex(BDSDiagnosticError, "invalid classification"):
            validate_log_probes(
                (BDSLogProbe("broad", 1, "passed", "gameplay"),), restart_count=1,
            )
        with self.assertRaisesRegex(BDSDiagnosticError, "invalid cycle"):
            validate_log_probes(valid, restart_count=1)

    def test_failed_cycle_cannot_emit_positive_integration_claims(self) -> None:
        console = BDSConsoleProbe("fixture", 1, 1.0, "setblock 1 2 3 stone", "Block placed")
        logged = BDSLogProbe("action", 1, "action=passed", "simulated_player_integration")
        execution = {
            "cycle": 1, "timeout_seconds": 30, "timed_out": False, "elapsed_seconds": 1.0,
            "container_exit_code": 0, "stop_exit_code": 0,
            "analysis": analyze_bds_log(["Server started.", "runtime initialized", "[ERROR] script failed"]),
            "console_probes": [{
                "check_id": "fixture", "classification": "adapter_integration",
                "command": console.command, "expect_output": console.expect_output,
                "sent": True, "matched": True, "status": "PASSED",
            }],
            "log_probes": [{
                "check_id": "action", "classification": "simulated_player_integration",
                "expect_output": logged.expect_output, "matched": True, "status": "PASSED",
            }],
            "passed": False,
        }
        request = BDSRunRequest(
            "registry/bds@sha256:" + "a" * 64, self.world(), self.root / "failed-claims",
            timeout_seconds=30, boot_grace_seconds=10,
            console_probes=(console,), log_probes=(logged,),
        )
        with patch("mccompiler.runtime.bds.shutil.which", return_value="/fake/docker"), patch(
            "mccompiler.runtime.bds._run_cycle",
            return_value=(["Server started.", "runtime initialized", "[ERROR] script failed"], execution),
        ):
            result = run_bds_diagnostic(request)
        self.assertFalse(result["passed"])
        self.assertFalse(result["claims"]["adapter_integration_verified"])
        self.assertFalse(result["claims"]["simulated_player_integration_verified"])
        self.assertFalse(result["claims"]["diagnostic_state_persistence_verified"])

    def test_public_operation_persists_narrow_boot_claims(self) -> None:
        store = ProjectStore.create(self.root / "project")
        world = store.resolve("dist/test-world/converted-test-world.mcworld")
        world.parent.mkdir(parents=True, exist_ok=True)
        world.write_bytes(self.world().read_bytes())

        def fake_run(request: BDSRunRequest) -> dict[str, object]:
            self.assertEqual("probe-one", request.console_probes[0].check_id)
            self.assertEqual("testforblock 1 2 3 stone", request.console_probes[0].command)
            request.run_root.mkdir(parents=True)
            (request.run_root / "content.log").write_text("Server started.\nruntime initialized\n")
            result: dict[str, object] = {
                "status": "BDS_DIAGNOSTIC_BOOT_VERIFIED", "passed": True,
                "runtime": {"image": request.image},
                "claims": {"bds_boot_verified": True, "diagnostic_state_persistence_verified": False, "gameplay_verified": False, "persistence_verified": False, "multiplayer_verified": False, "console_verified": False, "marketplace_approval_implied": False},
            }
            (request.run_root / "result.json").write_text(json.dumps(result))
            return result

        revision = store.revision
        with patch.object(validation_ops, "run_bds_diagnostic", side_effect=fake_run):
            response, _, artifacts = validation_ops.start_test_runtime(store, {
                "adapter": "BDS_DOCKER", "execute": True, "image": "registry/bds@sha256:" + "b" * 64,
                "console_probes": [{
                    "check_id": "probe-one", "cycle": 1, "after_boot_seconds": 1,
                    "command": "testforblock 1 2 3 stone", "expect_output": "Successfully found",
                }],
            }, revision)
        self.assertEqual(revision + 1, response["revision"])
        self.assertFalse(response["run"]["claims"]["gameplay_verified"])
        self.assertFalse(response["run"]["claims"]["console_verified"])
        self.assertEqual(4, len(artifacts))
        self.assertTrue(store.resolve("reports/bds-diagnostic-validation.json").is_file())


if __name__ == "__main__":
    unittest.main()
