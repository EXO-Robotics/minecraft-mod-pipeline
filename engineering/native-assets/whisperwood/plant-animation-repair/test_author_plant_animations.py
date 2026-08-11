#!/usr/bin/env python3
"""Unit tests for the narrow Whisperwood plant animation authoring contract."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("author_plant_animations.py")
SPEC = importlib.util.spec_from_file_location("author_plant_animations", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class PlantAnimationContractTests(unittest.TestCase):
    def test_only_four_authorized_assets_exist(self) -> None:
        self.assertEqual(
            set(module.PLANT_SPECS),
            {"lantern_bloom", "pale_reed", "star_grass", "whisper_fern"},
        )

    def test_exact_approved_clip_leaves(self) -> None:
        self.assertEqual(
            {asset: spec["clip"] for asset, spec in module.PLANT_SPECS.items()},
            {
                "lantern_bloom": "glow_idle",
                "pale_reed": "sway",
                "star_grass": "wind_sway",
                "whisper_fern": "gentle_sway",
            },
        )

    def test_every_spec_is_finite_looping_and_nonzero(self) -> None:
        for asset, spec in module.PLANT_SPECS.items():
            with self.subTest(asset=asset):
                module.validate_spec(asset, spec)

    def test_full_clip_name_uses_model_namespace(self) -> None:
        self.assertEqual(
            module.full_clip_name("geometry.aionforge_ww.star_grass", "wind_sway"),
            "animation.aionforge_ww.star_grass.wind_sway",
        )


if __name__ == "__main__":
    unittest.main()
