import binascii
import hashlib
import json
import struct
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "engineering/native-assets/whisperwood/equipment-b"
ARMOR = ("whisperwood_helmet", "whisperwood_chest", "whisperwood_legs", "whisperwood_boots")
ACCESSORIES = ("moss_charm", "root_bracelet", "lantern_badge", "moon_sap_pendant", "briar_ring")
TROPHIES = ("thorn_stalker_skull", "briar_elk_trophy", "mosskip_trophy", "ancient_acorn_display")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png(path):
    data, offset, idat = path.read_bytes(), 8, bytearray()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width = height = depth = color = None
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind, payload = data[offset + 4:offset + 8], data[offset + 8:offset + 8 + length]
        expected = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])[0]
        assert binascii.crc32(kind + payload) & 0xFFFFFFFF == expected
        if kind == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", payload[:10])
        elif kind == b"IDAT":
            idat.extend(payload)
        offset += 12 + length
        if kind == b"IEND":
            break
    assert offset == len(data)
    assert len(zlib.decompress(bytes(idat))) == 32 * (1 + 32 * 4)
    return width, height, depth, color


class EquipmentRuntimeBTest(unittest.TestCase):
    def test_armor_is_functional_light_wearable_and_moss_repairable(self):
        expected = {
            "whisperwood_helmet": ("slot.armor.head", 1, 165, 40),
            "whisperwood_chest": ("slot.armor.chest", 3, 240, 60),
            "whisperwood_legs": ("slot.armor.legs", 2, 225, 55),
            "whisperwood_boots": ("slot.armor.feet", 1, 195, 50),
        }
        for asset, (slot, protection, durability, repair) in expected.items():
            item = json.loads((ROOT / f"behavior_pack/items/{asset}.item.json").read_text())["minecraft:item"]
            components = item["components"]
            self.assertEqual(item["description"]["identifier"], f"aionbound:{asset}")
            self.assertEqual(components["minecraft:wearable"], {"slot": slot, "protection": protection})
            self.assertEqual(components["minecraft:durability"], {"max_durability": durability})
            self.assertEqual(components["minecraft:repairable"]["repair_items"], [{"items": ["aionbound:moss_resin"], "repair_amount": repair}])

    def test_accessories_are_single_offhand_items_with_native_visuals(self):
        for asset in ACCESSORIES:
            item = json.loads((ROOT / f"behavior_pack/items/{asset}.item.json").read_text())["minecraft:item"]
            self.assertEqual(item["components"]["minecraft:wearable"], {"slot": "slot.weapon.offhand"})
            self.assertNotIn("minecraft:durability", item["components"])
            attachable = json.loads((ROOT / f"resource_pack/attachables/{asset}.attachable.json").read_text())["minecraft:attachable"]["description"]
            self.assertEqual(attachable["geometry"]["default"], f"geometry.aionbound.{asset}")
            self.assertEqual(attachable["textures"]["default"], f"textures/aionbound/whisperwood/equipment/models/{asset}")
        self.assertEqual(json.loads((ROOT / "resource_pack/attachables/moss_charm.attachable.json").read_text())["minecraft:attachable"]["description"]["animations"], {"idle_sway": "animation.aionbound.moss_charm.idle_sway"})
        self.assertEqual(json.loads((ROOT / "resource_pack/attachables/moon_sap_pendant.attachable.json").read_text())["minecraft:attachable"]["description"]["animations"], {"pulse": "animation.aionbound.moon_sap_pendant.pulse"})

    def test_trophies_are_placeable_display_blocks_without_reward_wiring(self):
        for asset in TROPHIES:
            block = json.loads((ROOT / f"behavior_pack/blocks/{asset}.block.json").read_text())["minecraft:block"]
            self.assertEqual(block["description"]["identifier"], f"aionbound:{asset}")
            self.assertEqual(block["components"]["minecraft:geometry"], f"geometry.aionbound.{asset}")
            self.assertFalse((ROOT / f"behavior_pack/items/{asset}.item.json").exists())
            self.assertFalse((ROOT / f"behavior_pack/loot_tables/blocks/{asset}.loot.json").exists())

    def test_shipping_visual_bytes_are_exact_native_pass_two_and_32px(self):
        categories = {**{asset: "armor" for asset in ARMOR}, **{asset: "accessories" for asset in ACCESSORIES}, **{asset: "trophies" for asset in TROPHIES}}
        for asset, category in categories.items():
            source_texture = NATIVE / f"inputs/{asset}/textures/{asset}.png"
            runtime_texture = ROOT / f"resource_pack/textures/aionbound/whisperwood/equipment/models/{asset}.png"
            self.assertEqual(sha(source_texture), sha(runtime_texture))
            self.assertEqual(png(runtime_texture), (32, 32, 8, 6))
            source_geo = NATIVE / f"evidence/{asset}/native-exports/pass-2.geo.json"
            model_dir = "blocks" if category == "trophies" else "aionbound/equipment"
            runtime_geo = ROOT / f"resource_pack/models/{model_dir}/{asset}.geo.json"
            self.assertEqual(sha(source_geo), sha(runtime_geo))
        for asset in ("moss_charm", "moon_sap_pendant"):
            self.assertEqual(sha(NATIVE / f"evidence/{asset}/native-exports/pass-2.animation.json"), sha(ROOT / f"resource_pack/animations/aionbound/equipment/{asset}.animation.json"))

    def test_ratified_recipe_acquisition_and_no_finished_equipment_loot(self):
        for asset in ARMOR + ACCESSORIES + ("briar_elk_trophy", "mosskip_trophy", "ancient_acorn_display"):
            recipe = json.loads((ROOT / f"behavior_pack/recipes/{asset}.recipe.json").read_text())["minecraft:recipe_shapeless"]
            self.assertEqual(recipe["result"]["item"], f"aionbound:{asset}")
        self.assertFalse((ROOT / "behavior_pack/recipes/thorn_stalker_skull.recipe.json").exists())
        for asset in ARMOR + ACCESSORIES + TROPHIES:
            self.assertFalse((ROOT / f"behavior_pack/loot_tables/equipment/{asset}.loot.json").exists())
            for loot_path in (ROOT / "behavior_pack/loot_tables").rglob("*.json"):
                self.assertNotIn(f"aionbound:{asset}", loot_path.read_text(), loot_path)

    def test_inventory_icons_are_reserved_separately_from_model_uv_sheets(self):
        atlas = json.loads((ROOT / "resource_pack/textures/item_texture.json").read_text())["texture_data"]
        for asset in ARMOR + ACCESSORIES:
            self.assertEqual(atlas[asset]["textures"], f"textures/aionbound/whisperwood/equipment/{asset}")
        terrain = json.loads((ROOT / "resource_pack/textures/terrain_texture.json").read_text())["texture_data"]
        for asset in TROPHIES:
            self.assertEqual(terrain[asset]["textures"], f"textures/aionbound/whisperwood/equipment/models/{asset}")


if __name__ == "__main__":
    unittest.main()
