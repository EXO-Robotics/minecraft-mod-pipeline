from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REPORT = HERE / "ASHEN_ENTITY_RUNTIME_REPORT.json"
BUILDER = HERE / "build_ashen_entity_runtime.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("ashen_entity_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_png(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, width, height, bit_depth, color_type = 8, bytearray(), None, None, None, None
    saw_iend = False
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        crc = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        assert (zlib.crc32(kind + payload) & 0xFFFFFFFF) == crc
        pos += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            assert width > 0 and height > 0 and compression == 0 and filtering == 0 and interlace == 0
        elif kind == b"IDAT": idat.extend(payload)
        elif kind == b"IEND": saw_iend = True; break
    assert saw_iend and width and height and bit_depth == 8
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    decoded = zlib.decompress(bytes(idat))
    assert len(decoded) == height * (1 + width * channels)
    assert all(decoded[row * (1 + width * channels)] <= 4 for row in range(height))
    return width, height


class AshenEntityRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_builder()
        cls.report = read_json(REPORT)

    def test_exact_base_and_roster(self):
        self.assertEqual(self.report["base"], {"commit": "d3f162db41b06ce502dd8fc6995288d2fe546fa0", "tree": "4843a3ad877cec4ecdd238d01867218ef9687741"})
        self.assertEqual(set(self.report["scope"]["entities"]), set(self.builder.ASSETS))
        self.assertEqual(len(self.report["scope"]["entities"]), 10)
        self.assertEqual(len(self.report["scope"]["natural_spawn_entities"]), 9)

    def test_exact_native_geometry_animation_and_texture_bytes(self):
        for row in self.report["native_binding"]:
            asset = row["asset"]
            targets = {
                "geometry": ROOT / f"resource_pack/models/aionbound/ashen/entities/{asset}.geo.json",
                "animation": ROOT / f"resource_pack/animations/aionbound/ashen/entities/{asset}.animation.json",
                "texture": ROOT / f"resource_pack/textures/aionbound/ashen/entity/{asset}.png",
            }
            for kind, target in targets.items():
                source = ROOT / row[f"{kind}_path"]
                self.assertEqual(target.read_bytes(), source.read_bytes())
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), row[f"{kind}_sha256"])
            self.assertEqual(validate_png(targets["texture"]), (32, 32))

    def test_geometry_animation_bone_and_identifier_closure(self):
        for asset in self.builder.ASSETS:
            geo = read_json(ROOT / f"resource_pack/models/aionbound/ashen/entities/{asset}.geo.json")["minecraft:geometry"][0]
            self.assertEqual(geo["description"]["identifier"], f"geometry.aionbound.{asset}")
            bones = {b["name"] for b in geo["bones"]}
            self.assertTrue(all(not b.get("parent") or b["parent"] in bones for b in geo["bones"]))
            animations = read_json(ROOT / f"resource_pack/animations/aionbound/ashen/entities/{asset}.animation.json")["animations"]
            for clip in animations.values():
                self.assertTrue(set(clip.get("bones", {})) <= bones)

    def test_client_controller_render_reference_closure(self):
        for asset in self.builder.ASSETS:
            client = read_json(ROOT / f"resource_pack/entity/aionbound/ashen/{asset}.entity.json")["minecraft:client_entity"]["description"]
            self.assertEqual(client["identifier"], f"aionbound:{asset}")
            self.assertEqual(client["geometry"]["default"], f"geometry.aionbound.{asset}")
            clips = read_json(ROOT / f"resource_pack/animations/aionbound/ashen/entities/{asset}.animation.json")["animations"]
            self.assertEqual(set(client["animations"].values()) - {f"controller.animation.aionbound.ashen.{asset}.runtime"}, set(clips))
            controller = read_json(ROOT / f"resource_pack/animation_controllers/aionbound/ashen/{asset}.animation_controller.json")["animation_controllers"]
            self.assertIn(client["animations"]["runtime"], controller)
            aliases = set(client["animations"])
            for state in next(iter(controller.values()))["states"].values():
                for animation in state.get("animations", []):
                    if isinstance(animation, str): self.assertIn(animation, aliases)
                    else: self.assertTrue(set(animation) <= aliases)
            render = read_json(ROOT / f"resource_pack/render_controllers/aionbound/ashen/{asset}.render_controller.json")["render_controllers"]
            self.assertIn(client["render_controllers"][0], render)

    def test_behavior_entities_are_non_statue_and_bind_exact_ecology_loot(self):
        for asset, cfg in self.builder.ASSETS.items():
            entity = read_json(ROOT / f"behavior_pack/entities/aionbound/ashen/{asset}.entity.json")["minecraft:entity"]
            components = entity["components"]
            self.assertEqual(entity["description"]["identifier"], f"aionbound:{asset}")
            table = asset if asset != "ash_drake" else "ash_drake_ecology"
            self.assertEqual(components["minecraft:loot"]["table"], f"loot_tables/entities/ashen/{table}.json")
            self.assertTrue((ROOT / f"behavior_pack/loot_tables/entities/ashen/{table}.json").is_file())
            self.assertIn("minecraft:movement", components)
            if cfg["flying"]:
                self.assertIn("minecraft:navigation.fly", components)
                self.assertIn("minecraft:behavior.random_fly", components)
            else:
                self.assertIn("minecraft:navigation.walk", components)
                self.assertIn("minecraft:behavior.random_stroll", components)
            if cfg["hostile"]:
                self.assertIn("minecraft:behavior.nearest_attackable_target", components)
                self.assertIn("minecraft:behavior.melee_attack", components)
            if cfg["neutral"]:
                self.assertIn("minecraft:behavior.hurt_by_target", components)
                self.assertNotIn("minecraft:behavior.nearest_attackable_target", components)

    def test_ash_drake_is_arena_only_shell_without_kiln_semantics(self):
        path = ROOT / "behavior_pack/entities/aionbound/ashen/ash_drake.entity.json"
        entity = read_json(path)["minecraft:entity"]
        self.assertFalse(entity["description"]["is_spawnable"])
        self.assertFalse((ROOT / "behavior_pack/spawn_rules/aionbound/ashen/ash_drake.spawn_rules.json").exists())
        raw = path.read_text()
        for forbidden in ("kiln_sky", "completed", "reward", "ash_drake_horn", "seal_credit", "encounter_session"):
            self.assertNotIn(forbidden, raw)
        self.assertIn("arena_only_shell", entity["components"]["minecraft:type_family"]["family"])

    def test_nine_distinct_console_bounded_spawn_rules(self):
        signatures = set()
        spawn_root = ROOT / "behavior_pack/spawn_rules/aionbound/ashen"
        files = sorted(spawn_root.glob("*.spawn_rules.json"))
        self.assertEqual(len(files), 9)
        for path in files:
            rule = read_json(path)["minecraft:spawn_rules"]
            self.assertNotEqual(rule["description"]["identifier"], "aionbound:ash_drake")
            condition = rule["conditions"][0]
            self.assertLessEqual(condition["minecraft:herd"]["max_size"], 2)
            self.assertLessEqual(condition["minecraft:density_limit"]["surface"], 2)
            self.assertLessEqual(condition["minecraft:weight"]["default"], 6)
            text = json.dumps(condition["minecraft:biome_filter"])
            self.assertIn("overworld", text)
            self.assertTrue("mountain" in text or "mesa" in text)
            self.assertNotIn("forest", text)
            signatures.add((condition["minecraft:weight"]["default"], condition["minecraft:herd"]["max_size"], condition["minecraft:density_limit"]["surface"], condition["minecraft:brightness_filter"]["min"], condition["minecraft:brightness_filter"]["max"], text))
        self.assertEqual(len(signatures), 9)

    def test_report_output_hashes_and_scope(self):
        listed = {row["path"]: row["sha256"] for row in self.report["outputs"]}
        self.assertEqual(len(listed), 79)
        for path, digest in listed.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)
        self.assertEqual(self.report["proof_boundary"]["build"], "NOT_RUN")
        self.assertEqual(self.report["proof_boundary"]["bds"], "NOT_RUN")
        self.assertEqual(self.report["proof_boundary"]["bedrock_client"], "NOT_RUN")

    def test_all_new_json_parses(self):
        for row in self.report["outputs"]:
            if row["path"].endswith(".json"):
                read_json(ROOT / row["path"])

    def test_generator_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as folder:
            one, two = Path(folder) / "one.json", Path(folder) / "two.json"
            for report in (one, two):
                subprocess.run(["python3", str(BUILDER), "--report", str(report)], cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            self.assertEqual(one.read_bytes(), REPORT.read_bytes())


if __name__ == "__main__":
    unittest.main()
