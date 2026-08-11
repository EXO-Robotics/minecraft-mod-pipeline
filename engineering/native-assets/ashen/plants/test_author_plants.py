import hashlib
import json
import unittest
from pathlib import Path

import author_plants as author
import build_plant_report as aggregate


PACKET = Path("/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-002-ashen-highlands")
HERE = Path(__file__).resolve().parent


class AshenPlantNativeContractTest(unittest.TestCase):
    @staticmethod
    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_scope_is_exact_and_representatives_are_excluded(self):
        self.assertEqual(len(author.ASSETS), 8)
        self.assertNotIn("fire_bloom", author.ASSETS)
        self.assertNotIn("smoke_reed", author.ASSETS)

    def test_frozen_briefs_declare_no_clips_and_one_effect_locator(self):
        for asset in author.ASSETS:
            brief = json.loads((PACKET / "assets" / "briefs" / f"{asset}.json").read_text())
            self.assertEqual(brief["animations"], [], asset)
            self.assertEqual(brief["locators"], ["effect"], asset)
            self.assertEqual(brief["model_identifier"], f"geometry.aionforge_ah.{asset}")

    def test_packet_editable_and_export_texture_bytes_match(self):
        for asset in author.ASSETS:
            editable = PACKET / "assets" / "editable" / f"{asset}.png"
            exported = PACKET / "assets" / "export" / "textures" / f"{asset}.png"
            self.assertEqual(editable.read_bytes(), exported.read_bytes(), asset)

    def test_receipts_if_present(self):
        evidence = HERE / "evidence"
        if not evidence.exists():
            self.skipTest("native evidence not generated yet")
        for asset in author.ASSETS:
            root = evidence / asset
            receipt = json.loads((root / author.RECEIPT_NAME).read_text())
            self.assertEqual(receipt["status"], "PASS_NATIVE_REPAIR_GATE", asset)
            self.assertEqual(receipt["native_result"]["blockbench_version"], "5.1.6")
            self.assertEqual(receipt["native_result"]["warning_count"], 0)
            self.assertEqual(receipt["native_result"]["error_count"], 0)
            self.assertEqual(receipt["brief_declared_clips"], [])
            self.assertEqual(receipt["authored_clip_names"], [])
            self.assertTrue(receipt["texture_bytes_preserved"])
            self.assertTrue(receipt["native_exports"]["geometry"]["canonical_equivalent"])
            self.assertTrue(receipt["native_exports"]["animations"]["canonical_equivalent"])
            self.assertEqual(len(set(receipt["geometry_signatures_excluding_intended_locators"].values())), 1)
            self.assertEqual(receipt["proof_inventory"], {"native_views": 7, "atlas_uv": 1, "timeline": 0})
            self.assertEqual(receipt["diagnostics"], [])
            for record in receipt["evidence_inputs"].values():
                self.assertEqual(self.sha256(root / record["path"]), record["sha256"])
            self.assertEqual(self.sha256(root / receipt["native_project"]["path"]), receipt["native_project"]["sha256"])
            self.assertEqual(self.sha256(root / receipt["staged_texture"]["path"]), receipt["staged_texture"]["sha256"])
            for kind in ("geometry", "animations"):
                for pass_name in ("pass_1", "pass_2"):
                    record = receipt["native_exports"][kind][pass_name]
                    self.assertEqual(self.sha256(root / record["path"]), record["sha256"])
            for screenshot in receipt["screenshots"]:
                proof = root / screenshot["path"]
                self.assertEqual(self.sha256(proof), screenshot["sha256"])
                self.assertEqual(proof.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_aggregate_if_present(self):
        if not aggregate.OUTPUT.exists():
            self.skipTest("aggregate report not generated yet")
        actual = json.loads(aggregate.OUTPUT.read_text())
        self.assertEqual(actual, aggregate.build())
        self.assertEqual(actual["status"], "PASS_NATIVE_REPAIR_GATE")
        self.assertEqual(actual["scope"], list(author.ASSETS))
        self.assertEqual(actual["excluded_representatives"], ["fire_bloom", "smoke_reed"])
        self.assertEqual(actual["totals"], {"assets": 8, "brief_declared_clips": 0, "true_native_locators": 8, "screenshots": 64, "warnings": 0, "errors": 0})
        self.assertTrue(all(item["texture_bytes_preserved"] for item in actual["assets"]))
        self.assertTrue(all(item["two_pass_geometry_equivalent"] for item in actual["assets"]))
        self.assertTrue(all(item["two_pass_animation_equivalent"] for item in actual["assets"]))
        self.assertTrue(all(item["geometry_uv_signature_preserved"] for item in actual["assets"]))


if __name__ == "__main__":
    unittest.main()
