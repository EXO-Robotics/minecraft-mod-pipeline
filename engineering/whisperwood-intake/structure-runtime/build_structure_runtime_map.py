#!/usr/bin/env python3
"""Build the deterministic Packet 001 structure/prop engineering map.

This writes planning authority only. It deliberately does not create pack files,
invent structure layouts, or choose unresolved loot probabilities.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BEDROCK_ROOT = next(parent for parent in HERE.parents if parent.name == "bedrock-server")
CREATIVE = BEDROCK_ROOT / "program/crazycraft-pack-production-v1/studio-prep/creative"
PACKET = BEDROCK_ROOT / "program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-001-whisperwood"

CONTRACT_JSON = CREATIVE / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json"
CONTRACT_MD = CREATIVE / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md"
STRUCTURES_MD = CREATIVE / "05_structures/STRUCTURES_DESIGN.md"
WORLDGEN_MD = CREATIVE / "06_world_gen/WORLD_GENERATION.md"
LOOT_MD = CREATIVE / "02_loot/LOOT_WHISPERWOOD.md"
LEDGER = REPO / "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return path.relative_to(BEDROCK_ROOT).as_posix()


CLASS = {
    "lantern_post": "CUSTOM_GEOMETRY_BLOCK_PROP",
    "moss_cairn": "CUSTOM_GEOMETRY_BLOCK_PROP",
    "hunter_camp": "AUTHORED_MCSTRUCTURE_ASSEMBLY",
    "broken_wagon": "AUTHORED_MCSTRUCTURE_ASSEMBLY",
    "root_bridge": "AUTHORED_MCSTRUCTURE_ASSEMBLY",
    "owl_shrine": "LANDMARK_ENCOUNTER",
    "forest_waystone": "LANDMARK_ENCOUNTER",
    "hollow_cave_entrance": "LANDMARK_ENCOUNTER",
    "ancient_totem": "LANDMARK_ENCOUNTER",
    "fallen_giant_tree": "LANDMARK_ENCOUNTER",
}

PURPOSE = {
    "lantern_post": "path light network and harvest node",
    "moss_cairn": "quiet memorial, curiosity, and Codex discovery",
    "hunter_camp": "safe-ish early teaching POI with journal and camp loot",
    "broken_wagon": "road breadcrumb carrying the Whisperwood to Ashen pointer",
    "root_bridge": "ravine traversal landmark with an under-bridge cache",
    "owl_shrine": "rare soft-power rite landmark on high ground",
    "forest_waystone": "rare return-network activation landmark",
    "hollow_cave_entrance": "face-bound danger-pocket entrance with elite support",
    "ancient_totem": "deep-forest mystery and pilgrim foreshadow landmark",
    "fallen_giant_tree": "very-rare wonder landmark with a hollow story cache",
}

PLACEMENT = {
    "lantern_post": "trail segments",
    "moss_cairn": "quiet hollows",
    "hunter_camp": "local forest region clusters",
    "broken_wagon": "roads",
    "root_bridge": "ravines only",
    "owl_shrine": "high-ground clearings",
    "forest_waystone": "one major node per forest expanse",
    "hollow_cave_entrance": "cliff and root faces",
    "ancient_totem": "deep forest core",
    "fallen_giant_tree": "very-rare wonder event",
}

UNRESOLVED_IDENTITY_TICKET = {
    "lantern_post": "W1-CREATIVE-001",
    "moss_cairn": "W1-CREATIVE-001",
    "hunter_camp": "W1-CREATIVE-001",
    "broken_wagon": "W1-CREATIVE-001",
    "owl_shrine": "W1-CREATIVE-001",
    "forest_waystone": "W1-CREATIVE-001",
    "ancient_totem": "W1-CREATIVE-001",
    "fallen_giant_tree": "W1-CREATIVE-001",
}

G7_PATTERNS = {
    "lantern_post": ["behavior_pack/features/waystone_ruin.feature.json", "behavior_pack/feature_rules/waystone_ruin.feature_rule.json"],
    "moss_cairn": ["behavior_pack/features/waystone_ruin.feature.json", "behavior_pack/feature_rules/waystone_ruin.feature_rule.json"],
    "hunter_camp": ["behavior_pack/structures/aionbound/hunters_blind.mcstructure", "behavior_pack/structures/aionbound/collapsed_survey_camp.mcstructure"],
    "broken_wagon": ["behavior_pack/structures/aionbound/broken_relay.mcstructure", "behavior_pack/structures/aionbound/collapsed_survey_camp.mcstructure"],
    "root_bridge": ["behavior_pack/structures/aionbound/lantern_causeway.mcstructure"],
    "owl_shrine": ["behavior_pack/structures/aionbound/mote_shrine.mcstructure", "behavior_pack/scripts/structures.js"],
    "forest_waystone": ["behavior_pack/features/waystone_ruin.feature.json", "behavior_pack/scripts/structures.js", "behavior_pack/scripts/state.js"],
    "hollow_cave_entrance": ["behavior_pack/structures/aionbound/glassroot_grotto.mcstructure", "behavior_pack/scripts/structures.js"],
    "ancient_totem": ["behavior_pack/structures/aionbound/pilgrim_cairn.mcstructure", "behavior_pack/scripts/structures.js"],
    "fallen_giant_tree": ["behavior_pack/structures/aionbound/overgrown_waystation.mcstructure", "behavior_pack/scripts/structures.js"],
}

ASSEMBLY_IDS = {asset_id for asset_id, kind in CLASS.items() if kind != "CUSTOM_GEOMETRY_BLOCK_PROP"}


def targets(asset_id: str, kind: str) -> dict:
    rp = {
        "geometry": f"resource_pack/models/aionbound/whisperwood/{asset_id}.geo.json",
        "texture": f"resource_pack/textures/aionbound/whisperwood/structures/{asset_id}.png",
        "client_block_registry": "resource_pack/blocks.json",
        "terrain_atlas": "resource_pack/textures/terrain_texture.json",
    }
    bp = {
        "anchor_block": f"behavior_pack/blocks/{asset_id}.block.json",
        "feature": f"behavior_pack/features/{asset_id}.feature.json" if kind == "CUSTOM_GEOMETRY_BLOCK_PROP" else f"behavior_pack/features/{asset_id}.structure_feature.json",
        "feature_rule": f"behavior_pack/feature_rules/{asset_id}.feature_rule.json" if kind == "CUSTOM_GEOMETRY_BLOCK_PROP" else f"behavior_pack/feature_rules/{asset_id}.structure_feature_rule.json",
    }
    if kind != "CUSTOM_GEOMETRY_BLOCK_PROP":
        bp["structure_bytes"] = f"behavior_pack/structures/aionbound/{asset_id}.mcstructure"
    if asset_id in {"lantern_post", "moss_cairn"}:
        bp["loot"] = f"behavior_pack/loot_tables/blocks/{asset_id}.json"
    elif asset_id == "forest_waystone":
        bp["activation_reward"] = "behavior_pack/scripts/structures.js"
    else:
        bp["loot"] = f"behavior_pack/loot_tables/chests/whisperwood/{asset_id}.json"
    runtime = ["behavior_pack/scripts/catalog.js"]
    if asset_id != "lantern_post":
        runtime.append("behavior_pack/scripts/structures.js")
    if asset_id == "forest_waystone":
        runtime += ["behavior_pack/scripts/state.js", "behavior_pack/scripts/codex.js"]
    return {
        "behavior_pack": bp,
        "resource_pack": rp,
        "runtime": sorted(set(runtime)),
        "codex": ["behavior_pack/scripts/codex.js", f"landmark:{asset_id}"],
    }


def disposition(asset_id: str, kind: str, brief: dict) -> dict:
    blockers = ["NATIVE_ASSET_DISPOSITION"]
    if kind != "CUSTOM_GEOMETRY_BLOCK_PROP":
        blockers.append("AUTHORED_STRUCTURE_BYTES_ABSENT")
    if brief.get("animations"):
        blockers.append("DECLARED_PROP_ANIMATION_NOT_YET_SHIPPING")
    blockers.append("W1-CREATIVE-004_FINAL_LOOT_VALUES")
    if asset_id in UNRESOLVED_IDENTITY_TICKET:
        blockers.append("W1-CREATIVE-001_UNRESOLVED_LOOT_OR_COMPONENT_IDENTITY")
    if asset_id in {"forest_waystone", "hollow_cave_entrance", "ancient_totem", "fallen_giant_tree"}:
        blockers.append("RUNTIME_INTERACTION_OR_ENCOUNTER_SEMANTICS_NOT_YET_IMPLEMENTED")
    return {
        "status": "WITHHELD_FROM_PACK_UNTIL_DEPENDENCIES_CLOSE",
        "blockers": blockers,
        "creative_support_required_now": False,
        "note": "Identity and qualitative role are approved; Engineering must author the implementation without treating the prop model as an encounter assembly.",
    }


def build() -> dict:
    contract = json.loads(CONTRACT_JSON.read_text())
    ledger = json.loads(LEDGER.read_text())
    rows = contract["packets"]["001_whisperwood"]["structures"]
    loot_ticket = next(ticket for ticket in ledger["support_tickets"] if ticket["id"] == "W1-CREATIVE-004")
    assets = []
    for row in rows:
        asset_id = row["id"]
        brief_path = PACKET / "props" / f"{asset_id}.brief.json"
        model_path = PACKET / "assets/export/models" / f"{asset_id}.geo.json"
        texture_path = PACKET / "assets/editable" / f"{asset_id}.png"
        editable_path = PACKET / "assets/editable" / f"{asset_id}.bbmodel"
        brief = json.loads(brief_path.read_text())
        model = json.loads(model_path.read_text())["minecraft:geometry"][0]
        kind = CLASS[asset_id]
        assets.append({
            "id": asset_id,
            "implementation_class": kind,
            "purpose": PURPOSE[asset_id],
            "placement_contract": PLACEMENT[asset_id],
            "creative_contract": row,
            "packet_visual_input": {
                "brief": rel(brief_path),
                "editable_model": rel(editable_path),
                "static_geometry": rel(model_path),
                "texture": rel(texture_path),
                "model_identifier": brief["model_identifier"],
                "profile": brief["profile"],
                "declared_scale": brief["minecraft_scale"],
                "declared_animations": brief["animations"],
                "locators": brief["locators"],
                "visible_bounds": {
                    key: model["description"].get(key)
                    for key in ("visible_bounds_width", "visible_bounds_height", "visible_bounds_offset")
                },
                "claims_boundary": brief["claims_boundary"],
            },
            "targets": targets(asset_id, kind),
            "dependencies": {
                "qualitative_loot_authority": rel(LOOT_MD),
                "final_loot_values": loot_ticket["id"],
                "unresolved_identity_ticket": UNRESOLVED_IDENTITY_TICKET.get(asset_id),
                "g7_reusable_patterns": G7_PATTERNS[asset_id],
            },
            "missing_authored_structure_bytes": (
                f"behavior_pack/structures/aionbound/{asset_id}.mcstructure"
                if asset_id in ASSEMBLY_IDS else None
            ),
            "disposition": disposition(asset_id, kind, brief),
        })

    return {
        "document_id": "AIONBOUND_WAVE1_WHISPERWOOD_STRUCTURE_RUNTIME_MAP_V1",
        "document_type": "IMPLEMENTATION_MAP_NOT_PACK_CONTENT",
        "base_commit": "c4d77b6",
        "namespace": "aionbound",
        "scope": "Packet 001 ten structure and prop IDs",
        "proof_boundary": [
            "No pack files, structure bytes, layouts, loot probabilities, boss values, Blockbench evidence, BDS evidence, or candidate claims are produced by this map.",
            "Packet geometry is an approved visual input, not proof of an authored Minecraft encounter assembly.",
            "G7 structure code and templates are reusable engineering patterns, not approved Whisperwood layouts or reward identities.",
        ],
        "authority": [
            {"path": rel(path), "sha256": sha256(path)}
            for path in (CONTRACT_JSON, CONTRACT_MD, STRUCTURES_MD, WORLDGEN_MD, LOOT_MD, LEDGER)
        ],
        "summary": {
            "asset_count": len(assets),
            "class_counts": {kind: sum(asset["implementation_class"] == kind for asset in assets) for kind in sorted(set(CLASS.values()))},
            "missing_authored_structure_byte_count": len(ASSEMBLY_IDS),
            "direct_prop_count": len(assets) - len(ASSEMBLY_IDS),
            "open_final_loot_ticket": loot_ticket["id"],
        },
        "reusable_g7_framework": {
            "keep": [
                "minecraft:structure_template_feature registration shape",
                "feature-rule identifier and filename closure convention",
                "bounded signature-based discovery and per-player claim guard",
                "persistent landmark stamps and capped per-player site history",
                "deterministic little-endian NBT writer as an authoring mechanism",
            ],
            "refine": [
                "Use Whisperwood-specific placement predicates; generic overworld non-ocean filters do not satisfy trail, ravine, face, high-ground, deep-core, or expanse semantics.",
                "Use approved structure-specific rewards; G7 pool rewards cannot be relabeled as Whisperwood loot.",
                "Author each assembly from approved Whisperwood blocks and props; G7 generic platform layouts are pattern evidence only.",
            ],
        },
        "assets": assets,
    }


def render_md(document: dict) -> str:
    lines = [
        "# Whisperwood Structure Runtime Implementation Map",
        "",
        f"Base: `{document['base_commit']}` · Scope: {document['scope']} · Status: planning authority only.",
        "",
        "## Boundary",
        "",
    ]
    lines += [f"- {item}" for item in document["proof_boundary"]]
    lines += [
        "",
        "## Disposition summary",
        "",
        f"- 2 direct custom-geometry prop placements: `lantern_post`, `moss_cairn`.",
        f"- 3 authored assembly POIs: `hunter_camp`, `broken_wagon`, `root_bridge`.",
        f"- 5 landmark encounters: `owl_shrine`, `forest_waystone`, `hollow_cave_entrance`, `ancient_totem`, `fallen_giant_tree`.",
        f"- 8 actual `.mcstructure` files are missing. The two direct props intentionally do not require an encounter assembly.",
        f"- All ten remain withheld from pack promotion until their listed dependencies close; final loot values remain blocked by `{document['summary']['open_final_loot_ticket']}`.",
        "",
        "## Per-ID map",
        "",
        "| ID | Class | Generation / encounter target | Loot or activation target | Missing authored bytes | Current blockers |",
        "|---|---|---|---|---|---|",
    ]
    for asset in document["assets"]:
        bp = asset["targets"]["behavior_pack"]
        reward = bp.get("loot", bp.get("activation_reward"))
        missing = asset["missing_authored_structure_bytes"] or "N/A — direct prop"
        lines.append(
            f"| `{asset['id']}` | {asset['implementation_class']} | `{bp['feature']}` + `{bp['feature_rule']}` | `{reward}` | `{missing}` | "
            + ", ".join(f"`{item}`" for item in asset["disposition"]["blockers"])
            + " |"
        )
    lines += [
        "",
        "## Reusable G7 engineering evidence",
        "",
    ]
    lines += [f"- KEEP: {item}" for item in document["reusable_g7_framework"]["keep"]]
    lines += [f"- REFINE: {item}" for item in document["reusable_g7_framework"]["refine"]]
    lines += [
        "",
        "## Implementation sequence",
        "",
        "1. Promote each packet prop only after its native/static geometry disposition, texture path, animation declarations, and locator bindings close.",
        "2. Implement `lantern_post` and `moss_cairn` as individually placeable custom-geometry blocks with direct feature rules; do not invent surrounding layouts.",
        "3. Author the eight listed `.mcstructure` assemblies using approved Packet 001 blocks and promoted prop anchors. The packet prop model cannot substitute for those bytes.",
        "4. Bind structure-specific biome/terrain predicates for trail, road, ravine, high ground, expanse, face, deep core, and wonder placement. Do not copy G7's generic overworld filter.",
        "5. Wire qualitative loot identities and Codex stamps now, but leave numeric rolls/quantities and unresolved non-warehouse item IDs fail-closed until their ledger tickets close.",
        "6. Run targeted JSON, identifier, structure-reference, loot-reference, and persistence tests before the bounded Whisperwood package smoke.",
        "",
        "## Authority hashes",
        "",
    ]
    lines += [f"- `{entry['sha256']}`  `{entry['path']}`" for entry in document["authority"]]
    return "\n".join(lines) + "\n"


def main() -> None:
    document = build()
    (HERE / "WHISPERWOOD_STRUCTURE_RUNTIME_MAP.json").write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    (HERE / "WHISPERWOOD_STRUCTURE_RUNTIME_MAP.md").write_text(render_md(document))


if __name__ == "__main__":
    main()
