#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("author_entity_animations.py")
SPEC = importlib.util.spec_from_file_location("author_entity_animations", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class EntityAnimationContractTests(unittest.TestCase):
    def test_exact_asset_scope(self) -> None:
        self.assertEqual(set(module.ENTITY_SPECS), {"lantern_hare", "mosskip_fawn", "mosskip_doe", "mosskip_buck", "rootback_boar"})

    def test_exact_brief_clip_scope(self) -> None:
        self.assertEqual({asset:list(spec["clips"]) for asset,spec in module.ENTITY_SPECS.items()}, {
            "lantern_hare":["idle_ear_flick","hop","alert","hurt","death"],
            "mosskip_fawn":["idle","hop","skitter","hurt","death"],
            "mosskip_doe":["idle_graze","walk","hop_bound","look","hurt","death"],
            "mosskip_buck":["idle_graze","walk","hop_bound","look","hurt","death"],
            "rootback_boar":["idle","walk_trundle","charge_snort","hurt","death"],
        })

    def test_every_spec_is_finite_and_role_readable(self) -> None:
        for asset,spec in module.ENTITY_SPECS.items():
            with self.subTest(asset=asset): module.validate_spec(asset,spec)

    def test_full_names_preserve_packet_namespace(self) -> None:
        self.assertEqual(module.full_clip_name("geometry.aionforge_ww.rootback_boar","charge_snort"),"animation.aionforge_ww.rootback_boar.charge_snort")

    def test_console_conservative_clip_budgets(self) -> None:
        for asset,spec in module.ENTITY_SPECS.items():
            self.assertLessEqual(len(spec["clips"]),6,asset)
            for name,record in spec["clips"].items():
                self.assertLessEqual(record["duration"],4.2,f"{asset}:{name}")
                self.assertLessEqual(len(record["bones"]),5,f"{asset}:{name}")

    def test_native_keyframe_tolerance_is_below_one_twentieth_second(self) -> None:
        self.assertGreater(module.KEYFRAME_TIME_TOLERANCE_SECONDS, 0)
        self.assertLess(module.KEYFRAME_TIME_TOLERANCE_SECONDS, 0.05)


if __name__ == "__main__": unittest.main()
