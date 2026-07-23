from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import uuid
import zipfile

from mccompiler.runtime.gametest import GameTestDiagnosticError, augment_mcworld_with_gametest_pack, enable_gametest_experiment
from mccompiler.world import _minimal_level_dat


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmarks/rights-cleared-java-mod/reconstruction"
DIAGNOSTIC_PACK = BENCHMARK / "diagnostic/simulated-player"


class GameTestDiagnosticTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def source_world(self, *, unsafe: bool = False) -> Path:
        path = self.root / "source.mcworld"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("level.dat", _minimal_level_dat("Diagnostic Source"))
            archive.writestr("levelname.txt", "Diagnostic Source\n")
            archive.writestr("world_behavior_packs.json", "[]\n")
            archive.writestr("world_resource_packs.json", "[]\n")
            if unsafe:
                archive.writestr("../escape", "no")
        return path

    def test_diagnostic_world_is_deterministic_experimental_and_source_preserving(self) -> None:
        source = self.source_world()
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        first = self.root / "first.mcworld"
        second = self.root / "second.mcworld"
        first_result = augment_mcworld_with_gametest_pack(source, DIAGNOSTIC_PACK, first)
        second_result = augment_mcworld_with_gametest_pack(source, DIAGNOSTIC_PACK, second)
        self.assertEqual(first_result["diagnostic_world"]["sha256"], second_result["diagnostic_world"]["sha256"])
        self.assertEqual(source_hash, hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertTrue(first_result["source_world"]["unchanged"])
        self.assertFalse(first_result["marketplace_or_console_evidence"])
        with zipfile.ZipFile(first) as archive:
            names = set(archive.namelist())
            bindings = json.loads(archive.read("world_behavior_packs.json"))
            level_dat = archive.read("level.dat")
        self.assertTrue(any(name.endswith("/scripts/main.js") for name in names))
        self.assertEqual("8d3f2291-f637-5c61-98cc-d970761177c8", bindings[-1]["pack_id"])
        self.assertIn(b"gametest", level_dat)
        self.assertIn(b"experiments_ever_used", level_dat)
        self.assertIn(b"saved_with_toggled_experiments", level_dat)

    def test_invalid_inputs_fail_closed(self) -> None:
        source = self.source_world()
        with self.assertRaisesRegex(GameTestDiagnosticError, "must not overwrite"):
            augment_mcworld_with_gametest_pack(source, DIAGNOSTIC_PACK, source)
        unsafe = self.source_world(unsafe=True)
        with self.assertRaisesRegex(GameTestDiagnosticError, "unsafe archive path"):
            augment_mcworld_with_gametest_pack(unsafe, DIAGNOSTIC_PACK, self.root / "unsafe-output.mcworld")
        source = self.source_world()
        invalid_pack = self.root / "invalid-pack"
        (invalid_pack / "scripts").mkdir(parents=True)
        manifest = json.loads((DIAGNOSTIC_PACK / "manifest.json").read_text())
        manifest["header"]["uuid"] = str(uuid.uuid4())
        manifest["dependencies"] = [row for row in manifest["dependencies"] if row["module_name"] != "@minecraft/server-gametest"]
        (invalid_pack / "manifest.json").write_text(json.dumps(manifest))
        (invalid_pack / "scripts/main.js").write_text("export {};\n")
        with self.assertRaisesRegex(GameTestDiagnosticError, "beta @minecraft/server-gametest"):
            augment_mcworld_with_gametest_pack(source, invalid_pack, self.root / "invalid-output.mcworld")

    def test_preview_module_overlay_is_explicit_deterministic_and_diagnostic_only(self) -> None:
        source = self.source_world()
        production_manifest = {
            "format_version": 2,
            "header": {"name": "Production", "uuid": str(uuid.uuid4()), "version": [1, 0, 0]},
            "modules": [],
            "dependencies": [{"module_name": "@minecraft/server", "version": "2.0.0"}],
        }
        with zipfile.ZipFile(source, "a") as archive:
            archive.writestr("behavior_packs/production/manifest.json", json.dumps(production_manifest))
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        first = self.root / "overlay-first.mcworld"
        second = self.root / "overlay-second.mcworld"
        first_result = augment_mcworld_with_gametest_pack(
            source, DIAGNOSTIC_PACK, first, diagnostic_server_version="2.10.0",
        )
        second_result = augment_mcworld_with_gametest_pack(
            source, DIAGNOSTIC_PACK, second, diagnostic_server_version="2.10.0",
        )
        self.assertEqual(first_result["diagnostic_world"]["sha256"], second_result["diagnostic_world"]["sha256"])
        self.assertTrue(first_result["production_pack_modified_for_preview_diagnostic"])
        self.assertEqual("2.0.0", first_result["production_pack_module_overrides"][0]["from"])
        self.assertEqual("2.10.0", first_result["production_pack_module_overrides"][0]["to"])
        self.assertFalse(first_result["marketplace_or_console_evidence"])
        self.assertEqual(source_hash, hashlib.sha256(source.read_bytes()).hexdigest())
        with zipfile.ZipFile(first) as archive:
            overlaid = json.loads(archive.read("behavior_packs/production/manifest.json"))
        self.assertEqual("2.10.0", overlaid["dependencies"][0]["version"])
        with zipfile.ZipFile(source) as archive:
            original = json.loads(archive.read("behavior_packs/production/manifest.json"))
        self.assertEqual("2.0.0", original["dependencies"][0]["version"])

        with self.assertRaisesRegex(GameTestDiagnosticError, "three-part numeric"):
            augment_mcworld_with_gametest_pack(
                source, DIAGNOSTIC_PACK, self.root / "bad-version.mcworld",
                diagnostic_server_version="latest",
            )

    def test_consumer_artifact_contract_excludes_preview_diagnostic(self) -> None:
        technical = json.loads((BENCHMARK / "technical-build-validation.json").read_text())
        self.assertNotEqual("8d3f2291-f637-5c61-98cc-d970761177c8", technical["artifacts"]["mcworld"]["behavior_pack_id"])
        script = (DIAGNOSTIC_PACK / "scripts/main.js").read_text()
        self.assertIn("spawnSimulatedPlayer", script)
        production = (BENCHMARK / "custom/scripts/doorlock.js").read_text()
        self.assertNotIn("server-gametest", production)
        self.assertNotIn("spawnSimulatedPlayer", production)

    def test_level_dat_rejects_duplicate_experiment_injection(self) -> None:
        enabled = enable_gametest_experiment(_minimal_level_dat("Experiment"))
        with self.assertRaisesRegex(GameTestDiagnosticError, "already contains"):
            enable_gametest_experiment(enabled)


if __name__ == "__main__":
    unittest.main()
