#!/usr/bin/env python3
"""Build the bounded Packet 002 Ashen warehouse-resource registry."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AUTHORITY = ROOT / "engineering/ashen-intake/authority/ASHEN_HIGHLANDS_VERTICAL_INTAKE_MAP.json"
ICON_RECEIPT = ROOT / "assets/wave1/ashen/icons/ASHEN_RESOURCE_ICON_RECEIPT.json"
ATLAS = ROOT / "resource_pack/textures/item_texture.json"
LANG = ROOT / "resource_pack/texts/en_US.lang"
REPORT = Path(__file__).with_name("ASHEN_RESOURCE_RUNTIME_REPORT.json")

BASE_COMMIT = "e9eeb3dd9bfbd8b50fdd29babd09247552bfbe7b"
BASE_TREE = "20fa2c37e1ed3e6efcd5a74edbbbb54aafcc86c4"
RESOURCE_IDS = (
    "smolder_bark",
    "charbone",
    "sulfur_cluster",
    "volcanic_glass_shard",
    "ember_resin",
    "heatstone",
    "furnace_chitin",
    "basalt_core",
    "ash_crystal",
    "fire_bloom_seed",
)
DISPLAY_NAMES = {
    "smolder_bark": "Smolder Bark",
    "charbone": "Charbone",
    "sulfur_cluster": "Sulfur Cluster",
    "volcanic_glass_shard": "Volcanic Glass Shard",
    "ember_resin": "Ember Resin",
    "heatstone": "Heatstone",
    "furnace_chitin": "Furnace Chitin",
    "basalt_core": "Basalt Core",
    "ash_crystal": "Ash Crystal",
    "fire_bloom_seed": "Fire Bloom Seed",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def update_lang() -> None:
    lines = LANG.read_text(encoding="utf-8").splitlines()
    prefix = "item.aionbound:"
    owned = {f"{prefix}{asset}" for asset in RESOURCE_IDS}
    lines = [line for line in lines if line.split("=", 1)[0] not in owned]
    lines.extend(f"{prefix}{asset}={DISPLAY_NAMES[asset]}" for asset in RESOURCE_IDS)
    LANG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    authoritative = [
        asset for asset in authority["assets"] if asset["category"] == "resources"
    ]
    actual_ids = tuple(asset["warehouse_id"] for asset in authoritative)
    if actual_ids != RESOURCE_IDS:
        raise SystemExit(f"authority resource drift: {actual_ids!r}")
    for asset in authoritative:
        expected = f"aionbound:{asset['warehouse_id']}"
        if asset["runtime_id"] != expected:
            raise SystemExit(f"runtime identity drift: {asset['runtime_id']} != {expected}")

    for asset in RESOURCE_IDS:
        item = {
            "format_version": "1.21.80",
            "minecraft:item": {
                "components": {
                    "minecraft:display_name": {"value": DISPLAY_NAMES[asset]},
                    "minecraft:icon": {"textures": {"default": asset}},
                },
                "description": {
                    "identifier": f"aionbound:{asset}",
                    "menu_category": {"category": "items"},
                },
            },
        }
        write_json(ROOT / f"behavior_pack/items/{asset}.item.json", item)

    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    texture_data = atlas["texture_data"]
    for asset in RESOURCE_IDS:
        texture_data[asset] = {
            "textures": f"textures/aionbound/ashen/items/{asset}"
        }
    write_json(ATLAS, atlas)
    update_lang()

    icon_receipt = json.loads(ICON_RECEIPT.read_text(encoding="utf-8"))
    icon_hashes = {entry["id"]: entry["shipping_sha256"] for entry in icon_receipt["icons"]}
    resources = []
    for authority_asset in authoritative:
        asset = authority_asset["warehouse_id"]
        icon = ROOT / f"resource_pack/textures/aionbound/ashen/items/{asset}.png"
        if not icon.is_file() or sha256(icon) != icon_hashes.get(asset):
            raise SystemExit(f"icon receipt mismatch: {asset}")
        item_path = ROOT / f"behavior_pack/items/{asset}.item.json"
        resources.append(
            {
                "warehouse_id": asset,
                "runtime_id": f"aionbound:{asset}",
                "display_name": DISPLAY_NAMES[asset],
                "authority_rarity": authority_asset["dependencies"]["rarity"],
                "item_path": item_path.relative_to(ROOT).as_posix(),
                "item_sha256": sha256(item_path),
                "atlas_key": asset,
                "texture_path": f"textures/aionbound/ashen/items/{asset}",
                "icon_path": icon.relative_to(ROOT).as_posix(),
                "icon_sha256": sha256(icon),
                "blockbench": {
                    "status": "NOT_APPLICABLE",
                    "reason": "flat inventory icon; no custom geometry, rig, locator, UV layout, or animation",
                },
            }
        )

    report = {
        "schema": "aionbound.wave1.ashen-resource-runtime.v1",
        "status": "STATIC_RESOURCE_REGISTRY_COMPLETE",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE},
        "authority": {
            "path": AUTHORITY.relative_to(ROOT).as_posix(),
            "sha256": sha256(AUTHORITY),
            "icon_receipt_path": ICON_RECEIPT.relative_to(ROOT).as_posix(),
            "icon_receipt_sha256": sha256(ICON_RECEIPT),
        },
        "scope": "ten Packet 002 warehouse resource items only",
        "resources": resources,
        "shared_files": [
            {
                "path": ATLAS.relative_to(ROOT).as_posix(),
                "sha256": sha256(ATLAS),
                "change": "ten aionbound item-atlas bindings",
            },
            {
                "path": LANG.relative_to(ROOT).as_posix(),
                "sha256": sha256(LANG),
                "change": "ten English item localization bindings",
            },
        ],
        "withheld": [
            "acquisition and harvesting",
            "recipes and crafting relations",
            "loot tables and numeric rarity behavior",
            "derived or nonwarehouse identities",
            "equipment and progression behavior",
            "scripts and persistence",
        ],
        "proof_boundary": {
            "proves": [
                "static Behavior Pack item-definition closure",
                "exact aionbound warehouse identifiers",
                "item icon-key to Resource Pack atlas closure",
                "English localization closure",
                "exact shipping-icon byte binding",
            ],
            "does_not_prove": [
                "Bedrock schema acceptance or pack loading",
                "acquisition, loot, recipes, progression, equipment, scripts, or persistence",
                "client rendering or inventory readability",
                "Stable BDS, multiplayer, controller, console, Marketplace, candidate, or release qualification",
            ],
        },
    }
    write_json(REPORT, report)


if __name__ == "__main__":
    main()
