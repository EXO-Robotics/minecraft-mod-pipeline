from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from mccompiler.operations import generation_ops
from mccompiler.operations.envelope import OperationError
from mccompiler.project.store import ProjectError, ProjectStore


def _evidence() -> list[dict[str, object]]:
    return [{"source_file": "Demo.java", "line_range": [1, 2], "source_mode": "test", "confidence": 1.0}]


def _ir() -> dict[str, object]:
    return {
        "schema_version": "1.0.0", "metadata": {"id": "demo"}, "mods": [], "dependencies": [],
        "dependency_graph": {"nodes": [], "edges": []}, "registries": [], "assets": [],
        "content": [
            {"kind": "item", "identifier": "demo:wand", "properties": {}, "evidence": _evidence()},
            {"kind": "block", "identifier": "demo:machine", "properties": {}, "evidence": _evidence()},
        ],
        "behaviors": [], "state": [], "presentation_requirements": [], "world_requirements": [],
        "ui_intent": [], "networking_intent": [], "unsupported_hooks": [], "diagnostics": [], "tests": [], "errors": [],
    }


class GenerationOperationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.store = ProjectStore.create(Path(temporary.name) / "project", name="generation")
        self.store.commit({"analysis/modir.json": _ir()}, manifest_updates={"analysis_revision": 1})

    def test_generate_pack_world_and_archive_are_persistent_and_deterministic(self) -> None:
        custom = self.store.resolve("custom/assets/owned.txt")
        custom.write_text("do not overwrite", encoding="utf-8")
        revision = self.store.revision
        pack, _, artifacts = generation_ops.generate_pack(self.store, {}, revision)
        self.assertEqual("GENERATED", pack["status"])
        self.assertEqual(
            {"behavior_pack", "resource_pack", "conversion_manifest", "generated_archive", "backend_reports"},
            {row["kind"] for row in artifacts},
        )
        self.assertTrue(self.store.resolve("bedrock/behavior_pack/manifest.json").is_file())
        self.assertEqual("do not overwrite", custom.read_text(encoding="utf-8"))

        world, _, world_artifacts = generation_ops.generate_world(self.store, {"world_name": "Deterministic Demo"}, self.store.revision)
        first_world = self.store.resolve(world_artifacts[0]["path"]).read_bytes()
        self.assertEqual(world_artifacts[0]["sha256"], world["world"]["world_hash"])
        generation_ops.generate_world(self.store, {"world_name": "Deterministic Demo"}, self.store.revision)
        self.assertEqual(first_world, self.store.resolve(world_artifacts[0]["path"]).read_bytes())

        packaged, _, package_artifacts = generation_ops.package_mcaddon(self.store, {}, self.store.revision)
        archive = self.store.resolve(package_artifacts[0]["path"])
        self.assertEqual("PACKAGED", packaged["status"])
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
        self.assertTrue(any(name.startswith("behavior_pack/") for name in names))
        self.assertTrue(any(name.startswith("resource_pack/") for name in names))
        self.assertFalse(any(name.startswith("reports/") or name.startswith("custom/") for name in names))
        self.assertTrue(self.store.resolve("reports/generation/package_mcaddon.json").is_file())
        self.assertTrue(self.store.resolve("dist/marketplace-candidate/behavior-pack/manifest.json").is_file())
        self.assertTrue(self.store.resolve("dist/marketplace-candidate/resource-pack/manifest.json").is_file())
        self.assertTrue(self.store.resolve("dist/marketplace-candidate/consumer-metadata/package.json").is_file())

    def test_focused_generation_scaffolds_attributable_feature(self) -> None:
        result, _, artifacts = generation_ops.generate_item(self.store, {"id": "demo:wand"}, self.store.revision)
        self.assertEqual("SCAFFOLDED", result["status"])
        self.assertEqual("item", artifacts[0]["kind"])
        self.assertTrue(self.store.resolve(artifacts[0]["path"]).is_file())
        self.assertTrue(self.store.resolve("reports/generation/generate_item.json").is_file())

    def test_focused_generation_returns_explicit_feature_blockers(self) -> None:
        revision = self.store.revision
        with self.assertRaises(OperationError) as missing:
            generation_ops.generate_entity(self.store, {"id": "demo:missing"}, revision)
        self.assertEqual("FEATURE_NOT_FOUND", missing.exception.code)
        self.assertEqual("demo:missing", missing.exception.details["feature"])
        self.assertFalse(missing.exception.details["mutated"])
        with self.assertRaises(OperationError) as unsupported:
            generation_ops.generate_animation(self.store, {"id": "demo:spin"}, revision)
        self.assertEqual("FEATURE_GENERATION_BLOCKED", unsupported.exception.code)
        self.assertEqual(revision, self.store.revision)

    def test_revision_conflict_prevents_generation_and_custom_paths_are_protected(self) -> None:
        stale = self.store.revision
        self.store.commit({"reports/concurrent.json": {"changed": True}})
        with self.assertRaises(ProjectError) as conflict:
            generation_ops.generate_pack(self.store, {}, stale)
        self.assertEqual("REVISION_CONFLICT", conflict.exception.code)
        self.assertFalse(self.store.resolve("reports/generation/generate_pack.json").exists())


if __name__ == "__main__":
    unittest.main()
