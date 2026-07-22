from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
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
        self.assertNotIn("password", script.lower())
        self.assertNotIn("src/main/java", script)
        node = shutil.which("node")
        if node:
            completed = subprocess.run([node, "--check", str(script_path)], capture_output=True, text=True, check=False)
            self.assertEqual(0, completed.returncode, completed.stderr)

    def test_every_declared_api_symbol_is_stable_and_marketplace_candidate(self) -> None:
        metadata = json.loads((RECONSTRUCTION / "custom-handler.json").read_text())
        requirements = [(row["module"], row["symbol"]) for row in metadata["handlers"][0]["api_symbols"]]
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
        self.assertFalse(validation["bds_diagnostic"]["published_ports"])
        self.assertEqual(validation["artifacts"]["mcworld"]["sha256"], validation["bds_diagnostic"]["world_sha256"])
        self.assertFalse(validation["marketplace_candidate"]["passed"])
        self.assertIn("actual player item and block event adapters", validation["unverified"])


if __name__ == "__main__":
    unittest.main()
