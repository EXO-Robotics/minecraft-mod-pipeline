import importlib.util
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("ww_codex", HERE / "build_whisperwood_codex_map.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class WhisperwoodCodexMapTest(unittest.TestCase):
    def setUp(self):
        self.data = MOD.build()

    def test_exact_coverage_and_unique_runtime_ids(self):
        entries = self.data["entries"]
        self.assertEqual(len(entries), 40)
        self.assertEqual(len({e["runtime_id"] for e in entries}), 40)
        counts = {kind: sum(e["entry_kind"] == kind for e in entries) for kind in ("resource", "block", "plant", "creature")}
        self.assertEqual(counts, {"resource": 10, "block": 10, "plant": 10, "creature": 10})
        expected = {
            "resource": {row[0] for row in MOD.RESOURCES},
            "block": {row[0] for row in MOD.BLOCKS},
            "plant": {row[0] for row in MOD.PLANTS},
            "creature": {row[0] for row in MOD.CREATURES},
        }
        actual = {kind: {e["id"] for e in entries if e["entry_kind"] == kind} for kind in expected}
        self.assertEqual(actual, expected)

    def test_exact_stamps_are_unique_and_bounded(self):
        stamps = [s["id"] for e in self.data["entries"] for s in e["discovery_stamps"]]
        self.assertEqual(len(stamps), 40)
        self.assertEqual(len(stamps), len(set(stamps)))
        self.assertTrue(all(s.startswith("codex:ww:") and len(s) < 128 for s in stamps))
        details = [d["id"] for e in self.data["entries"] for d in e.get("detail_events", [])]
        self.assertEqual(len(details), 3)
        self.assertEqual(len(details), len(set(details)))

    def test_all_entries_answer_three_questions_without_primary_chat(self):
        required = {"what_did_i_find", "what_can_i_make", "what_should_i_investigate_next"}
        for entry in self.data["entries"]:
            self.assertEqual(set(entry["player_questions"]), required)
            self.assertTrue(all(value["text"] for value in entry["player_questions"].values()))
            self.assertTrue(all(value["data_status"] == "SAFE_AUTHORED_GUIDANCE_DATA" for value in entry["player_questions"].values()))
            self.assertEqual(entry["readiness"]["discovery_entry_and_stamp_contract"], "SAFE_NOW")
            self.assertFalse(entry["integration"]["primary_chat_ux_allowed"])

    def test_creative_vocabulary_and_no_lore_rewrite(self):
        allowed = set(self.data["creative_rules"]["importance_vocabulary"])
        self.assertTrue(self.data["creative_rules"]["no_lore_rewrite"])
        self.assertTrue(all(e["importance"] in allowed for e in self.data["entries"]))
        self.assertTrue(all("lore" not in e for e in self.data["entries"]))
        blocks = [e for e in self.data["entries"] if e["entry_kind"] == "block"]
        self.assertTrue(all(e["codex_category"] == "resource" for e in blocks))

    def test_runtime_blockers_are_explicit(self):
        stalker = next(e for e in self.data["entries"] if e["id"] == "thorn_stalker")
        self.assertIn("boss_envelope:W1-CREATIVE-003", stalker["runtime_completion_blocked_by"])
        self.assertIn("loot_probability:W1-CREATIVE-004", stalker["runtime_completion_blocked_by"])
        acorn = next(e for e in self.data["entries"] if e["id"] == "ancient_acorn")
        self.assertIn("twinbond_presentation:W1-CREATIVE-002", acorn["runtime_completion_blocked_by"])
        self.assertTrue(self.data["minimal_successor_integration"]["migration_required"])
        self.assertEqual(self.data["minimal_successor_integration"]["successor_schema_extension"]["version"], 4)

    def test_checked_in_outputs_are_deterministic(self):
        expected = json.dumps(self.data, indent=2, sort_keys=True) + "\n"
        self.assertEqual((HERE / "WHISPERWOOD_CODEX_IMPLEMENTATION_MAP.json").read_text(), expected)
        self.assertEqual((HERE / "WHISPERWOOD_CODEX_IMPLEMENTATION_MAP.md").read_text(), MOD.render_md(self.data))


if __name__ == "__main__":
    unittest.main()
