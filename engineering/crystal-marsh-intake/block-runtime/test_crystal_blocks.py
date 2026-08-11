#!/usr/bin/env python3
"""Targeted static tests for Packet 003 ordinary full-cube blocks."""

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
    "crystal_log", "marsh_wood", "flood_planks", "crystal_stone",
    "prism_brick", "wet_clay_block", "glass_root_block", "algae_block",
    "marsh_soil", "crystal_gravel",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_rgba_png(path: Path) -> tuple[int, int, int, int, bool]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"bad PNG signature: {path}")
    offset = 8
    idat = bytearray()
    width = height = depth = color = 0
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : offset + 12 + length])[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != expected_crc:
            raise AssertionError(f"bad PNG CRC: {path}")
        if kind == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", payload[:10])
        elif kind == b"IDAT":
            idat.extend(payload)
        offset += 12 + length
        if kind == b"IEND":
            break
    raw = zlib.decompress(bytes(idat))
    stride = width * 4
    prior = bytearray(stride)
    alpha = []
    cursor = 0
    for _ in range(height):
        filter_type = raw[cursor]
        cursor += 1
        encoded = raw[cursor : cursor + stride]
        cursor += stride
        decoded = bytearray(stride)
        for index, value in enumerate(encoded):
            left = decoded[index - 4] if index >= 4 else 0
            up = prior[index]
            upper_left = prior[index - 4] if index >= 4 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                estimate = left + up - upper_left
                choices = (left, up, upper_left)
                predictor = choices[
                    (abs(estimate - left), abs(estimate - up), abs(estimate - upper_left)).index(
                        min(abs(estimate - left), abs(estimate - up), abs(estimate - upper_left))
                    )
                ]
            else:
                raise AssertionError(f"unsupported PNG filter {filter_type}: {path}")
            decoded[index] = (value + predictor) & 0xFF
        alpha.extend(decoded[3::4])
        prior = decoded
    return width, height, depth, color, all(value == 255 for value in alpha)


class CrystalBlockRuntime(unittest.TestCase):
    def test_exact_packet_inventory_and_blockbench_na(self) -> None:
        authority = load(OUT / "CRYSTAL_BLOCK_RUNTIME_AUTHORITY.json")
        self.assertEqual(set(authority["asset_ids"]), IDS)
        self.assertEqual(authority["asset_count"], 10)
        self.assertEqual(
            authority["base_commit"],
            "466a061cbe22a01a4e561169df31e4f351edea71",
        )
        policy = authority["geometry_policy"]
        self.assertEqual(policy["shipping_geometry"], "minecraft:geometry.full_block")
        self.assertEqual(policy["blockbench_status"], "NOT_APPLICABLE")
        self.assertEqual(policy["packet_custom_geometry_status"], "NOT_PROMOTED")

    def test_behavior_and_registry_closure(self) -> None:
        terrain = load(ROOT / "resource_pack/textures/terrain_texture.json")["texture_data"]
        blocks = load(ROOT / "resource_pack/blocks.json")
        language = (ROOT / "resource_pack/texts/en_US.lang").read_text(encoding="utf-8")
        for asset_id in IDS:
            block = load(ROOT / f"behavior_pack/blocks/{asset_id}.block.json")["minecraft:block"]
            self.assertEqual(block["description"]["identifier"], f"aionbound:{asset_id}")
            components = block["components"]
            self.assertEqual(components["minecraft:geometry"], "minecraft:geometry.full_block")
            self.assertEqual(
                components["minecraft:material_instances"]["*"],
                {"texture": asset_id, "render_method": "opaque"},
            )
            self.assertEqual(components["minecraft:loot"], f"loot_tables/blocks/{asset_id}.json")
            self.assertTrue((ROOT / "behavior_pack" / components["minecraft:loot"]).is_file())
            self.assertEqual(
                terrain[asset_id]["textures"],
                f"textures/aionbound/crystal_marsh/blocks/{asset_id}",
            )
            self.assertEqual(blocks[f"aionbound:{asset_id}"]["textures"], asset_id)
            self.assertIn(f"tile.aionbound:{asset_id}.name=", language)

    def test_exact_packet_texture_and_png_closure(self) -> None:
        authority = load(OUT / "CRYSTAL_BLOCK_RUNTIME_AUTHORITY.json")
        for asset_id in IDS:
            source_hash = authority["source_inputs"][asset_id]["exported_texture"]["sha256"]
            self.assertEqual(
                authority["source_inputs"][asset_id]["editable_texture"]["sha256"],
                source_hash,
            )
            shipping = ROOT / f"resource_pack/textures/aionbound/crystal_marsh/blocks/{asset_id}.png"
            self.assertEqual(sha256(shipping), source_hash)
            self.assertEqual(decode_rgba_png(shipping), (32, 32, 8, 6, True))

    def test_no_custom_geometry_or_animation_promoted(self) -> None:
        for asset_id in IDS:
            self.assertFalse((ROOT / f"resource_pack/models/blocks/{asset_id}.geo.json").exists())
            self.assertFalse(
                (ROOT / f"resource_pack/animations/aionbound/crystal_marsh/blocks/{asset_id}.animation.json").exists()
            )

    def test_receipt_hashes_and_scope(self) -> None:
        report = load(OUT / "CRYSTAL_BLOCK_RUNTIME_REPORT.json")
        self.assertEqual(report["status"], "CRYSTAL_BLOCK_RUNTIME_STATIC_PASS")
        self.assertEqual(report["asset_count"], 10)
        for entry in report["assets"]:
            self.assertTrue(entry["texture_byte_equality"])
            for record in entry["files"].values():
                self.assertEqual(sha256(ROOT / record["path"]), record["sha256"])
        self.assertIn("STABLE_BDS", report["not_proven"])

    def test_authoring_is_idempotent(self) -> None:
        tracked = [
            ROOT / "resource_pack/textures/terrain_texture.json",
            ROOT / "resource_pack/blocks.json",
            ROOT / "resource_pack/texts/en_US.lang",
            OUT / "CRYSTAL_BLOCK_RUNTIME_AUTHORITY.json",
            OUT / "CRYSTAL_BLOCK_RUNTIME_REPORT.json",
        ]
        before = {path: sha256(path) for path in tracked}
        subprocess.run(
            ["python3", str(OUT / "author_crystal_blocks.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        after = {path: sha256(path) for path in tracked}
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
