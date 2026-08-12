#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "SKYREACH_ECONOMY_CODEX_SCAFFOLD.json").read_text())


class SkyreachEconomyCodexTest(unittest.TestCase):
    def test_append_only_exact_50(self):
        registry = DATA["registry"]
        self.assertEqual((204, 50, 254), (registry["prefix_entries"], registry["skyreach_entries"], registry["entries_after"]))
        self.assertEqual(list(range(204, 254)), [row["global_append_ordinal"] for row in registry["entries"]])
        self.assertEqual(50, len({row["id"] for row in registry["entries"]}))

    def test_region_local_indices_and_exact_events(self):
        grouped = {}
        events = set()
        for row in DATA["registry"]["entries"]:
            grouped.setdefault(row["codex_category"], []).append(row["category_index"])
            event = row["discovery_event"]
            self.assertTrue(event["id"].startswith(f"codex:sr:{row['codex_category']}:{row['id']}:"))
            self.assertNotIn(event["id"], events)
            events.add(event["id"])
        self.assertEqual(list(range(10)), grouped["creature"])
        self.assertEqual(list(range(20)), grouped["resource"])
        self.assertEqual(list(range(10)), grouped["plant"])
        self.assertEqual(list(range(10)), grouped["structure"])

    def test_resources_have_purpose_or_deferred_relationship(self):
        resources = [row for row in DATA["registry"]["entries"] if row["source_category"] == "resources"]
        self.assertEqual(10, len(resources))
        for row in resources:
            self.assertTrue(row["economy_relationships"], row["id"])
            self.assertTrue(all(rel["status"] in {"SAFE_NOW_NONNUMERIC_RELATIONSHIP", "DEFERRED_RELATIONSHIP"} for rel in row["economy_relationships"]))

    def test_unratified_surfaces_remain_deferred(self):
        self.assertEqual({"W1-001-SR", "W1-003-STORM-NEST", "W1-004-SR", "W1-CREATIVE-005"}, {row["id"] for row in DATA["deferred_matrix"]})
        self.assertEqual("W1-CREATIVE-005", DATA["packet006_relationships"]["deferred_no_identity_or_page_allocation"]["blocker"])
        self.assertTrue(all(value is False for value in DATA["guards"].values()))

    def test_schema_and_handoffs(self):
        self.assertEqual((4, 4), (DATA["registry"]["state_schema_before"], DATA["registry"]["state_schema_after"]))
        self.assertEqual("codex:cm:progression:skyreach_rumor:ruined_observatory_visited", DATA["progression_handoffs"]["cm_to_skyreach"]["existing_event"])
        self.assertEqual("pilgrimage", DATA["progression_handoffs"]["skyreach_to_pilgrimage"]["target"])

    def test_generated_files_current(self):
        subprocess.run(["python3", str(HERE / "build_skyreach_economy_codex.py"), "--check"], check=True)

    def test_runtime_data_is_identity_only(self):
        source = (HERE.parents[2] / "behavior_pack/scripts/wave1_codex_skyreach_data.js").read_text()
        self.assertEqual(50, source.count('"region": "sr"'))
        payload = source.split("export const", 1)[1].lower()
        for forbidden in ("storm_nest:completed", "seal_credit", '"reward"', '"sidegrade"'):
            self.assertNotIn(forbidden, payload)


if __name__ == "__main__":
    unittest.main()
