import json
import struct
import unittest
from pathlib import Path

import author_equipment as author
import build_report


PACKET = Path("/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-006-equipment-progression")
HERE = Path(__file__).resolve().parent


class AshenEquipmentNativeTest(unittest.TestCase):
    def test_scope_is_exact_and_briar_ring_absent(self):
        self.assertEqual(list(author.SPECS), ["basalt_hammer", "ember_great_axe", "ash_repeater", "ashen_helmet", "ashen_chest", "ashen_legs", "ashen_boots", "basalt_pick", "ember_hammer", "ore_chisel", "ember_totem", "ash_drake_horn", "ember_forge_core"])
        self.assertNotIn("briar_ring", author.SPECS)
        self.assertEqual(sum(len(row["clips"]) for row in author.SPECS.values()), 18)

    def test_specs_bind_exact_briefs_and_bones(self):
        for asset, spec in author.SPECS.items():
            brief = json.loads((PACKET / "assets/briefs" / f"{asset}.json").read_text())
            model = json.loads((PACKET / "assets/editable" / f"{asset}.bbmodel").read_text())
            self.assertEqual(brief["animations"], list(spec["clips"]))
            self.assertEqual(brief["model_identifier"], f"geometry.aionforge_eq.{asset}")
            author.engine.validate_spec(asset, spec["clips"], set(author.engine.group_names(model)))

    def test_source_textures_are_exact_32x32_rgba_and_match_exports(self):
        for asset in author.SPECS:
            source = PACKET / "assets/editable" / f"{asset}.png"
            export = PACKET / "assets/export/textures" / f"{asset}.png"
            data = source.read_bytes()
            self.assertEqual(data, export.read_bytes())
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            width, height, depth, color = struct.unpack(">IIBB", data[16:26])
            self.assertEqual((width, height, depth, color), (32, 32, 8, 6))

    def test_effect_locator_uses_canonical_export(self):
        for asset in author.SPECS:
            brief = json.loads((PACKET / "assets/briefs" / f"{asset}.json").read_text())
            model = json.loads((PACKET / "assets/editable" / f"{asset}.bbmodel").read_text())
            geometry = json.loads((PACKET / "assets/export/models" / f"{asset}.geo.json").read_text())
            required = author.engine.native.required_names(brief["locators"], field="locators")
            exported = author.engine.native.exported_locator_specs(geometry, required)
            plan = author.engine.native.build_locator_plan(required, author.engine.group_names(model), exported, {name: row["source_parent"] for name, row in exported.items()})
            self.assertEqual(set(plan), {"effect"})

    def test_receipts_if_present(self):
        if not (HERE / "evidence").exists():
            self.skipTest("evidence not generated")
        for asset, spec in author.SPECS.items():
            root = HERE / "evidence" / asset
            receipt = json.loads((root / author.RECEIPT_NAME).read_text())
            self.assertEqual(receipt["status"], "PASS_NATIVE_REPAIR_GATE")
            self.assertEqual(receipt["schema"], "aionforge.wave1.ashen.equipment_native.v1")
            self.assertEqual(receipt["packet_brief_identity"], f"geometry.aionforge_eq.{asset}")
            self.assertEqual(receipt["native_result"]["blockbench_version"], "5.1.6")
            self.assertEqual(receipt["native_result"]["warning_count"], 0)
            self.assertEqual(receipt["native_result"]["error_count"], 0)
            self.assertEqual(receipt["proof_inventory"]["timeline"], len(spec["clips"]))
            self.assertEqual(receipt["diagnostics"], [])
            self.assertTrue(receipt["texture_bytes_preserved"])
            self.assertTrue(receipt["native_exports"]["geometry"]["canonical_equivalent"])
            self.assertTrue(receipt["native_exports"]["animations"]["canonical_equivalent"])
            self.assertEqual((root / receipt["evidence_inputs"]["brief"]["path"]).read_bytes(), (PACKET / "assets/briefs" / f"{asset}.json").read_bytes())
            for record in receipt["evidence_inputs"].values():
                self.assertEqual(author.engine.native.sha256_file(root / record["path"]), record["sha256"])
            for screenshot in receipt["screenshots"]:
                path = root / screenshot["path"]
                self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(author.engine.native.sha256_file(path), screenshot["sha256"])

    def test_aggregate_if_present(self):
        if not build_report.OUTPUT.exists():
            self.skipTest("aggregate not generated")
        report = json.loads(build_report.OUTPUT.read_text())
        self.assertEqual(report, build_report.build())
        self.assertEqual(report["status"], "PASS_NATIVE_REPAIR_GATE")
        self.assertEqual(report["totals"], {"assets": 13, "brief_declared_clips": 18, "true_native_locators": 13, "screenshots": 122, "warnings": 0, "errors": 0})
        self.assertEqual(report["excluded_and_unchanged"]["briar_ring"], "EXISTING_WHISPERWOOD_BASE_W1_CREATIVE_005_DEFERRED")


if __name__ == "__main__":
    unittest.main()
