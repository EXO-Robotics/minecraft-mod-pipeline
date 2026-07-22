from __future__ import annotations

import hashlib
import unittest
from datetime import datetime, timezone

from mccompiler.console_evidence import evaluate_platform_statuses, new_platform_statuses
from mccompiler.runtime import EvidenceExpectation, required_checks, validate_runtime_evidence


LOG = b"runtime evidence log\n"
NOW = datetime(2026, 7, 22, 16, 0, tzinfo=timezone.utc)


def expectation(**changes):
    values = {
        "pack_hash": "a" * 64,
        "build_hash": "b" * 64,
        "runtime_id": "bedrock-client-1.21",
        "world_id": "world-showcase-v1",
        "test_id": "marketplace-smoke-v1",
        "now": NOW,
        "max_age_seconds": 3600,
    }
    values.update(changes)
    return EvidenceExpectation(**values)


def complete_evidence():
    return {
        "schema_version": "1.0.0",
        "pack_hash": "a" * 64,
        "build_hash": "b" * 64,
        "runtime_id": "bedrock-client-1.21",
        "world_id": "world-showcase-v1",
        "test_id": "marketplace-smoke-v1",
        "started_at": "2026-07-22T15:30:00Z",
        "ended_at": "2026-07-22T15:45:00Z",
        "log_hash": hashlib.sha256(LOG).hexdigest(),
        "checks": [
            {"check_id": check_id, "classification": classification.value, "status": "PASSED"}
            for check_id, classification in required_checks().items()
        ],
    }


class RuntimeEvidenceTests(unittest.TestCase):
    def test_expectations_require_real_hashes_and_nonempty_identities(self) -> None:
        with self.assertRaisesRegex(ValueError, "pack_hash"):
            expectation(pack_hash="not-a-hash")
        with self.assertRaisesRegex(ValueError, "world_id"):
            expectation(world_id="")

    def test_complete_hash_bound_evidence_passes(self) -> None:
        result = validate_runtime_evidence(complete_evidence(), expectation(), raw_log=LOG)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(7, result["observed_required_check_count"])
        self.assertFalse(result["marketplace_approval_implied"])

    def test_wrong_pack_build_world_runtime_and_test_identity_fail(self) -> None:
        for field in ("pack_hash", "build_hash", "runtime_id", "world_id", "test_id"):
            with self.subTest(field=field):
                evidence = complete_evidence(); evidence[field] = "wrong"
                result = validate_runtime_evidence(evidence, expectation(), raw_log=LOG)
                self.assertFalse(result["valid"])
                self.assertTrue(any(field in error for error in result["errors"]))

    def test_stale_future_reversed_and_wrong_log_evidence_fail(self) -> None:
        stale = complete_evidence(); stale["ended_at"] = "2026-07-22T14:00:00Z"
        self.assertTrue(any("stale" in error for error in validate_runtime_evidence(stale, expectation(), raw_log=LOG)["errors"]))
        future = complete_evidence(); future["ended_at"] = "2026-07-22T17:00:00Z"
        self.assertTrue(any("future" in error for error in validate_runtime_evidence(future, expectation(), raw_log=LOG)["errors"]))
        reversed_time = complete_evidence(); reversed_time["started_at"] = "2026-07-22T15:50:00Z"
        self.assertTrue(any("precedes" in error for error in validate_runtime_evidence(reversed_time, expectation(), raw_log=LOG)["errors"]))
        wrong_log = validate_runtime_evidence(complete_evidence(), expectation(), raw_log=b"different")
        self.assertTrue(any("log_hash" in error for error in wrong_log["errors"]))

    def test_missing_failed_and_misclassified_checks_fail(self) -> None:
        for check_id in ("persistence.migration", "persistence.reconnect", "multiplayer.player_isolation", "console.controller_gameplay"):
            with self.subTest(check_id=check_id):
                evidence = complete_evidence()
                evidence["checks"] = [check for check in evidence["checks"] if check["check_id"] != check_id]
                self.assertTrue(any(check_id in error for error in validate_runtime_evidence(evidence, expectation())["errors"]))
        failed = complete_evidence(); failed["checks"][0]["status"] = "FAILED"
        self.assertTrue(any("did not pass" in error for error in validate_runtime_evidence(failed, expectation())["errors"]))
        wrong_class = complete_evidence(); wrong_class["checks"][0]["classification"] = "gameplay"
        self.assertTrue(any("wrong classification" in error for error in validate_runtime_evidence(wrong_class, expectation())["errors"]))

    def test_reconnect_does_not_substitute_for_migration_or_multiplayer(self) -> None:
        persistence_only = {key: value for key, value in required_checks().items() if key == "persistence.reconnect"}
        evidence = complete_evidence()
        evidence["checks"] = [check for check in evidence["checks"] if check["check_id"] == "persistence.reconnect"]
        self.assertTrue(validate_runtime_evidence(evidence, expectation(), required=persistence_only)["valid"])
        self.assertFalse(validate_runtime_evidence(evidence, expectation())["valid"])


class ConsoleEvidenceTests(unittest.TestCase):
    def test_default_statuses_are_honestly_independent_and_unverified(self) -> None:
        result = new_platform_statuses()
        self.assertFalse(result["console_verified"])
        self.assertEqual({"UNVERIFIED"}, {record["status"] for record in result["platforms"].values()})

    def test_windows_or_realm_success_does_not_verify_consoles(self) -> None:
        result = evaluate_platform_statuses([
            {"platform": "windows_local", "status": "PASSED", "evidence_ids": ["ev-win"]},
            {"platform": "realm_windows", "status": "PASSED", "evidence_ids": ["ev-realm"]},
        ])
        self.assertTrue(result["valid"])
        self.assertFalse(result["console_verified"])
        self.assertEqual("UNVERIFIED", result["platforms"]["ps4"]["status"])
        self.assertEqual("UNVERIFIED", result["platforms"]["xbox_one"]["status"])

    def test_each_console_needs_its_own_evidence(self) -> None:
        playstation_only = evaluate_platform_statuses([
            {"platform": "ps4", "status": "PASSED", "evidence_ids": ["ev-ps4"]},
        ])
        self.assertFalse(playstation_only["console_verified"])
        all_consoles = evaluate_platform_statuses([
            {"platform": "ps4", "status": "PASSED", "evidence_ids": ["ev-ps4"]},
            {"platform": "ps5", "status": "PASSED", "evidence_ids": ["ev-ps5"]},
            {"platform": "xbox_one", "status": "PASSED", "evidence_ids": ["ev-xbox-one"]},
            {"platform": "xbox_series", "status": "PASSED", "evidence_ids": ["ev-xbox-series"]},
        ])
        self.assertTrue(all_consoles["console_verified"])
        self.assertTrue({"PS4_VERIFIED", "PS5_VERIFIED", "XBOX_ONE_VERIFIED", "XBOX_SERIES_VERIFIED"} <= set(all_consoles["verification_statuses"]))
        dishonest = evaluate_platform_statuses([{"platform": "xbox_series", "status": "PASSED", "evidence_ids": []}])
        self.assertFalse(dishonest["valid"])
        self.assertEqual("UNVERIFIED", dishonest["platforms"]["xbox_series"]["status"])


if __name__ == "__main__":
    unittest.main()
