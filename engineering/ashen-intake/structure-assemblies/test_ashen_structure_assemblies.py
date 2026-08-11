import importlib.util
import json
import struct
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("ashen_structure_author", HERE / "author_ashen_structures.py")
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
        if tag == 1: return self.u8()
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


class AshenStructureAssemblyTests(unittest.TestCase):
    def test_exact_ten_distinct_ids_sizes_hashes_and_anchor_ids(self):
        self.assertEqual(10, len(author.ASSEMBLIES))
        self.assertEqual(10, len({item.identifier for item in author.ASSEMBLIES}))
        self.assertEqual(10, len({item.size for item in author.ASSEMBLIES}))
        hashes = {author.hashlib.sha256(author.encode_structure(item)[0]).hexdigest() for item in author.ASSEMBLIES}
        self.assertEqual(10, len(hashes))
        anchor_ids = [anchor["anchor_id"] for item in author.ASSEMBLIES for anchor in item.anchors]
        self.assertEqual(len(anchor_ids), len(set(anchor_ids)))

    def test_little_endian_nbt_palette_indices_bounds_and_empty_position_data(self):
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
            self.assertEqual(len(primary), assembly.size[0] * assembly.size[1] * assembly.size[2])
            self.assertTrue(all(-1 <= index < len(palette) for index in primary))
            self.assertTrue(all(index == -1 for index in secondary))
            self.assertEqual([], structure["entities"])
            self.assertEqual({}, structure["palette"]["default"]["block_position_data"])
            self.assertNotIn(b"LootTable", data)

    def test_inert_anchor_coordinates_blocks_and_machine_manifest(self):
        outputs, manifest = author.expected_outputs()
        records = {record["id"]: record for record in manifest["assemblies"]}
        allowed_blocks = {"minecraft:barrel", "minecraft:lodestone", "minecraft:lectern"}
        for assembly in author.ASSEMBLIES:
            self.assertEqual(assembly.anchors, records[assembly.identifier]["anchors"])
            for item in assembly.anchors:
                xyz = tuple(item["coordinate"])
                self.assertIn(item["expected_block"], allowed_blocks)
                self.assertEqual(item["expected_block"], assembly.blocks[xyz])
                self.assertEqual("RESERVED_INERT_RUNTIME_HANDOFF", item["binding"])
                self.assertEqual("OMITTED", item["block_entity_nbt"])
                self.assertTrue(all(0 <= xyz[index] < assembly.size[index] for index in range(3)))
        encoded = json.dumps(manifest, sort_keys=True)
        for forbidden in ("ash_drake_horn", "ember_forge_core", "boss_activation", "LootTableSeed"):
            self.assertNotIn(forbidden, encoded)
        self.assertEqual(32, len(outputs))

    def test_custom_palette_identifier_closure(self):
        defined = set()
        for path in (author.BP / "blocks").glob("*.json"):
            document = json.loads(path.read_text())
            defined.add(document["minecraft:block"]["description"]["identifier"])
        for assembly in author.ASSEMBLIES:
            custom = {name for name in assembly.blocks.values() if name.startswith("aionbound:")}
            self.assertTrue(custom.issubset(defined), f"{assembly.identifier}: {sorted(custom - defined)}")

    def test_stable_feature_rule_ids_references_and_ashen_biome_proxy(self):
        outputs, _manifest = author.expected_outputs()
        for assembly in author.ASSEMBLIES:
            feature_path = author.BP / "features" / f"{assembly.identifier}.structure_feature.json"
            rule_path = author.BP / "feature_rules" / f"{assembly.identifier}.structure_feature_rule.json"
            feature = json.loads(outputs[feature_path])
            rule = json.loads(outputs[rule_path])
            self.assertEqual("1.13.0", feature["format_version"])
            self.assertEqual("1.13.0", rule["format_version"])
            body = feature["minecraft:structure_template_feature"]
            rule_body = rule["minecraft:feature_rules"]
            self.assertEqual(f"aionbound:{assembly.identifier}_structure_feature", body["description"]["identifier"])
            self.assertEqual(f"aionbound:{assembly.identifier}", body["structure_name"])
            self.assertEqual(body["description"]["identifier"], rule_body["description"]["places_feature"])
            self.assertEqual(f"aionbound:{assembly.identifier}.structure_feature_rule", rule_body["description"]["identifier"])
            filters = rule_body["conditions"]["minecraft:biome_filter"]["all_of"]
            self.assertIn({"test": "has_biome_tag", "operator": "==", "value": "overworld"}, filters)
            self.assertIn({"test": "has_biome_tag", "operator": "!=", "value": "ocean"}, filters)
            proxy = next(value["any_of"] for value in filters if "any_of" in value)
            self.assertEqual({"mountain", "mesa"}, {item["value"] for item in proxy})
            self.assertEqual(1, rule_body["distribution"]["iterations"])

    def test_rarity_is_distinct_conservative_and_not_whisperwood_copy(self):
        denominators = [item.denominator for item in author.ASSEMBLIES]
        self.assertEqual(len(denominators), len(set(denominators)))
        self.assertTrue(all(value >= 640 for value in denominators))
        self.assertTrue(author.WHISPERWOOD_DENOMINATORS.isdisjoint(denominators))
        forge = next(item for item in author.ASSEMBLIES if item.identifier == "ember_forge")
        self.assertEqual(16384, forge.denominator)

    def test_ember_forge_uniqueness_is_explicitly_unproven(self):
        _outputs, manifest = author.expected_outputs()
        uniqueness = manifest["ember_forge_uniqueness"]
        self.assertEqual("UNPROVEN_NOT_ENFORCED_BY_FEATURE_RULES", uniqueness["status"])
        self.assertEqual("exceptionally rare 1:16384 feature-rule proxy", uniqueness["implementation"])
        self.assertNotIn("PROVEN", uniqueness["status"].replace("UNPROVEN", ""))

    def test_visual_models_are_not_inputs_and_deterministic_regeneration(self):
        first, manifest = author.expected_outputs()
        second, _ = author.expected_outputs()
        self.assertEqual(first, second)
        self.assertIn("design evidence only", manifest["visual_asset_boundary"])
        self.assertTrue(all(not path.suffix in {".bbmodel", ".png"} for path in first))


if __name__ == "__main__":
    unittest.main()
