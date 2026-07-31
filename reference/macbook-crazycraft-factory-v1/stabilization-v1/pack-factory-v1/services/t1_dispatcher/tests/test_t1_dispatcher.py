from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("t1_dispatcher", ROOT / "t1_dispatcher.py")
t1 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(t1)


class T1DispatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.runtime = Path(self.temporary.name)
        self.config = t1.config_from(ROOT / "t1-dispatcher-config.json")
        self.config["runtime_root"] = str(self.runtime)
        self.connection = t1.open_database(self.runtime)
        self.addCleanup(self.connection.close)

    def insert(self, action_id: str = "action-1", action_type: str = "TEST") -> None:
        t1.insert_action(
            self.connection,
            action_id=action_id,
            action_type=action_type,
            pack_id="fixture-pack",
            generation=2,
            source_message="MSG-FIXTURE",
            source_commit="a" * 40,
            authority="b" * 64,
            idempotency_key=action_id,
            next_action="EXECUTE",
        )

    def test_01_prepared_mechanical_action_execution(self) -> None:
        self.insert(action_type="RUN_MECHANICAL_PREFLIGHT")
        self.assertTrue(t1.lease_action(self.connection, "action-1", "owner", 30, 3))
        row = self.connection.execute(
            "SELECT * FROM actions WHERE action_id='action-1'"
        ).fetchone()
        self.assertEqual(row["current_state"], "LEASED")
        self.assertEqual(row["attempt_count"], 1)

    def test_02_mechanical_pass_tester_routing(self) -> None:
        _, candidate, _ = t1.source_candidate(self.config, "ASPECTWEAVE-CANDIDATE-0009")
        evaluation, descriptors, artifact_bytes = t1.evaluate_candidate(
            self.config, candidate
        )
        self.assertEqual(evaluation["status"], "PASS")
        action = {"action_id": "c" * 64}
        mechanical = t1.prepared_mechanical_message(
            action, candidate, "d" * 64, evaluation, descriptors
        )
        intake = t1.tester_message(
            self.config, candidate, mechanical, descriptors, artifact_bytes, 999
        )
        self.assertEqual(intake["message_type"], "TESTER_INTAKE")
        self.assertEqual(
            intake["parent_message_id"], mechanical["message_id"]
        )

    def test_03_mechanical_fail_repair_routing(self) -> None:
        self.insert(action_type="RUN_MECHANICAL_PREFLIGHT")
        t1.update_action(
            self.connection,
            "action-1",
            "TERMINAL_FAIL",
            result="MSG-MECHANICAL-FAIL",
            next_action="PUBLISH_CONSOLIDATED_OWNER_REPAIR",
        )
        row = self.connection.execute(
            "SELECT * FROM actions WHERE action_id='action-1'"
        ).fetchone()
        self.assertEqual(row["next_action"], "PUBLISH_CONSOLIDATED_OWNER_REPAIR")

    def test_04_bds_pass_t10_routing(self) -> None:
        _, candidate, _ = t1.source_candidate(
            self.config, "ASPECTWEAVE-CANDIDATE-0009"
        )
        mechanical = {
            "message_id": "MSG-MECHANICAL-PASS",
            "exact_artifact_hashes": candidate["exact_artifact_hashes"],
        }
        tester = {
            "message_id": "MSG-TESTER-PASS",
            "pack_id": candidate["pack_id"],
            "candidate_generation": candidate["candidate_generation"],
        }
        route = t1.t10_route_message(candidate, mechanical, tester, "ACTIVE")
        self.assertEqual(route["routing_state"], "ACTIVE")
        self.assertEqual(route["source_tester_result_id"], tester["message_id"])

    def test_05_repair_message_worker_resumption(self) -> None:
        self.insert(action_type="RESUME_PACK_WORKER")
        t1.queue_resume_request(
            self.config,
            self.connection,
            action_id="action-1",
            pack_id="fixture-pack",
            task_id="task-1",
            assignment_id="assignment-1",
            repository="/tmp/fixture",
            ref="refs/heads/main",
            authority_message="MSG-REPAIR",
            authority_commit="e" * 40,
            authority_sha256="1" * 64,
            required_generation=3,
        )
        request = t1.pending_resume_requests(self.config)[0]
        self.assertEqual(request["authority_message"], "MSG-REPAIR")
        self.assertIn("complete-pack assignment", request["prompt"])

    def test_06_nonterminal_worker_exit_and_replacement(self) -> None:
        self.test_05_repair_message_worker_resumption()
        request = t1.pending_resume_requests(self.config)[0]
        t1.ack_resume(self.config, self.connection, request["request_id"], "SENT")
        row = self.connection.execute(
            "SELECT * FROM actions WHERE action_id='action-1'"
        ).fetchone()
        self.assertEqual(row["current_state"], "WAITING_EXTERNAL_RESULT")
        self.assertEqual(row["next_action"], "WAIT_FOR_REPLACEMENT_CANDIDATE")

    def test_07_duplicate_wake_prevention(self) -> None:
        self.insert(action_type="RESUME_PACK_WORKER")
        kwargs = dict(
            action_id="action-1",
            pack_id="fixture-pack",
            task_id="task-1",
            assignment_id="assignment-1",
            repository="/tmp/fixture",
            ref="refs/heads/main",
            authority_message="MSG-REPAIR",
            authority_commit="f" * 40,
            authority_sha256="2" * 64,
            required_generation=3,
        )
        t1.queue_resume_request(self.config, self.connection, **kwargs)
        t1.queue_resume_request(self.config, self.connection, **kwargs)
        self.assertEqual(len(list((self.runtime / "resume_requests").glob("*.json"))), 1)

    def test_08_t1_to_t2_request_preparation(self) -> None:
        source_path, source = next(
            (path, message)
            for path, message in t1.current_mailbox_messages(
                self.config, "integration_intake", "echo-vessels"
            )
            if message.get("message_id") == "MSG-P13-ECHO-PLATFORM-REQUEST-000004"
        )
        raw = source_path.read_bytes()
        authority = t1.mailbox_message_authority(
            self.config, source_path, source["message_id"]
        )
        action = {"action_id": "1" * 64}
        admission = t1.echo_admission_message(action, source, raw, authority)
        self.assertEqual(admission["recipient_role"], "SHARED_RUNTIME_INTEGRATION_WORKER")
        self.assertFalse(admission["immutable_candidate_exists"])
        self.assertTrue(admission["candidate_generation_label_only"])
        self.assertEqual(
            admission["source_request_introduction_commit"],
            "7b18e97d1852a45f78c909347c1f38e9926022c0",
        )

    def test_09_dispatcher_restart_reconstruction(self) -> None:
        self.insert()
        self.connection.close()
        reopened = t1.open_database(self.runtime)
        self.connection = reopened
        self.addCleanup(reopened.close)
        row = reopened.execute(
            "SELECT * FROM actions WHERE action_id='action-1'"
        ).fetchone()
        self.assertEqual(row["current_state"], "PENDING")

    def test_10_stale_lease_recovery(self) -> None:
        self.insert()
        self.assertTrue(t1.lease_action(self.connection, "action-1", "dead", 30, 3))
        self.connection.execute(
            "UPDATE actions SET lease_expires_at=? WHERE action_id='action-1'",
            (int(time.time()) - 1,),
        )
        self.assertTrue(t1.lease_action(self.connection, "action-1", "new", 30, 3))
        row = self.connection.execute(
            "SELECT * FROM actions WHERE action_id='action-1'"
        ).fetchone()
        self.assertEqual(row["lease_owner"], "new")
        self.assertEqual(row["attempt_count"], 2)

    def test_11_exact_candidate_binding(self) -> None:
        for message_id in (
            "ASPECTWEAVE-CANDIDATE-0009",
            "CC-P16-LATCHLINE-CANDIDATE-000007",
            "MSG-P14-OUTCOMES-CANDIDATE-000015",
            "MSG-P12-APERTURE-CANDIDATE-000004",
            "MSG-P08-HEARTH-HALL-CANDIDATE-000002",
        ):
            _, candidate, _ = t1.source_candidate(self.config, message_id)
            evaluation, _, _ = t1.evaluate_candidate(self.config, candidate)
            self.assertTrue(
                all(
                    status == "PASSED"
                    for gate, status in evaluation["gates"].items()
                    if gate != "working_tree_clean"
                ),
                message_id,
            )

    def test_12_superseded_repository_rejection(self) -> None:
        _, candidate, _ = t1.source_candidate(
            self.config, "MSG-P12-APERTURE-CANDIDATE-000004"
        )
        authority = t1.repository_authority(self.config, candidate)
        self.assertTrue(authority["repository"].endswith("aperture-foundry-reproduction-v1"))
        self.assertNotEqual(
            authority["repository"],
            self.config["worker_repository_overrides"].get("superseded-aperture", ""),
        )

    def test_13_integration_intake_publication(self) -> None:
        _, candidate, _ = t1.source_candidate(
            self.config, "ASPECTWEAVE-CANDIDATE-0009"
        )
        mechanical = {
            "message_id": "MSG-MECHANICAL-PASS",
            "exact_artifact_hashes": candidate["exact_artifact_hashes"],
        }
        tester = {"message_id": "MSG-TESTER-PASS"}
        audit = {"message_id": "MSG-T10-PASS"}
        intake = t1.integration_message(candidate, mechanical, tester, audit)
        self.assertEqual(intake["recipient_role"], "SHARED_RUNTIME_INTEGRATION_WORKER")
        self.assertEqual(intake["source_t10_result_id"], audit["message_id"])

    def test_14_no_product_writes_by_t1(self) -> None:
        source = inspect.getsource(t1.execute_mechanical)
        self.assertNotIn("write_text", source)
        self.assertNotIn("write_bytes", source)
        self.assertNotIn("git_text(", source)

    def test_15_no_direct_worker_action_from_t10_without_t1_repair(self) -> None:
        self.test_05_repair_message_worker_resumption()
        prompt = t1.pending_resume_requests(self.config)[0]["prompt"]
        self.assertIn("Exact committed mailbox authority: MSG-REPAIR", prompt)
        self.assertIn("do not read T10 directly", prompt)

    def test_16_reliquary_relative_path_normalization(self) -> None:
        source_path, candidate, _ = t1.source_candidate(
            self.config, "MSG-P07-RELIQUARY-CANDIDATE-000007"
        )
        authority = t1.mailbox_message_authority(
            self.config, source_path, candidate["message_id"]
        )
        normalized = t1.normalize_candidate_authority(
            self.config, candidate, authority
        )
        self.assertEqual(
            normalized["artifacts"]["behavior_pack"]["path"],
            "dist/reliquary-vaults-bp.mcpack",
        )
        self.assertEqual(
            normalized["artifacts"]["behavior_pack"]["sha256"],
            candidate["exact_artifact_hashes"]["behavior_pack"],
        )

    def test_17_equivalent_artifact_layouts_match(self) -> None:
        _, candidate, _ = t1.source_candidate(
            self.config, "MSG-P07-RELIQUARY-CANDIDATE-000007"
        )
        normalized = t1.normalize_candidate_authority(self.config, candidate)
        altered = copy.deepcopy(candidate)
        for role in ("behavior_pack", "resource_pack", "mcaddon", "artifact_manifest"):
            altered[role]["path"] = altered[role].pop("relative_path")
        altered.pop("artifact_authorities")
        alternate = t1.normalize_candidate_authority(self.config, altered)
        for role in ("behavior_pack", "resource_pack", "mcaddon", "artifact_manifest"):
            self.assertEqual(
                {
                    key: normalized["artifacts"][role][key]
                    for key in ("path", "sha256", "commit")
                },
                {
                    key: alternate["artifacts"][role][key]
                    for key in ("path", "sha256", "commit")
                },
            )

    def test_18_genuinely_incomplete_candidate_authority(self) -> None:
        _, candidate, _ = t1.source_candidate(
            self.config, "MSG-P09-HEARTHVEIL-CANDIDATE-000006"
        )
        malformed = copy.deepcopy(candidate)
        malformed.pop("assigned_ref")
        with self.assertRaisesRegex(t1.DispatchError, "incomplete candidate authority"):
            t1.normalize_candidate_authority(self.config, malformed)

    def test_19_unknown_future_artifact_layout_fails_closed(self) -> None:
        _, candidate, _ = t1.source_candidate(
            self.config, "MSG-P07-RELIQUARY-CANDIDATE-000007"
        )
        malformed = copy.deepcopy(candidate)
        malformed.pop("artifact_authorities")
        malformed["behavior_pack"]["artifact_locator"] = malformed[
            "behavior_pack"
        ].pop("relative_path")
        with self.assertRaisesRegex(t1.DispatchError, "descriptor missing"):
            t1.normalize_candidate_authority(self.config, malformed)

    def test_20_hearthveil_assigned_ref_and_product_metadata(self) -> None:
        source_path, candidate, _ = t1.source_candidate(
            self.config, "MSG-P09-HEARTHVEIL-CANDIDATE-000006"
        )
        authority = t1.mailbox_message_authority(
            self.config, source_path, candidate["message_id"]
        )
        normalized = t1.normalize_candidate_authority(
            self.config, candidate, authority
        )
        self.assertEqual(normalized["ref"], candidate["assigned_ref"])
        self.assertEqual(normalized["metadata_commit"], candidate["production_commit"])
        self.assertNotEqual(
            normalized["metadata_commit"], candidate["source_authority_commit"]
        )

    def test_21_echo_request_classification_binds_exact_surface(self) -> None:
        source_path, source = next(
            (path, message)
            for path, message in t1.current_mailbox_messages(
                self.config, "integration_intake", "echo-vessels"
            )
            if message.get("message_id") == "MSG-P13-ECHO-PLATFORM-REQUEST-000004"
        )
        authority = t1.mailbox_message_authority(
            self.config, source_path, source["message_id"]
        )
        classified = t1.classify_echo_platform_request(source, authority)
        self.assertEqual(classified["request_sequence"], 4)
        self.assertEqual(
            classified["requested_platform"]["request_kind"],
            "EXACT_REGISTRY_ADMISSION_ONLY",
        )

    def test_22_echo_admission_is_exactly_once_across_retry(self) -> None:
        source_path, source = next(
            (path, message)
            for path, message in t1.current_mailbox_messages(
                self.config, "integration_intake", "echo-vessels"
            )
            if message.get("message_id") == "MSG-P13-ECHO-PLATFORM-REQUEST-000004"
        )
        authority = t1.mailbox_message_authority(
            self.config, source_path, source["message_id"]
        )
        first = t1.echo_admission_message(
            {"action_id": "a" * 64}, source, source_path.read_bytes(), authority
        )
        second = t1.echo_admission_message(
            {"action_id": "b" * 64}, source, source_path.read_bytes(), authority
        )
        self.assertEqual(first["message_id"], second["message_id"])
        self.assertEqual(first["idempotency_key"], second["idempotency_key"])

    def test_23_semantic_identity_ignores_observational_head(self) -> None:
        arguments = dict(
            action_type="ROUTE_PLATFORM_REQUEST_TO_T2",
            pack_id="echo-vessels",
            message_id="MSG-P13-ECHO-PLATFORM-REQUEST-000004",
            introduction_commit="7" * 40,
            message_sha256="8" * 64,
            generation_or_sequence=4,
        )
        first = t1.semantic_action_identity(**arguments)
        observational_heads = ("9" * 40, "a" * 40)
        self.assertNotEqual(*observational_heads)
        self.assertEqual(first, t1.semantic_action_identity(**arguments))

    def test_24_resume_dedupes_after_mailbox_head_advance(self) -> None:
        self.insert(action_type="RESUME_PACK_WORKER")
        base = dict(
            action_id="action-1",
            pack_id="fixture-pack",
            task_id="task-1",
            assignment_id="assignment-1",
            repository="/tmp/fixture",
            ref="refs/heads/main",
            authority_message="MSG-IMMUTABLE-REPAIR",
            authority_sha256="3" * 64,
            required_generation=3,
        )
        t1.queue_resume_request(
            self.config, self.connection, authority_commit="4" * 40, **base
        )
        t1.queue_resume_request(
            self.config, self.connection, authority_commit="5" * 40, **base
        )
        self.assertEqual(len(list((self.runtime / "resume_requests").glob("*.json"))), 1)

    def test_25_historical_duplicate_attempts_are_preserved(self) -> None:
        self.insert(action_type="RESUME_PACK_WORKER")
        root = self.runtime / "resume_requests"
        root.mkdir(parents=True)
        for index, commit in enumerate(("6" * 40, "7" * 40)):
            t1.atomic_json(
                root / f"legacy-{index}.json",
                {
                    "request_id": f"legacy-{index}",
                    "action_id": "old-action",
                    "kind": "PACK_OWNER",
                    "pack_id": "fixture-pack",
                    "task_id": "task-1",
                    "assignment_id": "assignment-1",
                    "repository": "/tmp/fixture",
                    "ref": "refs/heads/main",
                    "authority_message": "MSG-DUPLICATED-REPAIR",
                    "authority_commit": commit,
                    "required_generation": 3,
                    "prompt": "historical",
                    "state": "SENT",
                    "created_at": f"2026-01-0{index + 1}T00:00:00Z",
                },
            )
        t1.queue_resume_request(
            self.config,
            self.connection,
            action_id="action-1",
            pack_id="fixture-pack",
            task_id="task-1",
            assignment_id="assignment-1",
            repository="/tmp/fixture",
            ref="refs/heads/main",
            authority_message="MSG-DUPLICATED-REPAIR",
            authority_commit="8" * 40,
            authority_sha256="9" * 64,
            required_generation=3,
        )
        self.assertEqual(len(list(root.glob("*.json"))), 2)

    def test_26_corrected_parser_block_replays_without_new_action(self) -> None:
        self.insert(action_type="RUN_MECHANICAL_PREFLIGHT")
        self.connection.execute(
            "UPDATE actions SET source_mailbox_message=?,current_state='PACK_LOCAL_BLOCK',"
            "last_error=?,attempt_count=1 WHERE action_id='action-1'",
            (
                "MSG-P07-RELIQUARY-CANDIDATE-000007",
                "KeyError: 'path'",
            ),
        )
        t1.reconcile_corrected_parser_blocks(self.connection)
        row = self.connection.execute(
            "SELECT * FROM actions WHERE action_id='action-1'"
        ).fetchone()
        self.assertEqual(row["current_state"], "PENDING")
        self.assertEqual(row["attempt_count"], 1)
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM actions").fetchone()[0], 1
        )

    def test_27_unrelated_traffic_does_not_change_semantic_identity(self) -> None:
        identity = t1.semantic_action_identity(
            action_type="RUN_MECHANICAL_PREFLIGHT",
            pack_id="reliquary-vaults",
            message_id="MSG-P07-RELIQUARY-CANDIDATE-000007",
            introduction_commit="d7e79747e4048999898a03d527389cb5e9619294",
            message_sha256="358b089f947385113d2ae83a4fb8ad32a1c8195207ce2d3dae9ecfea3b3dd547",
            generation_or_sequence=7,
        )
        unrelated = [
            message
            for _, message in t1.current_mailbox_messages(
                self.config, "candidate_submissions", "vanguard-arsenal"
            )
        ]
        self.assertTrue(unrelated)
        self.assertEqual(
            identity,
            t1.semantic_action_identity(
                action_type="RUN_MECHANICAL_PREFLIGHT",
                pack_id="reliquary-vaults",
                message_id="MSG-P07-RELIQUARY-CANDIDATE-000007",
                introduction_commit="d7e79747e4048999898a03d527389cb5e9619294",
                message_sha256="358b089f947385113d2ae83a4fb8ad32a1c8195207ce2d3dae9ecfea3b3dd547",
                generation_or_sequence=7,
            ),
        )

    def test_28_dispatcher_restart_preserves_single_admission_publication(self) -> None:
        self.insert(action_type="ROUTE_PLATFORM_REQUEST_TO_T2")
        self.connection.execute(
            "INSERT INTO publications(idempotency_key,message_id,mailbox_commit,"
            "message_sha256,action_id,published_at) VALUES(?,?,?,?,?,?)",
            (
                "a" * 64,
                "MSG-T1D-ECHO-ADMISSION-FIXTURE",
                "b" * 40,
                "c" * 64,
                "action-1",
                "2026-01-01T00:00:00Z",
            ),
        )
        self.connection.close()
        reopened = t1.open_database(self.runtime)
        self.connection = reopened
        self.addCleanup(reopened.close)
        self.assertEqual(
            reopened.execute(
                "SELECT COUNT(*) FROM publications WHERE action_id='action-1'"
            ).fetchone()[0],
            1,
        )

    def test_29_semantic_action_insert_is_idempotent(self) -> None:
        self.insert(action_id="semantic-1", action_type="ROUTE_PLATFORM_REQUEST_TO_T2")
        self.insert(action_id="semantic-1", action_type="ROUTE_PLATFORM_REQUEST_TO_T2")
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM actions WHERE action_id='semantic-1'"
            ).fetchone()[0],
            1,
        )

    def test_30_corrected_replay_does_not_execute_unrelated_actions(self) -> None:
        executed = []

        def reconcile(_config, connection):
            for action_id, message_id, pack_id in (
                (
                    "reliquary-action",
                    "MSG-P07-RELIQUARY-CANDIDATE-000007",
                    "reliquary-vaults",
                ),
                ("unrelated-action", "MSG-UNRELATED-CANDIDATE", "unrelated-pack"),
            ):
                t1.insert_action(
                    connection,
                    action_id=action_id,
                    action_type="RUN_MECHANICAL_PREFLIGHT",
                    pack_id=pack_id,
                    generation=7,
                    source_message=message_id,
                    source_commit="a" * 40,
                    authority="b" * 64,
                    idempotency_key=action_id,
                    next_action="EXECUTE_EXISTING_MECHANICAL_GATE",
                )

        def execute(_config, connection, action):
            executed.append(action["source_mailbox_message"])
            t1.update_action(connection, action["action_id"], "TERMINAL_PASS")

        with (
            mock.patch.object(t1, "reconcile_router_actions", side_effect=reconcile),
            mock.patch.object(t1, "reconcile_corrected_parser_blocks"),
            mock.patch.object(t1, "execute_mechanical", side_effect=execute),
            mock.patch.object(t1, "snapshot", return_value={}),
        ):
            t1.run_corrected_parser_replay(self.config)
        self.assertEqual(
            executed, ["MSG-P07-RELIQUARY-CANDIDATE-000007"]
        )


if __name__ == "__main__":
    unittest.main()
