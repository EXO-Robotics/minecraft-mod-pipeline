#!/usr/bin/env python3
"""Author bounded Ashen plant ecology without copying Whisperwood tuning."""

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
ASH_GROUND = ["aionbound:ash_soil", "aionbound:cinder_gravel"]
HOT_STONE = ["aionbound:smolder_stone", "aionbound:basalt_brick", "aionbound:basalt_pillar"]


@dataclass(frozen=True)
class Spec:
    asset: str
    locality: str
    faces: str
    supports: list[str]
    placement_pass: str
    iterations: int
    denominator: int
    y: object


SPECS = [
    Spec("cinder_grass", "ash fields", "bottom", ASH_GROUND, "surface_pass", 4, 8, SURFACE),
    Spec("ash_fern", "ash-dune shelter", "bottom", ASH_GROUND, "surface_pass", 2, 16, SURFACE),
    Spec("smoke_reed", "vent margins", "bottom", ASH_GROUND + HOT_STONE, "surface_pass", 2, 32, SURFACE),
    Spec("char_shrub", "dry plateau scrub", "bottom", ASH_GROUND, "surface_pass", 2, 24, SURFACE),
    Spec("soot_mushroom", "shaded ash and kiln stone", "bottom", ASH_GROUND + HOT_STONE, "surface_pass", 2, 48, SURFACE),
    Spec("magma_moss", "hot basalt plates", "bottom", HOT_STONE, "surface_pass", 3, 24, SURFACE),
    Spec("glow_root", "cave ceiling and wall faces", "all", HOT_STONE + ["minecraft:stone", "minecraft:deepslate"], "underground_pass", 2, 64, {"distribution": "uniform", "extent": [8, 56]}),
    Spec("basalt_flower", "rare stone seam", "bottom", HOT_STONE + ["aionbound:cinder_gravel"], "surface_pass", 1, 128, SURFACE),
    Spec("ember_vine", "heated cliffs and char trunks", "all", HOT_STONE + ["aionbound:ash_log", "aionbound:heat_bark"], "surface_pass", 2, 48, SURFACE),
    Spec("fire_bloom", "rare ember-moss patches", "bottom", ASH_GROUND + ["aionbound:ember_moss"], "surface_pass", 1, 64, SURFACE),
]


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def feature(spec: Spec) -> dict:
    attach = {"min_sides_must_attach": 1, "auto_rotate": spec.faces == "all", spec.faces: spec.supports}
    return {
        "format_version": "1.21.40",
        "minecraft:single_block_feature": {
            "description": {"identifier": f"aionbound:ah_ecology_{spec.asset}"},
            "places_block": f"aionbound:{spec.asset}",
            "enforce_placement_rules": True,
            "enforce_survivability_rules": True,
            "may_replace": ["minecraft:air"],
            "may_attach_to": attach,
        },
    }


def rule(spec: Spec) -> dict:
    return {
        "format_version": "1.21.40",
        "minecraft:feature_rules": {
            "description": {
                "identifier": f"aionbound:ah_ecology_{spec.asset}.feature_rule",
                "places_feature": f"aionbound:ah_ecology_{spec.asset}",
            },
            "conditions": {
                "placement_pass": spec.placement_pass,
                "minecraft:biome_filter": {"all_of": [
                    {"test": "has_biome_tag", "operator": "==", "value": "overworld"},
                    {"test": "has_biome_tag", "operator": "!=", "value": "ocean"},
                    {"any_of": [
                        {"test": "has_biome_tag", "operator": "==", "value": "mountain"},
                        {"test": "has_biome_tag", "operator": "==", "value": "mesa"},
                    ]},
                ]},
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
        feature_path = BP / "features" / f"ah_ecology_{spec.asset}.feature.json"
        rule_path = BP / "feature_rules" / f"ah_ecology_{spec.asset}.feature_rule.json"
        feature_bytes, rule_bytes = encoded(feature(spec)), encoded(rule(spec))
        files[feature_path], files[rule_path] = feature_bytes, rule_bytes
        rows.append({
            "asset": spec.asset,
            "qualitative_locality": spec.locality,
            "placement_pass": spec.placement_pass,
            "iterations": spec.iterations,
            "scatter_denominator": spec.denominator,
            "expected_attempts_per_chunk_before_filters": round(spec.iterations / spec.denominator, 6),
            "feature_sha256": hashlib.sha256(feature_bytes).hexdigest(),
            "feature_rule_sha256": hashlib.sha256(rule_bytes).hexdigest(),
        })
    total = round(sum(row["expected_attempts_per_chunk_before_filters"] for row in rows), 6)
    manifest = {
        "schema": "aionbound.wave1.ashen-ecology-worldgen.v1",
        "status": "PASS_STATIC_SOURCE_REGISTRATION",
        "authority": "Creative Ashen plateau/caldera language plus ratified G8 plant identities",
        "density": {"aggregate_attempts_per_chunk_before_filters": total, "maximum": 1.1, "cap_change": "NONE"},
        "regional_filter": "overworld and non-ocean and mountain-or-mesa proxy",
        "registrations": rows,
        "proof_boundary": ["static source only", "terrain tags are regional proxies", "not adjacency, client, BDS, console, or distribution proof"],
    }
    files[OUT / "ASHEN_ECOLOGY_WORLDGEN.json"] = encoded(manifest)
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
