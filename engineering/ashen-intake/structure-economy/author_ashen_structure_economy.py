#!/usr/bin/env python3
"""Author ratified Ashen structure chest tables and activation signatures."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BP = REPO / "behavior_pack"
ASSEMBLY_PATH = HERE.parent / "structure-assemblies" / "author_ashen_structures.py"
SPEC = importlib.util.spec_from_file_location("ashen_assembly_author_for_economy", ASSEMBLY_PATH)
assembly_author = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = assembly_author
SPEC.loader.exec_module(assembly_author)

SOURCE_COMMIT = "ae5838c08b445e57c30e92f99d90bed426fcaf91"
SOURCE_TREE = "b4bf5f1a2e39bb7477aedee68927a039a20f2e59"
FORBIDDEN_STATIC_REWARDS = {"aionbound:ash_drake_horn", "aionbound:ember_forge_core"}


def entry(type_id: str, weight: int, minimum: int = 1, maximum: int = 1) -> dict:
    return {"typeId": type_id, "weight": weight, "min": minimum, "max": maximum}


TABLES = {
    "burned_camp": {"band": "minor_cache", "guaranteedRolls": 1, "choiceRolls": [1, 2], "guaranteed": [entry("aionbound:charbone", 45, 1, 2), entry("aionbound:furnace_chitin", 30), entry("aionbound:ember_resin", 15), entry("aionbound:sulfur_cluster", 10)], "choice": [entry("aionbound:charbone", 35, 1, 2), entry("aionbound:furnace_chitin", 30), entry("aionbound:ember_resin", 20), entry("aionbound:sulfur_cluster", 15)]},
    "char_wagon": {"band": "minor_cache", "guaranteedRolls": 1, "choiceRolls": [1, 2], "guaranteed": [entry("aionbound:sulfur_cluster", 45, 1, 2), entry("aionbound:volcanic_glass_shard", 35, 1, 2), entry("aionbound:charbone", 20)], "choice": [entry("aionbound:sulfur_cluster", 30, 1, 2), entry("aionbound:volcanic_glass_shard", 30, 1, 2), entry("aionbound:charbone", 25, 1, 2), entry("aionbound:ember_resin", 10), entry("aionbound:basalt_core", 5)]},
    "broken_bridge": {"band": "standard_structure", "guaranteedRolls": 1, "choiceRolls": [2, 4], "guaranteed": [entry("aionbound:basalt_brick", 40, 2, 4), entry("aionbound:char_planks", 35, 2, 4), entry("aionbound:volcanic_glass_shard", 25, 1, 2)], "choice": [entry("aionbound:basalt_brick", 28, 1, 3), entry("aionbound:char_planks", 25, 1, 3), entry("aionbound:volcanic_glass_shard", 22, 1, 2), entry("aionbound:furnace_chitin", 18, 1, 2), entry("aionbound:basalt_core", 7)]},
    "basalt_arch": {"band": "landmark_structure", "guaranteedRolls": 2, "choiceRolls": [2, 4], "guaranteed": [entry("aionbound:basalt_brick", 45, 2, 4), entry("aionbound:cinder_gravel", 35, 2, 4), entry("aionbound:heatstone", 20, 1, 2)], "choice": [entry("aionbound:basalt_brick", 30, 1, 3), entry("aionbound:heatstone", 25, 1, 2), entry("aionbound:volcanic_glass_shard", 20, 1, 2), entry("aionbound:basalt_core", 15), entry("aionbound:sulfur_cluster", 10)]},
    "ash_watchtower": {"band": "landmark_structure", "guaranteedRolls": 2, "choiceRolls": [2, 4], "guaranteed": [entry("aionbound:sulfur_cluster", 45, 1, 2), entry("aionbound:volcanic_glass_shard", 35, 1, 2), entry("aionbound:charbone", 20, 1, 2)], "choice": [entry("aionbound:ash_crystal", 22), entry("aionbound:volcanic_glass_shard", 25, 1, 2), entry("aionbound:heatstone", 20, 1, 2), entry("aionbound:sulfur_cluster", 18, 1, 2), entry("aionbound:basalt_core", 15)]},
    "ancient_kiln": {"band": "landmark_structure", "guaranteedRolls": 2, "choiceRolls": [2, 4], "guaranteed": [entry("aionbound:heatstone", 45, 1, 2), entry("aionbound:sulfur_cluster", 30, 1, 2), entry("aionbound:basalt_core", 25)], "choice": [entry("aionbound:heatstone", 28, 1, 2), entry("aionbound:basalt_core", 22), entry("aionbound:ember_resin", 20, 1, 2), entry("aionbound:volcanic_glass_shard", 18, 1, 2), entry("aionbound:furnace_chitin", 12)]},
    "ash_cave": {"band": "standard_structure", "guaranteedRolls": 1, "choiceRolls": [2, 4], "guaranteed": [entry("aionbound:heatstone", 45, 1, 2), entry("aionbound:charbone", 35, 1, 2), entry("aionbound:furnace_chitin", 20)], "choice": [entry("aionbound:heatstone", 30, 1, 2), entry("aionbound:charbone", 25, 1, 2), entry("aionbound:magma_moss", 18, 1, 2), entry("aionbound:furnace_chitin", 17), entry("aionbound:basalt_core", 10)]},
    "ember_forge": {"band": "apex_arena_chest", "guaranteedRolls": 2, "choiceRolls": [2, 4], "guaranteed": [entry("aionbound:heatstone", 40, 1, 3), entry("aionbound:basalt_core", 35, 1, 2), entry("aionbound:volcanic_glass_shard", 25, 1, 3)], "choice": [entry("aionbound:heatstone", 25, 1, 3), entry("aionbound:basalt_core", 20, 1, 2), entry("aionbound:volcanic_glass_shard", 18, 1, 3), entry("aionbound:furnace_chitin", 15, 1, 2), entry("aionbound:ember_resin", 12, 1, 2), entry("aionbound:ash_crystal", 10)]},
}

BANDS = {
    "minor_cache": {"totalRolls": [2, 3], "guaranteedRegionalMaterialRolls": 1},
    "standard_structure": {"totalRolls": [3, 5], "guaranteedRegionalMaterialRolls": 1},
    "landmark_structure": {"totalRolls": [4, 6], "guaranteedRegionalMaterialRolls": 2},
    "apex_arena_chest": {"totalRolls": [4, 6], "guaranteedRegionalMaterialRolls": 2},
}


def loot_entry(spec: dict) -> dict:
    value = {"type": "item", "name": spec["typeId"], "weight": spec["weight"]}
    if spec["min"] != 1 or spec["max"] != 1:
        value["functions"] = [{"function": "set_count", "count": {"min": spec["min"], "max": spec["max"]}}]
    return value


def loot_document(spec: dict) -> dict:
    choice = spec["choiceRolls"]
    return {"pools": [
        {"rolls": spec["guaranteedRolls"], "entries": [loot_entry(value) for value in spec["guaranteed"]]},
        {"rolls": {"min": choice[0], "max": choice[1]}, "entries": [loot_entry(value) for value in spec["choice"]]},
    ]}


def nearest_probes(assembly, item: dict, count: int = 8) -> list[dict]:
    anchor_xyz = tuple(item["coordinate"])
    candidates = []
    for xyz, block in assembly.blocks.items():
        if xyz == anchor_xyz or block in {"minecraft:barrel", "minecraft:lodestone", "minecraft:lectern"}:
            continue
        offset = tuple(xyz[index] - anchor_xyz[index] for index in range(3))
        distance = sum(abs(value) for value in offset)
        candidates.append((0 if block.startswith("aionbound:") else 1, distance, block, offset))
    candidates.sort()
    return [{"offset": list(offset), "expected_block": block} for _custom, _distance, block, offset in candidates[:count]]


def signatures() -> list[dict]:
    result = []
    for assembly in assembly_author.ASSEMBLIES:
        for item in assembly.anchors:
            result.append({
                "structure": assembly.identifier,
                "stamp": f"aionbound.structure.ashen.{assembly.identifier}.discovered.v1",
                "anchor_id": item["anchor_id"],
                "anchor_type": item["expected_block"],
                "anchor_coordinate": item["coordinate"],
                "probes": nearest_probes(assembly, item),
            })
    return result


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def data_module_bytes(signature_records: list[dict]) -> bytes:
    tables = json.dumps(TABLES, indent=2)
    signature_json = json.dumps(signature_records, indent=2)
    return ("// Generated by engineering/ashen-intake/structure-economy/author_ashen_structure_economy.py\n"
            f"export const ASHEN_STRUCTURE_CHEST_TABLES = Object.freeze({tables});\n"
            f"export const ASHEN_STRUCTURE_SIGNATURES = Object.freeze({signature_json});\n").encode()


def expected_outputs() -> tuple[dict[Path, bytes], dict]:
    signature_records = signatures()
    outputs = {
        BP / "loot_tables" / "chests" / "ashen" / f"{table_id}.json": json_bytes(loot_document(spec))
        for table_id, spec in TABLES.items()
    }
    outputs[BP / "scripts" / "ashen_structure_reward_data.js"] = data_module_bytes(signature_records)
    signature_manifest = {
        "schema": "aionbound.wave1.ashen.structure_activation_signatures.v1",
        "source": "deterministically derived from authored block assemblies; visual models are not inputs",
        "rotation_policy": "four cardinal rotations around each anchor",
        "signatures": signature_records,
    }
    outputs[HERE / "ASHEN_STRUCTURE_ACTIVATION_SIGNATURES.json"] = json_bytes(signature_manifest)
    records = []
    for table_id, spec in TABLES.items():
        document = loot_document(spec)
        encoded = json_bytes(document)
        band = BANDS[spec["band"]]
        records.append({
            "structure": table_id,
            "band": spec["band"],
            "total_rolls": [spec["guaranteedRolls"] + spec["choiceRolls"][0], spec["guaranteedRolls"] + spec["choiceRolls"][1]],
            "approved_total_rolls": band["totalRolls"],
            "guaranteed_regional_material_rolls": spec["guaranteedRolls"],
            "loot_table": f"loot_tables/chests/ashen/{table_id}.json",
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "identities": sorted({item["typeId"] for pool in (spec["guaranteed"], spec["choice"]) for item in pool}),
            "static_structure_binding": table_id != "ember_forge",
        })
    manifest = {
        "schema": "aionbound.wave1.ashen.structure_economy.v1",
        "status": "STATIC_AND_COMMAND_FREE_BRIDGE_READY",
        "integration_authority": {"commit": SOURCE_COMMIT, "tree": SOURCE_TREE},
        "ratified_authority": ["W1-001-AH", "W1-004-AH"],
        "tables": records,
        "structures_without_chests": ["fire_totem", "lava_shrine"],
        "protected_arena_cache": {
            "structure": "ember_forge",
            "static_loot_binding": False,
            "pre_clear": "EMPTY_AND_INTERACTION_GUARDED",
            "post_clear_population": "requires explicit validClear true from Kiln Sky service",
            "boss_terminal_ownership": "KILN_SKY_SERVICE_ONLY",
            "forbidden_static_rewards": sorted(FORBIDDEN_STATIC_REWARDS),
        },
        "delivery": "inventory first; overflow spawns at the owning player; no commands",
        "activation_signatures": {"count": len(signature_records), "machine_manifest": "engineering/ashen-intake/structure-economy/ASHEN_STRUCTURE_ACTIVATION_SIGNATURES.json"},
        "proof_boundary": "STATIC LOOT, NBT BINDING, SIGNATURE, AND SEMANTIC TEST EVIDENCE ONLY; NO BDS, BUILD, CLIENT, BOSS TERMINAL, OR CANDIDATE CLAIM",
    }
    outputs[HERE / "ASHEN_STRUCTURE_ECONOMY.json"] = json_bytes(manifest)
    lines = [
        "# Ashen Structure Economy", "", "Status: **STATIC_AND_COMMAND_FREE_BRIDGE_READY**", "",
        "Seven ordinary structure barrels bind distinct ratified Ashen chest tables. The Ember Forge arena cache remains empty before valid Kiln Sky clear and cannot statically grant either protected reward.", "",
        "| Structure | Band | Rolls | Static binding |", "|---|---|---:|---|",
    ]
    for record in records:
        lines.append(f"| `{record['structure']}` | `{record['band']}` | `{record['total_rolls'][0]}-{record['total_rolls'][1]}` | `{str(record['static_structure_binding']).lower()}` |")
    lines += ["", "Activation stamps and exact cardinal signature probes are derived from the authored assembly coordinates and recorded in the machine manifest. The runtime bridge owns no boss terminal decision.", "", "No BDS, build, client, or candidate claim is made.", ""]
    outputs[HERE / "ASHEN_STRUCTURE_ECONOMY.md"] = ("\n".join(lines)).encode()
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
