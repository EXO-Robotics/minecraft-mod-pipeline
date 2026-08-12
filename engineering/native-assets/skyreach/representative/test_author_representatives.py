import json
import unittest
from pathlib import Path

import author_representatives as author
import build_contact_sheets as contacts
import build_representative_report as aggregate


PACKET = Path("/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-004-skyreach-cliffs")
HERE = Path(__file__).resolve().parent
EXPECTED = ["wind_roc", "gale_hawk", "cloud_goat", "wind_reed_plant", "hanging_sky_vine", "wind_shrine", "observation_tower"]


class RepresentativeContractTest(unittest.TestCase):
    def test_scope_is_exact(self):
        self.assertEqual(list(author.SPECS), EXPECTED)

    def test_specs_bind_exactly_to_frozen_briefs_and_existing_bones(self):
        for asset, spec in author.SPECS.items():
            with self.subTest(asset=asset):
                brief = json.loads((PACKET / "assets" / "briefs" / f"{asset}.json").read_text())
                model = json.loads((PACKET / "assets" / "editable" / f"{asset}.bbmodel").read_text())
                self.assertEqual(brief["animations"], list(spec["clips"]))
                groups = set(author.group_names(model))
                author.validate_spec(asset, spec["clips"], groups)

    def test_locator_parents_and_transforms_are_canonical(self):
        for asset in author.SPECS:
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
            self.assertEqual((PACKET / "assets" / "editable" / f"{asset}.png").read_bytes(), (PACKET / "assets" / "export" / "textures" / f"{asset}.png").read_bytes())

    def test_fail_closed_animation_validation(self):
        bad = {"idle": author.clip(1.0, True, 0.5, {"invented_bone": [author.frames("rotation", (0.0, author.ZERO), (0.5, [1.0, 0.0, 0.0]), (1.0, author.ZERO))]})}
        with self.assertRaisesRegex(author.RepresentativeError, "UNBOUND_ANIMATION_PARENT"):
            author.validate_spec("test", bad, {"root"})

    def test_existing_receipts_if_present(self):
        evidence = HERE / "evidence"
        if not evidence.exists():
            self.skipTest("native evidence not generated yet")
        total_clips = 0
        for asset, spec in author.SPECS.items():
            root = evidence / asset
            receipt = json.loads((root / author.RECEIPT_NAME).read_text())
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
        self.assertEqual(total_clips, 18)

    def test_aggregate_receipt_is_deterministic_and_bounded(self):
        if not aggregate.OUTPUT.exists():
            self.skipTest("aggregate native report not generated yet")
        actual = json.loads(aggregate.OUTPUT.read_text())
        self.assertEqual(actual, aggregate.build())
        self.assertEqual(actual["status"], "PASS_NATIVE_REPAIR_GATE")
        self.assertEqual(actual["scope"], EXPECTED)
        self.assertEqual(actual["totals"], {"assets": 7, "brief_declared_clips": 18, "true_native_locators": 10, "screenshots": 74, "warnings": 0, "errors": 0})
        self.assertTrue(all(all(item["checks"].values()) for item in actual["assets"]))

    def test_receipt_hashes_and_png_proofs_are_exact(self):
        if not (HERE / "evidence").exists():
            self.skipTest("native evidence not generated yet")
        for asset in author.SPECS:
            root = HERE / "evidence" / asset
            receipt = json.loads((root / author.RECEIPT_NAME).read_text())
            for record in receipt["evidence_inputs"].values():
                self.assertEqual(author.native.sha256_file(root / record["path"]), record["sha256"])
            for screenshot in receipt["screenshots"]:
                proof = root / screenshot["path"]
                self.assertEqual(author.native.sha256_file(proof), screenshot["sha256"])
                self.assertEqual(proof.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_contact_sheets_bind_exact_native_screenshot_inventories(self):
        manifest_path = HERE / "SKYREACH_REPRESENTATIVE_CONTACT_SHEETS.json"
        if not manifest_path.exists():
            self.skipTest("contact sheets not generated yet")
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["schema"], "aionforge.wave1.skyreach.native_contact_sheets.v1")
        self.assertEqual([item["asset"] for item in manifest["assets"]], list(contacts.ASSETS))


if __name__ == "__main__":
    unittest.main()
