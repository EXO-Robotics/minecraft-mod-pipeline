#!/usr/bin/env python3
"""Static closure checks for the ten Packet 001 Whisperwood blocks."""

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

IDS = {
    "forest_brick",
    "hollow_wood",
    "moss_bark",
    "stripped_whisperwood_log",
    "whisperwood_leaves",
    "whisperwood_log",
    "whisperwood_planks",
    "whisperwood_roots",
    "whisperwood_sapling",
    "whisperwood_wood",
}


def load(path: Path) -> dict:
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


class WhisperwoodBlockRuntime(unittest.TestCase):
    def test_native_receipts_and_shipping_geometry(self) -> None:
        self.assertEqual({p.name for p in EVIDENCE.iterdir() if p.is_dir()}, IDS)
        for asset_id in sorted(IDS):
            with self.subTest(asset_id=asset_id):
                receipt = load(EVIDENCE / asset_id / "whisperwood-native-blockbench-receipt.json")
                self.assertEqual(receipt["status"], "PASS")
                self.assertTrue(receipt["exports"]["geometry"]["canonical_equivalent"])
                source = load(EVIDENCE / asset_id / "native-exports/pass-2.geo.json")
                expected = copy.deepcopy(source)
                expected["minecraft:geometry"][0]["description"]["identifier"] = (
                    f"geometry.aionbound.{asset_id}"
                )
                shipping = load(RP / f"models/blocks/{asset_id}.geo.json")
                self.assertEqual(shipping, expected)

    def test_behavior_geometry_material_and_registry_closure(self) -> None:
        blocks_registry = load(RP / "blocks.json")
        terrain = load(RP / "textures/terrain_texture.json")["texture_data"]
        language = (RP / "texts/en_US.lang").read_text(encoding="utf-8")
        for asset_id in sorted(IDS):
            with self.subTest(asset_id=asset_id):
                block = load(BP / f"blocks/{asset_id}.block.json")["minecraft:block"]
                self.assertEqual(block["description"]["identifier"], f"aionbound:{asset_id}")
                components = block["components"]
                self.assertEqual(components["minecraft:geometry"], f"geometry.aionbound.{asset_id}")
                material = components["minecraft:material_instances"]["*"]
                self.assertEqual(material["render_method"], "opaque")
                texture_key = material["texture"]
                self.assertIn(texture_key, terrain)
                self.assertEqual(blocks_registry[f"aionbound:{asset_id}"]["textures"], texture_key)
                texture = RP / f"{terrain[texture_key]['textures']}.png"
                self.assertTrue(texture.is_file(), texture)
                self.assertIn(f"tile.aionbound:{asset_id}.name=", language)

    def test_textures_match_native_input_hashes_and_fully_decode(self) -> None:
        for asset_id in sorted(IDS):
            with self.subTest(asset_id=asset_id):
                receipt = load(EVIDENCE / asset_id / "whisperwood-native-blockbench-receipt.json")
                texture = RP / f"textures/aionbound/whisperwood/blocks/{asset_id}.png"
                self.assertEqual(sha256(texture), receipt["inputs"]["texture"]["sha256"])
                self.assertEqual(decode_png(texture), (32, 32))

    def test_shipping_lane_has_no_old_namespace_or_animation_promotion(self) -> None:
        for path in sorted((RP / "models/blocks").glob("*.geo.json")):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("aionforge_ww", text, path.name)
            self.assertNotIn("geometry.geometry", text, path.name)
        self.assertFalse((RP / "animations/aionbound/whisperwood/blocks").exists())


if __name__ == "__main__":
    unittest.main()
