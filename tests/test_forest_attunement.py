import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "production/features/forest-attunement"
BUILD = ROOT / "tools/build_forest_attunement.py"
STATE_JS = FEATURE / "behavior_pack/scripts/state.js"
MAIN_JS = FEATURE / "behavior_pack/scripts/main.js"
PROPERTY = "ccoriginal_cc:forest_attunement_v1"
CANONICAL = '{"version":1,"unlocked":true}'


def decode(raw):
    if raw is None:
        return "empty", False
    if raw is True:
        return "legacy", True
    if not isinstance(raw, str):
        return "corrupt", False
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return "corrupt", False
    if not isinstance(value, dict):
        return "corrupt", False
    if "version" not in value and value.get("unlocked") is True:
        return "legacy", True
    if not isinstance(value.get("version"), int):
        return "corrupt", False
    if value["version"] != 1:
        return "unknown", False
    if value.get("unlocked") is not True:
        return "corrupt", False
    return "current", True


@dataclass
class Player:
    count: int
    raw: object = None
    presentation_errors: int = 0

    def activate(self, presentation_throws=False):
        kind, unlocked = decode(self.raw)
        if unlocked:
            if kind == "legacy":
                self.raw = CANONICAL
            return False
        if kind in {"unknown", "corrupt"} or self.count < 1:
            return False
        self.raw = CANONICAL
        self.count -= 1
        try:
            if presentation_throws:
                raise RuntimeError("simulated particle failure")
        except RuntimeError:
            self.presentation_errors += 1
        return True

    def attuned(self):
        kind, unlocked = decode(self.raw)
        if kind == "legacy":
            self.raw = CANONICAL
        return unlocked

    def reset(self, is_op=True):
        if is_op:
            self.raw = None


