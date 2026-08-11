import json
import importlib.util
import unittest
from pathlib import Path

import author_creatures as author
import build_report
import validate_native_exports as static_validation


PACKET = Path("/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-003-crystal-marsh")
HERE = Path(__file__).resolve().parent
CONTACTS_SPEC = importlib.util.spec_from_file_location("crystal_creature_contacts", HERE / "build_contact_sheets.py")
contacts = importlib.util.module_from_spec(CONTACTS_SPEC)
assert CONTACTS_SPEC.loader is not None
CONTACTS_SPEC.loader.exec_module(contacts)


class CrystalMarshCreatureNativeTest(unittest.TestCase):
    def test_scope_and_clip_total_are_exact(self):
        self.assertEqual(list(author.SPECS), ["crystal_newt", "prism_frog", "glass_heron", "mire_turtle", "bloom_crab", "reed_serpent", "bog_watcher"])
        self.assertEqual(sum(len(spec["clips"]) for spec in author.SPECS.values()), 39)

    def test_specs_bind_frozen_briefs_and_existing_bones(self):
        for asset, spec in author.SPECS.items():
            with self.subTest(asset=asset):
                brief = json.loads((PACKET / "assets" / "briefs" / f"{asset}.json").read_text())
                model = json.loads((PACKET / "assets" / "editable" / f"{asset}.bbmodel").read_text())
                self.assertEqual(brief["animations"], list(spec["clips"]))
                author.engine.validate_spec(asset, spec["clips"], set(author.engine.group_names(model)))

    def test_locator_plan_uses_canonical_exports(self):
        for asset in author.SPECS:
            brief = json.loads((PACKET / "assets" / "briefs" / f"{asset}.json").read_text())
            model = json.loads((PACKET / "assets" / "editable" / f"{asset}.bbmodel").read_text())
            geometry = json.loads((PACKET / "assets" / "export" / "models" / f"{asset}.geo.json").read_text())
            required = author.engine.native.required_names(brief["locators"], field="locators")
            exported = author.engine.native.exported_locator_specs(geometry, required)
            plan = author.engine.native.build_locator_plan(required, author.engine.group_names(model), exported, {name: row["source_parent"] for name, row in exported.items()})
            self.assertEqual(set(plan), set(required))
            self.assertTrue(all(row["parent"] == row["source_parent"] for row in plan.values()))

    def test_source_packet_textures_are_unchanged(self):
        for asset in author.SPECS:
            self.assertEqual((PACKET / "assets" / "editable" / f"{asset}.png").read_bytes(), (PACKET / "assets" / "export" / "textures" / f"{asset}.png").read_bytes())

    def test_native_receipts_and_proofs_if_present(self):
        if not (HERE / "evidence").exists():
            self.skipTest("native evidence not generated")
        for asset, spec in author.SPECS.items():
            root = HERE / "evidence" / asset
            receipt = json.loads((root / author.RECEIPT_NAME).read_text())
            self.assertEqual(receipt["status"], "PASS_NATIVE_REPAIR_GATE")
            self.assertEqual(receipt["schema"], "aionforge.wave1.crystal_marsh.creature_native.v1")
            self.assertEqual(receipt["integration_authority"], {"commit": author.INTEGRATION_COMMIT, "tree": author.INTEGRATION_TREE})
            self.assertEqual(receipt["native_result"]["blockbench_version"], "5.1.6")
            self.assertEqual(receipt["native_result"]["warning_count"], 0)
            self.assertEqual(receipt["native_result"]["error_count"], 0)
            self.assertEqual(receipt["proof_inventory"]["timeline"], len(spec["clips"]))
            self.assertEqual(receipt["brief_declared_clips"], list(spec["clips"]))
            self.assertTrue(receipt["native_exports"]["geometry"]["canonical_equivalent"])
            self.assertTrue(receipt["native_exports"]["animations"]["canonical_equivalent"])
            self.assertEqual(receipt["diagnostics"], [])
            for record in receipt["evidence_inputs"].values():
                self.assertEqual(author.engine.native.sha256_file(root / record["path"]), record["sha256"])
            self.assertEqual(author.engine.native.sha256_file(root / receipt["native_project"]["path"]), receipt["native_project"]["sha256"])
            self.assertEqual(author.engine.native.sha256_file(root / receipt["staged_texture"]["path"]), receipt["staged_texture"]["sha256"])
            for kind in ("geometry", "animations"):
                for pass_name in ("pass_1", "pass_2"):
                    record = receipt["native_exports"][kind][pass_name]
                    self.assertEqual(author.engine.native.sha256_file(root / record["path"]), record["sha256"])
            for screenshot in receipt["screenshots"]:
                path = root / screenshot["path"]
                self.assertEqual(author.engine.native.sha256_file(path), screenshot["sha256"])
                self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_native_projects_and_exports_use_portable_aionbound_identities(self):
        if not (HERE / "evidence").exists():
            self.skipTest("native evidence not generated")
        for asset, spec in author.SPECS.items():
            root = HERE / "evidence" / asset
            project = json.loads((root / "native-project" / f"{asset}.bbmodel").read_text())
            self.assertEqual(project["model_identifier"], f"aionbound.{asset}")
            self.assertNotIn("/Users/", json.dumps(project))
            self.assertEqual({texture["relative_path"] for texture in project["textures"]}, {f"textures/{asset}.png"})
            geometry = json.loads((root / "native-exports" / "pass-2.geo.json").read_text())
            self.assertEqual(geometry["minecraft:geometry"][0]["description"]["identifier"], f"geometry.aionbound.{asset}")
            animations = json.loads((root / "native-exports" / "pass-2.animation.json").read_text())["animations"]
            self.assertEqual(list(animations), [f"animation.aionbound.{asset}.{leaf}" for leaf in spec["clips"]])

    def test_aggregate_is_deterministic_if_present(self):
        if not build_report.OUTPUT.exists():
            self.skipTest("aggregate not generated")
        report = json.loads(build_report.OUTPUT.read_text())
        self.assertEqual(report, build_report.build())
        self.assertEqual(report["status"], "PASS_NATIVE_REPAIR_GATE")
        self.assertEqual(report["totals"], {"assets": 7, "brief_declared_clips": 39, "true_native_locators": 14, "screenshots": 95, "warnings": 0, "errors": 0})

    def test_contact_sheets_bind_exact_native_screenshot_inventories(self):
        manifest_path = HERE / "CRYSTAL_MARSH_CREATURE_NATIVE_CONTACT_SHEETS.json"
        if not manifest_path.exists():
            self.skipTest("contact sheets not generated")
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["schema"], "aionforge.wave1.crystal_marsh.creature_native_contact_sheets.v1")
        self.assertEqual([item["asset"] for item in manifest["assets"]], list(contacts.ASSETS))
        for item in manifest["assets"]:
            path = HERE / item["path"]
            receipt = json.loads((HERE / "evidence" / item["asset"] / author.RECEIPT_NAME).read_text())
            self.assertEqual(item["source_screenshot_count"], len(receipt["screenshots"]))
            self.assertEqual(contacts.sha256(path), item["sha256"])
            self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_static_validation_receipt_is_deterministic_and_exact(self):
        if not static_validation.OUTPUT.exists():
            self.skipTest("static validation not generated")
        receipt = json.loads(static_validation.OUTPUT.read_text())
        self.assertEqual(receipt, static_validation.build())
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual([item["asset"] for item in receipt["assets"]], list(author.SPECS))
        self.assertTrue(all(item["exit_code"] == 0 and item["required_locators"] == ["effect", "gaze"] for item in receipt["assets"]))


if __name__ == "__main__":
    unittest.main()
