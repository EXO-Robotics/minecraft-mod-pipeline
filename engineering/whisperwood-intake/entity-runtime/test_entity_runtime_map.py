#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("entity_map", HERE / "build_entity_runtime_map.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EntityRuntimeMapTests(unittest.TestCase):
    def setUp(self):
        self.data = MODULE.build()

    def test_exact_creature_inventory(self):
        ids = [e["warehouse_id"] for e in self.data["entities"]]
        self.assertEqual(ids, sorted(MODULE.SPEC))
        self.assertEqual(len(ids), 10)

    def test_all_declared_role_clips_remain_explicitly_missing(self):
        for entity in self.data["entities"]:
            self.assertTrue(entity["animations"]["brief_declared"])
            self.assertEqual(entity["animations"]["missing_declared"], entity["animations"]["brief_declared"])
            self.assertEqual(entity["animations"]["status"], "BLOCKED_ROLE_CLIPS_ABSENT")

    def test_no_numeric_gameplay_tuning(self):
        forbidden = {"health", "damage", "speed", "priority", "weight", "chance", "threshold"}
        for entity in self.data["entities"]:
            keys = set()
            stack = [entity]
            while stack:
                item = stack.pop()
                if isinstance(item, dict):
                    keys.update(item)
                    stack.extend(item.values())
                elif isinstance(item, list):
                    stack.extend(item)
            self.assertFalse(keys & forbidden)

    def test_boss_and_motion_gaps_fail_closed(self):
        by_id = {e["warehouse_id"]: e for e in self.data["entities"]}
        self.assertIn("BOSS_ENVELOPE_W1_CREATIVE_003", by_id["thorn_stalker"]["blockers"])
        self.assertIn("CLIMB_RUNTIME_PATTERN_NOT_IN_G7", by_id["hollow_widow_spider"]["blockers"])
        self.assertIn("SPECTRAL_MOTION_ARCHITECTURE", by_id["bark_wraith"]["blockers"])

    def test_outputs_are_deterministic(self):
        expected_json = json.dumps(self.data, indent=2, sort_keys=True) + "\n"
        expected_md = MODULE.render_md(self.data)
        self.assertEqual((HERE / "WHISPERWOOD_ENTITY_RUNTIME_IMPLEMENTATION_MAP.json").read_text(), expected_json)
        self.assertEqual((HERE / "WHISPERWOOD_ENTITY_RUNTIME_IMPLEMENTATION_MAP.md").read_text(), expected_md)

    def test_all_bound_file_hashes_match_current_bytes(self):
        root = MODULE.PROGRAM.parent
        for entry in self.data["authorities"]:
            path = root / entry["path"] if entry["path"].startswith("program/") else MODULE.REPO / entry["path"]
            self.assertEqual(MODULE.sha256(path), entry["sha256"])
        for entries in self.data["g7_patterns"].values():
            for entry in entries:
                self.assertEqual(MODULE.sha256(MODULE.REPO / entry["path"]), entry["sha256"])
        for entity in self.data["entities"]:
            for entry in entity["source_assets"].values():
                self.assertEqual(MODULE.sha256(root / entry["path"]), entry["sha256"])


if __name__ == "__main__":
    unittest.main()
