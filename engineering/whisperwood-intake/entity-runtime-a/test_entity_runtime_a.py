#!/usr/bin/env python3

from __future__ import annotations

import binascii
import json
import struct
import unittest
import zlib
from pathlib import Path

from build_entity_runtime_a import ASSETS, EVIDENCE, ROOT, normalize_ids


EXPECTED_LOOT = {
    "lantern_hare": {"aionbound:glow_spore", "aionbound:lantern_fur"},
    "mosskip_fawn": {"aionbound:moss_resin", "aionbound:star_grass"},
    "mosskip_doe": {"aionbound:moss_resin", "aionbound:whisper_bark"},
    "mosskip_buck": {
        "aionbound:moss_resin",
        "aionbound:whisper_bark",
        "aionbound:mosskip_crown_fragment",
    },
    "rootback_boar": {
        "aionbound:whisper_bark",
        "aionbound:briar_antler",
        "aionbound:root_heart",
    },
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def decode_png(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{path}: bad PNG signature")
    offset = 8
    idat = bytearray()
    width = height = bit_depth = color_type = interlace = None
    saw_end = False
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        crc = struct.unpack(">I", data[offset + 8 + length : offset + 12 + length])[0]
        if binascii.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise AssertionError(f"{path}: CRC failure in {kind!r}")
        offset += length + 12
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            saw_end = True
            break
    if not saw_end or offset != len(data):
        raise AssertionError(f"{path}: incomplete or trailing PNG data")
    if (bit_depth, color_type, interlace) != (8, 6, 0):
        raise AssertionError(f"{path}: expected non-interlaced 8-bit RGBA")
    raw = zlib.decompress(bytes(idat))
    if len(raw) != height * (1 + width * 4):
        raise AssertionError(f"{path}: incomplete RGBA scanlines")
    return width, height


class WhisperwoodEntityRuntimeATest(unittest.TestCase):
    def paths(self, asset: str) -> dict[str, Path]:
        return {
            "behavior": ROOT / f"behavior_pack/entities/{asset}.entity.json",
            "spawn": ROOT / f"behavior_pack/spawn_rules/{asset}.spawn_rules.json",
            "client": ROOT / f"resource_pack/entity/{asset}.entity.json",
            "geometry": ROOT / f"resource_pack/models/aionbound/whisperwood/{asset}.geo.json",
            "animations": ROOT / f"resource_pack/animations/aionbound/whisperwood/{asset}.animation.json",
            "controller": ROOT / f"resource_pack/animation_controllers/aionbound/whisperwood/{asset}.animation_controllers.json",
            "render": ROOT / f"resource_pack/render_controllers/aionbound/whisperwood/{asset}.render_controllers.json",
            "texture": ROOT / f"resource_pack/textures/aionbound/whisperwood/entity/{asset}.png",
        }

    def test_exact_file_set_and_native_inputs(self) -> None:
        for asset in ASSETS:
            with self.subTest(asset=asset):
                paths = self.paths(asset)
                self.assertTrue(all(path.is_file() for path in paths.values()))
                receipt = load(EVIDENCE / asset / "entity-animation-native-receipt.json")
                self.assertEqual("PASS", receipt["status"])
                expected_geo = normalize_ids(load(EVIDENCE / asset / "native-exports/pass-2.geo.json"))
                expected_anim = normalize_ids(load(EVIDENCE / asset / "native-exports/pass-2.animation.json"))
                self.assertEqual(expected_geo, load(paths["geometry"]))
                self.assertEqual(expected_anim, load(paths["animations"]))
                self.assertEqual(
                    (EVIDENCE / asset / f"native-project/textures/{asset}.png").read_bytes(),
                    paths["texture"].read_bytes(),
                )

    def test_identifier_geometry_animation_controller_and_render_closure(self) -> None:
        for asset, spec in ASSETS.items():
            with self.subTest(asset=asset):
                paths = self.paths(asset)
                behavior = load(paths["behavior"])["minecraft:entity"]
                client = load(paths["client"])["minecraft:client_entity"]["description"]
                geometry = load(paths["geometry"])["minecraft:geometry"][0]
                animations = load(paths["animations"])["animations"]
                controller_doc = load(paths["controller"])["animation_controllers"]
                render_doc = load(paths["render"])["render_controllers"]

                self.assertEqual(f"aionbound:{asset}", behavior["description"]["identifier"])
                self.assertEqual(behavior["description"]["identifier"], client["identifier"])
                self.assertEqual(f"geometry.aionbound.whisperwood.{asset}", geometry["description"]["identifier"])
                self.assertEqual(geometry["description"]["identifier"], client["geometry"]["default"])
                self.assertNotIn("aionforge_ww", json.dumps([client, geometry, animations, controller_doc, render_doc]))

                aliases = client["animations"]
                self.assertEqual(set(animations), {value for key, value in aliases.items() if key != "runtime"})
                controller_id = f"controller.animation.aionbound.whisperwood.{asset}.runtime"
                self.assertEqual(controller_id, aliases["runtime"])
                self.assertIn(controller_id, controller_doc)
                self.assertEqual(["runtime"], client["scripts"]["animate"])

                render_id = f"controller.render.aionbound.whisperwood.{asset}"
                self.assertEqual([render_id], client["render_controllers"])
                self.assertIn(render_id, render_doc)

                bones = {bone["name"] for bone in geometry["bones"]}
                for clip in animations.values():
                    self.assertTrue(set(clip.get("bones", {})).issubset(bones))
                states = controller_doc[controller_id]["states"]
                played_aliases = {name for state in states.values() for name in state.get("animations", [])}
                self.assertTrue({spec["idle"], spec["move"], "hurt", "death"}.issubset(played_aliases))

    def test_server_ai_and_ratified_natural_loot_close(self) -> None:
        for asset, spec in ASSETS.items():
            with self.subTest(asset=asset):
                components = load(self.paths(asset)["behavior"])["minecraft:entity"]["components"]
                required = {
                    "minecraft:movement",
                    "minecraft:movement.basic",
                    "minecraft:navigation.walk",
                    "minecraft:despawn",
                    "minecraft:behavior.random_stroll",
                    "minecraft:behavior.look_at_player",
                    "minecraft:behavior.random_look_around",
                }
                self.assertTrue(required.issubset(components))
                expected_table = f"loot_tables/entities/{asset}.json"
                self.assertEqual({"table": expected_table}, components["minecraft:loot"])
                loot_path = ROOT / "behavior_pack" / expected_table
                self.assertTrue(loot_path.is_file())
                loot = load(loot_path)
                self.assertEqual(
                    EXPECTED_LOOT[asset],
                    {entry["name"] for pool in loot["pools"] for entry in pool["entries"]},
                )
                self.assertNotIn("aionbound:thorn_stalker_skull", json.dumps(loot))
                self.assertLessEqual(components["minecraft:behavior.random_stroll"]["speed_multiplier"], 0.8)
                self.assertGreaterEqual(components["minecraft:behavior.random_stroll"]["interval"], 100)
                if spec["class"] == "ambient":
                    self.assertIn("minecraft:behavior.panic", components)
                    self.assertNotIn("minecraft:attack", components)
                else:
                    self.assertIn("minecraft:attack", components)
                    self.assertIn("minecraft:behavior.hurt_by_target", components)
                    self.assertIn("minecraft:behavior.melee_attack", components)
                    self.assertNotIn("minecraft:behavior.nearest_attackable_target", components)

    def test_spawn_rules_are_conservative_and_forest_scoped(self) -> None:
        for asset in ASSETS:
            with self.subTest(asset=asset):
                spawn = load(self.paths(asset)["spawn"])["minecraft:spawn_rules"]
                self.assertEqual(f"aionbound:{asset}", spawn["description"]["identifier"])
                self.assertEqual("animal", spawn["description"]["population_control"])
                self.assertEqual(1, len(spawn["conditions"]))
                condition = spawn["conditions"][0]
                self.assertIn("minecraft:spawns_on_surface", condition)
                self.assertLessEqual(condition["minecraft:weight"]["default"], 3)
                self.assertLessEqual(condition["minecraft:herd"]["max_size"], 2)
                self.assertEqual({"surface": 2, "underground": 0}, condition["minecraft:density_limit"])
                self.assertEqual({"min": 24, "max": 96}, condition["minecraft:distance_filter"])
                tags = {entry["value"] for entry in condition["minecraft:biome_filter"]["all_of"]}
                self.assertEqual({"overworld", "forest"}, tags)

    def test_textures_fully_decode_and_match_geometry_atlas(self) -> None:
        for asset in ASSETS:
            with self.subTest(asset=asset):
                width, height = decode_png(self.paths(asset)["texture"])
                geometry = load(self.paths(asset)["geometry"])["minecraft:geometry"][0]["description"]
                self.assertEqual((geometry["texture_width"], geometry["texture_height"]), (width, height))


if __name__ == "__main__":
    unittest.main(verbosity=2)
