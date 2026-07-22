from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from mccompiler.operations import generation_ops, validation_ops
from mccompiler.project.store import ProjectStore
from tools.build_benchmark_b import build_legacy_seed_world


ROOT = Path(__file__).resolve().parents[1]
RECONSTRUCTION = ROOT / "benchmarks/rights-cleared-java-mod/reconstruction"


class BenchmarkBProjectWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.store = ProjectStore.create(Path(temporary.name) / "doorlock-project", name="DoorLock technical reconstruction")
        self.store.write("analysis/modir.json", json.loads((RECONSTRUCTION / "modir-seed.json").read_text()))
        self.store.write("rights/rights-manifest.yaml", json.loads((RECONSTRUCTION / "rights-manifest.json").read_text()))
        self.store.write("reports/fidelity.json", json.loads((RECONSTRUCTION / "quality-records.json").read_text()))
        self.store.write("decisions/custom-handlers.json", json.loads((RECONSTRUCTION / "custom-handler.json").read_text()))
        for name in ("doorlock-state.js", "doorlock.js"):
            custom = self.store.resolve(f"custom/scripts/{name}")
            custom.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(RECONSTRUCTION / f"custom/scripts/{name}", custom)

    def test_deterministic_clean_package_and_world_with_honest_gates(self) -> None:
        generated, _, _ = generation_ops.generate_pack(self.store, {}, self.store.revision)
        first_hash = next(row["sha256"] for row in generated["artifacts"] if row["kind"] == "generated_archive")
        generated_again, _, _ = generation_ops.generate_pack(self.store, {}, self.store.revision)
        second_hash = next(row["sha256"] for row in generated_again["artifacts"] if row["kind"] == "generated_archive")
        self.assertEqual(first_hash, second_hash)
        recorded = json.loads((RECONSTRUCTION / "technical-build-validation.json").read_text())
        self.assertEqual(recorded["artifacts"]["mcaddon"]["sha256"], first_hash)

        static, _, _ = validation_ops.validate_static(self.store, {"marketplace": True})
        scripts, _, _ = validation_ops.validate_scripts(self.store, {})
        assets, _, _ = validation_ops.validate_assets(self.store, {})
        api, _, _ = validation_ops.validate_api_symbols(self.store, {})
        performance, _, _ = validation_ops.validate_performance(self.store, {})
        self.assertTrue(static["valid"], static["errors"])
        self.assertTrue(scripts["valid"], scripts["errors"])
        self.assertTrue(assets["valid"], assets["errors"])
        self.assertTrue(api["valid"], api["errors"])
        self.assertTrue(performance["passed"], performance)

        world, _, _ = generation_ops.generate_world(self.store, {"world_name": "DoorLock Technical Validation"}, self.store.revision)
        current_world = self.store.resolve(world["world"]["path"])
        legacy_a = build_legacy_seed_world(current_world, self.store.resolve("runtime/legacy-a.mcworld"))
        legacy_b = build_legacy_seed_world(current_world, self.store.resolve("runtime/legacy-b.mcworld"))
        self.assertEqual(legacy_a["sha256"], legacy_b["sha256"])
        self.assertNotEqual(world["world"]["world_hash"], legacy_a["sha256"])
        with zipfile.ZipFile(self.store.resolve("runtime/legacy-a.mcworld")) as legacy_bundle:
            legacy_script_name = next(name for name in legacy_bundle.namelist() if name.endswith("/scripts/custom/doorlock.js"))
            legacy_script = legacy_bundle.read(legacy_script_name).decode()
        self.assertIn("legacy_seed=1", legacy_script)
        self.assertNotIn("migration_nonempty_verified", legacy_script)
        package, _, artifacts = generation_ops.package_mcaddon(self.store, {}, self.store.revision)
        self.assertEqual("GENERATED", world["status"])
        self.assertEqual(recorded["artifacts"]["mcworld"]["sha256"], world["world"]["world_hash"])
        self.assertEqual("PACKAGED", package["status"])
        archive = self.store.resolve(artifacts[0]["path"])
        with zipfile.ZipFile(archive) as bundle:
            names = set(bundle.namelist())
        self.assertIn("behavior_pack/scripts/custom/doorlock.js", names)
        self.assertIn("behavior_pack/scripts/custom/doorlock-state.js", names)
        self.assertTrue(any(name.endswith("items/door_lock_key.json") for name in names))
        self.assertTrue(any(name.endswith("items/door_lock_golden_key.json") for name in names))
        self.assertTrue(any(name.endswith("items/door_lock_universal_key.json") for name in names))
        self.assertFalse(any(name.startswith(("reports/", "custom/", "analysis/", "rights/", "tests/")) for name in names))
        self.assertFalse(any(name.endswith((".java", ".class", ".jar")) for name in names))

        candidate, _, _ = validation_ops.evaluate_marketplace_candidate(self.store, {}, self.store.revision)
        self.assertFalse(candidate["candidate"]["passed"])
        self.assertTrue(candidate["candidate"]["blockers"]["rights"])
        self.assertTrue(candidate["candidate"]["blockers"]["quality"])
        self.assertEqual([], candidate["candidate"]["quality"]["missing_feature_ids"])
        self.assertTrue(all("unresolved quality classification" in error for error in candidate["candidate"]["blockers"]["quality"]))
        self.assertTrue(candidate["candidate"]["blockers"]["creator_tools"])
        self.assertFalse(candidate["candidate"]["marketplace_approval_implied"])


if __name__ == "__main__":
    unittest.main()
