from __future__ import annotations

import hashlib
import json
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bedrock_factory.identity import IdentityError, LifecycleIdentity, identity
from bedrock_factory.platform_authority import (
    NEW_AUTHORITY_TRIGGERS,
    PLATFORM_SCHEMA,
    REQUIRED_CANARY_STEPS,
    REQUIRED_PLATFORM_COMPONENTS,
    STANDING_AUTHORITY_SCHEMA,
    document_sha256,
    resolve_standing_launch_authority,
)
from bedrock_factory.shadow_admission import inspect_mcaddon


H = "a" * 64


def platform_receipt() -> dict:
    receipt = {
        "schema_version": PLATFORM_SCHEMA,
        "qualification_id": "FPQ-fixture-v1",
        "status": "PASS",
        "components": {name: H for name in sorted(REQUIRED_PLATFORM_COMPONENTS)},
        "canary_steps": {name: "PASS" for name in sorted(REQUIRED_CANARY_STEPS)},
        "process_receipt_sha256": H,
        "cleanup_receipt_sha256": H,
    }
    receipt["canonical_payload_sha256"] = document_sha256(receipt)
    return receipt


def standing_fixture() -> tuple[dict, dict, dict]:
    platform = platform_receipt()
    authority = {
        "schema_version": STANDING_AUTHORITY_SCHEMA,
        "authority_id": "authority-fixture-v1",
        "state": "ACTIVE",
        "visibility": "PRIVATE_FACTORY_ONLY",
        "campaign_id": "campaign-one",
        "source_authority_sha256": "1" * 64,
        "rights_authority_sha256": "2" * 64,
        "security_model_sha256": "3" * 64,
        "platform_qualification_sha256": document_sha256(platform),
    }
    activation = {
        "activation_id": "A1",
        "candidate_id": "C1",
        "activation_type": "NEW_PACK",
        "campaign_id": authority["campaign_id"],
        "source_authority_sha256": authority["source_authority_sha256"],
        "rights_authority_sha256": authority["rights_authority_sha256"],
        "security_model_sha256": authority["security_model_sha256"],
        "candidate_sha256": "4" * 64,
        "product_bytes_changed": True,
        "requested_new_authority_triggers": [],
    }
    return authority, activation, platform


class KernelAuthorityTests(unittest.TestCase):
    def test_same_security_model_allows_new_candidate_hash(self) -> None:
        authority, activation, platform = standing_fixture()
        first = resolve_standing_launch_authority(authority, activation, platform)
        activation["activation_id"] = "A2"
        activation["candidate_id"] = "C2"
        activation["candidate_sha256"] = "5" * 64
        second = resolve_standing_launch_authority(authority, activation, platform)
        self.assertEqual((first["status"], second["status"]), ("PASS", "PASS"))

    def test_changed_security_model_requires_new_authority(self) -> None:
        authority, activation, platform = standing_fixture()
        activation["security_model_sha256"] = "9" * 64
        result = resolve_standing_launch_authority(authority, activation, platform)
        self.assertEqual(result["error"]["code"], "AUTHORITY_HASH_MISMATCH")
        self.assertTrue(result["new_authority_required"])

    def test_recovery_with_unchanged_product_bytes_is_routine(self) -> None:
        authority, activation, platform = standing_fixture()
        activation.update(
            activation_id="A7",
            activation_type="RECOVERY_AFTER_INTERRUPTION",
            product_bytes_changed=False,
        )
        self.assertEqual(resolve_standing_launch_authority(authority, activation, platform)["status"], "PASS")

    def test_realms_and_authenticated_identity_require_new_authority(self) -> None:
        for trigger in ("REALMS", "AUTHENTICATED_IDENTITY"):
            with self.subTest(trigger=trigger):
                authority, activation, platform = standing_fixture()
                self.assertIn(trigger, NEW_AUTHORITY_TRIGGERS)
                activation["requested_new_authority_triggers"] = [trigger]
                result = resolve_standing_launch_authority(authority, activation, platform)
                self.assertEqual(result["error"]["code"], "NEW_AUTHORITY_REQUIRED")

    def test_platform_canary_fails_closed_without_broker_proof(self) -> None:
        authority, activation, platform = standing_fixture()
        platform["canary_steps"]["PRIVILEGED_BROKER_OPERATION_PROVED"] = "FAIL"
        normalized = dict(platform)
        normalized.pop("canonical_payload_sha256")
        platform["canonical_payload_sha256"] = document_sha256(normalized)
        result = resolve_standing_launch_authority(authority, activation, platform)
        self.assertEqual(result["error"]["code"], "PLATFORM_UNQUALIFIED")

    def test_identity_namespaces_cannot_be_collapsed(self) -> None:
        self.assertEqual(identity("candidate", 5), "C5")
        self.assertEqual(identity("activation", 25), "A25")
        LifecycleIdentity("C5", "A25", "HOST_AUTHORITY_REBIND").validate()
        with self.assertRaises(IdentityError):
            LifecycleIdentity("A5", "A25", "PRODUCT_CANDIDATE").validate()

    def test_shadow_admission_catches_icons_symlinks_and_entrypoints(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "fixture.mcaddon"
            manifest = {
                "format_version": 2,
                "header": {"name": "Fixture", "uuid": "11111111-1111-1111-1111-111111111111", "version": [1, 0, 0]},
                "modules": [{"type": "script", "uuid": "22222222-2222-2222-2222-222222222222", "version": [1, 0, 0], "entry": "scripts/main.js"}],
            }
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("BP/manifest.json", json.dumps(manifest))
                symlink = zipfile.ZipInfo("BP/linked")
                symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
                bundle.writestr(symlink, "elsewhere")
            result = inspect_mcaddon(archive)
            self.assertEqual(result["authority"], "NON_AUTHORITATIVE_PRODUCER_SHADOW")
            self.assertTrue(result["independent_t1_still_required"])
            self.assertEqual(
                {finding["code"] for finding in result["findings"]},
                {"FORBIDDEN_SPECIAL_FILE", "PACK_ICON_MISSING", "SCRIPT_ENTRYPOINT_MISSING"},
            )


if __name__ == "__main__":
    unittest.main()
