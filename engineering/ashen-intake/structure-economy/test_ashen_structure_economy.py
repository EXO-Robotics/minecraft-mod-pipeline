import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("ashen_structure_economy_author", HERE / "author_ashen_structure_economy.py")
author = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = author
SPEC.loader.exec_module(author)


class AshenStructureEconomyTests(unittest.TestCase):
    def test_exact_table_scope_bands_and_distinct_hashes(self):
        self.assertEqual({
            "burned_camp", "char_wagon", "broken_bridge", "basalt_arch",
            "ash_watchtower", "ancient_kiln", "ash_cave", "ember_forge",
        }, set(author.TABLES))
        hashes = set()
        for table_id, spec in author.TABLES.items():
            band = author.BANDS[spec["band"]]
            total = [spec["guaranteedRolls"] + value for value in spec["choiceRolls"]]
            self.assertEqual(band["totalRolls"], total, table_id)
            self.assertEqual(band["guaranteedRegionalMaterialRolls"], spec["guaranteedRolls"], table_id)
            encoded = author.json_bytes(author.loot_document(spec))
            hashes.add(hashlib.sha256(encoded).hexdigest())
        self.assertEqual(8, len(hashes))

    def test_identities_close_and_protected_rewards_are_never_static(self):
        defined = set()
        for path in (author.BP / "items").glob("*.json"):
            defined.add(json.loads(path.read_text())["minecraft:item"]["description"]["identifier"])
        for path in (author.BP / "blocks").glob("*.json"):
            defined.add(json.loads(path.read_text())["minecraft:block"]["description"]["identifier"])
        used = {item["typeId"] for spec in author.TABLES.values() for pool in (spec["guaranteed"], spec["choice"]) for item in pool}
        self.assertTrue(used.issubset(defined), sorted(used - defined))
        self.assertTrue(author.FORBIDDEN_STATIC_REWARDS.isdisjoint(used))

    def test_static_bindings_and_protected_ember_forge_cache(self):
        static_ids = set(author.assembly_author.STATIC_CHEST_STRUCTURES)
        self.assertEqual(set(author.TABLES) - {"ember_forge"}, static_ids)
        for assembly in author.assembly_author.ASSEMBLIES:
            bound = [anchor for anchor in assembly.anchors if anchor.get("loot_table")]
            if assembly.identifier in static_ids:
                self.assertEqual(1, len(bound), assembly.identifier)
                self.assertEqual(f"loot_tables/chests/ashen/{assembly.identifier}.json", bound[0]["loot_table"])
            elif assembly.identifier == "ember_forge":
                self.assertEqual([], bound)
                encoded, _palette, _indices = author.assembly_author.encode_structure(assembly)
                self.assertNotIn(b"LootTable", encoded)

    def test_activation_signatures_are_exact_assembly_derived(self):
        records = author.signatures()
        expected_count = sum(len(assembly.anchors) for assembly in author.assembly_author.ASSEMBLIES)
        self.assertEqual(expected_count, len(records))
        self.assertEqual(set(item.identifier for item in author.assembly_author.ASSEMBLIES), {item["structure"] for item in records})
        keys = set()
        for record in records:
            assembly = next(item for item in author.assembly_author.ASSEMBLIES if item.identifier == record["structure"])
            anchor = next(item for item in assembly.anchors if item["anchor_id"] == record["anchor_id"])
            self.assertEqual(anchor["coordinate"], record["anchor_coordinate"])
            self.assertEqual(anchor["expected_block"], record["anchor_type"])
            self.assertEqual(8, len(record["probes"]))
            for probe in record["probes"]:
                xyz = tuple(anchor["coordinate"][index] + probe["offset"][index] for index in range(3))
                self.assertEqual(probe["expected_block"], assembly.blocks[xyz])
            key = (record["anchor_type"], tuple((tuple(probe["offset"]), probe["expected_block"]) for probe in record["probes"]))
            self.assertNotIn(key, keys, record["anchor_id"])
            keys.add(key)
            self.assertEqual(f"aionbound.structure.ashen.{assembly.identifier}.discovered.v1", record["stamp"])

    def test_outputs_are_deterministic_and_proof_bounded(self):
        first, manifest = author.expected_outputs()
        second, _ = author.expected_outputs()
        self.assertEqual(first, second)
        self.assertEqual(12, len(first))
        self.assertEqual("KILN_SKY_SERVICE_ONLY", manifest["protected_arena_cache"]["boss_terminal_ownership"])
        self.assertEqual(False, manifest["protected_arena_cache"]["static_loot_binding"])
        self.assertIn("NO BDS", manifest["proof_boundary"])


if __name__ == "__main__":
    unittest.main()
