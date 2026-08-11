#!/usr/bin/env python3
"""Deterministically author ten inert Crystal Marsh block assemblies.

Packet landmark models inform identity only. The emitted little-endian
``.mcstructure`` files are independently authored block assemblies. Ordinary
barrel, lodestone, and lectern blocks are recorded as inert handoff anchors;
the structures contain no block-entity data, loot paths, reward identities,
entities, encounter activation, or script bindings.
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
SOURCE_COMMIT = "583279583cc27422c3d2ac6db52ad8a5310ec7dc"
SOURCE_TREE = "45e23d9303fae9a0b07ca23ee9bedea9bdb5b5bc"
PREVIOUS_ECOSYSTEM_DENOMINATORS = {
    384, 512, 640, 768, 896, 1024, 1152, 1408, 1536, 2048, 2304,
    2816, 3328, 3584, 4096, 16384,
}


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


def flooded_dock() -> Assembly:
    l = Layout((17, 6, 13))
    l.fill((1, 0, 1), (15, 0, 11), "aionbound:marsh_soil")
    l.fill((3, 1, 2), (13, 1, 5), "aionbound:flood_planks")
    l.fill((7, 1, 6), (9, 1, 11), "aionbound:flood_planks")
    for x, z in ((3, 2), (13, 2), (3, 5), (13, 5), (7, 11), (9, 11)):
        l.line_y(x, 1, 3, z, "aionbound:marsh_wood")
    l.put(12, 2, 3, "minecraft:barrel")
    l.put(4, 2, 4, "minecraft:lectern")
    return Assembly("flooded_dock", l.size, "uncommon_shore", 704, "swamp or river shore discovery proxy", "broad low landing with a long split-water pier", [anchor("flooded_dock_cache", "cache", (12, 2, 3), "minecraft:barrel", "future dock cache"), anchor("flooded_dock_record", "journal", (4, 2, 4), "minecraft:lectern", "future dock record")], l.blocks)


def ancient_boat() -> Assembly:
    l = Layout((19, 8, 9))
    l.fill((2, 1, 2), (16, 1, 6), "aionbound:flood_planks")
    for x in range(3, 16):
        l.put(x, 2, 1 if x % 2 else 2, "aionbound:marsh_wood")
        l.put(x, 2, 7 if x % 2 else 6, "aionbound:marsh_wood")
    l.line_y(9, 2, 7, 4, "aionbound:crystal_log")
    l.line_x(6, 12, 6, 4, "aionbound:flood_planks")
    l.put(14, 2, 4, "minecraft:barrel")
    return Assembly("ancient_boat", l.size, "rare_stranded", 1216, "stranded wetland shelf proxy", "long shallow floodwood hull with a broken crystal mast", [anchor("ancient_boat_locker", "cache", (14, 2, 4), "minecraft:barrel", "future boat locker")], l.blocks)


def marsh_broken_bridge() -> Assembly:
    l = Layout((21, 7, 7))
    for x in list(range(0, 8)) + list(range(12, 21)):
        l.fill((x, 3, 2), (x, 3, 4), "aionbound:flood_planks")
        if x % 3 == 0:
            l.line_y(x, 0, 2, 2, "aionbound:marsh_wood")
            l.line_y(x, 0, 2, 4, "aionbound:marsh_wood")
    l.line_x(8, 12, 1, 3, "aionbound:crystal_log")
    l.put(5, 2, 3, "minecraft:lodestone")
    l.put(16, 3, 3, "minecraft:barrel")
    return Assembly("marsh_broken_bridge", l.size, "channel_crossing", 1472, "river and swamp channel proxy", "two low floodwood spans divided by a sunken crystal-log fracture", [anchor("marsh_bridge_route", "interaction", (5, 2, 3), "minecraft:lodestone", "future route stamp"), anchor("marsh_bridge_cache", "cache", (16, 3, 3), "minecraft:barrel", "future underwater cache")], l.blocks)


def pearl_cairn() -> Assembly:
    l = Layout((9, 8, 9))
    l.fill((1, 0, 1), (7, 0, 7), "aionbound:crystal_gravel")
    for y, inset in ((1, 2), (2, 2), (3, 3), (4, 3)):
        l.fill((inset, y, inset), (8 - inset, y, 8 - inset), "aionbound:crystal_stone")
    l.put(4, 5, 4, "aionbound:prism_brick")
    l.put(4, 1, 7, "minecraft:barrel")
    return Assembly("pearl_cairn", l.size, "uncommon_islet", 832, "small wetland islet proxy", "stepped gravel cairn capped by a single prism marker", [anchor("pearl_cairn_cache", "cache", (4, 1, 7), "minecraft:barrel", "future pearl curiosity cache")], l.blocks)


def marsh_totem() -> Assembly:
    l = Layout((11, 13, 9))
    l.fill((1, 0, 1), (9, 0, 7), "aionbound:marsh_soil")
    l.line_y(5, 1, 11, 4, "aionbound:marsh_wood")
    for y, reach in ((4, 2), (7, 3), (10, 2)):
        l.line_x(5 - reach, 5 + reach, y, 4, "aionbound:glass_root_block")
    l.put(3, 8, 4, "aionbound:prism_brick")
    l.put(7, 8, 4, "aionbound:prism_brick")
    l.put(5, 1, 7, "minecraft:lodestone")
    l.put(2, 1, 6, "minecraft:lectern")
    return Assembly("marsh_totem", l.size, "uncommon_ritual", 1088, "open swamp islet proxy", "forked rootwood idol with paired prism eyes", [anchor("marsh_totem_altar", "interaction", (5, 1, 7), "minecraft:lodestone", "future idol path"), anchor("marsh_totem_record", "journal", (2, 1, 6), "minecraft:lectern", "future marsh record")], l.blocks)


def crystal_arch() -> Assembly:
    l = Layout((15, 15, 7))
    l.fill((1, 0, 1), (13, 1, 5), "aionbound:crystal_gravel")
    for x in (2, 3, 11, 12):
        l.line_y(x, 2, 11, 3, "aionbound:crystal_stone")
    l.line_x(2, 12, 12, 3, "aionbound:prism_brick")
    l.line_x(5, 9, 13, 3, "aionbound:glass_root_block")
    l.put(7, 14, 3, "aionbound:prismglass_signal")
    l.put(7, 1, 5, "minecraft:barrel")
    return Assembly("crystal_arch", l.size, "rare_landmark", 2432, "open wetland sightline proxy", "twin crystal piers under a rootglass and signal crown", [anchor("crystal_arch_cache", "cache", (7, 1, 5), "minecraft:barrel", "future flood-crystal cache")], l.blocks)


def crystal_obelisk() -> Assembly:
    l = Layout((13, 18, 13))
    l.fill((1, 0, 1), (11, 1, 11), "aionbound:prism_brick")
    for y, inset in ((2, 3), (5, 4), (9, 5), (14, 6)):
        l.fill((inset, y, inset), (12 - inset, min(y + 3, 17), 12 - inset), "aionbound:crystal_stone")
    l.put(6, 17, 6, "aionbound:prismglass_signal")
    l.put(6, 2, 10, "minecraft:lodestone")
    l.put(3, 2, 6, "minecraft:barrel")
    return Assembly("crystal_obelisk", l.size, "rare_network", 3072, "isolated marsh rise proxy", "four-stage tapering crystal needle with a prism signal cap", [anchor("crystal_obelisk_stamp", "interaction", (6, 2, 10), "minecraft:lodestone", "future obelisk stamp"), anchor("crystal_obelisk_cache", "cache", (3, 2, 6), "minecraft:barrel", "future obelisk cache")], l.blocks)


def sunken_shrine() -> Assembly:
    l = Layout((17, 11, 17))
    l.fill((1, 0, 1), (15, 1, 15), "aionbound:wet_clay_block")
    for x, z in ((3, 3), (13, 3), (3, 13), (13, 13)):
        l.line_y(x, 2, 8, z, "aionbound:prism_brick")
    l.fill((5, 2, 5), (11, 2, 11), "aionbound:crystal_stone")
    l.fill((7, 3, 7), (9, 4, 9), "aionbound:glass_root_block")
    l.line_x(3, 13, 9, 3, "aionbound:prism_brick")
    l.line_x(3, 13, 9, 13, "aionbound:prism_brick")
    l.put(8, 5, 8, "minecraft:lodestone")
    l.put(13, 2, 8, "minecraft:lectern")
    return Assembly("sunken_shrine", l.size, "rare_flooded", 3712, "low swamp basin proxy", "four drowned prism columns around a raised rootglass altar", [anchor("sunken_shrine_altar", "interaction", (8, 5, 8), "minecraft:lodestone", "future shrine handoff"), anchor("sunken_shrine_choir", "journal", (13, 2, 8), "minecraft:lectern", "future Drowned Choir record")], l.blocks)


def ruined_observatory() -> Assembly:
    l = Layout((23, 19, 21))
    l.fill((2, 0, 2), (20, 1, 18), "aionbound:crystal_stone")
    for x, z in ((4, 4), (18, 4), (4, 16), (18, 16)):
        l.line_y(x, 2, 14, z, "aionbound:prism_brick")
    for y, radius in ((7, 8), (11, 6), (15, 4)):
        l.line_x(11 - radius, 11 + radius, y, 10, "aionbound:glass_root_block")
        l.line_z(11, y, 10 - radius, 10 + radius, "aionbound:glass_root_block")
    l.line_y(11, 2, 18, 10, "aionbound:crystal_log")
    l.put(11, 17, 8, "aionbound:prismglass_signal")
    l.put(6, 2, 10, "minecraft:lectern")
    l.put(16, 2, 10, "minecraft:barrel")
    return Assembly("ruined_observatory", l.size, "very_rare_height", 6656, "rare elevated wetland shelf proxy", "four prism piers carrying broken concentric rootglass survey arms", [anchor("ruined_observatory_chart", "journal", (6, 2, 10), "minecraft:lectern", "future survey record"), anchor("ruined_observatory_cache", "cache", (16, 2, 10), "minecraft:barrel", "future survey cache")], l.blocks)


def deep_pool_entrance() -> Assembly:
    l = Layout((19, 12, 19))
    l.fill((1, 0, 1), (17, 1, 17), "aionbound:marsh_soil")
    l.fill((3, 2, 5), (15, 10, 17), "aionbound:crystal_stone")
    for y in range(2, 9):
        reach = 5 if y < 6 else 4
        for x in range(9 - reach, 10 + reach):
            for z in range(5, 13):
                l.blocks.pop((x, y, z), None)
    for x in (3, 4, 14, 15):
        l.line_y(x, 2, 11, 5, "aionbound:glass_root_block")
    l.line_x(3, 15, 11, 5, "aionbound:prism_brick")
    l.fill((6, 1, 10), (12, 1, 15), "aionbound:algae_block")
    l.put(9, 1, 13, "minecraft:lodestone")
    l.put(5, 2, 10, "minecraft:barrel")
    return Assembly("deep_pool_entrance", l.size, "rare_dark_water", 4352, "swamp waterline cave-mouth proxy", "wide recessed crystal mouth framed by vertical glass roots", [anchor("deep_pool_depth", "encounter", (9, 1, 13), "minecraft:lodestone", "future deep-pool handoff"), anchor("deep_pool_cache", "cache", (5, 2, 10), "minecraft:barrel", "future pool cache")], l.blocks)


ASSEMBLIES = [flooded_dock(), ancient_boat(), marsh_broken_bridge(), pearl_cairn(), marsh_totem(), crystal_arch(), crystal_obelisk(), sunken_shrine(), ruined_observatory(), deep_pool_entrance()]


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
            "adjustment_radius": 5 if max(assembly.size) >= 20 else (4 if max(assembly.size) >= 15 else 3),
            "facing_direction": "random",
            "constraints": {
                "grounded": {}, "unburied": {},
                "block_intersection": {"block_allowlist": [
                    "minecraft:air", "minecraft:grass_block", "minecraft:dirt", "minecraft:mud",
                    "minecraft:clay", "minecraft:water", "minecraft:sand", "minecraft:gravel",
                    "aionbound:marsh_soil", "aionbound:wet_clay_block", "aionbound:crystal_gravel",
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
                        {"test": "has_biome_tag", "operator": "==", "value": "swamp"},
                        {"test": "has_biome_tag", "operator": "==", "value": "river"},
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
            "rarity": assembly.rarity,
            "scatter": {"numerator": 1, "denominator": assembly.denominator},
            "expected_attempts_per_256_chunk_cell_before_filters": round(256 / assembly.denominator, 6),
            "terrain_role": assembly.terrain_role,
            "placement_implementation": "overworld non-ocean swamp-or-river surface proxy; actual shore, water-depth, and regional topology remain unproven",
            "silhouette": assembly.silhouette,
            "anchors": assembly.anchors,
            "structure_path": str(structure_path.relative_to(REPO)),
            "feature_path": str(feature_path.relative_to(REPO)),
            "feature_rule_path": str(rule_path.relative_to(REPO)),
            "structure_sha256": hashlib.sha256(structure_bytes).hexdigest(),
            "block_position_data": "EMPTY_NO_BLOCK_ENTITY_NBT",
        })
    manifest = {
        "schema": "aionbound.wave1.crystal_marsh.structure_assemblies.v1",
        "integration_authority": {"commit": SOURCE_COMMIT, "tree": SOURCE_TREE},
        "authority": [
            {"path": "engineering/crystal-marsh-intake/authority/CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.json", "sha256": "922b40aaefff220d4bd9b60fa0596b09a76fb6cf7dd181dac42e1dda856417f3"},
            {"path": "engineering/crystal-marsh-intake/block-runtime/CRYSTAL_BLOCK_RUNTIME_AUTHORITY.json", "sha256": "4712897c58ac7d4a3cf70d04ef3705ca91e8f7a6fc73932fcdc9cf1fcc4ff"},
        ],
        "proof_boundary": "STATIC_SOURCE_AND_AUTHORED_BYTES_ONLY; NO_MCSTRUCTURE_CLIENT_LOAD, BDS, TERRAIN_AFFINITY, LOOT, ENCOUNTER, OR CANDIDATE CLAIM",
        "visual_asset_boundary": "Packet landmark and native Blockbench models are visual evidence only and are not serialized into or proof of these block-built assembly bytes",
        "anchor_policy": "ordinary barrel, lodestone, and lectern coordinates are machine-recorded inert handoff anchors with empty block_position_data; W1-004-CM and W1-003 remain required before any loot, reward, or encounter binding",
        "placement_policy": "one conservative attempt per selected chunk with overworld non-ocean swamp-or-river surface proxies; denominators are Crystal-specific and not copied from Whisperwood or Ashen",
        "content_omissions": ["loot-table NBT", "reward identifiers", "boss activation", "entities", "scripts", "seal semantics", "recovery semantics"],
        "assemblies": records,
    }
    outputs[OUT / "CRYSTAL_MARSH_STRUCTURE_ASSEMBLIES.json"] = json_bytes(manifest)
    lines = [
        "# Crystal Marsh Structure Assemblies", "", "Status: **STATIC_AUTHORING_PASS_ONLY**", "",
        "Ten deterministic little-endian Bedrock structure templates are authored as distinct Crystal Marsh block-built silhouettes. Every machine-recorded anchor is inert and every structure has empty block-position data.", "",
        "| ID | Size | Occupied | Rarity / chance | Terrain role |", "|---|---:|---:|---|---|",
    ]
    for record in records:
        lines.append(f"| `{record['id']}` | `{'x'.join(map(str, record['size']))}` | {record['occupied_blocks']} | `{record['rarity']}` / `1:{record['scatter']['denominator']}` | {record['terrain_role']} |")
    lines += [
        "", "## Boundaries", "",
        "- Feature rules use stable `minecraft:structure_template_feature` with overworld, non-ocean, and swamp-or-river surface proxies.",
        "- Wetland proxy placement does not prove shoreline fit, underwater depth, regional affinity, separation distance, or successful game load.",
        "- Barrel, lodestone, and lectern blocks carry no block-entity data. No structure binds loot, rewards, bosses, seals, recovery, entities, or scripts.",
        "- `W1-004-CM` is required before loot/reward binding and `W1-003` before encounter activation.",
        "- Packet/native landmark models are visual evidence only, not assembly proof.",
        "- No BDS, client, build, gameplay, or candidate claim is made.", "",
    ]
    outputs[OUT / "CRYSTAL_MARSH_STRUCTURE_ASSEMBLIES.md"] = ("\n".join(lines)).encode()
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
