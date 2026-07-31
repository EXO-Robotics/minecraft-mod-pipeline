from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import threading
import time
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "local_tester_service", ROOT / "local_tester_service.py"
)
assert SPEC and SPEC.loader
service = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(service)
from remote_job_lib import PROHIBITED_DISCLOSURE_CLASSES  # noqa: E402


def git(repository: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


class TesterServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def repository(self, name: str) -> Path:
        path = self.root / name
        path.mkdir()
        git(path, "init", "-q")
        git(path, "config", "user.email", "tester@example.invalid")
        git(path, "config", "user.name", "Tester")
        return path

    def fixture(self):
        product = self.repository("product")
        data = {
            "behavior_pack": ("dist/behavior.mcpack", b"behavior"),
            "resource_pack": ("dist/resource.mcpack", b"resource"),
            "mcaddon": ("dist/candidate.mcaddon", b"addon"),
        }
        for path, content in data.values():
            target = product / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        git(product, "add", ".")
        git(product, "commit", "-qm", "candidate")
        commit = git(product, "rev-parse", "HEAD")
        tree = git(product, "rev-parse", "HEAD^{tree}")
        request = {
            "schema_version": "crazycraft-remote-v1",
            "job_id": "JOB-000000000014",
            "job_type": "BDS_QUALIFICATION",
            "requesting_authority": "T1",
            "assignment_id": "PACK-EXAMPLE-1",
            "campaign_id": "example-pack",
            "exact_input_authorities": [{"candidate_commit": commit}],
            "permitted_evidence_roots": [],
            "permitted_candidate_paths": [
                "behavior.mcpack",
                "resource.mcpack",
                "candidate.mcaddon",
                "request.json",
            ],
            "permitted_output_directory": "artifacts",
            "prohibited_disclosure_classes": sorted(
                PROHIBITED_DISCLOSURE_CLASSES
            ),
            "timeout_seconds": 900,
            "termination_policy": "TERMINATE_AND_RECEIPT",
            "requested_result_schema": "example-v1",
            "bds": {
                "candidate_repository": str(product),
                "candidate_ref": "refs/heads/master",
                "content_commit": commit,
                "content_tree": tree,
                "metadata_commit": commit,
                "metadata_tree": tree,
                "behavior_pack_path": "behavior.mcpack",
                "behavior_pack_size": len(data["behavior_pack"][1]),
                "behavior_pack_sha256": hashlib.sha256(data["behavior_pack"][1]).hexdigest(),
                "resource_pack_path": "resource.mcpack",
                "resource_pack_size": len(data["resource_pack"][1]),
                "resource_pack_sha256": hashlib.sha256(data["resource_pack"][1]).hexdigest(),
                "mcaddon_path": "candidate.mcaddon",
                "mcaddon_size": len(data["mcaddon"][1]),
                "mcaddon_sha256": hashlib.sha256(data["mcaddon"][1]).hexdigest(),
                "image_digest": service.IMAGE_V2,
                "image_platform": "linux/amd64",
                "qualifier_sha256": "d1af68f59307d5624352acb2c11f1b24feb66bf1e6351190eb950ff705d56880",
                "bds_channel": "STABLE",
                "bds_version": "1.26.33.2",
                "bds_binary_sha256": "9" * 64,
                "base_world_sha256": "8" * 64,
                "fixture_set": "EXAMPLE_LOAD_RESTART_V1",
                "expected_gates": ["PACK_LOAD"],
                "port": 19220,
                "container_name": "example-job-14",
                "cpus": 1,
                "memory_mb": 512,
                "candidate_profile": {
                    "schema_version": "crazycraft-bds-candidate-profile-v1",
                    "behavior_pack": {
                        "manifest_uuid": "11111111-1111-4111-8111-111111111111",
                        "version": [1, 0, 0],
                        "install_directory": "example-bp",
                    },
                    "resource_pack": {
                        "manifest_uuid": "22222222-2222-4222-8222-222222222222",
                        "version": [1, 0, 0],
                        "install_directory": "example-rp",
                    },
                    "addon": {
                        "behavior_member": "example-behavior.mcpack",
                        "resource_member": "example-resource.mcpack",
                    },
                    "script": None,
                    "expected_pack_marker": "Example Behavior",
                    "world_name": "Example World",
                    "fixture_id": "EXAMPLE_LOAD_RESTART_V1",
                },
            },
            "request_payload_sha256": "",
        }
        request["request_payload_sha256"] = service.payload_hash(
            request, "request_payload_sha256"
        )
        message = {
            "schema_version": "1.0.0",
            "message_id": "MSG-EXAMPLE-000001",
            "message_type": "TESTER_INTAKE",
            "pack_id": "example-pack",
            "sender_role": "T1_PORTFOLIO_SUPERVISOR",
            "recipient_role": "PERSISTENT_TESTER",
            "created_at": "2026-07-29T00:00:00Z",
            "source_authority_commit": commit,
            "source_authority_tree": tree,
            "candidate_generation": 1,
            "exact_artifact_hashes": {
                role: request["bds"][f"{role}_sha256"] for role in service.ARTIFACT_ROLES
            },
            "parent_message_id": None,
            "required_action": "RUN_EXACT_PACKAGE_QUALIFICATION",
            "idempotency_key": "",
            "proof_boundary": ["STABLE_BDS_ONLY"],
            "qualification_request": request,
            "artifact_sources": {
                role: {"authority_commit": commit, "git_path": value[0]}
                for role, value in data.items()
            },
        }
        message["idempotency_key"] = service.sha256_bytes(
            service.canonical_bytes(
                {
                    "message_id": message["message_id"],
                    "pack_id": message["pack_id"],
                    "candidate_generation": 1,
                    "request_payload_sha256": request["request_payload_sha256"],
                }
            )
        )
        return product, request, message

    def config(self, mailbox: Path) -> dict:
        branch = git(mailbox, "branch", "--show-current")
        return {
            "schema_version": "crazycraft-local-tester-v1",
            "mailbox_repository": str(mailbox),
            "mailbox_ref": f"refs/heads/{branch}",
            "runtime_root": str(self.root / "runtime"),
            "allowed_candidate_roots": [str(self.root)],
            "allowed_tester_images": [service.IMAGE_V2],
            "max_active_jobs": 2,
            "max_active_per_pack": 1,
            "poll_seconds": 15,
        }

    def test_config_pins_v2_and_concurrency(self):
        config = service.load_config(ROOT / "local-tester-config.json")
        self.assertEqual(config["allowed_tester_images"], [service.IMAGE_V2])
        self.assertEqual((config["max_active_jobs"], config["max_active_per_pack"]), (2, 1))

    def test_selection_is_two_total_and_one_per_pack(self):
        messages = [
            (str(index), {"message_id": f"MSG-{index:08d}", "pack_id": pack})
            for index, pack in enumerate(("one", "one", "two", "three"), 1)
        ]
        selected = service.select_dispatchable(messages, {"jobs": {}}, 2)
        self.assertEqual([value[1]["pack_id"] for value in selected], ["one", "two"])

    def test_committed_discovery_ignores_untracked_intake(self):
        mailbox = self.repository("mailbox")
        target = mailbox / "tester_intake" / "pack" / "tracked.json"
        target.parent.mkdir(parents=True)
        target.write_text('{"qualification_request":{}}\n')
        git(mailbox, "add", ".")
        git(mailbox, "commit", "-qm", "intake")
        (target.parent / "untracked.json").write_text('{"qualification_request":{}}\n')
        _, records = service.committed_messages(
            {"mailbox_repository": str(mailbox), "mailbox_ref": "HEAD"}
        )
        self.assertEqual(len(records), 1)

    def test_committed_discovery_skips_intake_with_result(self):
        mailbox = self.repository("mailbox-consumed")
        intake = mailbox / "tester_intake" / "pack" / "tracked.json"
        result = mailbox / "tester_results" / "pack" / "result.json"
        intake.parent.mkdir(parents=True)
        result.parent.mkdir(parents=True)
        intake.write_text(
            '{"message_id":"MSG-INTAKE-000001","qualification_request":{}}\n'
        )
        result.write_text(
            '{"message_id":"MSG-RESULT-000001",'
            '"parent_message_id":"MSG-INTAKE-000001"}\n'
        )
        git(mailbox, "add", ".")
        git(mailbox, "commit", "-qm", "consumed intake")
        _, records = service.committed_messages(
            {"mailbox_repository": str(mailbox), "mailbox_ref": "HEAD"}
        )
        self.assertEqual(records, [])

    def test_stage_reads_exact_commit_without_product_edit(self):
        mailbox = self.repository("mailbox")
        (mailbox / ".keep").write_text("")
        git(mailbox, "add", ".")
        git(mailbox, "commit", "-qm", "mailbox")
        product, _, message = self.fixture()
        before = git(product, "status", "--porcelain")
        job = service.stage_job(
            self.config(mailbox),
            git(mailbox, "rev-parse", "HEAD"),
            "tester_intake/example.json",
            message,
        )
        self.assertEqual((job / "inputs" / "candidate.mcaddon").read_bytes(), b"addon")
        self.assertEqual(git(product, "status", "--porcelain"), before)

    def test_result_publication_is_append_only_and_candidate_bound(self):
        mailbox = self.repository("mailbox")
        (mailbox / ".keep").write_text("")
        git(mailbox, "add", ".")
        git(mailbox, "commit", "-qm", "mailbox")
        _, request, message = self.fixture()
        head = git(mailbox, "rev-parse", "HEAD")
        job = service.stage_job(
            self.config(mailbox), head, "tester_intake/example.json", message
        )
        result = {
            "schema_version": "crazycraft-remote-v1",
            "job_id": request["job_id"],
            "result_classification": "TEST_PASS",
            "opaque_finding_ids": [],
            "proof_boundary": "Exact Stable BDS only.",
            "external_gates_not_run": ["BEDROCK_CLIENT"],
            "result_payload_sha256": "",
        }
        result["result_payload_sha256"] = service.payload_hash(
            result, "result_payload_sha256"
        )
        service.write_json(job / "result.json", result)
        service.write_json(
            job / "artifacts" / "qualifier-receipt.json",
            {"job_id": request["job_id"]},
        )
        commit, _ = service.publish_result(self.config(mailbox), job)
        self.assertEqual(git(mailbox, "rev-parse", "HEAD"), commit)
        path = (
            mailbox
            / "tester_results"
            / "example-pack"
            / "MSG-TESTER-000000000014-PASS.json"
        )
        published = json.loads(path.read_text())
        self.assertEqual(published["candidate_hash"], request["bds"]["mcaddon_sha256"])
        repeated_commit, repeated_tree = service.publish_result(
            self.config(mailbox), job
        )
        self.assertEqual(repeated_commit, commit)
        self.assertEqual(repeated_tree, git(mailbox, "rev-parse", "HEAD^{tree}"))

    def test_result_publication_retries_transient_dirty_mailbox(self):
        mailbox = self.repository("mailbox-transient-dirty")
        (mailbox / ".keep").write_text("")
        git(mailbox, "add", ".")
        git(mailbox, "commit", "-qm", "mailbox")
        _, request, message = self.fixture()
        job = service.stage_job(
            self.config(mailbox),
            git(mailbox, "rev-parse", "HEAD"),
            "tester_intake/example.json",
            message,
        )
        result = {
            "schema_version": "crazycraft-remote-v1",
            "job_id": request["job_id"],
            "result_classification": "TEST_PASS",
            "opaque_finding_ids": [],
            "proof_boundary": "Exact Stable BDS only.",
            "external_gates_not_run": [],
            "result_payload_sha256": "",
        }
        result["result_payload_sha256"] = service.payload_hash(
            result, "result_payload_sha256"
        )
        service.write_json(job / "result.json", result)
        service.write_json(
            job / "artifacts" / "qualifier-receipt.json",
            {"job_id": request["job_id"]},
        )
        transient = mailbox / "unrelated-worker.tmp"
        transient.write_text("in progress\n")

        def clear_transient():
            time.sleep(0.05)
            transient.unlink()

        cleanup = threading.Thread(target=clear_transient)
        cleanup.start()
        old_delay = service.PUBLICATION_RETRY_DELAY_SECONDS
        service.PUBLICATION_RETRY_DELAY_SECONDS = 0.01
        try:
            commit, _ = service.publish_result(self.config(mailbox), job)
        finally:
            service.PUBLICATION_RETRY_DELAY_SECONDS = old_delay
            cleanup.join()
        self.assertEqual(git(mailbox, "rev-parse", "HEAD"), commit)

    def test_reconcile_recovers_completed_result_without_rerunning_bds(self):
        mailbox = self.repository("mailbox-recovery")
        (mailbox / ".keep").write_text("")
        git(mailbox, "add", ".")
        git(mailbox, "commit", "-qm", "mailbox")
        _, request, message = self.fixture()
        config = self.config(mailbox)
        job = service.stage_job(
            config,
            git(mailbox, "rev-parse", "HEAD"),
            "tester_intake/example.json",
            message,
        )
        result = {
            "schema_version": "crazycraft-remote-v1",
            "job_id": request["job_id"],
            "result_classification": "TEST_PASS",
            "opaque_finding_ids": [],
            "proof_boundary": "Exact Stable BDS only.",
            "external_gates_not_run": [],
            "result_payload_sha256": "",
        }
        result["result_payload_sha256"] = service.payload_hash(
            result, "result_payload_sha256"
        )
        service.write_json(job / "result.json", result)
        service.write_json(
            job / "artifacts" / "qualifier-receipt.json",
            {"job_id": request["job_id"]},
        )
        service.result_message(job)
        state = {
            "jobs": {
                message["message_id"]: {
                    "state": "FAILED",
                    "pid": 99999999,
                    "pack_id": message["pack_id"],
                    "job_id": request["job_id"],
                    "job_root": str(job),
                }
            }
        }
        service.reconcile(state, config)
        self.assertEqual(
            state["jobs"][message["message_id"]]["state"], "COMPLETED"
        )
        status = json.loads((job / "status.json").read_text())
        self.assertTrue(status["recovered_publication"])
        self.assertTrue(
            (
                mailbox
                / "tester_results"
                / "example-pack"
                / "MSG-TESTER-000000000014-PASS.json"
            ).is_file()
        )

    def test_launchd_has_no_secret_material(self):
        text = (ROOT / "com.crazycraft.local-tester.plist").read_text()
        self.assertNotIn("SSH_AUTH_SOCK", text)
        self.assertNotIn("PRIVATE KEY", text)
        self.assertIn("runtime/launchd.stderr.log", text)

    def test_reconcile_prefers_terminal_status_over_live_pid(self):
        job_root = self.root / "job"
        job_root.mkdir()
        service.write_json(job_root / "status.json", {"state": "COMPLETED"})
        state = {
            "jobs": {
                "MSG-EXAMPLE-000001": {
                    "state": "DISPATCHED",
                    "pid": 1,
                    "job_root": str(job_root),
                }
            }
        }
        service.reconcile(state)
        self.assertEqual(
            state["jobs"]["MSG-EXAMPLE-000001"]["state"], "COMPLETED"
        )

    def test_exact_aperture_poison_is_dispositioned_and_retry_is_terminal(self):
        config = service.load_config(ROOT / "local-tester-config.json")
        config["mailbox_ref"] = "dcbc94f58989c6b952514880a3061c69d809b3dc"
        snapshot = service.committed_mailbox_snapshot(config)
        self.assertEqual(snapshot["mailbox_head"], config["mailbox_ref"])
        dispositions = snapshot["compatibility_dispositions"]
        self.assertEqual(len(dispositions), 1)
        self.assertEqual(
            dispositions[0]["message_id"], "MSG-T01-APERTURE-BDS-000030"
        )
        self.assertEqual(
            dispositions[0]["current_disposition"],
            "INVALID_SUPERSEDED_TERMINAL",
        )
        self.assertEqual(
            dispositions[0]["raw_message_sha256"],
            "3895ed3602c94686acb2f68b482655b54012fe6dd8dc74f339be65cec934d15a",
        )
        retry = snapshot["terminal_jobs"]["MSG-T01-APERTURE-BDS-RETRY-000031"]
        self.assertEqual(retry["state"], "COMPLETED")
        self.assertEqual(retry["job_id"], "JOB-000000000030")
        self.assertEqual(
            retry["result_raw_sha256"],
            "8a663b4f0e9724c670e80b041034f7486508fddca16a73707ac4a6dc16375a1c",
        )
        self.assertFalse(
            any(
                value["message"].get("message_id")
                in {
                    "MSG-T01-APERTURE-BDS-000030",
                    "MSG-T01-APERTURE-BDS-RETRY-000031",
                }
                for value in snapshot["executable"]
            )
        )

    def test_mailbox_rebuild_removes_stale_poison_and_has_no_active_job(self):
        config = service.load_config(ROOT / "local-tester-config.json")
        config["mailbox_ref"] = "dcbc94f58989c6b952514880a3061c69d809b3dc"
        snapshot = service.committed_mailbox_snapshot(config)
        stale = {
            "jobs": {
                "MSG-T01-APERTURE-BDS-000030": {
                    "state": "DISPATCHED",
                    "pid": 99999999,
                    "pack_id": "aperture-foundry",
                    "job_id": "JOB-000000000030",
                    "job_root": "/nonexistent/poison",
                }
            }
        }
        rebuilt = service.rebuild_runtime_state(stale, snapshot)
        self.assertNotIn("MSG-T01-APERTURE-BDS-000030", rebuilt["jobs"])
        self.assertEqual(
            rebuilt["jobs"]["MSG-T01-APERTURE-BDS-RETRY-000031"]["state"],
            "COMPLETED",
        )
        self.assertFalse(
            any(value["state"] == "DISPATCHED" for value in rebuilt["jobs"].values())
        )

    def test_live_poll_skips_mailbox_terminal_without_job_root_and_dispatches_later(self):
        mailbox = self.repository("mailbox-terminal-then-valid")
        _, request, later = self.fixture()
        terminal = deepcopy(later)
        terminal["message_id"] = "MSG-TERMINAL-INFRA-000001"
        terminal["pack_id"] = "terminal-pack"
        terminal_request = terminal["qualification_request"]
        terminal_request["job_id"] = "JOB-000000000013"
        terminal_request["campaign_id"] = terminal["pack_id"]
        terminal_request["bds"]["port"] = 19219
        terminal_request["bds"]["container_name"] = "terminal-job-13"
        terminal_request["request_payload_sha256"] = service.payload_hash(
            terminal_request, "request_payload_sha256"
        )
        terminal["idempotency_key"] = service.sha256_bytes(
            service.canonical_bytes(
                {
                    "message_id": terminal["message_id"],
                    "pack_id": terminal["pack_id"],
                    "candidate_generation": terminal["candidate_generation"],
                    "request_payload_sha256": terminal_request[
                        "request_payload_sha256"
                    ],
                }
            )
        )
        later["message_id"] = "MSG-LATER-VALID-000002"
        later["idempotency_key"] = service.sha256_bytes(
            service.canonical_bytes(
                {
                    "message_id": later["message_id"],
                    "pack_id": later["pack_id"],
                    "candidate_generation": later["candidate_generation"],
                    "request_payload_sha256": request["request_payload_sha256"],
                }
            )
        )
        terminal_path = (
            mailbox / "tester_intake" / terminal["pack_id"] / "000001.json"
        )
        later_path = mailbox / "tester_intake" / later["pack_id"] / "000002.json"
        result_path = (
            mailbox / "tester_results" / terminal["pack_id"] / "result.json"
        )
        for path, value in (
            (terminal_path, terminal),
            (later_path, later),
            (
                result_path,
                {
                    "message_id": "MSG-TERMINAL-INFRA-RESULT-000001",
                    "message_type": "TEST_FAIL_INFRASTRUCTURE",
                    "parent_message_id": terminal["message_id"],
                },
            ),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            service.write_json(path, value)
        git(mailbox, "add", ".")
        git(mailbox, "commit", "-qm", "terminal result then valid intake")
        config = self.config(mailbox)
        config_path = self.root / "terminal-valid-config.json"
        service.write_json(config_path, config)
        dispatched: list[str] = []

        def fake_dispatch(_config_path, _config, _head, _path, message, state):
            dispatched.append(message["message_id"])
            state.setdefault("jobs", {})[message["message_id"]] = {
                "state": "DISPATCHED",
                "pid": 99999999,
                "pack_id": message["pack_id"],
                "job_id": message["qualification_request"]["job_id"],
                "job_root": str(self.root / "later-job"),
            }

        with mock.patch.object(service, "dispatch", side_effect=fake_dispatch):
            state = service.poll_once(config_path)
        reconstructed = state["jobs"][terminal["message_id"]]
        self.assertEqual(reconstructed["state"], "FAILED")
        self.assertEqual(reconstructed["source"], "COMMITTED_MAILBOX_RESULT")
        self.assertNotIn("job_root", reconstructed)
        self.assertEqual(dispatched, [later["message_id"]])
        self.assertEqual(state["jobs"][later["message_id"]]["state"], "DISPATCHED")

    def test_new_invalid_is_pack_local_and_valid_later_dispatches_once(self):
        mailbox = self.repository("mailbox-poison-sequence")
        product, request, valid = self.fixture()
        invalid = deepcopy(valid)
        invalid["message_id"] = "MSG-AAA-INVALID-000001"
        invalid["pack_id"] = "invalid-pack"
        invalid["qualification_request"]["campaign_id"] = "invalid-pack"
        invalid["qualification_request"]["request_payload_sha256"] = service.payload_hash(
            invalid["qualification_request"], "request_payload_sha256"
        )
        invalid["idempotency_key"] = "0" * 64
        valid["message_id"] = "MSG-ZZZ-VALID-000002"
        valid["idempotency_key"] = service.sha256_bytes(
            service.canonical_bytes(
                {
                    "message_id": valid["message_id"],
                    "pack_id": valid["pack_id"],
                    "candidate_generation": valid["candidate_generation"],
                    "request_payload_sha256": request["request_payload_sha256"],
                }
            )
        )
        for pack, filename, value in (
            ("invalid-pack", "000001.json", invalid),
            ("example-pack", "000002.json", valid),
        ):
            target = mailbox / "tester_intake" / pack / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            service.write_json(target, value)
        git(mailbox, "add", ".")
        git(mailbox, "commit", "-qm", "invalid then valid")
        config = self.config(mailbox)
        config_path = self.root / "tester-config.json"
        service.write_json(config_path, config)
        dispatched: list[str] = []

        def fake_dispatch(_config_path, _config, _head, _path, message, state):
            dispatched.append(message["message_id"])
            state.setdefault("jobs", {})[message["message_id"]] = {
                "state": "DISPATCHED",
                "pid": 99999999,
                "pack_id": message["pack_id"],
                "job_id": message["qualification_request"]["job_id"],
                "job_root": str(self.root / "synthetic-job"),
            }

        with mock.patch.object(service, "dispatch", side_effect=fake_dispatch):
            first = service.poll_once(config_path)
            second = service.poll_once(config_path)
        self.assertEqual(dispatched, ["MSG-ZZZ-VALID-000002"])
        self.assertEqual(len(first["pack_local_rejections"]), 1)
        self.assertEqual(
            first["pack_local_rejections"][0]["message_id"],
            "MSG-AAA-INVALID-000001",
        )
        self.assertEqual(
            second["jobs"]["MSG-ZZZ-VALID-000002"]["state"], "FAILED"
        )


if __name__ == "__main__":
    unittest.main()
