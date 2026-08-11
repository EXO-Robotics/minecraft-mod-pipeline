#!/usr/bin/env python3
"""Deterministically author ten inert block-built Ashen assemblies.

The lane emits structure bytes plus stable feature registrations. Anchors are
ordinary barrel, lodestone, or lectern blocks with no block-entity payload,
loot table, reward identity, encounter activation, entity, or script binding.
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
SOURCE_COMMIT = "fce314f2251f9e9eb0cb9a1c2b8310d90a8a7c6c"
SOURCE_TREE = "c059ca23dadb7d19ac471848e910bfd28a55caa5"
WHISPERWOOD_DENOMINATORS = {384, 512, 768, 1536, 2048, 4096}


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
        for value in values: emit(value)

    def list_payload(self, tag_type: int, values: list, emit: Callable) -> None:
        self.u8(tag_type)
        self.i32(len(values))
        for value in values: emit(value)

    def compound(self, name: str, emit: Callable[[], None]) -> None:
        self.head(10, name)
        emit()
        self.u8(0)

    def finish(self) -> bytes: return b"".join(self.parts)


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


def anchor(anchor_id: str, kind: str, xyz: tuple[int, int, int], block: str, purpose: str) -> dict:
    return {
        "anchor_id": anchor_id,
        "kind": kind,
        "coordinate": list(xyz),
        "expected_block": block,
        "purpose": purpose,
        "binding": "RESERVED_INERT_RUNTIME_HANDOFF",
        "block_entity_nbt": "OMITTED",
    }


def fire_totem() -> Assembly:
    l = Layout((9, 12, 9))
    l.fill((2, 0, 2), (6, 0, 6), "aionbound:ash_soil")
    l.fill((3, 1, 3), (5, 2, 5), "aionbound:basalt_brick")
    l.line_y(4, 3, 10, 4, "aionbound:basalt_pillar")
    for y, reach in ((4, 2), (7, 3), (9, 2)):
        l.line_x(4 - reach, 4 + reach, y, 4, "aionbound:ember_vent_stone")
    l.put(3, 8, 3, "minecraft:magma_block")
    l.put(5, 8, 3, "minecraft:magma_block")
    l.put(4, 11, 4, "aionbound:fire_bloom")
    l.put(4, 1, 7, "minecraft:lectern")
    return Assembly("fire_totem", l.size, "uncommon_cluster", 640, "open ash shelf prayer cluster", "forked ember-stone idol with offset heat eyes", [anchor("fire_totem_prayer", "journal", (4, 1, 7), "minecraft:lectern", "inert First Fire text handoff")], l.blocks)


def burned_camp() -> Assembly:
    l = Layout((13, 6, 11))
    l.fill((1, 0, 1), (11, 0, 9), "aionbound:ash_soil")
    l.fill((3, 1, 2), (9, 1, 4), "aionbound:char_planks")
    for x, z in ((3, 2), (9, 2), (3, 4), (9, 4)):
        l.line_y(x, 2, 4, z, "aionbound:ash_log")
    l.line_x(2, 10, 5, 3, "minecraft:blackstone")
    l.put(6, 1, 7, "minecraft:soul_campfire")
    l.put(5, 1, 7, "aionbound:ash_log")
    l.put(7, 1, 7, "aionbound:ash_log")
    l.put(10, 1, 6, "minecraft:barrel")
    l.put(2, 1, 6, "minecraft:lectern")
    l.put(9, 1, 8, "aionbound:char_shrub")
    return Assembly("burned_camp", l.size, "uncommon_edge", 896, "mountain-to-mesa edge onboarding", "collapsed black roof over a cold blue fire and split bedroll deck", [anchor("burned_camp_cache", "cache", (10, 1, 6), "minecraft:barrel", "inert future camp cache"), anchor("burned_camp_rumor", "journal", (2, 1, 6), "minecraft:lectern", "inert Crystal Marsh rumor handoff")], l.blocks)


def char_wagon() -> Assembly:
    l = Layout((15, 6, 9))
    l.fill((3, 2, 2), (10, 3, 6), "aionbound:char_planks")
    l.line_x(2, 12, 2, 4, "aionbound:ash_log")
    for x, z in ((4, 1), (4, 7), (10, 1), (10, 7)):
        l.fill((x, 1, z), (x, 3, z), "minecraft:polished_blackstone")
    l.line_x(11, 14, 2, 4, "aionbound:ash_log")
    l.line_y(3, 3, 5, 2, "aionbound:ash_log")
    l.line_y(3, 3, 5, 6, "aionbound:ash_log")
    l.line_z(3, 5, 2, 6, "aionbound:char_planks")
    l.put(11, 3, 4, "minecraft:barrel")
    l.put(7, 4, 4, "aionbound:cinder_gravel")
    return Assembly("char_wagon", l.size, "uncommon_route", 1152, "dry mesa route breadcrumb", "long charwood freight bed with paired blackstone wheels and raised gate", [anchor("char_wagon_trade", "cache", (11, 3, 4), "minecraft:barrel", "inert future trade-slag cache")], l.blocks)


def broken_bridge() -> Assembly:
    l = Layout((19, 8, 9))
    for x in list(range(0, 8)) + list(range(11, 19)):
        l.fill((x, 4, 3), (x, 4, 5), "aionbound:char_planks")
        if x % 2 == 0:
            l.put(x, 3, 2, "aionbound:basalt_pillar")
            l.put(x, 3, 6, "aionbound:basalt_pillar")
    for x in (0, 1, 17, 18):
        l.line_y(x, 0, 3, 3, "aionbound:basalt_brick")
        l.line_y(x, 0, 3, 5, "aionbound:basalt_brick")
    l.line_x(7, 11, 2, 4, "aionbound:ash_log")
    l.put(3, 3, 4, "minecraft:lodestone")
    l.put(15, 4, 4, "minecraft:barrel")
    l.put(8, 5, 3, "aionbound:ember_vine")
    l.put(10, 5, 5, "aionbound:ember_vine")
    return Assembly("broken_bridge", l.size, "ravine_gated", 1408, "mountain cut traversal check", "two basalt-supported char decks separated by a three-block fracture", [anchor("broken_bridge_route", "interaction", (3, 3, 4), "minecraft:lodestone", "inert traversal marker"), anchor("broken_bridge_cache", "cache", (15, 4, 4), "minecraft:barrel", "inert future materials cache")], l.blocks)


def basalt_arch() -> Assembly:
    l = Layout((13, 13, 7))
    l.fill((1, 0, 1), (11, 1, 5), "aionbound:cinder_gravel")
    for x in (2, 3, 9, 10):
        l.line_y(x, 2, 9, 3, "aionbound:basalt_pillar")
    l.line_x(2, 10, 10, 3, "aionbound:basalt_brick")
    l.line_x(4, 8, 11, 3, "minecraft:polished_blackstone_bricks")
    l.put(6, 12, 3, "aionbound:ember_vent_stone")
    l.put(6, 1, 5, "minecraft:barrel")
    l.put(2, 10, 2, "aionbound:magma_moss")
    l.put(10, 10, 4, "aionbound:magma_moss")
    return Assembly("basalt_arch", l.size, "rare_landmark", 2304, "high saddle route spoiler", "twin four-pier basalt gateway capped by a single ember key", [anchor("basalt_arch_cache", "cache", (6, 1, 5), "minecraft:barrel", "inert future basalt-core cache")], l.blocks)


def ash_watchtower() -> Assembly:
    l = Layout((11, 18, 11))
    l.fill((1, 0, 1), (9, 1, 9), "aionbound:basalt_brick")
    for x, z in ((2, 2), (8, 2), (2, 8), (8, 8)):
        l.line_y(x, 2, 14, z, "aionbound:basalt_pillar")
    for y in (5, 10, 15):
        l.fill((2, y, 2), (8, y, 8), "aionbound:char_planks")
        for x, z in ((1, 1), (9, 1), (1, 9), (9, 9)):
            l.put(x, y, z, "aionbound:ember_vent_stone")
    l.line_x(1, 9, 16, 5, "aionbound:ash_log")
    l.line_z(5, 16, 1, 9, "aionbound:ash_log")
    l.put(5, 1, 5, "minecraft:lodestone")
    l.put(4, 10, 6, "minecraft:lectern")
    l.put(7, 10, 6, "minecraft:barrel")
    return Assembly("ash_watchtower", l.size, "rare_ridge", 2816, "exposed mountain ridge sightline", "four open basalt legs supporting three cross-braced charwood decks", [anchor("ash_watchtower_stamp", "interaction", (5, 1, 5), "minecraft:lodestone", "inert Codex sightline stamp"), anchor("ash_watchtower_notes", "journal", (4, 10, 6), "minecraft:lectern", "inert survey-note handoff"), anchor("ash_watchtower_cache", "cache", (7, 10, 6), "minecraft:barrel", "inert future ash-crystal cache")], l.blocks)


def ancient_kiln() -> Assembly:
    l = Layout((15, 11, 15))
    l.fill((1, 0, 1), (13, 1, 13), "aionbound:ash_soil")
    for y, inset in ((2, 2), (3, 2), (4, 3), (5, 3), (6, 4), (7, 4), (8, 5)):
        l.fill((inset, y, inset), (14 - inset, y, 14 - inset), "aionbound:basalt_brick")
    for y in range(3, 8):
        for x in range(5, 10):
            l.blocks.pop((x, y, 2 if y < 6 else 4), None)
    l.fill((5, 2, 5), (9, 2, 9), "minecraft:magma_block")
    l.put(7, 3, 7, "minecraft:lodestone")
    l.put(3, 2, 10, "minecraft:barrel")
    l.put(11, 2, 10, "minecraft:lectern")
    l.put(7, 9, 7, "aionbound:ember_vent_stone")
    return Assembly("ancient_kiln", l.size, "rare_kiln", 3328, "sheltered caldera bench", "stepped squat basalt kiln with open furnace throat and ember chimney cap", [anchor("ancient_kiln_hearth", "interaction", (7, 3, 7), "minecraft:lodestone", "inert kiln hearth handoff"), anchor("ancient_kiln_cache", "cache", (3, 2, 10), "minecraft:barrel", "inert future forge-material cache"), anchor("ancient_kiln_record", "journal", (11, 2, 10), "minecraft:lectern", "inert unfinished-tool record")], l.blocks)


def ember_forge() -> Assembly:
    l = Layout((23, 14, 23))
    l.fill((1, 0, 1), (21, 1, 21), "aionbound:basalt_brick")
    for inset, y in ((3, 2), (5, 3), (7, 4)):
        for x in range(inset, 23 - inset):
            l.put(x, y, inset, "aionbound:basalt_pillar")
            l.put(x, y, 22 - inset, "aionbound:basalt_pillar")
        for z in range(inset, 23 - inset):
            l.put(inset, y, z, "aionbound:basalt_pillar")
            l.put(22 - inset, y, z, "aionbound:basalt_pillar")
    for x, z in ((4, 4), (18, 4), (4, 18), (18, 18)):
        l.line_y(x, 2, 11, z, "aionbound:basalt_pillar")
        l.put(x, 12, z, "aionbound:ember_vent_stone")
    l.fill((8, 2, 8), (14, 2, 14), "minecraft:magma_block")
    for x, z in ((11, 5), (11, 17), (5, 11), (17, 11)):
        l.line_y(x, 3, 7, z, "aionbound:ash_log")
    l.put(11, 3, 11, "minecraft:lodestone")
    l.put(17, 3, 11, "minecraft:barrel")
    l.put(5, 3, 11, "minecraft:lectern")
    return Assembly("ember_forge", l.size, "exceptionally_rare_goal", 16384, "highlands goal proxy; exact realm uniqueness unproven", "large concentric basalt forge arena with four ember chimneys and a magma crucible", [anchor("ember_forge_arena", "encounter", (11, 3, 11), "minecraft:lodestone", "inert future Kiln Sky arena handoff"), anchor("ember_forge_cache", "cache", (17, 3, 11), "minecraft:barrel", "inert future post-clear forge cache"), anchor("ember_forge_record", "journal", (5, 3, 11), "minecraft:lectern", "inert forge record handoff")], l.blocks)


def lava_shrine() -> Assembly:
    l = Layout((11, 10, 13))
    l.fill((1, 0, 1), (9, 1, 11), "aionbound:cinder_gravel")
    for inset, y in ((2, 2), (3, 3), (4, 4)):
        l.fill((inset, y, inset + 1), (10 - inset, y, 12 - inset), "aionbound:basalt_brick")
    l.fill((4, 5, 5), (6, 5, 7), "minecraft:magma_block")
    for x, z in ((2, 3), (8, 3), (2, 9), (8, 9)):
        l.line_y(x, 2, 8, z, "aionbound:basalt_pillar")
        l.put(x, 9, z, "aionbound:fire_bloom")
    l.put(5, 4, 6, "minecraft:lodestone")
    l.put(5, 2, 10, "minecraft:lectern")
    return Assembly("lava_shrine", l.size, "rare_vent", 3584, "mesa vent and heat seam", "four-pillar basalt ritual court around a raised magma basin", [anchor("lava_shrine_altar", "interaction", (5, 4, 6), "minecraft:lodestone", "inert heat-ward altar handoff"), anchor("lava_shrine_liturgy", "journal", (5, 2, 10), "minecraft:lectern", "inert ritual-curio text handoff")], l.blocks)


def ash_cave() -> Assembly:
    l = Layout((17, 10, 15))
    l.fill((1, 0, 2), (15, 1, 14), "aionbound:ash_soil")
    l.fill((2, 2, 6), (14, 8, 14), "minecraft:blackstone")
    for y in range(2, 7):
        width = 4 if y < 5 else 3
        for x in range(8 - width, 9 + width):
            for z in range(6, 11):
                l.blocks.pop((x, y, z), None)
    for x in (2, 3, 13, 14):
        l.line_y(x, 2, 9, 6, "aionbound:basalt_pillar")
    l.line_x(2, 14, 9, 6, "aionbound:basalt_brick")
    l.put(8, 1, 11, "minecraft:lodestone")
    l.put(4, 2, 9, "minecraft:barrel")
    l.put(12, 2, 10, "aionbound:glow_root")
    l.put(7, 2, 13, "aionbound:magma_moss")
    return Assembly("ash_cave", l.size, "uncommon_face", 1024, "mountain or mesa face proxy", "broad blackstone mouth with asymmetric basalt ribs and a deep heat-marked chamber", [anchor("ash_cave_depth", "encounter", (8, 1, 11), "minecraft:lodestone", "inert future nest-depth handoff"), anchor("ash_cave_cache", "cache", (4, 2, 9), "minecraft:barrel", "inert future heatstone cache")], l.blocks)


ASSEMBLIES = [fire_totem(), burned_camp(), char_wagon(), broken_bridge(), basalt_arch(), ash_watchtower(), ancient_kiln(), ember_forge(), lava_shrine(), ash_cave()]
STATIC_CHEST_STRUCTURES = frozenset({"burned_camp", "char_wagon", "broken_bridge", "basalt_arch", "ash_watchtower", "ancient_kiln", "ash_cave"})
for _assembly in ASSEMBLIES:
    for _anchor in _assembly.anchors:
        if _assembly.identifier in STATIC_CHEST_STRUCTURES and _anchor["expected_block"] == "minecraft:barrel":
            _anchor["binding"] = "RATIFIED_W1_004_AH_STATIC_CHEST_TABLE"
            _anchor["block_entity_nbt"] = "LOOT_TABLE_PATH_ONLY"
            _anchor["loot_table"] = f"loot_tables/chests/ashen/{_assembly.identifier}.json"


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
        table = item.get("loot_table")
        if not table:
            continue
        x, y, z = item["coordinate"]
        flat_index = x + z * sx + y * sx * sz

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


def feature_document(assembly: Assembly) -> dict:
    return {
        "format_version": "1.13.0",
        "minecraft:structure_template_feature": {
            "description": {"identifier": f"aionbound:{assembly.identifier}_structure_feature"},
            "structure_name": f"aionbound:{assembly.identifier}",
            "adjustment_radius": 5 if max(assembly.size) >= 20 else (4 if max(assembly.size) >= 15 else 3),
            "facing_direction": "random",
            "constraints": {
                "grounded": {}, "unburied": {},
                "block_intersection": {"block_allowlist": [
                    "minecraft:air", "minecraft:grass_block", "minecraft:dirt", "minecraft:stone",
                    "minecraft:terracotta", "minecraft:red_sand", "minecraft:coarse_dirt",
                    "aionbound:ash_soil", "aionbound:cinder_gravel",
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
                    {"test": "has_biome_tag", "operator": "!=", "value": "ocean"},
                    {"any_of": [
                        {"test": "has_biome_tag", "operator": "==", "value": "mountain"},
                        {"test": "has_biome_tag", "operator": "==", "value": "mesa"},
                    ]},
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
        records.append({
            "id": assembly.identifier,
            "size": list(assembly.size),
            "volume": len(indices),
            "occupied_blocks": sum(index >= 0 for index in indices),
            "palette": palette,
            "rarity": assembly.rarity,
            "scatter": {"numerator": 1, "denominator": assembly.denominator},
            "expected_attempts_per_256_chunk_cell_before_filters": round(256 / assembly.denominator, 6),
            "terrain_role": assembly.terrain_role,
            "placement_implementation": "overworld non-ocean mountain-or-mesa surface proxy; exact regional topology remains unproven",
            "silhouette": assembly.silhouette,
            "anchors": assembly.anchors,
            "structure_path": str(structure_path.relative_to(REPO)),
            "feature_path": str(feature_path.relative_to(REPO)),
            "feature_rule_path": str(rule_path.relative_to(REPO)),
            "structure_sha256": hashlib.sha256(structure_bytes).hexdigest(),
            "block_position_data": "STATIC_LOOT_TABLE_PATH_ONLY" if assembly.identifier in STATIC_CHEST_STRUCTURES else "EMPTY_NO_BLOCK_ENTITY_NBT",
        })
    manifest = {
        "schema": "aionbound.wave1.ashen.structure_assemblies.v1",
        "integration_authority": {"commit": SOURCE_COMMIT, "tree": SOURCE_TREE},
        "authority": [
            {"path": "engineering/ashen-intake/authority/ASHEN_HIGHLANDS_VERTICAL_INTAKE_MAP.json", "sha256": "ffa63451feda80fb078f897e2cd8270e1c1e0b4928c17bbc0fdcd10b572ffc7b"},
            {"path": "engineering/ashen-intake/runtime-map/ASHEN_RUNTIME_IMPLEMENTATION_MAP.json", "sha256": "a54dbe5c440d128c75b2d30cd0db5927c850f9355f0baeba7dc5dbebb120ec52"},
            {"path": "engineering/authority/support-proposals/ashen/W1-004-AH.json", "sha256": "93736ff800b1c90c8a6547d84336a6650f8ae32750f262de8e460385a7a26889"},
        ],
        "proof_boundary": "STATIC_SOURCE_AND_AUTHORED_BYTES_ONLY; NO_MCSTRUCTURE_CLIENT_LOAD, BDS, TERRAIN_AFFINITY, LOOT, ENCOUNTER, OR CANDIDATE CLAIM",
        "visual_asset_boundary": "Packet and native Blockbench models are design evidence only and are not serialized into the block-built assembly bytes",
        "anchor_policy": "seven ordinary barrel anchors bind exact ratified Ashen chest-table paths; lodestone and lectern anchors remain inert; ember_forge arena cache remains empty and protected for valid-clear runtime population",
        "placement_policy": "one conservative attempt per selected chunk with overworld non-ocean mountain-or-mesa surface proxies; denominators are Ashen-specific and distinct from Whisperwood",
        "ember_forge_uniqueness": {
            "creative_obligation": "one_per_highlands_realm",
            "implementation": "exceptionally rare 1:16384 feature-rule proxy",
            "status": "UNPROVEN_NOT_ENFORCED_BY_FEATURE_RULES",
            "required_future_proof": "realm-level placement ownership or deterministic discovery registry",
        },
        "content_omissions": ["reward item NBT", "boss activation", "entities", "scripts", "static ash_drake_horn", "static ember_forge_core"],
        "assemblies": records,
    }
    outputs[OUT / "ASHEN_STRUCTURE_ASSEMBLIES.json"] = json_bytes(manifest)
    lines = [
        "# Ashen Structure Assemblies", "", "Status: **STATIC_AUTHORING_PASS_ONLY**", "",
        "Ten deterministic little-endian Bedrock structure templates are authored as distinct Ashen block-built silhouettes. Seven ordinary barrel anchors bind exact Ashen chest tables; the Ember Forge arena cache remains empty before a valid clear.", "",
        "| ID | Size | Occupied | Rarity / chance | Terrain role |", "|---|---:|---:|---|---|",
    ]
    for record in records:
        lines.append(f"| `{record['id']}` | `{'x'.join(map(str, record['size']))}` | {record['occupied_blocks']} | `{record['rarity']}` / `1:{record['scatter']['denominator']}` | {record['terrain_role']} |")
    lines += [
        "", "## Boundaries", "",
        "- Feature rules use stable `minecraft:structure_template_feature` with overworld, non-ocean, and mountain-or-mesa surface proxies.",
        "- `ember_forge` uses an exceptionally rare `1:16384` proxy. Feature rules cannot enforce or prove exactly one per highlands realm; that obligation remains open in the machine manifest.",
        "- Ordinary barrel anchors contain only exact LootTable path metadata. No structure contains reward items, boss activation, entities, or scripts.",
        "- The Ember Forge barrel contains no LootTable NBT and remains guarded for command-free post-clear population owned by the Kiln Sky service.",
        "- Packet/native visual models are evidence only and are not the assembly bytes.",
        "- No BDS, client load, terrain affinity, encounter, or candidate claim is made.", "",
    ]
    outputs[OUT / "ASHEN_STRUCTURE_ASSEMBLIES.md"] = ("\n".join(lines)).encode()
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
