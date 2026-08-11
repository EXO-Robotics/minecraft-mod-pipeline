#!/usr/bin/env python3
"""Targeted static closure and semantic tests for Ashen equipment runtime."""

from __future__ import annotations

import binascii
import hashlib
import json
import struct
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LANE = ROOT / "engineering/ashen-intake/equipment-runtime-ashen"
NATIVE = ROOT / "engineering/native-assets/ashen/equipment/evidence"
SPECS = {
    "basalt_hammer": ("weapon", ["idle_hold", "smash_pose"], "idle_hold"),
    "ember_great_axe": ("weapon", ["idle_hold", "overhead_pose", "slam_pose"], "idle_hold"),
    "ash_repeater": ("weapon", ["crank_pose", "fire_pose", "idle_hold"], "idle_hold"),
    "ashen_helmet": ("armor_head", ["vent_pulse_showcase"], "vent_pulse_showcase"),
    "ashen_chest": ("armor_chest", [], None),
    "ashen_legs": ("armor_legs", [], None),
    "ashen_boots": ("armor_feet", [], None),
    "basalt_pick": ("tool", ["hold", "swing"], "hold"),
    "ember_hammer": ("tool", ["hold", "tap"], "hold"),
    "ore_chisel": ("tool", ["hold", "tap"], "hold"),
    "ember_totem": ("accessory", ["vent_pulse"], "vent_pulse"),
    "ash_drake_horn": ("trophy", ["pulse_base"], "pulse_base"),
    "ember_forge_core": ("trophy", ["idle_pulse"], "idle_pulse"),
}
COMPONENTS = ("heat_core", "heavy_head", "chitin_plate", "ember_heart")
FORBIDDEN_NUMERIC = {
    "minecraft:damage", "minecraft:durability", "minecraft:repairable",
    "minecraft:digger", "minecraft:cooldown", "minecraft:use_modifiers",
}
FUNCTIONAL_SUCCESSOR_ITEMS = {
    "basalt_hammer", "ember_great_axe", "ash_repeater", "ashen_helmet", "ashen_chest",
    "ashen_legs", "ashen_boots", "basalt_pick", "ember_hammer", "ore_chisel",
}
BRIAR_HASHES = {
    # Exact bytes at the requested 7505ac2 integration authority. The earlier
    # intake inventory predates a legitimate Whisperwood-line item update.
    "behavior_pack/items/briar_ring.item.json": "052dde829b4b96fb01f3c060062e14e2f5f5d27c48ac841d56ae54eb34bc4748",
    "resource_pack/attachables/briar_ring.attachable.json": "af751b1473b19b36ca84c1787de4cf5e523d00ca0a9240fe0595a95054c8d4b3",
    "resource_pack/models/aionbound/equipment/briar_ring.geo.json": "fe624190389b6082c3195fdf57c5faf2b96bfaf879073aa396ecb19ddb7e7222",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_rgba(path: Path) -> tuple[int, int, list[bytes]]:
    data, offset, compressed = path.read_bytes(), 8, bytearray()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"invalid PNG signature: {path}")
    width = height = depth = color = None
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        expected = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])[0]
        if binascii.crc32(kind + payload) & 0xFFFFFFFF != expected:
            raise AssertionError(f"PNG CRC mismatch: {path}")
        if kind == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", payload[:10])
        elif kind == b"IDAT":
            compressed.extend(payload)
        offset += length + 12
        if kind == b"IEND":
            break
    if (depth, color) != (8, 6):
        raise AssertionError(f"expected 8-bit RGBA: {path}: {(depth, color)}")
    raw = zlib.decompress(bytes(compressed))
    stride = width * 4
    rows, previous, pos = [], bytearray(stride), 0
    for _ in range(height):
        filter_type = raw[pos]
        current = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += stride + 1
        for i in range(stride):
            left = current[i - 4] if i >= 4 else 0
            up = previous[i]
            upper_left = previous[i - 4] if i >= 4 else 0
            if filter_type == 1:
                current[i] = (current[i] + left) & 255
            elif filter_type == 2:
                current[i] = (current[i] + up) & 255
            elif filter_type == 3:
                current[i] = (current[i] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                p = left + up - upper_left
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upper_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else upper_left
                current[i] = (current[i] + predictor) & 255
            elif filter_type != 0:
                raise AssertionError(f"unsupported PNG filter {filter_type}")
        rows.append(bytes(current))
        previous = current
    return width, height, rows


class AshenEquipmentRuntimeTest(unittest.TestCase):
    def test_all_runtime_json_parses(self):
        owned = [
            *(ROOT / f"behavior_pack/items/{asset}.item.json" for asset, spec in SPECS.items() if spec[0] != "trophy"),
            *(ROOT / f"behavior_pack/blocks/{asset}.block.json" for asset, spec in SPECS.items() if spec[0] == "trophy"),
            *(ROOT / f"behavior_pack/items/{asset}.item.json" for asset in COMPONENTS),
            *(ROOT / f"resource_pack/attachables/{asset}.attachable.json" for asset in SPECS),
            *(ROOT / f"resource_pack/models/aionbound/ashen/equipment/{asset}.geo.json" for asset in SPECS),
            *(ROOT / f"resource_pack/animations/aionbound/ashen/equipment/{asset}.animation.json" for asset in SPECS),
        ]
        for path in owned:
            self.assertIsInstance(load(path), dict, path)

    def test_base_roles_are_preserved_and_successor_functional_components_are_bounded(self):
        slots = {
            "armor_head": "slot.armor.head", "armor_chest": "slot.armor.chest",
            "armor_legs": "slot.armor.legs", "armor_feet": "slot.armor.feet",
            "accessory": "slot.weapon.offhand",
        }
        for asset, (role, _, _) in SPECS.items():
            if role == "trophy":
                continue
            item = load(ROOT / f"behavior_pack/items/{asset}.item.json")["minecraft:item"]
            self.assertEqual(item["description"]["identifier"], f"aionbound:{asset}")
            components = item["components"]
            if asset in FUNCTIONAL_SUCCESSOR_ITEMS:
                self.assertIn("minecraft:durability", components, asset)
                self.assertIn("minecraft:repairable", components, asset)
            else:
                self.assertTrue(FORBIDDEN_NUMERIC.isdisjoint(components), asset)
            self.assertEqual(components.get("minecraft:hand_equipped", False), role in {"weapon", "tool"})
            if role in slots:
                self.assertEqual(components["minecraft:wearable"]["slot"], slots[role])
                if asset in FUNCTIONAL_SUCCESSOR_ITEMS:
                    self.assertGreater(components["minecraft:wearable"]["protection"], 0)
            else:
                self.assertNotIn("minecraft:wearable", components)

    def test_components_are_ratified_identity_shells_only(self):
        for asset in COMPONENTS:
            item = load(ROOT / f"behavior_pack/items/{asset}.item.json")["minecraft:item"]
            self.assertEqual(item["description"]["identifier"], f"aionbound:{asset}")
            self.assertEqual(item["components"]["minecraft:max_stack_size"], 64)
            self.assertTrue(FORBIDDEN_NUMERIC.isdisjoint(item["components"]))

    def test_trophies_are_placeable_displays_with_native_visuals(self):
        for asset in ("ash_drake_horn", "ember_forge_core"):
            block = load(ROOT / f"behavior_pack/blocks/{asset}.block.json")["minecraft:block"]
            self.assertEqual(block["description"]["identifier"], f"aionbound:{asset}")
            self.assertEqual(block["components"]["minecraft:geometry"], f"geometry.aionbound.{asset}")
            self.assertFalse((ROOT / f"behavior_pack/items/{asset}.item.json").exists())

    def test_native_pass_two_bytes_and_attachment_closure(self):
        for asset, (_, clips, idle) in SPECS.items():
            native = NATIVE / asset
            geometry = ROOT / f"resource_pack/models/aionbound/ashen/equipment/{asset}.geo.json"
            animation = ROOT / f"resource_pack/animations/aionbound/ashen/equipment/{asset}.animation.json"
            model_uv = ROOT / f"resource_pack/textures/aionbound/ashen/equipment/models/{asset}.png"
            self.assertEqual(sha(geometry), sha(native / "native-exports/pass-2.geo.json"), asset)
            self.assertEqual(sha(animation), sha(native / "native-exports/pass-2.animation.json"), asset)
            self.assertEqual(sha(model_uv), sha(native / f"native-project/textures/{asset}.png"), asset)
            geo = load(geometry)["minecraft:geometry"][0]
            self.assertEqual(geo["description"]["identifier"], f"geometry.aionbound.{asset}")
            self.assertIn("effect", {loc for bone in geo["bones"] for loc in bone.get("locators", {})}, asset)
            attachable = load(ROOT / f"resource_pack/attachables/{asset}.attachable.json")["minecraft:attachable"]["description"]
            self.assertEqual(attachable["identifier"], f"aionbound:{asset}")
            self.assertEqual(attachable["geometry"]["default"], f"geometry.aionbound.{asset}")
            self.assertEqual(attachable["textures"]["default"], f"textures/aionbound/ashen/equipment/models/{asset}")
            expected_animations = {clip: f"animation.aionbound.{asset}.{clip}" for clip in clips}
            self.assertEqual(attachable.get("animations", {}), expected_animations)
            self.assertEqual(attachable.get("scripts", {}).get("animate", []), [idle] if idle else [])
            self.assertEqual(set(load(animation)["animations"]), set(expected_animations.values()))

    def test_atlas_and_language_closure(self):
        item_atlas = load(ROOT / "resource_pack/textures/item_texture.json")["texture_data"]
        terrain_atlas = load(ROOT / "resource_pack/textures/terrain_texture.json")["texture_data"]
        lang = (ROOT / "resource_pack/texts/en_US.lang").read_text(encoding="utf-8")
        for asset, (role, _, _) in SPECS.items():
            self.assertEqual(item_atlas[asset]["textures"], f"textures/aionbound/ashen/equipment/{asset}")
            prefix = "tile" if role == "trophy" else "item"
            self.assertIn(f"{prefix}.aionbound:{asset}.name=", lang)
            if role == "trophy":
                self.assertEqual(terrain_atlas[asset]["textures"], f"textures/aionbound/ashen/equipment/models/{asset}")
        for asset in COMPONENTS:
            self.assertEqual(item_atlas[asset]["textures"], f"textures/aionbound/ashen/components/{asset}")
            self.assertIn(f"item.aionbound:{asset}.name=", lang)

    def test_shipping_icons_are_distinct_transparent_and_separate_from_model_uv(self):
        hashes = set()
        for asset in (*SPECS, *COMPONENTS):
            group = "components" if asset in COMPONENTS else "equipment"
            icon = ROOT / f"resource_pack/textures/aionbound/ashen/{group}/{asset}.png"
            width, height, rows = decode_rgba(icon)
            self.assertEqual((width, height), (32, 32), asset)
            alphas = [row[i] for row in rows for i in range(3, len(row), 4)]
            corners = [rows[0][3], rows[0][-1], rows[-1][3], rows[-1][-1]]
            self.assertTrue(all(alpha <= 4 for alpha in corners), (asset, corners))
            visible = sum(alpha >= 32 for alpha in alphas)
            self.assertGreater(visible, 32, asset)
            self.assertLess(visible, 950, asset)
            hashes.add(sha(icon))
            if asset in SPECS:
                model_uv = ROOT / f"resource_pack/textures/aionbound/ashen/equipment/models/{asset}.png"
                self.assertNotEqual(sha(icon), sha(model_uv), asset)
        self.assertEqual(len(hashes), 17)

    def test_imagegen_receipt_and_hashes_are_exact(self):
        report = load(LANE / "ASHEN_EQUIPMENT_RUNTIME_REPORT.json")
        self.assertEqual(report["authority_commit"], "7505ac2223f362d9b4e59a82cab5486cab304fc5")
        self.assertEqual(report["icon_pipeline"]["calls"], 17)
        self.assertEqual(report["icon_pipeline"]["call_rule"], "one call per distinct icon")
        self.assertEqual(report["scope"]["deferred"], "W1-CREATIVE-005")
        self.assertEqual(report["scope"]["preserved_existing_base"], "aionbound:briar_ring")
        for record in [*report["equipment"], *report["components"]]:
            self.assertIn("Primary request:", record["prompt"])
            for details in record["files"].values():
                path = ROOT / details["path"]
                # The runtime-A receipt remains evidence for its shell-era
                # authority. Behavior items intentionally advance in the
                # functional successor and are hash-bound by the new lane.
                if path.parent == ROOT / "behavior_pack/items" and path.stem.replace(".item", "") in FUNCTIONAL_SUCCESSOR_ITEMS:
                    self.assertRegex(details["sha256"], r"^[0-9a-f]{64}$")
                    self.assertNotEqual(sha(path), details["sha256"], path)
                else:
                    self.assertEqual(sha(path), details["sha256"], path)

    def test_briar_ring_is_byte_preserved_and_deferred_sidegrades_are_absent(self):
        for relative, expected in BRIAR_HASHES.items():
            self.assertEqual(sha(ROOT / relative), expected, relative)
        authored = (LANE / "author_runtime.py").read_text(encoding="utf-8")
        self.assertNotIn("W1-CREATIVE-005/", authored)
        self.assertNotIn("behavior_pack/recipes", authored)
        self.assertNotIn("behavior_pack/loot_tables", authored)


if __name__ == "__main__":
    unittest.main()
