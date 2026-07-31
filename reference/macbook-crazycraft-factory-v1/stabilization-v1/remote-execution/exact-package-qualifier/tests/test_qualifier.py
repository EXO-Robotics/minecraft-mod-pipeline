from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "exact_qualifier", ROOT / "qualify_exact_package.py"
)
assert SPEC and SPEC.loader
q = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(q)


def payload_hash(record, field):
    value = dict(record)
    value.pop(field, None)
    return hashlib.sha256(q.canonical_bytes(value)).hexdigest()


def request():
    result = {
        "schema_version": "crazycraft-remote-v1",
        "job_id": "JOB-000000000012",
        "job_type": "BDS_QUALIFICATION",
        "requesting_authority": "T1",
        "assignment_id": "PA-04-TRAILBOUND-PACKS-V1",
        "campaign_id": "trailbound-packs",
        "exact_input_authorities": [{"authority_type": "PUBLICATION_COMMIT"}],
        "permitted_evidence_roots": [],
        "permitted_candidate_paths": [
            "behavior.mcpack",
            "resource.mcpack",
            "candidate.mcaddon",
            "request.json",
        ],
        "permitted_output_directory": "artifacts",
        "prohibited_disclosure_classes": [
            "RAW_JAVA",
            "DECOMPILED_TEXT",
            "SOURCE_IDENTIFIERS",
            "SOURCE_PATHS",
            "SOURCE_ASSETS",
            "HIDDEN_CASES",
            "PRIVATE_ORACLE_VALUES",
            "CREDENTIALS",
            "SOURCE_EXPRESSION",
        ],
        "timeout_seconds": 900,
        "termination_policy": "TERMINATE_AND_RECEIPT",
        "requested_result_schema": "trailbound-stable-exact-package-v1",
        "bds": {
            "candidate_repository": "trailbound-golden-repair-v2.bundle",
            "candidate_ref": "refs/heads/main",
            "content_commit": "d2d737c5b7110c1c596ce429649fb002efdf9049",
            "content_tree": "47d8d3e409b8cc1b6de49654456f6cee5ddfb201",
            "metadata_commit": "3cfcc28f7a15a8f31413b77ca0cbd6f3c137f5e5",
            "metadata_tree": "f4dfc5db028a709bc89b588b57719ad78b215d8b",
            "behavior_pack_path": "behavior.mcpack",
            "behavior_pack_size": 33229,
            "behavior_pack_sha256": "f26e9daddfd7ba8893f6ccd5934b45ec0f88e1380b3e02038c13051d71fad8f3",
            "resource_pack_path": "resource.mcpack",
            "resource_pack_size": 65207,
            "resource_pack_sha256": "14fcdba454ab5ca85381628d71845dadc80b9c255eb812b7aaebea84814ef7af",
            "mcaddon_path": "candidate.mcaddon",
            "mcaddon_size": 84791,
            "mcaddon_sha256": "949fa581e930460a8bcc8e02f574d1bc89f848a754c57ec84907f07f27372bc4",
            "image_digest": "crazycraft-exact-package-qualifier@sha256:" + "a" * 64,
            "image_platform": "linux/amd64",
            "qualifier_sha256": hashlib.sha256(
                (ROOT / "qualify_exact_package.py").read_bytes()
            ).hexdigest(),
            "bds_channel": "STABLE",
            "bds_version": "1.26.33.2",
            "bds_binary_sha256": q.STABLE_BINARY_SHA256,
            "base_world_sha256": q.BASE_WORLD_SHA256,
            "fixture_set": q.TRAILBOUND_FIXTURE,
            "expected_gates": ["PACK_LOAD", "SHIPPED_ENTRYPOINT", "WORLD_RESTART"],
            "port": 19212,
            "container_name": "factory-trailbound-stable-job-12",
            "cpus": 2,
            "memory_mb": 4096,
        },
        "request_payload_sha256": "",
    }
    result["request_payload_sha256"] = payload_hash(result, "request_payload_sha256")
    return result


def generic_profile():
    return {
        "schema_version": "crazycraft-bds-candidate-profile-v1",
        "behavior_pack": {
            "manifest_uuid": "11111111-1111-4111-8111-111111111111",
            "version": [2, 0, 1],
            "install_directory": "example-bp",
        },
        "resource_pack": {
            "manifest_uuid": "22222222-2222-4222-8222-222222222222",
            "version": [2, 0, 1],
            "install_directory": "example-rp",
        },
        "addon": {
            "behavior_member": "example-behavior.mcpack",
            "resource_member": "example-resource.mcpack",
        },
        "script": {
            "entry_path": "scripts/main.js",
            "expected_marker": "[example] runtime initialized",
        },
        "expected_pack_marker": "Example Behavior",
        "world_name": "Example Exact Package",
        "fixture_id": "EXAMPLE_LOAD_RESTART_V1",
    }


