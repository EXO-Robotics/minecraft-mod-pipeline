from __future__ import annotations

import hashlib
import json
import struct
import unittest
import zlib
from pathlib import Path

import author_crystal_economy_equipment as author


ROOT = author.ROOT


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png(path: Path) -> tuple[int, int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n": raise AssertionError(path)
    width, height = struct.unpack(">II", data[16:24])
    offset, compressed = 8, bytearray()
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        if kind == b"IDAT": compressed.extend(payload)
        offset += length + 12
        if kind == b"IEND": break
    return width, height, len(zlib.decompress(bytes(compressed)))


class CrystalEconomyEquipmentTests(unittest.TestCase):
    def test_exact_identity_scope_and_no_sidegrades(self):
        self.assertEqual(11, len(author.EQUIPMENT))
        self.assertEqual({"prism_wing", "watcher_lens", "wight_shroud", "crystal_pole", "living_crystal_core", "wet_plate"}, set(author.COMPONENTS))
        authored = Path(author.__file__).read_text()
        for forbidden in ("gale_prism", "drowned_crown", "stormcloak"):
            self.assertNotIn(forbidden, authored.lower())

    def test_native_pass_two_geometry_animation_and_uv_are_exact(self):
        for asset in author.EQUIPMENT:
            native = author.NATIVE / asset
            pairs = [
                (native / "native-exports/pass-2.geo.json", ROOT / f"resource_pack/models/aionbound/crystal_marsh/equipment/{asset}.geo.json"),
                (native / "native-exports/pass-2.animation.json", ROOT / f"resource_pack/animations/aionbound/crystal_marsh/equipment/{asset}.animation.json"),
                (native / f"native-project/textures/{asset}.png", ROOT / f"resource_pack/textures/aionbound/crystal_marsh/equipment/models/{asset}.png"),
            ]
            for source, target in pairs: self.assertEqual(sha(source), sha(target), asset)
            attachable = load(ROOT / f"resource_pack/attachables/{asset}.attachable.json")["minecraft:attachable"]["description"]
            self.assertEqual(f"aionbound:{asset}", attachable["identifier"])
            self.assertEqual(f"geometry.aionbound.{asset}", attachable["geometry"]["default"])
            self.assertEqual(f"textures/aionbound/crystal_marsh/equipment/models/{asset}", attachable["textures"]["default"])

    def test_shipping_icons_are_separate_valid_and_distinct(self):
        hashes = set()
        for asset, spec in author.EQUIPMENT.items():
            if spec["role"] == "trophy":
                path = ROOT / f"resource_pack/textures/aionbound/crystal_marsh/equipment/presentation/trophies/{asset}.png"
            else:
                group = "armor" if spec["role"] == "armor" else "accessories" if spec["role"] == "accessory" else "items"
                path = ROOT / f"resource_pack/textures/aionbound/wave1/equipment/{group}/{asset}.png"
            self.assertEqual((32, 32), png(path)[:2], asset)
            self.assertNotEqual(sha(path), sha(ROOT / f"resource_pack/textures/aionbound/crystal_marsh/equipment/models/{asset}.png"), asset)
            hashes.add(sha(path))
        for asset in author.COMPONENTS:
            path = ROOT / f"resource_pack/textures/aionbound/crystal_marsh/components/{asset}.png"
            self.assertEqual((32, 32), png(path)[:2], asset)
            hashes.add(sha(path))
        self.assertEqual(17, len(hashes))

    def test_functional_declarative_roles_are_bounded_and_repairable(self):
        expected = {
            "crystal_pike": ("minecraft:damage", "minecraft:durability", "minecraft:repairable"),
            "prism_bow": ("minecraft:damage", "minecraft:durability", "minecraft:repairable", "minecraft:cooldown"),
            "crystal_circlet": ("minecraft:durability", "minecraft:repairable", "minecraft:wearable"),
            "explorer_cloak": ("minecraft:durability", "minecraft:repairable", "minecraft:wearable"),
            "crystal_shovel": ("minecraft:durability", "minecraft:repairable", "minecraft:digger"),
            "marsh_sickle": ("minecraft:durability", "minecraft:repairable", "minecraft:digger"),
        }
        for asset, keys in expected.items():
            components = load(ROOT / f"behavior_pack/items/{asset}.item.json")["minecraft:item"]["components"]
            for key in keys: self.assertIn(key, components, asset)
        for asset in ("crystal_talisman", "marsh_idol"):
            components = load(ROOT / f"behavior_pack/items/{asset}.item.json")["minecraft:item"]["components"]
            self.assertEqual("slot.weapon.offhand", components["minecraft:wearable"]["slot"])
            self.assertNotIn("minecraft:damage", components)

    def test_recipe_graph_closes_without_trophy_or_sidegrade_bypass(self):
        self.assertEqual(13, len(author.RECIPES))
        self.assertNotIn("marsh_wight_mask", author.RECIPES)
        self.assertNotIn("crystal_obelisk_fragment", author.RECIPES)
        results = {result for _ingredients, result in author.RECIPES.values()}
        for expected in ("aionbound:crystal_pike", "aionbound:prism_bow", "aionbound:crystal_circlet", "aionbound:explorer_cloak", "aionbound:crystal_shovel", "aionbound:marsh_sickle", "aionbound:crystal_talisman", "aionbound:marsh_idol", "aionbound:moon_pearl_pedestal"):
            self.assertIn(expected, results)
        self.assertEqual((['aionbound:mire_bloom_item'], 'minecraft:cyan_dye'), author.RECIPES['mire_bloom_cyan_dye'])
        for name in author.RECIPES:
            body = load(ROOT / f"behavior_pack/recipes/{name}.recipe.json")["minecraft:recipe_shapeless"]
            self.assertEqual(f"aionbound:{name}_recipe", body["description"]["identifier"])
            self.assertLessEqual(len(body["ingredients"]), 9)

    def test_all_loot_tables_parse_and_ecology_wight_cannot_grant_mask(self):
        for folder in ("entities/crystal", "chests/crystal", "encounters/crystal"):
            for path in (ROOT / "behavior_pack/loot_tables" / folder).glob("*.json"):
                self.assertIn("pools", load(path), path)
        ecology = (ROOT / "behavior_pack/loot_tables/entities/crystal/marsh_wight.json").read_text()
        self.assertNotIn("marsh_wight_mask", ecology)
        self.assertNotIn("pearl_depths", ecology.lower())
        for path in [*(ROOT / "behavior_pack/loot_tables/entities/crystal").glob("*.json"), *(ROOT / "behavior_pack/loot_tables/chests/crystal").glob("*.json"), *(ROOT / "behavior_pack/loot_tables/encounters/crystal").glob("*.json")]:
            self.assertNotIn("marsh_wight_mask", path.read_text(), path)

    def test_probability_bands_and_chest_roll_bands(self):
        for creature, rows in author.ENTITY_LOOT.items():
            for _item, chance, low, high in rows:
                self.assertGreaterEqual(chance, .08, creature)
                self.assertLessEqual(chance, 1.0, creature)
                self.assertGreaterEqual(low, 1); self.assertLessEqual(high, 4)
        approved = {"minor_cache": (2, 3, 1), "standard_structure": (3, 5, 1), "landmark_structure": (4, 6, 2), "apex_arena_chest": (4, 6, 2)}
        for name, (band, guaranteed, choice, _fixed, _choices) in author.CHESTS.items():
            low, high, exact_guaranteed = approved[band]
            self.assertEqual(exact_guaranteed, guaranteed, name)
            self.assertEqual((low, high), (guaranteed + choice[0], guaranteed + choice[1]), name)

    def test_resources_are_acquirable_and_protected_rewards_remain_separate(self):
        for block in author.RESOURCE_BLOCKS:
            components = load(ROOT / f"behavior_pack/blocks/{block}.block.json")["minecraft:block"]["components"]
            self.assertEqual(f"loot_tables/blocks/{block}.json", components["minecraft:loot"])
        report = load(author.HERE / "CRYSTAL_ECONOMY_EQUIPMENT_REPORT.json")
        self.assertFalse(report["protected_pearl_depths"]["contains_mask"])
        self.assertFalse(report["protected_pearl_depths"]["static_structure_binding"])
        self.assertFalse(report["mastery"]["pilgrim_seal_substitute"])
        self.assertEqual("DEFERRED_UNCHANGED_NO_SIDEGRADES", report["w1_creative_005"])

    def test_generator_check_is_byte_deterministic(self):
        before = {path: sha(path) for path in [author.HERE / "CRYSTAL_ECONOMY_EQUIPMENT_REPORT.json", ROOT / "resource_pack/textures/item_texture.json", ROOT / "resource_pack/texts/en_US.lang"]}
        author.author()
        self.assertEqual(before, {path: sha(path) for path in before})

    def test_language_refresh_preserves_unrelated_later_vertical_order(self):
        lines = [
            "before=Before",
            "item.aionbound:crystal_pike.name=Old Pike",
            "item.aionbound:prism_wing.name=Old Wing",
            "# BEGIN WAVE1 SKYREACH RESOURCE ITEMS",
            "item.aionbound:sky_feather=Sky Feather",
            "# END WAVE1 SKYREACH RESOURCE ITEMS",
        ]
        entries = ["item.aionbound:crystal_pike.name=Crystal Pike", "item.aionbound:prism_wing.name=Prism Wing"]
        prefixes = ["item.aionbound:crystal_pike.name=", "item.aionbound:prism_wing.name="]
        refreshed = author.replace_owned_language_entries(lines, entries, prefixes)
        self.assertEqual(refreshed[:3], ["before=Before", *entries])
        self.assertEqual(refreshed[3:], lines[3:])


if __name__ == "__main__":
    unittest.main()
