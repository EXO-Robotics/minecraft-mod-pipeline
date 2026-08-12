from __future__ import annotations

import hashlib
import json
import struct
import unittest
import zlib
from pathlib import Path

import author_presentation_shells as author


ROOT = author.ROOT


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(path)
    width, height = struct.unpack(">II", data[16:24])
    offset, compressed = 8, bytearray()
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        if kind == b"IDAT":
            compressed.extend(payload)
        offset += length + 12
        if kind == b"IEND":
            break
    zlib.decompress(bytes(compressed))
    return width, height


class Packet006PresentationShellTests(unittest.TestCase):
    def test_exact_five_base_identities_only(self):
        self.assertEqual(
            {"surveyor_medallion", "surveyor_staff", "trail_compass", "warden_sigil", "twinbond_relic"},
            set(author.ASSETS),
        )
        for asset in author.ASSETS:
            item = load(ROOT / f"behavior_pack/items/{asset}.item.json")["minecraft:item"]
            self.assertEqual(f"aionbound:{asset}", item["description"]["identifier"])
            self.assertNotIn("menu_category", item["description"])
            self.assertEqual({"minecraft:display_name", "minecraft:icon", "minecraft:max_stack_size"}, set(item["components"]))

    def test_native_pass_two_geometry_animation_and_model_texture_are_exact(self):
        for asset, spec in author.ASSETS.items():
            native = ROOT / spec["native"]
            pairs = (
                (native / "native-exports/pass-2.geo.json", ROOT / f"resource_pack/models/aionbound/wave1/packet006/{asset}.geo.json"),
                (native / "native-exports/pass-2.animation.json", ROOT / f"resource_pack/animations/aionbound/wave1/packet006/{asset}.animation.json"),
                (native / f"native-project/textures/{asset}.png", ROOT / f"resource_pack/textures/aionbound/wave1/packet006/models/{asset}.png"),
            )
            for source, target in pairs:
                self.assertEqual(sha(source), sha(target), asset)

    def test_attachables_resolve_exact_geometry_texture_and_clip(self):
        for asset, spec in author.ASSETS.items():
            desc = load(ROOT / f"resource_pack/attachables/{asset}.attachable.json")["minecraft:attachable"]["description"]
            self.assertEqual(f"aionbound:{asset}", desc["identifier"])
            self.assertEqual(f"geometry.aionbound.{asset}", desc["geometry"]["default"])
            self.assertEqual(f"textures/aionbound/wave1/packet006/models/{asset}", desc["textures"]["default"])
            if spec["clip"]:
                clip = spec["clip"]
                self.assertEqual({clip: f"animation.aionbound.{asset}.{clip}"}, desc["animations"])
                self.assertEqual([clip], desc["scripts"]["animate"])
            else:
                self.assertNotIn("animations", desc)
                self.assertNotIn("scripts", desc)

    def test_icons_are_valid_distinct_and_separate_from_model_uv(self):
        hashes = set()
        for asset, spec in author.ASSETS.items():
            icon = ROOT / f"resource_pack/textures/aionbound/wave1/packet006/icons/{asset}.png"
            model = ROOT / f"resource_pack/textures/aionbound/wave1/packet006/models/{asset}.png"
            self.assertEqual((32, 32), png_size(icon), asset)
            self.assertNotEqual(sha(icon), sha(model), asset)
            hashes.add(sha(icon))
        self.assertEqual(5, len(hashes))

    def test_atlas_and_language_close_each_identity(self):
        atlas = load(ROOT / "resource_pack/textures/item_texture.json")["texture_data"]
        lang = (ROOT / "resource_pack/texts/en_US.lang").read_text(encoding="utf-8")
        for asset, spec in author.ASSETS.items():
            self.assertEqual(f"textures/aionbound/wave1/packet006/icons/{asset}", atlas[asset]["textures"])
            self.assertIn(f"item.aionbound:{asset}.name={spec['name']}\n", lang)

    def test_no_gameplay_or_acquisition_surfaces_created(self):
        report = load(author.HERE / "PACKET006_PRESENTATION_SHELLS_REPORT.json")
        self.assertEqual("DORMANT_PRESENTATION_IDENTITY_ONLY", report["authority_gate"]["state"])
        for value in report["invariants"].values():
            self.assertIn(value, (0, False))
        for asset in author.ASSETS:
            self.assertFalse((ROOT / f"behavior_pack/recipes/{asset}.recipe.json").exists())
            for loot_root in (ROOT / "behavior_pack/loot_tables",):
                for path in loot_root.rglob("*.json"):
                    self.assertNotIn(f"aionbound:{asset}", path.read_text(encoding="utf-8"), str(path))
        for script in (ROOT / "behavior_pack/scripts").glob("*.js"):
            body = script.read_text(encoding="utf-8")
            for asset in author.ASSETS:
                self.assertNotIn(f"aionbound:{asset}", body, str(script))

    def test_generator_is_byte_deterministic(self):
        observed = [
            author.HERE / "PACKET006_PRESENTATION_SHELLS_REPORT.json",
            ROOT / "resource_pack/textures/item_texture.json",
            ROOT / "resource_pack/texts/en_US.lang",
            *[ROOT / f"resource_pack/textures/aionbound/wave1/packet006/icons/{asset}.png" for asset in author.ASSETS],
        ]
        before = {path: sha(path) for path in observed}
        author.author()
        self.assertEqual(before, {path: sha(path) for path in observed})


if __name__ == "__main__":
    unittest.main()
