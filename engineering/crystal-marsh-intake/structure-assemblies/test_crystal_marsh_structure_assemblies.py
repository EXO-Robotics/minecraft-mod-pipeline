import importlib.util
import json
import struct
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("crystal_structure_author", HERE / "author_crystal_marsh_structures.py")
author = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = author
SPEC.loader.exec_module(author)


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0
    def take(self, length: int) -> bytes:
        value = self.data[self.offset:self.offset + length]
        if len(value) != length: raise ValueError("truncated NBT")
        self.offset += length
        return value
    def u8(self): return struct.unpack("<B", self.take(1))[0]
    def i32(self): return struct.unpack("<i", self.take(4))[0]
    def string(self): return self.take(struct.unpack("<H", self.take(2))[0]).decode()
    def payload(self, tag):
        if tag == 3: return self.i32()
        if tag == 8: return self.string()
        if tag == 9:
            subtype, count = self.u8(), self.i32()
            return [self.payload(subtype) for _ in range(count)]
        if tag == 10:
            value = {}
            while True:
                subtype = self.u8()
                if subtype == 0: return value
                name = self.string()
                value[name] = self.payload(subtype)
        raise ValueError(f"unsupported tag {tag}")
    def root(self):
        if self.u8() != 10 or self.string() != "": raise ValueError("not unnamed root compound")
        value = self.payload(10)
        if self.offset != len(self.data): raise ValueError("trailing bytes")
        return value


class CrystalMarshStructureAssemblyTests(unittest.TestCase):
    def test_exact_packet_landmark_inventory_and_distinct_bytes(self):
        expected = {
            "flooded_dock", "ancient_boat", "marsh_broken_bridge", "pearl_cairn", "marsh_totem",
            "crystal_arch", "crystal_obelisk", "sunken_shrine", "ruined_observatory", "deep_pool_entrance",
        }
        self.assertEqual(expected, {item.identifier for item in author.ASSEMBLIES})
        self.assertEqual(10, len({item.size for item in author.ASSEMBLIES}))
        hashes = {author.hashlib.sha256(author.encode_structure(item)[0]).hexdigest() for item in author.ASSEMBLIES}
        self.assertEqual(10, len(hashes))

    def test_little_endian_nbt_palette_indices_and_empty_metadata(self):
        for assembly in author.ASSEMBLIES:
            data, expected_palette, expected_indices = author.encode_structure(assembly)
            self.assertEqual(b"\x0a\x00\x00", data[:3], assembly.identifier)
            root = Reader(data).root()
            self.assertEqual(list(assembly.size), root["size"])
            structure = root["structure"]
            primary, secondary = structure["block_indices"]
            palette = [entry["name"] for entry in structure["palette"]["default"]["block_palette"]]
            self.assertEqual(expected_palette, palette)
            self.assertEqual(expected_indices, primary)
            self.assertEqual(assembly.size[0] * assembly.size[1] * assembly.size[2], len(primary))
            self.assertTrue(all(-1 <= index < len(palette) for index in primary))
            self.assertTrue(all(index == -1 for index in secondary))
            self.assertEqual([], structure["entities"])
            self.assertEqual({}, structure["palette"]["default"]["block_position_data"])
            for forbidden in (b"LootTable", b"reward", b"boss", b"entity_data"):
                self.assertNotIn(forbidden, data)

    def test_inert_machine_recorded_anchors_close_to_blocks(self):
        _outputs, manifest = author.expected_outputs()
        records = {record["id"]: record for record in manifest["assemblies"]}
        allowed = {"minecraft:barrel", "minecraft:lodestone", "minecraft:lectern"}
        anchor_ids = []
        for assembly in author.ASSEMBLIES:
            self.assertEqual(assembly.anchors, records[assembly.identifier]["anchors"])
            for item in assembly.anchors:
                anchor_ids.append(item["anchor_id"])
                xyz = tuple(item["coordinate"])
                self.assertIn(item["expected_block"], allowed)
                self.assertEqual(item["expected_block"], assembly.blocks[xyz])
                self.assertEqual("RESERVED_INERT_RUNTIME_HANDOFF", item["binding"])
                self.assertEqual("OMITTED", item["block_entity_nbt"])
                self.assertNotIn("loot_table", item)
        self.assertEqual(len(anchor_ids), len(set(anchor_ids)))

    def test_custom_palette_identifier_closure(self):
        defined = set()
        for path in (author.BP / "blocks").glob("*.json"):
            document = json.loads(path.read_text())
            defined.add(document["minecraft:block"]["description"]["identifier"])
        for assembly in author.ASSEMBLIES:
            custom = {name for name in assembly.blocks.values() if name.startswith("aionbound:")}
            self.assertTrue(custom.issubset(defined), f"{assembly.identifier}: {sorted(custom - defined)}")

    def test_stable_feature_references_and_wetland_proxy(self):
        outputs, _manifest = author.expected_outputs()
        for assembly in author.ASSEMBLIES:
            feature_path = author.BP / "features" / f"{assembly.identifier}.structure_feature.json"
            rule_path = author.BP / "feature_rules" / f"{assembly.identifier}.structure_feature_rule.json"
            feature = json.loads(outputs[feature_path])
            rule = json.loads(outputs[rule_path])
            body = feature["minecraft:structure_template_feature"]
            rule_body = rule["minecraft:feature_rules"]
            self.assertEqual("1.13.0", feature["format_version"])
            self.assertEqual("1.13.0", rule["format_version"])
            self.assertEqual(f"aionbound:{assembly.identifier}", body["structure_name"])
            self.assertEqual(body["description"]["identifier"], rule_body["description"]["places_feature"])
            filters = rule_body["conditions"]["minecraft:biome_filter"]["all_of"]
            self.assertIn({"test": "has_biome_tag", "operator": "==", "value": "overworld"}, filters)
            self.assertIn({"test": "has_biome_tag", "operator": "!=", "value": "ocean"}, filters)
            proxy = next(value["any_of"] for value in filters if "any_of" in value)
            self.assertEqual({"swamp", "river"}, {item["value"] for item in proxy})
            self.assertEqual(1, rule_body["distribution"]["iterations"])

    def test_crystal_specific_conservative_spacing(self):
        denominators = [item.denominator for item in author.ASSEMBLIES]
        self.assertEqual(len(denominators), len(set(denominators)))
        self.assertTrue(all(value >= 704 for value in denominators))
        self.assertTrue(author.PREVIOUS_ECOSYSTEM_DENOMINATORS.isdisjoint(denominators))
        self.assertGreater(max(denominators), 6000)

    def test_deterministic_regeneration_and_scope_boundary(self):
        first, manifest = author.expected_outputs()
        second, _ = author.expected_outputs()
        self.assertEqual(first, second)
        self.assertEqual(32, len(first))
        self.assertIn("visual evidence only", manifest["visual_asset_boundary"])
        self.assertTrue(all(path.suffix not in {".bbmodel", ".png"} for path in first))
        encoded = json.dumps(manifest, sort_keys=True)
        for forbidden in ("loot_tables/", "marsh_wight_mask", "boss_activation", "reward item"):
            self.assertNotIn(forbidden, encoded)


if __name__ == "__main__":
    unittest.main()
