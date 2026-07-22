from __future__ import annotations

import json
import hashlib
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
        self.assertIn("world.afterEvents.playerBreakBlock.subscribe", script)
        self.assertIn("function rawBreakKey(block)", script)
        self.assertNotIn("rawBreakKey(event.player", script)
        self.assertIn("world.afterEvents.playerInteractWithBlock.subscribe", script)
        self.assertIn("system.runTimeout", script)
        self.assertIn("system.runInterval(reconcileLockedOpenables, 1)", script)
        self.assertIn("REDSTONE_RECONCILE_BUDGET = 32", script)
        self.assertIn("const locations = lockLocationCache", script)
        self.assertIn("if (lockCacheReady) return lockCache", script)
        self.assertIn("state(block, 'open_bit')", script)
        self.assertIn("state(block, 'upper_block_bit')", script)
        self.assertNotIn("minecraft:open_bit", script)
        self.assertNotIn("minecraft:upper_block_bit", script)
        self.assertIn("removeLockIfRevision", script)
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
import { migrateLegacyState, prepareLegacyMigration, resumePreparedMigration } from './doorlock-state.mjs';
const cases = {};
cases.empty = migrateLegacyState([]);
cases.single = migrateLegacyState(['1,2,3_abcd']);
cases.malformed = migrateLegacyState(['bad']);
cases.same = migrateLegacyState(['1,2,3_abcd', '1,2,3_abcd']);
cases.conflict = migrateLegacyState(['1,2,3_abcd', '1,2,3_efgh']);
cases.nonOverworld = migrateLegacyState(['1,2,3_abcd'], {}, { dimension: 'minecraft:nether' });
cases.second = migrateLegacyState(['1,2,3_abcd'], cases.single.locks);
cases.prepared = prepareLegacyMigration(['1,2,3_abcd'], {});
cases.resumeBeforeWrite = resumePreparedMigration(['1,2,3_abcd'], {}, cases.prepared.journal);
cases.resumeAfterStateWrite = resumePreparedMigration(['1,2,3_abcd'], cases.prepared.locks, cases.prepared.journal);
cases.changedLegacy = resumePreparedMigration(['1,2,3_changed'], {}, cases.prepared.journal);
cases.divergedCurrent = resumePreparedMigration(['1,2,3_abcd'], { unexpected: {} }, cases.prepared.journal);
cases.tamperedJournal = resumePreparedMigration(['1,2,3_abcd'], {}, { ...cases.prepared.journal, result_digest: '0'.repeat(64) });
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
        self.assertEqual("prepared", cases["prepared"]["journal"]["status"])
        self.assertTrue(cases["resumeBeforeWrite"]["ok"])
        self.assertTrue(cases["resumeAfterStateWrite"]["ok"])
        self.assertEqual(cases["prepared"]["locks"], cases["resumeBeforeWrite"]["locks"])
        self.assertEqual(cases["prepared"]["locks"], cases["resumeAfterStateWrite"]["locks"])
        self.assertEqual("completed", cases["resumeAfterStateWrite"]["journal"]["status"])
        self.assertEqual("legacy_payload_changed", cases["changedLegacy"]["error"])
        self.assertEqual("current_state_diverged", cases["divergedCurrent"]["error"])
        self.assertEqual("result_digest_mismatch", cases["tamperedJournal"]["error"])

    def test_authorization_handler_preserves_two_player_isolation(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required for clean-room authorization logic tests")
        module_source = RECONSTRUCTION / "custom/scripts/doorlock-state.js"
        with tempfile.TemporaryDirectory() as directory:
            module = Path(directory) / "doorlock-state.mjs"
            shutil.copyfile(module_source, module)
            runner = """
import { credentialFormResult, decideBreak, decideInteraction, normalizeBreakPolicy, removalConfirmed, sha256 } from './doorlock-state.mjs';
const owner = 'player-a';
const stranger = 'player-b';
const digest = 'a'.repeat(64);
const wrongDigest = 'b'.repeat(64);
const lock = { owner, schema: 1, authorization_mode: 'shared_credential', credential_digest: digest, revision: 1 };
const decide = (playerId, itemId, isSneaking = false, current = lock, credentialDigest = undefined) =>
  decideInteraction({ lock: current, playerId, itemId, isSneaking, credentialDigest }).action;
console.log(JSON.stringify({
  create: decide(owner, 'door_lock:key', false, null, digest),
  createUnconfigured: decide(owner, 'door_lock:key', false, null),
  universalDoesNotCreate: decide(owner, 'door_lock:universal_key', false, null),
  ownerWithoutCredentialDenied: decide(owner, 'door_lock:key'),
  matchingOtherPlayerOpen: decide(stranger, 'door_lock:key', false, lock, digest),
  wrongCredentialDenied: decide(stranger, 'door_lock:key', false, lock, wrongDigest),
  strangerDenied: decide(stranger, undefined),
  matchingOtherPlayerUnlock: decide(stranger, 'door_lock:key', true, lock, digest),
  strangerUnlockDenied: decide(stranger, 'door_lock:key', true, lock, wrongDigest),
  universalOpen: decide(stranger, 'door_lock:universal_key'),
  universalUnlock: decide(stranger, 'door_lock:universal_key', true),
  ironUniversalDenied: decideInteraction({ lock, playerId: stranger, itemId: 'door_lock:universal_key', isSneaking: false, universalAllowed: false }).action,
  ironUniversalDoesNotCreate: decideInteraction({ lock: null, playerId: stranger, itemId: 'door_lock:universal_key', isSneaking: false, universalAllowed: false }).action,
  lockedBreakDefault: decideBreak(lock).action,
  lockedBreakRemoveOwner: decideBreak(lock).expectedOwner,
  lockedBreakRemoveRevision: decideBreak(lock).expectedRevision,
  lockedBreakDenied: decideBreak(lock, 'deny').action,
  invalidBreakDenied: decideBreak(lock, 'invalid').action,
  unlockedBreak: decideBreak(undefined).action,
  defaultBreakPolicy: normalizeBreakPolicy(undefined),
  removeBreakPolicy: normalizeBreakPolicy('remove'),
  denyBreakPolicy: normalizeBreakPolicy('deny'),
  invalidBreakPolicy: normalizeBreakPolicy('invalid'),
  confirmed: removalConfirmed({ canceled: false, selection: 0 }),
  kept: removalConfirmed({ canceled: false, selection: 1 }),
  canceled: removalConfirmed({ canceled: true, selection: 0 }),
  shaEmpty: sha256(''),
  shaUnicode: sha256('lock🔒'),
  configured: credentialFormResult({ canceled: false, formValues: [' shared-code '] }),
  tooShort: credentialFormResult({ canceled: false, formValues: ['abc'] }),
  formCanceled: credentialFormResult({ canceled: true, formValues: ['never-read'] }),
}));
"""
            completed = subprocess.run(
                [node, "--input-type=module", "--eval", runner], cwd=directory,
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        expected = {
            "create": "CREATE_CREDENTIAL_LOCK",
            "createUnconfigured": "DENY_UNCONFIGURED",
            "universalDoesNotCreate": "ALLOW_DEFAULT",
            "ownerWithoutCredentialDenied": "DENY_LOCKED",
            "matchingOtherPlayerOpen": "ALLOW_OPEN",
            "wrongCredentialDenied": "DENY_LOCKED",
            "strangerDenied": "DENY_LOCKED",
            "matchingOtherPlayerUnlock": "REMOVE_LOCK",
            "strangerUnlockDenied": "DENY_LOCKED",
            "universalOpen": "ALLOW_OPEN",
            "universalUnlock": "REMOVE_LOCK",
            "ironUniversalDenied": "DENY_LOCKED",
            "ironUniversalDoesNotCreate": "ALLOW_DEFAULT",
            "lockedBreakDefault": "ALLOW_BREAK_REMOVE_LOCK",
            "lockedBreakRemoveOwner": "player-a",
            "lockedBreakRemoveRevision": 1,
            "lockedBreakDenied": "DENY_LOCKED",
            "invalidBreakDenied": "DENY_LOCKED",
            "unlockedBreak": "ALLOW_BREAK",
            "confirmed": True,
            "kept": False,
            "canceled": False,
        }
        self.assertEqual(expected, {key: result[key] for key in expected})
        self.assertEqual(hashlib.sha256(b"").hexdigest(), result["shaEmpty"])
        self.assertEqual(hashlib.sha256("lock🔒".encode()).hexdigest(), result["shaUnicode"])
        self.assertTrue(result["configured"]["ok"])
        self.assertEqual(hashlib.sha256(b"mccompiler:doorlock:v1:shared-code").hexdigest(), result["configured"]["digest"])
        self.assertFalse(result["tooShort"]["ok"])
        self.assertTrue(result["formCanceled"]["canceled"])
        self.assertNotIn("shared-code", json.dumps(result["configured"]))
        self.assertEqual({"policy": "remove", "valid": True, "usedDefault": True}, result["defaultBreakPolicy"])
        self.assertEqual({"policy": "remove", "valid": True, "usedDefault": False}, result["removeBreakPolicy"])
        self.assertEqual({"policy": "deny", "valid": True, "usedDefault": False}, result["denyBreakPolicy"])
        self.assertEqual({"policy": "deny", "valid": False, "usedDefault": False}, result["invalidBreakPolicy"])

    def test_state_records_and_revision_checks_match_the_v1_contract(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required for clean-room state operation tests")
        module_source = RECONSTRUCTION / "custom/scripts/doorlock-state.js"
        with tempfile.TemporaryDirectory() as directory:
            module = Path(directory) / "doorlock-state.mjs"
            shutil.copyfile(module_source, module)
            runner = """
import { buildCredentialLock, buildOwnerLock, canonicalLocationKey, createLockIfAbsent, decideOpenReconciliation, isLockableBlockType, isRedstoneProtectedBlockType, normalizeLockMap, removeLockIfRevision, universalKeyAllowedForBlock, updateProtectedOpenIfRevision, validateLockMap } from './doorlock-state.mjs';
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
const badProtectedOpen = validateLockMap({ [location]: { ...record, protected_open: 'yes' } });
const sparse = normalizeLockMap({ [location]: { owner: 'player-a', schema: 1 } });
const shared = buildCredentialLock('minecraft:overworld:1:2:3', 'a'.repeat(64), 'player-a', 46, false);
const protectedCaptured = updateProtectedOpenIfRevision(created.locks, location, 'player-a', 1, false);
const protectedStale = updateProtectedOpenIfRevision(protectedCaptured.locks, location, 'player-a', 1, true);
const protectedUpdated = updateProtectedOpenIfRevision(protectedCaptured.locks, location, 'player-a', 2, true);
const reconciliation = {
  missing: decideOpenReconciliation(undefined, false),
  stable: decideOpenReconciliation(true, true),
  changed: decideOpenReconciliation(true, false),
  unsupported: decideOpenReconciliation(true, undefined),
};
const canonical = {
  lowerDoor: canonicalLocationKey({ dimensionId: 'minecraft:overworld', location: { x: 4, y: 64, z: 8 } }),
  upperDoor: canonicalLocationKey({ dimensionId: 'minecraft:overworld', location: { x: 4, y: 65, z: 8 }, doorLowerLocation: { x: 4, y: 64, z: 8 } }),
  chestLeft: canonicalLocationKey({ dimensionId: 'minecraft:overworld', location: { x: 10, y: 70, z: 5 }, pairedLocations: [{ x: 11, y: 70, z: 5 }] }),
  chestRight: canonicalLocationKey({ dimensionId: 'minecraft:overworld', location: { x: 11, y: 70, z: 5 }, pairedLocations: [{ x: 10, y: 70, z: 5 }] }),
  ambiguousChest: canonicalLocationKey({ dimensionId: 'minecraft:overworld', location: { x: 11, y: 70, z: 5 }, pairedLocations: [{ x: 10, y: 70, z: 5 }, { x: 12, y: 70, z: 5 }] }),
};
const coverage = {
  door: isLockableBlockType('minecraft:oak_door'),
  gate: isLockableBlockType('minecraft:warped_fence_gate'),
  trapdoor: isLockableBlockType('minecraft:iron_trapdoor'),
  legacyTrapdoor: isLockableBlockType('minecraft:trapdoor'),
  shulker: isLockableBlockType('minecraft:purple_shulker_box'),
  chest: isLockableBlockType('minecraft:chest'),
  anvil: isLockableBlockType('minecraft:anvil'),
  barrel: isLockableBlockType('minecraft:barrel'),
  doorRedstone: isRedstoneProtectedBlockType('minecraft:oak_door'),
  gateRedstone: isRedstoneProtectedBlockType('minecraft:warped_fence_gate'),
  trapdoorRedstone: isRedstoneProtectedBlockType('minecraft:iron_trapdoor'),
  legacyTrapdoorRedstone: isRedstoneProtectedBlockType('minecraft:trapdoor'),
  chestRedstone: isRedstoneProtectedBlockType('minecraft:chest'),
  ironUniversal: universalKeyAllowedForBlock('minecraft:iron_door'),
  oakUniversal: universalKeyAllowedForBlock('minecraft:oak_door'),
};
console.log(JSON.stringify({ record, created, competingCreate, twoLocks, dimensions, staleRemove, wrongOwnerRemove, removed, validErrors, badDimension, badRevision, badMode, badProtectedOpen, sparse, sparseErrors: validateLockMap(sparse.locks), shared, sharedErrors: validateLockMap({ 'minecraft:overworld:1:2:3': shared }), protectedCaptured, protectedStale, protectedUpdated, reconciliation, canonical, coverage }));
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
        self.assertTrue(any("protected_open must be boolean" in error for error in result["badProtectedOpen"]))
        self.assertTrue(result["sparse"]["upgraded"])
        self.assertEqual([], result["sparseErrors"])
        self.assertEqual("owner_identity", result["sparse"]["locks"]["minecraft:nether:-4:65:12"]["authorization_mode"])
        self.assertEqual("shared_credential", result["shared"]["authorization_mode"])
        self.assertEqual("a" * 64, result["shared"]["credential_digest"])
        self.assertFalse(result["shared"]["protected_open"])
        self.assertEqual([], result["sharedErrors"])
        self.assertTrue(result["protectedCaptured"]["changed"])
        self.assertEqual(2, result["protectedCaptured"]["locks"]["minecraft:nether:-4:65:12"]["revision"])
        self.assertFalse(result["protectedCaptured"]["locks"]["minecraft:nether:-4:65:12"]["protected_open"])
        self.assertFalse(result["protectedStale"]["changed"])
        self.assertTrue(result["protectedUpdated"]["changed"])
        self.assertTrue(result["protectedUpdated"]["locks"]["minecraft:nether:-4:65:12"]["protected_open"])
        self.assertEqual(
            {
                "missing": {"action": "CAPTURE_OPEN_STATE", "open": False},
                "stable": {"action": "OPEN_STATE_STABLE"},
                "changed": {"action": "RESTORE_OPEN_STATE", "open": True},
                "unsupported": {"action": "NO_OPEN_STATE"},
            },
            result["reconciliation"],
        )
        self.assertEqual(result["canonical"]["lowerDoor"], result["canonical"]["upperDoor"])
        self.assertEqual(result["canonical"]["chestLeft"], result["canonical"]["chestRight"])
        self.assertEqual("minecraft:overworld:11:70:5", result["canonical"]["ambiguousChest"])
        self.assertEqual(
            {"door": True, "gate": True, "trapdoor": True, "legacyTrapdoor": True, "shulker": True, "chest": True,
             "anvil": False, "barrel": False, "doorRedstone": True, "gateRedstone": True,
             "trapdoorRedstone": True, "legacyTrapdoorRedstone": True, "chestRedstone": False,
             "ironUniversal": False, "oakUniversal": True},
            result["coverage"],
        )

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
        self.assertEqual("PARTIAL_TECHNICAL_RECONSTRUCTION_BDS_ADAPTER_VERIFIED", status["status"])
        self.assertIsNone(status["approved_quality_claim"])
        self.assertEqual(
            {
                "physical-player gameplay, feature persistence, multiplayer, Realm, and console tests",
            },
            set(status["missing"]),
        )
        self.assertFalse(status["claims"]["technical_reconstruction_complete"])
        self.assertFalse(status["claims"]["runtime_verified"])
        self.assertTrue(status["claims"]["bds_boot_verified"])
        self.assertTrue(status["claims"]["creator_tools_passed"])
        self.assertFalse(status["claims"]["rights_cleared"])
        self.assertFalse(status["claims"]["marketplace_candidate"])
        self.assertFalse(status["claims"]["console_verified"])
        redesign = status["intentional_redesigns"][0]
        self.assertEqual("PROPOSED_NOT_APPROVED", redesign["status"])
        self.assertEqual(["anvil and command configuration parity", "item-instance credential storage"], redesign["lost"])

    def test_external_validation_is_hash_bound_and_narrow(self) -> None:
        validation = json.loads((RECONSTRUCTION / "technical-build-validation.json").read_text())
        self.assertEqual("STATIC_BDS_UPGRADE_ADAPTER_AND_SIMULATED_BREAK_INTEGRATION_VERIFIED", validation["status"])
        self.assertEqual(0, validation["creator_tools"]["errors"])
        self.assertEqual(0, validation["creator_tools"]["warnings"])
        self.assertFalse(validation["creator_tools"]["marketplace_approval_implied"])
        self.assertTrue(validation["bds_diagnostic"]["script_initialized"])
        self.assertTrue(validation["bds_diagnostic"]["diagnostic_state_persistence_verified"])
        self.assertTrue(validation["bds_diagnostic"]["empty_state_migration_executed"])
        self.assertTrue(validation["bds_diagnostic"]["nonempty_state_migration_verified"])
        self.assertTrue(validation["bds_diagnostic"]["interrupted_write_recovery_verified"])
        self.assertEqual(
            "prepared_journal_before_current_state_write",
            validation["bds_diagnostic"]["interruption_fixture_point"],
        )
        self.assertTrue(validation["bds_diagnostic"]["migrated_state_restart_verified"])
        self.assertEqual(1, validation["bds_diagnostic"]["migrated_lock_records"])
        self.assertTrue(validation["bds_diagnostic"]["adapter_integration_verified"])
        self.assertTrue(validation["bds_diagnostic"]["redstone_reconciliation_adapter_verified"])
        self.assertFalse(validation["bds_diagnostic"]["gameplay_verified"])
        self.assertFalse(validation["bds_diagnostic"]["multiplayer_verified"])
        self.assertFalse(validation["bds_diagnostic"]["console_verified"])
        self.assertFalse(validation["bds_diagnostic"]["feature_persistence_verified"])
        self.assertEqual([1, 2, 3], validation["bds_diagnostic"]["persistent_boot_values"])
        self.assertFalse(validation["bds_diagnostic"]["published_ports"])
        self.assertEqual(validation["artifacts"]["mcworld"]["sha256"], validation["bds_diagnostic"]["world_sha256"])
        self.assertEqual(validation["artifacts"]["legacy_seed_mcworld"]["sha256"], validation["bds_diagnostic"]["legacy_seed_world_sha256"])
        self.assertTrue(validation["artifacts"]["legacy_seed_mcworld"]["fixture_only"])
        self.assertEqual(3, validation["bds_diagnostic"]["restart_cycles"])
        simulated = validation["simulated_player_diagnostic"]
        self.assertEqual("EVENT_ADAPTER_INTEGRATION_TEST", simulated["classification"])
        self.assertEqual("1.26.50.20", simulated["bedrock_version"])
        self.assertTrue(simulated["preview_channel"])
        self.assertTrue(simulated["simulated_player_break_before_event_observed"])
        self.assertTrue(simulated["simulated_player_break_after_event_observed"])
        self.assertTrue(simulated["simulated_player_integration_verified"])
        self.assertFalse(simulated["physical_player_verified"])
        self.assertFalse(simulated["gameplay_verified"])
        self.assertFalse(simulated["console_verified"])
        self.assertFalse(simulated["marketplace_or_console_evidence"])
        self.assertFalse(validation["marketplace_candidate"]["passed"])
        self.assertIn("actual physical-player item and block-interaction event adapters", validation["unverified"])

    def test_bds_redstone_probes_are_adapter_integration_only(self) -> None:
        probes = json.loads((RECONSTRUCTION / "bds-console-probes.json").read_text())
        self.assertEqual("adapter_integration", probes["classification"])
        self.assertFalse(probes["gameplay_or_console_evidence"])
        self.assertEqual(
            {
                "doorlock-fixture-ticking-area",
                "doorlock-fixture-trapdoor",
                "doorlock-redstone-force-open",
                "doorlock-redstone-restored",
                "doorlock-redstone-restart-state",
            },
            {probe["check_id"] for probe in probes["probes"]},
        )
        self.assertEqual([1, 1, 2, 2, 3], [probe["cycle"] for probe in probes["probes"]])
        self.assertTrue(all(probe["command"].split()[0] in {"setblock", "testforblock", "tickingarea"} for probe in probes["probes"]))


if __name__ == "__main__":
    unittest.main()
