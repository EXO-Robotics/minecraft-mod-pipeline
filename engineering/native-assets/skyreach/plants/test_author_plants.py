import json
import unittest
from pathlib import Path

import author_plants as author
import build_plant_report as aggregate


PACKET = Path("/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-004-skyreach-cliffs")
HERE = Path(__file__).resolve().parent


class SkyreachPlantContractTest(unittest.TestCase):
    def test_scope_is_exact_and_representatives_are_excluded(self):
        self.assertEqual(list(author.SPECS), list(author.ASSETS))
        self.assertEqual(len(author.ASSETS), 8)
        self.assertNotIn("wind_reed_plant", author.ASSETS)
        self.assertNotIn("hanging_sky_vine", author.ASSETS)

    def test_specs_bind_exact_brief_clips_and_existing_bones(self):
        for asset, spec in author.SPECS.items():
            with self.subTest(asset=asset):
                brief = json.loads((PACKET / "assets" / "briefs" / f"{asset}.json").read_text())
                model = json.loads((PACKET / "assets" / "editable" / f"{asset}.bbmodel").read_text())
                self.assertEqual(brief["animations"], list(spec["clips"]))
                groups = set(author.native_gate.group_names(model))
                author.native_gate.validate_spec(asset, spec["clips"], groups)
                authored = {bone for clip in spec["clips"].values() for bone in clip["bones"]}
                self.assertLessEqual(authored, groups)

    def test_no_generic_idle_or_action_aliases(self):
        for asset, spec in author.SPECS.items():
            with self.subTest(asset=asset):
                self.assertFalse({"idle", "action"} & set(spec["clips"]))

    def test_locator_parents_and_transforms_are_canonical(self):
        for asset in author.ASSETS:
            with self.subTest(asset=asset):
                brief = json.loads((PACKET / "assets" / "briefs" / f"{asset}.json").read_text())
                model = json.loads((PACKET / "assets" / "editable" / f"{asset}.bbmodel").read_text())
                geometry = json.loads((PACKET / "assets" / "export" / "models" / f"{asset}.geo.json").read_text())
                required = author.native_gate.native.required_names(brief["locators"], field="locators")
                exported = author.native_gate.native.exported_locator_specs(geometry, required)
                plan = author.native_gate.native.build_locator_plan(
                    required,
                    author.native_gate.group_names(model),
                    exported,
                    {name: record["source_parent"] for name, record in exported.items()},
                )
                self.assertEqual(set(plan), set(required))
                self.assertTrue(all(record["parent"] == record["source_parent"] for record in plan.values()))

    def test_packet_textures_are_exact(self):
        for asset in author.ASSETS:
            source = PACKET / "assets" / "editable" / f"{asset}.png"
            export = PACKET / "assets" / "export" / "textures" / f"{asset}.png"
            self.assertEqual(source.read_bytes(), export.read_bytes())

    def test_existing_receipts(self):
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
            self.assertEqual(receipt["brief_declared_clips"], list(spec["clips"]))
            self.assertEqual(receipt["authored_clip_names"], [f"animation.aionbound.{asset}.{leaf}" for leaf in spec["clips"]])
            self.assertEqual(receipt["diagnostics"], [])
            self.assertFalse(receipt["scope_enforcement"]["representative_wind_reed_plant_edited"])
            self.assertFalse(receipt["scope_enforcement"]["representative_hanging_sky_vine_edited"])
            total_clips += len(spec["clips"])
        self.assertEqual(total_clips, 2)

    def test_receipt_file_hashes_and_png_proofs_are_exact(self):
        evidence = HERE / "evidence"
        if not evidence.exists():
            self.skipTest("native evidence not generated yet")
        for asset in author.ASSETS:
            root = evidence / asset
            receipt = json.loads((root / author.RECEIPT_NAME).read_text())
            for record in receipt["evidence_inputs"].values():
                self.assertEqual(author.native_gate.native.sha256_file(root / record["path"]), record["sha256"])
            self.assertEqual(author.native_gate.native.sha256_file(root / receipt["native_project"]["path"]), receipt["native_project"]["sha256"])
            self.assertEqual(author.native_gate.native.sha256_file(root / receipt["staged_texture"]["path"]), receipt["staged_texture"]["sha256"])
            for kind in ("geometry", "animations"):
                for pass_name in ("pass_1", "pass_2"):
                    record = receipt["native_exports"][kind][pass_name]
                    self.assertEqual(author.native_gate.native.sha256_file(root / record["path"]), record["sha256"])
            for screenshot in receipt["screenshots"]:
                proof = root / screenshot["path"]
                self.assertEqual(author.native_gate.native.sha256_file(proof), screenshot["sha256"])
                self.assertEqual(proof.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_aggregate_is_deterministic_and_bounded(self):
        if not aggregate.OUTPUT.exists():
            self.skipTest("aggregate not generated yet")
        actual = json.loads(aggregate.OUTPUT.read_text())
        self.assertEqual(actual, aggregate.build())
        self.assertEqual(actual["status"], "PASS_NATIVE_REPAIR_GATE")
        self.assertEqual(actual["scope"], list(author.ASSETS))
        self.assertEqual(actual["excluded_representatives"], ["wind_reed_plant", "hanging_sky_vine"])
        self.assertEqual(actual["totals"], {"assets": 8, "brief_declared_clips": 2, "true_native_locators": 8, "screenshots": 66, "warnings": 0, "errors": 0})
        self.assertIn("BDS", actual["proof_boundaries"]["does_not_prove"])


if __name__ == "__main__":
    unittest.main()
