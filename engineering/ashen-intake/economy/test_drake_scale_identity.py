#!/usr/bin/env python3

import hashlib
import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ITEM = ROOT / "behavior_pack/items/drake_scale.item.json"
ATLAS = ROOT / "resource_pack/textures/item_texture.json"
LANG = ROOT / "resource_pack/texts/en_US.lang"
PNG = ROOT / "resource_pack/textures/aionbound/ashen/items/drake_scale.png"
RECEIPT = ROOT / "assets/wave1/ashen/economy-icons/ASHEN_DRAKE_SCALE_ICON_RECEIPT.json"
LEDGER = ROOT / "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json"


class DrakeScaleIdentityTests(unittest.TestCase):
    def test_exact_ratified_identity_and_sidegrade_boundary(self):
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        approved = {row["tranche"]: row for row in ledger["ratifications"]["approved"]}
        self.assertIn("W1-001-AH", approved)
        self.assertIn("W1-CREATIVE-005", ledger["ratifications"]["deferred"])
        item = json.loads(ITEM.read_text(encoding="utf-8"))["minecraft:item"]
        self.assertEqual(item["description"]["identifier"], "aionbound:drake_scale")
        self.assertEqual(item["components"]["minecraft:icon"]["textures"]["default"], "drake_scale")

    def test_atlas_language_and_shipping_png_close(self):
        atlas = json.loads(ATLAS.read_text(encoding="utf-8"))["texture_data"]
        self.assertEqual(atlas["drake_scale"]["textures"], "textures/aionbound/ashen/items/drake_scale")
        self.assertIn("item.aionbound:drake_scale=Drake Scale", LANG.read_text(encoding="utf-8").splitlines())
        data = PNG.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
        self.assertEqual((width, height, bit_depth, color_type), (128, 128, 8, 6))

    def test_receipt_hashes_exact_shipping_bytes(self):
        receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        for row in (receipt["source"], receipt["shipping"]):
            path = ROOT / row["path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["sha256"])
        self.assertEqual(receipt["generation"]["calls"], 1)


if __name__ == "__main__":
    unittest.main()
