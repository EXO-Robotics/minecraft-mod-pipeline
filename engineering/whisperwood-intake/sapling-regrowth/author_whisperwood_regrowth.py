#!/usr/bin/env python3
"""Author the ratified W1-006 standing tree and its static evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Callable


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BP = REPO / "behavior_pack"
STRUCTURE_ID = "aionbound:ww_sapling_growth_tree"
FEATURE_ID = "aionbound:ww_sapling_growth_tree_structure_feature"
SIZE = (7, 9, 7)
TRUNK_HEIGHT = 6
PALETTE_ALLOWED = {
    "aionbound:whisperwood_log",
    "aionbound:whisperwood_leaves",
    "aionbound:whisperwood_roots",
    "aionbound:moss_bark",
}
SUPPORTED_SOIL = [
    "minecraft:grass_block",
    "minecraft:dirt",
    "minecraft:coarse_dirt",
    "minecraft:podzol",
    "minecraft:moss_block",
]


class NbtWriter:
    def __init__(self) -> None:
        self.parts: list[bytes] = []

    def u8(self, value: int) -> None: self.parts.append(struct.pack("<B", value))
    def i32(self, value: int) -> None: self.parts.append(struct.pack("<i", value))
    def string_payload(self, value: str) -> None:
        encoded = value.encode("utf-8")
        self.parts.extend((struct.pack("<H", len(encoded)), encoded))
    def head(self, tag_type: int, name: str) -> None:
        self.u8(tag_type); self.string_payload(name)
    def int_tag(self, name: str, value: int) -> None:
        self.head(3, name); self.i32(value)
    def string_tag(self, name: str, value: str) -> None:
        self.head(8, name); self.string_payload(value)
    def list_tag(self, name: str, tag_type: int, values: list, emit: Callable) -> None:
        self.head(9, name); self.u8(tag_type); self.i32(len(values))
        for value in values: emit(value)
    def list_payload(self, tag_type: int, values: list, emit: Callable) -> None:
        self.u8(tag_type); self.i32(len(values))
        for value in values: emit(value)
    def compound(self, name: str, emit: Callable[[], None]) -> None:
        self.head(10, name); emit(); self.u8(0)
    def finish(self) -> bytes: return b"".join(self.parts)


def tree_blocks() -> dict[tuple[int, int, int], str]:
    blocks: dict[tuple[int, int, int], str] = {}
    put = lambda xyz, block: blocks.__setitem__(xyz, block)

    # Six-block upright trunk; the sapling origin becomes its lowest log.
    for y in range(TRUNK_HEIGHT):
        put((3, y, 3), "aionbound:whisperwood_log")

    # Exposed asymmetrical root flare, fully inside the approved footprint.
    for xyz in ((2, 0, 3), (4, 0, 3), (3, 0, 2), (3, 0, 4), (1, 0, 3), (3, 0, 5)):
        put(xyz, "aionbound:whisperwood_roots")

    # Short structural limbs preserve an upright, non-landmark silhouette.
    for xyz in ((2, 4, 3), (4, 4, 3), (3, 5, 2), (3, 5, 4)):
        put(xyz, "aionbound:whisperwood_log")

    # Three irregular canopy tiers. They are intentionally not a symmetric cube.
    for y, center, radius in ((4, (3, 3), 3), (5, (3, 3), 3), (6, (3, 3), 2), (7, (3, 2), 2)):
        cx, cz = center
        for x in range(7):
            for z in range(7):
                distance = abs(x - cx) + abs(z - cz)
                if distance <= radius and (x + 2 * z + y) % 5 != 0:
                    blocks.setdefault((x, y, z), "aionbound:whisperwood_leaves")
    for xyz in ((3, 8, 2), (2, 8, 2), (3, 8, 1), (4, 7, 4)):
        put(xyz, "aionbound:whisperwood_leaves")

    # Restrained moss-bark accents use the fourth and final approved block.
    for xyz in ((4, 2, 3), (2, 4, 3), (3, 6, 4)):
        put(xyz, "aionbound:moss_bark")
    return blocks


def encode_structure(blocks: dict[tuple[int, int, int], str]) -> tuple[bytes, list[str], list[int]]:
    palette = sorted(set(blocks.values()))
    palette_index = {name: index for index, name in enumerate(palette)}
    sx, sy, sz = SIZE
    indices = [-1] * (sx * sy * sz)
    for (x, y, z), name in blocks.items():
        indices[x + z * sx + y * sx * sz] = palette_index[name]
    n = NbtWriter()
    n.head(10, "")
    n.int_tag("format_version", 1)
    n.list_tag("size", 3, list(SIZE), n.i32)
    n.list_tag("structure_world_origin", 3, [0, 0, 0], n.i32)
    n.compound("structure", lambda: emit_structure(n, indices, palette))
    n.u8(0)
    return n.finish(), palette, indices


def emit_structure(n: NbtWriter, indices: list[int], palette: list[str]) -> None:
    n.list_tag("block_indices", 9, [indices, [-1] * len(indices)], lambda layer: n.list_payload(3, layer, n.i32))
    n.list_tag("entities", 10, [], lambda _value: None)
    n.compound("palette", lambda: n.compound("default", lambda: emit_palette(n, palette)))


def emit_palette(n: NbtWriter, palette: list[str]) -> None:
    def entry(name: str) -> None:
        n.string_tag("name", name)
        n.compound("states", lambda: None)
        n.int_tag("version", 18168865)
        n.u8(0)
    n.list_tag("block_palette", 10, palette, entry)
    n.compound("block_position_data", lambda: None)


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def expected_outputs() -> dict[Path, bytes]:
    blocks = tree_blocks()
    structure, palette, indices = encode_structure(blocks)
    structure_path = BP / "structures/aionbound/ww_sapling_growth_tree.mcstructure"
    feature_path = BP / "features/ww_sapling_growth_tree.structure_feature.json"
    feature = {
        "format_version": "1.13.0",
        "minecraft:structure_template_feature": {
            "description": {"identifier": FEATURE_ID},
            "structure_name": STRUCTURE_ID,
            "adjustment_radius": 0,
            "facing_direction": "north",
            "constraints": {"unburied": {}},
        },
    }
    report = {
        "schema": "aionbound.wave1.whisperwood.sapling_regrowth.v1",
        "status": "SOURCE_RUNTIME_WIRED",
        "authority": {
            "tranche": "W1-006-WW-SAPLING",
            "proposal_preserved": "engineering/authority/support-proposals/W1-CREATIVE-006/whisperwood_sapling_regrowth_proposal.json",
            "decision_ledger": "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
        },
        "assembly": {
            "structure_id": STRUCTURE_ID,
            "feature_id": FEATURE_ID,
            "variant_count": 1,
            "size": list(SIZE),
            "trunk_height": TRUNK_HEIGHT,
            "palette": palette,
            "occupied_blocks": sum(index >= 0 for index in indices),
            "origin_binding": "structure origin equals sapling location minus [3,0,3]; the sapling becomes the trunk base at local [3,0,3]",
            "sha256": hashlib.sha256(structure).hexdigest(),
        },
        "sapling_soil_filter": SUPPORTED_SOIL,
        "growth_contract": {
            "natural_loaded_tick_interval": [14400, 36000],
            "loaded_minutes_at_20_tps": [12, 30],
            "retry": "loop after every failed obstruction or soil check; leave sapling unchanged",
            "bone_meal": "one interaction may enqueue at most one early attempt; apply a 1-in-3 success gate before clearance; consume at most one bone meal in Survival; never guarantee growth",
            "preconditions": {
                "center": "aionbound:whisperwood_sapling",
                "soil_below_center": SUPPORTED_SOIL,
                "all_other_occupied_structure_coordinates": ["minecraft:air"],
                "all_referenced_chunks": "loaded",
            },
            "placement": "after all preconditions pass atomically, place aionbound:ww_sapling_growth_tree at sapling-[3,0,3] with no rotation or mirroring",
            "persistence": "world block state only; no player, entity, scoreboard, or dynamic-property stamp",
            "required_block_wiring": {
                "minecraft:tick": {"interval_range": [14400, 36000], "looping": True},
                "custom_component": "aionbound:whisperwood_sapling_regrowth",
                "handlers": ["onTick", "onPlayerInteract"],
            },
            "runtime_module": "behavior_pack/scripts/whisperwood_regrowth.js",
            "startup_registration": "behavior_pack/scripts/main.js uses system.beforeEvents.startup and the event blockComponentRegistry",
        },
        "ecology_density_audit": {
            "scope": "12 ww_ecology rules plus two ww_prop rules; landmark structure rules excluded as a separately budgeted surface",
            "attempts_per_chunk_before_filters": 1.2408854166666666,
            "ceiling": 1.25,
            "regrowth_rule_delta": 0,
            "cap_change": "NONE",
        },
        "blockbench": "NOT_APPLICABLE: assembly uses only ordinary existing block states in a native .mcstructure; no new geometry, UV, rig, animation, or texture",
        "proof_boundary": "STATIC_AUTHORED_BYTES_AND_SOURCE_SEMANTIC_RUNTIME_WIRING_ONLY; NOT BDS, CLIENT, LOADED-TIME, BONE-MEAL_DELIVERY, RESTART, OR CANDIDATE PROOF",
        "official_stable_basis": [
            "https://learn.microsoft.com/en-us/minecraft/creator/reference/content/blockreference/examples/blockcomponents/minecraftblock_tick?view=minecraft-bedrock-stable",
            "https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server/blockcomponentregistry?view=minecraft-bedrock-stable",
            "https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server/structure?view=minecraft-bedrock-stable",
        ],
    }
    readme = """# Whisperwood Sapling Regrowth\n\nStatus: **SOURCE_RUNTIME_WIRED**\n\nThe ratified W1-006 tree is one `7x9x7` upright asymmetric assembly with a six-block trunk and exactly the approved four-block palette. The sapling has a stable supported-soil filter, the approved loaded-time tick interval, and the registered `aionbound:whisperwood_sapling_regrowth` component.\n\nCurrent stable Bedrock dispatches `minecraft:tick` through a registered custom block component. `scripts/main.js` registers this component during `system.beforeEvents.startup`; `scripts/whisperwood_regrowth.js` performs full-footprint obstruction checks before atomic structure placement and applies the bounded one-in-three bone-meal attempt.\n\nThe committed `.mcstructure` is deterministic little-endian NBT. Blockbench is `NOT_APPLICABLE` because this assembly introduces no custom geometry, texture, UV, rig, or animation. Source semantic tests do not prove loaded-time delivery, client interaction, BDS restart behavior, or rendering; those remain within Checkpoint 1 and later client proof boundaries.\n"""
    return {
        structure_path: structure,
        feature_path: json_bytes(feature),
        HERE / "WHISPERWOOD_SAPLING_REGROWTH_REPORT.json": json_bytes(report),
        HERE / "README.md": readme.encode(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    mismatches = []
    for path, data in expected_outputs().items():
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                mismatches.append(str(path.relative_to(REPO)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if mismatches:
        print(json.dumps({"status": "FAIL", "mismatches": mismatches}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write", "outputs": 4}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
