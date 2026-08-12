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
BUILDER = HERE / "build_skyreach_entity_runtime.py"
REPORT = HERE / "SKYREACH_ENTITY_RUNTIME_REPORT.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_builder():
    spec = importlib.util.spec_from_file_location("skyreach_entity_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, image, width, height = 8, bytearray(), None, None
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        crc = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        assert zlib.crc32(kind + payload) & 0xFFFFFFFF == crc
        pos += 12 + length
        if kind == b"IHDR":
            width, height = struct.unpack(">II", payload[:8])
        elif kind == b"IDAT":
            image.extend(payload)
        elif kind == b"IEND":
            break
    assert width and height and zlib.decompress(bytes(image))
    return width, height


class SkyreachEntityRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_builder()
        cls.report = read_json(REPORT)

    def test_exact_base_completed_and_withheld_rosters(self):
        self.assertEqual(self.report["base"], {"commit": "10e60dfb4ae95996286d455473612b58c234ec9b", "tree": "57088d0df2e3ccdf4a8e463ee09d3d6fbe7bd4bf"})
        self.assertEqual(self.report["completed"], ["cloud_goat", "gale_hawk", "wind_roc"])
        self.assertEqual([row["asset"] for row in self.report["withheld"]], self.builder.WITHHELD)
        self.assertTrue(all(not row["runtime_created"] for row in self.report["withheld"]))

    def test_native_qualified_bytes_are_exact(self):
        for row in self.report["native_bindings"]:
            asset = row["asset"]
            self.assertEqual(row["native_status"], "PASS_NATIVE_REPAIR_GATE")
            targets = {
                "geometry": ROOT / f"resource_pack/models/aionbound/skyreach/{asset}.geo.json",
                "animation": ROOT / f"resource_pack/animations/aionbound/skyreach/{asset}.animation.json",
                "texture": ROOT / f"resource_pack/textures/aionbound/skyreach/entity/{asset}.png",
            }
            for kind, target in targets.items():
                source = ROOT / row[f"{kind}_source_path"]
                self.assertEqual(source.read_bytes(), target.read_bytes())
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), row[f"{kind}_sha256"])
            self.assertEqual(png_dimensions(targets["texture"]), (32, 32))

    def test_geometry_animation_client_controller_render_closure(self):
        for asset in self.builder.ASSETS:
            geometry = read_json(ROOT / f"resource_pack/models/aionbound/skyreach/{asset}.geo.json")["minecraft:geometry"][0]
            self.assertEqual(geometry["description"]["identifier"], f"geometry.aionbound.{asset}")
            bones = {bone["name"] for bone in geometry["bones"]}
            self.assertTrue(all(not bone.get("parent") or bone["parent"] in bones for bone in geometry["bones"]))
            clips = read_json(ROOT / f"resource_pack/animations/aionbound/skyreach/{asset}.animation.json")["animations"]
            self.assertTrue(all(set(clip.get("bones", {})) <= bones for clip in clips.values()))
            client = read_json(ROOT / f"resource_pack/entity/aionbound/skyreach/{asset}.entity.json")["minecraft:client_entity"]["description"]
            self.assertEqual(client["geometry"]["default"], f"geometry.aionbound.{asset}")
            self.assertEqual(set(client["animations"].values()) - {f"controller.animation.aionbound.skyreach.{asset}.runtime"}, set(clips))
            controller = read_json(ROOT / f"resource_pack/animation_controllers/aionbound/skyreach/{asset}.animation_controller.json")["animation_controllers"]
            self.assertIn(client["animations"]["runtime"], controller)
            render = read_json(ROOT / f"resource_pack/render_controllers/aionbound/skyreach/{asset}.render_controller.json")["render_controllers"]
            self.assertIn(client["render_controllers"][0], render)

    def test_role_correct_non_statue_ai(self):
        cloud = read_json(ROOT / "behavior_pack/entities/aionbound/skyreach/cloud_goat.entity.json")["minecraft:entity"]
        self.assertIn("minecraft:navigation.walk", cloud["components"])
        self.assertIn("minecraft:behavior.random_stroll", cloud["components"])
        self.assertIn("minecraft:behavior.hurt_by_target", cloud["components"])
        self.assertNotIn("minecraft:behavior.nearest_attackable_target", cloud["components"])
        for asset in ("gale_hawk", "wind_roc"):
            components = read_json(ROOT / f"behavior_pack/entities/aionbound/skyreach/{asset}.entity.json")["minecraft:entity"]["components"]
            self.assertIn("minecraft:navigation.fly", components)
            self.assertIn("minecraft:behavior.random_fly", components)
            self.assertIn("minecraft:behavior.nearest_attackable_target", components)
            self.assertIn("minecraft:behavior.melee_attack", components)

    def test_only_two_console_bounded_natural_spawn_rules(self):
        files = sorted((ROOT / "behavior_pack/spawn_rules/aionbound/skyreach").glob("*.spawn_rules.json"))
        self.assertEqual([p.name for p in files], ["cloud_goat.spawn_rules.json", "gale_hawk.spawn_rules.json"])
        for path in files:
            condition = read_json(path)["minecraft:spawn_rules"]["conditions"][0]
            self.assertLessEqual(condition["minecraft:herd"]["max_size"], 2)
            self.assertLessEqual(condition["minecraft:density_limit"]["surface"], 2)
            self.assertLessEqual(condition["minecraft:weight"]["default"], 2)
            self.assertGreaterEqual(condition["minecraft:distance_filter"]["min"], 40)
            text = json.dumps(condition["minecraft:biome_filter"])
            self.assertIn("mountain", text)
            self.assertNotIn("forest", text)
            self.assertNotIn("swamp", text)

    def test_wind_roc_is_arena_only_without_deferred_semantics(self):
        path = ROOT / "behavior_pack/entities/aionbound/skyreach/wind_roc.entity.json"
        entity = read_json(path)["minecraft:entity"]
        self.assertFalse(entity["description"]["is_spawnable"])
        self.assertFalse((ROOT / "behavior_pack/spawn_rules/aionbound/skyreach/wind_roc.spawn_rules.json").exists())
        self.assertIn("arena_only_shell", entity["components"]["minecraft:type_family"]["family"])
        raw = path.read_text(encoding="utf-8")
        for forbidden in ("storm_nest", "terminal", "reward", "seal", "completion", "entitlement"):
            self.assertNotIn(forbidden, raw)

    def test_no_dangling_or_invented_loot_bindings(self):
        for asset in self.builder.ASSETS:
            components = read_json(ROOT / f"behavior_pack/entities/aionbound/skyreach/{asset}.entity.json")["minecraft:entity"]["components"]
            self.assertNotIn("minecraft:loot", components)
        self.assertEqual(self.report["loot_binding"], "OMITTED_NO_SKYREACH_CREATURE_LOOT_TABLES_ON_EXACT_BASE")

    def test_audio_pointers_and_localization_deferral(self):
        sounds = read_json(ROOT / "resource_pack/sounds.json")["entity_sounds"]["entities"]
        for asset, cfg in self.builder.ASSETS.items():
            self.assertIn(f"aionbound:{asset}", sounds)
        self.assertEqual(self.report["localization_binding"], "DEFERRED_TO_SHARED_CLOSURE_REFRESH")

    def test_report_hashes_json_and_determinism(self):
        listed = {row["path"]: row["sha256"] for row in self.report["outputs"]}
        self.assertEqual(len(listed), 24)
        for path, digest in listed.items():
            target = ROOT / path
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), digest)
            if path.endswith(".json"):
                read_json(target)
        with tempfile.TemporaryDirectory() as folder:
            one, two = Path(folder) / "one.json", Path(folder) / "two.json"
            for report in (one, two):
                subprocess.run(["python3", str(BUILDER), "--report", str(report)], cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            self.assertEqual(one.read_bytes(), REPORT.read_bytes())

    def test_proof_boundaries(self):
        boundary = self.report["proof_boundary"]
        self.assertEqual(boundary["storm_nest_terminal_reward_seal"], "NOT_IMPLEMENTED_DEFERRED_AUTHORITY")
        for key in ("build", "bds", "client", "multiplayer", "console_ps4", "release"):
            self.assertEqual(boundary[key], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
