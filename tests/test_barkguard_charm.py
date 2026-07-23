from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "production/features/barkguard-charm"
BP = FEATURE / "bedrock/behavior_pack"
RP = FEATURE / "bedrock/resource_pack"
ASSETS = ROOT / "prototypes/blockbench/barkguard_charm"


class PlayerModel:
    def __init__(self, durability=0, offhand=True):
        self.damage = durability
        self.offhand = offhand
        self.cooldown = 0
        self.effects = []
        self.last_tick = None

    def hurt(self, amount, tick):
        if amount < 2 or not self.offhand or self.cooldown > 0 or self.last_tick == tick:
            return False
        self.last_tick = tick
        self.effects.append(("resistance", 60, 0))
        self.cooldown = 240
        self.damage += 1
        if self.damage >= 96:
            self.offhand = False
        return True


class BarkguardCharmTests(unittest.TestCase):
    def test_references_reserved_ids_and_stable_api(self):
        for path in list(BP.rglob("*.json")) + list(RP.rglob("*.json")) + list(ASSETS.glob("*.json")) + list(ASSETS.glob("*.bbmodel")):
            json.loads(path.read_text())
        manifest = json.loads((BP / "manifest.json").read_text())
        self.assertIn({"module_name": "@minecraft/server", "version": "2.0.0"}, manifest["dependencies"])
        item = json.loads((BP / "items/barkguard_charm.json").read_text())["minecraft:item"]
        self.assertEqual(item["description"]["identifier"], "ccoriginal_cc:barkguard_charm")
        self.assertTrue(item["components"]["minecraft:allow_off_hand"])
        self.assertEqual(item["components"]["minecraft:durability"]["max_durability"], 96)
        attachable = json.loads((RP / "attachables/barkguard_charm.entity.json").read_text())
        self.assertEqual(attachable["minecraft:attachable"]["description"]["geometry"]["default"], "geometry.ccoriginal_cc.barkguard_charm")

    def test_offhand_threshold_effect_cooldown_and_duplicate(self):
        p = PlayerModel(offhand=False)
        self.assertFalse(p.hurt(2, 1))
        p.offhand = True
        self.assertFalse(p.hurt(1.999, 2))
        self.assertTrue(p.hurt(2, 3))
        self.assertEqual(p.effects, [("resistance", 60, 0)])
        self.assertEqual(p.cooldown, 240)
        self.assertEqual(p.damage, 1)
        p.cooldown = 0
        self.assertFalse(p.hurt(8, 3), "duplicate event path in the same server tick")
        self.assertEqual(p.damage, 1)

    def test_exact_durability_and_break(self):
        p = PlayerModel(durability=94)
        self.assertTrue(p.hurt(2, 1))
        self.assertTrue(p.offhand)
        self.assertEqual(p.damage, 95)
        p.cooldown = 0
        self.assertTrue(p.hurt(2, 2))
        self.assertFalse(p.offhand)
        self.assertEqual(p.damage, 96)

    def test_two_and_four_player_isolation(self):
        for count in (2, 4):
            players = [PlayerModel() for _ in range(count)]
            for player in players:
                self.assertTrue(player.hurt(2, 10))
            self.assertEqual([p.damage for p in players], [1] * count)
            players[0].cooldown = 0
            self.assertTrue(players[0].hurt(2, 11))
            self.assertEqual([p.damage for p in players], [2] + [1] * (count - 1))

    def test_death_reconnect_and_restart_model(self):
        p = PlayerModel(durability=12)
        p.cooldown = 37
        inventory_damage = p.damage
        reconnected = PlayerModel(durability=inventory_damage)
        self.assertEqual(reconnected.damage, 12)
        self.assertEqual(reconnected.cooldown, 0)
        self.assertTrue(reconnected.hurt(2, 1))
        restarted = PlayerModel(durability=reconnected.damage)
        self.assertEqual(restarted.damage, 13)
        self.assertEqual(restarted.last_tick, None)

    def test_no_scan_callbacks_or_custom_persistence(self):
        script = (BP / "scripts/main.js").read_text()
        self.assertIn("world.afterEvents.entityHurt.subscribe", script)
        self.assertIn("EquipmentSlot.Offhand", script)
        for forbidden in ("runInterval", "getPlayers(", "getEntities(", "setDynamicProperty", "getDynamicProperty", "runTimeout"):
            self.assertNotIn(forbidden, script)
        self.assertEqual(script.count("entityHurt.subscribe"), 1)

    def test_geometry_animation_icon_recipe_and_grant(self):
        geo = json.loads((ASSETS / "barkguard_charm.geo.json").read_text())["minecraft:geometry"][0]
        self.assertEqual(geo["description"]["texture_width"], 32)
        self.assertEqual(sum(len(b.get("cubes", [])) for b in geo["bones"]), 7)
        animations = json.loads((RP / "animations/barkguard_charm.animation.json").read_text())["animations"]
        self.assertEqual(len(animations), 2)
        self.assertTrue((RP / "textures/items/barkguard_charm.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        recipe = json.loads((BP / "recipes/barkguard_charm.json").read_text())["minecraft:recipe_shaped"]
        self.assertEqual(recipe["result"]["item"], "ccoriginal_cc:barkguard_charm")
        self.assertEqual((BP / "functions/barkguard_test.mcfunction").read_text(), "give @s ccoriginal_cc:barkguard_charm 1\n")

    def test_deterministic_build_hashes_and_labels(self):
        builder = ROOT / "tools/build_barkguard_charm.py"
        subprocess.run(["python3", str(builder)], cwd=ROOT, check=True, capture_output=True)
        package = FEATURE / "dist/barkguard-charm-INTERNAL-TEST.mcaddon"
        first = hashlib.sha256(package.read_bytes()).hexdigest()
        subprocess.run(["python3", str(builder)], cwd=ROOT, check=True, capture_output=True)
        second = hashlib.sha256(package.read_bytes()).hexdigest()
        self.assertEqual(first, second)
        packet = json.loads((FEATURE / "reports/candidate-packet.json").read_text())
        self.assertEqual(packet["package"]["sha256"], first)
        self.assertIn("NOT PHYSICAL PS4 CERTIFIED", packet["labels"])
        with zipfile.ZipFile(package) as archive:
            self.assertIn("behavior_pack/manifest.json", archive.namelist())
            self.assertIn("resource_pack/manifest.json", archive.namelist())


if __name__ == "__main__":
    unittest.main()
