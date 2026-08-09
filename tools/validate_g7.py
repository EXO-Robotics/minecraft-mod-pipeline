#!/usr/bin/env python3
"""Producer-local mechanical and content-density admission for Aionbound Core G7."""

from __future__ import annotations

import json
from pathlib import Path
import re
import struct
import sys
import zlib


ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def files(folder: str) -> list[Path]:
    return sorted((BP / folder).rglob("*.json"))


def custom_ids(folder: str, component: str) -> set[str]:
    result = set()
    for path in files(folder):
        document = load(path)
        identifier = document[component]["description"]["identifier"]
        if identifier in result:
            raise AssertionError(f"duplicate identifier {identifier}")
        result.add(identifier)
    return result


def png_ok(path: Path) -> None:
    data = path.read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n"), path
    offset = 8
    seen = set()
    while offset < len(data):
        size = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + size]
        expected = struct.unpack(">I", data[offset + 8 + size:offset + 12 + size])[0]
        assert zlib.crc32(kind + payload) & 0xFFFFFFFF == expected, path
        seen.add(kind)
        offset += size + 12
    assert {b"IHDR", b"IDAT", b"IEND"} <= seen, path


def recipe_refs() -> tuple[set[str], set[str]]:
    ingredients, results = set(), set()
    for path in files("recipes"):
        recipe = load(path)
        key = next(key for key in recipe if key.startswith("minecraft:recipe_"))
        body = recipe[key]
        for field in ("ingredients",):
            for row in body.get(field, []):
                ingredients.add(row.get("item", row.get("tag", "")))
        for row in body.get("key", {}).values():
            ingredients.add(row.get("item", row.get("tag", "")))
        result = body.get("result")
        if isinstance(result, list):
            results.update(row.get("item", "") for row in result)
        elif isinstance(result, dict):
            results.add(result.get("item", ""))
        elif isinstance(result, str):
            results.add(result)
    return {value for value in ingredients if value}, {value for value in results if value}


def loot_refs() -> set[str]:
    refs = set()
    def walk(value):
        if isinstance(value, dict):
            if value.get("type") == "item" and isinstance(value.get("name"), str): refs.add(value["name"])
            for child in value.values(): walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    for path in files("loot_tables"):
        walk(load(path))
    return refs


def main() -> None:
    for path in sorted(BP.rglob("*.json")) + sorted(RP.rglob("*.json")):
        load(path)
    for path in sorted(RP.rglob("*.png")):
        png_ok(path)

    entities = custom_ids("entities", "minecraft:entity")
    items = custom_ids("items", "minecraft:item")
    blocks = custom_ids("blocks", "minecraft:block")
    recipes = files("recipes")
    loot = files("loot_tables")
    spawn_rules = files("spawn_rules")
    structures = sorted((BP / "structures" / "aionbound").glob("*.mcstructure"))
    assert len(entities) == 24, len(entities)
    assert len(blocks) == 49, len(blocks)
    assert len(recipes) == 55, len(recipes)
    assert len(loot) == 32, len(loot)
    assert len(spawn_rules) == 10, len(spawn_rules)
    assert len(structures) == 15, len(structures)
    assert all(path.stat().st_size > 1500 for path in structures)

    custom = entities | items | blocks
    ingredients, results = recipe_refs()
    unresolved = sorted(ref for ref in ingredients | results | loot_refs() if ref.startswith("aionbound:") and ref not in custom)
    assert not unresolved, f"unresolved custom refs: {unresolved}"
    assert len(results) == len(recipes), "recipe result collision or missing result"

    terrain = load(RP / "textures" / "terrain_texture.json")["texture_data"]
    item_atlas = load(RP / "textures" / "item_texture.json")["texture_data"]
    missing_block_textures = sorted(identifier for identifier in blocks if identifier.split(":", 1)[1] not in terrain)
    missing_item_textures = sorted(identifier for identifier in items if identifier.split(":", 1)[1] not in item_atlas)
    assert not missing_block_textures, missing_block_textures
    assert not missing_item_textures, missing_item_textures
    for atlas in (terrain, item_atlas):
        for entry in atlas.values():
            texture = entry["textures"] if isinstance(entry, dict) else entry
            if isinstance(texture, list): texture = texture[0]
            assert (RP / f"{texture}.png").is_file(), texture

    scripts = "\n".join(path.read_text() for path in sorted((BP / "scripts").glob("*.js")))
    forbidden = ["@minecraft/server-ui", "node:", "require(\"fs\")", "child_process", "process.env"]
    assert not [token for token in forbidden if token in scripts]
    assert re.search(r"schema[^\n]{0,40}3|(?:SCHEMA|STATE)_VERSION\s*=\s*3", scripts, re.I), "schema v3 not visible"
    for value in (40, 24, 96, 48, 16):
        assert str(value) in scripts, f"runtime budget {value} missing"

    manifests = [load(BP / "manifest.json"), load(RP / "manifest.json")]
    assert all(document["header"]["version"] == [1, 2, 0] for document in manifests)
    assert all(document["header"]["min_engine_version"] == [1, 21, 80] for document in manifests)

    result = {
        "armor": len([item for item in items if any(piece in item for piece in ("helmet", "chestplate", "leggings", "boots"))]),
        "blocks": len(blocks), "entities": len(entities), "items": len(items), "loot_tables": len(loot),
        "recipes": len(recipes), "spawn_rules": len(spawn_rules), "structures": len(structures),
        "status": "PASS"
    }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}), file=sys.stderr)
        raise
