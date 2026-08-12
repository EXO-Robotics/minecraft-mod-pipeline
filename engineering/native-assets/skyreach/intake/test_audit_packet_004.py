import json
import tempfile
import unittest
from pathlib import Path

import audit_packet_004 as audit


HERE = Path(__file__).resolve().parent
REPORT_PATH = HERE / "SKYREACH_PACKET_004_NATIVE_READINESS.json"
MARKDOWN_PATH = HERE / "SKYREACH_PACKET_004_NATIVE_READINESS.md"


class Packet004NativeReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.build_report(audit.DEFAULT_PACKET_ROOT)

    def test_exact_authority_and_scope(self):
        scope = self.report["audit_scope"]
        self.assertEqual(scope["integration_commit"], "1810d0bb75e73be16d1c98e1d57dfe9ea485849d")
        self.assertEqual(scope["integration_tree"], "11f377745f69b848396780dac1d039955fa90131")
        self.assertTrue(scope["read_only_packet_audit"])
        self.assertFalse(scope["blockbench_launched"])
        self.assertFalse(scope["packet_assets_edited"])
        self.assertFalse(scope["bp_rp_touched"])

    def test_complete_exact_inventory_and_hashes(self):
        summary = self.report["summary"]
        self.assertEqual(summary["asset_count"], 50)
        self.assertEqual(summary["tier_counts"], {"BLOCK": 10, "CREATURE": 10, "LANDMARK": 10, "PLANT": 10, "RESOURCE": 10})
        self.assertEqual(summary["complete_artifact_sets"], 50)
        self.assertTrue(summary["all_hashes_sha256"])
        self.assertTrue(summary["all_json_parsed"])
        self.assertTrue(summary["all_pngs_decoded"])
        self.assertEqual(summary["exact_category_mirrors"], 50)
        self.assertEqual(summary["source_namespace_consistent"], 50)

    def test_native_blockers_are_measured_not_promoted(self):
        summary = self.report["summary"]
        self.assertEqual(summary["real_editable_locator_assets"], 0)
        self.assertEqual(summary["exported_locator_sets_match_briefs"], 50)
        self.assertEqual(summary["declared_clip_sets_match_exports"], 0)
        self.assertEqual(summary["texture_contract_compatible"] + summary["texture_contract_mismatch"], 50)
        self.assertEqual(summary["absolute_editable_texture_path_assets"], 50)
        self.assertEqual(summary["portfolio_native_status"], "NOT_READY_NATIVE_REPAIR_REQUIRED")
        self.assertTrue(all(asset["native_export_equivalence"] == "UNPROVEN" for asset in self.report["assets"]))

    def test_blockbench_disposition_is_class_specific(self):
        native = [asset for asset in self.report["assets"] if asset["blockbench_disposition"] == "NATIVE_REPAIR_REQUIRED"]
        not_applicable = [asset for asset in self.report["assets"] if asset["blockbench_disposition"].startswith("NOT_APPLICABLE")]
        self.assertEqual(len(native), 30)
        self.assertEqual({asset["tier"] for asset in native}, {"CREATURE", "PLANT", "LANDMARK"})
        self.assertEqual(len(not_applicable), 20)
        self.assertEqual({asset["tier"] for asset in not_applicable}, {"BLOCK", "RESOURCE"})

    def test_exact_representative_gaps_are_bound(self):
        by_name = {asset["name"]: asset for asset in self.report["assets"]}
        roc = by_name["wind_roc"]
        comparison = roc["declared_vs_actual"]
        self.assertEqual(comparison["real_editable_locator_elements"], [])
        self.assertEqual(comparison["exported_geometry_locators"], ["effect", "gaze"])
        self.assertEqual(comparison["missing_declared_role_clips"], ["death", "dive", "hurt", "idle_perch", "soar"])
        self.assertEqual(comparison["generic_or_extra_exported_clips"], ["action", "idle"])
        self.assertEqual(comparison["texture_contract"], "128×64")
        self.assertEqual(comparison["decoded_texture_resolution"], [32, 32])
        self.assertTrue(roc["path_normalization"]["requires_relative_shipping_path_rebind"])
        self.assertEqual([term["resolved_packet_warehouse_ids"] for term in roc["related_asset_bindings"]["terms"]], [["nest_platform"], ["storm_pinion"]])

    def test_representative_gate_and_repair_order_are_bounded(self):
        representatives = [entry["name"] for entry in self.report["representative_class_gate"]["assets_in_order"]]
        self.assertEqual(representatives, ["wind_roc", "gale_hawk", "cloud_goat", "wind_reed_plant", "hanging_sky_vine", "wind_shrine", "observation_tower"])
        stages = self.report["bounded_repair_order"]
        self.assertEqual([stage["stage"] for stage in stages], [1, 2, 3, 4, 5])
        flattened = [name for stage in stages for name in stage["assets"]]
        self.assertEqual(len(flattened), 50)
        self.assertEqual(len(set(flattened)), 50)
        self.assertEqual(set(flattened), {asset["name"] for asset in self.report["assets"]})

    def test_committed_reports_are_deterministic(self):
        expected_json = json.dumps(self.report, indent=2, sort_keys=True) + "\n"
        expected_markdown = audit.render_markdown(self.report)
        self.assertEqual(REPORT_PATH.read_text(encoding="utf-8"), expected_json)
        self.assertEqual(MARKDOWN_PATH.read_text(encoding="utf-8"), expected_markdown)
        with tempfile.TemporaryDirectory() as directory:
            one = Path(directory) / "one.json"
            two = Path(directory) / "two.json"
            one.write_text(expected_json, encoding="utf-8")
            two.write_text(json.dumps(audit.build_report(audit.DEFAULT_PACKET_ROOT), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            self.assertEqual(one.read_bytes(), two.read_bytes())


if __name__ == "__main__":
    unittest.main()
