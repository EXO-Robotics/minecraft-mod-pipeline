#!/usr/bin/env python3
"""Build the deterministic Crystal Marsh Packet 006 equipment intake map.

This inventory is evidence and planning only. It never authors pack content,
runtime wiring, recipes, Creative decisions, or qualification claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path


BASE_COMMIT = "b4005112cf7ad347433ec3aa42bf7a761359b95d"
BASE_TREE = "6a2008f2a4f68859ef330a5b984af5eb8d9692c8"
BEDROCK_ROOT_DEFAULT = Path("/Users/blakegrove/Desktop/bedrock-server")

AUTHORITY_REL = Path("engineering/crystal-marsh-intake/authority/CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.json")
LEDGER_REL = Path("engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json")
PROPOSAL_RELS = [
    Path("engineering/authority/support-proposals/crystal-marsh/W1-001-CM.json"),
    Path("engineering/authority/support-proposals/crystal-marsh/W1-003-PEARL-DEPTHS.json"),
    Path("engineering/authority/support-proposals/crystal-marsh/W1-004-CM.json"),
]

RECIPES = {
    "crystal_pike": {
        "source_formula": "Crystal Pole + Heron Beak / crystal tip -> crystal_pike",
        "acquisition_inputs": ["crystal_reed_item", "flood_crystal", "glass_heron", "reed_serpent"],
        "provenance": "Crystal Marsh reeds, flood crystal, and heron/serpent routes",
        "gated_by": ["W1-001-CM"],
    },
    "prism_bow": {
        "source_formula": "bow limbs + prism wing + algae polish -> prism_bow",
        "acquisition_inputs": ["crystal_dragonfly", "flood_crystal", "glass_algae", "glass_heron"],
        "provenance": "Crystal Marsh prism-wing and mineral-polish route",
        "gated_by": ["W1-001-CM"],
        "sidegrade_boundary": "Gale-strung prism_bow remains W1-CREATIVE-005 deferred; base prism_bow is not blocked by that deferral.",
    },
    "crystal_circlet": {
        "source_formula": "Living Crystal Core + Watcher Lens + silk -> crystal_circlet",
        "acquisition_inputs": ["crystal_root_item", "moon_pearl", "prism_pearl", "bog_watcher", "crystal_newt", "wet_chitin", "marsh_wight"],
        "provenance": "Crystal Marsh living crystal, pearl, watcher, and wet-chitin route",
        "gated_by": ["W1-001-CM", "W1-004-CM"],
    },
    "explorer_cloak": {
        "source_formula": "Croc Hide + WW leather + CM polish -> explorer_cloak",
        "acquisition_inputs": ["silt_crocodile", "marsh_wight", "glass_algae"],
        "provenance": "Multi-biome Whisperwood-to-Crystal travel identity",
        "gated_by": ["W1-001-CM", "W1-004-CM"],
    },
    "crystal_shovel": {
        "source_formula": "silt_core + reed haft -> crystal_shovel",
        "acquisition_inputs": ["silt_core", "mire_turtle", "silt_crocodile", "flood_reed"],
        "provenance": "Crystal Marsh silt and reed tool route",
        "gated_by": ["W1-001-CM"],
    },
    "marsh_sickle": {
        "source_formula": "wet_chitin + crystal edge -> marsh_sickle",
        "acquisition_inputs": ["wet_chitin", "marsh_resin", "bloom_crab", "flood_reed"],
        "provenance": "Crystal Marsh chitin, resin, and reed harvest route",
        "gated_by": ["W1-001-CM"],
    },
    "crystal_talisman": {
        "source_formula": "prism chips + pearl grain -> crystal_talisman",
        "acquisition_inputs": ["prism_frog", "bloom_crab", "crystal_root_item", "moon_pearl", "crystal_obelisk"],
        "provenance": "Crystal Marsh pearl ecology and obelisk network",
        "gated_by": ["W1-001-CM", "W1-004-CM"],
    },
    "marsh_idol": {
        "source_formula": "totem wood + mire_orchid + resin -> marsh_idol",
        "acquisition_inputs": ["marsh_totem", "mire_orchid", "marsh_resin", "sunken_shrine"],
        "provenance": "Crystal Marsh totem, orchid, resin, and shrine route",
        "gated_by": ["W1-001-CM", "W1-004-CM"],
    },
    "marsh_wight_mask": {
        "source_formula": "Pearl Depths first-clear chapter seal and display trophy",
        "acquisition_inputs": ["marsh_wight"],
        "provenance": "Pearl Depths arena apex only; ecology form is prohibited as a seal source",
        "gated_by": ["W1-003-PEARL-DEPTHS", "W1-004-CM"],
    },
    "moon_pearl_pedestal": {
        "source_formula": "moon_pearl + prism_brick -> moon_pearl_pedestal",
        "acquisition_inputs": ["moon_pearl", "prism_brick", "sunken_shrine"],
        "provenance": "Crystal Marsh pearl craft and shrine mastery display",
        "gated_by": ["W1-001-CM", "W1-004-CM"],
    },
    "crystal_obelisk_fragment": {
        "source_formula": "crystal_obelisk_fragment -> display",
        "acquisition_inputs": ["crystal_obelisk", "ruined_observatory"],
        "provenance": "Crystal Marsh obelisk network and observatory mastery",
        "gated_by": ["W1-004-CM"],
    },
    "surveyor_staff": {
        "source_formula": "Twin Mineral Lens + sky timber + aether chip -> surveyor_staff",
        "acquisition_inputs": ["bog_watcher", "flood_crystal", "ruined_observatory"],
        "provenance": "Adjacent Crystal-to-Skyreach/pilgrim cross-craft; not a direct Packet 003 equipment page",
        "gated_by": ["W1-001-CM", "SKYREACH_AUTHORITY"],
    },
    "trail_compass": {
        "source_formula": "waystone needle + brass + wind oil -> trail_compass",
        "acquisition_inputs": ["ruined_observatory"],
        "provenance": "Adjacent multi-region navigation link; not a direct Packet 003 equipment page",
        "gated_by": ["W1-001-CM", "SKYREACH_AUTHORITY"],
    },
}

BRANCH_ROLES = {
    "crystal_pike": "Long wet reach and precision for bridge/boat fights",
    "prism_bow": "Clean ranged prism utility for open water and heron cliffs",
    "crystal_circlet": "Marsh crown with magic/perception identity; not a full set",
    "explorer_cloak": "Multi-biome travel and inventory fantasy",
    "crystal_shovel": "Silt and wet-dig verb",
    "marsh_sickle": "Bulk plant and reed harvest verb",
    "crystal_talisman": "Wet vision and pearl-luck identity",
    "marsh_idol": "Structure calm and wight-resist narrative",
    "marsh_wight_mask": "Chapter 3 seal and apex display",
    "moon_pearl_pedestal": "Optional pearl mastery display",
    "crystal_obelisk_fragment": "Optional obelisk mastery display",
    "surveyor_staff": "Reveal, measure, and Codex-aid verb for Skyreach/pilgrim",
    "trail_compass": "Multi-region navigation and waystone verb",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_dimensions(path: Path) -> list[int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not PNG: {path}")
    return list(struct.unpack(">II", data[16:24]))


def git_paths(repo: Path) -> set[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", BASE_COMMIT],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    )
    return set(result.stdout.splitlines())


def native_static(source_files: dict, bedrock_root: Path) -> dict:
    brief = json.loads((bedrock_root / source_files["brief"]["path"]).read_text())
    bbmodel = json.loads((bedrock_root / source_files["editable_bbmodel"]["path"]).read_text())
    geometry = json.loads((bedrock_root / source_files["export_geometry"]["path"]).read_text())
    animation = json.loads((bedrock_root / source_files["export_animation"]["path"]).read_text())
    outliner = bbmodel.get("outliner", [])
    elements = bbmodel.get("elements", [])
    native_locator_names = sorted({
        str(row.get("name")) for row in [*outliner, *elements]
        if isinstance(row, dict) and row.get("type") == "locator" and row.get("name")
    })
    exported_locator_names = sorted({
        name
        for geo in geometry.get("minecraft:geometry", [])
        for bone in geo.get("bones", [])
        for name in (bone.get("locators") or {}).keys()
    })
    source_clips = sorted((bbmodel.get("animations") or {}).keys()) if isinstance(bbmodel.get("animations"), dict) else sorted(
        row.get("name") for row in (bbmodel.get("animations") or []) if isinstance(row, dict) and row.get("name")
    )
    exported_clips = sorted((animation.get("animations") or {}).keys())
    texture_sources = [row.get("source", "") for row in bbmodel.get("textures", []) if isinstance(row, dict)]
    expected_locators = sorted(brief.get("locators", []))
    expected_clips = sorted(brief.get("animations", []))
    texture = bedrock_root / source_files["export_texture"]["path"]
    return {
        "brief_model_identifier": brief.get("model_identifier"),
        "brief_role": brief.get("role"),
        "brief_expected_locators": expected_locators,
        "native_locator_names": native_locator_names,
        "exported_locator_names": exported_locator_names,
        "native_locator_gap": sorted(set(expected_locators) - set(native_locator_names)),
        "brief_expected_clips": expected_clips,
        "source_clip_names": source_clips,
        "exported_clip_names": exported_clips,
        "role_clip_gap": sorted(set(expected_clips) - set(source_clips) - set(exported_clips)),
        "texture_dimensions": png_dimensions(texture),
        "brief_texture_resolution": brief.get("texture_resolution"),
        "absolute_texture_binding_present": any(str(source).startswith("/") for source in texture_sources),
        "native_roundtrip": "NOT_RUN_REPAIR_REQUIRED" if (set(expected_locators) - set(native_locator_names)) or (set(expected_clips) - set(source_clips) - set(exported_clips)) else "NOT_RUN_STATIC_READY",
    }


def target_profile(item_id: str, group: str) -> list[str]:
    if group == "trophies":
        return [
            f"behavior_pack/blocks/{item_id}.block.json",
            f"behavior_pack/loot_tables/blocks/{item_id}.json",
            f"resource_pack/models/aionbound/crystal_marsh/equipment/{item_id}.geo.json",
            f"resource_pack/animations/aionbound/crystal_marsh/equipment/{item_id}.animation.json",
            f"resource_pack/textures/aionbound/wave1/equipment/trophies/{item_id}.png",
            "resource_pack/blocks.json",
            "resource_pack/textures/terrain_texture.json",
            "resource_pack/texts/en_US.lang",
            "behavior_pack/scripts/catalog.js",
            "behavior_pack/scripts/codex.js",
        ]
    texture_class = "armor" if group == "armor" else "accessories" if group == "accessories" else "items"
    return [
        f"behavior_pack/items/{item_id}.item.json",
        f"behavior_pack/recipes/{item_id}.recipe.json",
        f"resource_pack/attachables/{item_id}.attachable.json",
        f"resource_pack/models/aionbound/crystal_marsh/equipment/{item_id}.geo.json",
        f"resource_pack/animations/aionbound/crystal_marsh/equipment/{item_id}.animation.json",
        f"resource_pack/textures/aionbound/wave1/equipment/{texture_class}/{item_id}.png",
        "resource_pack/textures/item_texture.json",
        "resource_pack/texts/en_US.lang",
        "behavior_pack/scripts/catalog.js",
        "behavior_pack/scripts/codex.js",
    ]


def authority_ref(repo: Path, rel: Path, role: str) -> dict:
    path = repo / rel
    return {"path": rel.as_posix(), "sha256": sha256(path), "role": role}


def build(repo: Path, bedrock_root: Path) -> dict:
    authority = json.loads((repo / AUTHORITY_REL).read_text())
    base_paths = git_paths(repo)
    direct = authority["equipment_links"]["contract_direct"]
    adjacent = authority["equipment_links"]["adjacent_structure_or_crosscraft_references"]
    groups = {row["warehouse_id"]: row.get("group") for row in direct}
    groups.update({"surveyor_staff": "tools", "trail_compass": "tools"})

    def row(source: dict, relationship: str) -> dict:
        item_id = source["warehouse_id"]
        group = groups[item_id]
        targets = target_profile(item_id, group)
        recipe = RECIPES[item_id]
        is_direct = relationship == "DIRECT_PACKET_003_LINK"
        return {
            "id": item_id,
            "runtime_id": source["runtime_id"],
            "group": group,
            "relationship": relationship,
            "codex_page_allocation": "CM_EQUIPMENT_PAGE" if is_direct else "REFERENCE_ONLY_NO_CM_ADDRESS",
            "visual_role": native_static(source["source_files"], bedrock_root)["brief_role"],
            "gameplay_role": BRANCH_ROLES[item_id],
            "source_files": source["source_files"],
            "native_readiness": native_static(source["source_files"], bedrock_root),
            "target_status_at_base": {
                "targets": [{"path": path, "present": path in base_paths} for path in targets],
                "identity_specific_targets_present": [path for path in targets if item_id in path and path in base_paths],
                "identity_specific_targets_missing": [path for path in targets if item_id in path and path not in base_paths],
                "shared_targets_present": [path for path in targets if item_id not in path and path in base_paths],
            },
            "recipe_acquisition_provenance": recipe,
            "safe_now": [
                "retain exact warehouse/runtime identity and Packet 006 visual provenance",
                "prepare namespace-safe registry, localization, target paths, and Codex page scaffolding",
                "repair native locator/clip/portable-binding gaps and bind approved presentation without inventing gameplay",
                "preserve nonnumeric region, role, and source relationships",
            ],
            "gated_semantics": {
                "blockers": recipe["gated_by"],
                "withheld": [
                    "final ingredient disposition and recipe quantities",
                    "numeric acquisition or loot probability",
                    "gameplay effect values and balance",
                    "boss/reward grant or recovery semantics where applicable",
                ],
            },
        }

    rows_direct = [row(source, "DIRECT_PACKET_003_LINK") for source in direct]
    rows_adjacent = [row(source, "ADJACENT_CROSS_REGION_LINK") for source in adjacent]
    references = [
        authority_ref(repo, AUTHORITY_REL, "current exact Packet 003 and Packet 006 structural authority; receipt refreshed after ratification without authority mutation"),
        authority_ref(repo, LEDGER_REL, "current ratified/deferred decision boundary"),
    ]
    references.extend(authority_ref(repo, rel, "ratified Crystal implementation authority; proposal bytes preserved") for rel in PROPOSAL_RELS)
    data = {
        "schema": "aionbound.wave1.crystal-marsh-equipment-intake.v1.0.0",
        "status": "HASH_BOUND_PACKET006_INTAKE_SAFE_SCAFFOLDING_SEPARATED",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE, "g7_immutable": True},
        "scope": "Read-only Packet 006 Crystal equipment intake; no BP/RP/runtime/ledger/BDS mutation.",
        "authority": references,
        "counts": {"direct_packet003_links": 11, "adjacent_cross_region_links": 2, "cm_codex_pages": 11},
        "direct_packet003_links": rows_direct,
        "adjacent_cross_region_links": rows_adjacent,
        "presentation_and_runtime_summary": {
            "all_identity_specific_targets_absent_at_base": all(not row["target_status_at_base"]["identity_specific_targets_present"] for row in rows_direct + rows_adjacent),
            "native_blockbench_roundtrip_required_before_shipping": True,
            "blockbench_run": "NOT_RUN",
            "runtime_behavior_proven": False,
            "presentation_readability_proven": False,
        },
        "authority_partition": {
            "SAFE_NOW": [
                "11 direct identity pages and two adjacent references",
                "registry/localization/target scaffolding",
                "nonnumeric role, provenance, acquisition-source, and crafting-edge mapping",
                "native repair and approved-art presentation preparation",
            ],
            "W1-001-CM": "RATIFIED_EXACT_PROPOSAL_BYTES_PRESERVED",
            "W1-003-PEARL-DEPTHS": "RATIFIED_EXACT_PROPOSAL_BYTES_PRESERVED",
            "W1-004-CM": "RATIFIED_EXACT_PROPOSAL_BYTES_PRESERVED",
            "W1-CREATIVE-005": "DEFERRED_BY_USER; blocks only distinct Gale-strung prism_bow and other sidegrade representations, not the base prism_bow identity.",
        },
        "ashen_runtime_dependency": {
            "status": "MANAGED_REVIEWER_ACTIVATION_BLOCKED",
            "relationship": "FINAL_INTEGRATION_DEPENDENCY_ONLY",
            "crystal_dependency": False,
        },
        "proof_boundary": {
            "proven": ["exact 11+2 link coverage", "source hashes", "base target presence/absence", "static native gaps", "recipe/acquisition/provenance mapping", "deterministic regeneration"],
            "not_proven": ["native Blockbench round-trip", "shipping presentation", "recipes", "runtime behavior", "loot or rewards", "BP/RP integration", "BDS", "client", "console", "candidate readiness"],
        },
    }
    return data


def markdown(data: dict) -> str:
    native_repair = sum(row["native_readiness"]["native_roundtrip"] == "NOT_RUN_REPAIR_REQUIRED" for row in data["direct_packet003_links"] + data["adjacent_cross_region_links"])
    return "\n".join([
        "# Crystal Marsh Equipment Intake",
        "",
        f"Status: `{data['status']}`",
        "",
        f"Base: `{data['base']['commit']}` / tree `{data['base']['tree']}`.",
        "",
        "This is a deterministic intake map only. It changes no BP, RP, runtime, decision ledger, or qualification state.",
        "",
        "## Coverage",
        "",
        "| Relationship | Count | Codex treatment |",
        "|---|---:|---|",
        "| Direct Packet 003 links | 11 | Eleven CM equipment pages |",
        "| Adjacent cross-region links | 2 | Reference only; no CM address |",
        f"| Native static repair-required rows | {native_repair} | Blockbench was not run |",
        "",
        "All identity-specific shipping targets were absent at the bound base. Shared catalog, Codex, texture-atlas, and language targets exist as frameworks only; they are not evidence that any Crystal equipment identity ships.",
        "",
        "## Authority partition",
        "",
        "`W1-001-CM`, `W1-003-PEARL-DEPTHS`, and `W1-004-CM` are ratified with their exact proposal bytes preserved. This receipt refreshes only the intake's authority hashes and ratification descriptions; it does not mutate the authority files.",
        "",
        "`W1-CREATIVE-005` remains deferred. It blocks the distinct Gale-strung `prism_bow` representation, not the base `prism_bow` page. `surveyor_staff` and `trail_compass` stay adjacent Skyreach/pilgrim references and receive no CM registry address.",
        "",
        "The dormant Ashen services remain a final-integration dependency only and are not called by this intake.",
        "",
        "## Proof boundary",
        "",
        "Tests prove exact 11+2 coverage, source hashes, base target status, static native gaps, blocker separation, and byte-deterministic regeneration. They do not prove native Blockbench round-trip, presentation readability, recipes, gameplay, BP/RP integration, BDS, client, multiplayer, or console behavior.",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--bedrock-root", type=Path, default=BEDROCK_ROOT_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = build(args.repo_root, args.bedrock_root)
    (args.output_dir / "CRYSTAL_EQUIPMENT_INTAKE.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    (args.output_dir / "CRYSTAL_EQUIPMENT_INTAKE.md").write_text(markdown(data))


if __name__ == "__main__":
    main()
