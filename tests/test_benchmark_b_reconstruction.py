from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from mccompiler.api_catalog import ApiCatalog


ROOT = Path(__file__).resolve().parents[1]
RECONSTRUCTION = ROOT / "benchmarks/rights-cleared-java-mod/reconstruction"


class BenchmarkBReconstructionTests(unittest.TestCase):
    def test_clean_room_script_is_syntax_valid_and_uses_cancellable_events(self) -> None:
        script_path = RECONSTRUCTION / "custom/scripts/doorlock.js"
        script = script_path.read_text(encoding="utf-8")
        self.assertIn("world.beforeEvents.playerInteractWithBlock.subscribe", script)
        self.assertIn("world.beforeEvents.playerBreakBlock.subscribe", script)
        self.assertIn("event.cancel = true", script)
        self.assertIn("system.run(() =>", script)
        self.assertIn("persistent_boot=${current}", script)
        self.assertNotIn("password", script.lower())
        self.assertNotIn("src/main/java", script)
        node = shutil.which("node")
        if node:
            completed = subprocess.run([node, "--check", str(script_path)], capture_output=True, text=True, check=False)
            self.assertEqual(0, completed.returncode, completed.stderr)

    def test_legacy_state_migration_is_idempotent_and_fail_closed(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required for clean-room migration logic tests")
        module_source = RECONSTRUCTION / "custom/scripts/doorlock-state.js"
        with tempfile.TemporaryDirectory() as directory:
            module = Path(directory) / "doorlock-state.mjs"
            shutil.copyfile(module_source, module)
            runner = """
import { migrateLegacyState } from './doorlock-state.mjs';
const cases = {};
cases.empty = migrateLegacyState([]);
cases.single = migrateLegacyState(['1,2,3_abcd']);
cases.malformed = migrateLegacyState(['bad']);
cases.same = migrateLegacyState(['1,2,3_abcd', '1,2,3_abcd']);
cases.conflict = migrateLegacyState(['1,2,3_abcd', '1,2,3_efgh']);
cases.nonOverworld = migrateLegacyState(['1,2,3_abcd'], {}, { dimension: 'minecraft:nether' });
cases.second = migrateLegacyState(['1,2,3_abcd'], cases.single.locks);
console.log(JSON.stringify(cases));
"""
            completed = subprocess.run(
                [node, "--input-type=module", "--eval", runner], cwd=directory,
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
        cases = json.loads(completed.stdout)
        self.assertEqual({}, cases["empty"]["locks"])
        self.assertEqual(1, cases["single"]["stats"]["imported"])
        record = cases["single"]["locks"]["minecraft:overworld:1:2:3"]
        self.assertEqual("legacy-unclaimed", record["owner"])
        self.assertEqual("abcd", record["credential_digest"])
        self.assertNotIn("password", record)
        self.assertEqual("malformed_legacy_entry", cases["malformed"]["quarantine"][0]["error"])
        self.assertEqual(1, cases["same"]["stats"]["deduplicated"])
        self.assertEqual({}, cases["conflict"]["locks"])
        self.assertEqual(2, cases["conflict"]["stats"]["quarantined"])
        self.assertEqual("non_overworld_mapping_requires_approval", cases["nonOverworld"]["quarantine"][0]["error"])
        self.assertEqual(cases["single"]["locks"], cases["second"]["locks"])
        self.assertEqual(0, cases["second"]["stats"]["imported"])

    def test_authorization_handler_preserves_two_player_isolation(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required for clean-room authorization logic tests")
        module_source = RECONSTRUCTION / "custom/scripts/doorlock-state.js"
        with tempfile.TemporaryDirectory() as directory:
            module = Path(directory) / "doorlock-state.mjs"
            shutil.copyfile(module_source, module)
            runner = """
import { decideBreak, decideInteraction } from './doorlock-state.mjs';
const owner = 'player-a';
const stranger = 'player-b';
const lock = { owner, schema: 1 };
const decide = (playerId, itemId, isSneaking = false, current = lock) =>
  decideInteraction({ lock: current, playerId, itemId, isSneaking }).action;
console.log(JSON.stringify({
  create: decide(owner, 'door_lock:key', false, null),
  ownerOpen: decide(owner, undefined),
  strangerDenied: decide(stranger, undefined),
  strangerKeyDenied: decide(stranger, 'door_lock:key'),
  ownerUnlock: decide(owner, 'door_lock:key', true),
  strangerUnlockDenied: decide(stranger, 'door_lock:key', true),
  universalOpen: decide(stranger, 'door_lock:universal_key'),
  universalUnlock: decide(stranger, 'door_lock:universal_key', true),
  lockedBreak: decideBreak(lock).action,
  unlockedBreak: decideBreak(undefined).action,
}));
"""
            completed = subprocess.run(
                [node, "--input-type=module", "--eval", runner], cwd=directory,
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual({
            "create": "CREATE_LOCK",
            "ownerOpen": "ALLOW_OPEN",
            "strangerDenied": "DENY_LOCKED",
            "strangerKeyDenied": "DENY_LOCKED",
            "ownerUnlock": "REMOVE_LOCK",
            "strangerUnlockDenied": "DENY_LOCKED",
            "universalOpen": "ALLOW_OPEN",
            "universalUnlock": "REMOVE_LOCK",
            "lockedBreak": "DENY_LOCKED",
            "unlockedBreak": "ALLOW_BREAK",
        }, json.loads(completed.stdout))

    def test_every_declared_api_symbol_is_stable_and_marketplace_candidate(self) -> None:
        metadata = json.loads((RECONSTRUCTION / "custom-handler.json").read_text())
        requirements = [
            (row["module"], row["symbol"])
            for handler in metadata["handlers"]
            for row in handler["api_symbols"]
        ]
        versions, evidence = ApiCatalog.load_default().resolve_versions(requirements, marketplace=True)
        self.assertEqual("2.0.0", versions["@minecraft/server"])
        self.assertEqual(len(requirements), len(evidence))
        self.assertTrue(all(row["stability"] == "stable" and not row["bds_only"] for row in evidence))

    def test_status_exposes_every_unfinished_claim(self) -> None:
        status = json.loads((RECONSTRUCTION / "implementation-status.json").read_text())
        self.assertEqual("PARTIAL_TECHNICAL_RECONSTRUCTION_BDS_BOOT_VERIFIED", status["status"])
        self.assertIsNone(status["approved_quality_claim"])
        self.assertGreater(len(status["missing"]), 5)
        self.assertFalse(status["claims"]["technical_reconstruction_complete"])
        self.assertFalse(status["claims"]["runtime_verified"])
        self.assertTrue(status["claims"]["bds_boot_verified"])
        self.assertTrue(status["claims"]["creator_tools_passed"])
        self.assertFalse(status["claims"]["rights_cleared"])
        self.assertFalse(status["claims"]["marketplace_candidate"])
        self.assertFalse(status["claims"]["console_verified"])
        redesign = status["intentional_redesigns"][0]
        self.assertEqual("PROPOSED_NOT_APPROVED", redesign["status"])
        self.assertTrue(redesign["lost"])

    def test_external_validation_is_hash_bound_and_narrow(self) -> None:
        validation = json.loads((RECONSTRUCTION / "technical-build-validation.json").read_text())
        self.assertEqual("STATIC_AND_BDS_BOOT_VERIFIED", validation["status"])
        self.assertEqual(0, validation["creator_tools"]["errors"])
        self.assertEqual(0, validation["creator_tools"]["warnings"])
        self.assertFalse(validation["creator_tools"]["marketplace_approval_implied"])
        self.assertTrue(validation["bds_diagnostic"]["script_initialized"])
        self.assertTrue(validation["bds_diagnostic"]["diagnostic_state_persistence_verified"])
        self.assertFalse(validation["bds_diagnostic"]["feature_persistence_verified"])
        self.assertEqual([1, 2], validation["bds_diagnostic"]["persistent_boot_values"])
        self.assertFalse(validation["bds_diagnostic"]["published_ports"])
        self.assertEqual(validation["artifacts"]["mcworld"]["sha256"], validation["bds_diagnostic"]["world_sha256"])
        self.assertFalse(validation["marketplace_candidate"]["passed"])
        self.assertIn("actual player item and block event adapters", validation["unverified"])


if __name__ == "__main__":
    unittest.main()
