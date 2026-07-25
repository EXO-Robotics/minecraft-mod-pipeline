#!/usr/bin/env python3
"""Perform conservative static checks on Bedrock geometry and PNG textures."""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a valid PNG")
    return struct.unpack(">II", data[16:24])


def finite_numbers(value: object, location: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            finite_numbers(child, f"{location}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            finite_numbers(child, f"{location}[{index}]", errors)
    elif isinstance(value, float) and not math.isfinite(value):
        errors.append(f"{location} contains a non-finite number")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--texture", type=Path)
    parser.add_argument("--namespace", required=True)
    parser.add_argument(
        "--required-locator",
        action="append",
        default=[],
        help="Locator name that must survive native export; repeat as needed",
    )
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    try:
        document = json.loads(args.geometry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot parse geometry: {exc}")
        return 1

    finite_numbers(document, "$", errors)
    geometries = document.get("minecraft:geometry")
    if not isinstance(geometries, list) or not geometries:
        errors.append("minecraft:geometry must be a non-empty array")
        geometries = []

    total_bones = 0
    total_cubes = 0
    locator_names: set[str] = set()
    for index, geometry in enumerate(geometries):
        description = geometry.get("description", {})
        identifier = description.get("identifier", "")
        expected_prefix = f"geometry.{args.namespace}."
        if not isinstance(identifier, str) or not identifier.startswith(expected_prefix):
            errors.append(
                f"geometry[{index}] identifier must start with {expected_prefix!r}; got {identifier!r}"
            )

        bones = geometry.get("bones", [])
        if not isinstance(bones, list):
            errors.append(f"geometry[{index}].bones must be an array")
            continue
        names = {bone.get("name") for bone in bones if isinstance(bone, dict)}
        total_bones += len(bones)
        for bone_index, bone in enumerate(bones):
            if not isinstance(bone, dict):
                errors.append(f"geometry[{index}].bones[{bone_index}] must be an object")
                continue
            name = bone.get("name")
            if not isinstance(name, str) or not name:
                errors.append(f"geometry[{index}].bones[{bone_index}] has no name")
            parent = bone.get("parent")
            if parent is not None and parent not in names:
                errors.append(f"bone {name!r} references missing parent {parent!r}")
            cubes = bone.get("cubes", [])
            if not isinstance(cubes, list):
                errors.append(f"bone {name!r}.cubes must be an array")
            else:
                total_cubes += len(cubes)
            locators = bone.get("locators", {})
            if not isinstance(locators, dict):
                errors.append(f"bone {name!r}.locators must be an object")
            else:
                for locator_name, locator_value in locators.items():
                    locator_names.add(locator_name)
                    if not isinstance(locator_name, str) or not locator_name:
                        errors.append(f"bone {name!r} contains an invalid locator name")
                    if not (
                        isinstance(locator_value, list)
                        and len(locator_value) == 3
                        and all(isinstance(value, (int, float)) for value in locator_value)
                    ):
                        errors.append(
                            f"locator {locator_name!r} on bone {name!r} "
                            "must be a three-number vector"
                        )

        texture_width = description.get("texture_width")
        texture_height = description.get("texture_height")
        if args.texture:
            try:
                actual_width, actual_height = png_dimensions(args.texture)
                if (texture_width, texture_height) != (actual_width, actual_height):
                    errors.append(
                        "geometry texture dimensions "
                        f"{texture_width}x{texture_height} do not match PNG "
                        f"{actual_width}x{actual_height}"
                    )
            except (OSError, ValueError) as exc:
                errors.append(str(exc))

    if total_bones > 64:
        warnings.append(f"high bone count: {total_bones}")
    if total_cubes > 128:
        warnings.append(f"high cube count: {total_cubes}")
    for required_locator in args.required_locator:
        if required_locator not in locator_names:
            errors.append(
                f"required locator {required_locator!r} is absent from native geometry export"
            )

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(
        f"OK: {len(geometries)} geometry definition(s), "
        f"{total_bones} bone(s), {total_cubes} cube(s), "
        f"{len(locator_names)} locator(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
