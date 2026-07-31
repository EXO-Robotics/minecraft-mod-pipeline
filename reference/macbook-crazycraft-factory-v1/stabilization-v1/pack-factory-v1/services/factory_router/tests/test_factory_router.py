from __future__ import annotations

import contextlib
import fcntl
import importlib.util
import json
import os
import plistlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "factory_router", ROOT / "factory_router.py"
)
router = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(router)


def git(repository: Path, *args: str) -> str:
    return subprocess.run(
        ["/usr/bin/git", "-C", str(repository), *args],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def message(message_id: str, generation: int = 1, key: str = "a" * 64) -> dict:
    return {
        "schema_version": "1.0.0",
        "message_id": message_id,
        "message_type": "CANDIDATE_SUBMISSION",
        "pack_id": "fixture-pack",
        "sender_role": "PACK-WORKER",
        "recipient_role": "PACK-TESTER",
        "created_at": "2026-07-30T00:00:00Z",
        "source_authority_commit": "b" * 40,
        "source_authority_tree": "c" * 40,
        "candidate_generation": generation,
        "exact_artifact_hashes": {"mcaddon": "d" * 64},
        "parent_message_id": None,
        "required_action": "MECHANICAL_PREFLIGHT",
        "idempotency_key": key,
        "proof_boundary": ["STATIC_ONLY"],
    }


class FactoryRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.mailbox = self.base / "mailbox"
        self.runtime = self.base / "runtime"
        self.mailbox.mkdir()
        git(self.mailbox, "init", "-q")
        git(self.mailbox, "config", "user.name", "Fixture")
        git(self.mailbox, "config", "user.email", "fixture@example.invalid")
        (self.mailbox / ".gitignore").write_text(".runtime/\n", encoding="utf-8")
        git(self.mailbox, "add", ".gitignore")
        git(self.mailbox, "commit", "-qm", "baseline")
        self.baseline = git(self.mailbox, "rev-parse", "HEAD")
        self.mailbox_ref = git(self.mailbox, "symbolic-ref", "HEAD")
        self.config_path = self.base / "config.json"
        self.tester_state = self.base / "tester-state.json"
        self.compatibility_ledger = self.base / "compatibility-ledger.json"
        write_json(self.tester_state, {"jobs": {}})
        write_json(
            self.compatibility_ledger,
            {
                "schema_version": "crazycraft-router-compatibility-v1",
                "entries": [],
            },
        )
        self.config = {
            "schema_version": "crazycraft-factory-router-v1",
            "mailbox_repository": str(self.mailbox),
            "mailbox_ref": self.mailbox_ref,
            "initial_consumed_mailbox_commit": self.baseline,
            "runtime_root": str(self.runtime),
            "publisher": str(ROOT.parent.parent / "tools/publish_mailbox_message.py"),
            "local_tester_state": str(self.tester_state),
            "compatibility_ledger": str(self.compatibility_ledger),
            "compatibility_ledger_expected_entries": 0,
            "poll_interval_seconds": 120,
            "max_tester_active": 2,
            "max_t10_active": 1,
            "max_t10_queued": 1,
            "allowed_tester_sender_roles": ["PERSISTENT_TESTER"],
            "allowed_t10_sender_roles": ["T10_INDEPENDENT_AUDIT_SERVICE"],
            "initial_t10_projection": {
                "active": None,
                "queued": None,
                "audit_backlog": [],
            },
            "allowed_message_roots": sorted(router.MESSAGE_ROOTS),
        }
        write_json(self.config_path, self.config)

    def commit_message(self, value: dict) -> str:
        return self.commit_mailbox_message(value, "candidate_submissions")

    def commit_mailbox_message(self, value: dict, root: str) -> str:
        path = self.mailbox / root / value["pack_id"] / f"{value['message_id']}.json"
        write_json(path, value)
        git(self.mailbox, "add", path.relative_to(self.mailbox).as_posix())
        git(self.mailbox, "commit", "-qm", value["message_id"])
        return git(self.mailbox, "rev-parse", "HEAD")

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "factory_router.py"),
                "--config",
                str(self.config_path),
                *args,
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_01_config_requires_exact_120_second_interval(self):
        config = dict(self.config)
        config["poll_interval_seconds"] = 30
        write_json(self.config_path, config)
        with self.assertRaises(router.RouterError):
            router.config_from(self.config_path)

    def test_02_noop_is_silent_and_does_not_commit(self):
        before = git(self.mailbox, "rev-parse", "HEAD")
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(git(self.mailbox, "rev-parse", "HEAD"), before)
        state = json.loads((self.runtime / "routing_state.json").read_text())
        self.assertEqual(state["last_consumed_mailbox_commit"], before)
        self.assertEqual(state["unseen_message_count"], 0)

    def test_03_nonblocking_singleton_skips_cycle_silently(self):
        self.runtime.mkdir(parents=True)
        lock_path = self.runtime / "routing-cycle.lock"
        with lock_path.open("a+") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse((self.runtime / "routing_state.json").exists())

    def test_04_discovers_and_consumes_append_only_candidate(self):
        head = self.commit_message(message("MSG-FIXTURE-CANDIDATE-000001"))
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads((self.runtime / "routing_state.json").read_text())
        self.assertEqual(state["last_consumed_mailbox_commit"], head)
        self.assertEqual(len(state["active_preflight"]), 1)
        self.assertEqual(
            state["active_preflight"][0]["message_id"],
            "MSG-FIXTURE-CANDIDATE-000001",
        )
        self.assertEqual(
            state["pending_semantic_actions"][0]["action_type"],
            "RUN_MECHANICAL_PREFLIGHT",
        )

    def test_05_duplicate_candidate_identity_is_deduplicated(self):
        self.commit_message(message("MSG-FIXTURE-CANDIDATE-000001", key="1" * 64))
        first = self.run_cli("--run-once")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.commit_message(message("MSG-FIXTURE-CANDIDATE-000002", key="2" * 64))
        second = self.run_cli("--run-once")
        self.assertEqual(second.returncode, 0, second.stderr)
        state = json.loads((self.runtime / "routing_state.json").read_text())
        self.assertEqual(len(state["active_preflight"]), 1)
        self.assertEqual(
            state["duplicate_observations"][-1]["reason"],
            "CANDIDATE_IDENTITY_ALREADY_OBSERVED",
        )

    def test_06_stale_or_unknown_cursor_fails_closed(self):
        config = dict(self.config)
        config["initial_consumed_mailbox_commit"] = "f" * 40
        write_json(self.config_path, config)
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cursor does not exist", result.stderr)

    def test_07_rewritten_message_history_fails_closed(self):
        self.commit_message(message("MSG-FIXTURE-CANDIDATE-000001"))
        self.run_cli("--run-once")
        path = (
            self.mailbox
            / "candidate_submissions/fixture-pack/MSG-FIXTURE-CANDIDATE-000001.json"
        )
        path.unlink()
        git(self.mailbox, "add", "-u")
        git(self.mailbox, "commit", "-qm", "delete message")
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not append-only", result.stderr)

    def test_08_runtime_contains_all_required_fields(self):
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads((self.runtime / "routing_state.json").read_text())
        self.assertTrue(router.REQUIRED_RUNTIME_FIELDS <= state.keys())

    def test_09_status_is_the_only_success_mode_that_prints(self):
        self.run_cli("--run-once")
        result = self.run_cli("--status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("last_consumed_mailbox_commit", result.stdout)

    def test_10_launchd_is_one_shot_at_120_seconds(self):
        with (ROOT / "com.crazycraft.factory-router.plist").open("rb") as handle:
            plist = plistlib.load(handle)
        self.assertEqual(plist["Label"], "com.crazycraft.factory-router")
        self.assertEqual(plist["StartInterval"], 120)
        self.assertNotIn("KeepAlive", plist)
        self.assertIn("--run-once", plist["ProgramArguments"])

    def test_11_no_product_worker_dispatch_surface_exists(self):
        source = (ROOT / "factory_router.py").read_text(encoding="utf-8")
        self.assertNotIn("codex exec", source)
        self.assertNotIn("dispatch_worker", source)
        self.assertNotIn("Popen(", source)

    def test_12_runtime_is_ignored(self):
        ignore = (ROOT / "runtime/.gitignore").read_text(encoding="utf-8")
        self.assertEqual(ignore, "*\n!.gitignore\n")

    def test_13_t10_result_frees_active_but_does_not_mutate_queue(self):
        config = router.config_from(self.config_path)
        state = router.initial_state(config)
        state["t10_active"] = {
            "pack_id": "fixture-pack",
            "candidate_generation": 1,
        }
        state["t10_queued"] = {"pack_id": "next-pack", "candidate_generation": 2}
        value = message("MSG-T10-FIXTURE-AUDIT-000001")
        value.update(
            {
                "message_type": "TEST_FAIL_PRODUCT",
                "sender_role": "T10_INDEPENDENT_AUDIT_SERVICE",
                "recipient_role": "T1_PORTFOLIO_SUPERVISOR",
            }
        )
        raw = router.canonical_bytes(value) + b"\n"
        record = router.validate_message(
            raw,
            "tester_results/fixture-pack/MSG-T10-FIXTURE-AUDIT-000001.json",
            "e" * 40,
        )
        router.consume_record(state, record, config)
        self.assertIsNone(state["t10_active"])
        self.assertEqual(state["t10_queued"]["pack_id"], "next-pack")
        actions = {item["action_type"] for item in state["pending_semantic_actions"]}
        self.assertNotIn("PROMOTE_T10_QUEUED", actions)
        self.assertIn("PUBLISH_CONSOLIDATED_OWNER_REPAIR", actions)

    def test_14_unauthorized_result_sender_fails_closed(self):
        config = router.config_from(self.config_path)
        state = router.initial_state(config)
        value = message("MSG-ROGUE-RESULT-000001")
        value.update(
            {
                "message_type": "TEST_PASS",
                "sender_role": "UNAUTHORIZED_RESULT_WRITER",
                "recipient_role": "T1_PORTFOLIO_SUPERVISOR",
            }
        )
        raw = router.canonical_bytes(value) + b"\n"
        record = router.validate_message(
            raw,
            "tester_results/fixture-pack/MSG-ROGUE-RESULT-000001.json",
            "e" * 40,
        )
        with self.assertRaises(router.RouterError):
            router.consume_record(state, record, config)

    def test_15_consumed_candidate_remains_durably_routable(self):
        head = self.commit_message(message("MSG-FIXTURE-CANDIDATE-000001"))
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads((self.runtime / "routing_state.json").read_text())
        self.assertEqual(state["last_consumed_mailbox_commit"], head)
        action = state["pending_semantic_actions"][0]
        self.assertEqual(action["source_mailbox_commit"], head)
        self.assertEqual(action["state"], "AWAITING_EXACT_PREPARED_SEMANTIC_INPUT")
        second = self.run_cli("--run-once")
        self.assertEqual(second.returncode, 0, second.stderr)
        preserved = json.loads((self.runtime / "routing_state.json").read_text())
        self.assertEqual(preserved["pending_semantic_actions"], state["pending_semantic_actions"])

    def test_16_semantic_publisher_rejects_unprepared_or_forbidden_content(self):
        config = router.config_from(self.config_path)
        message_path = self.base / "unprepared.json"
        write_json(message_path, message("MSG-FIXTURE-CANDIDATE-000001"))
        with self.assertRaises(router.RouterError):
            router.publish_semantic_message(
                config,
                message_path=message_path,
                target=(
                    "candidate_submissions/fixture-pack/"
                    "MSG-FIXTURE-CANDIDATE-000001.json"
                ),
                expected_head=self.baseline,
                actor="PACK-WORKER",
            )

    def test_17_established_audit_slot_moves_queued_candidate_to_active(self):
        config = router.config_from(self.config_path)
        state = router.initial_state(config)
        state["t10_active"] = None
        state["t10_queued"] = {
            "pack_id": "fixture-pack",
            "candidate_generation": 1,
        }
        state["audit_backlog"] = [
            {"pack_id": "fixture-pack", "candidate_generation": 1}
        ]
        value = message("MSG-T01-FIXTURE-AUDIT-PROMOTION-000001")
        value.update(
            {
                "message_type": "AUDIT_INTAKE",
                "sender_role": "T1_PORTFOLIO_SUPERVISOR",
                "recipient_role": "T10_INDEPENDENT_AUDIT_SERVICE",
                "audit_slot": "ACTIVE",
            }
        )
        raw = router.canonical_bytes(value) + b"\n"
        record = router.validate_message(
            raw,
            "integration_intake/fixture-pack/"
            "MSG-T01-FIXTURE-AUDIT-PROMOTION-000001.json",
            "e" * 40,
        )
        router.consume_record(state, record, config)
        self.assertEqual(state["t10_active"]["pack_id"], "fixture-pack")
        self.assertIsNone(state["t10_queued"])
        self.assertEqual(state["audit_backlog"], [])

    def test_18_committed_route_resolves_candidate_preflight_action(self):
        config = router.config_from(self.config_path)
        state = router.initial_state(config)
        candidate = message("MSG-FIXTURE-CANDIDATE-000001")
        candidate_record = router.validate_message(
            router.canonical_bytes(candidate) + b"\n",
            "candidate_submissions/fixture-pack/"
            "MSG-FIXTURE-CANDIDATE-000001.json",
            "d" * 40,
        )
        router.consume_record(state, candidate_record, config)
        intake = message("MSG-T01-FIXTURE-BDS-000001", key="f" * 64)
        intake.update(
            {
                "message_type": "TESTER_INTAKE",
                "sender_role": "T1_PORTFOLIO_SUPERVISOR",
                "recipient_role": "PERSISTENT_TESTER",
                "parent_message_id": "MSG-FIXTURE-CANDIDATE-000001",
            }
        )
        intake_record = router.validate_message(
            router.canonical_bytes(intake) + b"\n",
            "tester_intake/fixture-pack/MSG-T01-FIXTURE-BDS-000001.json",
            "e" * 40,
        )
        router.consume_record(state, intake_record, config)
        self.assertEqual(state["active_preflight"], [])
        self.assertFalse(
            any(
                item["action_type"] == "RUN_MECHANICAL_PREFLIGHT"
                for item in state["pending_semantic_actions"]
            )
        )

    def test_19_repair_projection_is_single_and_replacement_supersedes_it(self):
        config = router.config_from(self.config_path)
        state = router.initial_state(config)
        failed = message("MSG-T10-FIXTURE-AUDIT-000002")
        failed.update(
            {
                "message_type": "TEST_FAIL_PRODUCT",
                "sender_role": "T10_INDEPENDENT_AUDIT_SERVICE",
                "recipient_role": "T1_PORTFOLIO_SUPERVISOR",
                "findings": [
                    {
                        "finding_id": "F-001",
                        "allowed_repair_scope": ["runtime only"],
                        "required_regression_gates": ["GATE-001"],
                    }
                ],
            }
        )
        state["t10_active"] = {
            "pack_id": "fixture-pack",
            "candidate_generation": 1,
        }
        failed_record = router.validate_message(
            router.canonical_bytes(failed) + b"\n",
            "tester_results/fixture-pack/MSG-T10-FIXTURE-AUDIT-000002.json",
            "d" * 40,
        )
        router.consume_record(state, failed_record, config)
        self.assertEqual(
            state["repair_messages_pending"][0]["repair_state"],
            "RESULT_AWAITING_ROUTING",
        )
        repair = message("MSG-T1R-FIXTURE-OWNER-REPAIR-000001", key="2" * 64)
        repair.update(
            {
                "message_type": "REPAIR_INSTRUCTION",
                "sender_role": "T1_FACTORY_ROUTER",
                "recipient_role": "PACK-WORKER",
                "parent_message_id": failed["message_id"],
                "required_replacement_generation": 2,
            }
        )
        repair_record = router.validate_message(
            router.canonical_bytes(repair) + b"\n",
            "worker_repairs/fixture-pack/"
            "MSG-T1R-FIXTURE-OWNER-REPAIR-000001.json",
            "e" * 40,
        )
        router.consume_record(state, repair_record, config)
        self.assertEqual(len(state["repair_messages_pending"]), 1)
        self.assertEqual(
            state["repair_messages_pending"][0]["repair_state"],
            "OWNER_REPLACEMENT_PENDING",
        )
        replacement = message(
            "MSG-FIXTURE-CANDIDATE-000002", generation=2, key="3" * 64
        )
        replacement_record = router.validate_message(
            router.canonical_bytes(replacement) + b"\n",
            "candidate_submissions/fixture-pack/"
            "MSG-FIXTURE-CANDIDATE-000002.json",
            "f" * 40,
        )
        router.consume_record(state, replacement_record, config)
        self.assertEqual(state["repair_messages_pending"], [])
        self.assertEqual(
            state["repair_state_history"][-1]["repair_state"],
            "SUPERSEDED_BY_REPLACEMENT",
        )

    def test_20_mechanical_fail_routes_only_to_owner_repair(self):
        config = router.config_from(self.config_path)
        state = router.initial_state(config)
        candidate = message("MSG-FIXTURE-CANDIDATE-000001")
        candidate_record = router.validate_message(
            router.canonical_bytes(candidate) + b"\n",
            "candidate_submissions/fixture-pack/"
            "MSG-FIXTURE-CANDIDATE-000001.json",
            "d" * 40,
        )
        router.consume_record(state, candidate_record, config)
        result = message("MSG-T01-FIXTURE-PREFLIGHT-FAIL-000001", key="4" * 64)
        result.update(
            {
                "message_type": "MECHANICAL_PREFLIGHT_RESULT",
                "sender_role": "T1_MECHANICAL_PREFLIGHT",
                "recipient_role": "T1_FACTORY_ROUTER",
                "parent_message_id": candidate["message_id"],
                "mechanical_status": "FAIL",
                "findings": [{"finding_id": "MECH-001"}],
            }
        )
        record = router.validate_message(
            router.canonical_bytes(result) + b"\n",
            "final_decisions/fixture-pack/"
            "MSG-T01-FIXTURE-PREFLIGHT-FAIL-000001.json",
            "e" * 40,
        )
        router.consume_record(state, record, config)
        actions = {item["action_type"] for item in state["pending_semantic_actions"]}
        self.assertEqual(actions, {"PUBLISH_CONSOLIDATED_OWNER_REPAIR"})
        self.assertIsNone(state["t10_active"])
        self.assertIsNone(state["t10_queued"])

    def test_21_mechanical_pass_routes_tester_and_audit_backlog(self):
        config = router.config_from(self.config_path)
        state = router.initial_state(config)
        candidate = message("MSG-FIXTURE-CANDIDATE-000001")
        candidate_record = router.validate_message(
            router.canonical_bytes(candidate) + b"\n",
            "candidate_submissions/fixture-pack/"
            "MSG-FIXTURE-CANDIDATE-000001.json",
            "d" * 40,
        )
        router.consume_record(state, candidate_record, config)
        result = message("MSG-T01-FIXTURE-PREFLIGHT-PASS-000001", key="5" * 64)
        result.update(
            {
                "message_type": "MECHANICAL_PREFLIGHT_RESULT",
                "sender_role": "T1_MECHANICAL_PREFLIGHT",
                "recipient_role": "T1_FACTORY_ROUTER",
                "parent_message_id": candidate["message_id"],
                "mechanical_status": "PASS",
            }
        )
        record = router.validate_message(
            router.canonical_bytes(result) + b"\n",
            "final_decisions/fixture-pack/"
            "MSG-T01-FIXTURE-PREFLIGHT-PASS-000001.json",
            "e" * 40,
        )
        router.consume_record(state, record, config)
        actions = {item["action_type"] for item in state["pending_semantic_actions"]}
        self.assertEqual(
            actions, {"ROUTE_MECHANICALLY_ADMITTED_CANDIDATE_TO_TESTER"}
        )
        self.assertEqual(state["audit_backlog"][0]["source_message_id"], result["message_id"])

    def test_22_capacity_derivation_never_leaves_valid_queue_idle(self):
        config = router.config_from(self.config_path)
        queued = message("MSG-T01-FIXTURE-AUDIT-QUEUED-000001")
        queued.update(
            {
                "message_type": "AUDIT_INTAKE",
                "sender_role": "T1_PORTFOLIO_SUPERVISOR",
                "recipient_role": "T10_INDEPENDENT_AUDIT_SERVICE",
                "audit_slot": "QUEUED",
            }
        )
        head = self.commit_mailbox_message(queued, "integration_intake")
        state = router.initial_state(config)
        state["t10_active"] = None
        state["t10_queued"] = {
            "pack_id": "fixture-pack",
            "candidate_generation": 1,
            "source_message_id": queued["message_id"],
        }
        router.derive_deterministic_actions(state, self.mailbox, head)
        actions = {item["action_type"] for item in state["pending_semantic_actions"]}
        self.assertIn("PROMOTE_T10_QUEUED", actions)

    def test_23_ambiguous_prepared_action_fails_closed(self):
        config = router.config_from(self.config_path)
        state = router.initial_state(config)
        candidate = message("MSG-FIXTURE-CANDIDATE-000001")
        record = router.validate_message(
            router.canonical_bytes(candidate) + b"\n",
            "candidate_submissions/fixture-pack/"
            "MSG-FIXTURE-CANDIDATE-000001.json",
            "d" * 40,
        )
        router.consume_record(state, record, config)
        action = state["pending_semantic_actions"][0]
        prepared = message("MSG-T01-FIXTURE-PREFLIGHT-PASS-000001", key="6" * 64)
        prepared.update(
            {
                "message_type": "MECHANICAL_PREFLIGHT_RESULT",
                "sender_role": "T1_MECHANICAL_PREFLIGHT",
                "recipient_role": "T1_FACTORY_ROUTER",
                "parent_message_id": "WRONG-PARENT",
                "mechanical_status": "PASS",
                "source_message_sha256": record["message_sha256"],
            }
        )
        path = self.runtime / "prepared_semantic_messages" / f"{action['action_id']}.json"
        write_json(path, prepared)
        with self.assertRaises(router.RouterError):
            router.prepared_action_message(config, action, record)

    def test_24_promotion_executor_publishes_once_and_updates_slots(self):
        config = router.config_from(self.config_path)
        queued = message("MSG-T01-FIXTURE-AUDIT-QUEUED-000002", key="7" * 64)
        queued.update(
            {
                "message_type": "AUDIT_INTAKE",
                "sender_role": "T1_PORTFOLIO_SUPERVISOR",
                "recipient_role": "T10_INDEPENDENT_AUDIT_SERVICE",
                "audit_slot": "QUEUED",
            }
        )
        head = self.commit_mailbox_message(queued, "integration_intake")
        state = router.initial_state(config)
        queued_path = (
            "integration_intake/fixture-pack/"
            "MSG-T01-FIXTURE-AUDIT-QUEUED-000002.json"
        )
        queued_record = router.validate_message(
            (self.mailbox / queued_path).read_bytes(), queued_path, head
        )
        router.consume_record(state, queued_record, config)
        router.derive_deterministic_actions(state, self.mailbox, head)

        def publish_fixture(_config, **kwargs):
            value = json.loads(kwargs["message_path"].read_text(encoding="utf-8"))
            before = git(self.mailbox, "rev-parse", "HEAD")
            self.commit_mailbox_message(
                value, Path(kwargs["target"]).parts[0]
            )
            commit = git(self.mailbox, "rev-parse", "HEAD")
            target = self.mailbox / kwargs["target"]
            return {
                "message_id": value["message_id"],
                "commit": commit,
                "tree": git(self.mailbox, "show", "-s", "--format=%T", commit),
                "parent": before,
                "target": kwargs["target"],
                "message_sha256": router.hashlib.sha256(target.read_bytes()).hexdigest(),
            }

        with mock.patch.object(
            router, "publish_semantic_message", side_effect=publish_fixture
        ):
            new_head, published = router.execute_one_semantic_action(
                state, config, self.mailbox, head
            )
        self.assertTrue(published)
        self.assertNotEqual(new_head, head)
        self.assertEqual(state["t10_active"]["pack_id"], "fixture-pack")
        self.assertIsNone(state["t10_queued"])
        with mock.patch.object(router, "publish_semantic_message") as publisher:
            unchanged, published_again = router.execute_one_semantic_action(
                state, config, self.mailbox, new_head
            )
        self.assertFalse(published_again)
        self.assertEqual(unchanged, new_head)
        publisher.assert_not_called()

    def test_25_owner_repair_is_one_schema_complete_consolidated_message(self):
        candidate = message("MSG-FIXTURE-CANDIDATE-000001")
        head = self.commit_message(candidate)
        result = message("MSG-T10-FIXTURE-AUDIT-000001", key="8" * 64)
        result.update(
            {
                "message_type": "TEST_FAIL_PRODUCT",
                "sender_role": "T10_INDEPENDENT_AUDIT_SERVICE",
                "recipient_role": "T1_PORTFOLIO_SUPERVISOR",
                "parent_message_id": candidate["message_id"],
                "findings": [
                    {
                        "finding_id": "F-001",
                        "allowed_repair_scope": ["runtime only"],
                        "required_regression_gates": ["GATE-001"],
                    },
                    {
                        "finding_id": "F-002",
                        "allowed_repair_scope": ["resource pack only"],
                        "required_regression_gates": ["GATE-002"],
                    },
                ],
            }
        )
        head = self.commit_mailbox_message(result, "tester_results")
        result_path = (
            "tester_results/fixture-pack/MSG-T10-FIXTURE-AUDIT-000001.json"
        )
        result_record = router.validate_message(
            (self.mailbox / result_path).read_bytes(), result_path, head
        )
        state = router.initial_state(router.config_from(self.config_path))
        state["t10_active"] = {
            "pack_id": "fixture-pack",
            "candidate_generation": 1,
        }
        router.consume_record(
            state, result_record, router.config_from(self.config_path)
        )
        action = next(
            item
            for item in state["pending_semantic_actions"]
            if item["action_type"] == "PUBLISH_CONSOLIDATED_OWNER_REPAIR"
        )
        repair, target = router.build_owner_repair_message(
            action, result_record, self.mailbox, head
        )
        self.assertEqual(repair["candidate_generation"], 2)
        self.assertEqual(repair["failed_candidate_generation"], 1)
        self.assertEqual(repair["required_replacement_generation"], 2)
        self.assertEqual(repair["recipient_role"], candidate["sender_role"])
        self.assertEqual(repair["finding_ids"], ["F-001", "F-002"])
        self.assertEqual(
            repair["allowed_repair_scope"],
            ["runtime only", "resource pack only"],
        )
        self.assertEqual(
            repair["required_regression_gates"], ["GATE-001", "GATE-002"]
        )
        self.assertEqual(
            target,
            f"worker_repairs/fixture-pack/{repair['message_id']}.json",
        )

    def test_26_tester_product_failure_removes_unstarted_audit_route(self):
        config = router.config_from(self.config_path)
        state = router.initial_state(config)
        state["audit_backlog"] = [
            {
                "pack_id": "fixture-pack",
                "candidate_generation": 1,
                "source_message_id": "MSG-FIXTURE-AUDIT-BACKLOG-000001",
            }
        ]
        failed = message("MSG-TESTER-FIXTURE-FAIL-000001", key="9" * 64)
        failed.update(
            {
                "message_type": "TEST_FAIL_PRODUCT",
                "sender_role": "PERSISTENT_TESTER",
                "recipient_role": "T1_PORTFOLIO_SUPERVISOR",
                "findings": [{"finding_id": "BDS-001"}],
            }
        )
        record = router.validate_message(
            router.canonical_bytes(failed) + b"\n",
            "tester_results/fixture-pack/MSG-TESTER-FIXTURE-FAIL-000001.json",
            "d" * 40,
        )
        router.consume_record(state, record, config)
        self.assertEqual(state["audit_backlog"], [])
        actions = {
            item["action_type"] for item in state["pending_semantic_actions"]
        }
        self.assertEqual(actions, {"PUBLISH_CONSOLIDATED_OWNER_REPAIR"})

    def test_27_direct_replacement_supersedes_repair_projection(self):
        config = router.config_from(self.config_path)
        state = router.initial_state(config)
        state["repair_messages_pending"] = [
            {
                "message_id": "MSG-T01-FIXTURE-REPAIR-000001",
                "repair_message_id": "MSG-T01-FIXTURE-REPAIR-000001",
                "pack_id": "fixture-pack",
                "candidate_generation": 2,
                "failed_generation": 2,
                "required_replacement_generation": 3,
                "source_result_id": "MSG-T10-FIXTURE-AUDIT-000001",
                "repair_state": "OWNER_REPLACEMENT_PENDING",
            }
        ]
        replacement = message(
            "MSG-FIXTURE-CANDIDATE-000002", generation=2, key="a" * 64
        )
        replacement["parent_message_id"] = "MSG-T01-FIXTURE-REPAIR-000001"
        record = router.validate_message(
            router.canonical_bytes(replacement) + b"\n",
            "candidate_submissions/fixture-pack/"
            "MSG-FIXTURE-CANDIDATE-000002.json",
            "d" * 40,
        )
        router.consume_record(state, record, config)
        self.assertEqual(state["repair_messages_pending"], [])
        self.assertEqual(
            state["repair_state_history"][-1]["repair_state"],
            "SUPERSEDED_BY_REPLACEMENT",
        )

    def test_28_exact_compatibility_object_quarantines_one_pack_and_advances(self):
        legacy = message("MSG-FIXTURE-LEGACY-000001")
        legacy["exact_artifact_hashes"] = None
        commit = self.commit_mailbox_message(legacy, "integration_intake")
        relative = (
            "integration_intake/fixture-pack/MSG-FIXTURE-LEGACY-000001.json"
        )
        raw = (self.mailbox / relative).read_bytes()
        raw_hash = router.hashlib.sha256(raw).hexdigest()
        entry_key = router.compatibility_key(commit, relative, raw_hash)
        write_json(
            self.compatibility_ledger,
            {
                "schema_version": "crazycraft-router-compatibility-v1",
                "entries": [
                    {
                        "entry_key": entry_key,
                        "message_id": legacy["message_id"],
                        "mailbox_commit": commit,
                        "message_path": relative,
                        "raw_message_sha256": raw_hash,
                        "historical_role": "FIXTURE_LEGACY",
                        "current_disposition": (
                            "PACK_LOCAL_QUARANTINE_SUPERSESSION_REQUIRED"
                        ),
                        "pack_affected": "fixture-pack",
                        "cursor_advancement_permitted": True,
                        "superseding_authority": None,
                        "replay_behavior": "QUARANTINE_ONE_PACK_AND_ADVANCE",
                        "exact_exemption_reason": "Exact fixture only.",
                    }
                ],
            },
        )
        self.config["compatibility_ledger_expected_entries"] = 1
        write_json(self.config_path, self.config)
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads((self.runtime / "routing_state.json").read_text())
        self.assertEqual(state["last_consumed_mailbox_commit"], commit)
        self.assertEqual(sorted(state["blocked_packs"]), ["fixture-pack"])
        self.assertEqual(len(state["compatibility_events"]), 1)
        replacement = message(
            "MSG-FIXTURE-LEGACY-000002", generation=2, key="1" * 64
        )
        replacement["message_type"] = "SHARED_RUNTIME_REQUEST"
        replacement["parent_message_id"] = legacy["message_id"]
        later = self.commit_mailbox_message(replacement, "integration_intake")
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads((self.runtime / "routing_state.json").read_text())
        self.assertEqual(state["last_consumed_mailbox_commit"], later)
        self.assertEqual(state["blocked_packs"], {})

    def test_29_new_attributable_invalid_is_pack_local_but_unknown_invalid_fails(self):
        local = message("MSG-FIXTURE-LOCAL-INVALID-000001")
        local["exact_artifact_hashes"] = None
        first = self.commit_mailbox_message(local, "integration_intake")
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads((self.runtime / "routing_state.json").read_text())
        self.assertEqual(state["last_consumed_mailbox_commit"], first)
        self.assertEqual(sorted(state["blocked_packs"]), ["fixture-pack"])
        unknown = message("MSG-FIXTURE-UNKNOWN-INVALID-000001")
        del unknown["required_action"]
        self.commit_mailbox_message(unknown, "integration_intake")
        failed = self.run_cli("--run-once")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("message missing fields", failed.stderr)

    def test_30_conflicting_semantic_idempotency_key_halts_globally(self):
        self.commit_message(
            message("MSG-FIXTURE-CANDIDATE-000001", key="f" * 64)
        )
        self.assertEqual(self.run_cli("--run-once").returncode, 0)
        second = message(
            "MSG-FIXTURE-CANDIDATE-000002", generation=2, key="f" * 64
        )
        self.commit_message(second)
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 1)
        self.assertIn("conflicting semantic idempotency keys", result.stderr)

    def test_31_current_cursor_and_full_history_replays_are_identical(self):
        anchor = self.baseline
        self.commit_message(message("MSG-FIXTURE-CANDIDATE-000001"))
        cursor = git(self.mailbox, "rev-parse", "HEAD")
        second = message(
            "MSG-FIXTURE-CANDIDATE-000002", generation=2, key="b" * 64
        )
        self.commit_message(second)
        head = git(self.mailbox, "rev-parse", "HEAD")
        config = router.config_from(self.config_path)
        _, current = router.replay_state(
            config,
            head=head,
            recovery_anchor=anchor,
            cursor=cursor,
        )
        _, full = router.replay_state(
            config, head=head, recovery_anchor=anchor
        )
        self.assertEqual(
            current["projection_sha256"], full["projection_sha256"]
        )
        self.assertEqual(current["projection"], full["projection"])
        repeated_state, repeated = router.replay_state(
            config,
            head=head,
            recovery_anchor=anchor,
            cursor=cursor,
        )
        self.assertEqual(repeated["projection_sha256"], current["projection_sha256"])
        self.assertEqual(
            len(repeated_state["pending_semantic_actions"]),
            len(current["projection"]["pending_semantic_actions"]),
        )

    def test_32_compatibility_ledger_rejects_wrong_raw_hash(self):
        legacy = message("MSG-FIXTURE-LEGACY-000002")
        legacy["exact_artifact_hashes"] = None
        commit = self.commit_mailbox_message(legacy, "integration_intake")
        relative = (
            "integration_intake/fixture-pack/MSG-FIXTURE-LEGACY-000002.json"
        )
        wrong_hash = "0" * 64
        write_json(
            self.compatibility_ledger,
            {
                "schema_version": "crazycraft-router-compatibility-v1",
                "entries": [
                    {
                        "entry_key": router.compatibility_key(
                            commit, relative, wrong_hash
                        ),
                        "message_id": legacy["message_id"],
                        "mailbox_commit": commit,
                        "message_path": relative,
                        "raw_message_sha256": wrong_hash,
                        "historical_role": "FIXTURE",
                        "current_disposition": "HISTORICAL_SUPERSEDED",
                        "pack_affected": "fixture-pack",
                        "cursor_advancement_permitted": True,
                        "superseding_authority": None,
                        "replay_behavior": "ADVANCE",
                        "exact_exemption_reason": "Fixture.",
                    }
                ],
            },
        )
        self.config["compatibility_ledger_expected_entries"] = 1
        write_json(self.config_path, self.config)
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 1)
        self.assertIn("raw object hash mismatch", result.stderr)

    def test_33_global_allocation_conflict_halts(self):
        value = message("MSG-FIXTURE-GLOBAL-CONFLICT-000001")
        value["message_type"] = "GLOBAL_ALLOCATION_CONFLICT"
        self.commit_mailbox_message(value, "final_decisions")
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 1)
        self.assertIn("global authority halt", result.stderr)

    def test_34_platform_request_waits_for_exact_t1_admission(self):
        request = message("MSG-FIXTURE-PLATFORM-REQUEST-000001")
        request["message_type"] = "SHARED_RUNTIME_INTERFACE_AUTHORITY_REQUEST"
        self.commit_mailbox_message(request, "integration_intake")
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads((self.runtime / "routing_state.json").read_text())
        self.assertEqual(state["protocol_defects"], [])
        pending = [
            action
            for action in state["pending_semantic_actions"]
            if action["action_type"] == "ROUTE_PLATFORM_REQUEST_TO_T2"
        ]
        self.assertEqual([entry["source_message_id"] for entry in pending], [
            request["message_id"]
        ])
        assignment = message(
            "MSG-T01-FIXTURE-PLATFORM-ADMISSION-000001",
            generation=request["candidate_generation"],
            key="d" * 64,
        )
        assignment["message_type"] = "PLATFORM_ADMISSION_ASSIGNMENT"
        assignment["parent_message_id"] = request["message_id"]
        self.commit_mailbox_message(assignment, "integration_intake")
        second = self.run_cli("--run-once")
        self.assertEqual(second.returncode, 0, second.stderr)
        state = json.loads((self.runtime / "routing_state.json").read_text())
        self.assertFalse(any(
            action["action_type"] == "ROUTE_PLATFORM_REQUEST_TO_T2"
            for action in state["pending_semantic_actions"]
        ))
        self.assertEqual(state["protocol_defects"], [])

    def test_35_exact_candidate_scan_sidecars_are_bound_not_messages(self):
        value = message("MSG-FIXTURE-CANDIDATE-000035")
        root = self.mailbox / "candidate_submissions" / value["pack_id"]
        object_scan = root / f"{value['message_id']}.RESTRICTED_GIT_OBJECTS_SCAN.json"
        identifier_scan = root / f"{value['message_id']}.RESTRICTED_IDENTIFIERS_SCAN.json"
        write_json(object_scan, {"status": "PASS", "reachable_blobs": 7})
        write_json(identifier_scan, {"status": "PASS", "files_scanned": 3})
        value["exact_artifact_hashes"].update(
            {
                "final_metadata_restricted_git_object_scan_sha256": (
                    router.hashlib.sha256(object_scan.read_bytes()).hexdigest()
                ),
                "final_product_restricted_identifier_scan_sha256": (
                    router.hashlib.sha256(identifier_scan.read_bytes()).hexdigest()
                ),
            }
        )
        message_path = root / f"{value['message_id']}.json"
        write_json(message_path, value)
        git(self.mailbox, "add", root.relative_to(self.mailbox).as_posix())
        git(self.mailbox, "commit", "-qm", value["message_id"])
        head = git(self.mailbox, "rev-parse", "HEAD")
        result = self.run_cli("--run-once")
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads((self.runtime / "routing_state.json").read_text())
        self.assertEqual(state["last_consumed_mailbox_commit"], head)
        self.assertEqual(
            [entry["message_id"] for entry in state["active_preflight"]],
            [value["message_id"]],
        )

        replacement = message(
            "MSG-FIXTURE-CANDIDATE-000036", generation=2, key="e" * 64
        )
        bad_sidecar = (
            root / f"{replacement['message_id']}.RESTRICTED_GIT_OBJECTS_SCAN.json"
        )
        write_json(bad_sidecar, {"status": "PASS"})
        replacement["exact_artifact_hashes"][
            "final_metadata_restricted_git_object_scan_sha256"
        ] = "0" * 64
        replacement_path = root / f"{replacement['message_id']}.json"
        write_json(replacement_path, replacement)
        git(self.mailbox, "add", root.relative_to(self.mailbox).as_posix())
        git(self.mailbox, "commit", "-qm", replacement["message_id"])
        failed = self.run_cli("--run-once")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("candidate sidecar authority binding failed", failed.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
