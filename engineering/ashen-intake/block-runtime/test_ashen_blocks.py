#!/usr/bin/env python3
"""Targeted static tests for Packet 002 Ashen full-cube blocks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
IDS = {
    "ash_log",
    "char_planks",
    "basalt_brick",
    "smolder_stone",
    "ash_soil",
    "ember_moss",
    "volcanic_glass_block",
    "heat_bark",
    "basalt_pillar",
    "cinder_gravel",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_rgba_png(path: Path) -> tuple[int, int, int, int, bool]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{path}: invalid PNG signature")
    offset = 8
    width = height = color_type = bit_depth = 0
    compressed = bytearray()
    saw_iend = False
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        crc = struct.unpack(">I", data[offset + 8 + length : offset + 12 + length])[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise AssertionError(f"{path}: CRC mismatch in {kind!r}")
        if kind == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", payload[:10])
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            saw_iend = True
        offset += 12 + length
    if not saw_iend or offset != len(data):
        raise AssertionError(f"{path}: incomplete PNG chunk stream")
    inflated = zlib.decompress(bytes(compressed))
    self_check = (width, height, bit_depth, color_type)
    if self_check != (32, 32, 8, 6):
        return (*self_check, False)
    bytes_per_pixel = 4
    row_bytes = width * bytes_per_pixel
    prior = bytearray(row_bytes)
    alpha_values = []
    cursor = 0
    for _row in range(height):
        filter_type = inflated[cursor]
        cursor += 1
        encoded = inflated[cursor : cursor + row_bytes]
        cursor += row_bytes
        if filter_type > 4:
            raise AssertionError(f"{path}: illegal PNG filter {filter_type}")
        decoded = bytearray(row_bytes)
        for index, value in enumerate(encoded):
            left = decoded[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            up = prior[index]
            upper_left = prior[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            else:
                estimate = left + up - upper_left
                distances = (
                    abs(estimate - left),
                    abs(estimate - up),
                    abs(estimate - upper_left),
                )
                predictor = (left, up, upper_left)[distances.index(min(distances))]
            decoded[index] = (value + predictor) & 0xFF
        alpha_values.extend(decoded[3::4])
        prior = decoded
    return (*self_check, all(alpha == 255 for alpha in alpha_values))


class AshenBlockRuntime(unittest.TestCase):
    def test_authority_is_exact_and_blockbench_is_honestly_na(self) -> None:
        authority = load(OUT / "ASHEN_BLOCK_RUNTIME_AUTHORITY.json")
        self.assertEqual(set(authority["asset_ids"]), IDS)
        self.assertEqual(authority["asset_count"], 10)
        self.assertEqual(
            authority["base_commit"],
            "e9eeb3dd9bfbd8b50fdd29babd09247552bfbe7b",
        )
        policy = authority["geometry_policy"]
        self.assertEqual(policy["shipping_geometry"], "minecraft:geometry.full_block")
        self.assertEqual(policy["blockbench_status"], "NOT_APPLICABLE")
        self.assertEqual(policy["packet_custom_geometry_status"], "NOT_PROMOTED")

    def test_behavior_and_registry_closure(self) -> None:
        terrain = load(ROOT / "resource_pack/textures/terrain_texture.json")["texture_data"]
        blocks = load(ROOT / "resource_pack/blocks.json")
        language = (ROOT / "resource_pack/texts/en_US.lang").read_text(encoding="utf-8")
        for asset_id in sorted(IDS):
            with self.subTest(asset_id=asset_id):
                block = load(ROOT / f"behavior_pack/blocks/{asset_id}.block.json")
                block = block["minecraft:block"]
                self.assertEqual(block["description"]["identifier"], f"aionbound:{asset_id}")
                components = block["components"]
                self.assertEqual(components["minecraft:geometry"], "minecraft:geometry.full_block")
                material = components["minecraft:material_instances"]["*"]
                self.assertEqual(material, {"texture": asset_id, "render_method": "opaque"})
                self.assertEqual(
                    terrain[asset_id]["textures"],
                    f"textures/aionbound/ashen/blocks/{asset_id}",
                )
                self.assertEqual(blocks[f"aionbound:{asset_id}"]["textures"], asset_id)
                self.assertIn(f"tile.aionbound:{asset_id}.name=", language)

    def test_shipping_textures_match_packet_and_fully_decode(self) -> None:
        authority = load(OUT / "ASHEN_BLOCK_RUNTIME_AUTHORITY.json")
        for asset_id in sorted(IDS):
            with self.subTest(asset_id=asset_id):
                source_hash = authority["source_inputs"][asset_id]["texture"]["sha256"]
                shipping = ROOT / f"resource_pack/textures/aionbound/ashen/blocks/{asset_id}.png"
                self.assertEqual(sha256(shipping), source_hash)
                self.assertEqual(decode_rgba_png(shipping), (32, 32, 8, 6, True))

    def test_no_custom_geometry_or_animation_was_promoted(self) -> None:
        for asset_id in IDS:
            self.assertFalse((ROOT / f"resource_pack/models/blocks/{asset_id}.geo.json").exists())
            self.assertFalse(
                (ROOT / f"resource_pack/animations/aionbound/ashen/blocks/{asset_id}.animation.json").exists()
            )

    def test_receipt_hashes_and_texture_equality(self) -> None:
        report = load(OUT / "ASHEN_BLOCK_RUNTIME_REPORT.json")
        self.assertEqual(report["status"], "ASHEN_BLOCK_RUNTIME_STATIC_PASS")
        self.assertEqual(report["asset_count"], 10)
        for asset in report["assets"]:
            self.assertTrue(asset["texture_byte_equality"])
            for record in asset["files"].values():
                path = ROOT / record["path"]
                self.assertEqual(sha256(path), record["sha256"])

    def test_authoring_primitives_match_current_composed_blocks(self) -> None:
        import author_ashen_blocks as author
        for asset, spec in author.ASSETS.items():
            expected = author.block_definition(asset, spec)
            current = load(ROOT / f"behavior_pack/blocks/{asset}.block.json")
            # Later economy integration adds loot to the historical block
            # primitive. All other author-controlled fields remain exact.
            current["minecraft:block"]["components"].pop("minecraft:loot", None)
            self.assertEqual(expected, current, asset)


if __name__ == "__main__":
    unittest.main()
