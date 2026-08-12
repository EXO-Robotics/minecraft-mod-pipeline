#!/usr/bin/env python3
"""Targeted tests for Packet 004 flat resources and full-cube blocks."""

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
RESOURCE_IDS = {"sky_feather", "wind_silk", "cloud_wool", "cliff_crystal", "storm_pinion", "aether_stone", "updraft_reed_item", "sky_vine_item", "float_resin", "lift_bloom_item"}
BLOCK_IDS = {"skyreach_log", "skyreach_wood", "skyreach_planks", "wind_slate", "cliff_stone", "rope_timber", "cloud_wool_block", "pale_shelf_stone", "cliff_gravel", "sky_moss_block"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_png(path: Path) -> tuple[int, int, int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"bad PNG signature: {path}")
    offset, idat = 8, bytearray()
    width = height = depth = color = 0
    found_end = False
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        crc = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise AssertionError(f"bad PNG CRC: {path}")
        if kind == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", payload[:10])
        elif kind == b"IDAT": idat.extend(payload)
        elif kind == b"IEND": found_end = True; break
        offset += 12 + length
    if not found_end: raise AssertionError(f"missing PNG IEND: {path}")
    zlib.decompress(bytes(idat))
    return width, height, depth, color


class SkyreachStaticFoundations(unittest.TestCase):
    def test_authority_inventory_namespace_and_boundaries(self) -> None:
        authority = load(OUT / "SKYREACH_STATIC_FOUNDATIONS_AUTHORITY.json")
        self.assertEqual(authority["base"], {"commit": "dde6dbe1a331ee2d1673624daaad0c56fc1f9950", "tree": "5111a8f664cd072bafe5654cfc31753235e8d567"})
        self.assertEqual(set(authority["resource_ids"]), RESOURCE_IDS)
        self.assertEqual(set(authority["block_ids"]), BLOCK_IDS)
        self.assertEqual(authority["normalization"], {"warehouse_namespace": "aionforge_sr", "runtime_namespace": "aionbound", "identifier_policy": "PRESERVE_PACKET_ASSET_ID_NORMALIZE_NAMESPACE_ONLY"})
        self.assertEqual(authority["presentation_policy"]["resources"]["blockbench_status"], "NOT_APPLICABLE")
        self.assertEqual(authority["presentation_policy"]["blocks"]["blockbench_status"], "NOT_APPLICABLE")
        self.assertIn("loot", authority["scope_exclusions"])
        for asset_id, inputs in authority["source_inputs"].items():
            geometry = load(ROOT.parents[3] / inputs["exported_geometry"]["path"])
            geometry_id = geometry["minecraft:geometry"][0]["description"]["identifier"]
            animation = load(ROOT.parents[3] / inputs["exported_animation"]["path"])
            self.assertEqual(geometry_id, f"geometry.aionforge_sr.{asset_id}")
            self.assertTrue(all(key.startswith(f"animation.aionforge_sr.{asset_id}.") for key in animation["animations"]))

    def test_resource_closure(self) -> None:
        report = load(OUT / "SKYREACH_STATIC_FOUNDATIONS_REPORT.json")
        atlas = load(ROOT / "resource_pack/textures/item_texture.json")["texture_data"]
        language = (ROOT / "resource_pack/texts/en_US.lang").read_text(encoding="utf-8")
        self.assertEqual({entry["id"] for entry in report["resources"]}, RESOURCE_IDS)
        for entry in report["resources"]:
            asset_id = entry["id"]
            item = load(ROOT / entry["definition"]["path"])["minecraft:item"]
            self.assertEqual(item["description"]["identifier"], f"aionbound:{asset_id}")
            self.assertEqual(set(item["components"]), {"minecraft:display_name", "minecraft:icon"})
            self.assertEqual(item["components"]["minecraft:icon"]["textures"]["default"], asset_id)
            self.assertEqual(atlas[asset_id]["textures"], f"textures/aionbound/skyreach/items/{asset_id}")
            self.assertIn(f"item.aionbound:{asset_id}=", language)
            texture = ROOT / entry["texture"]["path"]
            self.assertEqual(sha256(texture), entry["source_texture_sha256"])
            self.assertEqual(decode_png(texture), (32, 32, 8, 6))

    def test_block_closure_and_no_early_loot(self) -> None:
        report = load(OUT / "SKYREACH_STATIC_FOUNDATIONS_REPORT.json")
        terrain = load(ROOT / "resource_pack/textures/terrain_texture.json")["texture_data"]
        rp_blocks = load(ROOT / "resource_pack/blocks.json")
        language = (ROOT / "resource_pack/texts/en_US.lang").read_text(encoding="utf-8")
        self.assertEqual({entry["id"] for entry in report["blocks"]}, BLOCK_IDS)
        for entry in report["blocks"]:
            asset_id = entry["id"]
            block = load(ROOT / entry["definition"]["path"])["minecraft:block"]
            self.assertEqual(block["description"]["identifier"], f"aionbound:{asset_id}")
            components = block["components"]
            self.assertEqual(components["minecraft:geometry"], "minecraft:geometry.full_block")
            self.assertEqual(components["minecraft:material_instances"]["*"], {"texture": asset_id, "render_method": "opaque"})
            self.assertNotIn("minecraft:loot", components)
            self.assertEqual(terrain[asset_id]["textures"], f"textures/aionbound/skyreach/blocks/{asset_id}")
            self.assertEqual(rp_blocks[f"aionbound:{asset_id}"]["textures"], asset_id)
            self.assertIn(f"tile.aionbound:{asset_id}.name=", language)
            texture = ROOT / entry["texture"]["path"]
            self.assertEqual(sha256(texture), entry["source_texture_sha256"])
            self.assertEqual(decode_png(texture), (32, 32, 8, 6))

    def test_receipt_hashes_and_scope(self) -> None:
        report = load(OUT / "SKYREACH_STATIC_FOUNDATIONS_REPORT.json")
        self.assertEqual(report["status"], "SKYREACH_STATIC_FOUNDATIONS_STATIC_PASS")
        for entry in report["resources"] + report["blocks"]:
            self.assertTrue(entry["texture_byte_equality"])
            for key in ("definition", "texture"):
                self.assertEqual(sha256(ROOT / entry[key]["path"]), entry[key]["sha256"])
        self.assertIn("STABLE_BDS", report["not_proven"])
        self.assertIn("resource_pack/texts/en_US.lang", report["shared_merge_hotspots"])

    def test_no_packet_custom_geometry_or_animation_promoted(self) -> None:
        for asset_id in RESOURCE_IDS | BLOCK_IDS:
            matches = list((ROOT / "resource_pack").rglob(f"{asset_id}.geo.json"))
            matches += list((ROOT / "resource_pack").rglob(f"{asset_id}.animation.json"))
            self.assertEqual(matches, [])

    def test_authoring_is_idempotent(self) -> None:
        tracked = [ROOT / "resource_pack/textures/item_texture.json", ROOT / "resource_pack/textures/terrain_texture.json", ROOT / "resource_pack/blocks.json", ROOT / "resource_pack/texts/en_US.lang", OUT / "SKYREACH_STATIC_FOUNDATIONS_AUTHORITY.json", OUT / "SKYREACH_STATIC_FOUNDATIONS_REPORT.json"]
        before = {path: sha256(path) for path in tracked}
        subprocess.run(["python3", str(OUT / "author_skyreach_static.py")], cwd=ROOT, check=True, capture_output=True, text=True)
        after = {path: sha256(path) for path in tracked}
        self.assertEqual(after, before)


if __name__ == "__main__": unittest.main()
