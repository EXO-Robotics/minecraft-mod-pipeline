import json
import unittest
from pathlib import Path

import author_representatives as author
import build_representative_report as aggregate
import build_contact_sheets as contacts


PACKET = Path("/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-003-crystal-marsh")
HERE = Path(__file__).resolve().parent


class RepresentativeContractTest(unittest.TestCase):
    def test_scope_is_exact(self):
        self.assertEqual(
            list(author.SPECS),
            ["marsh_wight", "crystal_dragonfly", "silt_crocodile", "bubble_pod", "flood_reed", "sunken_shrine", "ancient_boat"],
        )

    def test_specs_bind_exactly_to_frozen_briefs_and_existing_bones(self):
        for asset, spec in author.SPECS.items():
            with self.subTest(asset=asset):
                brief = json.loads((PACKET / "assets" / "briefs" / f"{asset}.json").read_text())
                model = json.loads((PACKET / "assets" / "editable" / f"{asset}.bbmodel").read_text())
                self.assertEqual(brief["animations"], list(spec["clips"]))
                groups = set(author.group_names(model))
                author.validate_spec(asset, spec["clips"], groups)
                authored = {bone for clip in spec["clips"].values() for bone in clip["bones"]}
                self.assertLessEqual(authored, groups)

    def test_locator_parents_and_transforms_are_canonical(self):
        for asset in author.SPECS:
            with self.subTest(asset=asset):
                brief = json.loads((PACKET / "assets" / "briefs" / f"{asset}.json").read_text())
                model = json.loads((PACKET / "assets" / "editable" / f"{asset}.bbmodel").read_text())
                geometry = json.loads((PACKET / "assets" / "export" / "models" / f"{asset}.geo.json").read_text())
                required = author.native.required_names(brief["locators"], field="locators")
                exported = author.native.exported_locator_specs(geometry, required)
                plan = author.native.build_locator_plan(required, author.group_names(model), exported, {name: record["source_parent"] for name, record in exported.items()})
                self.assertEqual(set(plan), set(required))
                self.assertTrue(all(record["parent"] == record["source_parent"] for record in plan.values()))

    def test_source_packet_textures_are_not_reauthored(self):
        for asset in author.SPECS:
            source = PACKET / "assets" / "editable" / f"{asset}.png"
            export = PACKET / "assets" / "export" / "textures" / f"{asset}.png"
            self.assertEqual(source.read_bytes(), export.read_bytes())

    def test_fail_closed_on_unbound_animation_parent(self):
        bad = {"idle": author.clip(1.0, True, 0.5, {"invented_bone": [author.frames("rotation", (0.0, author.ZERO), (0.5, [1.0, 0.0, 0.0]), (1.0, author.ZERO))]})}
        with self.assertRaisesRegex(author.RepresentativeError, "UNBOUND_ANIMATION_PARENT"):
            author.validate_spec("test", bad, {"root"})

    def test_fail_closed_on_non_looping_loop_seam(self):
        bad = {"idle": author.clip(1.0, True, 0.5, {"root": [author.frames("rotation", (0.0, author.ZERO), (1.0, [1.0, 0.0, 0.0]))]})}
        with self.assertRaisesRegex(author.RepresentativeError, "SPEC_LOOP_SEAM_INVALID"):
            author.validate_spec("test", bad, {"root"})

    def test_existing_receipts_if_present(self):
        evidence = HERE / "evidence"
        if not evidence.exists():
            self.skipTest("native evidence not generated yet")
        total_clips = 0
        for asset, spec in author.SPECS.items():
            receipt_path = evidence / asset / author.RECEIPT_NAME
            self.assertTrue(receipt_path.is_file())
            receipt = json.loads(receipt_path.read_text())
            self.assertEqual(receipt["status"], "PASS_NATIVE_REPAIR_GATE")
            self.assertEqual(receipt["native_result"]["blockbench_version"], "5.1.6")
            self.assertEqual(receipt["native_result"]["warning_count"], 0)
            self.assertEqual(receipt["native_result"]["error_count"], 0)
            self.assertTrue(receipt["texture_bytes_preserved"])
            self.assertTrue(receipt["native_exports"]["geometry"]["canonical_equivalent"])
            self.assertTrue(receipt["native_exports"]["animations"]["canonical_equivalent"])
            self.assertEqual(len(set(receipt["geometry_signatures_excluding_intended_locators"].values())), 1)
            self.assertEqual(receipt["proof_inventory"]["timeline"], len(spec["clips"]))
            self.assertEqual(set(receipt["brief_declared_clips"]), set(spec["clips"]))
            self.assertEqual(receipt["diagnostics"], [])
            total_clips += len(spec["clips"])
        self.assertEqual(total_clips, 19)

    def test_aggregate_receipt_is_deterministic_and_bounded(self):
        if not aggregate.OUTPUT.exists():
            self.skipTest("aggregate native report not generated yet")
        actual = json.loads(aggregate.OUTPUT.read_text())
        self.assertEqual(actual, aggregate.build())
        self.assertEqual(actual["status"], "PASS_NATIVE_REPAIR_GATE")
        self.assertEqual(actual["scope"], list(aggregate.ASSETS))
        self.assertEqual(actual["totals"], {"assets": 7, "brief_declared_clips": 19, "true_native_locators": 10, "screenshots": 75, "warnings": 0, "errors": 0})
        self.assertTrue(all(all(item["checks"].values()) for item in actual["assets"]))
        self.assertIn("BDS", actual["proof_boundaries"]["does_not_prove"])

    def test_receipt_file_hashes_and_png_proof_are_exact(self):
        if not (HERE / "evidence").exists():
            self.skipTest("native evidence not generated yet")
        for asset in author.SPECS:
            root = HERE / "evidence" / asset
            receipt = json.loads((root / author.RECEIPT_NAME).read_text())
            for record in receipt["evidence_inputs"].values():
                self.assertEqual(author.native.sha256_file(root / record["path"]), record["sha256"])
            self.assertEqual(author.native.sha256_file(root / receipt["native_project"]["path"]), receipt["native_project"]["sha256"])
            self.assertEqual(author.native.sha256_file(root / receipt["staged_texture"]["path"]), receipt["staged_texture"]["sha256"])
            for kind in ("geometry", "animations"):
                for pass_name in ("pass_1", "pass_2"):
                    record = receipt["native_exports"][kind][pass_name]
                    self.assertEqual(author.native.sha256_file(root / record["path"]), record["sha256"])
            for screenshot in receipt["screenshots"]:
                proof = root / screenshot["path"]
                self.assertEqual(author.native.sha256_file(proof), screenshot["sha256"])
                self.assertEqual(proof.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_contact_sheets_bind_exact_native_screenshot_inventories(self):
        manifest_path = HERE / "CRYSTAL_MARSH_REPRESENTATIVE_CONTACT_SHEETS.json"
        if not manifest_path.exists():
            self.skipTest("contact sheets not generated yet")
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["schema"], "aionforge.wave1.crystal_marsh.native_contact_sheets.v1")
        self.assertEqual([item["asset"] for item in manifest["assets"]], list(contacts.ASSETS))
        for item in manifest["assets"]:
            path = HERE / item["path"]
            receipt = json.loads((HERE / "evidence" / item["asset"] / author.RECEIPT_NAME).read_text())
            self.assertEqual(item["source_screenshot_count"], len(receipt["screenshots"]))
            self.assertEqual(contacts.sha256(path), item["sha256"])
            self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
