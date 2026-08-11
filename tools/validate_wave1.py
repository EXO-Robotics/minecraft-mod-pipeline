#!/usr/bin/env python3
"""Fail-closed, successor-native source validation for Aionbound Wave 1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from typing import Any, Iterable
import zlib


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_REL = Path("engineering/validation/wave1/WAVE_1_VALIDATION_AUTHORITY.json")
CUSTOM_ID = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")
IMPORT = re.compile(r"(?:from\s+|import\s*\(\s*)[\"']([^\"']+)[\"']")
PROOF_BOUNDARIES = [
    "source_tree_mechanical_only",
    "not_immutable_package_proof",
    "not_archive_extracted_entrypoint_proof",
    "not_bedrock_schema_or_stable_bds_proof",
    "not_client_rendering_or_gameplay_proof",
    "not_multiplayer_console_marketplace_or_release_proof",
]


class ValidationFailure(Exception):
    """A deterministic validation failure with one or more actionable findings."""

    def __init__(self, findings: Iterable[str], evidence: dict[str, Any] | None = None):
        self.findings = sorted(set(findings))
        self.evidence = evidence or {}
        super().__init__("; ".join(self.findings))


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValidationFailure([f"malformed_json:{path}:{exc}"]) from exc


def json_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.json"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pack_tree_sha256(bp: Path, rp: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    paths = sorted(path for pack in (bp, rp) for path in pack.rglob("*") if path.is_file())
    for path in paths:
        relative = path.relative_to(bp.parent).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest(), len(paths)


def validate_png(path: Path) -> None:
    data = path.read_bytes()
    errors: list[str] = []
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValidationFailure([f"invalid_png_signature:{path}"])
    offset, kinds, image_data = 8, [], bytearray()
    try:
        while offset < len(data):
            if offset + 12 > len(data):
                raise ValueError("truncated chunk header")
            size = struct.unpack(">I", data[offset:offset + 4])[0]
            end = offset + 12 + size
            if end > len(data):
                raise ValueError("truncated chunk payload")
            kind = data[offset + 4:offset + 8]
            payload = data[offset + 8:offset + 8 + size]
            expected = struct.unpack(">I", data[offset + 8 + size:end])[0]
            if zlib.crc32(kind + payload) & 0xFFFFFFFF != expected:
                errors.append(f"invalid_png_crc:{path}:{kind.decode('ascii', 'replace')}")
            kinds.append(kind)
            if kind == b"IDAT":
                image_data.extend(payload)
            offset = end
            if kind == b"IEND":
                break
        if offset != len(data):
            errors.append(f"invalid_png_trailing_bytes:{path}")
        if not {b"IHDR", b"IDAT", b"IEND"}.issubset(kinds):
            errors.append(f"invalid_png_required_chunks:{path}")
        if kinds and (kinds[0] != b"IHDR" or kinds[-1] != b"IEND"):
            errors.append(f"invalid_png_chunk_order:{path}")
        try:
            if image_data:
                zlib.decompress(bytes(image_data))
        except zlib.error as exc:
            errors.append(f"invalid_png_image_stream:{path}:{exc}")
    except (ValueError, struct.error) as exc:
        errors.append(f"invalid_png_structure:{path}:{exc}")
    if errors:
        raise ValidationFailure(errors)


def documents(folder: Path, component: str) -> tuple[dict[str, Path], list[str]]:
    result: dict[str, Path] = {}
    errors: list[str] = []
    for path in json_files(folder):
        document = read_json(path)
        try:
            identifier = document[component]["description"]["identifier"]
        except (KeyError, TypeError):
            errors.append(f"missing_identifier:{path}:{component}")
            continue
        if not isinstance(identifier, str) or not CUSTOM_ID.fullmatch(identifier):
            errors.append(f"invalid_identifier:{path}:{identifier!r}")
            continue
        if identifier in result:
            errors.append(f"duplicate_identifier:{identifier}:{result[identifier]}:{path}")
        else:
            result[identifier] = path
    return result, errors


def walk_item_refs(value: Any, refs: set[str]) -> None:
    if isinstance(value, dict):
        if value.get("type") == "item" and isinstance(value.get("name"), str):
            refs.add(value["name"])
        for child in value.values():
            walk_item_refs(child, refs)
    elif isinstance(value, list):
        for child in value:
            walk_item_refs(child, refs)


def keyed_strings(value: Any, requested: set[str]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in requested:
                if isinstance(child, str):
                    result.append((key, child))
                elif isinstance(child, list):
                    result.extend((key, item) for item in child if isinstance(item, str))
            result.extend(keyed_strings(child, requested))
    elif isinstance(value, list):
        for child in value:
            result.extend(keyed_strings(child, requested))
    return result


def texture_path(root: Path, value: Any) -> Path | None:
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, dict):
        value = value.get("path")
    if not isinstance(value, str) or not value:
        return None
    candidate = root / value
    return candidate if candidate.suffix else candidate.with_suffix(".png")


def version_at_least(actual: Any, minimum: list[int]) -> bool:
    return isinstance(actual, list) and all(isinstance(v, int) for v in actual) and tuple(actual) >= tuple(minimum)


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    bp, rp = root / "behavior_pack", root / "resource_pack"
    authority_path = root / AUTHORITY_REL
    authority = read_json(authority_path)
    errors: list[str] = []

    for required in (bp, rp):
        if not required.is_dir():
            errors.append(f"missing_pack_directory:{required}")
    if errors:
        raise ValidationFailure(errors)

    parsed: dict[Path, Any] = {}
    for path in json_files(bp) + json_files(rp):
        try:
            parsed[path] = read_json(path)
        except ValidationFailure as exc:
            errors.extend(exc.findings)
    for path in sorted(rp.rglob("*.png")):
        try:
            validate_png(path)
        except ValidationFailure as exc:
            errors.extend(exc.findings)

    entities, found = documents(bp / "entities", "minecraft:entity"); errors += found
    items, found = documents(bp / "items", "minecraft:item"); errors += found
    blocks, found = documents(bp / "blocks", "minecraft:block"); errors += found
    spawn_rules, found = documents(bp / "spawn_rules", "minecraft:spawn_rules"); errors += found
    feature_rules, found = documents(bp / "feature_rules", "minecraft:feature_rules"); errors += found
    client_entities, found = documents(rp / "entity", "minecraft:client_entity"); errors += found
    attachables, found = documents(rp / "attachables", "minecraft:attachable"); errors += found
    for identifier in entities:
        if identifier not in client_entities:
            errors.append(f"behavior_entity_missing_client_entity:{identifier}")

    feature_components = (
        "minecraft:aggregate_feature", "minecraft:beards_and_shavers", "minecraft:cave_carver_feature",
        "minecraft:conditional_list", "minecraft:fossil_feature", "minecraft:geode_feature",
        "minecraft:growing_plant_feature", "minecraft:multiface_feature", "minecraft:nether_cave_carver_feature",
        "minecraft:ore_feature", "minecraft:partially_exposed_blob_feature", "minecraft:rect_layout",
        "minecraft:scan_surface", "minecraft:scatter_feature", "minecraft:search_feature",
        "minecraft:sequence_feature", "minecraft:single_block_feature", "minecraft:snap_to_surface_feature",
        "minecraft:structure_template_feature", "minecraft:surface_relative_threshold_feature",
        "minecraft:tree_feature", "minecraft:underwater_cave_carver_feature", "minecraft:vegetation_patch_feature",
        "minecraft:weighted_random_feature",
    )
    features: dict[str, Path] = {}
    for path in json_files(bp / "features"):
        document = parsed.get(path, {})
        matches = [key for key in feature_components if key in document]
        if len(matches) != 1:
            errors.append(f"feature_component_count:{path}:{len(matches)}")
            continue
        try:
            identifier = document[matches[0]]["description"]["identifier"]
        except (KeyError, TypeError):
            errors.append(f"missing_feature_identifier:{path}")
            continue
        if not isinstance(identifier, str) or not CUSTOM_ID.fullmatch(identifier):
            errors.append(f"invalid_feature_identifier:{path}:{identifier!r}")
        elif identifier in features:
            errors.append(f"duplicate_feature_identifier:{identifier}:{features[identifier]}:{path}")
        else:
            features[identifier] = path

    recipes: dict[str, Path] = {}
    recipe_signatures: dict[tuple, tuple[str, Path]] = {}
    recipe_refs: set[str] = set()
    recipe_results: list[str] = []
    for path in json_files(bp / "recipes"):
        document = parsed.get(path, {})
        keys = [key for key in document if key.startswith("minecraft:recipe_")]
        if len(keys) != 1:
            errors.append(f"recipe_component_count:{path}:{len(keys)}")
            continue
        body = document[keys[0]]
        identifier = body.get("description", {}).get("identifier")
        if not isinstance(identifier, str) or not CUSTOM_ID.fullmatch(identifier):
            errors.append(f"invalid_recipe_identifier:{path}:{identifier!r}")
        elif identifier in recipes:
            errors.append(f"duplicate_recipe_identifier:{identifier}:{recipes[identifier]}:{path}")
        else:
            recipes[identifier] = path
        tags = tuple(sorted(value for value in body.get("tags", []) if isinstance(value, str)))
        signature = None
        if keys[0] == "minecraft:recipe_shapeless":
            ingredients = []
            for row in body.get("ingredients", []):
                if isinstance(row, dict):
                    ingredients.append(tuple(sorted(
                        (key, value) for key, value in row.items()
                        if key in {"item", "tag", "data"} and isinstance(value, (str, int))
                    )))
            if ingredients:
                signature = (keys[0], tags, tuple(sorted(ingredients)))
        elif keys[0] == "minecraft:recipe_shaped":
            pattern = tuple(body.get("pattern", []))
            key_rows = []
            for symbol, row in sorted(body.get("key", {}).items()):
                if isinstance(row, dict):
                    key_rows.append((symbol, tuple(sorted(
                        (key, value) for key, value in row.items()
                        if key in {"item", "tag", "data"} and isinstance(value, (str, int))
                    ))))
            if pattern and key_rows:
                signature = (keys[0], tags, pattern, tuple(key_rows))
        if signature is not None and isinstance(identifier, str):
            if signature in recipe_signatures:
                prior_identifier, prior_path = recipe_signatures[signature]
                errors.append(
                    f"duplicate_recipe_ingredients:{prior_identifier}:{prior_path}:"
                    f"{identifier}:{path}"
                )
            else:
                recipe_signatures[signature] = (identifier, path)
        rows = list(body.get("ingredients", [])) + list(body.get("key", {}).values()) + list(body.get("unlock", []))
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("item"), str):
                recipe_refs.add(row["item"])
        result = body.get("result")
        result_rows = result if isinstance(result, list) else [result]
        for row in result_rows:
            value = row.get("item") if isinstance(row, dict) else row
            if isinstance(value, str):
                recipe_refs.add(value); recipe_results.append(value)
            else:
                errors.append(f"missing_recipe_result:{path}")

    loot_files = json_files(bp / "loot_tables")
    loot_refs: set[str] = set()
    for path in loot_files:
        walk_item_refs(parsed.get(path, {}), loot_refs)

    custom = set(entities) | set(items) | set(blocks)
    namespace = authority["namespace"] + ":"
    for category, identifiers in (("entity", entities), ("item", items), ("block", blocks), ("recipe", recipes)):
        for identifier in identifiers:
            if not identifier.startswith(namespace):
                errors.append(f"identifier_outside_successor_namespace:{category}:{identifier}")
    for reference in sorted(recipe_refs | loot_refs):
        if reference.startswith(namespace) and reference not in custom:
            errors.append(f"unresolved_custom_item_reference:{reference}")

    for identifier, path in entities.items():
        entity = parsed[path]["minecraft:entity"]
        loot_path = entity.get("components", {}).get("minecraft:loot", {}).get("table")
        if isinstance(loot_path, str) and not (bp / loot_path).is_file():
            errors.append(f"missing_entity_loot_table:{identifier}:{loot_path}")
    for identifier in spawn_rules:
        if identifier not in entities:
            errors.append(f"spawn_rule_without_entity:{identifier}")

    for identifier, path in feature_rules.items():
        expected_stem = path.name.removesuffix(".json")
        if identifier.split(":", 1)[1] != expected_stem:
            errors.append(f"feature_rule_filename_identifier_mismatch:{path}:{identifier}")
        feature = parsed[path]["minecraft:feature_rules"].get("description", {}).get("places_feature")
        if isinstance(feature, str) and feature.startswith(namespace) and feature not in features:
            errors.append(f"feature_rule_missing_feature:{identifier}:{feature}")

    structures = sorted((bp / "structures").rglob("*.mcstructure"))
    structure_ids: set[str] = set()
    for path in structures:
        relative = path.relative_to(bp / "structures")
        if len(relative.parts) >= 2:
            namespace = relative.parts[0]
            name = Path(*relative.parts[1:]).with_suffix("").as_posix()
            structure_ids.add(f"{namespace}:{name}")
    structure_ids = {
        f"{path.parent.name}:{path.stem}" if path.parent != bp / "structures" else path.stem
        for path in structures
    }
    for path in structures:
        if path.stat().st_size == 0:
            errors.append(f"empty_structure:{path}")
    for identifier, path in features.items():
        document = parsed[path]
        for key, reference in keyed_strings(document, {"places_block", "feature", "features", "places_feature", "structure_name"}):
            if not reference.startswith(namespace):
                continue
            if key == "places_block" and reference not in blocks:
                errors.append(f"feature_missing_block:{identifier}:{reference}")
            elif key == "structure_name" and reference not in structure_ids:
                errors.append(f"feature_missing_structure:{identifier}:{reference}")
            elif key in {"feature", "features", "places_feature"} and reference not in features:
                errors.append(f"feature_missing_nested_feature:{identifier}:{reference}")

    bp_manifest = parsed.get(bp / "manifest.json", {})
    rp_manifest = parsed.get(rp / "manifest.json", {})
    manifests = [("behavior", bp_manifest), ("resource", rp_manifest)]
    all_uuids: dict[str, str] = {}
    minimum_engine = authority["minimum_engine_version"]
    for label, document in manifests:
        header = document.get("header", {})
        if document.get("format_version") != 2:
            errors.append(f"manifest_format_version:{label}")
        if not version_at_least(header.get("min_engine_version"), minimum_engine):
            errors.append(f"manifest_min_engine_version:{label}:{header.get('min_engine_version')}")
        header_version = header.get("version")
        if not version_at_least(header_version, [0, 0, 1]):
            errors.append(f"manifest_invalid_header_version:{label}:{header_version}")
        for module in document.get("modules", []):
            if isinstance(module, dict) and module.get("version") != header_version:
                errors.append(f"manifest_module_version_mismatch:{label}:{module.get('type')}:{module.get('version')}!={header_version}")
        for location, value in [(f"{label}.header", header.get("uuid"))] + [
            (f"{label}.module", module.get("uuid")) for module in document.get("modules", []) if isinstance(module, dict)
        ]:
            if not isinstance(value, str):
                errors.append(f"manifest_missing_uuid:{location}")
            elif value in all_uuids:
                errors.append(f"manifest_duplicate_uuid:{value}:{all_uuids[value]}:{location}")
            else:
                all_uuids[value] = location
    bp_uuid = bp_manifest.get("header", {}).get("uuid")
    rp_uuid = rp_manifest.get("header", {}).get("uuid")
    bp_version = bp_manifest.get("header", {}).get("version")
    rp_version = rp_manifest.get("header", {}).get("version")
    bp_deps = bp_manifest.get("dependencies", [])
    rp_deps = rp_manifest.get("dependencies", [])
    if not any(dep.get("uuid") == rp_uuid and dep.get("version") == rp_version for dep in bp_deps if isinstance(dep, dict)):
        errors.append("manifest_missing_exact_bp_to_rp_dependency")
    if not any(dep.get("uuid") == bp_uuid and dep.get("version") == bp_version for dep in rp_deps if isinstance(dep, dict)):
        errors.append("manifest_missing_exact_rp_to_bp_dependency")
    for label, dependencies, peer_uuid in (("behavior", bp_deps, rp_uuid), ("resource", rp_deps, bp_uuid)):
        for dependency in dependencies:
            if isinstance(dependency, dict) and "uuid" in dependency and dependency.get("uuid") != peer_uuid:
                errors.append(f"manifest_unresolved_pack_dependency:{label}:{dependency.get('uuid')}")
    script_modules = [module for module in bp_manifest.get("modules", []) if module.get("type") == "script"]
    if len(script_modules) != 1:
        errors.append(f"manifest_script_module_count:{len(script_modules)}")
    else:
        entry = script_modules[0].get("entry")
        if not isinstance(entry, str) or not (bp / entry).is_file():
            errors.append(f"manifest_missing_script_entry:{entry}")
    allowed_modules = set(authority["allowed_script_modules"])
    allowed_module_versions = authority.get("allowed_script_module_versions", {})
    declared_modules: set[str] = set()
    for dep in bp_deps:
        module = dep.get("module_name") if isinstance(dep, dict) else None
        if module:
            declared_modules.add(module)
            version = dep.get("version")
            if module not in allowed_modules:
                errors.append(f"manifest_unapproved_script_module:{module}")
            if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
                errors.append(f"manifest_unstable_script_module_version:{module}:{version}")
            elif module in allowed_module_versions and version != allowed_module_versions[module]:
                errors.append(f"manifest_unapproved_script_module_version:{module}:{version}!={allowed_module_versions[module]}")

    terrain = parsed.get(rp / "textures" / "terrain_texture.json", {}).get("texture_data", {})
    item_atlas = parsed.get(rp / "textures" / "item_texture.json", {}).get("texture_data", {})
    for identifier in blocks:
        key = identifier.split(":", 1)[1]
        if key not in terrain:
            errors.append(f"block_missing_terrain_atlas:{identifier}")
    for identifier in items:
        key = identifier.split(":", 1)[1]
        item = parsed[items[identifier]]["minecraft:item"]
        icon = item.get("components", {}).get("minecraft:icon", {})
        declared = icon.get("textures", {}).get("default") if isinstance(icon, dict) else icon
        atlas_key = declared if isinstance(declared, str) else key
        if atlas_key not in item_atlas:
            errors.append(f"item_missing_item_atlas:{identifier}:{atlas_key}")
    for atlas_name, atlas in (("terrain", terrain), ("items", item_atlas)):
        if not isinstance(atlas, dict):
            errors.append(f"invalid_texture_atlas:{atlas_name}")
            continue
        for key, entry in atlas.items():
            value = entry.get("textures") if isinstance(entry, dict) else entry
            path = texture_path(rp, value)
            if path is None or not path.is_file():
                errors.append(f"atlas_missing_texture:{atlas_name}:{key}:{value}")

    geometries: set[str] = set()
    for path in sorted((rp / "models").rglob("*.json")):
        document = parsed.get(path, {})
        for geometry in document.get("minecraft:geometry", []) if isinstance(document, dict) else []:
            identifier = geometry.get("description", {}).get("identifier")
            if isinstance(identifier, str):
                if identifier in geometries:
                    errors.append(f"duplicate_geometry_identifier:{identifier}:{path}")
                geometries.add(identifier)
    animations: set[str] = set()
    for path in sorted((rp / "animations").rglob("*.json")):
        animations.update(parsed.get(path, {}).get("animations", {}).keys())
    render_controllers: set[str] = set()
    for path in sorted((rp / "render_controllers").rglob("*.json")):
        render_controllers.update(parsed.get(path, {}).get("render_controllers", {}).keys())
    animation_controllers: set[str] = set()
    for path in sorted((rp / "animation_controllers").rglob("*.json")):
        animation_controllers.update(parsed.get(path, {}).get("animation_controllers", {}).keys())

    for identifier, path in client_entities.items():
        if identifier not in entities:
            errors.append(f"client_entity_without_behavior_entity:{identifier}")
        desc = parsed[path]["minecraft:client_entity"]["description"]
        for geometry in desc.get("geometry", {}).values():
            if geometry not in geometries:
                errors.append(f"client_entity_missing_geometry:{identifier}:{geometry}")
        for animation in desc.get("animations", {}).values():
            if isinstance(animation, str):
                if animation.startswith("animation.controller.") and animation not in animation_controllers:
                    errors.append(f"client_entity_missing_animation_controller:{identifier}:{animation}")
                elif animation.startswith("animation.") and animation not in animations:
                    errors.append(f"client_entity_missing_animation:{identifier}:{animation}")
        for controller in desc.get("render_controllers", []):
            value = controller if isinstance(controller, str) else next(iter(controller), "") if isinstance(controller, dict) else ""
            if value and value not in render_controllers:
                errors.append(f"client_entity_missing_render_controller:{identifier}:{value}")
        for texture in desc.get("textures", {}).values():
            resolved = texture_path(rp, texture)
            if resolved is None or not resolved.is_file():
                errors.append(f"client_entity_missing_texture:{identifier}:{texture}")

    for identifier, path in attachables.items():
        if identifier not in items:
            errors.append(f"attachable_without_item:{identifier}")
        desc = parsed[path]["minecraft:attachable"]["description"]
        for geometry in desc.get("geometry", {}).values():
            if isinstance(geometry, str) and geometry.startswith("geometry.aionbound.") and geometry not in geometries:
                errors.append(f"attachable_missing_geometry:{identifier}:{geometry}")
        for controller in desc.get("render_controllers", []):
            value = controller if isinstance(controller, str) else next(iter(controller), "") if isinstance(controller, dict) else ""
            if value.startswith("controller.render.aionbound.") and value not in render_controllers:
                errors.append(f"attachable_missing_render_controller:{identifier}:{value}")
        for texture in desc.get("textures", {}).values():
            if isinstance(texture, str) and texture.startswith("textures/aionbound/"):
                resolved = texture_path(rp, texture)
                if resolved is None or not resolved.is_file():
                    errors.append(f"attachable_missing_texture:{identifier}:{texture}")

    for identifier, path in blocks.items():
        components = parsed[path]["minecraft:block"].get("components", {})
        geometry = components.get("minecraft:geometry")
        if isinstance(geometry, dict):
            geometry = geometry.get("identifier")
        if isinstance(geometry, str) and geometry not in {"geometry.full_block", "minecraft:geometry.full_block"} and geometry not in geometries:
            errors.append(f"block_missing_geometry:{identifier}:{geometry}")
        materials = components.get("minecraft:material_instances", {})
        if isinstance(materials, dict):
            for material in materials.values():
                texture = material.get("texture") if isinstance(material, dict) else None
                if isinstance(texture, str) and texture not in terrain:
                    errors.append(f"block_missing_material_texture:{identifier}:{texture}")

    scripts = sorted((bp / "scripts").rglob("*.js"))
    forbidden_patterns = {
        "node_builtin": re.compile(r"(?:from\s+|import\s*\(\s*)[\"']node:"),
        "commonjs_require": re.compile(r"\brequire\s*\("),
        "filesystem": re.compile(r"\b(?:fs|child_process)\b"),
        "process": re.compile(r"\bprocess(?:\.|\[)"),
        "deno": re.compile(r"\bDeno\."),
        "external_network": re.compile(r"\b(?:fetch|WebSocket)\s*\("),
        "dynamic_code": re.compile(r"\b(?:eval|Function)\s*\("),
    }
    imported_bare: set[str] = set()
    for path in scripts:
        source = path.read_text(encoding="utf-8")
        for name, pattern in forbidden_patterns.items():
            if pattern.search(source):
                errors.append(f"forbidden_runtime:{name}:{path}")
        for specifier in IMPORT.findall(source):
            if specifier.startswith("."):
                target = (path.parent / specifier)
                if target.suffix == "":
                    target = target.with_suffix(".js")
                if not target.is_file():
                    errors.append(f"missing_relative_script_import:{path}:{specifier}")
            else:
                imported_bare.add(specifier)
    for module in imported_bare:
        if module not in allowed_modules:
            errors.append(f"unapproved_script_import:{module}")
        if module not in declared_modules:
            errors.append(f"undeclared_script_import:{module}")

    inventory = {
        "blocks": len(blocks), "entities": len(entities), "items": len(items),
        "loot_tables": len(loot_files), "recipes": len(recipes),
        "spawn_rules": len(spawn_rules), "structures": len(structures),
        "features": len(features), "feature_rules": len(feature_rules),
        "client_entities": len(client_entities), "attachables": len(attachables),
        "geometries": len(geometries), "animations": len(animations),
        "render_controllers": len(render_controllers), "animation_controllers": len(animation_controllers),
        "png_files": len(list(rp.rglob("*.png"))),
        "json_files": len(parsed), "script_files": len(scripts),
    }
    pack_digest, pack_file_count = pack_tree_sha256(bp, rp)
    source_evidence = {"pack_source_sha256": pack_digest, "pack_source_file_count": pack_file_count}
    for category, minimum in authority["minimum_inventory"].items():
        actual = inventory.get(category, 0)
        if actual < minimum:
            errors.append(f"inventory_below_minimum:{category}:{actual}<{minimum}")
    id_sets = {
        "blocks": set(blocks), "entities": set(entities), "items": set(items),
        "recipes": set(recipes), "structures": structure_ids,
        "features": set(features), "feature_rules": set(feature_rules),
    }
    for category, required in authority["required_successor_ids"].items():
        missing = sorted(set(required) - id_sets.get(category, set()))
        for identifier in missing:
            errors.append(f"missing_required_successor_id:{category}:{identifier}")

    if errors:
        raise ValidationFailure(errors, {
            "authority": str(AUTHORITY_REL),
            "authority_sha256": sha256(authority_path),
            "inventory": inventory,
            "source_evidence": source_evidence,
        })
    return {
        "schema_version": 1,
        "status": "PASS",
        "validator": "tools/validate_wave1.py",
        "authority": str(AUTHORITY_REL),
        "authority_sha256": sha256(authority_path),
        "source_evidence": source_evidence,
        "inventory": inventory,
        "required_successor_ids_verified": authority["required_successor_ids"],
        "checks": [
            "json_and_png_structure", "manifest_and_dependency_closure", "identifier_closure",
            "texture_and_model_closure", "recipe_and_loot_closure", "script_import_and_runtime_policy",
            "minimum_substrate_inventory", "explicit_successor_additions",
        ],
        "proof_boundaries": PROOF_BOUNDARIES,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        report = validate(args.root)
    except ValidationFailure as exc:
        report = {
            "schema_version": 1, "status": "FAIL", "validator": "tools/validate_wave1.py",
            "findings": exc.findings, "proof_boundaries": PROOF_BOUNDARIES,
        }
        report.update(exc.evidence)
    except Exception as exc:  # fail closed and retain a machine-readable result
        report = {
            "schema_version": 1, "status": "FAIL", "validator": "tools/validate_wave1.py",
            "findings": [f"validator_exception:{type(exc).__name__}:{exc}"],
            "proof_boundaries": PROOF_BOUNDARIES,
        }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    stream = sys.stdout if report["status"] == "PASS" else sys.stderr
    stream.write(rendered)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
