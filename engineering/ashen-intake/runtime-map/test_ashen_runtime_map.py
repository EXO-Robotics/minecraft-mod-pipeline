from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MAP_PATH = HERE / "ASHEN_RUNTIME_IMPLEMENTATION_MAP.json"
GENERATOR_PATH = HERE / "build_ashen_runtime_map.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("ashen_runtime_map_builder", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AshenRuntimeMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(MAP_PATH.read_text())
        cls.builder = load_generator()

    def test_exact_base_and_counts(self):
        self.assertEqual(self.payload["base"]["commit"], "9c2880863ff260410028284228f5995b59dcacfc")
        self.assertEqual(self.payload["base"]["tree"], "91d7ed5ffbe94d693c5d37848942b2702edfbd69")
        self.assertEqual(self.payload["counts"], {"blocks": 10, "creatures": 10, "equipment_links": 14, "packet_002_assets": 50, "plants": 10, "ratified_ashen_prose_terms": 22, "resources": 10, "structures": 10, "unratified_ashen_identity_terms": 0})

    def test_closed_classification_vocabulary_and_coverage(self):
        allowed = {"KEEP", "REFINE", "REPLACE", "SUPERSEDE", "DEFER"}
        self.assertEqual(set(self.payload["classification_vocabulary"]), allowed)
        values = [r["classification"] for r in self.payload["system_reconciliation"]]
        for section in ("creatures", "plants", "blocks", "resources", "structures", "equipment"):
            values.extend(r["classification"] for r in self.payload[section])
        self.assertTrue(set(values) <= allowed)
        self.assertEqual(set(values), allowed)

    def test_exact_ids_are_unique(self):
        expected = {"creatures": {r[0] for r in self.builder.CREATURES}, "plants": {r[0] for r in self.builder.PLANTS}, "blocks": set(self.builder.BLOCKS), "resources": {r[0] for r in self.builder.RESOURCES}, "structures": {r[0] for r in self.builder.STRUCTURES}, "equipment": {r[0] for r in self.builder.EQUIPMENT}}
        for section, ids in expected.items():
            actual = [r["id"] for r in self.payload[section]]
            self.assertEqual(set(actual), ids)
            self.assertEqual(len(actual), len(set(actual)))

    def test_proposals_are_exact_snapshots_bound_by_v3(self):
        for ticket, (path, sha) in self.builder.PROPOSALS.items():
            raw = subprocess.check_output(["git", "show", f'{self.builder.BASE_COMMIT}:{path}'], cwd=ROOT)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), sha)
            rat = self.payload["ratifications"][ticket]
            self.assertEqual(rat["status"], "RATIFIED_BY_DECISION_LEDGER_V3")
            self.assertTrue(rat["proposal_bytes_preserved"])
            self.assertEqual(rat["proposal"], json.loads(raw)["proposal"])

    def test_only_authority_blocked_statuses_unlocked(self):
        states = {r["id"]: r for r in self.payload["authority_status"]}
        for ticket in ("W1-001-AH", "W1-003-KILN-SKY", "W1-004-AH"):
            self.assertEqual(states[ticket]["status"], "READY_AS_RATIFIED")
            self.assertFalse(states[ticket]["blocking"])
        self.assertEqual(states["W1-CREATIVE-005"]["status"], "DEFER")
        self.assertEqual(next(r for r in self.payload["system_reconciliation"] if r["system"] == "ashen_regrowth")["classification"], "DEFER")

    def test_all_22_prose_terms_resolve_without_new_invention(self):
        dispositions = [d for row in self.payload["creatures"] for d in row["loot"]["ratified_prose_dispositions"]]
        self.assertEqual(len(dispositions), 22)
        self.assertEqual(sum(d["disposition"] == "SELECTED_EXISTING_NEW_REQUIRED_ITEM" for d in dispositions), 1)
        self.assertEqual(next(d for d in dispositions if d["term"] == "Pack Cinder Mark")["disposition"], "NARRATIVE_CODEX_ONLY")
        drake = next(d for d in dispositions if d["term"] == "Drake Scale")
        self.assertEqual(drake["canonical_id"], "aionbound:drake_scale")
        self.assertEqual(drake["sidegrade_authority"], "NONE_W1-CREATIVE-005_DEFERRED")

    def test_kiln_sky_and_reward_boundaries_are_ratified(self):
        boss = self.payload["boss_boundary"]
        self.assertEqual((boss["classification"], boss["implementation_status"]), ("REFINE", "READY_AS_RATIFIED"))
        self.assertEqual(boss["encounter"], "aionbound:kiln_sky")
        self.assertEqual(boss["arena_tag"], "aionbound.kiln_sky_apex")
        self.assertFalse(boss["whisperwood_tuning_transfer"])
        self.assertEqual(boss["reward_resolution"]["chapter_critical_seal"], "aionbound:ash_drake_horn")
        self.assertFalse(boss["reward_resolution"]["ember_forge_core"]["progression_substitute_for_ash_drake_horn"])
        self.assertIn("damage_values", boss["explicit_nondecisions"])

    def test_native_and_product_proof_gaps_remain_explicit(self):
        gates = self.payload["asset_gates"]
        self.assertEqual((gates["representative_pass_count"], gates["remaining_custom_geometry_native_repair"], gates["block_or_resource_blockbench_na_conditional"]), (7, 23, 20))
        self.assertEqual(gates["golden_and_client_visual_promotion"], "WITHHELD")
        for key in ("bp_rp_edits", "build", "bds", "client", "runtime_behavior"):
            self.assertIn("NOT_", self.payload["proof_boundary"][key])

    def test_no_whisperwood_tuning_and_no_density_cap_increase(self):
        self.assertFalse(self.payload["worldgen_budget"]["whisperwood_tuning_transfer"])
        self.assertEqual(self.payload["worldgen_budget"]["global_natural_entities_target"], 40)
        self.assertEqual(self.payload["worldgen_budget"]["cap_change"], "NONE")
        self.assertTrue(all(not r["spawn"]["whisperwood_tuning_transfer"] for r in self.payload["creatures"]))
        self.assertFalse(next(r for r in self.payload["creatures"] if r["id"] == "ash_drake")["spawn"]["natural"])

    def test_source_target_ownership_never_conflicts(self):
        owners = defaultdict(set)
        def collect(v):
            if isinstance(v, dict):
                if set(v) >= {"path", "owner"}: owners[v["path"]].add(v["owner"])
                for child in v.values(): collect(child)
            elif isinstance(v, list):
                for child in v: collect(child)
        collect(self.payload)
        self.assertEqual({p: sorted(o) for p, o in owners.items() if len(o) > 1}, {})

    def test_all_authority_hashes_match_exact_base(self):
        for row in self.payload["authority"]:
            raw = subprocess.check_output(["git", "show", f'{self.builder.BASE_COMMIT}:{row["path"]}'], cwd=ROOT)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])

    def test_generator_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.json", Path(folder) / "b.json"
            for out in (a, b): subprocess.run(["python3", str(GENERATOR_PATH), "--output", str(out)], cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(a.read_bytes(), MAP_PATH.read_bytes())


if __name__ == "__main__":
    unittest.main()
