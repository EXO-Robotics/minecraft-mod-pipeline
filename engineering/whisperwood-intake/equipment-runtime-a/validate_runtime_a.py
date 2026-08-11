#!/usr/bin/env python3
"""Fail-closed source and semantic closure for Whisperwood equipment-A."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from author_runtime_a import NATIVE, ROOT, SPECS


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check() -> dict:
    errors: list[str] = []
    assets: dict[str, dict] = {}
    atlas = read_json(ROOT / "resource_pack/textures/item_texture.json")["texture_data"]
    language = (ROOT / "resource_pack/texts/en_US.lang").read_text(encoding="utf-8").splitlines()
    authority = read_json(ROOT / "engineering/validation/wave1/WAVE_1_VALIDATION_AUTHORITY.json")
    required_items = set(authority["required_successor_ids"]["items"])
    icon_receipt_path = ROOT / "assets/wave1/whisperwood/equipment-icons/WHISPERWOOD_EQUIPMENT_ICON_RECEIPT.json"
    icon_receipt = read_json(icon_receipt_path)
    receipt_icons = {icon["id"]: icon for icon in icon_receipt.get("icons", [])}
    if icon_receipt.get("status") != "PASS_STATIC_PRESENTATION": errors.append("icon_receipt_status")
    global_report_path = Path(__file__).with_name("GLOBAL_WAVE1_VALIDATION.json")
    global_report = read_json(global_report_path)
    if global_report.get("status") != "PASS": errors.append("global_validator_status")

    for asset_id, spec in SPECS.items():
        item_path = ROOT / f"behavior_pack/items/{asset_id}.item.json"
        attachable_path = ROOT / f"resource_pack/attachables/{asset_id}.attachable.json"
        geometry_path = ROOT / f"resource_pack/models/aionbound/whisperwood/equipment/{asset_id}.geo.json"
        animation_path = ROOT / f"resource_pack/animations/aionbound/whisperwood/equipment/{asset_id}.animation.json"
        texture_path = ROOT / f"resource_pack/textures/aionbound/whisperwood/equipment/models/{asset_id}.png"
        shipping_icon = ROOT / f"resource_pack/textures/aionbound/whisperwood/equipment/{asset_id}.png"
        native_geometry = NATIVE / asset_id / "native-exports/pass-2.geo.json"
        native_animation = NATIVE / asset_id / "native-exports/pass-2.animation.json"
        native_texture = NATIVE / asset_id / f"native-project/textures/{asset_id}.png"

        for path in (item_path, attachable_path, geometry_path, animation_path, texture_path):
            if not path.is_file(): errors.append(f"missing:{path.relative_to(ROOT)}")
        if errors:
            continue

        item = read_json(item_path)["minecraft:item"]
        components = item["components"]
        if item["description"]["identifier"] != f"aionbound:{asset_id}": errors.append(f"item_id:{asset_id}")
        if components.get("minecraft:damage") != spec["damage"]: errors.append(f"damage:{asset_id}")
        if components.get("minecraft:durability", {}).get("max_durability") != spec["durability"]: errors.append(f"durability:{asset_id}")
        if components.get("minecraft:icon", {}).get("textures", {}).get("default") != asset_id: errors.append(f"icon_key:{asset_id}")
        if f"aionbound:{asset_id}" not in required_items: errors.append(f"validator_authority:{asset_id}")
        if f"item.aionbound:{asset_id}={spec['name']}" not in language: errors.append(f"language:{asset_id}")

        expected_icon = f"textures/aionbound/whisperwood/equipment/{asset_id}"
        if atlas.get(asset_id, {}).get("textures") != expected_icon: errors.append(f"atlas:{asset_id}")
        if not shipping_icon.is_file(): errors.append(f"shipping_icon_missing:{asset_id}")
        receipt_icon = receipt_icons.get(asset_id)
        if not receipt_icon: errors.append(f"icon_receipt_missing:{asset_id}")
        elif shipping_icon.is_file():
            if receipt_icon.get("shipping_path") != shipping_icon.relative_to(ROOT).as_posix(): errors.append(f"icon_receipt_path:{asset_id}")
            if receipt_icon.get("shipping_sha256") != sha256(shipping_icon): errors.append(f"icon_receipt_hash:{asset_id}")
            icon_width, icon_height = struct.unpack(">II", shipping_icon.read_bytes()[16:24])
            if (icon_width, icon_height) != (32, 32) or receipt_icon.get("shipping_size") != [32, 32]: errors.append(f"icon_dimensions:{asset_id}")

        attachable = read_json(attachable_path)["minecraft:attachable"]["description"]
        if attachable["geometry"].get("default") != f"geometry.aionbound.{asset_id}": errors.append(f"attachable_geometry:{asset_id}")
        if attachable["textures"].get("default") != f"textures/aionbound/whisperwood/equipment/models/{asset_id}": errors.append(f"attachable_texture:{asset_id}")
        expected_animations = {clip: f"animation.aionbound.{asset_id}.{clip}" for clip in spec["clips"]}
        if attachable.get("animations") != expected_animations: errors.append(f"attachable_animations:{asset_id}")
        if attachable.get("scripts", {}).get("animate") != [spec["idle"]]: errors.append(f"attachable_idle:{asset_id}")

        geometry = read_json(geometry_path)["minecraft:geometry"][0]
        description = geometry["description"]
        if description.get("identifier") != f"geometry.aionbound.{asset_id}": errors.append(f"geometry_id:{asset_id}")
        if (description.get("texture_width"), description.get("texture_height")) != (32, 32): errors.append(f"geometry_texture_size:{asset_id}")
        animation_ids = set(read_json(animation_path).get("animations", {}))
        if animation_ids != set(expected_animations.values()): errors.append(f"animation_ids:{asset_id}")

        if geometry_path.read_bytes() != native_geometry.read_bytes(): errors.append(f"geometry_not_pass2:{asset_id}")
        if animation_path.read_bytes() != native_animation.read_bytes(): errors.append(f"animation_not_pass2:{asset_id}")
        if texture_path.read_bytes() != native_texture.read_bytes(): errors.append(f"texture_not_native:{asset_id}")
        width, height = struct.unpack(">II", texture_path.read_bytes()[16:24])
        if (width, height) != (32, 32): errors.append(f"texture_dimensions:{asset_id}")

        assets[asset_id] = {
            "runtime_id": f"aionbound:{asset_id}",
            "item_sha256": sha256(item_path),
            "geometry_sha256": sha256(geometry_path),
            "animation_sha256": sha256(animation_path),
            "model_texture_sha256": sha256(texture_path),
            "shipping_icon_sha256": sha256(shipping_icon),
            "shipping_icon_status": "PASS_STATIC_PRESENTATION",
        }

    ledger = read_json(ROOT / "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json")
    approved = {entry["tranche"] for entry in ledger.get("ratifications", {}).get("approved", [])}
    if "W1-001-WW" not in approved or "W1-004-WW-CH1" not in approved:
        errors.append("ratified_economy_authority_missing")
    for asset_id in SPECS:
        recipe_path = ROOT / f"behavior_pack/recipes/{asset_id}.recipe.json"
        if not recipe_path.is_file():
            errors.append(f"approved_recipe_missing:{asset_id}")
        else:
            body = read_json(recipe_path).get("minecraft:recipe_shapeless", {})
            if body.get("result", {}).get("item") != f"aionbound:{asset_id}":
                errors.append(f"approved_recipe_result:{asset_id}")
        for loot_path in sorted((ROOT / "behavior_pack/loot_tables").rglob("*.json")):
            if f"aionbound:{asset_id}" in loot_path.read_text(encoding="utf-8"):
                errors.append(f"finished_equipment_in_loot:{asset_id}:{loot_path.relative_to(ROOT)}")

    if errors:
        raise AssertionError("\n".join(sorted(set(errors))))
    return {
        "schema_version": 1,
        "status": "PASS",
        "scope": "eight Packet 006 Whisperwood equipment-A base assets",
        "assets": assets,
        "checks": [
            "exact_native_pass2_geometry_animation_and_32x32_texture_bytes",
            "item_attachable_geometry_animation_model_texture_closure",
            "exact_item_components_and_validator_authority",
            "shipping_icon_atlas_and_receipt_hash_closure",
            "ratified_recipe_acquisition_and_no_finished_equipment_loot",
        ],
        "global_validator_after_icon_handoff": {
            "status": "PASS_OBSERVED",
            "report": global_report_path.relative_to(ROOT).as_posix(),
            "report_sha256": sha256(global_report_path),
            "pack_source_sha256": global_report.get("source_evidence", {}).get("pack_source_sha256"),
            "findings": global_report.get("findings", []),
        },
        "withheld": [
            "extended_melee_reach",
            "literal_attack_speed_control",
            "elite_specific_bonus_damage",
            "lantern_hook_pull_or_climb",
            "all_sidegrades",
            "action_clip_input_binding_pending_client_presentation_validation",
        ],
        "proof_boundaries": [
            "source_tree_and_transformed_semantic_harness_only",
            "not_build_or_package_proof",
            "not_bds_or_bedrock_schema_proof",
            "not_client_rendering_gameplay_or_input_proof",
            "not_multiplayer_controller_console_marketplace_or_release_proof",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    report = check()
    if args.write_report:
        output = Path(__file__).with_name("WHISPERWOOD_EQUIPMENT_RUNTIME_A_REPORT.json")
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "assets": len(report["assets"])}, sort_keys=True))


if __name__ == "__main__":
    main()
