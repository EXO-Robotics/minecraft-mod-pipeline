import importlib.util
import json
import struct
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("crystal_structure_economy_author", HERE / "author_crystal_structure_economy.py")
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
        if len(value) != length:
            raise ValueError("truncated NBT")
        self.offset += length
        return value
    def u8(self): return struct.unpack("<B", self.take(1))[0]
    def i32(self): return struct.unpack("<i", self.take(4))[0]
    def i64(self): return struct.unpack("<q", self.take(8))[0]
    def string(self): return self.take(struct.unpack("<H", self.take(2))[0]).decode()
    def payload(self, tag):
        if tag == 1: return self.u8()
        if tag == 3: return self.i32()
        if tag == 4: return self.i64()
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
        if self.u8() != 10 or self.string() != "":
            raise ValueError("not unnamed root compound")
        value = self.payload(10)
        if self.offset != len(self.data):
            raise ValueError("trailing bytes")
        return value


class CrystalStructureEconomyTests(unittest.TestCase):
    def test_exact_seven_ordinary_bindings_and_three_inert_structures(self):
        self.assertEqual(7, len(author.STATIC_BINDINGS))
        self.assertEqual({"marsh_totem", "sunken_shrine"}, author.STRUCTURES_WITHOUT_APPROVED_CHEST)
        self.assertEqual("deep_pool_entrance", author.PROTECTED_STRUCTURE)
        all_ids = {item.identifier for item in author.assembly_author.ASSEMBLIES}
        self.assertEqual(all_ids, set(author.STATIC_BINDINGS) | author.STRUCTURES_WITHOUT_APPROVED_CHEST | {author.PROTECTED_STRUCTURE})

    def test_only_exact_barrel_position_data_is_added(self):
        for assembly in author.assembly_author.ASSEMBLIES:
            encoded, palette, indices = author.encode_structure(assembly)
            predecessor, predecessor_palette, predecessor_indices = author.assembly_author.encode_structure(assembly)
            self.assertEqual(predecessor_palette, palette)
            self.assertEqual(predecessor_indices, indices)
            root = Reader(encoded).root()
            predecessor_root = Reader(predecessor).root()
            self.assertEqual(root["size"], predecessor_root["size"])
            self.assertEqual(root["structure"]["block_indices"], predecessor_root["structure"]["block_indices"])
            self.assertEqual(root["structure"]["palette"]["default"]["block_palette"], predecessor_root["structure"]["palette"]["default"]["block_palette"])
            position_data = root["structure"]["palette"]["default"]["block_position_data"]
            anchor = author.approved_anchor(assembly)
            if anchor is None:
                self.assertEqual({}, position_data, assembly.identifier)
                self.assertEqual(predecessor, encoded, assembly.identifier)
                continue
            x, y, z = anchor["coordinate"]
            flat = str(x + z * assembly.size[0] + y * assembly.size[0] * assembly.size[2])
            self.assertEqual({flat}, set(position_data))
            block_entity = position_data[flat]["block_entity_data"]
            self.assertEqual("Barrel", block_entity["id"])
            self.assertEqual(f"loot_tables/chests/crystal/{assembly.identifier}.json", block_entity["LootTable"])
            self.assertEqual(0, block_entity["LootTableSeed"])
            self.assertEqual([x, y, z], [block_entity["x"], block_entity["y"], block_entity["z"]])

    def test_manifest_anchor_and_cardinal_rotation_closure(self):
        predecessor = json.loads(author.ASSEMBLY_MANIFEST.read_text())
        manifest_by_id = {item["id"]: item for item in predecessor["assemblies"]}
        for assembly in author.assembly_author.ASSEMBLIES:
            self.assertEqual(assembly.anchors, manifest_by_id[assembly.identifier]["anchors"])
            anchor = author.approved_anchor(assembly)
            if anchor is None:
                continue
            xyz = tuple(anchor["coordinate"])
            self.assertEqual("minecraft:barrel", assembly.blocks[xyz])
            rotations = [author.rotated_coordinate(assembly.size, anchor["coordinate"], turns) for turns in range(4)]
            self.assertEqual(4, len(set((tuple(size), tuple(coordinate)) for size, coordinate in rotations)))
            for size, coordinate in rotations:
                self.assertTrue(all(0 <= coordinate[index] < size[index] for index in range(3)))

    def test_ordinary_tables_exist_close_and_never_contain_seal(self):
        defined = set()
        for directory, key in ((author.BP / "items", "minecraft:item"), (author.BP / "blocks", "minecraft:block")):
            for path in directory.glob("*.json"):
                defined.add(json.loads(path.read_text())[key]["description"]["identifier"])
        for structure in author.STATIC_BINDINGS:
            table = author.BP / "loot_tables" / "chests" / "crystal" / f"{structure}.json"
            self.assertTrue(table.is_file(), table)
            identities = set(author.table_identities(table))
            self.assertTrue(identities.issubset(defined), sorted(identities - defined))
            self.assertTrue(author.FORBIDDEN_STATIC_IDENTITIES.isdisjoint(identities))
            text = table.read_text()
            self.assertNotIn("marsh_wight_mask", text)
            self.assertNotIn("seal_credit", text)

    def test_pearl_depths_cache_is_empty_and_arena_table_is_not_static(self):
        assembly = next(item for item in author.assembly_author.ASSEMBLIES if item.identifier == author.PROTECTED_STRUCTURE)
        cache = next(item for item in assembly.anchors if item["anchor_id"] == author.PROTECTED_ANCHOR)
        self.assertEqual("minecraft:barrel", assembly.blocks[tuple(cache["coordinate"])])
        root = Reader(author.encode_structure(assembly)[0]).root()
        self.assertEqual({}, root["structure"]["palette"]["default"]["block_position_data"])
        self.assertNotIn(b"LootTable", author.encode_structure(assembly)[0])
        self.assertNotIn("pearl_depths", author.STATIC_BINDINGS)

    def test_deterministic_outputs_and_proof_boundary(self):
        first, manifest = author.expected_outputs()
        second, _ = author.expected_outputs()
        self.assertEqual(first, second)
        self.assertEqual(12, len(first))
        self.assertEqual(7, manifest["ordinary_static_bindings"])
        self.assertFalse(manifest["protected_pearl_depths_cache"]["static_loot_binding"])
        self.assertIn("NO BDS", manifest["proof_boundary"])
        self.assertFalse(any("features/" in str(path) or "feature_rules/" in str(path) for path in first))


if __name__ == "__main__":
    unittest.main()
