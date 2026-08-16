from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
BUILDER_PATH = ROOT / "engineering/client-visual-r1/build_client_visual_test_pack.py"
SPEC = importlib.util.spec_from_file_location("client_visual_builder", BUILDER_PATH)
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BUILDER)


class ClientVisualTestPackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "out"
        cls.receipt = BUILDER.build(cls.output)
        cls.rp = cls.output / "staging/resource_pack"
        cls.bp = cls.output / "staging/behavior_pack"

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_manifest_versions_and_dependencies_are_reciprocal(self):
        bp = json.loads((self.bp / "manifest.json").read_text())
        rp = json.loads((self.rp / "manifest.json").read_text())
        self.assertEqual(bp["header"]["version"], [1, 3, 2])
        self.assertEqual(rp["header"]["version"], [1, 3, 2])
        self.assertEqual(bp["dependencies"][0]["version"], [1, 3, 2])
        self.assertEqual(rp["dependencies"][0]["version"], [1, 3, 2])

    def test_bounded_mutation_inventory(self):
        def digest(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()

        source_bp = {str(p.relative_to(ROOT / "behavior_pack")): digest(p) for p in (ROOT / "behavior_pack").rglob("*") if p.is_file()}
        staged_bp = {str(p.relative_to(self.bp)): digest(p) for p in self.bp.rglob("*") if p.is_file()}
        self.assertEqual(set(source_bp), set(staged_bp))
        self.assertEqual(
            sorted(path for path in source_bp if source_bp[path] != staged_bp[path]),
            ["manifest.json"],
        )

        source_rp = {str(p.relative_to(ROOT / "resource_pack")): digest(p) for p in (ROOT / "resource_pack").rglob("*") if p.is_file()}
        staged_rp = {str(p.relative_to(self.rp)): digest(p) for p in self.rp.rglob("*") if p.is_file()}
        removed = sorted(set(source_rp) - set(staged_rp))
        added = sorted(set(staged_rp) - set(source_rp))
        changed = sorted(path for path in set(source_rp) & set(staged_rp) if source_rp[path] != staged_rp[path])
        self.assertEqual(removed, [
            "models/aionbound/ashen/entities/char_wolf.geo.json",
            "models/aionbound/trophy_edge_assembled.geo.json",
        ])
        self.assertEqual(added, [
            "models/entity/aionbound/ashen/char_wolf.geo.json",
            "models/entity/aionbound/trophy_edge_assembled.geo.json",
        ])
        self.assertEqual(changed, [
            "attachables/trophy_edge.attachable.json",
            "manifest.json",
            "textures/aionbound/trophy_edge.png",
        ])

    def test_trophy_edge_attachable_contract(self):
        data = json.loads((self.rp / "attachables/trophy_edge.attachable.json").read_text())
        desc = data["minecraft:attachable"]["description"]
        self.assertEqual(desc["item"], {"aionbound:trophy_edge": "query.is_owner_identifier_any('minecraft:player')"})
        self.assertEqual(desc["render_controllers"], ["controller.render.item_default"])
        self.assertEqual(set(desc["animations"]), {"hold_first_person", "hold_third_person"})
        self.assertNotIn("controller.render.aionbound.default", desc["render_controllers"])

    def test_trophy_edge_geometry_contract(self):
        old = self.rp / "models/aionbound/trophy_edge_assembled.geo.json"
        new = self.rp / "models/entity/aionbound/trophy_edge_assembled.geo.json"
        self.assertFalse(old.exists())
        data = json.loads(new.read_text())
        geometry = data["minecraft:geometry"][0]
        root = [b for b in geometry["bones"] if "parent" not in b][0]
        self.assertEqual(root["binding"], "q.item_slot_to_bone_name(context.item_slot)")
        self.assertEqual(root["pivot"], [0, 5, -6])
        self.assertEqual(root["rotation"], [125, 0, 0])
        faces = []
        for bone in geometry["bones"]:
            for cube in bone.get("cubes", []):
                faces.extend(cube.get("uv", {}).values())
        self.assertEqual(len(faces), 168)
        self.assertTrue(all(len(face["uv"]) == 2 and len(face["uv_size"]) == 2 for face in faces))
        self.assertTrue(all(value >= 0 for face in faces for value in face["uv_size"]))

    def test_trophy_edge_icon_is_an_isolated_alpha_sprite(self):
        path = self.rp / "textures/aionbound/trophy_edge.png"
        with Image.open(path) as image:
            self.assertEqual(image.size, (64, 64))
            self.assertEqual(image.mode, "RGBA")
            alpha = image.getchannel("A")
            self.assertEqual([alpha.getpixel(p) for p in [(0, 0), (63, 0), (0, 63), (63, 63)]], [0, 0, 0, 0])
            visible = sum(alpha.histogram()[1:])
            self.assertGreater(visible, 64)
            self.assertLess(visible, 64 * 64 * 0.65)
        self.assertNotEqual(path.read_bytes(), (self.rp / "textures/aionbound/trophy_edge_assembled.png").read_bytes())

    def test_char_wolf_is_path_only_ab_probe(self):
        old = self.rp / "models/aionbound/ashen/entities/char_wolf.geo.json"
        new = self.rp / "models/entity/aionbound/ashen/char_wolf.geo.json"
        control = self.rp / "models/aionbound/ashen/entities/cinder_lynx.geo.json"
        self.assertFalse(old.exists())
        self.assertTrue(control.is_file())
        self.assertEqual(new.read_bytes(), (ROOT / "resource_pack/models/aionbound/ashen/entities/char_wolf.geo.json").read_bytes())

        shipped = json.loads(new.read_text())
        native = json.loads((ROOT / "engineering/native-assets/ashen/creatures/evidence/char_wolf/native-exports/pass-2.geo.json").read_text())
        self.assertEqual(shipped, native)
        negative_sizes = 0
        for bone in json.loads(new.read_text())["minecraft:geometry"][0]["bones"]:
            for cube in bone.get("cubes", []):
                for face in cube.get("uv", {}).values():
                    negative_sizes += any(value < 0 for value in face.get("uv_size", []))
        self.assertGreater(negative_sizes, 0, "native Blockbench mirroring evidence must not be silently normalized")

    def test_changed_geometry_identifiers_resolve_once(self):
        identifiers = {}
        for path in self.rp.rglob("*.geo.json"):
            document = json.loads(path.read_text())
            for geometry in document.get("minecraft:geometry", []):
                identifier = geometry["description"]["identifier"]
                identifiers.setdefault(identifier, []).append(path)
        for identifier in ["geometry.aionbound.char_wolf", "geometry.aionbound.trophy_edge_assembled"]:
            self.assertEqual(len(identifiers[identifier]), 1, identifier)

        client = json.loads((self.rp / "entity/aionbound/ashen/char_wolf.entity.json").read_text())
        self.assertEqual(
            client["minecraft:client_entity"]["description"]["geometry"]["default"],
            "geometry.aionbound.char_wolf",
        )

    def test_archives_are_complete_and_deterministic(self):
        with tempfile.TemporaryDirectory() as second:
            second_receipt = BUILDER.build(Path(second) / "out")
        self.assertEqual(self.receipt["artifacts"], second_receipt["artifacts"])
        addon = self.output / "aionbound-wave1-g8-client-visual-r1.mcaddon"
        with zipfile.ZipFile(addon) as archive:
            self.assertEqual(
                archive.namelist(),
                [
                    "aionbound-wave1-g8-client-visual-r1-behavior.mcpack",
                    "aionbound-wave1-g8-client-visual-r1-resources.mcpack",
                ],
            )


if __name__ == "__main__":
    unittest.main()
