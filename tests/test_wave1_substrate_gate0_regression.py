#!/usr/bin/env python3
"""Targeted static regressions for the G7 Gate 0 content-schema debts."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BLOCKS = ROOT / "behavior_pack" / "blocks"
FEATURES = ROOT / "behavior_pack" / "features"
FEATURE_RULES = ROOT / "behavior_pack" / "feature_rules"
ITEMS = ROOT / "behavior_pack" / "items"
RECIPES = ROOT / "behavior_pack" / "recipes"

GATE0_BLOCKS = {
    "aionite_ore",
    "brinewood_beam",
    "carved_lumen_stone",
    "charged_aionite_block",
    "codex_lectern",
    "cut_ferrowake",
    "ferrowake_beam",
    "ferrowake_bricks",
    "ferrowake_grate",
    "ferrowake_lamp",
    "ferrowake_ore",
    "fossil_rib_block",
    "lumen_brazier",
    "lumen_inlay",
    "lumen_salt_cluster",
    "lumen_stone",
    "mite_resin_block",
    "prismglass_framed",
    "prismglass_frosted",
    "prismglass_signal",
    "relic_sandstone",
    "resonance_press",
    "resonant_lamp",
    "riveted_ferrowake",
    "rootglass_lantern",
    "rootglass_mosaic",
    "rootglass_nodule",
    "salvage_bench",
    "storm_slate_tiles",
    "survey_relay",
    "trophy_plinth",
    "woven_nest",
}

GATE0_RECIPES = {
    "aionite_crystal_from_ore",
    "ferrowake_bricks",
    "ferrowake_lamp",
    "lumen_salt_from_cluster",
    "lumen_stone",
    "prismglass_framed",
    "raw_ferrowake_from_ore",
    "resonance_press",
    "rootglass_mosaic",
    "rootglass_shard_from_nodule",
    "salvage_bench",
    "survey_relay",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def recipe_payload(path: Path) -> dict:
    document = load(path)
    keys = [key for key in document if key.startswith("minecraft:recipe_")]
    if len(keys) != 1:
        raise AssertionError(f"{path.name}: expected one recipe payload, got {keys}")
    return document[keys[0]]


def recipe_item_refs(payload: dict) -> set[str]:
    refs = {payload["result"]["item"]}
    refs.update(entry["item"] for entry in payload.get("ingredients", []))
    refs.update(entry["item"] for entry in payload.get("key", {}).values())
    refs.update(entry["item"] for entry in payload.get("unlock", []) if "item" in entry)
    return refs


class Gate0SubstrateRegression(unittest.TestCase):
    def test_all_json_in_affected_families_parses(self) -> None:
        paths = [
            *BLOCKS.glob("*.json"),
            *FEATURES.glob("*.json"),
            *FEATURE_RULES.glob("*.json"),
            *RECIPES.glob("*.json"),
        ]
        self.assertGreater(len(paths), 0)
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                load(path)

    def test_block_geometry_and_material_instances_are_paired(self) -> None:
        seen = set()
        for path in sorted(BLOCKS.glob("*.block.json")):
            block = load(path)["minecraft:block"]
            identifier = block["description"]["identifier"]
            components = block["components"]
            has_geometry = "minecraft:geometry" in components
            has_materials = "minecraft:material_instances" in components
            self.assertEqual(has_geometry, has_materials, identifier)
            if identifier.removeprefix("aionbound:") in GATE0_BLOCKS:
                seen.add(identifier.removeprefix("aionbound:"))
                self.assertEqual(
                    components["minecraft:geometry"],
                    "minecraft:geometry.full_block",
                    identifier,
                )
        self.assertEqual(seen, GATE0_BLOCKS)

    def test_feature_rule_identifiers_match_filenames_and_targets_exist(self) -> None:
        feature_ids = {
            load(path)["minecraft:single_block_feature"]["description"]["identifier"]
            for path in FEATURES.glob("*.feature.json")
        }
        for path in sorted(FEATURE_RULES.glob("*.feature_rule.json")):
            description = load(path)["minecraft:feature_rules"]["description"]
            self.assertEqual(description["identifier"], f"aionbound:{path.stem}", path.name)
            self.assertIn(description["places_feature"], feature_ids, path.name)

    def test_gate0_recipe_set_and_custom_identifier_closure(self) -> None:
        registered = {
            load(path)["minecraft:block"]["description"]["identifier"]
            for path in BLOCKS.glob("*.block.json")
        }
        registered.update(
            load(path)["minecraft:item"]["description"]["identifier"]
            for path in ITEMS.glob("*.item.json")
        )
        affected = set()
        for path in sorted(RECIPES.glob("*.recipe.json")):
            refs = recipe_item_refs(recipe_payload(path))
            unresolved = {ref for ref in refs if ref.startswith("aionbound:") and ref not in registered}
            self.assertEqual(unresolved, set(), path.name)
            if refs & {f"aionbound:{name}" for name in GATE0_BLOCKS}:
                affected.add(path.name.removesuffix(".recipe.json"))
        self.assertEqual(affected, GATE0_RECIPES)


if __name__ == "__main__":
    unittest.main()
