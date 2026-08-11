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
        if shipping_icon.exists(): errors.append(f"reserved_icon_path_modified:{asset_id}")

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
            "shipping_icon_dependency": f"resource_pack/textures/aionbound/whisperwood/equipment/{asset_id}.png",
            "shipping_icon_status": "EXTERNAL_ICON_PASS_PENDING",
        }

    recipes_and_loot = [*sorted((ROOT / "behavior_pack/recipes").rglob("*.json")), *sorted((ROOT / "behavior_pack/loot_tables").rglob("*.json"))]
    for path in recipes_and_loot:
        text = path.read_text(encoding="utf-8")
        for asset_id in SPECS:
            if f"aionbound:{asset_id}" in text:
                errors.append(f"forbidden_recipe_or_loot_binding:{asset_id}:{path.relative_to(ROOT)}")

    if errors:
        raise AssertionError("\n".join(sorted(set(errors))))
    return {
        "schema_version": 1,
        "status": "PASS_WITH_EXTERNAL_ICON_HANDOFF",
        "scope": "eight Packet 006 Whisperwood equipment-A base assets",
        "assets": assets,
        "checks": [
            "exact_native_pass2_geometry_animation_and_32x32_texture_bytes",
            "item_attachable_geometry_animation_model_texture_closure",
            "exact_item_components_and_validator_authority",
            "reserved_shipping_icon_atlas_contract",
            "no_recipe_or_loot_binding",
        ],
        "global_validator_before_icon_handoff": {
            "status": "EXPECTED_FAIL",
            "finding_class": "atlas_missing_texture",
            "expected_count": 8,
            "reason": "shipping icon bytes are owned by the separate icon pass",
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
