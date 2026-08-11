#!/usr/bin/env python3
"""Targeted static tests for Packet 003 Crystal Marsh resource items."""

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
    "prism_pearl",
    "crystal_reed_item",
    "marsh_resin",
    "glass_algae",
    "silt_core",
    "flood_crystal",
    "moon_pearl",
    "wet_chitin",
    "mire_bloom_item",
    "crystal_root_item",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_header(path: Path) -> tuple[int, int, int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"bad PNG signature: {path}")
    length = struct.unpack(">I", data[8:12])[0]
    if data[12:16] != b"IHDR" or length != 13:
        raise AssertionError(f"bad PNG IHDR: {path}")
    width, height, depth, color = struct.unpack(">IIBB", data[16:26])
    offset = 8
    compressed = bytearray()
    while offset < len(data):
        size = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + size]
        crc = struct.unpack(">I", data[offset + 8 + size : offset + 12 + size])[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise AssertionError(f"bad PNG CRC: {path}")
        if kind == b"IDAT":
            compressed.extend(payload)
        offset += 12 + size
        if kind == b"IEND":
            break
    zlib.decompress(bytes(compressed))
    return width, height, depth, color


class CrystalResourceRuntime(unittest.TestCase):
    def test_exact_packet_inventory_and_narrow_authority(self) -> None:
        authority = load(OUT / "CRYSTAL_RESOURCE_RUNTIME_AUTHORITY.json")
        self.assertEqual(set(authority["asset_ids"]), IDS)
        self.assertEqual(authority["asset_count"], 10)
        self.assertEqual(
            authority["base_commit"],
            "466a061cbe22a01a4e561169df31e4f351edea71",
        )
        policy = authority["presentation_policy"]
        self.assertEqual(policy["blockbench_status"], "NOT_APPLICABLE")
        self.assertEqual(policy["packet_custom_geometry_status"], "NOT_PROMOTED")

    def test_item_atlas_language_and_exact_icon_closure(self) -> None:
        report = load(OUT / "CRYSTAL_RESOURCE_RUNTIME_REPORT.json")
        authority = load(OUT / "CRYSTAL_RESOURCE_RUNTIME_AUTHORITY.json")
        atlas = load(ROOT / "resource_pack/textures/item_texture.json")["texture_data"]
        language = (ROOT / "resource_pack/texts/en_US.lang").read_text(encoding="utf-8")
        self.assertEqual({entry["warehouse_id"] for entry in report["resources"]}, IDS)
        for entry in report["resources"]:
            asset_id = entry["warehouse_id"]
            item_path = ROOT / entry["item_path"]
            item = load(item_path)["minecraft:item"]
            self.assertEqual(item["description"]["identifier"], f"aionbound:{asset_id}")
            self.assertEqual(set(item["components"]), {"minecraft:display_name", "minecraft:icon"})
            self.assertEqual(
                item["components"]["minecraft:icon"]["textures"]["default"], asset_id
            )
            self.assertEqual(atlas[asset_id]["textures"], entry["texture_path"])
            self.assertIn(f"item.aionbound:{asset_id}=", language)
            icon = ROOT / entry["icon_path"]
            self.assertEqual(sha256(icon), entry["source_icon_sha256"])
            self.assertEqual(
                authority["source_inputs"][asset_id]["editable_texture"]["sha256"],
                authority["source_inputs"][asset_id]["exported_texture"]["sha256"],
            )
            self.assertTrue(entry["icon_byte_equality"])
            self.assertEqual(png_header(icon), (32, 32, 8, 6))

    def test_no_packet_geometry_or_animation_promoted(self) -> None:
        for asset_id in IDS:
            self.assertFalse(
                (ROOT / f"resource_pack/models/aionbound/crystal_marsh/items/{asset_id}.geo.json").exists()
            )
            self.assertFalse(
                (ROOT / f"resource_pack/animations/aionbound/crystal_marsh/items/{asset_id}.animation.json").exists()
            )

    def test_receipt_hashes_and_scope(self) -> None:
        report = load(OUT / "CRYSTAL_RESOURCE_RUNTIME_REPORT.json")
        self.assertEqual(report["status"], "CRYSTAL_RESOURCE_RUNTIME_STATIC_PASS")
        self.assertEqual(report["scope"], "ten Packet 003 warehouse resource items only")
        for entry in report["resources"]:
            self.assertEqual(sha256(ROOT / entry["item_path"]), entry["item_sha256"])
            self.assertEqual(sha256(ROOT / entry["icon_path"]), entry["icon_sha256"])
        self.assertIn("STABLE_BDS", report["not_proven"])

    def test_authoring_is_idempotent(self) -> None:
        tracked = [
            ROOT / "resource_pack/textures/item_texture.json",
            ROOT / "resource_pack/texts/en_US.lang",
            OUT / "CRYSTAL_RESOURCE_RUNTIME_AUTHORITY.json",
            OUT / "CRYSTAL_RESOURCE_RUNTIME_REPORT.json",
        ]
        before = {path: sha256(path) for path in tracked}
        subprocess.run(
            ["python3", str(OUT / "author_crystal_resources.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        after = {path: sha256(path) for path in tracked}
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
