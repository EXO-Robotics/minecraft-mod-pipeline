#!/usr/bin/env python3
"""Bind ratified Crystal Marsh structure loot without changing assembly geometry.

The predecessor structure-assembly source remains the geometry authority. This
post-ratification author emits the same palette and block-index layers, adding
only standard Bedrock barrel block-entity data at the seven approved ordinary
cache anchors. Pearl Depths and structures without an approved chest identity
remain byte-inert at their anchors.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path
from typing import Callable


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BP = REPO / "behavior_pack"
ASSEMBLY_DIR = HERE.parent / "structure-assemblies"
ASSEMBLY_SOURCE = ASSEMBLY_DIR / "author_crystal_marsh_structures.py"
ASSEMBLY_MANIFEST = ASSEMBLY_DIR / "CRYSTAL_MARSH_STRUCTURE_ASSEMBLIES.json"
SOURCE_COMMIT = "d8974fee959f0f15a8a212364a38d285e38078a5"
SOURCE_TREE = "35a07b3a82e161e43bc03f8bdbf6929902fc2297"
RATIFIED_AUTHORITY = ["W1-001-CM", "W1-004-CM"]
FORBIDDEN_STATIC_IDENTITIES = {
    "aionbound:marsh_wight_mask",
}

SPEC = importlib.util.spec_from_file_location("crystal_assembly_for_structure_economy", ASSEMBLY_SOURCE)
assembly_author = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = assembly_author
SPEC.loader.exec_module(assembly_author)


STATIC_BINDINGS = {
    "flooded_dock": "flooded_dock_cache",
    "ancient_boat": "ancient_boat_locker",
    "marsh_broken_bridge": "marsh_bridge_cache",
    "pearl_cairn": "pearl_cairn_cache",
    "crystal_arch": "crystal_arch_cache",
    "crystal_obelisk": "crystal_obelisk_cache",
    "ruined_observatory": "ruined_observatory_cache",
}
STRUCTURES_WITHOUT_APPROVED_CHEST = {"marsh_totem", "sunken_shrine"}
PROTECTED_STRUCTURE = "deep_pool_entrance"
PROTECTED_ANCHOR = "deep_pool_cache"


class NbtWriter:
    def __init__(self) -> None:
        self.parts: list[bytes] = []

    def u8(self, value: int) -> None: self.parts.append(struct.pack("<B", value))
    def i32(self, value: int) -> None: self.parts.append(struct.pack("<i", value))
    def i64(self, value: int) -> None: self.parts.append(struct.pack("<q", value))
    def string_payload(self, value: str) -> None:
        encoded = value.encode("utf-8")
        self.parts.append(struct.pack("<H", len(encoded)))
        self.parts.append(encoded)
    def head(self, tag_type: int, name: str) -> None:
        self.u8(tag_type)
        self.string_payload(name)
    def byte_tag(self, name: str, value: int) -> None:
        self.head(1, name)
        self.u8(value)
    def int_tag(self, name: str, value: int) -> None:
        self.head(3, name)
        self.i32(value)
    def long_tag(self, name: str, value: int) -> None:
        self.head(4, name)
        self.i64(value)
    def string_tag(self, name: str, value: str) -> None:
        self.head(8, name)
        self.string_payload(value)
    def list_tag(self, name: str, tag_type: int, values: list, emit: Callable) -> None:
        self.head(9, name)
        self.u8(tag_type)
        self.i32(len(values))
        for value in values:
            emit(value)
    def list_payload(self, tag_type: int, values: list, emit: Callable) -> None:
        self.u8(tag_type)
        self.i32(len(values))
        for value in values:
            emit(value)
    def compound(self, name: str, emit: Callable[[], None]) -> None:
        self.head(10, name)
        emit()
        self.u8(0)
    def finish(self) -> bytes:
        return b"".join(self.parts)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def approved_anchor(assembly):
    anchor_id = STATIC_BINDINGS.get(assembly.identifier)
    if anchor_id is None:
        return None
    matches = [item for item in assembly.anchors if item["anchor_id"] == anchor_id]
    if len(matches) != 1:
        raise ValueError(f"{assembly.identifier}: expected one exact anchor {anchor_id}")
    item = matches[0]
    if item["expected_block"] != "minecraft:barrel" or item["kind"] != "cache":
        raise ValueError(f"{assembly.identifier}: approved anchor is not a cache barrel")
    return item


def encode_structure(assembly) -> tuple[bytes, list[str], list[int]]:
    palette = sorted(set(assembly.blocks.values()))
    palette_index = {name: index for index, name in enumerate(palette)}
    sx, sy, sz = assembly.size
    indices = [-1] * (sx * sy * sz)
    for (x, y, z), name in assembly.blocks.items():
        indices[x + z * sx + y * sx * sz] = palette_index[name]

    n = NbtWriter()
    n.head(10, "")
    n.int_tag("format_version", 1)
    n.list_tag("size", 3, list(assembly.size), n.i32)
    n.list_tag("structure_world_origin", 3, [0, 0, 0], n.i32)
    n.compound("structure", lambda: emit_structure(n, assembly, indices, palette))
    n.u8(0)
    return n.finish(), palette, indices


def emit_structure(n: NbtWriter, assembly, indices: list[int], palette: list[str]) -> None:
    n.list_tag("block_indices", 9, [indices, [-1] * len(indices)], lambda layer: n.list_payload(3, layer, n.i32))
    n.list_tag("entities", 10, [], lambda _value: None)
    n.compound("palette", lambda: n.compound("default", lambda: emit_palette(n, assembly, palette)))


def emit_palette(n: NbtWriter, assembly, palette: list[str]) -> None:
    def entry(name: str) -> None:
        n.string_tag("name", name)
        n.compound("states", lambda: None)
        n.int_tag("version", 18168865)
        n.u8(0)

    n.list_tag("block_palette", 10, palette, entry)
    n.compound("block_position_data", lambda: emit_block_position_data(n, assembly))


def emit_block_position_data(n: NbtWriter, assembly) -> None:
    item = approved_anchor(assembly)
    if item is None:
        return
    x, y, z = item["coordinate"]
    sx, _sy, sz = assembly.size
    flat_index = x + z * sx + y * sx * sz
    table = f"loot_tables/chests/crystal/{assembly.identifier}.json"

    def block_entity() -> None:
        n.byte_tag("Findable", 0)
        n.string_tag("LootTable", table)
        n.long_tag("LootTableSeed", 0)
        n.string_tag("id", "Barrel")
        n.byte_tag("isMovable", 1)
        n.int_tag("x", x)
        n.int_tag("y", y)
        n.int_tag("z", z)

    n.compound(str(flat_index), lambda: n.compound("block_entity_data", block_entity))


def rotated_coordinate(size: tuple[int, int, int], coordinate: list[int], quarter_turns: int) -> tuple[list[int], list[int]]:
    sx, sy, sz = size
    x, y, z = coordinate
    turns = quarter_turns % 4
    if turns == 0:
        return [sx, sy, sz], [x, y, z]
    if turns == 1:
        return [sz, sy, sx], [sz - 1 - z, y, x]
    if turns == 2:
        return [sx, sy, sz], [sx - 1 - x, y, sz - 1 - z]
    return [sz, sy, sx], [z, y, sx - 1 - x]


def table_identities(path: Path) -> list[str]:
    document = json.loads(path.read_text())
    names: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("name"), str):
                names.add(value["name"])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(document)
    return sorted(names)


def expected_outputs() -> tuple[dict[Path, bytes], dict]:
    predecessor_manifest = json.loads(ASSEMBLY_MANIFEST.read_text())
    manifest_by_id = {item["id"]: item for item in predecessor_manifest["assemblies"]}
    outputs: dict[Path, bytes] = {}
    records = []
    for assembly in assembly_author.ASSEMBLIES:
        if assembly.identifier not in manifest_by_id:
            raise ValueError(f"missing predecessor manifest row: {assembly.identifier}")
        if assembly.anchors != manifest_by_id[assembly.identifier]["anchors"]:
            raise ValueError(f"predecessor anchor manifest drift: {assembly.identifier}")
        data, palette, indices = encode_structure(assembly)
        predecessor_data, predecessor_palette, predecessor_indices = assembly_author.encode_structure(assembly)
        if palette != predecessor_palette or indices != predecessor_indices:
            raise ValueError(f"geometry drift: {assembly.identifier}")
        path = BP / "structures" / "aionbound" / f"{assembly.identifier}.mcstructure"
        feature_path = BP / "features" / f"{assembly.identifier}.structure_feature.json"
        feature_rule_path = BP / "feature_rules" / f"{assembly.identifier}.structure_feature_rule.json"
        outputs[path] = data
        item = approved_anchor(assembly)
        loot_path = None
        identities: list[str] = []
        if item is not None:
            loot_path = f"loot_tables/chests/crystal/{assembly.identifier}.json"
            table_path = BP / loot_path
            if not table_path.is_file():
                raise ValueError(f"missing approved loot table: {loot_path}")
            identities = table_identities(table_path)
            forbidden = FORBIDDEN_STATIC_IDENTITIES.intersection(identities)
            if forbidden:
                raise ValueError(f"forbidden static identity in {loot_path}: {sorted(forbidden)}")
        rotations = []
        for turns in range(4):
            if item is None:
                break
            rotated_size, rotated_anchor = rotated_coordinate(assembly.size, item["coordinate"], turns)
            rotations.append({"quarter_turns": turns, "size": rotated_size, "anchor": rotated_anchor})
        records.append({
            "structure": assembly.identifier,
            "structure_path": str(path.relative_to(REPO)),
            "feature_path": str(feature_path.relative_to(REPO)),
            "feature_sha256_unchanged": sha256_bytes(feature_path.read_bytes()),
            "feature_rule_path": str(feature_rule_path.relative_to(REPO)),
            "feature_rule_sha256_unchanged": sha256_bytes(feature_rule_path.read_bytes()),
            "predecessor_structure_sha256": sha256_bytes(predecessor_data),
            "bound_structure_sha256": sha256_bytes(data),
            "geometry_equal": True,
            "approved_anchor": item["anchor_id"] if item else None,
            "anchor_coordinate": item["coordinate"] if item else None,
            "loot_table": loot_path,
            "loot_table_sha256": sha256_bytes((BP / loot_path).read_bytes()) if loot_path else None,
            "loot_identities": identities,
            "cardinal_rotation_closure": rotations,
            "binding": "STATIC_ORDINARY_LOOT_TABLE_NBT" if item else (
                "PROTECTED_EMPTY_SYNCHRONOUS_ENCOUNTER_CACHE" if assembly.identifier == PROTECTED_STRUCTURE
                else "INERT_NO_APPROVED_CHEST_IDENTITY"
            ),
        })

    manifest = {
        "schema": "aionbound.wave1.crystal_marsh.structure_economy_binding.v1",
        "status": "STATIC_STRUCTURE_LOOT_BINDING_PASS",
        "integration_authority": {"commit": SOURCE_COMMIT, "tree": SOURCE_TREE},
        "ratified_authority": RATIFIED_AUTHORITY,
        "predecessor_anchor_manifest": {
            "path": str(ASSEMBLY_MANIFEST.relative_to(REPO)),
            "sha256": sha256_bytes(ASSEMBLY_MANIFEST.read_bytes()),
        },
        "ordinary_static_bindings": len(STATIC_BINDINGS),
        "structures_without_approved_chest_identity": sorted(STRUCTURES_WITHOUT_APPROVED_CHEST),
        "protected_pearl_depths_cache": {
            "structure": PROTECTED_STRUCTURE,
            "anchor": PROTECTED_ANCHOR,
            "static_loot_binding": False,
            "pre_clear": "EMPTY_AND_SYNCHRONOUSLY_GUARDABLE",
            "terminal_owner": "PEARL_DEPTHS_SERVICE_ONLY",
            "marsh_wight_mask_static_grant": False,
        },
        "forbidden_static_identities": sorted(FORBIDDEN_STATIC_IDENTITIES),
        "assemblies": records,
        "unchanged_surfaces": [
            "assembly sizes, palettes, primary and secondary block-index layers",
            "feature JSON bytes",
            "feature-rule JSON bytes",
            "placement denominators and biome filters",
        ],
        "proof_boundary": "STATIC_EXACT_NBT_BINDING_AND_TARGETED_SEMANTIC_TESTS_ONLY; NO BDS, BUILD, CLIENT, ENCOUNTER_RUNTIME, REWARD, OR CANDIDATE CLAIM",
    }
    outputs[HERE / "CRYSTAL_STRUCTURE_ECONOMY_BINDING.json"] = json_bytes(manifest)
    lines = [
        "# Crystal Marsh Structure Economy Binding", "",
        "Status: **STATIC_STRUCTURE_LOOT_BINDING_PASS**", "",
        "Seven ordinary Crystal Marsh barrel anchors now carry exact ratified loot-table paths. `marsh_totem` and `sunken_shrine` remain inert because they have no approved chest identity. The `deep_pool_entrance` cache remains empty and synchronously guardable by the Pearl Depths encounter service.", "",
        "No structure table contains `aionbound:marsh_wight_mask`; no structure grants seal credit or encounter completion.", "",
        "| Structure | Binding | Anchor | Loot table |", "|---|---|---|---|",
    ]
    for record in records:
        lines.append(f"| `{record['structure']}` | `{record['binding']}` | `{record['approved_anchor'] or '-'}` | `{record['loot_table'] or '-'}` |")
    lines += ["", "The machine receipt records predecessor and bound hashes plus four-cardinal rotation closure for every bound anchor. Feature and feature-rule files are not outputs of this author.", "", "No BDS, build, client, encounter-runtime, reward, or candidate claim is made.", ""]
    outputs[HERE / "README.md"] = ("\n".join(lines)).encode()
    return outputs, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs, _manifest = expected_outputs()
    mismatches = []
    for path, data in outputs.items():
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                mismatches.append(str(path.relative_to(REPO)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if mismatches:
        print(json.dumps({"status": "FAIL", "mismatches": mismatches}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write", "outputs": len(outputs)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
