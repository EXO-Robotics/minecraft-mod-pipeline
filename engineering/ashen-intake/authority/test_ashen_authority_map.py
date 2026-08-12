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
MAP_PATH = HERE / "ASHEN_HIGHLANDS_VERTICAL_INTAKE_MAP.json"
BUILDER = HERE / "build_ashen_authority_map.py"
BEDROCK_ROOT = Path("/Users/blakegrove/Desktop/bedrock-server")

EXPECTED_IDS = {
    "creatures": {"ash_mite", "ember_crow", "magma_lizard", "furnace_beetle", "char_wolf", "cinder_lynx", "ash_ram", "soot_stag", "basalt_tortoise", "ash_drake"},
    "resources": {"smolder_bark", "charbone", "sulfur_cluster", "volcanic_glass_shard", "ember_resin", "heatstone", "furnace_chitin", "basalt_core", "ash_crystal", "fire_bloom_seed"},
    "blocks": {"ash_log", "char_planks", "ash_soil", "cinder_gravel", "smolder_stone", "basalt_brick", "basalt_pillar", "heat_bark", "ember_moss", "volcanic_glass_block"},
    "plants": {"cinder_grass", "ash_fern", "smoke_reed", "char_shrub", "soot_mushroom", "magma_moss", "glow_root", "basalt_flower", "ember_vine", "fire_bloom"},
    "structures": {"fire_totem", "burned_camp", "char_wagon", "broken_bridge", "basalt_arch", "ash_watchtower", "ancient_kiln", "ember_forge", "lava_shrine", "ash_cave"},
}

EXPECTED_AUTHORITY_HASHES = {
    "program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-002-ashen-highlands/MANIFEST_FULL.json": "6cb3bd25a1ef473e60e5ed0ebf78288bcc4d53db1ff4ec74db4d22ddb036c738",
    "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json": "aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5",
    "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md": "3116c217e06afe1fd0cd56ee742c537f948a4c91193ec831fd1b3ec362837bfc",
    "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json": "cf7e1cd8b81b4a8088d136e1f9f2cb4ee3e245cfa71259f2a957d6e4f55ccff9",
    "engineering/authority/support-proposals/ashen/W1-001-AH.json": "dd26a683f7f3e5301b66d7f2861454b5bf6b79818d12e0e8e1b22b6f07217774",
    "engineering/authority/support-proposals/ashen/W1-003-KILN-SKY.json": "1b2d5f77185a1461040d7559d0d8ecdaf803d7727e419ceac32636865be85d7c",
    "engineering/authority/support-proposals/ashen/W1-004-AH.json": "93736ff800b1c90c8a6547d84336a6650f8ae32750f262de8e460385a7a26889",
}


class AshenAuthorityMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(MAP_PATH.read_text())

    def test_exact_50_id_category_partition(self) -> None:
        assets = self.data["assets"]
        self.assertEqual(50, len(assets))
        self.assertEqual(50, len({a["warehouse_id"] for a in assets}))
        for category, expected in EXPECTED_IDS.items():
            actual = {a["warehouse_id"] for a in assets if a["category"] == category}
            self.assertEqual(expected, actual, category)
        self.assertEqual({k: 10 for k in EXPECTED_IDS}, self.data["counts"]["by_category"])

    def test_runtime_identity_and_hash_bound_sources(self) -> None:
        for asset in self.data["assets"]:
            self.assertEqual(f"aionbound:{asset['warehouse_id']}", asset["runtime_id"])
            self.assertEqual(6, len(asset["source_files"]))
            for source in asset["source_files"].values():
                self.assertRegex(source["sha256"], r"^[0-9a-f]{64}$")
            self.assertIn("equipment", asset["dependencies"])
            self.assertEqual("REQUIRED", asset["dependencies"]["codex"]["coverage"])
            self.assertTrue(asset["dependencies"]["codex"]["discovery"])
        actual = {entry["path"]: entry["sha256"] for entry in self.data["source_authorities"]}
        for path, digest in EXPECTED_AUTHORITY_HASHES.items():
            self.assertEqual(digest, actual[path])

    def test_authority_digest_covers_payload(self) -> None:
        payload = dict(self.data)
        expected = payload.pop("authority_digest_sha256")
        encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
        self.assertEqual(expected, hashlib.sha256(encoded).hexdigest())

    def test_deferred_boundaries_are_fail_closed(self) -> None:
        unresolved = self.data["unresolved_terms"]
        self.assertEqual("DEFERRED_BY_USER", unresolved["W1-CREATIVE-005"]["status"])
        self.assertEqual("DEFERRED_UNTIL_SEPARATE_RATIFICATION", unresolved["W1-CREATIVE-001_CRYSTAL_SKY"]["status"])
        self.assertEqual("DEFERRED_EXCLUDING_RATIFIED_THORN_COURT_AND_KILN_SKY", unresolved["W1-CREATIVE-003_OTHER_BOSSES"]["status"])
        self.assertEqual("DEFERRED", unresolved["W1-CREATIVE-004_CRYSTAL_SKY"]["status"])
        withheld = " ".join(self.data["safe_now_withheld"]["withheld"])
        self.assertIn("outside the exact refined Ashen proposals", withheld)
        self.assertIn("sidegrade", withheld)
        self.assertIn("damage values", withheld)
        self.assertIn("arena-radius", withheld)

    def test_apex_has_no_natural_spawn_target(self) -> None:
        by_id = {a["warehouse_id"]: a for a in self.data["assets"]}
        self.assertFalse(any("spawn_rules" in p for p in by_id["ash_drake"]["shipping_targets"]["create"]))
        for creature in EXPECTED_IDS["creatures"] - {"ash_drake"}:
            self.assertTrue(any("spawn_rules" in p for p in by_id[creature]["shipping_targets"]["create"]), creature)

    def test_ratified_term_scope_is_narrow(self) -> None:
        self.assertEqual({
            "Heat Core": "aionbound:heat_core", "Heavy Head": "aionbound:heavy_head",
            "Chitin Plate": "aionbound:chitin_plate", "Ember Heart": "aionbound:ember_heart",
        }, self.data["ratified_terms"]["derived_components"])
        self.assertEqual({"mite_resin language": "aionbound:ember_resin"}, self.data["ratified_terms"]["aliases"])
        self.assertEqual("W1-001-AH_APPROVED_EXACT_REFINED_BYTES", self.data["ratified_terms"]["ashen_identity_authority"])
        self.assertEqual("W1-003-KILN-SKY_APPROVED_EXACT_REFINED_BYTES", self.data["ratified_terms"]["kiln_sky_authority"])
        self.assertEqual("W1-004-AH_APPROVED_EXACT_REFINED_BYTES", self.data["ratified_terms"]["ashen_loot_reward_authority"])

    def test_builder_is_byte_deterministic(self) -> None:
        if not BEDROCK_ROOT.is_dir():
            self.skipTest("authoritative bedrock root unavailable")
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for output in (first, second):
                subprocess.run([
                    "python3", str(BUILDER), "--bedrock-root", str(BEDROCK_ROOT),
                    "--repo-root", str(REPO), "--output-dir", output,
                ], check=True)
            for name in ("ASHEN_HIGHLANDS_VERTICAL_INTAKE_MAP.json", "ASHEN_HIGHLANDS_VERTICAL_INTAKE_MAP.md"):
                first_bytes = (Path(first) / name).read_bytes()
                second_bytes = (Path(second) / name).read_bytes()
                self.assertEqual(first_bytes, second_bytes, name)
                self.assertEqual((HERE / name).read_bytes(), first_bytes, name)


if __name__ == "__main__":
    unittest.main()
