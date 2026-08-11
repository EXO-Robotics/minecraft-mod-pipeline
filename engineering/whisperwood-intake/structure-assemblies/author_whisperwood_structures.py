#!/usr/bin/env python3
"""Deterministically author the eight block-built Whisperwood assemblies.

Six approved barrel anchors carry ratified Whisperwood chest-table paths. The
Ancient Totem barrel is emitted empty for the runtime-gated Thorn Court cache.
Interaction, encounter, progression, and reward-entitlement behavior remains
outside this structure authoring lane.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


REPO = Path(__file__).resolve().parents[3]
BP = REPO / "behavior_pack"
OUT = Path(__file__).resolve().parent


class NbtWriter:
    def __init__(self) -> None:
        self.parts: list[bytes] = []

    def u8(self, value: int) -> None:
        self.parts.append(struct.pack("<B", value))

    def i32(self, value: int) -> None:
        self.parts.append(struct.pack("<i", value))

    def i64(self, value: int) -> None:
        self.parts.append(struct.pack("<q", value))

    def string_payload(self, value: str) -> None:
        encoded = value.encode("utf-8")
        self.parts.append(struct.pack("<H", len(encoded)))
        self.parts.append(encoded)

    def head(self, tag_type: int, name: str) -> None:
        self.u8(tag_type)
        self.string_payload(name)

    def int_tag(self, name: str, value: int) -> None:
        self.head(3, name)
        self.i32(value)

    def byte_tag(self, name: str, value: int) -> None:
        self.head(1, name)
        self.u8(value)

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


@dataclass
class Assembly:
    identifier: str
    size: tuple[int, int, int]
    rarity: str
    denominator: int
    terrain_role: str
    silhouette: str
    anchors: list[dict]
    blocks: dict[tuple[int, int, int], str]


class Layout:
    def __init__(self, size: tuple[int, int, int]) -> None:
        self.size = size
        self.blocks: dict[tuple[int, int, int], str] = {}

    def put(self, x: int, y: int, z: int, block: str) -> None:
        assert 0 <= x < self.size[0] and 0 <= y < self.size[1] and 0 <= z < self.size[2]
        self.blocks[(x, y, z)] = block

    def fill(self, a: tuple[int, int, int], b: tuple[int, int, int], block: str) -> None:
        for y in range(a[1], b[1] + 1):
            for z in range(a[2], b[2] + 1):
                for x in range(a[0], b[0] + 1):
                    self.put(x, y, z, block)

    def line_x(self, x0: int, x1: int, y: int, z: int, block: str) -> None:
        self.fill((x0, y, z), (x1, y, z), block)

    def line_y(self, x: int, y0: int, y1: int, z: int, block: str) -> None:
        self.fill((x, y0, z), (x, y1, z), block)

    def line_z(self, x: int, y: int, z0: int, z1: int, block: str) -> None:
        self.fill((x, y, z0), (x, y, z1), block)


def anchor(kind: str, xyz: tuple[int, int, int], block: str, purpose: str) -> dict:
    value = {
        "kind": kind,
        "coordinate": list(xyz),
        "expected_block": block,
        "purpose": purpose,
        "binding": "RESERVED_NON_LOOT_RUNTIME_HANDOFF",
    }
    if kind == "loot":
        value["binding"] = "RATIFIED_W1_004_WW_CH1_CHEST_TABLE"
    if kind == "arena_cache":
        value["binding"] = "RUNTIME_GATED_POST_CLEAR_CACHE_EMPTY_AT_STRUCTURE_LOAD"
    return value


def hunter_camp() -> Assembly:
    l = Layout((13, 7, 11))
    l.fill((2, 0, 2), (10, 0, 8), "aionbound:glow_moss")
    l.fill((3, 1, 2), (9, 1, 4), "aionbound:whisperwood_planks")
    for x, z in ((3, 2), (9, 2), (3, 4), (9, 4)):
        l.line_y(x, 2, 4, z, "aionbound:stripped_whisperwood_log")
    for y, inset in ((5, 0), (6, 2)):
        l.fill((3 + inset, y, 2), (9 - inset, y, 4), "aionbound:whisperwood_leaves")
    l.put(6, 1, 7, "minecraft:campfire")
    l.put(5, 1, 7, "minecraft:oak_log")
    l.put(7, 1, 7, "minecraft:oak_log")
    l.put(9, 2, 5, "minecraft:lantern")
    l.put(8, 2, 5, "minecraft:barrel")
    l.put(4, 2, 5, "minecraft:lectern")
    l.line_z(1, 1, 4, 7, "aionbound:whisperwood_roots")
    return Assembly("hunter_camp", l.size, "uncommon", 384, "local forest region cluster", "low leaf-roof ranger shelter around a fire ring", [anchor("loot", (8, 2, 5), "minecraft:barrel", "empty structure-loot handoff"), anchor("journal", (4, 2, 5), "minecraft:lectern", "future authored journal handoff")], l.blocks)


def broken_wagon() -> Assembly:
    l = Layout((11, 5, 7))
    l.fill((2, 1, 2), (7, 2, 4), "aionbound:whisperwood_planks")
    l.line_x(1, 8, 1, 3, "aionbound:stripped_whisperwood_log")
    for x, z in ((2, 1), (2, 5), (7, 1), (7, 5)):
        l.put(x, 1, z, "minecraft:blackstone")
        l.put(x, 2, z, "minecraft:blackstone")
    l.line_x(8, 10, 1, 3, "aionbound:whisperwood_roots")
    l.put(9, 2, 2, "aionbound:whisperwood_roots")
    l.put(8, 2, 3, "minecraft:barrel")
    l.put(6, 3, 2, "aionbound:briar_vine")
    l.put(3, 3, 4, "aionbound:whisper_fern")
    return Assembly("broken_wagon", l.size, "uncommon", 512, "forest road breadcrumb", "tilted open wagon bed with four dark wheels and a snapped root-grown shaft", [anchor("loot", (8, 2, 3), "minecraft:barrel", "empty structure-loot handoff")], l.blocks)


def root_bridge() -> Assembly:
    l = Layout((17, 7, 7))
    for x in range(17):
        curve = 4 if x in range(3, 14) else 3
        for z in range(2, 5):
            l.put(x, curve, z, "aionbound:whisperwood_roots" if z != 3 else "aionbound:whisperwood_wood")
    for x in (0, 1, 15, 16):
        l.line_y(x, 0, 3, 2, "aionbound:whisperwood_log")
        l.line_y(x, 0, 3, 4, "aionbound:whisperwood_log")
    for x in range(2, 15, 2):
        l.put(x, 5, 1, "aionbound:briar_vine")
        l.put(x, 5, 5, "aionbound:briar_vine")
    l.put(8, 1, 3, "minecraft:barrel")
    l.put(7, 2, 3, "aionbound:glow_moss")
    return Assembly("root_bridge", l.size, "uncommon_ravine", 768, "ravine traversal landmark", "two-block-wide arched living-root span with hanging briars and an under-span cache", [anchor("loot", (8, 1, 3), "minecraft:barrel", "empty structure-loot handoff")], l.blocks)


def owl_shrine() -> Assembly:
    l = Layout((11, 10, 11))
    for inset, y in ((0, 0), (1, 1), (2, 2)):
        l.fill((inset, y, inset), (10 - inset, y, 10 - inset), "minecraft:mossy_stone_bricks")
    l.fill((3, 3, 4), (7, 4, 7), "minecraft:chiseled_stone_bricks")
    l.line_y(3, 5, 8, 5, "aionbound:whisperwood_log")
    l.line_y(7, 5, 8, 5, "aionbound:whisperwood_log")
    l.put(3, 7, 5, "aionbound:glow_moss")
    l.put(7, 7, 5, "aionbound:glow_moss")
    l.put(4, 8, 5, "aionbound:whisperwood_leaves")
    l.put(6, 8, 5, "aionbound:whisperwood_leaves")
    l.put(5, 4, 5, "minecraft:lodestone")
    l.put(5, 3, 8, "minecraft:barrel")
    for x, z in ((2, 2), (8, 2), (2, 8), (8, 8)):
        l.put(x, 3, z, "aionbound:lantern_bloom")
    return Assembly("owl_shrine", l.size, "rare", 1536, "high-ground forest clearing", "stepped moss-stone dais beneath twin log ears and glowing owl eyes", [anchor("interaction", (5, 4, 5), "minecraft:lodestone", "future authored interaction handoff"), anchor("loot", (5, 3, 8), "minecraft:barrel", "empty structure-loot handoff")], l.blocks)


def forest_waystone() -> Assembly:
    l = Layout((9, 10, 9))
    for x, z in ((2, 2), (4, 1), (6, 2), (7, 4), (6, 6), (4, 7), (2, 6), (1, 4)):
        l.put(x, 0, z, "aionbound:whisperwood_roots")
    l.fill((3, 0, 3), (5, 1, 5), "minecraft:mossy_stone_bricks")
    l.line_y(4, 2, 8, 4, "minecraft:chiseled_stone_bricks")
    for y, x in ((3, 3), (5, 5), (7, 3)):
        l.put(x, y, 4, "aionbound:glow_moss")
    l.put(4, 2, 4, "minecraft:lodestone")
    l.put(4, 9, 4, "aionbound:root_flower")
    return Assembly("forest_waystone", l.size, "rare_expanse", 2048, "major forest expanse", "solitary circuit-carved waystone on an eight-point living-root compass", [anchor("activation", (4, 2, 4), "minecraft:lodestone", "future network-stamp and multiplayer meeting handoff")], l.blocks)


def hollow_cave_entrance() -> Assembly:
    l = Layout((13, 8, 11))
    l.fill((1, 0, 2), (11, 1, 10), "minecraft:mossy_cobblestone")
    l.fill((2, 2, 5), (10, 5, 10), "minecraft:stone")
    for x in range(4, 9):
        for y in range(2, 5):
            l.blocks.pop((x, y, 5), None)
            l.blocks.pop((x, y, 6), None)
    for x in (2, 3, 9, 10):
        l.line_y(x, 2, 6, 5, "aionbound:whisperwood_roots")
    l.line_x(2, 10, 6, 5, "aionbound:whisperwood_roots")
    l.put(3, 2, 7, "minecraft:barrel")
    l.put(9, 2, 7, "aionbound:glow_moss")
    l.put(5, 5, 7, "aionbound:briar_vine")
    l.put(7, 5, 8, "aionbound:briar_vine")
    l.put(6, 1, 8, "minecraft:lodestone")
    return Assembly("hollow_cave_entrance", l.size, "uncommon_face", 512, "cliff or giant-root face", "root-ribbed stone mouth descending toward a glow-moss-marked dark pocket", [anchor("loot", (3, 2, 7), "minecraft:barrel", "empty structure-loot handoff"), anchor("encounter", (6, 1, 8), "minecraft:lodestone", "future authored encounter handoff")], l.blocks)


def ancient_totem() -> Assembly:
    l = Layout((9, 13, 9))
    l.fill((1, 0, 1), (7, 0, 7), "aionbound:glow_moss")
    l.fill((3, 1, 3), (5, 9, 5), "aionbound:hollow_wood")
    for y, reach in ((4, 2), (7, 3), (10, 2)):
        l.line_x(4 - reach, 4 + reach, y, 4, "aionbound:whisperwood_roots")
    l.put(3, 6, 2, "aionbound:glow_moss")
    l.put(5, 6, 2, "aionbound:glow_moss")
    l.put(4, 10, 4, "minecraft:chiseled_stone_bricks")
    l.put(4, 11, 4, "aionbound:root_flower")
    l.put(4, 1, 4, "minecraft:lodestone")
    l.put(2, 1, 6, "minecraft:barrel")
    return Assembly("ancient_totem", l.size, "rare_deep", 2048, "deep Whisperwood core", "tall split-root idol with amber-like moss eyes and asymmetric binding arms", [anchor("interaction", (4, 1, 4), "minecraft:lodestone", "Thorn Court interaction handoff"), anchor("arena_cache", (2, 1, 6), "minecraft:barrel", "post-clear Thorn Court cache; empty and locked before valid clear")], l.blocks)


def fallen_giant_tree() -> Assembly:
    l = Layout((21, 8, 11))
    for x in range(2, 19):
        for y, z in ((2, 4), (2, 5), (2, 6), (3, 3), (3, 4), (3, 6), (3, 7), (4, 4), (4, 5), (4, 6)):
            l.put(x, y, z, "aionbound:whisperwood_log" if (y, z) != (3, 4) else "aionbound:hollow_wood")
    for x in range(5, 17):
        l.blocks.pop((x, 3, 5), None)
    for x, z in ((1, 2), (1, 8), (3, 1), (3, 9)):
        l.line_x(x, min(7, x + 4), 1, z, "aionbound:whisperwood_roots")
    for x in (17, 18, 19, 20):
        for y in range(3, 7):
            for z in range(2, 9):
                if (x + y + z) % 3 == 0:
                    l.put(x, y, z, "aionbound:whisperwood_leaves")
    l.put(12, 3, 5, "minecraft:barrel")
    l.put(15, 3, 5, "aionbound:glow_moss")
    l.put(6, 2, 5, "aionbound:mooncap_mushroom")
    return Assembly("fallen_giant_tree", l.size, "very_rare_wonder", 4096, "rare forest wonder event", "twenty-block fallen hollow trunk with exposed root fan and surviving crown", [anchor("loot", (12, 3, 5), "minecraft:barrel", "empty structure-loot handoff")], l.blocks)


ASSEMBLIES = [hunter_camp(), broken_wagon(), root_bridge(), owl_shrine(), forest_waystone(), hollow_cave_entrance(), ancient_totem(), fallen_giant_tree()]


def encode_structure(assembly: Assembly) -> tuple[bytes, list[str], list[int]]:
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
    n.compound("structure", lambda: _emit_structure_payload(n, indices, palette, assembly))
    n.u8(0)
    return n.finish(), palette, indices


def _emit_structure_payload(n: NbtWriter, indices: list[int], palette: list[str], assembly: Assembly) -> None:
    n.list_tag("block_indices", 9, [indices, [-1] * len(indices)], lambda layer: n.list_payload(3, layer, n.i32))
    n.list_tag("entities", 10, [], lambda _value: None)
    n.compound("palette", lambda: n.compound("default", lambda: _emit_palette(n, palette, assembly)))


def _emit_palette(n: NbtWriter, palette: list[str], assembly: Assembly) -> None:
    def entry(name: str) -> None:
        n.string_tag("name", name)
        n.compound("states", lambda: None)
        n.int_tag("version", 18168865)
        n.u8(0)

    n.list_tag("block_palette", 10, palette, entry)
    n.compound("block_position_data", lambda: _emit_block_position_data(n, assembly))


def _emit_block_position_data(n: NbtWriter, assembly: Assembly) -> None:
    sx, _sy, sz = assembly.size
    for item in assembly.anchors:
        if item["kind"] != "loot":
            continue
        x, y, z = item["coordinate"]
        flat_index = x + z * sx + y * sx * sz

        def block_entity() -> None:
            n.byte_tag("Findable", 0)
            n.string_tag("LootTable", f"loot_tables/chests/whisperwood/{assembly.identifier}.json")
            n.long_tag("LootTableSeed", 0)
            n.string_tag("id", "Barrel")
            n.byte_tag("isMovable", 1)
            n.int_tag("x", x)
            n.int_tag("y", y)
            n.int_tag("z", z)

        n.compound(str(flat_index), lambda: n.compound("block_entity_data", block_entity))


def feature_document(assembly: Assembly) -> dict:
    return {
        "format_version": "1.13.0",
        "minecraft:structure_template_feature": {
            "description": {"identifier": f"aionbound:{assembly.identifier}_structure_feature"},
            "structure_name": f"aionbound:{assembly.identifier}",
            "adjustment_radius": 3 if max(assembly.size) < 17 else 4,
            "facing_direction": "random",
            "constraints": {
                "grounded": {},
                "unburied": {},
                "block_intersection": {"block_allowlist": [
                    "minecraft:air", "minecraft:grass_block", "minecraft:dirt",
                    "minecraft:podzol", "minecraft:coarse_dirt", "minecraft:stone",
                    "aionbound:glow_moss", "aionbound:whisperwood_roots",
                ]},
            },
        },
    }


def rule_document(assembly: Assembly) -> dict:
    return {
        "format_version": "1.13.0",
        "minecraft:feature_rules": {
            "description": {
                "identifier": f"aionbound:{assembly.identifier}.structure_feature_rule",
                "places_feature": f"aionbound:{assembly.identifier}_structure_feature",
            },
            "conditions": {
                "placement_pass": "surface_pass",
                "minecraft:biome_filter": {"all_of": [
                    {"test": "has_biome_tag", "operator": "==", "value": "overworld"},
                    {"test": "has_biome_tag", "operator": "==", "value": "forest"},
                    {"test": "has_biome_tag", "operator": "!=", "value": "ocean"},
                ]},
            },
            "distribution": {
                "iterations": 1,
                "scatter_chance": {"numerator": 1, "denominator": assembly.denominator},
                "x": {"distribution": "uniform", "extent": [0, 15]},
                "y": "q.heightmap(v.worldx, v.worldz)",
                "z": {"distribution": "uniform", "extent": [0, 15]},
            },
        },
    }


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=False) + "\n").encode()


def expected_outputs() -> tuple[dict[Path, bytes], dict]:
    outputs: dict[Path, bytes] = {}
    records = []
    for assembly in ASSEMBLIES:
        structure_bytes, palette, indices = encode_structure(assembly)
        structure_path = BP / "structures" / "aionbound" / f"{assembly.identifier}.mcstructure"
        feature_path = BP / "features" / f"{assembly.identifier}.structure_feature.json"
        rule_path = BP / "feature_rules" / f"{assembly.identifier}.structure_feature_rule.json"
        outputs[structure_path] = structure_bytes
        outputs[feature_path] = json_bytes(feature_document(assembly))
        outputs[rule_path] = json_bytes(rule_document(assembly))
        occupied = sum(index >= 0 for index in indices)
        records.append({
            "id": assembly.identifier,
            "size": list(assembly.size),
            "volume": len(indices),
            "occupied_blocks": occupied,
            "palette": palette,
            "rarity": assembly.rarity,
            "scatter": {"numerator": 1, "denominator": assembly.denominator},
            "expected_attempts_per_256_chunk_cell_before_filters": round(256 / assembly.denominator, 6),
            "terrain_role": assembly.terrain_role,
            "placement_implementation": "overworld+forest surface proxy; exact terrain topology requires a later biome/terrain integration proof",
            "silhouette": assembly.silhouette,
            "anchors": assembly.anchors,
            "structure_path": str(structure_path.relative_to(REPO)),
            "feature_path": str(feature_path.relative_to(REPO)),
            "feature_rule_path": str(rule_path.relative_to(REPO)),
            "sha256": hashlib.sha256(structure_bytes).hexdigest(),
        })
    manifest = {
        "schema": "aionbound.wave1.whisperwood.structure_assemblies.v2",
        "authority": [
            {"path": "studio-prep/creative/05_structures/STRUCTURES_DESIGN.md", "sha256": "9e62ae9ba6c1da33b64ff0bfa4ac4799b083c6de995585424864d5cf2b0cb076"},
            {"path": "studio-prep/creative/06_world_gen/WORLD_GENERATION.md", "sha256": "bc18a1e1f73d6045ab7e583afe910ca13d4776d439c8f3dfb45dae5784372f4b"},
            {"path": "engineering/whisperwood-intake/structure-runtime/WHISPERWOOD_STRUCTURE_RUNTIME_MAP.json", "sha256": "55a3996d5ae247d85a1543205e55a845ba910a971d485b8cd5bb13912aa85b13"},
        ],
        "proof_boundary": "STATIC_AUTHORING_AND_PRE_CLEAR_CACHE_GATING_BYTES_ONLY; NO_BDS, CLIENT, LOADED_RUNTIME, TERRAIN_TOPOLOGY, OR CANDIDATE CLAIM",
        "direct_prop_dependency": "lantern_post and moss_cairn omitted from all eight assemblies",
        "loot_policy": "six ordinary barrel anchors bind W1-004-WW-CH1 chest tables; Ancient Totem barrel has no LootTable NBT and is runtime-gated for post-clear Thorn Court cache population; no chapter trophy is stored in any structure chest",
        "placement_policy": "one attempt per selected chunk with forest-surface filters and conservative denominators; qualitative road/ravine/high-ground/face/deep-core affinity remains unproven",
        "concurrency_policy": "templates contain no entities, processors, or scheduled runtime; registry density does not authorize loaded-area concurrency growth",
        "assemblies": records,
    }
    outputs[OUT / "WHISPERWOOD_STRUCTURE_ASSEMBLIES.json"] = json_bytes(manifest)
    lines = [
        "# Whisperwood Structure Assemblies", "",
        "Status: **STATIC_AUTHORING_PASS_ONLY**", "",
        "Eight deterministic little-endian Bedrock structure templates are authored with distinct block-built silhouettes. Six ordinary barrel anchors bind ratified Whisperwood chest tables; the Ancient Totem barrel is empty at structure load for runtime-gated post-clear use. Chapter-trophy fulfillment, BDS load, and exact terrain affinity remain outside this receipt.", "",
        "Authority is hash-bound in \u0060WHISPERWOOD_STRUCTURE_ASSEMBLIES.json\u0060.", "",
        "| ID | Size | Occupied | Rarity / chance | Terrain role |", "|---|---:|---:|---|---|",
    ]
    for record in records:
        lines.append(f"| `{record['id']}` | `{'x'.join(map(str, record['size']))}` | {record['occupied_blocks']} | `{record['rarity']}` / `1:{record['scatter']['denominator']}` | {record['terrain_role']} |")
    lines += ["", "## Boundaries", "", "- The feature rules use stable `minecraft:structure_template_feature` plus `overworld` + `forest` surface filters.", "- Roads, ravines, high ground, cliff faces, deep core, and expanse spacing cannot be proven by these rules alone; the manifest records them as later terrain-integration obligations.", "- `lantern_post` and `moss_cairn` are not placed or substituted.", "- Six ordinary barrel block entities bind exact `loot_tables/chests/whisperwood/<structure>.json` paths. The Ancient Totem barrel at offset `(-2, 0, +2)` from its lodestone has no LootTable NBT and is reserved for runtime-gated post-clear Thorn Court cache population.", "- No structure chest contains the chapter trophy; trophy ownership remains in `thorn_court.js`.", "- Deterministic regeneration, NBT decoding, palette/index closure, bounds, IDs/filenames, and anchor coordinates are covered by the lane tests.", ""]
    outputs[OUT / "WHISPERWOOD_STRUCTURE_ASSEMBLIES.md"] = ("\n".join(lines)).encode()
    return outputs, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare committed outputs without writing")
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
