from __future__ import annotations

import importlib.util
import json
import hashlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/build_forest_wave_1_parallel_batch_1.py"
SPEC = importlib.util.spec_from_file_location("batch_1_builder", SCRIPT)
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = BUILDER
SPEC.loader.exec_module(BUILDER)


class ForestWave1ParallelBatch1IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = BUILDER.build()

    def test_all_six_feature_pack_pairs_are_bound(self) -> None:
        world = ROOT / self.report["artifacts"]["mcworld"]["path"]
        with zipfile.ZipFile(world) as archive:
            behavior = json.loads(archive.read("world_behavior_packs.json"))
            resource = json.loads(archive.read("world_resource_packs.json"))
            self.assertEqual(6, len(behavior))
            self.assertEqual(6, len(resource))
            self.assertEqual(12, len({entry["pack_id"] for entry in [*behavior, *resource]}))
            manifests = [name for name in archive.namelist() if name.endswith("/manifest.json")]
            self.assertEqual(12, len(manifests))

    def test_mcaddon_contains_every_feature_without_path_collisions(self) -> None:
        addon = ROOT / self.report["artifacts"]["mcaddon"]["path"]
        with zipfile.ZipFile(addon) as archive:
            names = archive.namelist()
            self.assertEqual(len(names), len(set(names)))
            for spec in BUILDER.PACKS:
                self.assertIn(f"behavior_packs/{spec.feature_id}/manifest.json", names)
                self.assertIn(f"resource_packs/{spec.feature_id}/manifest.json", names)

    def test_preview_diagnostic_is_separate_and_never_ship(self) -> None:
        production = ROOT / self.report["artifacts"]["mcworld"]["path"]
        diagnostic = ROOT / self.report["preview_diagnostic"]["path"]
        self.assertNotEqual(production, diagnostic)
        self.assertTrue(self.report["preview_diagnostic"]["never_ship"])
        self.assertTrue(self.report["preview_diagnostic"]["preview_only"])
        with zipfile.ZipFile(production) as archive:
            self.assertFalse(any("preview_simulated_player" in name for name in archive.namelist()))
        with zipfile.ZipFile(diagnostic) as archive:
            diagnostic_manifests = [
                name
                for name in archive.namelist()
                if name.startswith("behavior_packs/") and name.endswith("/manifest.json")
                and self.report["preview_diagnostic"]["diagnostic_pack_uuid"]
                in archive.read(name).decode("utf-8")
            ]
            self.assertEqual(
                1,
                len(diagnostic_manifests),
            )

    def test_preview_build_does_not_mutate_production_world(self) -> None:
        production = ROOT / self.report["artifacts"]["mcworld"]["path"]
        before = production.read_bytes()
        BUILDER.build()
        self.assertEqual(before, production.read_bytes())

    def test_build_is_byte_deterministic(self) -> None:
        first_addon = (ROOT / self.report["artifacts"]["mcaddon"]["path"]).read_bytes()
        first_world = (ROOT / self.report["artifacts"]["mcworld"]["path"]).read_bytes()
        second = BUILDER.build()
        self.assertEqual(first_addon, (ROOT / second["artifacts"]["mcaddon"]["path"]).read_bytes())
        self.assertEqual(first_world, (ROOT / second["artifacts"]["mcworld"]["path"]).read_bytes())

    def test_pack_uuids_and_archive_paths_are_unique(self) -> None:
        entries = BUILDER.pack_entries(BUILDER.PACKS)
        self.assertEqual(len(entries), len({name for name, _ in entries}))
        headers = []
        for spec in BUILDER.PACKS:
            headers.extend(
                [
                    BUILDER.manifest_header(spec.behavior_pack),
                    BUILDER.manifest_header(spec.resource_pack),
                ]
            )
        self.assertEqual(len(headers), len({header["uuid"] for header in headers}))

    def test_integration_labels_and_ps4_boundary_are_explicit(self) -> None:
        self.assertIn("NOT PHYSICAL PS4 CERTIFIED", self.report["labels"])
        self.assertFalse(self.report["claims"]["physical_ps4_verified"])
        self.assertFalse(self.report["claims"]["marketplace_approved"])
        self.assertFalse(self.report["claims"]["bds_qualified"])

    def test_resonance_sling_frozen_artifacts_remain_exact(self) -> None:
        protected = self.report["protected_resonance_sling"]
        self.assertTrue(protected["unchanged"])
        self.assertEqual(
            "0bbd00a285cb8c7ccab49cf9a246f2ad95386eeaa239631a1c6463c0c84855ec",
            protected["mcaddon_sha256"],
        )
        self.assertEqual(
            "061501b67b0886296ad2765f1b7c5246efbe38d64b9494303a05b9ee81a58d9a",
            protected["mcworld_sha256"],
        )

    def test_writer_rejects_duplicate_archive_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            duplicate = BUILDER.FeaturePacks(
                "duplicate",
                BUILDER.PACKS[0].behavior_pack,
                BUILDER.PACKS[0].resource_pack,
            )
            path = Path(directory) / "duplicate.mcaddon"
            with self.assertRaisesRegex(ValueError, "Duplicate integration archive entry"):
                BUILDER.write_zip(path, BUILDER.pack_entries([duplicate, duplicate]))

    def test_final_digest_freeze_matches_every_integrated_feature_package(self) -> None:
        freeze = json.loads(
            (
                ROOT
                / "production/batches/forest-wave-1-parallel-batch-1/reports/final-digest-freeze.json"
            ).read_text()
        )
        self.assertEqual("AUTHORITATIVE_POST_RED_TEAM_DIGESTS", freeze["status"])
        for feature in freeze["features"].values():
            package = ROOT / feature["package"]
            self.assertTrue(package.is_file())
            self.assertEqual(
                hashlib.sha256(package.read_bytes()).hexdigest(),
                feature["final_package_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
