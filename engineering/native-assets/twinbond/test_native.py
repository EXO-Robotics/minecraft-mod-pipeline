import json
import unittest
from pathlib import Path

import author_native as author
import build_report


HERE = Path(__file__).resolve().parent


class TwinbondNativeTest(unittest.TestCase):
    def test_scope_and_authority_are_exact(self):
        self.assertEqual(list(author.SPECS), ["ash_sovereign_wyrm", "tide_empress_wyrm", "twinbond_relic"])
        self.assertEqual(author.INTEGRATION_COMMIT, "50b683dfc3e390b19fc7900b88523c90bcc6a31d")
        self.assertEqual(author.INTEGRATION_TREE, "6dd2cd6547bfcb061083baa2a87e168f86b5d479")

    def test_native_receipts(self):
        for asset, spec in author.SPECS.items():
            with self.subTest(asset=asset):
                root = HERE / "evidence" / asset
                receipt = json.loads((root / author.RECEIPT_NAME).read_text())
                self.assertEqual(receipt["status"], "PASS_NATIVE_REPAIR_GATE")
                self.assertEqual(receipt["brief_declared_clips"], list(spec["clips"]))
                self.assertEqual(receipt["native_result"]["blockbench_version"], "5.1.6")
                self.assertEqual(receipt["native_result"]["warning_count"], 0)
                self.assertEqual(receipt["native_result"]["error_count"], 0)
                self.assertEqual(receipt["diagnostics"], [])
                self.assertTrue(receipt["texture_bytes_preserved"])
                self.assertTrue(receipt["native_exports"]["geometry"]["canonical_equivalent"])
                self.assertTrue(receipt["native_exports"]["animations"]["canonical_equivalent"])
                self.assertEqual(receipt["proof_inventory"], {"native_views": 7, "atlas_uv": 1, "timeline": len(spec["clips"])})
                for screenshot in receipt["screenshots"]:
                    path = root / screenshot["path"]
                    self.assertEqual(author.engine.native.sha256_file(path), screenshot["sha256"])
                    self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_phase_clip_authority_is_exact_and_fail_closed(self):
        required = ["split_approach", "concord_pressure", "relic_trial", "finale_ignition"]
        for asset in ("ash_sovereign_wyrm", "tide_empress_wyrm"):
            receipt = json.loads((HERE / "evidence" / asset / author.RECEIPT_NAME).read_text())
            self.assertEqual(receipt["original_brief"]["animations_field"], "ABSENT")
            self.assertEqual(receipt["phase_ready"], True)
            self.assertEqual(receipt["phase_presentation"], required)
            self.assertEqual(receipt["clip_authority"], "RATIFIED_W1_003_TWINBOND_PHASE_PRESENTATION_REPAIR")
            self.assertEqual(receipt["preservation_contract"], {"geometry": True, "uv": True, "texture_bytes": True, "locators": True, "balance": True, "new_attack_identity": False, "damage_effect_radius_change": False})
            self.assertEqual(receipt["brief_declared_clips"], ["idle", "action", *required])
            runtime = json.loads((HERE.parents[2] / "resource_pack" / "animations" / "aionbound" / f"{asset}.animation.json").read_text())
            self.assertEqual(runtime, json.loads((HERE / "evidence" / asset / "native-exports" / "pass-2.animation.json").read_text()))
            animations = runtime["animations"]
            self.assertEqual(sorted(name.rsplit(".", 1)[-1] for name in animations), ["action", "concord_pressure", "finale_ignition", "idle", "relic_trial", "split_approach"])
            signatures = {phase: json.dumps(animations[f"animation.aionbound.{asset}.{phase}"]["bones"], sort_keys=True) for phase in required}
            self.assertEqual(len(set(signatures.values())), 4)
        relic = json.loads((HERE / "evidence" / "twinbond_relic" / author.RECEIPT_NAME).read_text())
        self.assertEqual(relic["original_brief"]["animations_field"], ["dual_pulse"])
        self.assertEqual(relic["brief_declared_clips"], ["dual_pulse"])

    def test_report_is_deterministic(self):
        report = json.loads(build_report.OUTPUT.read_text())
        self.assertEqual(report, build_report.build())
        self.assertEqual(report["status"], "PASS_PHASE_READY_NATIVE_REPAIR")
        self.assertEqual(report["totals"], {"assets": 3, "clips": 13, "true_native_locators": 7, "screenshots": 37, "warnings": 0, "errors": 0})

    def test_static_phase_binding_is_presentation_only(self):
        root = HERE.parents[2]
        phases = ["split_approach", "concord_pressure", "relic_trial", "finale_ignition"]
        for asset in ("ash_sovereign_wyrm", "tide_empress_wyrm"):
            behavior = json.loads((root / "behavior_pack" / "entities" / f"{asset}.entity.json").read_text())
            description = behavior["minecraft:entity"]["description"]
            prop = description["properties"]["aionbound:twinbond_phase"]
            self.assertEqual(prop, {"type": "enum", "values": phases, "default": "split_approach", "client_sync": True})
            components = behavior["minecraft:entity"]["components"]
            self.assertEqual(components["minecraft:health"], {"max": 160, "value": 160})
            self.assertEqual(components["minecraft:attack"], {"damage": 8})
            client = json.loads((root / "resource_pack" / "entity" / f"{asset}.entity.json").read_text())["minecraft:client_entity"]["description"]
            self.assertEqual(set(client["animations"]), set(phases))
            self.assertEqual(len(client["scripts"]["animate"]), 4)
        source = (root / "behavior_pack" / "scripts" / "twinbond.js").read_text()
        self.assertIn('entity.setProperty?.("aionbound:twinbond_phase", phase)', source)
        for forbidden in ("applyDamage", "addEffect", "knockback", "new_attack"):
            self.assertNotIn(forbidden, source[source.index("function phaseTag"):source.index("function actionTag")])


if __name__ == "__main__":
    unittest.main()