class ForestAttunementTests(unittest.TestCase):
    def test_fresh_activation_consumes_exactly_one_and_duplicate_preserves(self):
        player = Player(3)
        self.assertTrue(player.activate())
        self.assertEqual((player.count, player.raw), (2, CANONICAL))
        self.assertFalse(player.activate())
        self.assertEqual((player.count, player.raw), (2, CANONICAL))

    def test_presentation_failure_after_consumption_preserves_commit(self):
        player = Player(2)
        self.assertTrue(player.activate(presentation_throws=True))
        self.assertEqual(player.presentation_errors, 1)
        self.assertEqual(player.count, 1)
        self.assertEqual(player.raw, CANONICAL)
        self.assertFalse(player.activate())
        self.assertEqual((player.count, player.raw), (1, CANONICAL))

        source = MAIN_JS.read_text()
        presentation = source.split("function presentActivation(player) {", 1)[1].split(
            "\n}\n\nfunction activate", 1
        )[0]
        committed_tail = source.split("presentActivation(player);", 1)[1].split(
            "\n}\n\nworld.afterEvents", 1
        )[0]
        self.assertNotIn("setDynamicProperty", presentation + committed_tail)
        self.assertNotIn("PROPERTY_ID", presentation + committed_tail)

    def test_two_and_four_player_isolation_and_simultaneous_activation(self):
        players = [Player(i + 1) for i in range(4)]
        self.assertTrue(players[0].activate())
        self.assertIsNone(players[1].raw)
        for player in players[1:]:
            self.assertTrue(player.activate())
        self.assertEqual([p.count for p in players], [0, 1, 2, 3])
        players[2].reset()
        self.assertEqual([p.attuned() for p in players], [True, True, False, True])

    def test_death_disconnect_reconnect_and_restart_use_persisted_property(self):
        player = Player(1)
        player.activate()
        persisted = player.raw
        del player
        reconnected = Player(0, persisted)
        self.assertTrue(reconnected.attuned())
        restarted = Player(0, reconnected.raw)
        self.assertTrue(restarted.attuned())
        self.assertEqual(restarted.raw, CANONICAL)

    def test_known_migrations_are_canonical_and_idempotent(self):
        for legacy in (True, '{"unlocked":true}'):
            player = Player(2, legacy)
            self.assertTrue(player.attuned())
            self.assertEqual(player.raw, CANONICAL)
            self.assertTrue(player.attuned())
            self.assertEqual(player.count, 2)

    def test_unknown_and_corrupt_fail_closed_preserved_without_consumption(self):
        states = ('{"version":2,"unlocked":true}', "{broken", False, 17, "null",
                  '{"version":1,"unlocked":false}')
        for state in states:
            player = Player(2, state)
            self.assertFalse(player.activate())
            self.assertEqual(player.raw, state)
            self.assertEqual(player.count, 2)

    def test_admin_reset_is_invoker_only_and_non_operator_refused(self):
        a, b = Player(0, CANONICAL), Player(0, CANONICAL)
        a.reset(is_op=False)
        self.assertEqual(a.raw, CANONICAL)
        a.reset(is_op=True)
        self.assertIsNone(a.raw)
        self.assertEqual(b.raw, CANONICAL)

    def test_runtime_has_one_bounded_interval_and_no_tick_subscription_or_cache(self):
        source = MAIN_JS.read_text()
        self.assertEqual(source.count("system.runInterval("), 1)
        self.assertIn("}, 100);", source)
        self.assertNotIn("runInterval(() =>", source.replace("system.runInterval(() =>", "", 1))
        self.assertNotIn("afterEvents.tick", source)
        self.assertNotIn("beforeEvents.tick", source)
        self.assertNotRegex(source, r"new\s+Map|new\s+WeakMap")
        self.assertEqual(source.count("world.getAllPlayers()"), 1)
        self.assertIn("world.getAllPlayers().slice(0, 4)", source)

    def test_stable_api_version_reserved_ids_and_pack_uuids(self):
        bp = json.loads((FEATURE / "behavior_pack/manifest.json").read_text())
        rp = json.loads((FEATURE / "resource_pack/manifest.json").read_text())
        dependency = next(d for d in bp["dependencies"] if d.get("module_name") == "@minecraft/server")
        self.assertEqual(dependency["version"], "2.0.0")
        self.assertEqual(bp["header"]["uuid"], "43b642d0-a651-45cf-ae20-96a0b853fba5")
        self.assertEqual(bp["modules"][0]["uuid"], "e7798870-c7e2-4522-87bf-d046b08b442f")
        self.assertEqual(bp["modules"][1]["uuid"], "2db423eb-5691-4207-bb37-01751206657d")
        self.assertEqual(rp["header"]["uuid"], "0317044d-9b78-4101-aa2e-cb395af4e948")
        self.assertEqual(rp["modules"][0]["uuid"], "f00200ff-d682-4f87-9873-2e92abe15060")
        self.assertIn(PROPERTY, STATE_JS.read_text())

    def test_all_json_parses_and_icon_is_32px_png(self):
        for path in FEATURE.rglob("*.json"):
            json.loads(path.read_text())
        icon = FEATURE / "resource_pack/textures/items/forest_attunement_sigil.png"
        subprocess.run(["python3", str(BUILD)], cwd=ROOT, check=True, capture_output=True, text=True)
        data = icon.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(tuple(int.from_bytes(data[offset:offset + 4], "big") for offset in (16, 20)), (32, 32))

    def test_deterministic_package_rebuild_and_internal_labels(self):
        subprocess.run(["python3", str(BUILD)], cwd=ROOT, check=True, capture_output=True, text=True)
        outputs = sorted((FEATURE / "dist").glob("*"))
        before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in outputs}
        subprocess.run(["python3", str(BUILD)], cwd=ROOT, check=True, capture_output=True, text=True)
        after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in outputs}
        self.assertEqual(before, after)
        self.assertTrue(all("INTERNAL-TEST" in path.name for path in outputs))
        addon = FEATURE / "dist/forest-attunement-INTERNAL-TEST.mcaddon"
        with zipfile.ZipFile(addon) as archive:
            self.assertTrue(all(info.date_time == (2020, 1, 1, 0, 0, 0) for info in archive.infolist()))
            self.assertIn("ForestAttunement_BP/scripts/main.js", archive.namelist())
            self.assertIn("ForestAttunement_RP/textures/items/forest_attunement_sigil.png", archive.namelist())


if __name__ == "__main__":
    unittest.main()
