#!/usr/bin/env python3

import hashlib
import json
import unittest
from pathlib import Path

from build_ashen_plants import PLANTS, REPRESENTATIVE, evidence_root


ROOT = Path(__file__).resolve().parents[3]


class AshenPlantRuntimeTests(unittest.TestCase):
    def test_exact_roster_and_native_sources(self):
        self.assertEqual(len(PLANTS), 10)
        self.assertEqual(REPRESENTATIVE, {"smoke_reed", "fire_bloom"})
        for asset in PLANTS:
            evidence = evidence_root(ROOT, asset)
            self.assertTrue((evidence / "native-exports/pass-2.geo.json").is_file(), asset)
            self.assertTrue((evidence / f"inputs/{asset}.source.png").is_file(), asset)

    def test_runtime_definitions_bind_exact_native_bytes(self):
        for asset, (_, faces, supports, _) in PLANTS.items():
            evidence = evidence_root(ROOT, asset)
            block = json.loads((ROOT / f"behavior_pack/blocks/{asset}.block.json").read_text())["minecraft:block"]
            self.assertEqual(block["description"]["identifier"], f"aionbound:{asset}")
            self.assertFalse(block["components"]["minecraft:collision_box"])
            condition = block["components"]["minecraft:placement_filter"]["conditions"][0]
            self.assertEqual(condition["allowed_faces"], faces)
            self.assertEqual(condition["block_filter"], supports)
            runtime_geo = json.loads((ROOT / f"resource_pack/models/aionbound/ashen/{asset}.geo.json").read_text())
            self.assertEqual(runtime_geo["minecraft:geometry"][0]["description"]["identifier"], f"geometry.aionbound.{asset}")
            source_png = evidence / f"inputs/{asset}.source.png"
            runtime_png = ROOT / f"resource_pack/textures/aionbound/ashen/plants/{asset}.png"
            self.assertEqual(hashlib.sha256(source_png.read_bytes()).digest(), hashlib.sha256(runtime_png.read_bytes()).digest())

    def test_shared_registry_closure(self):
        blocks = json.loads((ROOT / "resource_pack/blocks.json").read_text())
        terrain = json.loads((ROOT / "resource_pack/textures/terrain_texture.json").read_text())["texture_data"]
        lang = set((ROOT / "resource_pack/texts/en_US.lang").read_text().splitlines())
        for asset, (display, _, _, _) in PLANTS.items():
            self.assertEqual(blocks[f"aionbound:{asset}"]["textures"], asset)
            self.assertEqual(terrain[asset]["textures"], f"textures/aionbound/ashen/plants/{asset}")
            self.assertIn(f"tile.aionbound:{asset}.name={display}", lang)

    def test_no_runtime_animation_surrogate(self):
        for asset in PLANTS:
            self.assertFalse((ROOT / f"resource_pack/animation_controllers/{asset}.animation_controller.json").exists())
            block = (ROOT / f"behavior_pack/blocks/{asset}.block.json").read_text()
            self.assertNotIn("custom_component", block)


if __name__ == "__main__":
    unittest.main()
