from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


RELEASABLE_RIGHTS_STATES = {"original_generated", "licensed_reuse", "public_domain"}
REQUIRED_AUTHORING_INPUTS = (
    "project_id",
    "asset_id",
    "asset_class",
    "asset_manifest",
    "template_family",
    "gameplay_role",
    "visual_intent",
    "style_profile",
    "silhouette_requirements",
    "geometry_budget",
    "texture_budget",
    "bone_contract",
    "pivot_contract",
    "locator_contract",
    "animation_contract",
    "collision_contract",
    "visible_bounds_contract",
    "bedrock_target_profile",
    "rights_policy",
    "deterministic_seed",
    "reference_restrictions",
    "source_files",
    "blockbench_version",
    "exporter_version",
    "native_roundtrip",
)


class AssetContractError(ValueError):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bbmodel_hash(document: Mapping[str, Any]) -> str:
    """Hash semantic project content while excluding editor-local volatile fields."""
    ignored = {
        "saved",
        "path",
        "backup",
        "last_used_export_path",
        "last_used_animation_path",
        "export_path",
    }

    def normalize(value: Any, key: str | None = None) -> Any:
        if isinstance(value, Mapping):
            return {
                str(child_key): normalize(child, str(child_key))
                for child_key, child in sorted(value.items(), key=lambda row: str(row[0]))
                if str(child_key) not in ignored
            }
        if isinstance(value, list):
            return [normalize(child, key) for child in value]
        if key == "relative_path" and isinstance(value, str):
            return Path(value).name
        return value

    return sha256_bytes(canonical_json(normalize(document)))


def _finite_vector(value: Any, *, size: int = 3) -> bool:
    return (
        isinstance(value, list)
        and len(value) == size
        and all(isinstance(item, (int, float)) and not isinstance(item, bool) and math.isfinite(item) for item in value)
    )


def validate_geometry(
    document: Mapping[str, Any],
    *,
    namespace: str,
    required_bones: Sequence[str],
    required_locators: Sequence[str],
    texture_size: tuple[int, int],
) -> dict[str, Any]:
    geometries = document.get("minecraft:geometry")
    if document.get("format_version") != "1.12.0" or not isinstance(geometries, list) or len(geometries) != 1:
        raise AssetContractError("Bedrock geometry must use format 1.12.0 and contain exactly one geometry")
    geometry = geometries[0]
    if not isinstance(geometry, Mapping):
        raise AssetContractError("Geometry entry must be an object")
    description = geometry.get("description")
    bones = geometry.get("bones")
    if not isinstance(description, Mapping) or not isinstance(bones, list):
        raise AssetContractError("Geometry description and bones are required")
    identifier = description.get("identifier")
    if not isinstance(identifier, str) or not identifier.startswith(f"geometry.{namespace}."):
        raise AssetContractError(f"Geometry identifier must use namespace {namespace}")
    if (description.get("texture_width"), description.get("texture_height")) != texture_size:
        raise AssetContractError("Geometry texture dimensions do not match the asset contract")
    names = [str(row.get("name")) for row in bones if isinstance(row, Mapping)]
    if len(names) != len(set(names)):
        raise AssetContractError("Duplicate bone names are not allowed")
    missing_bones = sorted(set(required_bones) - set(names))
    if missing_bones:
        raise AssetContractError(f"Missing required bones: {', '.join(missing_bones)}")
    parents = {
        str(row["name"]): str(row["parent"])
        for row in bones
        if isinstance(row, Mapping) and isinstance(row.get("name"), str) and isinstance(row.get("parent"), str)
    }
    for child, parent in parents.items():
        if parent not in names:
            raise AssetContractError(f"Bone {child} references missing parent {parent}")
        seen = {child}
        cursor = parent
        while cursor in parents:
            if cursor in seen:
                raise AssetContractError("Bone parent cycle detected")
            seen.add(cursor)
            cursor = parents[cursor]
    locator_names: set[str] = set()
    cube_count = 0
    for bone in bones:
        if not isinstance(bone, Mapping) or not _finite_vector(bone.get("pivot")):
            raise AssetContractError("Every bone requires a finite three-component pivot")
        locators = bone.get("locators", {})
        if locators is not None and not isinstance(locators, Mapping):
            raise AssetContractError("Bone locators must be an object")
        for name, location in (locators or {}).items():
            if not _finite_vector(location):
                raise AssetContractError(f"Locator {name} must be a finite three-component vector")
            locator_names.add(str(name))
        cubes = bone.get("cubes", [])
        if not isinstance(cubes, list):
            raise AssetContractError("Bone cubes must be an array")
        for cube in cubes:
            if not isinstance(cube, Mapping) or not _finite_vector(cube.get("origin")) or not _finite_vector(cube.get("size")):
                raise AssetContractError("Every cube requires finite origin and size vectors")
            cube_count += 1
    missing_locators = sorted(set(required_locators) - locator_names)
    if missing_locators:
        raise AssetContractError(f"Missing required locators: {', '.join(missing_locators)}")
    for field in ("visible_bounds_width", "visible_bounds_height"):
        value = description.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
            raise AssetContractError(f"{field} must be a positive finite number")
    if not _finite_vector(description.get("visible_bounds_offset")):
        raise AssetContractError("visible_bounds_offset must be a finite three-component vector")
    return {
        "identifier": identifier,
        "bone_count": len(names),
        "cube_count": cube_count,
        "locator_count": len(locator_names),
        "bones": names,
        "locators": sorted(locator_names),
    }


