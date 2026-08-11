import importlib.util
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("author", HERE / "author_whisperwood_structures.py")
author = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = author
SPEC.loader.exec_module(author)


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def take(self, length: int) -> bytes:
        result = self.data[self.offset:self.offset + length]
        if len(result) != length:
            raise ValueError("truncated NBT")
        self.offset += length
        return result

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
        self.offset = 0
        if self.u8() != 10 or self.string() != "":
            raise ValueError("not an unnamed root compound")
        value = self.payload(10)
        if self.offset != len(self.data):
            raise ValueError("trailing bytes")
        return value


class StructureAssemblyTests(unittest.TestCase):
    def test_exact_eight_unique_structures(self):
        self.assertEqual(8, len(author.ASSEMBLIES))
        self.assertEqual(8, len({value.identifier for value in author.ASSEMBLIES}))
        self.assertEqual(8, len({value.size for value in author.ASSEMBLIES}))

    def test_little_endian_nbt_palette_indices_and_bounds(self):
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
            self.assertFalse(structure["palette"]["default"]["block_position_data"])

    def test_anchor_coordinates_are_inert_present_and_in_bounds(self):
        for assembly in author.ASSEMBLIES:
            for item in assembly.anchors:
                xyz = tuple(item["coordinate"])
                self.assertEqual("RESERVED_INERT_NO_CONTENT_OR_RUNTIME_BINDING", item["binding"])
                self.assertEqual(item["expected_block"], assembly.blocks[xyz])
                self.assertTrue(all(0 <= xyz[i] < assembly.size[i] for i in range(3)))

    def test_no_direct_props_or_unratified_reward_bindings(self):
        forbidden_blocks = {"aionbound:lantern_post", "aionbound:moss_cairn"}
        for assembly in author.ASSEMBLIES:
            self.assertTrue(forbidden_blocks.isdisjoint(assembly.blocks.values()))
        outputs, manifest = author.expected_outputs()
        encoded = json.dumps(manifest)
        self.assertNotIn("loot_tables/", encoded)
        self.assertNotIn("warden_sigil", encoded)
        self.assertNotIn("owl_token", encoded.lower())
        self.assertEqual(26, len(outputs))

    def test_custom_palette_identifier_closure(self):
        defined = set()
        for path in (author.BP / "blocks").glob("*.json"):
            document = json.loads(path.read_text())
            defined.add(document["minecraft:block"]["description"]["identifier"])
        for assembly in author.ASSEMBLIES:
            custom = {name for name in assembly.blocks.values() if name.startswith("aionbound:")}
            self.assertTrue(custom.issubset(defined), f"{assembly.identifier}: {sorted(custom - defined)}")

    def test_feature_and_rule_identifier_filename_closure(self):
        outputs, _manifest = author.expected_outputs()
        for assembly in author.ASSEMBLIES:
            feature_path = author.BP / "features" / f"{assembly.identifier}.structure_feature.json"
            rule_path = author.BP / "feature_rules" / f"{assembly.identifier}.structure_feature_rule.json"
            feature = json.loads(outputs[feature_path])
            rule = json.loads(outputs[rule_path])
            body = feature["minecraft:structure_template_feature"]
            rule_body = rule["minecraft:feature_rules"]
            self.assertEqual(f"aionbound:{assembly.identifier}_structure_feature", body["description"]["identifier"])
            self.assertEqual(f"aionbound:{assembly.identifier}", body["structure_name"])
            self.assertEqual(body["description"]["identifier"], rule_body["description"]["places_feature"])
            self.assertEqual(f"aionbound:{assembly.identifier}.structure_feature_rule", rule_body["description"]["identifier"])
            self.assertEqual(1, rule_body["distribution"]["iterations"])
            self.assertGreaterEqual(rule_body["distribution"]["scatter_chance"]["denominator"], 384)

    def test_deterministic_regeneration(self):
        first, _ = author.expected_outputs()
        second, _ = author.expected_outputs()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
