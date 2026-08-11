import hashlib
import json
import unittest
from pathlib import Path

import author_landmarks as author
import build_landmark_report as aggregate


PACKET = Path("/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-002-ashen-highlands")
HERE = Path(__file__).resolve().parent


class AshenLandmarkNativeContractTest(unittest.TestCase):
    @staticmethod
    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_scope_is_exact_and_representatives_are_excluded(self):
        self.assertEqual(len(author.ASSETS), 8)
        self.assertNotIn("ember_forge", author.ASSETS)
        self.assertNotIn("ancient_kiln", author.ASSETS)

    def test_specs_bind_exact_brief_clips_and_existing_bones(self):
        for asset, spec in author.SPECS.items():
            brief = json.loads((PACKET / "assets" / "briefs" / f"{asset}.json").read_text())
            model = json.loads((PACKET / "assets" / "editable" / f"{asset}.bbmodel").read_text())
            self.assertEqual(brief["animations"], list(spec["clips"]), asset)
            self.assertEqual(brief["locators"], ["effect"], asset)
            self.assertEqual(brief["model_identifier"], f"geometry.aionforge_ah.{asset}")
            author.native_gate.validate_spec(asset, spec["clips"], set(author.native_gate.group_names(model)))

    def test_packet_editable_and_export_texture_bytes_match(self):
        for asset in author.ASSETS:
            editable = PACKET / "assets" / "editable" / f"{asset}.png"
            exported = PACKET / "assets" / "export" / "textures" / f"{asset}.png"
            self.assertEqual(editable.read_bytes(), exported.read_bytes(), asset)

    def test_receipts_if_present(self):
        evidence = HERE / "evidence"
        if not evidence.exists():
            self.skipTest("native evidence not generated yet")
        for asset, spec in author.SPECS.items():
            root = evidence / asset
            receipt = json.loads((root / author.RECEIPT_NAME).read_text())
            self.assertEqual(receipt["status"], "PASS_NATIVE_REPAIR_GATE", asset)
            self.assertEqual(receipt["native_result"]["blockbench_version"], "5.1.6")
            self.assertEqual(receipt["native_result"]["warning_count"], 0)
            self.assertEqual(receipt["native_result"]["error_count"], 0)
            self.assertEqual(receipt["brief_declared_clips"], list(spec["clips"]))
            self.assertEqual({name.rsplit(".", 1)[-1] for name in receipt["authored_clip_names"]}, set(spec["clips"]))
            self.assertTrue(receipt["texture_bytes_preserved"])
            self.assertTrue(receipt["native_exports"]["geometry"]["canonical_equivalent"])
            self.assertTrue(receipt["native_exports"]["animations"]["canonical_equivalent"])
            self.assertEqual(len(set(receipt["geometry_signatures_excluding_intended_locators"].values())), 1)
            self.assertEqual(receipt["proof_inventory"], {"native_views": 7, "atlas_uv": 1, "timeline": len(spec["clips"])})
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
        self.assertEqual(actual["excluded_representatives"], ["ember_forge", "ancient_kiln"])
        self.assertEqual(actual["totals"], {"assets": 8, "brief_declared_clips": 1, "true_native_locators": 8, "screenshots": 65, "warnings": 0, "errors": 0})
        self.assertTrue(all(item["texture_bytes_preserved"] for item in actual["assets"]))
        self.assertTrue(all(item["two_pass_geometry_equivalent"] for item in actual["assets"]))
        self.assertTrue(all(item["two_pass_animation_equivalent"] for item in actual["assets"]))
        self.assertTrue(all(item["geometry_uv_signature_preserved"] for item in actual["assets"]))
        self.assertIn("MCSTRUCTURE_ASSEMBLY", actual["proof_boundaries"]["does_not_prove"])


if __name__ == "__main__":
    unittest.main()
