#!/usr/bin/env python3
"""Deterministically stage safe Packet 001 asset normalization.

This tool never writes to a behavior pack or resource pack.  It emits only to
an empty caller-supplied staging directory.  Assets with unresolved creative
references or incomplete native custom-geometry evidence are described in the
manifest but are not copied into the promotable tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SOURCE_NAMESPACE = "aionforge_ww"
SHIPPING_NAMESPACE = "aionbound"
MANIFEST_NAME = "WHISPERWOOD_IMPORT_MANIFEST.json"
ID_RE = re.compile(r"^[a-z0-9_]+$")
TIER_CATEGORIES = {
    "BLOCK": "blocks",
    "CREATURE": "creatures",
    "LANDMARK": "structures",
    "PLANT": "plants",
    "RESOURCE": "resources",
}


class ImportFailure(RuntimeError):
    """Raised when the importer cannot establish a safe, deterministic input."""


@dataclass(frozen=True)
class AssetPaths:
    brief: Path
    bbmodel: Path
    geometry: Path
    animations: Path
    texture: Path


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImportFailure(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ImportFailure(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _asset_paths(packet_root: Path, asset_id: str) -> AssetPaths:
    assets = packet_root / "assets"
    return AssetPaths(
        brief=assets / "briefs" / f"{asset_id}.json",
        bbmodel=assets / "editable" / f"{asset_id}.bbmodel",
        geometry=assets / "export" / "models" / f"{asset_id}.geo.json",
        animations=assets / "export" / "animations" / f"{asset_id}.animation.json",
        texture=assets / "export" / "textures" / f"{asset_id}.png",
    )


def _discover_asset_ids(packet_root: Path) -> list[str]:
    briefs = packet_root / "assets" / "briefs"
    if not briefs.is_dir():
        raise ImportFailure(f"missing canonical briefs directory: {briefs}")
    asset_ids = sorted(path.stem for path in briefs.glob("*.json"))
    if not asset_ids:
        raise ImportFailure(f"no canonical briefs found: {briefs}")
    invalid = [asset_id for asset_id in asset_ids if not ID_RE.fullmatch(asset_id)]
    if invalid:
        raise ImportFailure(f"invalid canonical asset IDs: {invalid}")
    if len(asset_ids) != len(set(asset_ids)):
        raise ImportFailure("duplicate canonical asset IDs")
    return asset_ids


def _require_files(paths: AssetPaths) -> None:
    missing = [str(path) for path in paths.__dict__.values() if not path.is_file()]
    if missing:
        raise ImportFailure("missing canonical asset files: " + ", ".join(missing))


def _native_locator_names(bbmodel: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for element in bbmodel.get("elements", []):
        if isinstance(element, dict) and element.get("type") == "locator":
            name = element.get("name")
            if isinstance(name, str) and name:
                names.add(name)
    return names


def _geometry_locator_names(geometry: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    entries = geometry.get("minecraft:geometry", [])
    if not isinstance(entries, list):
        return names
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for bone in entry.get("bones", []):
            if isinstance(bone, dict) and isinstance(bone.get("locators"), dict):
                names.update(str(name) for name in bone["locators"])
    return names


def _animation_suffixes(animations: dict[str, Any], asset_id: str) -> set[str]:
    values = animations.get("animations", {})
    if not isinstance(values, dict):
        return set()
    prefix = f"animation.{SOURCE_NAMESPACE}.{asset_id}."
    return {name[len(prefix) :] for name in values if isinstance(name, str) and name.startswith(prefix)}


def _parse_related_assets(raw: Any, warehouse_ids: set[str]) -> tuple[list[str], list[str]]:
    if raw is None or raw == "":
        return [], []
    if not isinstance(raw, str):
        return [], ["related_assets must be a comma-separated string"]
    resolved: list[str] = []
    ambiguous: list[str] = []
    for token in (part.strip() for part in raw.split(",")):
        if not token:
            ambiguous.append("empty related_assets token")
        elif token in warehouse_ids:
            resolved.append(token)
        else:
            ambiguous.append(token)
    return sorted(set(resolved)), ambiguous


def _geometry_description(geometry: dict[str, Any]) -> dict[str, Any]:
    entries = geometry.get("minecraft:geometry")
    if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
        raise ImportFailure("geometry must contain exactly one minecraft:geometry object")
    description = entries[0].get("description")
    if not isinstance(description, dict):
        raise ImportFailure("geometry description is missing")
    return description


def _validate_source_identity(
    asset_id: str,
    brief: dict[str, Any],
    bbmodel: dict[str, Any],
    geometry: dict[str, Any],
) -> None:
    source_geometry_id = f"geometry.{SOURCE_NAMESPACE}.{asset_id}"
    if brief.get("model_identifier") != source_geometry_id:
        raise ImportFailure(f"brief model identifier mismatch for {asset_id}")
    if bbmodel.get("model_identifier") != source_geometry_id:
        raise ImportFailure(f"bbmodel model identifier mismatch for {asset_id}")
    if _geometry_description(geometry).get("identifier") != source_geometry_id:
        raise ImportFailure(f"geometry identifier mismatch for {asset_id}")


def _category(brief: dict[str, Any], asset_id: str) -> str:
    tier = brief.get("tier")
    if tier not in TIER_CATEGORIES:
        raise ImportFailure(f"unknown brief tier for {asset_id}: {tier!r}")
    return TIER_CATEGORIES[tier]


def _is_plain_full_cube(brief: dict[str, Any], geometry: dict[str, Any]) -> bool:
    if brief.get("profile") != "block" or brief.get("animations") not in (None, []):
        return False
    entries = geometry.get("minecraft:geometry", [])
    if not isinstance(entries, list) or len(entries) != 1:
        return False
    cubes: list[dict[str, Any]] = []
    for bone in entries[0].get("bones", []):
        if isinstance(bone, dict):
            cubes.extend(cube for cube in bone.get("cubes", []) if isinstance(cube, dict))
    if len(cubes) != 1:
        return False
    cube = cubes[0]
    return cube.get("origin") == [-8, 0, -8] and cube.get("size") == [16, 16, 16] and not cube.get("rotation")


def _simple_disposition(brief: dict[str, Any], geometry: dict[str, Any]) -> str | None:
    # A model's UV atlas is not an inventory icon.  Texture-only promotion is
    # legal only when the brief explicitly binds that PNG as the shipping icon.
    if (
        brief.get("profile") == "item"
        and brief.get("animations") in (None, [])
        and brief.get("shipping_representation") == "flat_inventory_icon"
    ):
        return "PROMOTABLE_SIMPLE_TEXTURE_ITEM_BLOCKBENCH_NOT_APPLICABLE"
    if _is_plain_full_cube(brief, geometry):
        return "PROMOTABLE_SIMPLE_FULL_CUBE_BLOCKBENCH_NOT_APPLICABLE"
    return None


def _replace_prefix(value: str, source: str, target: str, label: str) -> str:
    if not value.startswith(source):
        raise ImportFailure(f"unexpected {label}: {value}")
    return target + value[len(source) :]


def _normalize_custom(
    asset_id: str,
    brief: dict[str, Any],
    bbmodel: dict[str, Any],
    geometry: dict[str, Any],
    animations: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    shipping_geometry_id = f"geometry.{SHIPPING_NAMESPACE}.{asset_id}"
    _validate_source_identity(asset_id, brief, bbmodel, geometry)

    normalized_brief = json.loads(json.dumps(brief))
    normalized_brief["model_identifier"] = shipping_geometry_id
    normalized_brief["editable"] = f"editable/{asset_id}.bbmodel"
    normalized_brief["runtime_identifier"] = f"{SHIPPING_NAMESPACE}:{asset_id}"
    normalized_brief["source_namespace"] = SOURCE_NAMESPACE

    normalized_bbmodel = json.loads(json.dumps(bbmodel))
    normalized_bbmodel["model_identifier"] = shipping_geometry_id
    for texture in normalized_bbmodel.get("textures", []):
        if not isinstance(texture, dict):
            raise ImportFailure(f"invalid bbmodel texture entry for {asset_id}")
        if texture.get("name") != f"{asset_id}.png":
            raise ImportFailure(f"unexpected bbmodel texture name for {asset_id}")
        texture["path"] = f"../textures/{asset_id}.png"
        texture["relative_path"] = f"../textures/{asset_id}.png"
    for animation in normalized_bbmodel.get("animations", []):
        if not isinstance(animation, dict) or not isinstance(animation.get("name"), str):
            raise ImportFailure(f"invalid bbmodel animation entry for {asset_id}")
        animation["name"] = _replace_prefix(
            animation["name"],
            f"animation.{SOURCE_NAMESPACE}.{asset_id}.",
            f"animation.{SHIPPING_NAMESPACE}.{asset_id}.",
            "bbmodel animation identifier",
        )

    normalized_geometry = json.loads(json.dumps(geometry))
    _geometry_description(normalized_geometry)["identifier"] = shipping_geometry_id

    normalized_animations = json.loads(json.dumps(animations))
    source_animations = normalized_animations.get("animations")
    if not isinstance(source_animations, dict):
        raise ImportFailure(f"animations object missing for {asset_id}")
    rewritten: dict[str, Any] = {}
    for name in sorted(source_animations):
        if not isinstance(name, str):
            raise ImportFailure(f"non-string animation identifier for {asset_id}")
        shipping_name = _replace_prefix(
            name,
            f"animation.{SOURCE_NAMESPACE}.{asset_id}.",
            f"animation.{SHIPPING_NAMESPACE}.{asset_id}.",
            "exported animation identifier",
        )
        if shipping_name in rewritten:
            raise ImportFailure(f"animation identifier collision for {asset_id}")
        rewritten[shipping_name] = source_animations[name]
    normalized_animations["animations"] = rewritten
    return normalized_brief, normalized_bbmodel, normalized_geometry, normalized_animations


def _stage_simple(
    destination: Path,
    asset_id: str,
    category: str,
    disposition: str,
    brief: dict[str, Any],
    texture: Path,
    related_assets: list[str],
) -> list[Path]:
    root = destination / "promotable" / category / asset_id
    normalized_brief = json.loads(json.dumps(brief))
    normalized_brief["model_identifier"] = None
    normalized_brief["editable"] = None
    normalized_brief["runtime_identifier"] = f"{SHIPPING_NAMESPACE}:{asset_id}"
    normalized_brief["source_namespace"] = SOURCE_NAMESPACE
    normalized_brief["resolved_related_assets"] = related_assets
    normalized_brief["native_blockbench_disposition"] = disposition
    brief_path = root / "briefs" / f"{asset_id}.json"
    texture_path = root / "textures" / f"{asset_id}.png"
    _write_json(brief_path, normalized_brief)
    texture_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(texture, texture_path)
    return [brief_path, texture_path]


def _stage_custom(
    destination: Path,
    asset_id: str,
    category: str,
    normalized: tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]],
    texture: Path,
    related_assets: list[str],
) -> list[Path]:
    root = destination / "promotable" / category / asset_id
    brief, bbmodel, geometry, animations = normalized
    brief["resolved_related_assets"] = related_assets
    brief["native_blockbench_disposition"] = "PROMOTABLE_CUSTOM_GEOMETRY_STATIC_ONLY"
    paths = [
        root / "briefs" / f"{asset_id}.json",
        root / "editable" / f"{asset_id}.bbmodel",
        root / "geometry" / f"{asset_id}.geo.json",
        root / "animations" / f"{asset_id}.animation.json",
    ]
    for path, value in zip(paths, normalized, strict=True):
        _write_json(path, value)
    texture_path = root / "textures" / f"{asset_id}.png"
    texture_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(texture, texture_path)
    return paths + [texture_path]


def import_packet(packet_root: Path, destination: Path) -> dict[str, Any]:
    packet_root = packet_root.resolve()
    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ImportFailure(f"staging directory must be empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    asset_ids = _discover_asset_ids(packet_root)
    warehouse_ids = set(asset_ids)
    records: list[dict[str, Any]] = []
    for asset_id in asset_ids:
        paths = _asset_paths(packet_root, asset_id)
        _require_files(paths)
        brief = _read_json(paths.brief)
        bbmodel = _read_json(paths.bbmodel)
        geometry = _read_json(paths.geometry)
        animations = _read_json(paths.animations)
        if brief.get("name") != asset_id:
            raise ImportFailure(f"brief name mismatch for {asset_id}")
        _validate_source_identity(asset_id, brief, bbmodel, geometry)

        category = _category(brief, asset_id)
        simple = _simple_disposition(brief, geometry)
        resolved_related, ambiguous_related = _parse_related_assets(brief.get("related_assets"), warehouse_ids)
        required_locators = sorted(set(brief.get("locators") or []))
        required_clips = sorted(set(brief.get("animations") or []))
        native_locators = _native_locator_names(bbmodel)
        exported_locators = _geometry_locator_names(geometry)
        clip_suffixes = _animation_suffixes(animations, asset_id)

        blockers: list[str] = []
        if ambiguous_related:
            blockers.append("AMBIGUOUS_RELATED_ASSETS")
        if simple is None:
            if missing := sorted(set(required_locators) - native_locators):
                blockers.append("MISSING_NATIVE_BBMODEL_LOCATORS:" + ",".join(missing))
            if missing := sorted(set(required_locators) - exported_locators):
                blockers.append("MISSING_EXPORTED_GEOMETRY_LOCATORS:" + ",".join(missing))
            if missing := sorted(set(required_clips) - clip_suffixes):
                blockers.append("MISSING_REQUIRED_ROLE_CLIPS:" + ",".join(missing))

        emitted: list[Path] = []
        if not blockers:
            if simple is not None:
                disposition = simple
                emitted = _stage_simple(
                    destination, asset_id, category, disposition, brief, paths.texture, resolved_related
                )
            else:
                disposition = "PROMOTABLE_CUSTOM_GEOMETRY_STATIC_ONLY"
                emitted = _stage_custom(
                    destination,
                    asset_id,
                    category,
                    _normalize_custom(asset_id, brief, bbmodel, geometry, animations),
                    paths.texture,
                    resolved_related,
                )
        else:
            disposition = "NATIVE_REPAIR_REQUIRED_CUSTOM_GEOMETRY" if simple is None else "BLOCKED_SIMPLE_ASSET"

        records.append(
            {
                "asset_id": asset_id,
                "ambiguous_related_assets": ambiguous_related,
                "blockers": blockers,
                "category": category,
                "disposition": disposition,
                "emitted": [str(path.relative_to(destination)) for path in emitted],
                "required_role_clips": required_clips,
                "required_locators": required_locators,
                "resolved_related_assets": resolved_related,
                "runtime_identifier": f"{SHIPPING_NAMESPACE}:{asset_id}",
                "source_hashes": {
                    field: _sha256(path) for field, path in sorted(paths.__dict__.items())
                },
            }
        )

    blocked = [record for record in records if record["blockers"]]
    manifest = {
        "schema": "aionbound.wave1.whisperwood-import-manifest.v1",
        "packet": "001_whisperwood",
        "proof_boundary": {
            "bedrock_client": "NOT_RUN",
            "blockbench_native_roundtrip": "NOT_RUN",
            "candidate_declared": False,
            "shipping_bp_rp_mutated": False,
            "static_normalization": "RUN",
        },
        "source_namespace": SOURCE_NAMESPACE,
        "shipping_namespace": SHIPPING_NAMESPACE,
        "status": "BLOCKED_NATIVE_OR_CREATIVE_REPAIR_REQUIRED" if blocked else "STATIC_STAGING_COMPLETE",
        "summary": {
            "asset_count": len(records),
            "blocked_count": len(blocked),
            "promotable_count": len(records) - len(blocked),
        },
        "assets": records,
    }
    _write_json(destination / MANIFEST_NAME, manifest)
    return manifest


def _parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--staging-dir", type=Path, required=True)
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        manifest = import_packet(args.packet_root, args.staging_dir)
    except ImportFailure as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest["summary"], sort_keys=True))
    return 2 if manifest["summary"]["blocked_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
