#!/usr/bin/env python3
"""Bounded static checks for Packet 001 foundation crafting."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
RECIPES = ROOT / "behavior_pack" / "recipes"
REPORT = Path(__file__).with_name("WHISPERWOOD_CRAFTING_FOUNDATION.json")
SCOPED_FILES = {
    "whisperwood_log_to_planks.recipe.json",
    "whisperwood_stripped_log_to_planks.recipe.json",
    "whisperwood_wood_to_planks.recipe.json",
    "whisperwood_wood_from_logs.recipe.json",
}
ALLOWED_CUSTOM_IDS = {
    "aionbound:whisperwood_log",
    "aionbound:stripped_whisperwood_log",
    "aionbound:whisperwood_wood",
    "aionbound:whisperwood_planks",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def recipe_body(document: dict) -> tuple[str, dict]:
    recipe_keys = [key for key in document if key.startswith("minecraft:recipe_")]
    if len(recipe_keys) != 1:
        raise AssertionError(f"expected one recipe body, got {recipe_keys}")
    key = recipe_keys[0]
    return key, document[key]


def ingredients(kind: str, body: dict) -> list[tuple[str, int]]:
    if kind == "minecraft:recipe_shapeless":
        return sorted((entry["item"], entry.get("count", 1)) for entry in body["ingredients"])
    counts: dict[str, int] = {}
    for row in body["pattern"]:
        for symbol in row:
            if symbol != " ":
                item = body["key"][symbol]["item"]
                counts[item] = counts.get(item, 0) + 1
    return sorted(counts.items())


def signature(document: dict) -> tuple:
    kind, body = recipe_body(document)
    result = body["result"]
    return (
        kind,
        tuple(ingredients(kind, body)),
        result["item"],
        result.get("count", 1),
    )


class WhisperwoodCraftingFoundationTests(unittest.TestCase):
    def test_exact_scoped_recipe_set_and_report(self) -> None:
        actual = {path.name for path in RECIPES.glob("whisperwood_*.recipe.json")}
        self.assertEqual(SCOPED_FILES, actual)
        report = load(REPORT)
        self.assertEqual("STATIC_CLOSURE_PASS", report["status"])
        self.assertEqual(4, len(report["implemented"]))
        self.assertTrue(any(row["identity"] == "derived_components" for row in report["withheld"]))

    def test_schema_and_exact_quantities(self) -> None:
        expected = {
            "aionbound:whisperwood_log_to_planks_recipe":
                (("aionbound:whisperwood_log", 1), "aionbound:whisperwood_planks", 4),
            "aionbound:whisperwood_stripped_log_to_planks_recipe":
                (("aionbound:stripped_whisperwood_log", 1), "aionbound:whisperwood_planks", 4),
            "aionbound:whisperwood_wood_to_planks_recipe":
                (("aionbound:whisperwood_wood", 1), "aionbound:whisperwood_planks", 4),
            "aionbound:whisperwood_wood_from_logs_recipe":
                (("aionbound:whisperwood_log", 4), "aionbound:whisperwood_wood", 3),
        }
        actual = {}
        for name in SCOPED_FILES:
            document = load(RECIPES / name)
            self.assertEqual("1.20.10", document["format_version"])
            kind, body = recipe_body(document)
            self.assertEqual(["crafting_table"], body["tags"])
            self.assertEqual([{"item": ingredients(kind, body)[0][0]}], body["unlock"])
            grouped = ingredients(kind, body)
            self.assertEqual(1, len(grouped))
            result = body["result"]
            actual[body["description"]["identifier"]] = (
                grouped[0], result["item"], result.get("count", 1)
            )
        self.assertEqual(expected, actual)

    def test_custom_identifier_closure_and_scope(self) -> None:
        declared = set()
        for directory, envelope in (("blocks", "minecraft:block"), ("items", "minecraft:item")):
            for path in (ROOT / "behavior_pack" / directory).glob("*.json"):
                document = load(path)
                if envelope in document:
                    declared.add(document[envelope]["description"]["identifier"])
        referenced = set()
        for name in SCOPED_FILES:
            kind, body = recipe_body(load(RECIPES / name))
            referenced.update(item for item, _ in ingredients(kind, body))
            referenced.add(body["result"]["item"])
            referenced.update(row["item"] for row in body["unlock"])
        self.assertEqual(ALLOWED_CUSTOM_IDS, referenced)
        self.assertEqual(set(), referenced - declared)

    def test_global_recipe_identifiers_and_signatures_do_not_collide(self) -> None:
        identifiers: dict[str, Path] = {}
        signatures: dict[tuple, Path] = {}
        for path in sorted(RECIPES.glob("*.json")):
            document = load(path)
            kind, body = recipe_body(document)
            identifier = body["description"]["identifier"]
            self.assertNotIn(identifier, identifiers, f"identifier collision: {path} and {identifiers.get(identifier)}")
            identifiers[identifier] = path
            recipe_signature = signature(document)
            self.assertNotIn(recipe_signature, signatures, f"exact signature collision: {path} and {signatures.get(recipe_signature)}")
            signatures[recipe_signature] = path
        scoped_identifiers = {
            recipe_body(load(RECIPES / name))[1]["description"]["identifier"]
            for name in SCOPED_FILES
        }
        self.assertEqual(4, len(scoped_identifiers))


if __name__ == "__main__":
    unittest.main()
