#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MAP_PATH = HERE / "CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.json"
BUILDER = HERE / "build_crystal_marsh_authority_map.py"
BEDROCK_ROOT = Path("/Users/blakegrove/Desktop/bedrock-server")

EXPECTED_IDS = {
    "creatures": {"prism_frog", "crystal_newt", "crystal_dragonfly", "bloom_crab", "mire_turtle", "glass_heron", "reed_serpent", "silt_crocodile", "bog_watcher", "marsh_wight"},
    "resources": {"glass_algae", "marsh_resin", "crystal_reed_item", "crystal_root_item", "wet_chitin", "silt_core", "flood_crystal", "mire_bloom_item", "moon_pearl", "prism_pearl"},
    "blocks": {"marsh_soil", "wet_clay_block", "algae_block", "crystal_gravel", "crystal_stone", "crystal_log", "marsh_wood", "flood_planks", "glass_root_block", "prism_brick"},
    "plants": {"pearl_grass", "marsh_fern", "flood_reed", "glass_moss", "glow_kelp", "bubble_pod", "crystal_lily", "crystal_vine", "mire_orchid", "prism_bloom"},
    "structures": {"flooded_dock", "ancient_boat", "marsh_broken_bridge", "pearl_cairn", "marsh_totem", "crystal_arch", "crystal_obelisk", "sunken_shrine", "ruined_observatory", "deep_pool_entrance"},
}

EXPECTED_EQUIPMENT = {
    "crystal_pike", "prism_bow", "crystal_circlet", "explorer_cloak", "crystal_shovel", "marsh_sickle",
    "crystal_talisman", "marsh_idol", "marsh_wight_mask", "moon_pearl_pedestal", "crystal_obelisk_fragment",
}

EXPECTED_AUTHORITY_HASHES = {
    "program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-003-crystal-marsh/MANIFEST_FULL.json": "dd91525f249163544a628d3f75658659f413f5b3e3792de13b14206aef3512ae",
    "program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-006-equipment-progression/MANIFEST_FULL.json": "71ab8dec6949ab4a1321fe4215d843cdb9c4279e8ca6a37adfb95c20149951ea",
    "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json": "aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5",
    "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md": "3116c217e06afe1fd0cd56ee742c537f948a4c91193ec831fd1b3ec362837bfc",
    "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json": "cf7e1cd8b81b4a8088d136e1f9f2cb4ee3e245cfa71259f2a957d6e4f55ccff9",
}


class CrystalMarshAuthorityMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(MAP_PATH.read_text())

    def test_exact_50_id_category_partition(self) -> None:
        assets = self.data["assets"]
        self.assertEqual(50, len(assets))
        self.assertEqual(50, len({asset["warehouse_id"] for asset in assets}))
        for category, expected in EXPECTED_IDS.items():
            actual = {asset["warehouse_id"] for asset in assets if asset["category"] == category}
            self.assertEqual(expected, actual, category)
        self.assertEqual({key: 10 for key in EXPECTED_IDS}, self.data["counts"]["by_category"])

    def test_runtime_identity_and_hash_bound_packet_sources(self) -> None:
        for asset in self.data["assets"]:
            self.assertEqual(f"aionbound:{asset['warehouse_id']}", asset["runtime_id"])
            self.assertEqual(6, len(asset["source_files"]))
            for source in asset["source_files"].values():
                self.assertRegex(source["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual("REQUIRED", asset["dependencies"]["codex"]["coverage"])
            self.assertIn("equipment", asset["dependencies"])

    def test_exact_packet006_links_and_hash_bound_sources(self) -> None:
        links = self.data["equipment_links"]["contract_direct"]
        self.assertEqual(EXPECTED_EQUIPMENT, {entry["warehouse_id"] for entry in links})
        self.assertEqual(11, len(links))
        for entry in links:
            self.assertEqual(f"aionbound:{entry['warehouse_id']}", entry["runtime_id"])
            self.assertEqual(6, len(entry["source_files"]))
        adjacent = {entry["warehouse_id"] for entry in self.data["equipment_links"]["adjacent_structure_or_crosscraft_references"]}
        self.assertEqual({"surveyor_staff", "trail_compass"}, adjacent)

    def test_minimum_ratification_tranches_are_exact(self) -> None:
        tickets = {ticket["id"] for ticket in self.data["minimum_source_complete_ratifications"]}
        self.assertEqual({"W1-001-CM", "W1-003-PEARL-DEPTHS", "W1-004-CM"}, tickets)
        self.assertEqual(
            {
                "W1-001-CM": "APPROVED_AS_PROPOSED",
                "W1-003-PEARL-DEPTHS": "APPROVED_AS_PROPOSED",
                "W1-004-CM": "APPROVED_AS_PROPOSED",
            },
            {key: value for key, value in self.data["current_ratification_reconciliation"].items() if key != "effect"},
        )
        self.assertEqual("DEFERRED_BY_USER", self.data["ratification_boundaries"]["W1-CREATIVE-005"]["status"])
        self.assertTrue(self.data["ratification_boundaries"]["W1-CREATIVE-005"]["not_minimum_for_base_crystal_vertical"])

    def test_deferred_ashen_activation_is_not_crystal_dependency(self) -> None:
        ashen = self.data["ratification_boundaries"]["ashen_runtime_activation"]
        self.assertEqual("MANAGED_REVIEWER_ACTIVATION_BLOCKED", ashen["status"])
        self.assertEqual("FINAL_INTEGRATION_DEPENDENCY_ONLY", ashen["relationship"])
        self.assertFalse(ashen["crystal_dependency"])

    def test_apex_is_not_natural_spawn_target_and_is_blocked(self) -> None:
        by_id = {asset["warehouse_id"]: asset for asset in self.data["assets"]}
        self.assertFalse(any("spawn_rules" in path for path in by_id["marsh_wight"]["shipping_targets"]["create"]))
        self.assertIn("W1-003-PEARL-DEPTHS", by_id["marsh_wight"]["classification"]["blocked_until"])
        for creature in EXPECTED_IDS["creatures"] - {"marsh_wight"}:
            self.assertTrue(any("spawn_rules" in path for path in by_id[creature]["shipping_targets"]["create"]), creature)

    def test_unresolved_terms_are_fail_closed(self) -> None:
        unresolved = self.data["unresolved_terms"]
        self.assertEqual("W1-001-CM", unresolved["disposition_required_by"])
        for term in ("Prism Mucus", "Watcher Lens", "Wight Shroud Cloth", "Crystal Pole", "Living Crystal Core", "Gale-strung prism_bow"):
            self.assertIn(term, unresolved["terms"])
        self.assertIn("Do not promote", unresolved["rule"])

    def test_authority_hashes_and_digest(self) -> None:
        actual = {entry["path"]: entry["sha256"] for entry in self.data["source_authorities"]}
        for path, digest in EXPECTED_AUTHORITY_HASHES.items():
            self.assertEqual(digest, actual[path])
        payload = dict(self.data)
        expected = payload.pop("authority_digest_sha256")
        encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
        self.assertEqual(expected, hashlib.sha256(encoded).hexdigest())

    def test_builder_is_byte_deterministic(self) -> None:
        if not BEDROCK_ROOT.is_dir():
            self.skipTest("authoritative bedrock root unavailable")
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for output in (first, second):
                subprocess.run([
                    "python3", str(BUILDER), "--bedrock-root", str(BEDROCK_ROOT),
                    "--repo-root", str(REPO), "--output-dir", output,
                ], check=True)
            for name in ("CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.json", "CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.md"):
                first_bytes = (Path(first) / name).read_bytes()
                second_bytes = (Path(second) / name).read_bytes()
                self.assertEqual(first_bytes, second_bytes, name)
                self.assertEqual((HERE / name).read_bytes(), first_bytes, name)


if __name__ == "__main__":
    unittest.main()
