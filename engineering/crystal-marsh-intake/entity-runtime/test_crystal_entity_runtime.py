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
REPORT = HERE / "CRYSTAL_MARSH_ENTITY_RUNTIME_REPORT.json"
BUILDER = HERE / "build_crystal_entity_runtime.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("crystal_entity_builder", BUILDER)
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
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            saw_iend = True
            break
    assert saw_iend and width and height and bit_depth == 8
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    decoded = zlib.decompress(bytes(idat))
    assert len(decoded) == height * (1 + width * channels)
    assert all(decoded[row * (1 + width * channels)] <= 4 for row in range(height))
    return width, height


class CrystalEntityRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_builder()
        cls.report = read_json(REPORT)

    def test_exact_base_authority_and_roster(self):
        self.assertEqual(self.report["base"], {"commit": "6a10cd8a82635299ae62ab8f6b9095c9b793c7a3", "tree": "689fa214ae21ab9739a8b6710fdbb5bb00ebeaeb"})
        self.assertEqual(set(self.report["scope"]["entities"]), set(self.builder.ASSETS))
        self.assertEqual(len(self.report["scope"]["entities"]), 10)
        self.assertEqual(len(self.report["scope"]["natural_spawn_entities"]), 9)
        self.assertEqual(self.report["authority"]["W1-CREATIVE-005"], "DEFERRED_UNCHANGED")

    def test_exact_native_pass_two_geometry_animation_and_texture_bytes(self):
        for row in self.report["native_binding"]:
            asset = row["asset"]
            self.assertEqual(row["receipt_status"], "PASS_NATIVE_REPAIR_GATE")
            targets = {
                "geometry": ROOT / f"resource_pack/models/aionbound/crystal_marsh/entities/{asset}.geo.json",
                "animation": ROOT / f"resource_pack/animations/aionbound/crystal_marsh/entities/{asset}.animation.json",
                "texture": ROOT / f"resource_pack/textures/aionbound/crystal_marsh/entity/{asset}.png",
            }
            for kind, target in targets.items():
                source = ROOT / row[f"{kind}_path"]
                self.assertEqual(target.read_bytes(), source.read_bytes())
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), row[f"{kind}_sha256"])
            width, height = validate_png(targets["texture"])
            self.assertGreater(width, 0)
            self.assertGreater(height, 0)

    def test_geometry_animation_bone_and_identifier_closure(self):
        for asset in self.builder.ASSETS:
            geometry = read_json(ROOT / f"resource_pack/models/aionbound/crystal_marsh/entities/{asset}.geo.json")["minecraft:geometry"][0]
            self.assertEqual(geometry["description"]["identifier"], f"geometry.aionbound.{asset}")
            bones = {bone["name"] for bone in geometry["bones"]}
            self.assertTrue(all(not bone.get("parent") or bone["parent"] in bones for bone in geometry["bones"]))
            animations = read_json(ROOT / f"resource_pack/animations/aionbound/crystal_marsh/entities/{asset}.animation.json")["animations"]
            for clip in animations.values():
                self.assertTrue(set(clip.get("bones", {})) <= bones)

    def test_client_controller_render_reference_closure(self):
        for asset in self.builder.ASSETS:
            client = read_json(ROOT / f"resource_pack/entity/aionbound/crystal_marsh/{asset}.entity.json")["minecraft:client_entity"]["description"]
            self.assertEqual(client["identifier"], f"aionbound:{asset}")
            self.assertEqual(client["geometry"]["default"], f"geometry.aionbound.{asset}")
            clips = read_json(ROOT / f"resource_pack/animations/aionbound/crystal_marsh/entities/{asset}.animation.json")["animations"]
            runtime = f"controller.animation.aionbound.crystal_marsh.{asset}.runtime"
            self.assertEqual(set(client["animations"].values()) - {runtime}, set(clips))
            controller = read_json(ROOT / f"resource_pack/animation_controllers/aionbound/crystal_marsh/{asset}.animation_controller.json")["animation_controllers"]
            self.assertIn(runtime, controller)
            aliases = set(client["animations"])
            for state in controller[runtime]["states"].values():
                for animation in state.get("animations", []):
                    if isinstance(animation, str):
                        self.assertIn(animation, aliases)
                    else:
                        self.assertTrue(set(animation) <= aliases)
            render = read_json(ROOT / f"resource_pack/render_controllers/aionbound/crystal_marsh/{asset}.render_controller.json")["render_controllers"]
            self.assertIn(client["render_controllers"][0], render)

    def test_behavior_entities_have_role_specific_non_statue_ai(self):
        for asset, cfg in self.builder.ASSETS.items():
            entity = read_json(ROOT / f"behavior_pack/entities/aionbound/crystal_marsh/{asset}.entity.json")["minecraft:entity"]
            components = entity["components"]
            self.assertEqual(entity["description"]["identifier"], f"aionbound:{asset}")
            self.assertIn("minecraft:movement", components)
            self.assertNotIn("minecraft:loot", components)
            if cfg["locomotion"] == "flying":
                self.assertIn("minecraft:navigation.fly", components)
                self.assertIn("minecraft:behavior.random_fly", components)
            elif cfg["locomotion"] == "aquatic":
                self.assertIn("minecraft:navigation.swim", components)
                self.assertIn("minecraft:behavior.random_swim", components)
                self.assertFalse(components["minecraft:physics"]["has_gravity"])
                self.assertTrue(components["minecraft:navigation.swim"]["can_swim"])
            elif cfg["locomotion"] == "amphibious":
                self.assertIn("minecraft:navigation.generic", components)
                self.assertIn("minecraft:behavior.random_stroll", components)
                self.assertTrue(components["minecraft:navigation.generic"]["is_amphibious"])
                self.assertFalse(components["minecraft:navigation.generic"]["can_sink"])
            else:
                self.assertIn("minecraft:navigation.walk", components)
                self.assertIn("minecraft:behavior.random_stroll", components)
            if cfg["hostile"]:
                self.assertIn("minecraft:behavior.nearest_attackable_target", components)
                self.assertIn("minecraft:behavior.melee_attack", components)
            elif cfg["neutral"]:
                self.assertIn("minecraft:behavior.hurt_by_target", components)
                self.assertIn("minecraft:behavior.melee_attack", components)
                self.assertNotIn("minecraft:behavior.nearest_attackable_target", components)
            else:
                self.assertIn("minecraft:behavior.panic", components)

    def test_loot_is_a_recorded_nondangling_integration_dependency(self):
        binding = self.report["loot_binding"]
        self.assertEqual(binding["minecraft_loot_components_authored"], 0)
        self.assertEqual(set(binding["dependencies"]), set(self.builder.ASSETS))
        self.assertEqual(binding["expected_table_paths"], {asset: f"behavior_pack/loot_tables/entities/crystal/{asset}.json" for asset in sorted(self.builder.ASSETS)})
        for asset in self.builder.ASSETS:
            components = read_json(ROOT / f"behavior_pack/entities/aionbound/crystal_marsh/{asset}.entity.json")["minecraft:entity"]["components"]
            self.assertNotIn("minecraft:loot", components)

    def test_marsh_wight_is_arena_only_shell_without_seal_or_terminal_semantics(self):
        path = ROOT / "behavior_pack/entities/aionbound/crystal_marsh/marsh_wight.entity.json"
        entity = read_json(path)["minecraft:entity"]
        self.assertFalse(entity["description"]["is_spawnable"])
        self.assertFalse((ROOT / "behavior_pack/spawn_rules/aionbound/crystal_marsh/marsh_wight.spawn_rules.json").exists())
        self.assertIn("arena_only_shell", entity["components"]["minecraft:type_family"]["family"])
        self.assertNotIn("minecraft:loot", entity["components"])
        raw = path.read_text(encoding="utf-8")
        for forbidden in ("pearl_depths", "marsh_wight_mask", "seal_credit", "reward_entitled", "trophy_claimed", "encounter_session", "completed"):
            self.assertNotIn(forbidden, raw)

    def test_nine_distinct_console_bounded_wetland_spawn_rules(self):
        spawn_root = ROOT / "behavior_pack/spawn_rules/aionbound/crystal_marsh"
        files = sorted(spawn_root.glob("*.spawn_rules.json"))
        self.assertEqual(len(files), 9)
        signatures = set()
        underwater = set()
        for path in files:
            rule = read_json(path)["minecraft:spawn_rules"]
            self.assertNotEqual(rule["description"]["identifier"], "aionbound:marsh_wight")
            condition = rule["conditions"][0]
            self.assertLessEqual(condition["minecraft:herd"]["max_size"], 2)
            self.assertLessEqual(condition["minecraft:density_limit"]["surface"], 2)
            self.assertLessEqual(condition["minecraft:weight"]["default"], 5)
            self.assertEqual(condition["minecraft:distance_filter"], {"min": 32, "max": 88})
            biome_text = json.dumps(condition["minecraft:biome_filter"])
            self.assertIn("overworld", biome_text)
            self.assertTrue("swamp" in biome_text or "river" in biome_text)
            for copied_tag in ("forest", "mountain", "mesa"):
                self.assertNotIn(copied_tag, biome_text)
            placement = "underwater" if "minecraft:spawns_underwater" in condition else "surface"
            if placement == "underwater":
                underwater.add(rule["description"]["identifier"].split(":", 1)[1])
            signatures.add((condition["minecraft:weight"]["default"], condition["minecraft:herd"]["max_size"], condition["minecraft:density_limit"]["surface"], condition["minecraft:brightness_filter"]["min"], condition["minecraft:brightness_filter"]["max"], biome_text, placement))
        self.assertEqual(len(signatures), 9)
        self.assertEqual(underwater, {"reed_serpent", "silt_crocodile"})

    def test_vanilla_placeholder_audio_mappings_are_bounded(self):
        sounds = read_json(ROOT / "resource_pack/sounds.json")["entity_sounds"]["entities"]
        allowed = {"mob.rabbit.idle", "mob.rabbit.hurt", "mob.rabbit.death", "mob.pig.say", "mob.pig.death", "mob.spider.say", "mob.spider.death", "mob.ravager.ambient", "mob.ravager.hurt", "mob.ravager.death", "mob.vex.ambient", "mob.vex.hurt", "mob.vex.death"}
        for asset in self.builder.ASSETS:
            entry = sounds[f"aionbound:{asset}"]
            self.assertTrue(set(entry["events"].values()) <= allowed)
            self.assertGreater(entry["volume"], 0)
            self.assertLessEqual(entry["volume"], 1)

    def test_report_output_hashes_and_proof_boundaries(self):
        listed = {row["path"]: row["sha256"] for row in self.report["outputs"]}
        self.assertEqual(len(listed), 80)
        for path, digest in listed.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)
        self.assertEqual(self.report["proof_boundary"]["build"], "NOT_RUN")
        self.assertEqual(self.report["proof_boundary"]["bds"], "NOT_RUN")
        self.assertEqual(self.report["proof_boundary"]["bedrock_client"], "NOT_RUN")

    def test_all_authored_json_parses(self):
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
