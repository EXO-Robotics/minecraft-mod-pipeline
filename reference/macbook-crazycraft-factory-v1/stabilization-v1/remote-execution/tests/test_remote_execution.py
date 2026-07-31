#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "macbook"))
sys.path.insert(0, str(ROOT / "studio"))
sys.path.insert(0, str(ROOT / "tools"))

from remote_job_lib import (  # noqa: E402
    PROHIBITED_DISCLOSURE_CLASSES,
    ValidationError,
    build_bds_docker_argv,
    canonical_bytes,
    disclosure_scan,
    payload_hash,
    sha256_file,
    validate_request,
    validate_safe_relative_path,
    verify_worker_environment,
    write_json,
)
from remote_jobs import (  # noqa: E402
    encode_transfer,
    local_retrieve,
    local_submit,
    validate_local_bundle,
)
from remote_job_entrypoint import _canonical_bds_result, process_job  # noqa: E402
from validate_remote_record import validate_receipt, validate_result  # noqa: E402


def make_request(job_id: str, role: str, job_type: str) -> dict:
    request = {
        "schema_version": "crazycraft-remote-v1",
        "job_id": job_id,
        "job_type": job_type,
        "requesting_authority": role,
        "assignment_id": f"A-{role}-SYNTHETIC-0001",
        "campaign_id": "synthetic-boundary-fixture",
        "exact_input_authorities": [
            {
                "authority_id": "SYNTHETIC-INPUT-001",
                "classification": "NON_SENSITIVE_FIXTURE",
            }
        ],
        "permitted_evidence_roots": ["/synthetic/evidence"]
        if job_type in {"EVIDENCE_RECOVERY", "PRIVATE_CANDIDATE_AUDIT"}
        else [],
        "permitted_candidate_paths": ["inputs/candidate.mcaddon"]
        if job_type != "EVIDENCE_RECOVERY"
        else [],
        "permitted_output_directory": "artifacts",
        "prohibited_disclosure_classes": sorted(PROHIBITED_DISCLOSURE_CLASSES),
        "timeout_seconds": 60,
        "termination_policy": "TERMINATE_AND_RECEIPT",
        "requested_result_schema": "synthetic-result-v1",
        "request_payload_sha256": "",
    }
    if job_type in {"BDS_QUALIFICATION", "COMBINED_PRIVATE_AUDIT_AND_QUALIFICATION"}:
        request["permitted_candidate_paths"] = [
            "behavior.mcpack",
            "resource.mcpack",
            "candidate.mcaddon",
            "request.json",
        ]
        request["bds"] = {
            "candidate_repository": "synthetic-repository",
            "candidate_ref": "refs/heads/synthetic",
            "content_commit": "1" * 64,
            "content_tree": "2" * 64,
            "metadata_commit": "7" * 64,
            "metadata_tree": "8" * 64,
            "behavior_pack_path": "behavior.mcpack",
            "behavior_pack_size": 10,
            "behavior_pack_sha256": "3" * 64,
            "resource_pack_path": "resource.mcpack",
            "resource_pack_size": 11,
            "resource_pack_sha256": "4" * 64,
            "mcaddon_path": "candidate.mcaddon",
            "mcaddon_size": 12,
            "mcaddon_sha256": "5" * 64,
            "image_digest": "synthetic-bds@sha256:" + "6" * 64,
            "image_platform": "linux/amd64",
            "qualifier_sha256": "9" * 64,
            "bds_channel": "STABLE",
            "bds_version": "synthetic-1",
            "bds_binary_sha256": "a" * 64,
            "base_world_sha256": "b" * 64,
            "fixture_set": "synthetic-fixture-v1",
            "expected_gates": ["PACKAGE_LOAD", "RESTART"],
            "port": 19132 + int(job_id[-2:]),
            "container_name": "synthetic-" + job_id.lower(),
            "cpus": 1,
            "memory_mb": 512,
        }
    request["request_payload_sha256"] = payload_hash(
        request, "request_payload_sha256"
    )
    return request


def make_bundle(base: Path, request: dict, content: bytes = b"synthetic input\n") -> Path:
    bundle = base / request["job_id"]
    (bundle / "inputs").mkdir(parents=True)
    input_path = bundle / "inputs" / "candidate.mcaddon"
    input_path.write_bytes(content)
    write_json(bundle / "request.json", request)
    (bundle / "request.sha256").write_text(sha256_file(bundle / "request.json") + "\n")
    manifest = {
        "schema_version": "crazycraft-remote-v1",
        "job_id": request["job_id"],
        "entries": [
            {
                "relative_path": "candidate.mcaddon",
                "sha256": sha256_file(input_path),
                "size_bytes": input_path.stat().st_size,
                "content_role": "SYNTHETIC_FIXTURE",
            }
        ],
        "manifest_payload_sha256": "",
    }
    manifest["manifest_payload_sha256"] = payload_hash(
        manifest, "manifest_payload_sha256"
    )
    write_json(bundle / "input-manifest.json", manifest)
    return bundle


class RemoteExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="crazycraft-remote-test-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def test_01_t1_evidence_submit_and_sanitized_return(self):
        bundle = make_bundle(
            self.tmp / "local",
            make_request("JOB-000000000001", "T1", "EVIDENCE_RECOVERY"),
        )
        remote = self.tmp / "remote"
        self.assertEqual(local_submit(bundle, remote, "T1", True), 0)
        result = json.loads(
            (remote / "completed" / bundle.name / "result.json").read_text()
        )
        self.assertEqual(result["outcome"], "PASS")
        self.assertEqual(result["disclosure_scan"]["status"], "PASS")

    def test_02_sanitized_result_has_no_prohibited_markers(self):
        bundle = make_bundle(
            self.tmp / "local",
            make_request("JOB-000000000001", "T1", "EVIDENCE_RECOVERY"),
        )
        remote = self.tmp / "remote"
        local_submit(bundle, remote, "T1", True)
        scan = disclosure_scan([remote / "completed" / bundle.name / "result.json"])
        self.assertEqual(scan["status"], "PASS")

    def test_03_worker_can_consume_only_sanitized_result(self):
        bundle = make_bundle(
            self.tmp / "local",
            make_request("JOB-000000000001", "T1", "EVIDENCE_RECOVERY"),
        )
        remote = self.tmp / "remote"
        local_submit(bundle, remote, "T1", True)
        destination = self.tmp / "worker-result"
        local_retrieve(remote, bundle.name, destination)
        result = json.loads((destination / "result.json").read_text())
        self.assertTrue(result["opaque_contract_ids"])
        self.assertFalse((destination / "inputs").exists())

    def test_04_worker_environment_rejects_ssh_agent(self):
        with self.assertRaises(ValidationError):
            verify_worker_environment({"SSH_AUTH_SOCK": "/tmp/agent"}, [])

    def test_05_worker_environment_rejects_readable_privileged_key(self):
        key = self.tmp / "t1-key"
        key.write_text("synthetic")
        with self.assertRaises(ValidationError):
            verify_worker_environment({}, [key])

    def test_06_t10_private_audit_returns_opaque_finding(self):
        bundle = make_bundle(
            self.tmp / "local",
            make_request("JOB-000000000001", "T10", "PRIVATE_CANDIDATE_AUDIT"),
        )
        remote = self.tmp / "remote"
        self.assertEqual(local_submit(bundle, remote, "T10", True), 0)
        result = json.loads(
            (remote / "completed" / bundle.name / "result.json").read_text()
        )
        self.assertEqual(result["opaque_finding_ids"], ["FINDING-SYNTHETIC-001"])
        self.assertNotIn("private-oracle-value:", canonical_bytes(result).decode())

    def test_07_private_oracle_markers_blocked(self):
        output = self.tmp / "output.txt"
        output.write_text("private-oracle-value: synthetic-secret")
        self.assertEqual(disclosure_scan([output])["status"], "FAIL")

    def test_08_bds_argv_mounts_only_job_inputs_and_outputs(self):
        request = make_request("JOB-000000000001", "T10", "BDS_QUALIFICATION")
        job_root = self.tmp / "job"
        (job_root / "inputs").mkdir(parents=True)
        (job_root / "artifacts").mkdir()
        argv = build_bds_docker_argv(request, job_root)
        joined = "\n".join(argv)
        self.assertIn(str((job_root / "inputs").resolve()), joined)
        self.assertIn(str((job_root / "artifacts").resolve()), joined)
        self.assertNotIn("/synthetic/evidence", joined)
        self.assertNotIn(".ssh", joined)

    def test_09_bds_argv_has_hardening_controls(self):
        request = make_request("JOB-000000000001", "T10", "BDS_QUALIFICATION")
        job_root = self.tmp / "job"
        (job_root / "inputs").mkdir(parents=True)
        (job_root / "artifacts").mkdir()
        argv = build_bds_docker_argv(request, job_root)
        for token in ("none", "ALL", "no-new-privileges", "65532:65532", "256"):
            self.assertIn(token, argv)

    def test_10_two_bds_jobs_have_disjoint_resources(self):
        requests = [
            make_request(f"JOB-{index:012d}", "T10", "BDS_QUALIFICATION")
            for index in (1, 2)
        ]
        roots = [self.tmp / f"job-{index}" for index in (1, 2)]
        for root in roots:
            (root / "inputs").mkdir(parents=True)
            (root / "artifacts").mkdir()
        commands: list[list[str]] = []

        def build(index: int):
            commands.append(build_bds_docker_argv(requests[index], roots[index]))

        threads = [threading.Thread(target=build, args=(index,)) for index in (0, 1)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(commands), 2)
        self.assertNotEqual(requests[0]["bds"]["port"], requests[1]["bds"]["port"])
        self.assertNotEqual(
            requests[0]["bds"]["container_name"], requests[1]["bds"]["container_name"]
        )
        self.assertNotEqual(str(roots[0]), str(roots[1]))

    def test_11_wrong_package_hash_fails_before_execution(self):
        request = make_request("JOB-000000000001", "T1", "EVIDENCE_RECOVERY")
        bundle = make_bundle(self.tmp / "local", request)
        manifest = json.loads((bundle / "input-manifest.json").read_text())
        manifest["entries"][0]["sha256"] = "0" * 64
        manifest["manifest_payload_sha256"] = payload_hash(
            manifest, "manifest_payload_sha256"
        )
        write_json(bundle / "input-manifest.json", manifest)
        with self.assertRaises(ValidationError):
            validate_local_bundle(bundle, "T1")

    def test_12_duplicate_job_id_fails(self):
        bundle = make_bundle(
            self.tmp / "local",
            make_request("JOB-000000000001", "T1", "EVIDENCE_RECOVERY"),
        )
        remote = self.tmp / "remote"
        local_submit(bundle, remote, "T1", True)
        with self.assertRaises(ValidationError):
            local_submit(bundle, remote, "T1", True)

    def test_13_path_traversal_fails(self):
        for value in ("../secret", "/absolute", "a\\..\\secret", ".hidden"):
            with self.assertRaises(ValidationError):
                validate_safe_relative_path(value)

    def test_14_unauthorized_job_type_fails(self):
        request = make_request("JOB-000000000001", "T1", "EVIDENCE_RECOVERY")
        request["job_type"] = "ARBITRARY_SHELL"
        request["request_payload_sha256"] = payload_hash(
            request, "request_payload_sha256"
        )
        with self.assertRaises(ValidationError):
            validate_request(request, "T1")

    def test_15_t1_cannot_submit_private_audit(self):
        request = make_request("JOB-000000000001", "T1", "EVIDENCE_RECOVERY")
        request["job_type"] = "PRIVATE_CANDIDATE_AUDIT"
        request["request_payload_sha256"] = payload_hash(
            request, "request_payload_sha256"
        )
        with self.assertRaises(ValidationError):
            validate_request(request, "T1")

    def test_16_retrieval_never_returns_raw_inputs(self):
        bundle = make_bundle(
            self.tmp / "local",
            make_request("JOB-000000000001", "T10", "PRIVATE_CANDIDATE_AUDIT"),
        )
        remote = self.tmp / "remote"
        local_submit(bundle, remote, "T10", True)
        destination = self.tmp / "retrieved"
        local_retrieve(remote, bundle.name, destination)
        self.assertFalse((destination / "inputs").exists())
        self.assertFalse((destination / "logs").exists())

    def test_17_failed_job_moves_to_failed_with_receipt(self):
        request = make_request("JOB-000000000001", "T1", "EVIDENCE_RECOVERY")
        bundle = make_bundle(self.tmp / "bundle", request)
        remote = self.tmp / "remote"
        (remote / "incoming").mkdir(parents=True)
        for name in ("active", "completed", "failed", "templates", "runtime"):
            (remote / name).mkdir()
        shutil.copytree(bundle, remote / "incoming" / bundle.name)
        manifest = json.loads(
            (remote / "incoming" / bundle.name / "input-manifest.json").read_text()
        )
        manifest["entries"][0]["sha256"] = "0" * 64
        manifest["manifest_payload_sha256"] = payload_hash(
            manifest, "manifest_payload_sha256"
        )
        write_json(remote / "incoming" / bundle.name / "input-manifest.json", manifest)
        self.assertEqual(process_job(remote, "T1", bundle.name, synthetic=True), 1)
        failed = remote / "failed" / bundle.name
        self.assertTrue((failed / "receipt.json").is_file())
        self.assertEqual(json.loads((failed / "receipt.json").read_text())["exit_status"], 1)

    def test_18_nonmonotonic_job_id_fails(self):
        bundle = make_bundle(
            self.tmp / "local",
            make_request("JOB-000000000002", "T1", "EVIDENCE_RECOVERY"),
        )
        remote = self.tmp / "remote"
        self.assertEqual(local_submit(bundle, remote, "T1", True), 1)
        self.assertTrue((remote / "failed" / bundle.name / "receipt.json").is_file())

    def test_19_request_payload_tampering_fails(self):
        request = make_request("JOB-000000000001", "T1", "EVIDENCE_RECOVERY")
        request["campaign_id"] = "tampered"
        with self.assertRaises(ValidationError):
            validate_request(request, "T1")

    def test_20_result_receipt_hashes_are_present(self):
        bundle = make_bundle(
            self.tmp / "local",
            make_request("JOB-000000000001", "T1", "EVIDENCE_RECOVERY"),
        )
        remote = self.tmp / "remote"
        local_submit(bundle, remote, "T1", True)
        receipt = json.loads(
            (remote / "completed" / bundle.name / "receipt.json").read_text()
        )
        self.assertRegex(receipt["request_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(receipt["input_manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(receipt["receipt_payload_sha256"], r"^[0-9a-f]{64}$")

    def test_21_framed_ingest_uses_manifest_declared_files(self):
        bundle = make_bundle(
            self.tmp / "local",
            make_request("JOB-000000000001", "T1", "EVIDENCE_RECOVERY"),
        )
        remote = self.tmp / "remote"
        entrypoint = ROOT / "studio" / "remote_job_entrypoint.py"
        completed = __import__("subprocess").run(
            [
                sys.executable,
                str(entrypoint),
                "ingest",
                "T1",
                bundle.name,
                "--root",
                str(remote),
            ],
            input=encode_transfer(bundle),
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(
            (remote / "incoming" / bundle.name / "inputs" / "candidate.mcaddon").read_bytes(),
            b"synthetic input\n",
        )

    def test_22_forced_command_rejects_shell_injection(self):
        forced = ROOT / "studio" / "forced_command.py"
        completed = __import__("subprocess").run(
            [sys.executable, str(forced), "--expected-role", "T1", "--root", str(self.tmp)],
            env={
                "SSH_ORIGINAL_COMMAND": "/usr/local/libexec/crazycraft-remote-entry status T1 JOB-000000000001;id"
            },
            check=False,
        )
        self.assertEqual(completed.returncode, 126)

    def test_23_forced_command_rejects_role_confusion(self):
        forced = ROOT / "studio" / "forced_command.py"
        completed = __import__("subprocess").run(
            [sys.executable, str(forced), "--expected-role", "T1", "--root", str(self.tmp)],
            env={
                "SSH_ORIGINAL_COMMAND": "/usr/local/libexec/crazycraft-remote-entry status T10 JOB-000000000001"
            },
            check=False,
        )
        self.assertEqual(completed.returncode, 126)

    def test_24_result_and_receipt_contracts_validate(self):
        bundle = make_bundle(
            self.tmp / "local",
            make_request("JOB-000000000001", "T1", "EVIDENCE_RECOVERY"),
        )
        remote = self.tmp / "remote"
        local_submit(bundle, remote, "T1", True)
        terminal = remote / "completed" / bundle.name
        validate_result(json.loads((terminal / "result.json").read_text()))
        validate_receipt(json.loads((terminal / "receipt.json").read_text()))

    def test_25_detailed_bds_result_is_wrapped_in_canonical_envelope(self):
        request = make_request(
            "JOB-000000000001", "T1", "BDS_QUALIFICATION"
        )
        detailed = {
            "outcome": "PASS",
            "abstract_results": [
                {
                    "qualification": "STABLE_BDS_EXACT_PACKAGE_LOAD_RESTART",
                    "status": "PASS",
                }
            ],
            "opaque_contract_ids": [],
            "opaque_finding_ids": [],
            "required_regression_ids": [],
            "qualification_references": ["SYNTHETIC-BDS-001"],
            "external_gates_not_run": ["BEDROCK_CLIENT"],
            "proof_boundary": "Synthetic canonical-envelope fixture only.",
            "candidate": {"unexpected_outer_field": True},
        }
        result = _canonical_bds_result(request, detailed)
        validate_result(result)
        self.assertNotIn("candidate", result)
        self.assertEqual(
            result["qualification_references"], ["SYNTHETIC-BDS-001"]
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
