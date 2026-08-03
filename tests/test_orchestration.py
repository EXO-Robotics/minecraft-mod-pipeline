from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bedrock_factory.campaign import (
    CampaignDefinitionError,
    load_campaign_definition,
    validate_campaign_definition,
)
from bedrock_factory.executor import file_sha256
from bedrock_factory.runtime import WorkerPool
from bedrock_factory.store import (
    AWAITING_APPROVAL,
    BLOCKED,
    QUARANTINED,
    READY,
    RETRY_WAIT,
    RUNNING,
    SUCCEEDED,
    OrchestrationStore,
)
from tools.render_orchestrator_launchd import render_launch_agent


class OrchestrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = OrchestrationStore(self.root / "queue.sqlite3")
        self.store.initialize()
        self.store.create_campaign(
            campaign_id="test-campaign",
            name="Test campaign",
            kind="JAVA_TO_BEDROCK",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def enqueue_command(
        self,
        job_id: str,
        code: str,
        *,
        dependencies: list[str] | None = None,
        max_attempts: int = 1,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        command_payload: dict[str, object] = {
            "argv": [sys.executable, "-c", code],
            "cwd": str(self.root),
            "timeout_seconds": 5,
            "retry_backoff_seconds": 0.01,
        }
        command_payload.update(payload or {})
        return self.store.enqueue_job(
            campaign_id="test-campaign",
            job_id=job_id,
            name=job_id,
            stage="INVENTORY_COMPLETE",
            lane="EVIDENCE",
            kind="command",
            payload=command_payload,
            dependencies=dependencies,
            max_attempts=max_attempts,
        )

    def worker_pool(self, concurrency: int = 2) -> WorkerPool:
        return WorkerPool(
            self.store,
            runtime_root=self.root / "runtime",
            concurrency=concurrency,
            lease_seconds=2,
            heartbeat_seconds=0.05,
        )

    def test_dependency_graph_and_manual_gate(self) -> None:
        first_output = self.root / "first.txt"
        second_output = self.root / "second.txt"
        self.enqueue_command(
            "scan-java",
            f"from pathlib import Path; Path({str(first_output)!r}).write_text('scan')",
            payload={
                "expected_outputs": [{"path": str(first_output)}],
                "allowed_write_roots": [str(self.root)],
            },
        )
        self.store.enqueue_job(
            campaign_id="test-campaign",
            job_id="approve-contract",
            name="Approve sanitized contract",
            stage="CONTRACT_SANITIZED",
            lane="CONTROL",
            kind="manual_gate",
            payload={},
            dependencies=["scan-java"],
        )
        self.enqueue_command(
            "compile-bedrock",
            f"from pathlib import Path; Path({str(second_output)!r}).write_text('pack')",
            dependencies=["approve-contract"],
            payload={
                "expected_outputs": [{"path": str(second_output)}],
                "allowed_write_roots": [str(self.root)],
            },
        )

        counts = self.worker_pool().run()
        self.assertEqual(counts[SUCCEEDED], 1)
        self.assertEqual(self.store.get_job("approve-contract")["status"], AWAITING_APPROVAL)
        self.assertEqual(self.store.get_job("compile-bedrock")["status"], "WAITING")
        self.assertFalse(second_output.exists())

        self.store.approve(
            "approve-contract",
            operator="test-operator",
            reason="sanitization receipt reviewed",
        )
        approval = self.store.get_job("approve-contract")
        self.assertEqual(
            file_sha256(Path(approval["receipt_path"])),
            approval["receipt_sha256"],
        )
        counts = self.worker_pool().run()
        self.assertEqual(counts[SUCCEEDED], 3)
        self.assertEqual(second_output.read_text(), "pack")

    def test_parallel_workers_overlap(self) -> None:
        first = self.root / "first-timing.json"
        second = self.root / "second-timing.json"
        code = (
            "import json,os,time; from pathlib import Path; "
            "start=time.time(); time.sleep(0.35); "
            "Path(os.environ['OUTPUT']).write_text("
            "json.dumps({'start':start,'end':time.time()}))"
        )
        for job_id, output in (("parallel-one", first), ("parallel-two", second)):
            self.enqueue_command(
                job_id,
                code,
                payload={
                    "env": {"OUTPUT": str(output)},
                    "expected_outputs": [{"path": str(output)}],
                    "allowed_write_roots": [str(self.root)],
                },
            )
        counts = self.worker_pool(concurrency=2).run()
        self.assertEqual(counts[SUCCEEDED], 2)
        windows = [json.loads(first.read_text()), json.loads(second.read_text())]
        latest_start = max(window["start"] for window in windows)
        earliest_end = min(window["end"] for window in windows)
        self.assertLess(latest_start, earliest_end)

    def test_bounded_retry_succeeds_on_second_attempt(self) -> None:
        marker = self.root / "attempted"
        output = self.root / "retry-output.txt"
        code = (
            "import sys; from pathlib import Path; "
            f"marker=Path({str(marker)!r}); output=Path({str(output)!r}); "
            "exists=marker.exists(); marker.write_text('attempted'); "
            "output.write_text('recovered') if exists else None; "
            "sys.exit(0 if exists else 7)"
        )
        self.enqueue_command(
            "retry-job",
            code,
            max_attempts=2,
            payload={
                "expected_outputs": [{"path": str(output)}],
                "allowed_write_roots": [str(self.root)],
            },
        )
        counts = self.worker_pool(concurrency=1).run(idle_grace_seconds=0.2)
        job = self.store.get_job("retry-job")
        self.assertEqual(counts[SUCCEEDED], 1)
        self.assertEqual(job["attempt_count"], 2)
        self.assertEqual(output.read_text(), "recovered")

    def test_expired_lease_is_recovered(self) -> None:
        self.enqueue_command("leased-job", "pass", max_attempts=2)
        claimed = self.store.claim(
            worker_id="dead-worker",
            lease_seconds=0.01,
        )
        self.assertIsNotNone(claimed)
        self.assertEqual(self.store.get_job("leased-job")["status"], RUNNING)
        time.sleep(0.03)
        self.store.refresh()
        self.assertEqual(self.store.get_job("leased-job")["status"], RETRY_WAIT)
        time.sleep(0.02)
        self.store.refresh()
        self.assertEqual(self.store.get_job("leased-job")["status"], READY)
        self.worker_pool(concurrency=1).run()
        self.assertEqual(self.store.get_job("leased-job")["status"], SUCCEEDED)

    def test_verified_transfer_is_atomic_and_idempotent(self) -> None:
        source = self.root / "source.bin"
        destination = self.root / "delivered" / "candidate.bin"
        source.write_bytes(b"candidate-bytes")
        expected_hash = file_sha256(source)
        self.store.enqueue_job(
            campaign_id="test-campaign",
            job_id="transfer-candidate",
            name="Transfer candidate",
            stage="INTEGRATED",
            lane="INTEGRATION",
            kind="transfer",
            payload={
                "transport": "local",
                "source": str(source),
                "destination": str(destination),
                "sha256": expected_hash,
                "allowed_read_roots": [str(self.root)],
                "allowed_write_roots": [str(self.root)],
            },
            max_attempts=2,
        )
        self.worker_pool(concurrency=1).run()
        job = self.store.get_job("transfer-candidate")
        self.assertEqual(job["status"], SUCCEEDED)
        self.assertEqual(file_sha256(destination), expected_hash)
        self.assertEqual(list((destination.parent / ".mccompiler-incoming").iterdir()), [])

    def test_failure_quarantines_and_blocks_dependents(self) -> None:
        self.enqueue_command("broken-job", "raise SystemExit(9)")
        self.enqueue_command(
            "dependent-job",
            "pass",
            dependencies=["broken-job"],
        )
        self.worker_pool(concurrency=1).run()
        self.assertEqual(self.store.get_job("broken-job")["status"], QUARANTINED)
        self.assertEqual(self.store.get_job("dependent-job")["status"], BLOCKED)

    def test_operator_retry_preserves_attempt_history(self) -> None:
        marker = self.root / "repair-present"
        code = (
            "import sys; from pathlib import Path; "
            f"sys.exit(0 if Path({str(marker)!r}).exists() else 4)"
        )
        self.enqueue_command("repairable-job", code)
        self.worker_pool(concurrency=1).run()
        first = self.store.get_job("repairable-job")
        first_receipt = Path(first["receipt_path"])
        self.assertEqual(first["attempt_count"], 1)
        self.assertTrue(first_receipt.is_file())
        marker.write_text("material repair", encoding="utf-8")
        self.store.retry(
            "repairable-job",
            operator="test-operator",
            reason="material test fixture repair",
            additional_attempts=1,
        )
        self.worker_pool(concurrency=1).run()
        repaired = self.store.get_job("repairable-job")
        self.assertEqual(repaired["status"], SUCCEEDED)
        self.assertEqual(repaired["attempt_count"], 2)
        self.assertTrue(first_receipt.is_file())
        self.assertNotEqual(first_receipt, Path(repaired["receipt_path"]))

    def test_campaign_definition_rejects_unsandboxed_production_command(self) -> None:
        definition = {
            "schema_version": "1.0.0",
            "campaign_id": "unsafe-campaign",
            "name": "Unsafe",
            "kind": "JAVA_TO_BEDROCK",
            "jobs": [
                {
                    "id": "production-job",
                    "name": "Production",
                    "stage": "PRODUCTION_ACTIVE",
                    "lane": "PRODUCTION",
                    "kind": "command",
                    "payload": {"argv": ["true"]},
                }
            ],
        }
        with self.assertRaisesRegex(CampaignDefinitionError, "sandbox_profile"):
            validate_campaign_definition(definition)

    def test_runtime_rejects_direct_unsandboxed_production_command(self) -> None:
        self.store.enqueue_job(
            campaign_id="test-campaign",
            job_id="unsafe-direct-production",
            name="Unsafe direct production",
            stage="PRODUCTION_ACTIVE",
            lane="PRODUCTION",
            kind="command",
            payload={
                "argv": [sys.executable, "-c", "pass"],
                "cwd": str(self.root),
            },
        )
        self.worker_pool(concurrency=1).run()
        job = self.store.get_job("unsafe-direct-production")
        self.assertEqual(job["status"], QUARANTINED)
        self.assertIn("hash-bound sandbox profile", job["last_error"])

    def test_sandboxed_production_records_minimal_activation_attestation(self) -> None:
        profile = self.root / "production.sb"
        profile.write_text("(version 1)\n(deny default)\n", encoding="utf-8")
        activation_attestation = self.root / "activation-attestation.json"
        attestation = {
            "schema_version": "bedrock-factory.activation-attestation.v1.0.0",
            "activation_id": "A1",
            "assignment_sha256": "a" * 64,
            "platform_qualification_sha256": "b" * 64,
            "repository_ref": "refs/heads/codex/test",
            "exit_code": 0,
            "cleanup_status": "PASS",
        }
        code = (
            "import json; from pathlib import Path; "
            f"Path({str(activation_attestation)!r}).write_text("
            f"json.dumps({attestation!r}))"
        )
        self.store.enqueue_job(
            campaign_id="test-campaign",
            job_id="sandboxed-production",
            name="Sandboxed production",
            stage="PRODUCTION_ACTIVE",
            lane="PRODUCTION",
            kind="command",
            payload={
                "argv": [sys.executable, "-c", code],
                "cwd": str(self.root),
                "allowed_read_roots": [str(self.root)],
                "allowed_write_roots": [str(self.root)],
                "sandbox_profile": {
                    "path": str(profile),
                    "sha256": file_sha256(profile),
                },
                "activation_attestation_required": True,
                "activation_attestation": {"path": str(activation_attestation)},
            },
        )
        self.worker_pool(concurrency=1).run()
        job = self.store.get_job("sandboxed-production")
        self.assertEqual(job["status"], SUCCEEDED)
        self.assertEqual(
            job["result"]["activation_attestation"]["sha256"],
            file_sha256(activation_attestation),
        )

    def test_generated_profile_mode_binds_studio_launcher(self) -> None:
        launcher = self.root / "studio-launcher.py"
        launcher.write_text("print('launcher')", encoding="utf-8")
        definition = {
            "schema_version": "1.0.0",
            "campaign_id": "studio-launcher-campaign",
            "name": "Studio launcher",
            "kind": "JAVA_TO_BEDROCK",
            "jobs": [
                {
                    "id": "studio-production",
                    "name": "Studio production",
                    "stage": "PRODUCTION_ACTIVE",
                    "lane": "PRODUCTION",
                    "kind": "command",
                    "payload": {
                        "argv": [sys.executable, str(launcher)],
                        "sandbox_profile": {
                            "mode": "generated_by_launcher",
                            "launcher_path": str(launcher),
                            "launcher_sha256": file_sha256(launcher),
                        },
                        "activation_attestation_required": True,
                        "activation_attestation": {
                            "path": str(self.root / "activation-attestation.json"),
                        },
                    },
                }
            ],
        }
        validate_campaign_definition(definition)

    def test_load_campaign_definition_is_idempotency_bound(self) -> None:
        definition = {
            "schema_version": "1.0.0",
            "campaign_id": "loaded-campaign",
            "name": "Loaded",
            "kind": "JAVA_TO_BEDROCK",
            "jobs": [
                {
                    "id": "rights-gate",
                    "name": "Rights authorization",
                    "stage": "RIGHTS_AUTHORIZED",
                    "lane": "CONTROL",
                    "kind": "manual_gate",
                    "payload": {},
                }
            ],
        }
        path = self.root / "campaign.json"
        path.write_text(json.dumps(definition), encoding="utf-8")
        loaded_store = OrchestrationStore(self.root / "loaded.sqlite3")
        result = load_campaign_definition(path, loaded_store)
        self.assertEqual(result["campaign"]["id"], "loaded-campaign")
        self.assertEqual(result["jobs"][0]["status"], AWAITING_APPROVAL)
        replay = load_campaign_definition(path, loaded_store)
        self.assertEqual(replay["campaign"]["id"], "loaded-campaign")
        self.assertEqual(len(replay["jobs"]), 1)

    def test_launchd_agent_runs_forever_from_repository_environment(self) -> None:
        payload = render_launch_agent(
            repository=ROOT,
            database=self.root / "queue.sqlite3",
            runtime_root=self.root / "runtime",
            concurrency=4,
            lanes=["EVIDENCE", "CONTROL"],
        )
        arguments = payload["ProgramArguments"]
        self.assertEqual(arguments[0], str(ROOT / ".venv/bin/bedrock-factory"))
        self.assertIn("--forever", arguments)
        self.assertEqual(arguments.count("--lane"), 2)
        self.assertTrue(payload["KeepAlive"])


if __name__ == "__main__":
    unittest.main()
