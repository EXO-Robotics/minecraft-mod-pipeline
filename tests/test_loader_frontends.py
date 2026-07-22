from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from mccompiler.scan import scan_path


FIXTURES = Path(__file__).parent / "fixtures" / "frontends"


class LoaderFrontendTests(unittest.TestCase):
    def test_conventional_fabric_source_tree_and_registration_helper(self):
        ir = scan_path(FIXTURES / "fabric_source_tree")
        self.assertEqual("source_tree", ir["mods"][0]["id"])
        self.assertEqual("fabric", ir["mods"][0]["loader"])
        self.assertEqual({("item", "source_tree:key")}, {(row["kind"], row["identifier"]) for row in ir["content"]})
        behavior = next(row for row in ir["behaviors"] if row["trigger"]["type"] == "item_use_on_block")
        self.assertEqual("fabric-source:Item.useOnBlock", behavior["evidence"][0]["extraction_rule"])

    def test_modern_fabric_metadata_is_lossless_and_source_evidence_is_scoped(self):
        root = FIXTURES / "fabric_modern"
        raw = (root / "fabric.mod.json").read_text()
        document = json.loads(raw)
        ir = scan_path(root)

        mod = next(row for row in ir["mods"] if row["id"] == "authentic_fabric")
        self.assertEqual("fabric", mod["loader"])
        self.assertEqual(document, mod["metadata"]["raw"])
        self.assertEqual(document["entrypoints"], mod["metadata"]["entrypoints"])
        self.assertEqual(document["jars"], mod["metadata"]["nested_jars"])
        provenance = next(row for row in mod["metadata_evidence"] if row["kind"] == "fabric.mod.json")
        self.assertEqual(raw, provenance["raw_text"])
        self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(), provenance["sha256"])

        self.assertEqual(
            {("item", "authentic_fabric:wand"), ("block", "authentic_fabric:machine")},
            {(row["kind"], row["identifier"]) for row in ir["content"]},
        )
        self.assertEqual({"item_use", "entity_hit", "object_tick"}, {row["trigger"]["type"] for row in ir["behaviors"]})
        self.assertEqual({"fixture_world_state"}, {row["id"] for row in ir["state"]})
        self.assertEqual(1, len(ir["networking_intent"]))
        self.assertTrue(all(row["evidence"] for row in ir["content"] + ir["behaviors"] + ir["state"] + ir["networking_intent"]))
        self.assertTrue(any(row["feature"].startswith("fabric_mixin:") for row in ir["unsupported_hooks"]))
        entrypoint = next(row for row in ir["diagnostics"] if row["code"] == "loader_entrypoint")
        self.assertEqual("fabric-source:ModInitializer", entrypoint["evidence"][0]["extraction_rule"])

    def test_forge_1_7_10_metadata_manifest_and_source_patterns(self):
        root = FIXTURES / "forge_1_7_10"
        raw_info = (root / "mcmod.info").read_text()
        raw_manifest = (root / "META-INF/MANIFEST.MF").read_text()
        document = json.loads(raw_info)
        ir = scan_path(root)

        mod = next(row for row in ir["mods"] if row["id"] == "authentic_legacy")
        self.assertEqual("forge-legacy", mod["loader"])
        self.assertEqual(document[0], mod["metadata"]["raw"])
        self.assertEqual("fixture.legacy.AuthenticCorePlugin", mod["metadata"]["manifest"]["FMLCorePlugin"])
        self.assertEqual({"Forge", "examplemod"}, {row["id"] for row in mod["dependencies"]})
        evidence = {row["kind"]: row for row in mod["metadata_evidence"]}
        self.assertEqual(raw_info, evidence["mcmod.info"]["raw_text"])
        self.assertEqual(raw_manifest, evidence["manifest"]["raw_text"])

        expected = {
            ("item", "authentic_legacy:legacy_wand"),
            ("block", "authentic_legacy:legacy_machine"),
            ("block_entity", "authentic_legacy:legacy_machine"),
            ("entity", "authentic_legacy:legacy_golem"),
        }
        self.assertTrue(expected <= {(row["kind"], row["identifier"]) for row in ir["content"]})
        event = next(row for row in ir["behaviors"] if row["id"].endswith("/onLivingHurt"))
        self.assertEqual("entity_hurt", event["trigger"]["type"])
        self.assertEqual("client_to_server", ir["networking_intent"][0]["direction"])
        features = {row["feature"] for row in ir["unsupported_hooks"]}
        self.assertIn("forge_coremod:fixture.legacy.AuthenticCorePlugin", features)
        self.assertTrue(any(value.startswith("forge_coremod_source:") for value in features))
        self.assertTrue(all(row["evidence"] for row in ir["content"] + ir["behaviors"] + ir["networking_intent"] + ir["unsupported_hooks"]))
        lifecycle = {row["event"] for row in ir["diagnostics"] if row["code"] == "loader_lifecycle"}
        self.assertEqual({"FMLPreInitializationEvent", "FMLInitializationEvent"}, lifecycle)


if __name__ == "__main__":
    unittest.main()
