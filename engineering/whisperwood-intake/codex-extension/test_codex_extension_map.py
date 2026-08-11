import hashlib
import json
import math
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MAP_PATH = HERE / "WHISPERWOOD_CODEX_EXTENSION_MAP.json"
BEDROCK_ROOT = Path("/Users/blakegrove/Desktop/bedrock-server")


class WhisperwoodCodexExtensionMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MAP_PATH.read_text())

    def test_generated_outputs_are_deterministic(self):
        subprocess.run(["python3", str(HERE / "build_codex_extension_map.py"), "--check"], check=True)

    def test_exact_coverage_and_unique_category_indexes(self):
        entries = self.data["entries"]
        self.assertEqual([len(entries[key]) for key in ("structures", "equipment", "bosses", "progression")], [10, 21, 1, 2])
        self.assertEqual(self.data["scope"]["adds_pages"], 34)
        self.assertEqual(self.data["scope"]["whisperwood_total_after_integration"], 74)
        for key in entries:
            category_entries = entries[key]
            self.assertEqual([entry["category_index"] for entry in category_entries], list(range(len(category_entries))))
        all_ids = [entry["id"] for group in entries.values() for entry in group]
        self.assertEqual(len(all_ids), len(set(all_ids)))

    def test_packet001_structures_and_packet006_equipment_are_exact(self):
        expected_structures = {"lantern_post", "moss_cairn", "hunter_camp", "broken_wagon", "root_bridge", "owl_shrine", "forest_waystone", "hollow_cave_entrance", "ancient_totem", "fallen_giant_tree"}
        self.assertEqual({entry["id"] for entry in self.data["entries"]["structures"]}, expected_structures)
        expected_equipment = {
            "mossfang_spear", "widow_fang_dagger", "thorn_whip", "briar_cleaver", "moon_sap_staff",
            "whisperwood_helmet", "whisperwood_chest", "whisperwood_legs", "whisperwood_boots",
            "root_knife", "whisperwood_hatchet", "lantern_hook",
            "moss_charm", "root_bracelet", "lantern_badge", "moon_sap_pendant", "briar_ring",
            "thorn_stalker_skull", "briar_elk_trophy", "mosskip_trophy", "ancient_acorn_display",
        }
        self.assertEqual({entry["id"] for entry in self.data["entries"]["equipment"]}, expected_equipment)
        for entry in self.data["entries"]["equipment"]:
            path = ROOT / ("behavior_pack/blocks" if entry["equipment_subtype"] == "trophy" else "behavior_pack/items") / f"{entry['id']}.{'block' if entry['equipment_subtype'] == 'trophy' else 'item'}.json"
            self.assertTrue(path.is_file(), path)

    def test_structure_discovery_is_exact_activation_or_ten_second_proximity(self):
        for entry in self.data["entries"]["structures"]:
            events = entry["discovery_events"]
            self.assertEqual({event["action"] for event in events}, {"first_successful_activation", "recognized_structure_proximity"})
            proximity = next(event for event in events if event["action"] == "recognized_structure_proximity")
            self.assertIn("200 accumulated consecutive ticks", proximity["predicate"])
            self.assertTrue(all(event["stage"] == "complete" for event in events))
            self.assertIn("no reward or loot claim", entry["unlock_semantics"])

    def test_trophy_and_boss_guards_preserve_ratified_semantics(self):
        equipment = {entry["id"]: entry for entry in self.data["entries"]["equipment"]}
        self.assertTrue(equipment["thorn_stalker_skull"]["chapter_seal_identity"])
        self.assertFalse(equipment["thorn_stalker_skull"]["physical_item_progression_blocker"])
        for identifier in ("briar_elk_trophy", "mosskip_trophy"):
            self.assertTrue(equipment[identifier]["optional_mastery"])
            self.assertFalse(equipment[identifier]["mastery_progression_blocker"])
        boss = self.data["entries"]["bosses"][0]
        self.assertFalse(boss["ecology_form_can_unlock_complete"])
        self.assertEqual([event["stage"] for event in boss["discovery_events"]], ["partial", "complete"])
        cross = self.data["cross_page_semantics"]
        self.assertIn("cannot complete", cross["ecology_stalker_seal_prohibition"])
        self.assertFalse(cross["mastery_trophies"]["progression_blockers"])
        self.assertIn("physical item presence", cross["recovery"])

    def test_ashen_rumor_is_codex_structure_state_not_item(self):
        rumor = next(entry for entry in self.data["entries"]["progression"] if entry["id"] == "ashen_rumor")
        self.assertEqual(rumor["presentation"], "Codex/structure-state page only")
        self.assertEqual(rumor["authority_text"]["safe_spoiler"], "Heat waits east of the burned wagons.")
        self.assertEqual(set(rumor["forbidden_representation"]), {"map-scrap item", "inventory grant", "Ashen unlock item"})
        self.assertIn("landmark:broken_wagon", rumor["discovery_events"][0]["predicate"])

    def test_compact_v4_extension_budget_is_exact_and_monotonic(self):
        extension = self.data["compact_v4_extension"]
        self.assertEqual(extension["state_schema_version"], {"before": 4, "after": 4})
        self.assertEqual(extension["registry_version"], {"before": 1, "after": 2})
        caps = extension["category_caps_after"]
        self.assertEqual(caps, {"resource": 20, "plant": 10, "creature": 10, "structure": 10, "equipment": 21, "boss": 1, "progression": 2})
        current = extension["category_caps_before"]
        added_bytes = sum(math.ceil(caps[key] / 4) for key in caps if key not in current)
        self.assertEqual(added_bytes, 11)
        discovery = {"rv": 2}
        for region in ("ww", "ah", "cm", "sr"):
            discovery[region] = {key: "aa" * math.ceil(cap / 4) for key, cap in caps.items()}
        self.assertEqual(len(json.dumps(discovery, separators=(",", ":"), ensure_ascii=False)), 596)
        self.assertLess(596, extension["player_budget_bytes"] * 0.08)

    def test_authority_hashes_match_current_frozen_bytes(self):
        for row in self.data["authority"]:
            path = ROOT / row["path"] if row["path"].startswith("engineering/") else BEDROCK_ROOT / row["path"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["sha256"], row["path"])

    def test_scope_is_map_only_and_conflicts_are_explicit(self):
        self.assertFalse(self.data["scope"]["edits_shipping_runtime"])
        files = {row["file"] for row in self.data["runtime_integration_conflicts"]}
        self.assertTrue({"behavior_pack/scripts/wave1_codex_data.js", "behavior_pack/scripts/state.js", "behavior_pack/scripts/codex.js", "behavior_pack/scripts/runtime.js"}.issubset(files))
        self.assertIn("BDS", self.data["not_proven"])
        self.assertIn("Checkpoint 1 readiness", self.data["not_proven"])


if __name__ == "__main__":
    unittest.main()
