from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/build_controlled_chaos_qualification.py"
SPEC = importlib.util.spec_from_file_location("controlled_chaos_builder", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BUILDER
SPEC.loader.exec_module(BUILDER)


class ControlledChaosPackageTests(unittest.TestCase):
    def test_committed_artifacts_match_manifest_and_checklists(self) -> None:
        qualification = ROOT / "benchmarks/controlled-chaos-integration/qualification"
        manifest = json.loads((qualification / "artifact-manifest.json").read_text(encoding="utf-8"))
        for kind, filename in (("mcaddon", "exact-test-addon.mcaddon"), ("mcworld", "exact-test-world.mcworld")):
            payload = (qualification / filename).read_bytes()
            expected = manifest["artifacts"][kind]["sha256"]
            self.assertEqual(expected, hashlib.sha256(payload).hexdigest())
            for checklist in qualification.glob("*-checklist.md"):
                self.assertIn(expected, checklist.read_text(encoding="utf-8"))

    def test_consumer_addon_is_clean_and_stable_only(self) -> None:
        path = ROOT / "benchmarks/controlled-chaos-integration/dist/controlled-chaos-qualification.mcaddon"
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            self.assertEqual(names, sorted(names))
            self.assertFalse(any("report" in name or "fixture" in name or "/tests/" in name for name in names))
            manifests = [json.loads(archive.read(name)) for name in names if name.endswith("manifest.json")]
        combined = json.dumps(manifests)
        self.assertNotIn("-beta", combined)
        self.assertNotIn("@minecraft/server-gametest", combined)
        self.assertNotIn("@minecraft/server-net", combined)

    def test_two_clean_builds_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            source_bp, source_rp = BUILDER.build_packs()
            one = BUILDER.zip_tree(Path(first) / "one.mcaddon", [(source_bp, "behavior_pack/"), (source_rp, "resource_pack/")])
            source_bp, source_rp = BUILDER.build_packs()
            two = BUILDER.zip_tree(Path(second) / "two.mcaddon", [(source_bp, "behavior_pack/"), (source_rp, "resource_pack/")])
            self.assertEqual(one["sha256"], two["sha256"])
            self.assertEqual((Path(first) / "one.mcaddon").read_bytes(), (Path(second) / "two.mcaddon").read_bytes())

    def test_result_schema_is_hash_bound(self) -> None:
        qualification = ROOT / "benchmarks/controlled-chaos-integration/qualification"
        manifest = json.loads((qualification / "artifact-manifest.json").read_text(encoding="utf-8"))
        schema = json.loads((qualification / "result-schema.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["artifacts"]["mcaddon"]["sha256"], schema["properties"]["mcaddon_sha256"]["const"])
        self.assertEqual(manifest["artifacts"]["mcworld"]["sha256"], schema["properties"]["mcworld_sha256"]["const"])


if __name__ == "__main__":
    unittest.main()
