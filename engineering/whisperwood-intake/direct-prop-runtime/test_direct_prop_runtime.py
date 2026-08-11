#!/usr/bin/env python3
"""Static closure tests for the two native-PASS Packet 001 direct props."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import struct
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[3]
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
EVIDENCE = ROOT / "engineering/native-assets/whisperwood/evidence"

SPECS = {
    "lantern_post": {
        "sound": "wood",
        "collision": {"origin": [-2, 0, -2], "size": [4, 16, 4]},
        "selection": {"origin": [-4, 0, -4], "size": [8, 16, 8]},
        "mining": 1.5,
        "light": 10,
        "locator": [0, 16, -7],
        "native_clips": {
            "animation.aionforge_ww.lantern_post.idle_sway",
            "animation.aionforge_ww.lantern_post.glow",
        },
    },
    "moss_cairn": {
        "sound": "stone",
        "collision": {"origin": [-6, 0, -6], "size": [12, 12, 12]},
        "selection": {"origin": [-7, 0, -7], "size": [14, 14, 14]},
        "mining": 1.8,
        "light": 4,
        "locator": [0, 10, 0],
        "native_clips": set(),
    },
}

GROUND_FILTER = {
    "minecraft:grass_block",
    "minecraft:dirt",
    "minecraft:coarse_dirt",
    "minecraft:podzol",
    "minecraft:moss_block",
    "minecraft:stone",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_png(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{path}: invalid PNG signature")
    offset = 8
    width = height = 0
    compressed = bytearray()
    saw_iend = False
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        expected = struct.unpack(">I", data[offset + 8 + length : offset + 12 + length])[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != expected:
            raise AssertionError(f"{path}: CRC mismatch in {kind!r}")
        if kind == b"IHDR":
            width, height = struct.unpack(">II", payload[:8])
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            saw_iend = True
        offset += 12 + length
    if not saw_iend or offset != len(data):
        raise AssertionError(f"{path}: incomplete PNG chunk stream")
    zlib.decompress(bytes(compressed))
    return width, height


class DirectPropRuntimeTest(unittest.TestCase):
    def test_exact_native_evidence_and_shipping_geometry(self):
        for asset, spec in SPECS.items():
            with self.subTest(asset=asset):
                root = EVIDENCE / asset
                receipt = load(root / "direct-prop-native-receipt.json")
                self.assertEqual(receipt["status"], "PASS")
                self.assertEqual(receipt["native_result"]["blockbench_version"], "5.1.6")
                self.assertEqual(receipt["native_result"]["warning_count"], 0)
                self.assertEqual(receipt["native_result"]["error_count"], 0)
                self.assertTrue(receipt["exports"]["geometry"]["canonical_equivalent"])
                self.assertEqual(set(receipt["native_result"]["final_animation_names"]), spec["native_clips"])

                native_geometry = load(root / "native-exports/pass-2.geo.json")
                expected = copy.deepcopy(native_geometry)
                expected["minecraft:geometry"][0]["description"]["identifier"] = f"geometry.aionbound.{asset}"
                shipping = load(RP / f"models/blocks/{asset}.geo.json")
                self.assertEqual(shipping, expected)
                chassis = next(bone for bone in shipping["minecraft:geometry"][0]["bones"] if bone["name"] == "chassis")
                self.assertEqual(chassis["locators"]["effect"], spec["locator"])

    def test_texture_bytes_and_png_decode(self):
        for asset in SPECS:
            with self.subTest(asset=asset):
                receipt = load(EVIDENCE / asset / "direct-prop-native-receipt.json")
                shipping = RP / f"textures/aionbound/whisperwood/blocks/{asset}.png"
                self.assertEqual(sha256(shipping), receipt["evidence_inputs"]["texture"]["sha256"])
                self.assertEqual(sha256(shipping), receipt["staged_texture"]["sha256"])
                self.assertEqual(decode_png(shipping), (32, 32))

    def test_behavior_roles_and_stable_static_components(self):
        for asset, spec in SPECS.items():
            with self.subTest(asset=asset):
                document = load(BP / f"blocks/{asset}.block.json")
                self.assertEqual(document["format_version"], "1.21.80")
                block = document["minecraft:block"]
                self.assertEqual(block["description"]["identifier"], f"aionbound:{asset}")
                components = block["components"]
                self.assertEqual(components["minecraft:geometry"], f"geometry.aionbound.{asset}")
                self.assertEqual(components["minecraft:collision_box"], spec["collision"])
                self.assertEqual(components["minecraft:selection_box"], spec["selection"])
                self.assertEqual(components["minecraft:destructible_by_mining"]["seconds_to_destroy"], spec["mining"])
                self.assertEqual(components["minecraft:light_emission"], spec["light"])
                material = components["minecraft:material_instances"]["*"]
                self.assertEqual(material, {"texture": asset, "render_method": "opaque"})
                condition = components["minecraft:placement_filter"]["conditions"]
                self.assertEqual(len(condition), 1)
                self.assertEqual(condition[0]["allowed_faces"], ["up"])
                self.assertEqual(set(condition[0]["block_filter"]), GROUND_FILTER)

    def test_registry_texture_and_language_closure(self):
        blocks = load(RP / "blocks.json")
        terrain = load(RP / "textures/terrain_texture.json")["texture_data"]
        language = (RP / "texts/en_US.lang").read_text(encoding="utf-8").splitlines()
        for asset, spec in SPECS.items():
            with self.subTest(asset=asset):
                self.assertEqual(blocks[f"aionbound:{asset}"], {"sound": spec["sound"], "textures": asset})
                expected_path = f"textures/aionbound/whisperwood/blocks/{asset}"
                self.assertEqual(terrain[asset], {"textures": expected_path})
                self.assertTrue((RP / f"{expected_path}.png").is_file())
                display = asset.replace("_", " ").title()
                self.assertEqual(language.count(f"tile.aionbound:{asset}.name={display}"), 1)

    def test_animation_loot_and_assembly_are_withheld(self):
        shipping_animation_dirs = [
            RP / "animations/aionbound/whisperwood/blocks",
            RP / "animation_controllers/aionbound/whisperwood/blocks",
        ]
        self.assertTrue(all(not path.exists() for path in shipping_animation_dirs))
        for asset in SPECS:
            text = (BP / f"blocks/{asset}.block.json").read_text(encoding="utf-8")
            self.assertNotIn("loot", text.lower())
            self.assertNotIn("reward", text.lower())
            self.assertNotIn("animation", text.lower())
        runtime_dir = Path(__file__).resolve().parent
        self.assertFalse(any(path.suffix == ".mcstructure" for path in runtime_dir.rglob("*")))

    def test_shipping_namespace_and_reference_scope(self):
        for asset in SPECS:
            geometry_text = (RP / f"models/blocks/{asset}.geo.json").read_text(encoding="utf-8")
            self.assertNotIn("aionforge_ww", geometry_text)
            self.assertNotIn("geometry.geometry", geometry_text)
            block_text = (BP / f"blocks/{asset}.block.json").read_text(encoding="utf-8")
            self.assertNotIn("aionforge", block_text)
            block = load(BP / f"blocks/{asset}.block.json")["minecraft:block"]
            self.assertNotIn("events", block)
            self.assertNotIn("minecraft:custom_components", block["components"])


if __name__ == "__main__":
    unittest.main()
