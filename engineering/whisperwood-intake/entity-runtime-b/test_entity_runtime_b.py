#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
IDS = ("bark_wraith", "briar_elk", "hollow_widow_spider", "rot_wolf", "thorn_stalker")
EVIDENCE = ROOT / "engineering/native-assets/whisperwood/evidence"
EXPECTED_LOOT = {
    "bark_wraith": {
        "aionbound:whisper_bark", "aionbound:hollow_amber",
        "aionbound:moon_sap", "aionbound:ancient_acorn",
    },
    "briar_elk": {
        "aionbound:whisper_bark", "aionbound:briar_antler", "aionbound:ancient_acorn",
    },
    "hollow_widow_spider": {"aionbound:widow_silk", "aionbound:hollow_venom_sac"},
    "rot_wolf": {"aionbound:whisper_bark", "aionbound:widow_silk"},
    "thorn_stalker": {"aionbound:briar_vine", "aionbound:thorn_barb", "aionbound:stalker_claw"},
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_namespace(value, old, new):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [replace_namespace(item, old, new) for item in value]
    if isinstance(value, dict):
        return {
            key.replace(old, new): replace_namespace(item, old, new)
            for key, item in value.items()
        }
    return value


class EntityRuntimeBTest(unittest.TestCase):
    def test_native_evidence_and_shipping_derivation(self):
        for entity_id in IDS:
            with self.subTest(entity=entity_id):
                evidence = EVIDENCE / entity_id
                receipt = load(evidence / "entity-animation-native-receipt.json")
                self.assertEqual(receipt["status"], "PASS")
                self.assertEqual(
                    receipt["proof_scope"],
                    "BLOCKBENCH_NATIVE_ENTITY_ANIMATION_AUTHORING_AND_CODEC_EXPORT_ONLY",
                )

                source_geo = load(evidence / "native-exports/pass-1.geo.json")
                shipped_geo = load(ROOT / f"resource_pack/models/aionbound/whisperwood/{entity_id}.geo.json")
                self.assertEqual(
                    shipped_geo,
                    replace_namespace(source_geo, "geometry.aionforge_ww.", "geometry.aionbound."),
                )

                source_animation = load(evidence / "native-exports/pass-1.animation.json")
                shipped_animation = load(ROOT / f"resource_pack/animations/aionbound/whisperwood/{entity_id}.animation.json")
                self.assertEqual(
                    shipped_animation,
                    replace_namespace(source_animation, "animation.aionforge_ww.", "animation.aionbound."),
                )

                source_png = evidence / f"inputs/{entity_id}.source.png"
                shipped_png = ROOT / f"resource_pack/textures/aionbound/whisperwood/{entity_id}.png"
                self.assertEqual(digest(shipped_png), digest(source_png))

    def test_identifier_and_resource_reference_closure(self):
        for entity_id in IDS:
            with self.subTest(entity=entity_id):
                runtime_id = f"aionbound:{entity_id}"
                bp = load(ROOT / f"behavior_pack/entities/{entity_id}.entity.json")["minecraft:entity"]
                spawn = load(ROOT / f"behavior_pack/spawn_rules/{entity_id}.spawn_rules.json")["minecraft:spawn_rules"]
                client = load(ROOT / f"resource_pack/entity/{entity_id}.entity.json")["minecraft:client_entity"]["description"]
                geometry = load(ROOT / f"resource_pack/models/aionbound/whisperwood/{entity_id}.geo.json")
                animations = load(ROOT / f"resource_pack/animations/aionbound/whisperwood/{entity_id}.animation.json")["animations"]
                controller = load(ROOT / f"resource_pack/animation_controllers/aionbound/whisperwood/{entity_id}.animation_controller.json")["animation_controllers"]
                renderer = load(ROOT / f"resource_pack/render_controllers/aionbound/whisperwood/{entity_id}.render_controller.json")["render_controllers"]

                self.assertEqual(bp["description"]["identifier"], runtime_id)
                self.assertEqual(spawn["description"]["identifier"], runtime_id)
                self.assertEqual(client["identifier"], runtime_id)
                self.assertEqual(client["geometry"]["default"], f"geometry.aionbound.{entity_id}")
                self.assertIn(f"geometry.aionbound.{entity_id}", [entry["description"]["identifier"] for entry in geometry["minecraft:geometry"]])
                self.assertEqual(client["textures"]["default"], f"textures/aionbound/whisperwood/{entity_id}")
                self.assertTrue((ROOT / f"resource_pack/textures/aionbound/whisperwood/{entity_id}.png").is_file())
                self.assertIn(f"controller.animation.aionbound.{entity_id}.runtime", controller)
                self.assertIn(f"controller.render.aionbound.{entity_id}", renderer)
                for key, target in client["animations"].items():
                    if key == "runtime":
                        self.assertIn(target, controller)
                    else:
                        self.assertIn(target, animations)

                runtime = controller[f"controller.animation.aionbound.{entity_id}.runtime"]
                states = runtime["states"]
                self.assertIn(runtime["initial_state"], states)
                for state in states.values():
                    for alias in state.get("animations", []):
                        self.assertIn(alias, client["animations"])
                    for transition in state.get("transitions", []):
                        self.assertEqual(len(transition), 1)
                        self.assertIn(next(iter(transition)), states)

    def test_non_statue_ai_components(self):
        for entity_id in IDS:
            with self.subTest(entity=entity_id):
                components = load(ROOT / f"behavior_pack/entities/{entity_id}.entity.json")["minecraft:entity"]["components"]
                self.assertIn("minecraft:movement", components)
                self.assertTrue(any(name.startswith("minecraft:navigation.") for name in components))
                self.assertIn("minecraft:behavior.hurt_by_target", components)
                self.assertIn("minecraft:behavior.melee_attack", components)
                self.assertIn("minecraft:behavior.random_stroll", components) if entity_id != "bark_wraith" else self.assertIn("minecraft:behavior.random_fly", components)
                if entity_id != "briar_elk":
                    self.assertIn("minecraft:behavior.nearest_attackable_target", components)
                else:
                    self.assertNotIn("minecraft:behavior.nearest_attackable_target", components)

        spider = load(ROOT / "behavior_pack/entities/hollow_widow_spider.entity.json")["minecraft:entity"]["components"]
        self.assertIn("minecraft:can_climb", spider)
        self.assertIn("minecraft:navigation.climb", spider)
        wraith = load(ROOT / "behavior_pack/entities/bark_wraith.entity.json")["minecraft:entity"]["components"]
        self.assertIn("minecraft:can_fly", wraith)
        self.assertIn("minecraft:navigation.fly", wraith)
        wolf = load(ROOT / "behavior_pack/entities/rot_wolf.entity.json")["minecraft:entity"]["components"]
        self.assertTrue(wolf["minecraft:behavior.hurt_by_target"]["alert_same_type"])

    def test_conservative_ecology_bounds(self):
        for entity_id in IDS:
            spawn = load(ROOT / f"behavior_pack/spawn_rules/{entity_id}.spawn_rules.json")["minecraft:spawn_rules"]
            self.assertEqual(len(spawn["conditions"]), 1)
            condition = spawn["conditions"][0]
            self.assertLessEqual(condition["minecraft:weight"]["default"], 3)
            self.assertLessEqual(condition["minecraft:herd"]["max_size"], 3)
        self.assertEqual(
            load(ROOT / "behavior_pack/spawn_rules/thorn_stalker.spawn_rules.json")["minecraft:spawn_rules"]["conditions"][0]["minecraft:weight"]["default"],
            1,
        )

    def test_animation_controller_queries_use_reviewed_stable_set(self):
        approved = {
            "query.any_animation_finished",
            "query.has_target",
            "query.hurt_time",
            "query.is_alive",
            "query.is_moving",
            "query.modified_move_speed",
        }
        for entity_id in IDS:
            path = ROOT / f"resource_pack/animation_controllers/aionbound/whisperwood/{entity_id}.animation_controller.json"
            used = set(re.findall(r"query\.[a-z_]+", path.read_text(encoding="utf-8")))
            self.assertTrue(used)
            self.assertTrue(used.issubset(approved), f"{entity_id}: unsupported query set {sorted(used - approved)}")

    def test_ratified_natural_loot_is_bound_and_seal_free(self):
        for entity_id in IDS:
            components = load(ROOT / f"behavior_pack/entities/{entity_id}.entity.json")["minecraft:entity"]["components"]
            expected_table = f"loot_tables/entities/{entity_id}.json"
            self.assertEqual({"table": expected_table}, components["minecraft:loot"])
            loot_path = ROOT / "behavior_pack" / expected_table
            self.assertTrue(loot_path.is_file())
            loot = load(loot_path)
            self.assertEqual(
                EXPECTED_LOOT[entity_id],
                {entry["name"] for pool in loot["pools"] for entry in pool["entries"]},
            )
            self.assertNotIn("aionbound:thorn_stalker_skull", json.dumps(loot))

    def test_thorn_stalker_is_machine_readable_base_shell_only(self):
        status = load(ROOT / "engineering/whisperwood-intake/entity-runtime-b/WHISPERWOOD_ENTITY_RUNTIME_B_STATUS.json")
        stalker = status["entities"]["thorn_stalker"]
        self.assertEqual(stalker["classification"], "BASE_HOSTILE_SHELL_ONLY")
        self.assertFalse(stalker["boss_complete"])
        self.assertFalse(stalker["chapter_apex_complete"])
        self.assertIn("boss_phase_state_machine", stalker["withheld"])
        self.assertIn("terminal_reward_semantics", stalker["withheld"])
        self.assertIn("aionbound:thorn_stalker_skull", stalker["forbidden_loot"])
        self.assertEqual(set(stalker["support_tickets"]), {"W1-CREATIVE-003", "W1-CREATIVE-004"})
        components = load(ROOT / "behavior_pack/entities/thorn_stalker.entity.json")["minecraft:entity"]["components"]
        forbidden_boss_components = {
            "minecraft:boss",
            "minecraft:timer",
            "minecraft:transformation",
            "minecraft:on_death",
        }
        self.assertFalse(forbidden_boss_components.intersection(components))


if __name__ == "__main__":
    unittest.main(verbosity=2)
