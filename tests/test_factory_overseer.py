from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from bedrock_factory.activation import (
    activation_digest,
    validate_activation_package,
)
from bedrock_factory.dispatch import ThreadDispatchOutbox
from bedrock_factory.mailbox import MailboxError
from bedrock_factory.overseer import POOL_LANES, OverseerRuntime
from bedrock_factory.planner import build_factory_plan, write_factory_plan
from bedrock_factory.runtime import WorkerPool
from bedrock_factory.scaling import (
    AdaptiveScalingPolicy,
    AdaptiveThreadScaler,
    load_adaptive_scaling_config,
)
from bedrock_factory.store import (
    BLOCKED,
    QUARANTINED,
    OrchestrationStore,
)
from tools.factory.init_studio_factory import initialize_factory
from tools.factory.rehearse_studio_factory import rehearse


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FactoryOverseerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        # macOS exposes /var as a symlink to /private/var. The planner
        # intentionally rejects symlink path components, so use the canonical
        # temporary-directory spelling in this safety-focused suite.
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_planner_separates_an_archive_deterministically_without_extracting(self) -> None:
        source = self.root / "source"
        source.mkdir()
        archive = source / "example.jar"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr(
                "fabric.mod.json",
                json.dumps({"id": "example", "name": "Example Fixture"}),
            )
            bundle.writestr("fixture/Example.class", b"not-executable-bytecode")
        output = self.root / "campaign"

        first = build_factory_plan(
            source,
            output,
            inspection_authority="test-authority",
        )
        second = build_factory_plan(
            source,
            output,
            inspection_authority="test-authority",
        )
        self.assertEqual(first, second)
        self.assertEqual(len(first["intake"]["units"]), 1)
        self.assertEqual(len(first["tasks"]), 6)
        self.assertEqual(first["intake"]["units"][0]["unit_kind"], "MOD_ARCHIVE")
        self.assertFalse(first["intake"]["execution"]["archive_content_executed"])
        self.assertFalse(output.exists())

        target = write_factory_plan(
            source,
            output,
            inspection_authority="test-authority",
        )
        self.assertEqual(target, output / "factory-plan.json")
        self.assertEqual(
            target,
            write_factory_plan(
                source,
                output,
                inspection_authority="test-authority",
            ),
        )
        self.assertFalse((source / "fabric.mod.json").exists())

    def test_activation_is_mechanical_and_downstream_gates_are_delegated(self) -> None:
        repository = self.root / "production"
        repository.mkdir()
        assignment = self.root / "assignment.json"
        authority = self.root / "activation-authority.json"
        assignment.write_text('{"assignment_id":"fixture"}\n', encoding="utf-8")
        authority.write_text('{"message_id":"fixture-authority"}\n', encoding="utf-8")
        activation = {
            "schema_version": "bedrock-factory.worker-activation-package.v1.0.0",
            "activation_id": "fixture-new-pack-g1",
            "activation_type": "NEW_PACK",
            "state": "AUTHORIZED",
            "pack": {
                "pack_id": "fixture-pack",
                "assignment_id": "fixture-assignment",
                "worker_role": "feature_producer",
                "lane": "PRODUCTION",
            },
            "repository": {
                "path": str(repository),
                "ref": "refs/heads/codex/fixture-pack-g1",
                "exclusive_write_roots": [str(repository)],
            },
            "authority": {
                "assignment": {"path": str(assignment), "sha256": sha256(assignment)},
                "activation_message": {"path": str(authority), "sha256": sha256(authority)},
                "precedence": ["activation_message", "assignment", "portfolio_defaults"],
            },
            "generation": {"current": 0, "next": 1},
            "action": {
                "code": "AUTHOR_TEST_FREEZE_AND_SUBMIT",
                "maximum_new_candidates": 1,
                "completion": {"code": "CANDIDATE_SUBMITTED"},
            },
            "validation": {
                "local_commands": [
                    {"argv": [sys.executable, "-m", "pytest", "-q"], "cwd": str(repository)}
                ],
                "downstream_delegations": [
                    {
                        "gate": gate,
                        "owner": owner,
                        "required_before_publication": False,
                    }
                    for gate, owner in (
                        ("T1", "t1_preflight_tester"),
                        ("STABLE_BDS", "bds_tester"),
                        ("T10", "independent_auditor"),
                        ("T2", "t2_adapter_owner"),
                        ("INTEGRATION", "segment_integrator"),
                    )
                ],
            },
            "publication": {"freeze_required": True, "immutable_generation": 1},
            "block_policy": {
                "allowed_codes": [
                    "AUTHORITY_MISSING",
                    "REPOSITORY_IDENTITY_MISMATCH",
                    "REQUIRED_LOCAL_TOOLCHAIN_UNAVAILABLE",
                ]
            },
            "recovery": {"replacement_worker_uses_committed_state_only": True},
            "integrity": {"canonical_payload_sha256": "0" * 64},
        }
        activation["integrity"]["canonical_payload_sha256"] = activation_digest(activation)
        validate_activation_package(activation, verify_files=True)

    def test_dispatch_outbox_is_hash_bound_idempotent_and_acknowledged(self) -> None:
        assignment = self.root / "assignment.json"
        activation = self.root / "activation.json"
        assignment.write_text("{}\n", encoding="utf-8")
        activation.write_text("{}\n", encoding="utf-8")
        outbox = ThreadDispatchOutbox(self.root / "outbox")
        request = outbox.enqueue(
            campaign_id="campaign-one",
            assignment_id="assignment-one",
            role="feature_producer",
            skill="launch-cleanroom-production-worker",
            lane="PRODUCTION",
            assignment_path=assignment,
            activation_path=activation,
        )
        self.assertEqual(
            request,
            outbox.enqueue(
                campaign_id="campaign-one",
                assignment_id="assignment-one",
                role="feature_producer",
                skill="launch-cleanroom-production-worker",
                lane="PRODUCTION",
                assignment_path=assignment,
                activation_path=activation,
            ),
        )
        self.assertEqual(len(outbox.pending()), 1)
        acknowledged = outbox.acknowledge(
            request["request_id"],
            state="SENT",
            worker_task_id="task-fixture",
        )
        self.assertEqual(acknowledged["worker_task_id"], "task-fixture")
        self.assertEqual(outbox.pending(), [])
        replay = outbox.enqueue(
            campaign_id="campaign-one",
            assignment_id="assignment-one",
            role="feature_producer",
            skill="launch-cleanroom-production-worker",
            lane="PRODUCTION",
            assignment_path=assignment,
            activation_path=activation,
        )
        self.assertEqual(replay["state"], "SENT")
        self.assertEqual(outbox.pending(), [])

    def test_mailbox_preserves_rejected_generation_and_requires_exact_repair(self) -> None:
        store = OrchestrationStore(self.root / "factory.sqlite3")
        store.initialize()
        first = store.publish_candidate(
            campaign_id="campaign-one",
            pack_id="fixture-pack",
            generation=1,
            payload={"artifact": "g1"},
            idempotency_key="candidate-g1",
        )
        repair = store.append_message(
            campaign_id="campaign-one",
            pack_id="fixture-pack",
            message_type="REPAIR_REQUIRED",
            sender_role="t1_preflight_tester",
            recipient_role="feature_producer",
            candidate_generation=2,
            payload={"rejected_generation": 1, "required_generation": 2},
            idempotency_key="repair-g1",
        )
        second = store.publish_repair_candidate(
            campaign_id="campaign-one",
            pack_id="fixture-pack",
            rejected_generation=1,
            payload={"artifact": "g2", "repair_message_id": repair["message_id"]},
            idempotency_key="candidate-g2",
            source_message_id=repair["message_id"],
        )
        self.assertEqual((first["generation"], second["generation"]), (1, 2))
        with self.assertRaises(MailboxError):
            store.publish_repair_candidate(
                campaign_id="campaign-one",
                pack_id="fixture-pack",
                rejected_generation=1,
                payload={"artifact": "illegal-g2-retry"},
                idempotency_key="candidate-g2-duplicate",
            )
        self.assertEqual(len(store.list_candidates(pack_id="fixture-pack")), 2)

    def test_retry_only_reopens_descendants_of_the_repaired_job(self) -> None:
        store = OrchestrationStore(self.root / "queue.sqlite3")
        store.initialize()
        store.create_campaign(
            campaign_id="campaign-one", name="Campaign", kind="JAVA_TO_BEDROCK"
        )
        for branch in ("a", "b"):
            store.enqueue_job(
                campaign_id="campaign-one",
                job_id=f"root-{branch}",
                name=f"root-{branch}",
                stage="INVENTORY_COMPLETE",
                lane="EVIDENCE",
                kind="command",
                payload={"argv": [sys.executable, "-c", "raise SystemExit(9)"], "cwd": str(self.root)},
            )
            store.enqueue_job(
                campaign_id="campaign-one",
                job_id=f"child-{branch}",
                name=f"child-{branch}",
                stage="CONTRACT_SANITIZED",
                lane="CONTROL",
                kind="command",
                payload={"argv": [sys.executable, "-c", "pass"], "cwd": str(self.root)},
                dependencies=[f"root-{branch}"],
            )
        WorkerPool(
            store,
            runtime_root=self.root / "runtime",
            concurrency=2,
            lease_seconds=2,
            heartbeat_seconds=0.05,
        ).run()
        self.assertEqual(store.get_job("root-a")["status"], QUARANTINED)
        self.assertEqual(store.get_job("child-a")["status"], BLOCKED)
        self.assertEqual(store.get_job("child-b")["status"], BLOCKED)
        store.retry(
            "root-a",
            operator="overseer",
            reason="material repair supplied",
        )
        self.assertNotEqual(store.get_job("child-a")["status"], BLOCKED)
        self.assertEqual(store.get_job("child-b")["status"], BLOCKED)

    def test_retry_ready_transition_is_present_in_event_replay(self) -> None:
        store = OrchestrationStore(self.root / "events.sqlite3")
        store.initialize()
        store.create_campaign(
            campaign_id="campaign-one", name="Campaign", kind="JAVA_TO_BEDROCK"
        )
        marker = self.root / "marker"
        code = (
            "from pathlib import Path; import sys; "
            f"p=Path({str(marker)!r}); existed=p.exists(); p.write_text('x'); "
            "sys.exit(0 if existed else 4)"
        )
        store.enqueue_job(
            campaign_id="campaign-one",
            job_id="retry",
            name="retry",
            stage="INVENTORY_COMPLETE",
            lane="EVIDENCE",
            kind="command",
            payload={
                "argv": [sys.executable, "-c", code],
                "cwd": str(self.root),
                "retry_backoff_seconds": 0.01,
            },
            max_attempts=2,
        )
        WorkerPool(
            store,
            runtime_root=self.root / "runtime",
            concurrency=1,
            lease_seconds=2,
            heartbeat_seconds=0.05,
        ).run(idle_grace_seconds=0.1)
        event_types = [row["event_type"] for row in store.events("campaign-one")]
        self.assertIn("JOB_RETRY_READY", event_types)

    def test_overseer_runs_five_bounded_role_pools_without_a_ui(self) -> None:
        store = OrchestrationStore(self.root / "overseer.sqlite3")
        runtime = OverseerRuntime(
            store,
            runtime_root=self.root / "runtime",
            pool_concurrency={name: 1 for name in POOL_LANES},
            reconciliation_interval_seconds=0.02,
        )
        runtime.start()
        deadline = time.monotonic() + 2
        while runtime.snapshot()["reconciliation"]["cycles"] < 1:
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.01)
        self.assertTrue(runtime.stop(timeout=2))
        snapshot = runtime.snapshot()
        self.assertEqual(snapshot["state"], "STOPPED")
        self.assertEqual(set(snapshot["pools"]), set(POOL_LANES))
        self.assertTrue(all(not pool["thread_alive"] for pool in snapshot["pools"].values()))
        self.assertGreaterEqual(snapshot["adaptive_scaling"]["cycle"], 1)

    @staticmethod
    def _pressure_job(
        job_id: str,
        *,
        lane: str = "QUALIFICATION",
        status: str = "READY",
        service: str | None = "STABLE_BDS",
    ) -> dict[str, object]:
        payload: dict[str, object] = {}
        if service is not None:
            payload["qualification_gate"] = service
        return {
            "id": job_id,
            "campaign_id": "campaign-one",
            "lane": lane,
            "stage": service or lane,
            "status": status,
            "priority": 0,
            "created_at": 1.0,
            "payload": payload,
        }

    def test_adaptive_scaler_waits_two_heartbeats_then_emits_one_spawn(self) -> None:
        state = self.root / "adaptive.json"
        scaler = AdaptiveThreadScaler(state)
        job = self._pressure_job("bds-one")
        first = scaler.observe([job])
        self.assertEqual(first["open_directives"], {})
        second = scaler.observe([job])
        directives = list(second["open_directives"].values())
        self.assertEqual(len(directives), 1)
        self.assertEqual(directives[0]["action"], "SPAWN_THREAD")
        self.assertEqual(directives[0]["service"], "STABLE_BDS")
        self.assertEqual(directives[0]["wait_heartbeats"], 2)

        assigned = scaler.acknowledge(
            directives[0]["directive_id"],
            outcome="ASSIGNED",
            worker_task_id="task-bds-one",
        )
        self.assertEqual(assigned["state"], "ASSIGNED")
        replay = scaler.observe([job])
        self.assertEqual(len(replay["open_directives"]), 1)
        self.assertEqual(
            next(iter(replay["open_directives"].values()))["worker_task_id"],
            "task-bds-one",
        )

    def test_adaptive_scaler_backpressures_when_stable_bds_cap_is_full(self) -> None:
        scaler = AdaptiveThreadScaler(self.root / "adaptive.json")
        waiting = self._pressure_job("bds-waiting")
        running = [
            self._pressure_job("bds-running-one", status="RUNNING"),
            self._pressure_job("bds-running-two", status="RUNNING"),
        ]
        scaler.observe([waiting, *running])
        snapshot = scaler.observe([waiting, *running])
        directive = next(iter(snapshot["open_directives"].values()))
        self.assertEqual(directive["action"], "BACKPRESSURE_UPSTREAM")
        self.assertEqual(directive["reason"], "SERVICE_CAP_SATURATED")
        self.assertEqual(directive["capacity_used"], 2)
        self.assertEqual(directive["capacity_limit"], 2)
        self.assertEqual(directive["upstream_pools"], ["production_workers"])

    def test_adaptive_scaler_respects_actual_assigned_thread_maximum(self) -> None:
        scaler = AdaptiveThreadScaler(self.root / "adaptive.json")
        waiting = self._pressure_job(
            "audit-waiting", lane="AUDIT", service=None
        )
        assigned = {"audit_workers": 3}
        scaler.observe([waiting], assigned_threads=assigned)
        snapshot = scaler.observe([waiting], assigned_threads=assigned)
        directive = next(iter(snapshot["open_directives"].values()))
        self.assertEqual(directive["action"], "BACKPRESSURE_UPSTREAM")
        self.assertEqual(directive["reason"], "POOL_CAP_SATURATED")
        self.assertEqual(directive["capacity_used"], 3)
        self.assertEqual(directive["capacity_limit"], 3)

    def test_adaptive_scaler_restart_preserves_streak_and_ignores_dependency_wait(self) -> None:
        state = self.root / "adaptive.json"
        ordinary_wait = self._pressure_job("dependency-wait", status="WAITING")
        capacity_wait = self._pressure_job("capacity-wait", status="WAITING")
        capacity_wait["payload"]["capacity_blocked"] = True  # type: ignore[index]
        AdaptiveThreadScaler(state).observe([ordinary_wait, capacity_wait])
        replay = AdaptiveThreadScaler(state).observe([ordinary_wait, capacity_wait])
        self.assertNotIn("dependency-wait", replay["wait_streaks"])
        self.assertEqual(replay["wait_streaks"]["capacity-wait"], 2)
        self.assertEqual(len(replay["open_directives"]), 1)

    def test_adaptive_scaler_releases_only_after_idle_cooldown(self) -> None:
        policy = AdaptiveScalingPolicy(idle_heartbeats=4)
        scaler = AdaptiveThreadScaler(self.root / "adaptive.json", policy=policy)
        for _ in range(3):
            snapshot = scaler.observe([], assigned_threads={"audit_workers": 2})
            self.assertFalse(
                any(
                    item["action"] == "RELEASE_IDLE_THREAD"
                    for item in snapshot["open_directives"].values()
                )
            )
        snapshot = scaler.observe([], assigned_threads={"audit_workers": 2})
        releases = [
            item
            for item in snapshot["open_directives"].values()
            if item["action"] == "RELEASE_IDLE_THREAD"
        ]
        self.assertEqual(len(releases), 1)
        self.assertEqual(releases[0]["pool"], "audit_workers")
        self.assertEqual(releases[0]["capacity_limit"], 1)

    def test_studio_factory_bootstrap_creates_fresh_independent_mailbox(self) -> None:
        factory = self.root / "factory"
        result = initialize_factory(factory)
        config = json.loads(Path(result["config"]).read_text(encoding="utf-8"))
        mailbox = Path(config["mailbox"]["mailbox"])
        self.assertEqual(config["overseer_interface"], "CODEX_TASK")
        self.assertFalse(config["activation_allowed"])
        self.assertEqual(
            config["adaptive_scaling"]["wait_heartbeats_before_scale_up"], 2
        )
        self.assertEqual(
            config["adaptive_scaling"]["service_caps"]["STABLE_BDS"][
                "execution_slots"
            ],
            2,
        )
        enabled, policy = load_adaptive_scaling_config(result["config"])
        self.assertTrue(enabled)
        self.assertEqual(policy.wait_heartbeats, 2)
        self.assertEqual(policy.service_caps["STABLE_BDS"], 2)
        self.assertTrue((mailbox / ".git").is_dir())
        self.assertEqual(
            subprocess.run(
                ["git", "-C", str(mailbox), "remote"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "",
        )
        history = subprocess.run(
            ["git", "-C", str(mailbox), "rev-list", "--count", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(history, "1")

    def test_git_mailbox_publisher_accepts_one_parent_and_rejects_stale_parent(self) -> None:
        factory = self.root / "factory"
        result = initialize_factory(factory)
        mailbox = Path(result["mailbox"]["mailbox"])
        initial_head = result["mailbox"]["commit"]

        def message(message_id: str, idempotency_character: str) -> Path:
            path = self.root / f"{message_id}.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "message_id": message_id,
                        "message_type": "CANDIDATE_SUBMISSION",
                        "pack_id": "fixture-pack",
                        "sender_role": "fixture-worker",
                        "recipient_role": "t1-preflight",
                        "created_at": "2026-07-31T00:00:00Z",
                        "source_authority_commit": "0" * 40,
                        "source_authority_tree": "0" * 40,
                        "candidate_generation": 1,
                        "exact_artifact_hashes": {},
                        "parent_message_id": None,
                        "required_action": "RUN_T1",
                        "idempotency_key": idempotency_character * 64,
                        "proof_boundary": ["SYNTHETIC_ONLY"],
                    }
                ),
                encoding="utf-8",
            )
            return path

        first_id = "STUDIO-CANDIDATE-0001"
        first = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/factory/publish_mailbox_message.py"),
                "--mailbox",
                str(mailbox),
                "--message",
                str(message(first_id, "1")),
                "--target",
                f"candidate_submissions/fixture-pack/{first_id}.json",
                "--expected-head",
                initial_head,
                "--actor",
                "Factory Test",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        published = json.loads(first.stdout)
        self.assertEqual(published["parent"], initial_head)

        second_id = "STUDIO-CANDIDATE-0002"
        stale = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/factory/publish_mailbox_message.py"),
                "--mailbox",
                str(mailbox),
                "--message",
                str(message(second_id, "2")),
                "--target",
                f"candidate_submissions/fixture-pack/{second_id}.json",
                "--expected-head",
                initial_head,
                "--actor",
                "Factory Test",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(stale.returncode, 0)
        self.assertIn("stale expected head", stale.stderr)
        self.assertFalse(
            (mailbox / f"candidate_submissions/fixture-pack/{second_id}.json").exists()
        )
        self.assertEqual(
            subprocess.run(
                ["git", "-C", str(mailbox), "status", "--porcelain"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout,
            "",
        )

    def test_synthetic_rehearsal_closes_one_repair_loop_and_is_replay_safe(self) -> None:
        factory = self.root / "factory"
        initialize_factory(factory)
        source = self.root / "synthetic-source.jar"
        with zipfile.ZipFile(source, "w") as bundle:
            bundle.writestr(
                "fabric.mod.json",
                json.dumps({"id": "synthetic", "name": "Synthetic"}),
            )
            bundle.writestr("fixture/Synthetic.class", b"synthetic-bytecode")
        first = rehearse(factory, source)
        second = rehearse(factory, source)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "PASS")
        self.assertEqual(first["candidate_generations"], [1, 2])
        self.assertEqual(first["dispatch_state"], "ACKNOWLEDGED")
        config = json.loads((factory / "factory-config.json").read_text(encoding="utf-8"))
        self.assertTrue(config["activation_allowed"])
        self.assertEqual(config["overseer_interface"], "CODEX_TASK")


if __name__ == "__main__":
    unittest.main()
