from __future__ import annotations

import json
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
        self.store.commit({"decisions/mappings.json": {
            "schema_version": "1.0.0", "mappings": [{
                "source_id": "custom/assets/owned.txt", "pack": "resource",
                "destination": "textures/custom/owned.txt", "provenance": {"author": "test", "reason": "fixture"},
            }],
        }}, expected_revision=self.store.revision)
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

    def test_custom_implementations_are_registered_staged_reported_and_packaged(self) -> None:
        custom = {
            "custom/scripts/clock.js": "import { world } from '@minecraft/server';\nexport const ready = !!world;\n",
            "custom/entities/clock.json": '{"format_version":"1.20.0","minecraft:entity":{"description":{"identifier":"demo:clock","is_spawnable":false,"is_summonable":true},"components":{}}}\n',
            "custom/models/clock.geo.json": '{"format_version":"1.12.0","minecraft:geometry":[]}\n',
            "custom/assets/clock.png": b"custom-png-fixture",
        }
        originals: dict[str, bytes] = {}
        for relative, content in custom.items():
            path = self.store.resolve(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content if isinstance(content, bytes) else content.encode())
            originals[relative] = path.read_bytes()
        self.store.commit({
            "decisions/custom-handlers.json": {"schema_version": "1.0.0", "handlers": [{
                "behavior_id": "demo:clock/use", "source_path": "custom/scripts/clock.js",
                "destination": "scripts/custom/clock.js",
                "api_symbols": [{"module": "@minecraft/server", "symbol": "world.afterEvents.itemUse"}],
                "provenance": {"author": "test", "reason": "reviewed implementation"},
            }]},
            "decisions/mappings.json": {"schema_version": "1.0.0", "mappings": [
                {"source_id": "custom/entities/clock.json", "pack": "behavior", "destination": "entities/clock.json"},
                {"source_id": "custom/models/clock.geo.json", "pack": "resource", "destination": "models/entity/clock.geo.json"},
                {"source_id": "custom/assets/clock.png", "pack": "resource", "destination": "textures/custom/clock.png"},
            ]},
        }, expected_revision=self.store.revision)

        first, _, _ = generation_ops.generate_pack(self.store, {}, self.store.revision)
        first_hash = next(row["sha256"] for row in first["artifacts"] if row["kind"] == "generated_archive")
        for relative, content in originals.items():
            self.assertEqual(content, self.store.resolve(relative).read_bytes())
        expected = {
            "bedrock/behavior_pack/scripts/custom/clock.js",
            "bedrock/behavior_pack/entities/clock.json",
            "bedrock/resource_pack/models/entity/clock.geo.json",
            "bedrock/resource_pack/textures/custom/clock.png",
        }
        self.assertTrue(all(self.store.resolve(path).is_file() for path in expected))
        api = json.loads(self.store.resolve("reports/backend/api-usage.json").read_text())
        self.assertTrue(api["complete"])
        self.assertIn(("@minecraft/server", "world.afterEvents.itemUse"), {(row["module"], row["symbol"]) for row in api["symbols"]})
        integration = json.loads(self.store.resolve("reports/backend/custom-integrations.json").read_text())
        self.assertEqual(4, len(integration["integrations"]))
        self.assertTrue(all(row["sha256"] for row in integration["integrations"]))

        second, _, _ = generation_ops.generate_pack(self.store, {}, self.store.revision)
        self.assertEqual(first_hash, next(row["sha256"] for row in second["artifacts"] if row["kind"] == "generated_archive"))
        packaged, _, artifacts = generation_ops.package_mcaddon(self.store, {}, self.store.revision)
        self.assertEqual("PACKAGED", packaged["status"])
        with zipfile.ZipFile(self.store.resolve(artifacts[0]["path"])) as bundle:
            names = set(bundle.namelist())
        self.assertIn("behavior_pack/scripts/custom/clock.js", names)
        self.assertIn("behavior_pack/entities/clock.json", names)
        self.assertIn("resource_pack/models/entity/clock.geo.json", names)
        self.assertIn("resource_pack/textures/custom/clock.png", names)
        self.assertFalse(any(name.startswith("custom/") or name.startswith("reports/") for name in names))

    def test_custom_content_fails_closed_without_mapping_or_api_metadata(self) -> None:
        script = self.store.resolve("custom/scripts/unreviewed.js")
        script.write_text("export const unsafe = true;\n", encoding="utf-8")
        revision = self.store.revision
        with self.assertRaises(ProjectError) as unregistered:
            generation_ops.generate_pack(self.store, {}, revision)
        self.assertEqual("UNREGISTERED_CUSTOM_IMPLEMENTATION", unregistered.exception.code)
        self.assertEqual(revision, self.store.revision)
        self.assertFalse(self.store.resolve("reports/generation/generate_pack.json").exists())

        self.store.commit({"decisions/custom-handlers.json": {"schema_version": "1.0.0", "handlers": [{
            "behavior_id": "demo:unsafe", "source_path": "custom/scripts/unreviewed.js",
            "destination": "scripts/custom/unreviewed.js",
        }]}}, expected_revision=revision)
        with self.assertRaises(ProjectError) as metadata:
            generation_ops.generate_pack(self.store, {}, self.store.revision)
        self.assertEqual("MISSING_CUSTOM_API_METADATA", metadata.exception.code)

        handlers = self.store.read("decisions/custom-handlers.json")
        handlers["handlers"][0]["api_symbols"] = [{"module": "@minecraft/server", "symbol": "world.futureUncataloguedEvent"}]
        self.store.commit({"decisions/custom-handlers.json": handlers}, expected_revision=self.store.revision)
        generation_ops.generate_pack(self.store, {}, self.store.revision)
        api = json.loads(self.store.resolve("reports/backend/api-usage.json").read_text())
        self.assertFalse(api["complete"])
        self.assertEqual(
            [{"module": "@minecraft/server", "symbol": "world.futureUncataloguedEvent"}],
            api["uncatalogued_symbols"],
        )

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