def validate_animation_contract(
    animations: Mapping[str, Any],
    controller: Mapping[str, Any],
    *,
    required_clips: Sequence[str],
    required_states: Sequence[str],
    bones: Sequence[str],
) -> dict[str, Any]:
    clips = animations.get("animations")
    controllers = controller.get("animation_controllers")
    if not isinstance(clips, Mapping) or not isinstance(controllers, Mapping) or len(controllers) != 1:
        raise AssetContractError("Animation and single-controller documents are required")
    missing_clips = sorted(set(required_clips) - set(map(str, clips)))
    if missing_clips:
        raise AssetContractError(f"Missing required animation clips: {', '.join(missing_clips)}")
    controller_row = next(iter(controllers.values()))
    states = controller_row.get("states") if isinstance(controller_row, Mapping) else None
    if not isinstance(states, Mapping):
        raise AssetContractError("Animation controller states are required")
    missing_states = sorted(set(required_states) - set(map(str, states)))
    if missing_states:
        raise AssetContractError(f"Missing required controller states: {', '.join(missing_states)}")
    animated_bones: set[str] = set()
    keyframe_count = 0
    for clip in clips.values():
        clip_bones = clip.get("bones", {}) if isinstance(clip, Mapping) else {}
        if not isinstance(clip_bones, Mapping):
            raise AssetContractError("Animation bones must be an object")
        for name, channels in clip_bones.items():
            if name not in bones:
                raise AssetContractError(f"Animation references missing bone {name}")
            animated_bones.add(str(name))
            if isinstance(channels, Mapping):
                for value in channels.values():
                    keyframe_count += len(value) if isinstance(value, Mapping) else 1
    transitions = sum(
        len(row.get("transitions", []))
        for row in states.values()
        if isinstance(row, Mapping) and isinstance(row.get("transitions", []), list)
    )
    return {
        "clip_count": len(clips),
        "controller_count": 1,
        "state_count": len(states),
        "transition_count": transitions,
        "animated_bone_count": len(animated_bones),
        "keyframe_count": keyframe_count,
    }


def validate_semantic_coordinates(geometry: Mapping[str, Any]) -> dict[str, Any]:
    """Validate semantic side/front assignments after Blockbench Bedrock conversion."""
    geometry_rows = geometry.get("minecraft:geometry", [])
    bones = geometry_rows[0].get("bones", []) if isinstance(geometry_rows, list) and geometry_rows else []
    pivots = {
        str(row.get("name")): row.get("pivot")
        for row in bones
        if isinstance(row, Mapping) and isinstance(row.get("name"), str)
    }
    pairs = (
        ("front_left_leg", "front_right_leg", 2, -1),
        ("back_left_leg", "back_right_leg", 2, 1),
    )
    for left, right, front_axis, expected_z_sign in pairs:
        left_pivot, right_pivot = pivots.get(left), pivots.get(right)
        if not _finite_vector(left_pivot) or not _finite_vector(right_pivot):
            raise AssetContractError(f"Semantic leg pivots are missing for {left}/{right}")
        if not (left_pivot[0] < 0 < right_pivot[0]):
            raise AssetContractError(f"Exported semantic left/right assignment is inverted for {left}/{right}")
        if expected_z_sign < 0 and not (left_pivot[front_axis] < 0 and right_pivot[front_axis] < 0):
            raise AssetContractError("Front leg pivots are not in the front half")
        if expected_z_sign > 0 and not (left_pivot[front_axis] > 0 and right_pivot[front_axis] > 0):
            raise AssetContractError("Rear leg pivots are not in the rear half")
    return {"left_right": "PRESERVED", "front_rear": "PRESERVED", "raw_sign_comparison_used": False}


def validate_authoring_parameters(parameters: Mapping[str, Any]) -> None:
    missing = [name for name in REQUIRED_AUTHORING_INPUTS if name not in parameters]
    if missing:
        raise AssetContractError(f"Missing author_blockbench_asset inputs: {', '.join(missing)}")
    if parameters.get("asset_class") not in {"block", "attachable", "item", "prop", "entity", "animal", "boss", "tree"}:
        raise AssetContractError("Unsupported asset_class")
    seed = parameters.get("deterministic_seed")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise AssetContractError("deterministic_seed must be a non-negative integer")
    rights = parameters.get("rights_policy")
    if not isinstance(rights, Mapping) or rights.get("status") not in RELEASABLE_RIGHTS_STATES:
        raise AssetContractError("Only a releasable rights state may enter the authored asset registry")
    roundtrip = parameters.get("native_roundtrip")
    if not isinstance(roundtrip, Mapping) or roundtrip.get("reopened") is not True or roundtrip.get("native_save") is not True:
        raise AssetContractError("Native Blockbench reopen and save evidence is required")
