#!/usr/bin/env python3
"""Author bounded, deterministic Whisperwood vegetation/resource proxies."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BP = REPO / "behavior_pack"
OUT = Path(__file__).resolve().parent
GROUND = ["minecraft:grass_block", "minecraft:dirt", "minecraft:coarse_dirt", "minecraft:podzol", "minecraft:moss_block"]
WET_GROUND = ["minecraft:mud", "minecraft:clay", "minecraft:dirt", "minecraft:grass_block"]
WOOD = ["minecraft:oak_log", "minecraft:dark_oak_log", "minecraft:mangrove_log", "aionbound:whisperwood_log", "aionbound:whisperwood_wood", "aionbound:moss_bark"]

@dataclass(frozen=True)
class Spec:
    identifier: str
    role: str
    locality: str
    feature: dict
    placement_pass: str
    iterations: int
    denominator: int
    y: object

def single(identifier: str, block, *, bottom=None, all_faces=None, enforce=True) -> dict:
    body = {
        "description": {"identifier": f"aionbound:{identifier}"},
        "places_block": block,
        "enforce_placement_rules": enforce,
        "enforce_survivability_rules": enforce,
        "may_replace": ["minecraft:air"],
    }
    if bottom:
        body["may_attach_to"] = {"min_sides_must_attach": 1, "auto_rotate": False, "bottom": bottom}
    elif all_faces:
        body["may_attach_to"] = {"min_sides_must_attach": 1, "auto_rotate": True, "all": all_faces}
    return {"format_version": "1.21.40", "minecraft:single_block_feature": body}

SURFACE = "q.heightmap(v.worldx, v.worldz)"
SPECS = [
    Spec("ww_ecology_whisper_fern", "representative understory plant", "forest floor", single("ww_ecology_whisper_fern", "aionbound:whisper_fern", bottom=GROUND), "surface_pass", 4, 8, SURFACE),
    Spec("ww_ecology_lantern_bloom", "representative luminous plant", "forest clearings", single("ww_ecology_lantern_bloom", "aionbound:lantern_bloom", bottom=GROUND[:-1]), "surface_pass", 2, 16, SURFACE),
    Spec("ww_ecology_mooncap", "representative shaded fungus", "soft hollows", single("ww_ecology_mooncap", "aionbound:mooncap_mushroom", bottom=GROUND + ["minecraft:mycelium"]), "surface_pass", 2, 24, SURFACE),
    Spec("ww_ecology_root_flower", "representative root-associated flower", "root plate edges", single("ww_ecology_root_flower", "aionbound:root_flower", bottom=GROUND[:-1]), "surface_pass", 1, 32, SURFACE),
    Spec("ww_ecology_glow_moss_floor", "moss/resin-adjacent floor node proxy", "mossy forest floor", single("ww_ecology_glow_moss_floor", "aionbound:glow_moss", bottom=GROUND + ["minecraft:stone"]), "surface_pass", 3, 12, SURFACE),
    Spec("ww_ecology_hollow_lily_margin", "lily/moon-sap pool-margin plant proxy", "wet forest margin; water adjacency unproven", single("ww_ecology_hollow_lily_margin", "aionbound:hollow_lily", bottom=WET_GROUND), "surface_pass", 2, 48, SURFACE),
    Spec("ww_ecology_briar_vine", "tree-side vine proxy", "forest wood faces", single("ww_ecology_briar_vine", "aionbound:briar_vine", all_faces=WOOD), "surface_pass", 3, 32, SURFACE),
    Spec("ww_ecology_root_bark_cluster", "root/bark/log surface cluster proxy", "forest floor near implied giant roots", single("ww_ecology_root_bark_cluster", [
        {"block": "aionbound:whisperwood_roots", "weight": 5},
        {"block": "aionbound:moss_bark", "weight": 3},
        {"block": "aionbound:whisperwood_log", "weight": 2},
    ], bottom=GROUND, enforce=False), "surface_pass", 2, 128, SURFACE),
    Spec("ww_ecology_hollow_wood_cave", "hollow wood/amber-adjacent cave proxy", "sampled underground forest cave air; cave topology unproven", single("ww_ecology_hollow_wood_cave", "aionbound:hollow_wood", all_faces=["minecraft:stone", "minecraft:deepslate", "minecraft:dirt", "aionbound:whisperwood_roots"], enforce=False), "underground_pass", 1, 96, {"distribution": "uniform", "extent": [8, 48]}),
]

def rule(spec: Spec) -> dict:
    return {
        "format_version": "1.21.40",
        "minecraft:feature_rules": {
            "description": {"identifier": f"aionbound:{spec.identifier}.feature_rule", "places_feature": f"aionbound:{spec.identifier}"},
            "conditions": {
                "placement_pass": spec.placement_pass,
                "minecraft:biome_filter": {"all_of": [
                    {"test": "has_biome_tag", "operator": "==", "value": "overworld"},
                    {"test": "has_biome_tag", "operator": "==", "value": "forest"},
                    {"test": "has_biome_tag", "operator": "!=", "value": "ocean"},
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

def encoded(value: dict) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()

def block_refs(value):
    if isinstance(value, str) and value.startswith("aionbound:"):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            if key in {"places_block", "block", "bottom", "all"}:
                yield from block_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from block_refs(child)

def expected_outputs() -> tuple[dict[Path, bytes], dict]:
    outputs = {}
    records = []
    for spec in SPECS:
        feature_path = BP / "features" / f"{spec.identifier}.feature.json"
        rule_path = BP / "feature_rules" / f"{spec.identifier}.feature_rule.json"
        feature_bytes, rule_bytes = encoded(spec.feature), encoded(rule(spec))
        outputs[feature_path] = feature_bytes
        outputs[rule_path] = rule_bytes
        refs = sorted(set(block_refs(spec.feature)))
        records.append({
            "id": spec.identifier,
            "role": spec.role,
            "qualitative_locality": spec.locality,
            "placement_proxy": "Stable feature-rule filter only; exact adjacency and terrain topology require later world observation",
            "placement_pass": spec.placement_pass,
            "iterations": spec.iterations,
            "scatter": {"numerator": 1, "denominator": spec.denominator},
            "expected_attempts_per_chunk_before_placement_filters": round(spec.iterations / spec.denominator, 6),
            "custom_block_references": refs,
            "feature_path": str(feature_path.relative_to(REPO)),
            "feature_rule_path": str(rule_path.relative_to(REPO)),
            "feature_sha256": hashlib.sha256(feature_bytes).hexdigest(),
            "feature_rule_sha256": hashlib.sha256(rule_bytes).hexdigest(),
        })
    total = round(sum(record["expected_attempts_per_chunk_before_placement_filters"] for record in records), 6)
    manifest = {
        "schema": "aionbound.wave1.whisperwood.ecology_worldgen.v1",
        "integration_base": "429ab6c4a9f308f93296dd106128303b44181061",
        "authority": [{"path": "studio-prep/creative/06_world_gen/WORLD_GENERATION.md", "sha256": "bc18a1e1f73d6045ab7e583afe910ca13d4776d439c8f3dfb45dae5784372f4b"}],
        "stable_schema_basis": ["minecraft:single_block_feature 1.21.40", "minecraft:feature_rules 1.21.40"],
        "density_policy": {"max_iterations_per_rule": 4, "minimum_scatter_denominator": 8, "aggregate_expected_attempts_per_chunk_before_filters": total, "cap_change": "NONE"},
        "content_boundary": "NO ITEMS, DROPS, LOOT, ENTITIES, STRUCTURES, SCRIPT API, CUSTOM BIOMES, OR CAP CHANGES",
        "proxy_boundary": "resin, amber, and moon sap remain item/loot concerns and are not placed; moss, hollow wood, and lily blocks only signal adjacent ecology",
        "proof_boundary": "STATIC_SOURCE_REGISTRATION_PASS_ONLY; NOT BDS, CLIENT, NATURAL-DISTRIBUTION, EXACT-TERRAIN-LOCALITY, OR CANDIDATE PROOF",
        "registrations": records,
    }
    outputs[OUT / "WHISPERWOOD_ECOLOGY_WORLDGEN.json"] = encoded(manifest)
    lines = ["# Whisperwood Ecology Worldgen", "", "Status: STATIC_SOURCE_REGISTRATION_PASS_ONLY", "", "Nine conservative Stable feature registrations place existing Packet 001 vegetation and resource-adjacent block proxies in overworld forest contexts.", "", "| Feature | Role | Pass | Iterations / chance | Expected attempts/chunk |", "|---|---|---|---:|---:|"]
    for record in records:
        lines.append(f"| {record['id']} | {record['role']} | {record['placement_pass']} | {record['iterations']} / 1:{record['scatter']['denominator']} | {record['expected_attempts_per_chunk_before_placement_filters']} |")
    lines += ["", "## Boundaries", "", f"- Aggregate expected attempts before placement filters: {total} per chunk; this does not raise entity or runtime caps.", "- Forest, surface, and underground filters are stable registration proxies. They do not prove pool adjacency, tree adjacency, caves, root plates, or biome-wide distribution.", "- Resin, amber, and moon sap items are not placed or referenced. Existing moss, hollow wood, and lily blocks provide only the approved resource-adjacent environmental signal.", "- No items, drops, loot, entities, structures, scripts, custom biomes, or runtime schedulers are authored.", ""]
    outputs[OUT / "WHISPERWOOD_ECOLOGY_WORLDGEN.md"] = ("\n".join(lines)).encode()
    return outputs, manifest

def main() -> int:
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
