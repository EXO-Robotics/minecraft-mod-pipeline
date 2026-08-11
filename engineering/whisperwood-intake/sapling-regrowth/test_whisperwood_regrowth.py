import importlib.util
import json
import struct
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("regrowth_author", HERE / "author_whisperwood_regrowth.py")
author = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = author
SPEC.loader.exec_module(author)


class Reader:
    def __init__(self, data: bytes): self.data, self.offset = data, 0
    def take(self, length):
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
            result = {}
            while True:
                subtype = self.u8()
                if subtype == 0: return result
                name = self.string()
                result[name] = self.payload(subtype)
        raise ValueError(f"unsupported tag {tag}")
    def root(self):
        self.offset = 0
        if self.u8() != 10 or self.string() != "": raise ValueError("not unnamed root")
        result = self.payload(10)
        if self.offset != len(self.data): raise ValueError("trailing bytes")
        return result


class RegrowthTests(unittest.TestCase):
    def test_exact_ratified_assembly_envelope(self):
        blocks = author.tree_blocks()
        self.assertEqual((7, 9, 7), author.SIZE)
        self.assertEqual(6, author.TRUNK_HEIGHT)
        self.assertEqual(author.PALETTE_ALLOWED, set(blocks.values()))
        self.assertTrue(all(0 <= xyz[i] < author.SIZE[i] for xyz in blocks for i in range(3)))
        self.assertEqual(
            ["aionbound:whisperwood_log"] * 6,
            [blocks[(3, y, 3)] for y in range(6)],
        )

    def test_structure_nbt_is_complete_and_palette_closed(self):
        data, palette, indices = author.encode_structure(author.tree_blocks())
        root = Reader(data).root()
        self.assertEqual(list(author.SIZE), root["size"])
        body = root["structure"]
        decoded_palette = [entry["name"] for entry in body["palette"]["default"]["block_palette"]]
        self.assertEqual(palette, decoded_palette)
        self.assertEqual(indices, body["block_indices"][0])
        self.assertTrue(all(index == -1 for index in body["block_indices"][1]))
        self.assertEqual([], body["entities"])

    def test_feature_binds_exact_internal_structure(self):
        outputs = author.expected_outputs()
        path = author.BP / "features/ww_sapling_growth_tree.structure_feature.json"
        body = json.loads(outputs[path])["minecraft:structure_template_feature"]
        self.assertEqual(author.FEATURE_ID, body["description"]["identifier"])
        self.assertEqual(author.STRUCTURE_ID, body["structure_name"])
        self.assertEqual("north", body["facing_direction"])

    def test_soil_filter_and_no_unregistered_runtime_component(self):
        document = json.loads((author.BP / "blocks/whisperwood_sapling.block.json").read_text())
        components = document["minecraft:block"]["components"]
        condition = components["minecraft:placement_filter"]["conditions"][0]
        self.assertEqual(["up"], condition["allowed_faces"])
        self.assertEqual(author.SUPPORTED_SOIL, condition["block_filter"])
        self.assertEqual(components["minecraft:tick"], {"interval_range": [14400, 36000], "looping": True})
        self.assertEqual(components["aionbound:whisperwood_sapling_regrowth"], {})

    def test_growth_interface_preserves_timing_retry_and_world_state_only(self):
        report = json.loads(author.expected_outputs()[HERE / "WHISPERWOOD_SAPLING_REGROWTH_REPORT.json"])
        contract = report["growth_contract"]
        self.assertEqual([14400, 36000], contract["natural_loaded_tick_interval"])
        self.assertEqual([12, 30], contract["loaded_minutes_at_20_tps"])
        self.assertIn("leave sapling unchanged", contract["retry"])
        self.assertIn("at most one early attempt", contract["bone_meal"])
        self.assertEqual("world block state only; no player, entity, scoreboard, or dynamic-property stamp", contract["persistence"])

    def test_ecology_density_is_computed_from_committed_rules(self):
        files = sorted((author.BP / "feature_rules").glob("ww_ecology_*.feature_rule.json"))
        files += sorted((author.BP / "feature_rules").glob("ww_prop_*.feature_rule.json"))
        density = 0.0
        for path in files:
            distribution = json.loads(path.read_text())["minecraft:feature_rules"]["distribution"]
            chance = distribution.get("scatter_chance", 1)
            chance_value = chance.get("numerator", 1) / chance.get("denominator", 1) if isinstance(chance, dict) else chance
            density += distribution["iterations"] * chance_value
        self.assertAlmostEqual(1.2408854166666666, density)
        self.assertLessEqual(density, 1.25)

    def test_deterministic_outputs(self):
        self.assertEqual(author.expected_outputs(), author.expected_outputs())


if __name__ == "__main__":
    unittest.main()
