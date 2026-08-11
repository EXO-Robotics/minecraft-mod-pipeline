#!/usr/bin/env python3
"""Author bounded natural registrations for the two Whisperwood direct props."""

import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BP = REPO / "behavior_pack"
OUT = Path(__file__).resolve().parent
ECOLOGY = REPO / "engineering/whisperwood-intake/ecology-worldgen/WHISPERWOOD_ECOLOGY_WORLDGEN.json"
GROUND = ["minecraft:grass_block", "minecraft:dirt", "minecraft:coarse_dirt", "minecraft:podzol", "minecraft:moss_block", "minecraft:stone"]
SPECS = [
    {"id": "ww_prop_lantern_post", "block": "aionbound:lantern_post", "role": "common path-language prop", "locality": "forest surface proxy; trail detection unproven", "iterations": 1, "denominator": 16},
    {"id": "ww_prop_moss_cairn", "block": "aionbound:moss_cairn", "role": "uncommon quiet-hollow prop", "locality": "forest surface proxy; hollow detection unproven", "iterations": 1, "denominator": 64},
]

def feature(spec):
    return {
        "format_version": "1.21.40",
        "minecraft:single_block_feature": {
            "description": {"identifier": f"aionbound:{spec['id']}"},
            "places_block": spec["block"],
            "enforce_placement_rules": True,
            "enforce_survivability_rules": True,
            "may_replace": ["minecraft:air"],
            "may_attach_to": {"min_sides_must_attach": 1, "auto_rotate": False, "bottom": GROUND},
        },
    }

def rule(spec):
    return {
        "format_version": "1.21.40",
        "minecraft:feature_rules": {
            "description": {"identifier": f"aionbound:{spec['id']}.feature_rule", "places_feature": f"aionbound:{spec['id']}"},
            "conditions": {
                "placement_pass": "surface_pass",
                "minecraft:biome_filter": {"all_of": [
                    {"test": "has_biome_tag", "operator": "==", "value": "overworld"},
                    {"test": "has_biome_tag", "operator": "==", "value": "forest"},
                    {"test": "has_biome_tag", "operator": "!=", "value": "ocean"},
                ]},
            },
            "distribution": {
                "coordinate_eval_order": "xzy",
                "iterations": spec["iterations"],
                "scatter_chance": {"numerator": 1, "denominator": spec["denominator"]},
                "x": {"distribution": "uniform", "extent": [0, 15]},
                "y": "q.heightmap(v.worldx, v.worldz)",
                "z": {"distribution": "uniform", "extent": [0, 15]},
            },
        },
    }

def encode(value):
    return (json.dumps(value, indent=2) + "\n").encode()

def expected_outputs():
    prior = json.loads(ECOLOGY.read_text())["density_policy"]["aggregate_expected_attempts_per_chunk_before_filters"]
    outputs, records = {}, []
    for spec in SPECS:
        feature_path = BP / "features" / f"{spec['id']}.feature.json"
        rule_path = BP / "feature_rules" / f"{spec['id']}.feature_rule.json"
        feature_bytes, rule_bytes = encode(feature(spec)), encode(rule(spec))
        outputs[feature_path], outputs[rule_path] = feature_bytes, rule_bytes
        attempts = spec["iterations"] / spec["denominator"]
        records.append({
            "id": spec["id"], "block": spec["block"], "role": spec["role"],
            "qualitative_locality": spec["locality"], "iterations": spec["iterations"],
            "scatter": {"numerator": 1, "denominator": spec["denominator"]},
            "expected_attempts_per_chunk_before_filters": round(attempts, 6),
            "feature_path": str(feature_path.relative_to(REPO)), "feature_rule_path": str(rule_path.relative_to(REPO)),
            "feature_sha256": hashlib.sha256(feature_bytes).hexdigest(), "feature_rule_sha256": hashlib.sha256(rule_bytes).hexdigest(),
        })
    added = round(sum(row["expected_attempts_per_chunk_before_filters"] for row in records), 6)
    combined = round(prior + added, 6)
    manifest = {
        "schema": "aionbound.wave1.whisperwood.direct_prop_worldgen.v1",
        "integration_base": "7d7e2e6",
        "authority": [{"path": "studio-prep/creative/06_world_gen/WORLD_GENERATION.md", "sha256": "bc18a1e1f73d6045ab7e583afe910ca13d4776d439c8f3dfb45dae5784372f4b"}],
        "density_accounting": {"existing_ecology_attempts_per_chunk": prior, "added_direct_prop_attempts_per_chunk": added, "combined_attempts_per_chunk": combined, "ceiling": 1.25, "cap_change": "NONE"},
        "placement_boundary": "overworld forest surface proxies only; no real trail or quiet-hollow detection claim",
        "content_boundary": "NO LOOT, SCRIPTS, STRUCTURES, ENTITIES, ITEMS, DROPS, OR CAP CHANGES",
        "proof_boundary": "STATIC_SOURCE_REGISTRATION_ONLY; NOT BDS, CLIENT, NATURAL DISTRIBUTION, TERRAIN LOCALITY, OR CANDIDATE PROOF",
        "registrations": records,
    }
    outputs[OUT / "WHISPERWOOD_DIRECT_PROP_WORLDGEN.json"] = encode(manifest)
    lines = ["# Whisperwood Direct Prop Worldgen", "", "Status: STATIC_SOURCE_REGISTRATION_ONLY", "", "Two Stable single-block features naturally register the integrated direct props with conservative forest-surface rules.", "", "| ID | Prop | Role | Chance |", "|---|---|---|---:|"]
    for row in records:
        lines.append(f"| {row['id']} | {row['block']} | {row['role']} | 1:{row['scatter']['denominator']} |")
    lines += ["", "## Density and boundaries", "", f"- Existing ecology attempts/chunk: {prior}.", f"- Added direct-prop attempts/chunk: {added}.", f"- Combined attempts/chunk: {combined}, below the 1.25 lane ceiling.", "- These are terrain-safe forest surface proxies. Trail and quiet-hollow detection remain unproven.", "- No loot, scripts, structures, entities, items, drops, or cap changes are included.", ""]
    outputs[OUT / "WHISPERWOOD_DIRECT_PROP_WORLDGEN.md"] = ("\n".join(lines)).encode()
    return outputs, manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs, _ = expected_outputs()
    mismatches = []
    for path, data in outputs.items():
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                mismatches.append(str(path.relative_to(REPO)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if mismatches:
        print(json.dumps({"status": "FAIL", "mismatches": mismatches}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write", "outputs": len(outputs)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
