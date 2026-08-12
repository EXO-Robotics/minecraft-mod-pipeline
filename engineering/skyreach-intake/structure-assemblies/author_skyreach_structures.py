#!/usr/bin/env python3
"""Deterministically author ten inert Skyreach block assemblies.

Packet 004 landmark models bind identity and silhouette intent only. The
little-endian Bedrock ``.mcstructure`` outputs are independently authored from
already-integrated full-cube blocks. They contain no entities, block-entity
NBT, containers, loot references, rewards, or encounter activation.
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
SOURCE_COMMIT = "252bb1441932fa5b55598494823b178bba0faab5"
SOURCE_TREE = "95fe1a93ec9951f51a2c19115c23f898d9b09931"


class NbtWriter:
    def __init__(self) -> None:
        self.parts: list[bytes] = []

    def u8(self, value: int) -> None: self.parts.append(struct.pack("<B", value))
    def i32(self, value: int) -> None: self.parts.append(struct.pack("<i", value))
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
    def finish(self) -> bytes: return b"".join(self.parts)


@dataclass(frozen=True)
class Assembly:
    identifier: str
    size: tuple[int, int, int]
    denominator: int
    terrain_role: str
    silhouette: str
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


def rope_bridge() -> Assembly:
    l = Layout((25, 10, 7))
    for x in range(25):
        if x not in (7, 17):
            l.fill((x, 4, 2), (x, 4, 4), "aionbound:skyreach_planks")
        if x % 4 == 0:
            l.line_y(x, 4, 8, 1, "aionbound:rope_timber")
            l.line_y(x, 4, 8, 5, "aionbound:rope_timber")
    for z in (1, 5):
        l.line_x(0, 24, 8, z, "aionbound:skyreach_log")
    l.fill((0, 2, 1), (3, 3, 5), "aionbound:cliff_stone")
    l.fill((21, 2, 1), (24, 3, 5), "aionbound:cliff_stone")
    return Assembly("rope_bridge", l.size, 1184, "high shelf crossing proxy", "long suspended timber walk with paired rope rails and two wind gaps", l.blocks)


def broken_sky_path() -> Assembly:
    l = Layout((21, 8, 11))
    for x0, x1, z0, z1, y in ((0, 6, 2, 8, 3), (9, 13, 1, 6, 4), (16, 20, 4, 10, 2)):
        l.fill((x0, y, z0), (x1, y, z1), "aionbound:pale_shelf_stone")
        if x1 - x0 > 4:
            l.line_x(x0 + 1, x1 - 1, y + 1, (z0 + z1) // 2, "aionbound:wind_slate")
    for xyz in ((5, 4, 3), (10, 5, 5), (17, 3, 6), (19, 3, 8)):
        l.put(*xyz, "aionbound:sky_moss_block")
    return Assembly("broken_sky_path", l.size, 1696, "fractured ridge route proxy", "three offset stone path islands with a broken wind-slate centerline", l.blocks)


def cliff_outpost() -> Assembly:
    l = Layout((15, 13, 13))
    l.fill((1, 1, 1), (13, 2, 11), "aionbound:cliff_stone")
    l.fill((3, 3, 3), (11, 3, 9), "aionbound:skyreach_planks")
    for x, z in ((3, 3), (11, 3), (3, 9), (11, 9)):
        l.line_y(x, 4, 10, z, "aionbound:rope_timber")
    l.fill((2, 10, 2), (12, 10, 10), "aionbound:skyreach_wood")
    l.fill((4, 4, 4), (10, 7, 8), "aionbound:cloud_wool_block")
    l.fill((5, 4, 3), (9, 6, 3), "aionbound:skyreach_planks")
    return Assembly("cliff_outpost", l.size, 2272, "sheltered ledge proxy", "stone shelf carrying a four-post timber lookout and cloud-wool windbreak", l.blocks)


def cliff_beacon() -> Assembly:
    l = Layout((9, 18, 9))
    l.fill((1, 0, 1), (7, 1, 7), "aionbound:pale_shelf_stone")
    l.fill((3, 2, 3), (5, 13, 5), "aionbound:wind_slate")
    l.line_x(1, 7, 14, 4, "aionbound:rope_timber")
    l.line_z(4, 14, 1, 7, "aionbound:rope_timber")
    for x, z in ((1, 4), (7, 4), (4, 1), (4, 7)):
        l.line_y(x, 14, 16, z, "aionbound:cloud_wool_block")
    l.put(4, 17, 4, "aionbound:sky_moss_block")
    return Assembly("cliff_beacon", l.size, 2944, "exposed ridge sightline proxy", "needle beacon with cross-braced wind vanes and a moss-lit crown", l.blocks)


def observation_tower() -> Assembly:
    l = Layout((15, 24, 15))
    l.fill((1, 0, 1), (13, 1, 13), "aionbound:cliff_stone")
    for x, z in ((3, 3), (11, 3), (3, 11), (11, 11)):
        l.line_y(x, 2, 19, z, "aionbound:rope_timber")
    for y in (6, 12, 18):
        l.line_x(3, 11, y, 3, "aionbound:skyreach_log")
        l.line_x(3, 11, y, 11, "aionbound:skyreach_log")
        l.line_z(3, y, 3, 11, "aionbound:skyreach_log")
        l.line_z(11, y, 3, 11, "aionbound:skyreach_log")
    l.fill((2, 20, 2), (12, 20, 12), "aionbound:skyreach_planks")
    l.line_x(1, 13, 22, 7, "aionbound:wind_slate")
    l.line_z(7, 22, 1, 13, "aionbound:wind_slate")
    return Assembly("observation_tower", l.size, 3520, "highest local shelf proxy", "slender open timber tower with three brace rings and a crossed survey crown", l.blocks)


def nest_platform() -> Assembly:
    l = Layout((25, 9, 25))
    for radius, y, block in ((11, 1, "aionbound:cliff_stone"), (9, 2, "aionbound:rope_timber"), (7, 3, "aionbound:cloud_wool_block")):
        for x in range(12 - radius, 13 + radius):
            for z in range(12 - radius, 13 + radius):
                if (x - 12) ** 2 + (z - 12) ** 2 <= radius ** 2:
                    l.put(x, y, z, block)
    for x, z in ((4, 12), (20, 12), (12, 4), (12, 20)):
        l.line_y(x, 2, 7, z, "aionbound:rope_timber")
    l.fill((9, 4, 9), (15, 4, 15), "aionbound:sky_moss_block")
    return Assembly("nest_platform", l.size, 9472, "isolated summit shelf proxy", "broad concentric cliff nest with four tall perimeter spars", l.blocks)


def floating_ruin_floor() -> Assembly:
    l = Layout((19, 9, 17))
    for x in range(1, 18):
        for z in range(1, 16):
            if (x + 2 * z) % 11 not in (0, 1):
                l.put(x, 6, z, "aionbound:wind_slate" if (x + z) % 4 else "aionbound:pale_shelf_stone")
    l.fill((6, 3, 5), (12, 5, 11), "aionbound:cliff_stone")
    l.fill((8, 1, 7), (10, 2, 9), "aionbound:cliff_gravel")
    for x, z in ((2, 2), (16, 2), (2, 14), (16, 14)):
        l.line_y(x, 6, 8, z, "aionbound:rope_timber")
    return Assembly("floating_ruin_floor", l.size, 4576, "detached high shelf proxy", "fractured slate room-floor slab tapering to a narrow stone keel", l.blocks)


def ancient_sky_arch() -> Assembly:
    l = Layout((17, 20, 9))
    l.fill((1, 0, 1), (15, 1, 7), "aionbound:pale_shelf_stone")
    for x in (2, 3, 13, 14):
        l.line_y(x, 2, 15, 4, "aionbound:cliff_stone")
    for y, inset in ((15, 0), (16, 1), (17, 2), (18, 4)):
        l.line_x(2 + inset, 14 - inset, y, 4, "aionbound:wind_slate")
    l.line_x(6, 10, 19, 4, "aionbound:skyreach_log")
    return Assembly("ancient_sky_arch", l.size, 5408, "ridge threshold proxy", "twin heavy cliff piers carrying a stepped wind-slate arch", l.blocks)


def hanging_lift_frame() -> Assembly:
    l = Layout((13, 20, 11))
    l.fill((1, 0, 1), (11, 1, 9), "aionbound:cliff_stone")
    for x, z in ((2, 2), (10, 2), (2, 8), (10, 8)):
        l.line_y(x, 2, 17, z, "aionbound:rope_timber")
    l.line_x(2, 10, 18, 2, "aionbound:skyreach_log")
    l.line_x(2, 10, 18, 8, "aionbound:skyreach_log")
    l.line_z(2, 18, 2, 8, "aionbound:skyreach_log")
    l.line_z(10, 18, 2, 8, "aionbound:skyreach_log")
    l.fill((4, 8, 3), (8, 8, 7), "aionbound:skyreach_planks")
    l.line_y(4, 9, 17, 5, "aionbound:rope_timber")
    l.line_y(8, 9, 17, 5, "aionbound:rope_timber")
    return Assembly("hanging_lift_frame", l.size, 6848, "vertical cliff route proxy", "tall four-post hoist frame with a visibly suspended inert platform", l.blocks)


def wind_shrine() -> Assembly:
    l = Layout((17, 13, 17))
    l.fill((1, 0, 1), (15, 1, 15), "aionbound:pale_shelf_stone")
    l.fill((4, 2, 4), (12, 2, 12), "aionbound:wind_slate")
    l.fill((7, 3, 7), (9, 6, 9), "aionbound:cliff_stone")
    for dx, dz in ((0, -6), (6, 0), (0, 6), (-6, 0)):
        x, z = 8 + dx, 8 + dz
        l.line_y(x, 2, 9, z, "aionbound:rope_timber")
        l.put(x, 10, z, "aionbound:cloud_wool_block")
    l.line_x(2, 14, 11, 8, "aionbound:skyreach_log")
    l.line_z(8, 12, 2, 14, "aionbound:skyreach_log")
    return Assembly("wind_shrine", l.size, 8256, "open summit ritual proxy", "radial slate altar beneath four windspars and crossed skywood arms", l.blocks)


ASSEMBLIES = [
    rope_bridge(), broken_sky_path(), cliff_outpost(), cliff_beacon(), observation_tower(),
    nest_platform(), floating_ruin_floor(), ancient_sky_arch(), hanging_lift_frame(), wind_shrine(),
]


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
    n.compound("structure", lambda: _emit_structure(n, indices, palette))
    n.u8(0)
    return n.finish(), palette, indices


def _emit_structure(n: NbtWriter, indices: list[int], palette: list[str]) -> None:
    n.list_tag("block_indices", 9, [indices, [-1] * len(indices)], lambda layer: n.list_payload(3, layer, n.i32))
    n.list_tag("entities", 10, [], lambda _value: None)
    n.compound("palette", lambda: n.compound("default", lambda: _emit_palette(n, palette)))


def _emit_palette(n: NbtWriter, palette: list[str]) -> None:
    def entry(name: str) -> None:
        n.string_tag("name", name)
        n.compound("states", lambda: None)
        n.int_tag("version", 18168865)
        n.u8(0)
    n.list_tag("block_palette", 10, palette, entry)
    n.compound("block_position_data", lambda: None)


def feature_document(assembly: Assembly) -> dict:
    return {
        "format_version": "1.13.0",
        "minecraft:structure_template_feature": {
            "description": {"identifier": f"aionbound:{assembly.identifier}_structure_feature"},
            "structure_name": f"aionbound:{assembly.identifier}",
            "adjustment_radius": 5 if max(assembly.size) >= 20 else 4,
            "facing_direction": "random",
            "constraints": {
                "grounded": {},
                "unburied": {},
                "block_intersection": {"block_allowlist": [
                    "minecraft:air", "minecraft:stone", "minecraft:dirt", "minecraft:grass_block",
                    "minecraft:gravel", "minecraft:snow", "minecraft:snow_layer",
                    "aionbound:cliff_stone", "aionbound:cliff_gravel",
                    "aionbound:pale_shelf_stone", "aionbound:sky_moss_block",
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
                        {"test": "has_biome_tag", "operator": "==", "value": "hills"},
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
    return (json.dumps(value, indent=2) + "\n").encode()


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
            "scatter": {"numerator": 1, "denominator": assembly.denominator},
            "expected_attempts_per_256_chunks_before_filters": round(256 / assembly.denominator, 6),
            "terrain_role": assembly.terrain_role,
            "silhouette": assembly.silhouette,
            "structure_path": str(structure_path.relative_to(REPO)),
            "feature_path": str(feature_path.relative_to(REPO)),
            "feature_rule_path": str(rule_path.relative_to(REPO)),
            "structure_sha256": hashlib.sha256(structure_bytes).hexdigest(),
            "block_position_data": "EMPTY_NO_BLOCK_ENTITY_NBT",
        })
    total_attempts = sum(256 / a.denominator for a in ASSEMBLIES)
    manifest = {
        "schema": "aionbound.wave1.skyreach.structure_assemblies.v1",
        "status": "PASS_STATIC_INERT_STRUCTURE_AUTHORING",
        "integration_authority": {"commit": SOURCE_COMMIT, "tree": SOURCE_TREE},
        "authority": "engineering/skyreach-intake/authority/SKYREACH_VERTICAL_INTAKE_MAP.json",
        "proof_boundary": "STATIC_SOURCE_AND_AUTHORED_BYTES_ONLY; NO_MCSTRUCTURE_CLIENT_LOAD, BDS, TERRAIN_AFFINITY, LOOT, ENCOUNTER, OR CANDIDATE CLAIM",
        "visual_asset_boundary": "Packet landmark exports bind identity only and are not serialized into or proof of these independently authored block assemblies",
        "inert_policy": "No container blocks, entities, block-entity NBT, loot paths, rewards, seals, encounter activation, or script bindings",
        "placement_policy": "One scatter trial per selected chunk with overworld non-ocean mountain-or-hills proxies; denominators are Skyreach-specific and bounded for console-first density",
        "aggregate_expected_attempts_per_256_chunks_before_filters": round(total_attempts, 6),
        "deferred": ["W1-001-SR", "W1-003-STORM-NEST", "W1-004-SR", "W1-CREATIVE-005"],
        "assemblies": records,
    }
    outputs[OUT / "SKYREACH_STRUCTURE_ASSEMBLIES.json"] = json_bytes(manifest)
    return outputs, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs, _ = expected_outputs()
    mismatches = []
    for path, data in outputs.items():
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
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
