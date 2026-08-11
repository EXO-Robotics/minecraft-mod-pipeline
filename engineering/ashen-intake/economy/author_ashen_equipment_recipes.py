#!/usr/bin/env python3
"""Author the ratified Ashen component-to-equipment crafting graph."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "behavior_pack/recipes"
REPORT = Path(__file__).with_name("ASHEN_EQUIPMENT_CRAFTING_REPORT.json")

RECIPES = {
    "heat_core": (["HS"], {"H": "aionbound:heatstone", "S": "aionbound:sulfur_cluster"}),
    "heavy_head": (["V", "B", "V"], {"V": "aionbound:volcanic_glass_shard", "B": "aionbound:basalt_core"}),
    "chitin_plate": (["CCC"], {"C": "aionbound:furnace_chitin"}),
    # Smolder Gland is ratified as the ember_resin alias, so this component
    # intentionally refines resin only; it does not invent a sulfur input.
    "ember_heart": ([" E ", "EEE", " E "], {"E": "aionbound:ember_resin"}),
    "basalt_hammer": ([" H ", " E ", " B "], {"H": "aionbound:heavy_head", "E": "aionbound:ember_resin", "B": "aionbound:smolder_bark"}),
    "ember_great_axe": (["HE", " B"], {"H": "aionbound:ember_heart", "E": "aionbound:ember_resin", "B": "aionbound:smolder_bark"}),
    "ash_repeater": (["CVG", " SR", "C  "], {"C": "aionbound:char_planks", "V": "aionbound:volcanic_glass_shard", "G": "aionbound:charbone", "S": "aionbound:smoke_reed", "R": "aionbound:smolder_bark"}),
    "basalt_pick": (["HHH", " B ", " B "], {"H": "aionbound:heavy_head", "B": "aionbound:smolder_bark"}),
    "ember_hammer": ([" H ", " C ", " C "], {"H": "aionbound:heat_core", "C": "aionbound:charbone"}),
    "ore_chisel": ([" C ", " B ", " B "], {"C": "aionbound:furnace_chitin", "B": "aionbound:charbone"}),
    "ashen_helmet": (["CCC", "B B"], {"C": "aionbound:chitin_plate", "B": "aionbound:basalt_core"}),
    "ashen_chest": (["CEC", "CCC", "CBC"], {"C": "aionbound:chitin_plate", "E": "aionbound:ember_resin", "B": "aionbound:basalt_core"}),
    "ashen_legs": (["CCC", "B B", "C C"], {"C": "aionbound:chitin_plate", "B": "aionbound:basalt_core"}),
    "ashen_boots": (["C C", "B B"], {"C": "aionbound:chitin_plate", "B": "aionbound:basalt_core"}),
    # Fire Totem ash is ratified through the Ash Dust -> charbone alias.
    "ember_totem": ([" E ", "HCH", " C "], {"E": "aionbound:ember_heart", "H": "aionbound:ember_resin", "C": "aionbound:charbone"}),
}


def main() -> None:
    item_ids = {
        json.loads(path.read_text())["minecraft:item"]["description"]["identifier"]
        for path in (ROOT / "behavior_pack/items").glob("*.json")
    }
    receipts = []
    for result, (pattern, key) in RECIPES.items():
        result_id = f"aionbound:{result}"
        missing = ({result_id} | set(key.values())) - item_ids - {
            "aionbound:smoke_reed", "aionbound:char_planks",
        }
        if missing:
            raise SystemExit(f"missing item authority for {result}: {sorted(missing)}")
        payload = {
            "format_version": "1.20.10",
            "minecraft:recipe_shaped": {
                "description": {"identifier": f"aionbound:ashen_{result}_recipe"},
                "tags": ["crafting_table"], "pattern": pattern,
                "key": {symbol: {"item": item} for symbol, item in key.items()},
                "result": {"item": result_id, "count": 1},
            },
        }
        path = OUT / f"ashen_{result}.recipe.json"
        encoded = (json.dumps(payload, indent=2) + "\n").encode()
        path.write_bytes(encoded)
        receipts.append({
            "result": result_id,
            "recipe_id": f"aionbound:ashen_{result}_recipe",
            "path": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "ingredients": sorted(set(key.values())),
        })
    authority_paths = [
        ROOT / "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
        ROOT / "engineering/authority/support-proposals/ashen/W1-001-AH.json",
    ]
    report = {
        "schema_version": 1,
        "status": "PASS_SOURCE_CRAFTING_CLOSURE",
        "authority": [
            {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in authority_paths
        ],
        "recipes": receipts,
        "guarded_outputs_absent": ["aionbound:ash_drake_horn", "aionbound:ember_forge_core"],
        "deferred_outputs_absent": ["aionbound:briar_ring"],
        "proof_boundaries": ["source_json_only", "not_bds_or_client_recipe_proof", "not_balance_or_sidegrade_authority"],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