class RequestTests(unittest.TestCase):
    def test_valid_request(self):
        self.assertEqual(q.validate_request(request())["bds_version"], "1.26.33.2")

    def test_missing_field_fails(self):
        value = request()
        value.pop("assignment_id")
        with self.assertRaises(q.QualificationError):
            q.validate_request(value)

    def test_unexpected_field_fails(self):
        value = request()
        value["command"] = "sh"
        with self.assertRaises(q.QualificationError):
            q.validate_request(value)

    def test_payload_hash_fails(self):
        value = request()
        value["campaign_id"] = "changed"
        with self.assertRaises(q.QualificationError):
            q.validate_request(value)

    def test_evidence_mount_fails(self):
        value = request()
        value["permitted_evidence_roots"] = ["/private/oracle"]
        value["request_payload_sha256"] = payload_hash(value, "request_payload_sha256")
        with self.assertRaises(q.QualificationError):
            q.validate_request(value)

    def test_unapproved_image_platform_fails(self):
        value = request()
        value["bds"]["image_platform"] = "linux/arm64"
        value["request_payload_sha256"] = payload_hash(value, "request_payload_sha256")
        with self.assertRaises(q.QualificationError):
            q.validate_request(value)

    def test_generic_candidate_profile_is_accepted(self):
        value = request()
        value["job_id"] = "JOB-000000000013"
        value["campaign_id"] = "example-pack"
        value["bds"]["fixture_set"] = "EXAMPLE_LOAD_RESTART_V1"
        value["bds"]["candidate_profile"] = generic_profile()
        value["request_payload_sha256"] = payload_hash(
            value, "request_payload_sha256"
        )
        observed = q.validate_request(value)
        self.assertEqual(
            observed["_candidate_profile"]["behavior_pack"]["version"],
            [2, 0, 1],
        )

    def test_nonlegacy_request_without_profile_fails(self):
        value = request()
        value["job_id"] = "JOB-000000000013"
        value["request_payload_sha256"] = payload_hash(
            value, "request_payload_sha256"
        )
        with self.assertRaises(q.QualificationError):
            q.validate_request(value)

    def test_asset_only_profile_is_accepted(self):
        profile = generic_profile()
        profile["script"] = None
        self.assertIsNone(q.validate_candidate_profile(profile)["script"])

    def test_addon_member_traversal_fails(self):
        profile = generic_profile()
        profile["addon"]["behavior_member"] = "../escape.mcpack"
        with self.assertRaises(q.QualificationError):
            q.validate_candidate_profile(profile)


class ArchiveTests(unittest.TestCase):
    def make_zip(self, root: Path, name: str, members):
        path = root / name
        with zipfile.ZipFile(path, "w") as archive:
            for member, data in members:
                archive.writestr(member, data)
        return path

    def test_safe_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.make_zip(root, "ok.zip", [("manifest.json", b"{}")])
            destination = root / "out"
            q.safe_extract(archive, destination)
            self.assertEqual((destination / "manifest.json").read_bytes(), b"{}")

    def test_path_traversal_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.make_zip(root, "bad.zip", [("../escape", b"x")])
            with self.assertRaises(q.QualificationError):
                q.safe_extract(archive, root / "out")

    def test_hidden_member_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.make_zip(root, "bad.zip", [(".secret", b"x")])
            with self.assertRaises(q.QualificationError):
                q.safe_extract(archive, root / "out")

    def test_symlink_member_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                info = zipfile.ZipInfo("link")
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                handle.writestr(info, "target")
            with self.assertRaises(q.QualificationError):
                q.safe_extract(archive, root / "out")


class FileTests(unittest.TestCase):
    def test_wrong_hash_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "candidate.mcaddon"
            path.write_bytes(b"candidate")
            with self.assertRaises(q.QualificationError):
                q.validate_regular(path, len(b"candidate"), "0" * 64)

    def test_symlink_input_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            target.write_bytes(b"x")
            link = root / "link"
            link.symlink_to(target)
            with self.assertRaises(q.QualificationError):
                q.validate_regular(link, 1, hashlib.sha256(b"x").hexdigest())


if __name__ == "__main__":
    unittest.main()
