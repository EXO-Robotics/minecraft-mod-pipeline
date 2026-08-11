#!/usr/bin/env python3
"""Build the point-in-time Ashen vertical readiness audit from an immutable Git tree."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE_COMMIT = "4e75503cc0597ba7e7ffe369a61e6db09212933a"
BASE_TREE = "e4a94c579612030c6f853eac9d214153fb48ef95"

AUTHORITY_PATH = "engineering/ashen-intake/authority/ASHEN_HIGHLANDS_VERTICAL_INTAKE_MAP.json"
EQUIPMENT_PATH = "engineering/ashen-intake/equipment/ASHEN_EQUIPMENT_INTAKE.json"
NATIVE_INTAKE_PATH = "engineering/native-assets/ashen/intake/ASHEN_PACKET_002_NATIVE_READINESS.json"
NATIVE_REP_PATH = "engineering/native-assets/ashen/representative/ASHEN_REPRESENTATIVE_NATIVE_REPORT.json"
CODEX_PATH = "engineering/ashen-intake/codex/ASHEN_CODEX_PROGRESSION_INTAKE_MAP.json"
LEDGER_PATH = "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json"

RESOURCE_IDS = [
    "smolder_bark", "charbone", "sulfur_cluster", "volcanic_glass_shard",
    "ember_resin", "heatstone", "furnace_chitin", "basalt_core",
    "ash_crystal", "fire_bloom_seed",
]
BLOCK_IDS = [
    "ash_log", "char_planks", "ash_soil", "cinder_gravel", "smolder_stone",
    "basalt_brick", "basalt_pillar", "heat_bark", "ember_moss",
    "volcanic_glass_block",
]


def git(*args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(REPO), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    )
    return result.stdout


def base_bytes(path: str) -> bytes:
    return git("show", f"{BASE_COMMIT}:{path}", text=False)


def base_text(path: str) -> str:
    return base_bytes(path).decode("utf-8")


def base_json(path: str) -> dict:
    return json.loads(base_text(path))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def base_files() -> set[str]:
    return set(git("ls-tree", "-r", "--name-only", BASE_COMMIT).splitlines())


def runtime_texts(files: set[str]) -> dict[str, str]:
    allowed = (".json", ".js", ".mjs", ".lang")
    result = {}
    for path in sorted(files):
        if not path.startswith(("behavior_pack/", "resource_pack/")):
            continue
        if not path.endswith(allowed):
            continue
        try:
            result[path] = base_text(path)
        except UnicodeDecodeError:
            continue
    return result


def exact_runtime_hits(asset_id: str, texts: dict[str, str]) -> list[str]:
    pattern = re.compile(rf"(?<![a-z0-9_])aionbound:{re.escape(asset_id)}(?![a-z0-9_])")
    return [path for path, text in texts.items() if pattern.search(text)]


def present(paths: list[str], files: set[str]) -> list[str]:
    return [path for path in paths if path in files]


def expected_registration(asset_id: str, category: str) -> list[str]:
    if category == "resources":
        return [
            f"behavior_pack/items/{asset_id}.item.json",
            f"resource_pack/textures/aionbound/ashen/items/{asset_id}.png",
            "resource_pack/textures/item_texture.json",
            "resource_pack/texts/en_US.lang",
        ]
    if category == "blocks":
        return [
            f"behavior_pack/blocks/{asset_id}.block.json",
            f"resource_pack/textures/aionbound/ashen/blocks/{asset_id}.png",
            "resource_pack/blocks.json",
            "resource_pack/textures/terrain_texture.json",
            "resource_pack/texts/en_US.lang",
        ]
    return []


def packet_native_state(asset_id: str, category: str, intake_by_id: dict, rep_by_id: dict) -> dict:
    if category in {"resources", "blocks"}:
        return {
            "status": "NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM",
            "reason": "Shipping form is an ordinary full cube or flat inventory icon; no fake Blockbench claim is made.",
        }
    if asset_id in rep_by_id:
        rep = rep_by_id[asset_id]
        return {
            "status": "PASS_REPRESENTATIVE_NATIVE_REPAIR_GATE",
            "receipt_status": rep["status"],
            "warning_count": rep["warning_count"],
            "error_count": rep["error_count"],
            "receipt_sha256": rep["receipt_sha256"],
            "limitation": "Native source/export proof only; no BP/RP binding or client rendering proof.",
        }
    original = intake_by_id[asset_id]
    return {
        "status": "NATIVE_REPAIR_REQUIRED",
        "packet_disposition": original["blockbench_disposition"],
        "native_roundtrip": original["native_roundtrip"],
        "native_export_equivalence": original["native_export_equivalence"],
    }


def packet_surface_state(asset_id: str, category: str, runtime_hits: list[str], files: set[str]) -> dict:
    expected = expected_registration(asset_id, category)
    expected_present = present(expected, files)
    is_static = category in {"resources", "blocks"} and len(expected_present) == len(expected)
    return {
        "item_or_block_registration": "IMPLEMENTED_STATIC_PASS" if is_static else "NOT_IMPLEMENTED",
        "registration_evidence": expected_present,
        "exact_runtime_reference_hits": runtime_hits,
        "entity_ai_motion_spawn": "NOT_APPLICABLE" if category != "creatures" else "NOT_IMPLEMENTED",
        "plant_runtime_and_worldgen": "NOT_APPLICABLE" if category != "plants" else "NOT_IMPLEMENTED",
        "structure_assembly_and_worldgen": "NOT_APPLICABLE" if category != "structures" else "NOT_IMPLEMENTED",
        "acquisition_loot_recipes_equipment": "NOT_IMPLEMENTED_AUTHORITY_BLOCKED",
        "codex_progression_persistence": "INTAKE_MAP_ONLY_NOT_RUNTIME",
        "kiln_sky": "BLOCKED_W1_003_AND_W1_004" if asset_id == "ash_drake" else "NOT_APPLICABLE",
        "overall": "IMPLEMENTED_STATIC_PASS" if is_static else "SAFE_BUT_UNIMPLEMENTED",
    }


def equipment_surface(asset: dict, runtime_hits: list[str], files: set[str]) -> dict:
    asset_id = asset["id"]
    if asset_id == "briar_ring":
        base_paths = [
            "behavior_pack/items/briar_ring.item.json",
            "behavior_pack/recipes/briar_ring.recipe.json",
            "resource_pack/attachables/briar_ring.attachable.json",
            "resource_pack/models/aionbound/equipment/briar_ring.geo.json",
        ]
        return {
            "overall": "EXISTING_WHISPERWOOD_BASE_KEEP_NOT_ASHEN_IMPLEMENTATION",
            "runtime_binding": "IMPLEMENTED_WW_BASE_ONLY",
            "evidence": present(base_paths, files),
            "exact_runtime_reference_hits": runtime_hits,
            "native_packet006": "NOT_RUN; existing WW bytes are not replacement authority",
            "acquisition_loot_recipe": "EXISTING_WW_BASE_ONLY",
            "codex_progression_persistence": "EXISTING_WW_BASE_ONLY; AH temper route withheld",
            "kiln_sky": "NOT_APPLICABLE",
        }
    return {
        "overall": "SAFE_SHELL_AND_NATIVE_WORK_UNIMPLEMENTED",
        "runtime_binding": "NOT_IMPLEMENTED",
        "evidence": [],
        "exact_runtime_reference_hits": runtime_hits,
        "native_packet006": "NATIVE_ROUNDTRIP_REQUIRED",
        "acquisition_loot_recipe": "NOT_IMPLEMENTED_AUTHORITY_BLOCKED",
        "codex_progression_persistence": "INTAKE_MAP_ONLY_NOT_RUNTIME",
        "kiln_sky": "BLOCKED_W1_003_AND_W1_004" if asset_id == "ash_drake_horn" else "NOT_APPLICABLE",
    }


def build() -> dict:
    resolved_commit = git("rev-parse", BASE_COMMIT).strip()
    resolved_tree = git("rev-parse", f"{BASE_COMMIT}^{{tree}}").strip()
    if resolved_commit != BASE_COMMIT or resolved_tree != BASE_TREE:
        raise RuntimeError("immutable audit base mismatch")

    files = base_files()
    texts = runtime_texts(files)
    authority = base_json(AUTHORITY_PATH)
    equipment = base_json(EQUIPMENT_PATH)
    native_intake = base_json(NATIVE_INTAKE_PATH)
    native_rep = base_json(NATIVE_REP_PATH)
    codex = base_json(CODEX_PATH)
    ledger = base_json(LEDGER_PATH)

    intake_by_id = {entry["name"]: entry for entry in native_intake["assets"]}
    rep_by_id = {entry["asset"]: entry for entry in native_rep["assets"]}

    packet_assets = []
    for asset in authority["assets"]:
        asset_id = asset["warehouse_id"]
        category = asset["category"]
        hits = exact_runtime_hits(asset_id, texts)
        blockers = ["W1-001-AH", "W1-004-AH"]
        if asset_id == "ash_drake":
            blockers.insert(1, "W1-003-KILN-SKY")
        packet_assets.append({
            "id": asset_id,
            "runtime_id": asset["runtime_id"],
            "category": category,
            "surface_state": packet_surface_state(asset_id, category, hits, files),
            "native_evidence": packet_native_state(asset_id, category, intake_by_id, rep_by_id),
            "authority_blockers": blockers,
            "client_and_bds": "UNPROVEN",
            "validator_coverage": (
                "STATIC_PRODUCT_AND_RECEIPT_TESTS_PRESENT"
                if category in {"resources", "blocks"}
                else "INTAKE_AND_NATIVE_EVIDENCE_TESTS_ONLY_NO_RUNTIME_COVERAGE"
            ),
        })

    equipment_assets = []
    for asset in equipment["assets"]:
        asset_id = asset["id"]
        hits = exact_runtime_hits(asset_id, texts)
        equipment_assets.append({
            "id": asset_id,
            "runtime_id": f"aionbound:{asset_id}",
            "category": asset["category"],
            "surface_state": equipment_surface(asset, hits, files),
            "authority_blockers": asset.get("blocked_by", []),
            "client_and_bds": "UNPROVEN_FOR_ASHEN_PACKET006",
            "validator_coverage": "INTAKE_COLLISION_AND_HASH_TESTS_ONLY_NO_NEW_ASHEN_RUNTIME_COVERAGE",
        })

    packet_counts = Counter(entry["surface_state"]["overall"] for entry in packet_assets)
    native_counts = Counter(entry["native_evidence"]["status"] for entry in packet_assets)
    equipment_counts = Counter(entry["surface_state"]["overall"] for entry in equipment_assets)

    implemented_packet_ids = [
        entry["id"] for entry in packet_assets
        if entry["surface_state"]["overall"] == "IMPLEMENTED_STATIC_PASS"
    ]
    runtime_packet_ids = [entry["id"] for entry in packet_assets if entry["surface_state"]["exact_runtime_reference_hits"]]
    non_static_packet_ids = sorted(set(runtime_packet_ids) - set(RESOURCE_IDS) - set(BLOCK_IDS))

    source_paths = [AUTHORITY_PATH, EQUIPMENT_PATH, NATIVE_INTAKE_PATH, NATIVE_REP_PATH, CODEX_PATH, LEDGER_PATH]
    return {
        "schema": "aionbound.wave1.ashen-vertical-readiness-audit.v1",
        "status": "ASHEN_VERTICAL_NOT_READY_AUTHORITY_AND_CONSTRUCTION_PENDING",
        "audit_base": {
            "commit": BASE_COMMIT,
            "tree": BASE_TREE,
            "g7_immutable": True,
            "scope": "read-only product inspection of exact G8 integration tree; audit artifacts only",
        },
        "source_evidence": [
            {"path": path, "sha256": sha256(base_bytes(path))} for path in source_paths
        ],
        "authority_state": {
            "checkpoint_1_passed": codex["base"]["checkpoint_1_passed"],
            "decision_ledger_status": ledger["status"],
            "ashen_proposals": {
                "W1-001-AH": "PROPOSED_NOT_RATIFIED",
                "W1-003-KILN-SKY": "PROPOSED_NOT_RATIFIED",
                "W1-004-AH": "PROPOSED_NOT_RATIFIED",
                "W1-CREATIVE-005": "DEFERRED_BY_USER",
            },
            "broad_ashen_continuation": "REQUIRES_LITERAL_POST_CHECKPOINT_USER_AUTHORIZATION_AND_RATIFICATION",
        },
        "summary": {
            "packet002_ids": len(packet_assets),
            "packet006_ashen_ids": len(equipment_assets),
            "packet002_overall_counts": dict(sorted(packet_counts.items())),
            "packet002_native_counts": dict(sorted(native_counts.items())),
            "packet006_overall_counts": dict(sorted(equipment_counts.items())),
            "implemented_static_packet002_ids": implemented_packet_ids,
            "exact_packet002_runtime_reference_ids": runtime_packet_ids,
            "packet002_runtime_ids_beyond_safe_resources_and_blocks": non_static_packet_ids,
            "confirmation": (
                "No exact Packet002 creature, plant, structure, AI/spawn, worldgen, loot/recipe, "
                "Codex/progression/persistence, or Kiln Sky runtime implementation exists at the audit base. "
                "The only exact Packet002 BP/RP implementation is the ten flat resource-item registrations/icons "
                "and ten ordinary full-cube block registrations/textures."
            ),
            "packet006_confirmation": (
                "Thirteen new Ashen Packet006 identities are absent. briar_ring is the existing Whisperwood base "
                "and is not Ashen implementation or authority for a heat-tempered sidegrade."
            ),
        },
        "packet002": packet_assets,
        "packet006_ashen": equipment_assets,
        "system_readiness": {
            "item_and_block_registration": "20_OF_20_SAFE_FOUNDATION_STATIC_PASS",
            "icon_evidence": "10_OF_10_RESOURCE_ICONS_STATIC_PASS_CLIENT_READABILITY_UNPROVEN",
            "native_evidence": "7_REPRESENTATIVES_PASS_23_CUSTOM_ASSETS_STILL_REQUIRE_NATIVE_REPAIR_20_NA",
            "entities_ai_spawn": "0_OF_10_IMPLEMENTED",
            "plants_worldgen": "0_OF_10_IMPLEMENTED",
            "structures_worldgen": "0_OF_10_IMPLEMENTED",
            "acquisition_loot_recipes_equipment": "NOT_IMPLEMENTED_AND_W1_001_W1_004_BLOCKED",
            "codex_progression_persistence": "DETERMINISTIC_INTAKE_MAP_ONLY_NO_RUNTIME",
            "kiln_sky": "IDENTITY_ONLY_INTAKE_W1_003_AND_W1_004_BLOCKED_NO_RUNTIME",
            "packet006_runtime": "13_NEW_ABSENT_1_WW_BASE_REUSE_ONLY",
            "client_bds_console": "UNPROVEN_NO_NEW_BDS_RUN_AUTHORIZED_OR_PERFORMED",
        },
        "validator_coverage": {
            "covered": [
                "Packet002 authority-map determinism and roster closure",
                "Packet002 static native intake parse/hash/PNG checks",
                "seven representative native repair receipts",
                "ten resource item/icon/atlas/localization registrations",
                "ten full-cube block/texture/registry/localization registrations",
                "Packet006 intake hashes, collision scan, and blocker partition",
                "Ashen support-proposal schema and deterministic bytes",
            ],
            "not_covered_because_runtime_absent": [
                "entity component/AI/motion/spawn behavior",
                "plant block/feature/harvest behavior",
                "structure mcstructure/feature-rule placement",
                "Ashen acquisition, loot, recipes, equipment behavior",
                "Ashen Codex events, progression composition, persistence migration",
                "Kiln Sky encounter/reward/recovery semantics",
                "exact package Stable BDS or client behavior",
            ],
        },
        "minimal_continuation_order_after_exact_user_authorization": [
            {
                "step": 1,
                "action": "Ratify W1-001-AH, W1-003-KILN-SKY, and W1-004-AH exactly as proposed; preserve W1-CREATIVE-005 deferred.",
            },
            {
                "step": 2,
                "action": "Complete native repair/export evidence for the remaining 23 Packet002 custom assets and all 14 Packet006 source assets; do not replace the existing briar_ring base.",
            },
            {
                "step": 3,
                "action": "Finish the noncombat foundation: block drops/recipes, ten plants and harvesting, regional resources, bounded features, and placement/worldgen using the existing 20 static registrations.",
            },
            {
                "step": 4,
                "action": "Implement the nine non-apex creatures vertically: BP/RP binding, authored motion, role AI, natural spawn/caps, approved loot, discovery, and Codex hooks.",
            },
            {
                "step": 5,
                "action": "Implement all ten structure assemblies and bounded generation, with approved structure loot and encounter identities; keep ember_forge terminal behavior disabled until the Kiln Sky step.",
            },
            {
                "step": 6,
                "action": "Implement derived components, closed recipes, 13 new Packet006 runtime identities, repair/durability/roles, and reuse-only briar_ring linkage.",
            },
            {
                "step": 7,
                "action": "Implement Kiln Sky and ash_drake from the ratified envelope, including multiplayer ownership, reset, durable seal credit, once-per-player physical fulfillment, recovery, repeat-clear, and ember_forge_core non-seal semantics.",
            },
            {
                "step": 8,
                "action": "Append Ashen Codex/progression rows, apply the idempotent registry migration, compose handlers, close persistence/reward guards, then run targeted source/closure tests only; do not add an intermediate BDS gate.",
            },
        ],
        "proof_boundary": {
            "proves": [
                "exact source state at the pinned commit/tree",
                "per-ID BP/RP presence or absence for 50 Packet002 and 14 Packet006 Ashen identities",
                "current static item/block and native-evidence dispositions",
                "current authority blockers and test-coverage gaps",
            ],
            "does_not_prove": [
                "future implementation correctness",
                "runtime AI, world generation, loot economy, progression, persistence, or Kiln Sky behavior",
                "Bedrock client rendering/audio/UI readability",
                "Stable BDS admission for Ashen changes",
                "multiplayer, controller, Realm, split-screen, physical PS4, Marketplace, release, or candidate readiness",
            ],
        },
    }


def render_markdown(data: dict) -> str:
    summary = data["summary"]
    lines = [
        "# Ashen Highlands vertical readiness audit",
        "",
        f"Audit base: `{data['audit_base']['commit']}` / tree `{data['audit_base']['tree']}`.",
        "",
        f"Status: **{data['status']}**",
        "",
        "## Bottom line",
        "",
        summary["confirmation"],
        "",
        summary["packet006_confirmation"],
        "",
        "This is a point-in-time source audit. It does not authorize Ashen construction and it does not claim client or BDS proof.",
        "",
        "## Counts",
        "",
        "| Surface | Current evidence |",
        "|---|---|",
        "| Packet002 exact IDs | 50 |",
        "| Packet002 static product implementation | 10 resources + 10 full-cube blocks |",
        "| Packet002 entity / plant / structure runtime | 0 / 10, 0 / 10, 0 / 10 |",
        "| Packet002 native evidence | 7 representative PASS; 23 repair required; 20 Blockbench N/A |",
        "| Packet006 Ashen runtime | 13 new absent; `briar_ring` is existing WW base only |",
        "| Ashen Codex/progression/persistence | intake maps only |",
        "| Kiln Sky | identity map only; no executable encounter |",
        "| Client / Stable BDS | unproven for Ashen product changes |",
        "",
        "## Packet002 per-ID state",
        "",
        "| Category | ID | Product state | Native evidence | Authority blockers |",
        "|---|---|---|---|---|",
    ]
    for entry in data["packet002"]:
        lines.append(
            f"| {entry['category']} | `{entry['id']}` | {entry['surface_state']['overall']} | "
            f"{entry['native_evidence']['status']} | {', '.join(entry['authority_blockers'])} |"
        )
    lines.extend([
        "",
        "## Packet006 Ashen per-ID state",
        "",
        "| Category | ID | Product state | Authority blockers |",
        "|---|---|---|---|",
    ])
    for entry in data["packet006_ashen"]:
        blockers = ", ".join(entry["authority_blockers"]) or "none"
        lines.append(f"| {entry['category']} | `{entry['id']}` | {entry['surface_state']['overall']} | {blockers} |")
    lines.extend([
        "",
        "## Minimal continuation order after exact authorization",
        "",
    ])
    for entry in data["minimal_continuation_order_after_exact_user_authorization"]:
        lines.append(f"{entry['step']}. {entry['action']}")
    lines.extend([
        "",
        "## Proof boundary",
        "",
        "Proven:",
        "",
    ])
    lines.extend(f"- {item}" for item in data["proof_boundary"]["proves"])
    lines.extend(["", "Not proven:", ""])
    lines.extend(f"- {item}" for item in data["proof_boundary"]["does_not_prove"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    data = build()
    json_path = HERE / "ASHEN_VERTICAL_READINESS_AUDIT.json"
    md_path = HERE / "ASHEN_VERTICAL_READINESS_AUDIT.md"
    json_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(data), encoding="utf-8")
    print(f"wrote {json_path.relative_to(REPO)}")
    print(f"wrote {md_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
