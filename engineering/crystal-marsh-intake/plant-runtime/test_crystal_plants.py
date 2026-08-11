#!/usr/bin/env python3

import hashlib
import json
import unittest
from pathlib import Path

from author_crystal_plants import PLANTS, REPRESENTATIVE, build, evidence_root


REPO = Path(__file__).resolve().parents[3]


class CrystalPlantRuntimeTests(unittest.TestCase):
    def test_exact_roster_and_native_pass(self):
        self.assertEqual(len(PLANTS), 10)
        self.assertEqual(REPRESENTATIVE, {"bubble_pod", "flood_reed"})
        for asset in PLANTS:
            evidence = evidence_root(REPO, asset)
            self.assertTrue((evidence / "native-exports/pass-2.geo.json").is_file(), asset)
            self.assertTrue((evidence / f"inputs/{asset}.source.png").is_file(), asset)

    def test_runtime_definitions_bind_native_geometry_and_texture(self):
        for asset, spec in PLANTS.items():
            evidence = evidence_root(REPO, asset)
            block = json.loads((REPO / f"behavior_pack/blocks/{asset}.block.json").read_text())["minecraft:block"]
            components = block["components"]
            self.assertEqual(block["description"]["identifier"], f"aionbound:{asset}")
            self.assertFalse(components["minecraft:collision_box"])
            self.assertEqual(components["minecraft:selection_box"]["origin"], list(spec.selection[:3]))
            self.assertEqual(components["minecraft:selection_box"]["size"], list(spec.selection[3:]))
            self.assertEqual(components["minecraft:placement_filter"]["conditions"][0]["allowed_faces"], list(spec.faces))
            self.assertEqual(components["minecraft:placement_filter"]["conditions"][0]["block_filter"], list(spec.supports))
            self.assertEqual(components["minecraft:loot"], f"loot_tables/blocks/{asset}.json")
            geometry = json.loads((REPO / f"resource_pack/models/aionbound/crystal_marsh/{asset}.geo.json").read_text())
            self.assertEqual(geometry["minecraft:geometry"][0]["description"]["identifier"], f"geometry.aionbound.{asset}")
            source_png = evidence / f"inputs/{asset}.source.png"
            runtime_png = REPO / f"resource_pack/textures/aionbound/crystal_marsh/plants/{asset}.png"
            self.assertEqual(hashlib.sha256(source_png.read_bytes()).digest(), hashlib.sha256(runtime_png.read_bytes()).digest())

    def test_waterlogging_is_explicit_and_bounded(self):
        expected = {"bubble_pod", "crystal_lily", "crystal_vine", "flood_reed", "glow_kelp"}
        for asset, spec in PLANTS.items():
            components = json.loads((REPO / f"behavior_pack/blocks/{asset}.block.json").read_text())["minecraft:block"]["components"]
            self.assertEqual("minecraft:liquid_detection" in components, asset in expected)
            if asset in expected:
                rule = components["minecraft:liquid_detection"]["detection_rules"][0]
                self.assertEqual(rule["liquid_type"], "water")
                self.assertTrue(rule["can_contain_liquid"])
                self.assertEqual(rule["on_liquid_touches"], "blocking")

    def test_registry_and_language_closure(self):
        blocks = json.loads((REPO / "resource_pack/blocks.json").read_text())
        terrain = json.loads((REPO / "resource_pack/textures/terrain_texture.json").read_text())["texture_data"]
        lang = set((REPO / "resource_pack/texts/en_US.lang").read_text().splitlines())
        for asset, spec in PLANTS.items():
            self.assertEqual(blocks[f"aionbound:{asset}"]["textures"], asset)
            self.assertEqual(terrain[asset]["textures"], f"textures/aionbound/crystal_marsh/plants/{asset}")
            self.assertIn(f"tile.aionbound:{asset}.name={spec.display}", lang)

    def test_no_animation_surrogate_or_new_script_surface(self):
        for asset in PLANTS:
            block_text = (REPO / f"behavior_pack/blocks/{asset}.block.json").read_text()
            self.assertNotIn("custom_component", block_text)
            self.assertFalse((REPO / f"resource_pack/animation_controllers/{asset}.animation_controller.json").exists())

    def test_authoring_is_deterministic(self):
        files, report = build(REPO)
        self.assertEqual(report["status"], "PASS_SOURCE_STATIC_PLANT_BINDING")
        for path, expected in files.items():
            self.assertTrue(path.is_file(), path)
            if path == REPO / "resource_pack/texts/en_US.lang":
                # Shared language rows are append-only and may be composed by
                # later Crystal equipment lanes in a different stable order.
                # Exact plant-row closure is asserted separately above.
                continue
            self.assertEqual(path.read_bytes(), expected, path)


if __name__ == "__main__":
    unittest.main()
