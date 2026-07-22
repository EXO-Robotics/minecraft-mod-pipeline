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
        self.assertIn("ActionFormData", script)
        self.assertIn("if (!await confirmLockRemoval(player)) return", script)
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
import { decideBreak, decideInteraction, removalConfirmed } from './doorlock-state.mjs';
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
  confirmed: removalConfirmed({ canceled: false, selection: 0 }),
  kept: removalConfirmed({ canceled: false, selection: 1 }),
  canceled: removalConfirmed({ canceled: true, selection: 0 }),
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
            "confirmed": True,
            "kept": False,
            "canceled": False,
        }, json.loads(completed.stdout))

    def test_state_records_and_revision_checks_match_the_v1_contract(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required for clean-room state operation tests")
        module_source = RECONSTRUCTION / "custom/scripts/doorlock-state.js"
        with tempfile.TemporaryDirectory() as directory:
            module = Path(directory) / "doorlock-state.mjs"
            shutil.copyfile(module_source, module)
            runner = """
import { buildOwnerLock, createLockIfAbsent, normalizeLockMap, removeLockIfRevision, validateLockMap } from './doorlock-state.mjs';
const location = 'minecraft:nether:-4:65:12';
const record = buildOwnerLock(location, 'player-a', 42);
const created = createLockIfAbsent({}, location, record);
const competingCreate = createLockIfAbsent(created.locks, location, buildOwnerLock(location, 'player-b', 43));
const secondLocation = 'minecraft:nether:9:65:12';
const twoLocks = createLockIfAbsent(created.locks, secondLocation, buildOwnerLock(secondLocation, 'player-b', 44));
const sameCoordinatesOverworld = 'minecraft:overworld:-4:65:12';
const dimensions = createLockIfAbsent(twoLocks.locks, sameCoordinatesOverworld, buildOwnerLock(sameCoordinatesOverworld, 'player-b', 45));
const staleRemove = removeLockIfRevision({ [location]: { ...record, revision: 2 } }, location, 'player-a', 1);
const wrongOwnerRemove = removeLockIfRevision(created.locks, location, 'player-b', 1);
const removed = removeLockIfRevision(created.locks, location, 'player-a', 1);
const validErrors = validateLockMap(dimensions.locks);
const badDimension = validateLockMap({ [location]: { ...record, dimension: 'minecraft:overworld' } });
const badRevision = validateLockMap({ [location]: { ...record, revision: 0 } });
const badMode = validateLockMap({ [location]: { ...record, authorization_mode: 'unknown' } });
const sparse = normalizeLockMap({ [location]: { owner: 'player-a', schema: 1 } });
console.log(JSON.stringify({ record, created, competingCreate, twoLocks, dimensions, staleRemove, wrongOwnerRemove, removed, validErrors, badDimension, badRevision, badMode, sparse, sparseErrors: validateLockMap(sparse.locks) }));
"""
            completed = subprocess.run(
                [node, "--input-type=module", "--eval", runner], cwd=directory,
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual({"x": -4, "y": 65, "z": 12}, result["record"]["position"])
        self.assertEqual("minecraft:nether", result["record"]["dimension"])
        self.assertEqual("owner_identity", result["record"]["authorization_mode"])
        self.assertEqual("player-a", result["record"]["created_by_player_id"])
        self.assertEqual(42, result["record"]["created_at_tick"])
        self.assertEqual(1, result["record"]["revision"])
        self.assertTrue(result["created"]["changed"])
        self.assertFalse(result["competingCreate"]["changed"])
        self.assertEqual("player-a", result["competingCreate"]["locks"]["minecraft:nether:-4:65:12"]["owner"])
        self.assertEqual(2, len(result["twoLocks"]["locks"]))
        self.assertEqual("player-b", result["twoLocks"]["locks"]["minecraft:nether:9:65:12"]["owner"])
        self.assertEqual(3, len(result["dimensions"]["locks"]))
        self.assertEqual("player-b", result["dimensions"]["locks"]["minecraft:overworld:-4:65:12"]["owner"])
        self.assertFalse(result["staleRemove"]["changed"])
        self.assertFalse(result["wrongOwnerRemove"]["changed"])
        self.assertTrue(result["removed"]["changed"])
        self.assertEqual({}, result["removed"]["locks"])
        self.assertEqual([], result["validErrors"])
        self.assertTrue(any("dimension does not match" in error for error in result["badDimension"]))
        self.assertTrue(any("revision must be positive" in error for error in result["badRevision"]))
        self.assertTrue(any("authorization mode is unsupported" in error for error in result["badMode"]))
        self.assertTrue(result["sparse"]["upgraded"])
        self.assertEqual([], result["sparseErrors"])
        self.assertEqual("owner_identity", result["sparse"]["locks"]["minecraft:nether:-4:65:12"]["authorization_mode"])

    def test_every_declared_api_symbol_is_stable_and_marketplace_candidate(self) -> None:
        metadata = json.loads((RECONSTRUCTION / "custom-handler.json").read_text())
        requirements = [
            (row["module"], row["symbol"])
            for handler in metadata["handlers"]
            for row in handler["api_symbols"]
        ]
        versions, evidence = ApiCatalog.load_default().resolve_versions(requirements, marketplace=True)
        self.assertEqual("2.0.0", versions["@minecraft/server"])
        self.assertEqual("2.0.0", versions["@minecraft/server-ui"])
        self.assertEqual(len(requirements), len(evidence))
        self.assertTrue(all(row["stability"] == "stable" and not row["bds_only"] for row in evidence))

    def test_status_exposes_every_unfinished_claim(self) -> None:
        status = json.loads((RECONSTRUCTION / "implementation-status.json").read_text())
        self.assertEqual("PARTIAL_TECHNICAL_RECONSTRUCTION_BDS_UPGRADE_VERIFIED", status["status"])
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
        self.assertEqual("STATIC_AND_BDS_UPGRADE_VERIFIED", validation["status"])
        self.assertEqual(0, validation["creator_tools"]["errors"])
        self.assertEqual(0, validation["creator_tools"]["warnings"])
        self.assertFalse(validation["creator_tools"]["marketplace_approval_implied"])
        self.assertTrue(validation["bds_diagnostic"]["script_initialized"])
        self.assertTrue(validation["bds_diagnostic"]["diagnostic_state_persistence_verified"])
        self.assertTrue(validation["bds_diagnostic"]["empty_state_migration_executed"])
        self.assertTrue(validation["bds_diagnostic"]["nonempty_state_migration_verified"])
        self.assertTrue(validation["bds_diagnostic"]["migrated_state_restart_verified"])
        self.assertEqual(1, validation["bds_diagnostic"]["migrated_lock_records"])
        self.assertFalse(validation["bds_diagnostic"]["feature_persistence_verified"])
        self.assertEqual([1, 2, 3], validation["bds_diagnostic"]["persistent_boot_values"])
        self.assertFalse(validation["bds_diagnostic"]["published_ports"])
        self.assertEqual(validation["artifacts"]["mcworld"]["sha256"], validation["bds_diagnostic"]["world_sha256"])
        self.assertEqual(validation["artifacts"]["legacy_seed_mcworld"]["sha256"], validation["bds_diagnostic"]["legacy_seed_world_sha256"])
        self.assertTrue(validation["artifacts"]["legacy_seed_mcworld"]["fixture_only"])
        self.assertEqual(3, validation["bds_diagnostic"]["restart_cycles"])
        self.assertFalse(validation["marketplace_candidate"]["passed"])
        self.assertIn("actual player item and block event adapters", validation["unverified"])


if __name__ == "__main__":
    unittest.main()
