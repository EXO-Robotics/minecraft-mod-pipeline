#!/usr/bin/env python3
"""Author bounded Crystal Marsh plant ecology without cross-biome tuning."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
BP = REPO / "behavior_pack"
OUT = Path(__file__).resolve().parent
SURFACE = "q.heightmap(v.worldx, v.worldz)"
MARSH_GROUND = [
    "aionbound:marsh_soil",
    "aionbound:wet_clay_block",
    "aionbound:crystal_gravel",
    "minecraft:mud",
    "minecraft:clay",
]
CRYSTAL_SHADE = [
    "aionbound:marsh_soil",
    "aionbound:glass_root_block",
    "aionbound:crystal_stone",
    "aionbound:crystal_gravel",
]
CHANNEL_ATTACHMENTS = [
    "aionbound:crystal_log",
    "aionbound:marsh_wood",
    "aionbound:glass_root_block",
    "aionbound:crystal_stone",
    "aionbound:prism_brick",
]


@dataclass(frozen=True)
class Spec:
    asset: str
    locality: str
    habitat: str
    faces: str
    supports: tuple[str, ...]
    iterations: int
    denominator: int
    y: object
    replace_water: bool = False


SPECS = [
    Spec("pearl_grass", "low islets", "wetland_surface", "bottom", tuple(MARSH_GROUND), 3, 12, SURFACE),
    Spec("marsh_fern", "sheltered banks", "wetland_surface", "bottom", tuple(MARSH_GROUND), 2, 16, SURFACE),
    Spec("flood_reed", "shallow reed seas", "shallow_water", "bottom", tuple(MARSH_GROUND), 4, 16, SURFACE, True),
    Spec("glass_moss", "crystal shade", "wetland_surface", "bottom", tuple(CRYSTAL_SHADE), 2, 24, SURFACE),
    Spec("glow_kelp", "deep basin water", "submerged", "bottom", tuple(MARSH_GROUND), 2, 32, {"distribution": "uniform", "extent": [40, 58]}, True),
    Spec("bubble_pod", "quiet shallows", "shallow_water", "bottom", tuple(MARSH_GROUND), 1, 24, SURFACE, True),
    Spec("crystal_lily", "still pools", "shallow_water", "bottom", tuple(MARSH_GROUND), 1, 32, SURFACE, True),
    Spec("crystal_vine", "flooded channels", "submerged_attachment", "all", tuple(CHANNEL_ATTACHMENTS), 2, 32, {"distribution": "uniform", "extent": [42, 62]}, True),
    Spec("mire_orchid", "rare mire pocket", "wetland_surface", "bottom", tuple(MARSH_GROUND), 1, 128, SURFACE),
    Spec("prism_bloom", "crystal clearing", "wetland_surface", "bottom", tuple(CRYSTAL_SHADE), 1, 64, SURFACE),
]


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def feature(spec: Spec) -> dict:
    attach = {
        "min_sides_must_attach": 1,
        "auto_rotate": spec.faces == "all",
        spec.faces: list(spec.supports),
    }
    may_replace = ["minecraft:water"] if spec.replace_water else ["minecraft:air"]
    return {
        "format_version": "1.21.40",
        "minecraft:single_block_feature": {
            "description": {"identifier": f"aionbound:cm_ecology_{spec.asset}"},
            "places_block": f"aionbound:{spec.asset}",
            "enforce_placement_rules": True,
            "enforce_survivability_rules": True,
            "may_replace": may_replace,
            "may_attach_to": attach,
        },
    }


def rule(spec: Spec) -> dict:
    return {
        "format_version": "1.21.40",
        "minecraft:feature_rules": {
            "description": {
                "identifier": f"aionbound:cm_ecology_{spec.asset}.feature_rule",
                "places_feature": f"aionbound:cm_ecology_{spec.asset}",
            },
            "conditions": {
                "placement_pass": "surface_pass",
                "minecraft:biome_filter": {
                    "all_of": [
                        {"test": "has_biome_tag", "operator": "==", "value": "overworld"},
                        {"test": "has_biome_tag", "operator": "!=", "value": "ocean"},
                        {
                            "any_of": [
                                {"test": "has_biome_tag", "operator": "==", "value": "swamp"},
                                {"test": "has_biome_tag", "operator": "==", "value": "river"},
                            ]
                        },
                    ]
                },
            },
            "distribution": {
                "coordinate_eval_order": "xzy",
                "iterations": spec.iterations,
                "scatter_chance": {"numerator": 1, "denominator": spec.denominator},
                "x": {"distribution": "uniform", "extent": [0, 15]},
                "y": spec.y,
                "z": {"distribution": "uniform", "extent": [0, 15]},
            },
        },
    }


def outputs() -> tuple[dict[Path, bytes], dict]:
    files: dict[Path, bytes] = {}
    rows = []
    for spec in SPECS:
        feature_path = BP / "features" / f"cm_ecology_{spec.asset}.feature.json"
        rule_path = BP / "feature_rules" / f"cm_ecology_{spec.asset}.feature_rule.json"
        feature_bytes = encoded(feature(spec))
        rule_bytes = encoded(rule(spec))
        files[feature_path] = feature_bytes
        files[rule_path] = rule_bytes
        rows.append({
            "asset": spec.asset,
            "qualitative_locality": spec.locality,
            "habitat": spec.habitat,
            "may_replace": "water" if spec.replace_water else "air",
            "iterations": spec.iterations,
            "scatter_denominator": spec.denominator,
            "expected_attempts_per_chunk_before_filters": round(spec.iterations / spec.denominator, 6),
            "feature_sha256": hashlib.sha256(feature_bytes).hexdigest(),
            "feature_rule_sha256": hashlib.sha256(rule_bytes).hexdigest(),
        })
    total = round(sum(row["expected_attempts_per_chunk_before_filters"] for row in rows), 6)
    manifest = {
        "schema": "aionbound.wave1.crystal-marsh-ecology-worldgen.v1",
        "status": "PASS_STATIC_SOURCE_REGISTRATION",
        "authority": "Creative Crystal Marsh low-basin, reed-sea, pool, channel, and crystal-clearing language",
        "density": {
            "aggregate_attempts_per_chunk_before_filters": total,
            "maximum": 1.0,
            "cap_change": "NONE",
        },
        "regional_filter": "overworld and non-ocean and swamp-or-river proxy",
        "water_ecology": {
            "shallow": ["bubble_pod", "crystal_lily", "flood_reed"],
            "submerged": ["crystal_vine", "glow_kelp"],
            "water_replace_requires_water_containment_component": True,
        },
        "registrations": rows,
        "proof_boundary": [
            "static source only",
            "swamp and river tags are regional proxies",
            "not live water adjacency or survivability proof",
            "not client BDS console distribution performance or release proof",
        ],
    }
    files[OUT / "CRYSTAL_ECOLOGY_WORLDGEN.json"] = encoded(manifest)
    return files, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, _ = outputs()
    mismatches = []
    for path, data in files.items():
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                mismatches.append(str(path.relative_to(REPO)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if mismatches:
        print(json.dumps({"status": "FAIL", "mismatches": mismatches}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "outputs": len(files), "mode": "check" if args.check else "write"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
