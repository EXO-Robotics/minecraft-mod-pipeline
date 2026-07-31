#!/usr/bin/env python3
"""Validate cross-file references and conservative bounds for an animated Bedrock entity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot parse {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--animations", type=Path, required=True)
    parser.add_argument("--controller", type=Path, required=True)
    parser.add_argument("--client-entity", type=Path, required=True)
    parser.add_argument("--behavior-entity", type=Path, required=True)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    try:
        geometry = load(args.geometry)
        animations = load(args.animations).get("animations", {})
        controllers = load(args.controller).get("animation_controllers", {})
        client = load(args.client_entity)["minecraft:client_entity"]["description"]
        behavior = load(args.behavior_entity)["minecraft:entity"]
    except (ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    bones = {
        bone.get("name")
        for item in geometry.get("minecraft:geometry", [])
        for bone in item.get("bones", [])
        if isinstance(bone, dict)
    }
    animated_bones = {
        bone
        for clip in animations.values()
        if isinstance(clip, dict)
        for bone in clip.get("bones", {})
    }
    for bone in sorted(animated_bones - bones):
        errors.append(f"animation references missing bone {bone!r}")

    aliases = client.get("animations", {})
    clip_ids = set(animations)
    controller_ids = set(controllers)
    for alias, target in aliases.items():
        if not isinstance(target, str):
            errors.append(f"client animation alias {alias!r} is not a string")
        elif target.startswith("animation.") and target not in clip_ids:
            errors.append(f"client alias {alias!r} references missing clip {target!r}")
        elif target.startswith("controller.animation.") and target not in controller_ids:
            errors.append(f"client alias {alias!r} references missing controller {target!r}")

    animate_roots = client.get("scripts", {}).get("animate", [])
    for entry in animate_roots:
        alias = entry if isinstance(entry, str) else next(iter(entry), "")
        if alias not in aliases:
            errors.append(f"scripts.animate references missing alias {alias!r}")

    components = behavior.get("components", {})
    movement = components.get("minecraft:movement", {}).get("value")
    if not isinstance(movement, (int, float)) or movement <= 0:
        errors.append("minecraft:movement.value must be positive")
    elif movement > 0.5:
        warnings.append(f"high base movement speed: {movement}")

    stroll = components.get("minecraft:behavior.random_stroll")
    if stroll:
        interval = stroll.get("interval", 0)
        if not isinstance(interval, int) or interval <= 0:
            warnings.append("random_stroll should use a positive interval for bounded path requests")

    priorities: list[tuple[str, int]] = []
    for name, component in components.items():
        if name.startswith("minecraft:behavior.") and isinstance(component, dict):
            priority = component.get("priority")
            if isinstance(priority, int):
                priorities.append((name, priority))
            else:
                errors.append(f"{name} must have an integer priority")

    if "minecraft:navigation.walk" not in components:
        warnings.append("no minecraft:navigation.walk component")
    if behavior.get("description", {}).get("is_experimental"):
        errors.append("entity is marked experimental")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(
        f"OK: {len(clip_ids)} clip(s), {len(controller_ids)} controller(s), "
        f"{len(animated_bones)} animated bone(s), {len(priorities)} AI goal(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
