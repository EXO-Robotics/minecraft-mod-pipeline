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

    def test_exact_base_and_complete_native_roster(self):
        self.assertEqual(self.report["base"], {"commit": "654d20ff9fd45d8bc7f2400ea35248e84d82b07b", "tree": "69ac4899f44d598da0bb939b710c4453c947ce37"})
        self.assertEqual(self.report["schema"], "aionbound.wave1.skyreach_entity_runtime.v2")
        self.assertEqual(self.report["status"], "SKYREACH_TEN_NATIVE_CREATURES_STATIC_RUNTIME_COMPLETE")
        self.assertEqual(self.report["completed"], sorted(self.builder.ASSETS))
        self.assertEqual(self.report["withheld"], [])

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
        for asset in ("cloud_goat", "cliff_ram", "sky_fox"):
            components = read_json(ROOT / f"behavior_pack/entities/aionbound/skyreach/{asset}.entity.json")["minecraft:entity"]["components"]
            self.assertIn("minecraft:navigation.walk", components)
            self.assertIn("minecraft:behavior.random_stroll", components)
            self.assertIn("minecraft:behavior.hurt_by_target", components)
            self.assertNotIn("minecraft:behavior.nearest_attackable_target", components)
        for asset in ("gale_hawk", "wind_roc", "glide_drake", "ropewing", "ruin_harpy", "stone_vulture", "storm_gull"):
            components = read_json(ROOT / f"behavior_pack/entities/aionbound/skyreach/{asset}.entity.json")["minecraft:entity"]["components"]
            self.assertIn("minecraft:navigation.fly", components)
            self.assertIn("minecraft:behavior.random_fly", components)
            self.assertIn("minecraft:behavior.melee_attack", components)
        for asset in ("gale_hawk", "wind_roc", "glide_drake", "ruin_harpy"):
            components = read_json(ROOT / f"behavior_pack/entities/aionbound/skyreach/{asset}.entity.json")["minecraft:entity"]["components"]
            self.assertIn("minecraft:behavior.nearest_attackable_target", components)
        for asset in ("ropewing", "stone_vulture", "storm_gull"):
            components = read_json(ROOT / f"behavior_pack/entities/aionbound/skyreach/{asset}.entity.json")["minecraft:entity"]["components"]
            self.assertNotIn("minecraft:behavior.nearest_attackable_target", components)

    def test_nine_console_bounded_mountain_hills_spawn_rules(self):
        files = sorted((ROOT / "behavior_pack/spawn_rules/aionbound/skyreach").glob("*.spawn_rules.json"))
        expected = sorted(f"{asset}.spawn_rules.json" for asset, cfg in self.builder.ASSETS.items() if cfg["natural"])
        self.assertEqual([p.name for p in files], expected)
        self.assertEqual(len(files), 9)
        for path in files:
            condition = read_json(path)["minecraft:spawn_rules"]["conditions"][0]
            self.assertLessEqual(condition["minecraft:herd"]["max_size"], 2)
            self.assertLessEqual(condition["minecraft:density_limit"]["surface"], 2)
            self.assertLessEqual(condition["minecraft:weight"]["default"], 2)
            self.assertGreaterEqual(condition["minecraft:distance_filter"]["min"], 40)
            text = json.dumps(condition["minecraft:biome_filter"])
            self.assertIn("mountain", text)
            self.assertIn("hills", text)
            self.assertNotIn("forest", text)
            self.assertNotIn("swamp", text)
        self.assertEqual(self.report["ecology"]["aggregate_surface_density_ceiling"], 12)

    def test_wind_roc_is_arena_only_without_deferred_semantics(self):
        path = ROOT / "behavior_pack/entities/aionbound/skyreach/wind_roc.entity.json"
        entity = read_json(path)["minecraft:entity"]
        self.assertFalse(entity["description"]["is_spawnable"])
        self.assertFalse((ROOT / "behavior_pack/spawn_rules/aionbound/skyreach/wind_roc.spawn_rules.json").exists())
        self.assertIn("arena_only_shell", entity["components"]["minecraft:type_family"]["family"])
        raw = path.read_text(encoding="utf-8")
        for forbidden in ("storm_nest", "terminal", "reward", "seal", "completion", "entitlement"):
            self.assertNotIn(forbidden, raw)

    def test_current_ratified_loot_bindings_are_closed(self):
        for asset in self.builder.ASSETS:
            components = read_json(ROOT / f"behavior_pack/entities/aionbound/skyreach/{asset}.entity.json")["minecraft:entity"]["components"]
            table = components.get("minecraft:loot", {}).get("table")
            self.assertEqual(f"loot_tables/entities/aionbound/skyreach/{asset}.json", table)
            self.assertTrue((ROOT / "behavior_pack" / table).is_file())
        self.assertEqual(self.report["loot_binding"], "OMITTED_NO_SKYREACH_CREATURE_LOOT_TABLES_ON_EXACT_BASE")

    def test_noncombat_scavenger_clips_are_not_misbound_to_targets(self):
        for asset, forbidden_clip in (("stone_vulture", "feed_pose"), ("storm_gull", "land")):
            controller = read_json(ROOT / f"resource_pack/animation_controllers/aionbound/skyreach/{asset}.animation_controller.json")
            self.assertNotIn(forbidden_clip, json.dumps(controller))
            client = read_json(ROOT / f"resource_pack/entity/aionbound/skyreach/{asset}.entity.json")["minecraft:client_entity"]["description"]
            self.assertIn(forbidden_clip, client["animations"])

    def test_authority_gated_surfaces_are_absent(self):
        forbidden = ("storm_nest", "seal", "reward_cache", "codex_terminal", "entitlement", "completion")
        for asset in self.builder.ASSETS:
            paths = [
                ROOT / f"behavior_pack/entities/aionbound/skyreach/{asset}.entity.json",
                ROOT / f"resource_pack/entity/aionbound/skyreach/{asset}.entity.json",
                ROOT / f"resource_pack/animation_controllers/aionbound/skyreach/{asset}.animation_controller.json",
            ]
            for path in paths:
                raw = path.read_text(encoding="utf-8")
                for token in forbidden:
                    self.assertNotIn(token, raw)

    def test_audio_pointers_and_localization_deferral(self):
        sounds = read_json(ROOT / "resource_pack/sounds.json")["entity_sounds"]["entities"]
        for asset, cfg in self.builder.ASSETS.items():
            self.assertIn(f"aionbound:{asset}", sounds)
        self.assertEqual(self.report["localization_binding"], "DEFERRED_TO_SHARED_CLOSURE_REFRESH")

    def test_report_hashes_json_and_determinism(self):
        listed = {row["path"]: row["sha256"] for row in self.report["outputs"]}
        self.assertEqual(len(listed), 80)
        for path, digest in listed.items():
            target = ROOT / path
            if path.startswith("behavior_pack/entities/aionbound/skyreach/"):
                # The historical runtime report predates exact ratified loot
                # composition. Remove only that later component before
                # comparing the generator's canonical JSON bytes.
                current = read_json(target)
                current["minecraft:entity"]["components"].pop("minecraft:loot", None)
                historical = self.builder.behavior_entity(Path(path).name.split(".", 1)[0], self.builder.ASSETS[Path(path).name.split(".", 1)[0]])
                self.assertEqual(historical, current)
            else:
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), digest)
            if path.endswith(".json"):
                read_json(target)
        # Do not replay the historical product author against a successor tree:
        # it predates the ratified loot component and would remove it. Its pure
        # per-entity generator is compared above instead.

    def test_bundled_cross_file_validator_passes_all_ten(self):
        validator = Path("/Users/blakegrove/.codex/skills/blockbench-build-bedrock-assets/scripts/validate_animated_entity.py")
        for asset in self.builder.ASSETS:
            with self.subTest(asset=asset):
                result = subprocess.run([
                    "python3", str(validator),
                    "--geometry", str(ROOT / f"resource_pack/models/aionbound/skyreach/{asset}.geo.json"),
                    "--animations", str(ROOT / f"resource_pack/animations/aionbound/skyreach/{asset}.animation.json"),
                    "--controller", str(ROOT / f"resource_pack/animation_controllers/aionbound/skyreach/{asset}.animation_controller.json"),
                    "--client-entity", str(ROOT / f"resource_pack/entity/aionbound/skyreach/{asset}.entity.json"),
                    "--behavior-entity", str(ROOT / f"behavior_pack/entities/aionbound/skyreach/{asset}.entity.json"),
                ], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("OK:", result.stdout)

    def test_proof_boundaries(self):
        boundary = self.report["proof_boundary"]
        self.assertEqual(boundary["storm_nest_terminal_reward_seal"], "NOT_IMPLEMENTED_DEFERRED_AUTHORITY")
        for key in ("build", "bds", "client", "multiplayer", "console_ps4", "release"):
            self.assertEqual(boundary[key], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
