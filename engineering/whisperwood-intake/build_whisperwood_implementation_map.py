#!/usr/bin/env python3
"""Build a deterministic, source-bound Whisperwood implementation map.

This tool inventories authority and proposes target paths. It never edits BP/RP.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
BEDROCK = next(parent for parent in REPO.parents if parent.name == "bedrock-server")
CREATIVE = BEDROCK / "program/crazycraft-pack-production-v1/studio-prep/creative"
PACKET = BEDROCK / "program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-001-whisperwood"
INVENTORY = REPO / "engineering/normalization/PACKET_NORMALIZATION_INVENTORY.json"
LEDGER = REPO / "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json"
CONTRACT = CREATIVE / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json"
OUT = REPO / "engineering/whisperwood-intake/WHISPERWOOD_VERTICAL_IMPLEMENTATION_MAP.json"
OUT_MD = REPO / "engineering/whisperwood-intake/WHISPERWOOD_VERTICAL_IMPLEMENTATION_MAP.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel_workspace(path: Path) -> str:
    return path.relative_to(BEDROCK).as_posix()


def canonical_workspace_paths(canonical: dict) -> dict:
    normalized = json.loads(json.dumps(canonical))
    for value in normalized.values():
        if value.get("path") and not value["path"].startswith("program/"):
            value["path"] = f"program/{value['path']}"
    return normalized


def creative_hits(asset_id: str) -> list[dict]:
    pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(asset_id)}(?![A-Za-z0-9_])", re.I)
    hits = []
    for path in sorted(CREATIVE.rglob("*.md")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                hits.append({
                    "path": rel_workspace(path),
                    "line": number,
                    "excerpt": line.strip()[:300],
                })
    return hits


def exact_g7_hits(asset_id: str) -> list[str]:
    roots = [REPO / "behavior_pack", REPO / "resource_pack", REPO / "assets"]
    pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(asset_id)}(?![A-Za-z0-9_])")
    hits: set[str] = set()
    for root in roots:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            if asset_id in path.name:
                hits.add(path.relative_to(REPO).as_posix())
                continue
            if path.suffix.lower() not in {".json", ".js", ".lang", ".md"}:
                continue
            try:
                if pattern.search(path.read_text(encoding="utf-8")):
                    hits.add(path.relative_to(REPO).as_posix())
            except UnicodeDecodeError:
                pass
    return sorted(hits)


def targets(category: str, asset_id: str) -> dict:
    shared = [
        "behavior_pack/scripts/catalog.js",
        "behavior_pack/scripts/codex.js",
        "resource_pack/texts/en_US.lang",
    ]
    if category == "creatures":
        return {
            "create": [
                f"behavior_pack/entities/{asset_id}.entity.json",
                f"behavior_pack/spawn_rules/{asset_id}.spawn_rules.json",
                f"behavior_pack/loot_tables/entities/{asset_id}.json",
                f"resource_pack/entity/{asset_id}.entity.json",
                f"resource_pack/models/aionbound/whisperwood/{asset_id}.geo.json",
                f"resource_pack/animations/aionbound/whisperwood/{asset_id}.animation.json",
                f"resource_pack/textures/aionbound/whisperwood/{asset_id}.png",
            ],
            "update_shared": shared + [
                "behavior_pack/scripts/combat.js",
                "behavior_pack/scripts/encounters.js",
                "behavior_pack/scripts/state.js",
                "behavior_pack/scripts/budgets.js",
                "resource_pack/animation_controllers/aionbound.animation_controllers.json",
                "resource_pack/render_controllers/aionbound.render_controllers.json",
            ],
        }
    if category == "resources":
        return {
            "create": [
                f"behavior_pack/items/{asset_id}.item.json",
                f"resource_pack/textures/aionbound/whisperwood/items/{asset_id}.png",
            ],
            "update_shared": shared + [
                "resource_pack/textures/item_texture.json",
                "behavior_pack/scripts/state.js",
            ],
        }
    if category == "blocks":
        create = [
            f"behavior_pack/blocks/{asset_id}.block.json",
            f"behavior_pack/loot_tables/blocks/{asset_id}.json",
            f"resource_pack/textures/aionbound/whisperwood/blocks/{asset_id}.png",
        ]
        if asset_id not in {"whisperwood_log", "stripped_whisperwood_log", "whisperwood_wood", "whisperwood_planks", "forest_brick"}:
            create.append(f"resource_pack/models/aionbound/whisperwood/{asset_id}.geo.json")
        return {
            "create": create,
            "update_shared": shared + [
                "resource_pack/blocks.json",
                "resource_pack/textures/terrain_texture.json",
            ],
        }
    if category == "plants":
        return {
            "create": [
                f"behavior_pack/blocks/{asset_id}.block.json",
                f"behavior_pack/loot_tables/blocks/{asset_id}.json",
                f"behavior_pack/features/{asset_id}.feature.json",
                f"behavior_pack/feature_rules/{asset_id}.feature_rule.json",
                f"resource_pack/models/aionbound/whisperwood/{asset_id}.geo.json",
                f"resource_pack/textures/aionbound/whisperwood/plants/{asset_id}.png",
            ],
            "update_shared": shared + [
                "resource_pack/blocks.json",
                "resource_pack/textures/terrain_texture.json",
            ],
        }
    if category == "structures":
        return {
            "create": [
                f"behavior_pack/structures/aionbound/whisperwood/{asset_id}.mcstructure",
                f"behavior_pack/features/{asset_id}.structure_feature.json",
                f"behavior_pack/feature_rules/{asset_id}.structure_feature_rule.json",
                f"behavior_pack/blocks/{asset_id}.block.json",
                f"behavior_pack/loot_tables/blocks/{asset_id}.json",
                f"resource_pack/models/aionbound/whisperwood/{asset_id}.geo.json",
                f"resource_pack/textures/aionbound/whisperwood/structures/{asset_id}.png",
            ],
            "update_shared": shared + [
                "behavior_pack/scripts/structures.js",
                "behavior_pack/scripts/state.js",
                "resource_pack/blocks.json",
                "resource_pack/textures/terrain_texture.json",
            ],
            "conditional": [
                f"behavior_pack/loot_tables/chests/whisperwood/{asset_id}.json",
            ],
        }
    raise ValueError(category)


SEMANTIC_PREDECESSORS = {
    "mosskip_fawn": ["behavior_pack/entities/mosskip.entity.json", "resource_pack/entity/mosskip.entity.json"],
    "mosskip_doe": ["behavior_pack/entities/mosskip.entity.json", "resource_pack/entity/mosskip.entity.json"],
    "mosskip_buck": ["behavior_pack/entities/mosskip.entity.json", "resource_pack/entity/mosskip.entity.json"],
    "hunter_camp": ["behavior_pack/structures/aionbound/hunters_blind.mcstructure", "behavior_pack/structures/aionbound/collapsed_survey_camp.mcstructure"],
    "moss_cairn": ["behavior_pack/structures/aionbound/pilgrim_cairn.mcstructure"],
    "forest_waystone": ["behavior_pack/features/waystone_ruin.feature.json", "behavior_pack/scripts/structures.js"],
    "hollow_cave_entrance": ["behavior_pack/structures/aionbound/glassroot_grotto.mcstructure"],
    "root_bridge": ["behavior_pack/structures/aionbound/lantern_causeway.mcstructure"],
}


def item_blockers(category: str, asset_id: str, issues: list[str]) -> list[dict]:
    blockers = []
    if category in {"creatures", "resources", "plants", "structures"}:
        blockers.append({
            "id": "W1-CREATIVE-004",
            "scope": "final drop/chest probability and quantity values; structural wiring is allowed",
            "blocks": "final economy values, not target-file construction",
        })
    if category == "creatures":
        blockers.append({
            "id": "W1-CREATIVE-001",
            "scope": "unratified non-warehouse creature-drop item candidates",
            "blocks": "final materialized loot identity; warehouse drops and narrative-only curiosities remain usable",
        })
    if asset_id == "thorn_stalker":
        blockers.append({
            "id": "W1-CREATIVE-003",
            "scope": "boss thresholds, timing, reset, multiplayer ownership, persistence, terminal rewards",
            "blocks": "apex completion; phase-kit architecture remains allowed",
        })
    if any(issue.startswith("DECLARED_") or issue.startswith("BRIEF_TEXTURE") for issue in issues):
        blockers.append({
            "id": "NATIVE_ASSET_DISPOSITION",
            "scope": "resolve brief/export animation, locator, or texture-resolution mismatch under Blockbench policy",
            "blocks": "shipping use where the asset class requires native proof; static integration preparation remains allowed",
        })
    return blockers


def main() -> None:
    inventory_doc = json.loads(INVENTORY.read_text(encoding="utf-8"))
    contract_doc = json.loads(CONTRACT.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    packet_contract = contract_doc["packets"]["001_whisperwood"]
    records = sorted(
        (row for row in inventory_doc["assets"] if row["packet_id"] == "001"),
        key=lambda row: (row["category"], row["warehouse_id"]),
    )

    indexed = {
        "creatures": {row["id"]: row for row in packet_contract["creatures"]},
        "resources": {row["id"]: row for row in packet_contract["resources"]},
        "blocks": {asset_id: {"id": asset_id} for asset_id in packet_contract["blocks"]},
        "plants": {asset_id: {"id": asset_id} for asset_id in packet_contract["plants"]},
        "structures": {row["id"]: row for row in packet_contract["structures"]},
    }

    assets = []
    for row in records:
        asset_id = row["warehouse_id"]
        category = row["category"]
        exact_hits = exact_g7_hits(asset_id)
        assets.append({
            "warehouse_id": asset_id,
            "runtime_id": row["runtime_id"],
            "category": category,
            "creative_contract": indexed[category][asset_id],
            "creative_evidence": creative_hits(asset_id),
            "canonical_source": canonical_workspace_paths(row["canonical"]),
            "source_brief": row["brief"],
            "static_validation": row["static"],
            "normalization": row["normalization"],
            "normalization_issues": row["issues"],
            "g7_collision": {
                "exact_id_hits": exact_hits,
                "classification": "EXACT_ID_COLLISION_REQUIRES_RECONCILIATION" if exact_hits else "NO_EXACT_ID_COLLISION",
                "semantic_predecessors": SEMANTIC_PREDECESSORS.get(asset_id, []),
                "rule": "Reuse framework/pattern only; approved Packet 001 identity supersedes any predecessor cast identity.",
            },
            "target_files": targets(category, asset_id),
            "blockers": item_blockers(category, asset_id, row["issues"]),
            "safe_now": [
                "normalize aionforge_ww identifiers to aionbound runtime identity",
                "copy and path normalized static export bytes into successor source targets",
                "author schema-valid BP/RP definitions and reference-closure tests",
                "wire approved role/acquisition/generation semantics without final numeric tuning",
            ],
        })

    linked_equipment = []
    for equipment_category, ids in packet_contract["equipment_links"].items():
        for asset_id in ids:
            linked_equipment.append({
                "id": asset_id,
                "category": equipment_category,
                "source_packet": "006",
                "status": "PACKET_006_DEPENDENCY_NOT_ONE_OF_PACKET_001_50",
                "target_files": [
                    f"behavior_pack/items/{asset_id}.item.json",
                    f"behavior_pack/recipes/{asset_id}.recipe.json",
                    f"resource_pack/attachables/{asset_id}.attachable.json",
                    f"resource_pack/models/aionbound/equipment/{asset_id}.geo.json",
                    f"resource_pack/animations/aionbound/equipment/{asset_id}.animation.json",
                    f"resource_pack/textures/aionbound/equipment/{asset_id}.png",
                ],
                "shared_targets": [
                    "resource_pack/textures/item_texture.json",
                    "resource_pack/texts/en_US.lang",
                    "behavior_pack/scripts/catalog.js",
                    "behavior_pack/scripts/codex.js",
                    "behavior_pack/scripts/combat.js",
                ],
            })

    ww_component_ids = {
        "moss_bind_glue",
        "amber_core",
        "thorn_cord",
        "cleaver_blank",
        "living_root_focus",
    }
    derived_components = []
    for decision in ledger["non_warehouse_terms"]["derived_components"]:
        asset_id = decision["id"].split(":", 1)[1]
        if asset_id not in ww_component_ids:
            continue
        derived_components.append({
            "term": decision["term"],
            "id": decision["id"],
            "identity_status": "RATIFIED_DERIVED_COMPONENT",
            "final_presentation_and_craft_home": "BLOCKED_BY_W1-CREATIVE-001",
            "target_files": [
                f"behavior_pack/items/{asset_id}.item.json",
                f"behavior_pack/recipes/{asset_id}.recipe.json",
                f"resource_pack/textures/aionbound/whisperwood/items/{asset_id}.png",
            ],
            "shared_targets": [
                "resource_pack/textures/item_texture.json",
                "resource_pack/texts/en_US.lang",
                "behavior_pack/scripts/catalog.js",
                "behavior_pack/scripts/codex.js",
            ],
        })

    report = {
        "schema": "aionbound.wave1.whisperwood-implementation-map.v1.0.0",
        "status": "SOURCE_BOUND_IMPLEMENTATION_MAP_COMPLETE_NO_PRODUCTION_MUTATION",
        "scope": "Packet 001 Whisperwood only; mapping, no BP/RP edits, no BDS, no candidate declaration",
        "base": {
            "commit": "05aff36392d9c31cf0745ee651427d7efc87b53d",
            "g7_immutable_commit": "042018eac3bd32b76d135219b9f59502dd4f4692",
        },
        "authority": {
            "contract_json": {"path": rel_workspace(CONTRACT), "sha256": sha256(CONTRACT)},
            "contract_markdown": {
                "path": rel_workspace(CREATIVE / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md"),
                "sha256": sha256(CREATIVE / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md"),
            },
            "decision_ledger": {"path": LEDGER.relative_to(REPO).as_posix(), "sha256": sha256(LEDGER)},
            "normalization_inventory": {"path": INVENTORY.relative_to(REPO).as_posix(), "sha256": sha256(INVENTORY)},
            "packet_manifest": {"path": rel_workspace(PACKET / "P0_MANIFEST.json"), "sha256": sha256(PACKET / "P0_MANIFEST.json")},
        },
        "counts": {
            "total": len(assets),
            "by_category": {category: sum(a["category"] == category for a in assets) for category in indexed},
            "exact_g7_id_collisions": sum(bool(a["g7_collision"]["exact_id_hits"]) for a in assets),
            "semantic_predecessor_mappings": sum(bool(a["g7_collision"]["semantic_predecessors"]) for a in assets),
        },
        "shared_reusable_g7_systems": [
            {"disposition": "KEEP", "paths": ["behavior_pack/scripts/runtime.js", "behavior_pack/scripts/router.js", "behavior_pack/scripts/main.js"], "use": "composed runtime and non-suppressing route architecture"},
            {"disposition": "REFINE", "paths": ["behavior_pack/scripts/state.js"], "use": "schema-v3 idempotent discovery/progression/reward persistence"},
            {"disposition": "REFINE", "paths": ["behavior_pack/scripts/budgets.js"], "use": "console-first locality and concurrent budgets"},
            {"disposition": "REFINE", "paths": ["behavior_pack/scripts/combat.js", "behavior_pack/scripts/encounters.js"], "use": "role AI hooks, admission, ownership, and reward guards; not legacy cast identity"},
            {"disposition": "KEEP", "paths": ["behavior_pack/scripts/structures.js", "behavior_pack/features", "behavior_pack/feature_rules", "behavior_pack/structures/aionbound"], "use": "bounded structure placement and generation framework"},
            {"disposition": "KEEP_REFINE", "paths": ["resource_pack/animation_controllers/aionbound.animation_controllers.json", "resource_pack/render_controllers/aionbound.render_controllers.json"], "use": "shared controller framework after exact geometry/animation/texture closure"},
            {"disposition": "REPLACE_CONTENT_KEEP_SCHEMA", "paths": ["behavior_pack/scripts/catalog.js", "behavior_pack/scripts/codex.js"], "use": "registry and persistent discovery schema, populated with Creative authority"},
        ],
        "linked_packet_006_equipment": {
            "count": len(linked_equipment),
            "note": "Required for the Packet 001 vertical exit, but owned by Packet 006 and excluded from the 50-ID Packet 001 count.",
            "items": sorted(linked_equipment, key=lambda item: (item["category"], item["id"])),
        },
        "ratified_whisperwood_derived_components": {
            "count": len(derived_components),
            "note": "Runtime IDs are ratified; final icon/craft-home decisions remain support-ticketed.",
            "items": sorted(derived_components, key=lambda item: item["id"]),
        },
        "global_blockers": [
            {"id": "W1-CREATIVE-001", "blocks": "materializing unratified non-warehouse drops/components and final WW craft closure"},
            {"id": "W1-CREATIVE-003", "blocks": "Thorn Court numeric, reset, ownership, persistence, and terminal reward completion"},
            {"id": "W1-CREATIVE-004", "blocks": "final loot/chest probability ranges, roll counts, and alternate-seal semantics"},
            {"id": "NATIVE_ASSET_DISPOSITION", "blocks": "shipping assets whose brief/export mismatches or risk class mandate native Blockbench proof"},
            {"id": "STRUCTURE_BYTES_NOT_PRESENT", "blocks": "structure registration until engineering authors actual block-built .mcstructure bytes; identity/design are already approved"},
        ],
        "safe_implementation_boundary": [
            "all 50 canonical IDs and source/export paths are bound",
            "namespace/path normalization and static asset staging",
            "schema-valid entity/block/item/feature/feature-rule scaffolding",
            "role-correct non-boss AI and spawn ecology without final numeric tuning",
            "approved warehouse-only loot identities with placeholder-free structural tables but no claimed final probabilities",
            "block-built structure authorship to approved roles and layouts",
            "Codex content binding and progression hooks through the AH rumor handoff",
            "targeted JSON, reference-closure, recipe, loot, PNG, geometry, and semantic checks",
        ],
        "not_proven": [
            "native Blockbench round trip",
            "Bedrock client rendering or inventory readability",
            "Stable BDS load",
            "Whisperwood checkpoint smoke",
            "physical console/controller/multiplayer",
            "candidate or release readiness",
        ],
        "assets": assets,
    }

    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Whisperwood vertical implementation map",
        "",
        "Status: `SOURCE_BOUND_IMPLEMENTATION_MAP_COMPLETE_NO_PRODUCTION_MUTATION`.",
        "",
        "This is an engineering intake map, not implementation or qualification. It binds all 50 Packet 001 warehouse IDs to canonical source bytes, Creative authority, G7 reuse boundaries, and exact proposed successor BP/RP targets. No production pack file was edited and no BDS run was performed.",
        "",
        "## Authority and counts",
        "",
        f"- Successor base: `{report['base']['commit']}`",
        f"- Immutable G7 parent: `{report['base']['g7_immutable_commit']}`",
        f"- Contract JSON SHA-256: `{report['authority']['contract_json']['sha256']}`",
        f"- Contract Markdown SHA-256: `{report['authority']['contract_markdown']['sha256']}`",
        f"- Decision ledger SHA-256: `{report['authority']['decision_ledger']['sha256']}`",
        f"- Normalization inventory SHA-256: `{report['authority']['normalization_inventory']['sha256']}`",
        "- Inventory: 10 creatures, 10 resources, 10 blocks, 10 plants, 10 structures; 50 total.",
        f"- Linked Packet 006 equipment dependencies: {report['linked_packet_006_equipment']['count']}. Ratified WW derived components: {report['ratified_whisperwood_derived_components']['count']}.",
        f"- Exact G7 ID collisions: {report['counts']['exact_g7_id_collisions']}. Semantic predecessor mappings: {report['counts']['semantic_predecessor_mappings']}.",
        "",
        "## Decision boundary",
        "",
        "Safely implementable now: namespace/path normalization; static asset staging; schema-valid definitions; non-boss role behavior; spawn and worldgen scaffolding; warehouse-only structural loot; block-built structures; Codex/progression hooks; targeted closure checks.",
        "",
        "Still blocking completion:",
        "",
        "- `W1-CREATIVE-001`: unratified non-warehouse drop/component identities and final WW craft closure.",
        "- `W1-CREATIVE-003`: Thorn Court numeric, reset, multiplayer, persistence, and terminal reward envelope.",
        "- `W1-CREATIVE-004`: final loot/chest probabilities, roll counts, and alternate-seal semantics.",
        "- `NATIVE_ASSET_DISPOSITION`: brief/export mismatches and risk-class Blockbench proof before shipping use.",
        "- `STRUCTURE_BYTES_NOT_PRESENT`: Engineering must author actual `.mcstructure` bytes from the approved designs; this is not a missing creative identity.",
        "",
        "## G7 reuse boundary",
        "",
        "Reuse the runtime composition/router, persistence migration pattern, bounded budgets, entity/encounter scaffolding, structure placement pipeline, controller framework, and Codex discovery schema. Do not inherit G7 cast, loot, recipe, or progression identity. The generic G7 mosskip and listed structure analogues are pattern evidence only.",
        "",
        "## Exact per-ID map",
        "",
        "The JSON twin contains every exact create/update target, all Creative evidence lines, source/export hashes, static findings, and blockers. The table below shows the primary mapping.",
        "",
        "| Category | Warehouse ID | Creative requirement | Canonical editable/export | G7 | Blocking disposition | Primary targets |",
        "|---|---|---|---|---|---|---|",
    ]
    for asset in assets:
        creative = asset["creative_contract"]
        requirement = ", ".join(f"{k}={v}" for k, v in creative.items() if k != "id") or "See Markdown evidence"
        canonical = asset["canonical_source"]
        source = f"`{canonical['bbmodel']['path']}`; `{canonical['geometry']['path']}`; `{canonical['png']['path']}`"
        collision = asset["g7_collision"]
        g7 = collision["classification"]
        if collision["semantic_predecessors"]:
            g7 += "; pattern: " + ", ".join(f"`{p}`" for p in collision["semantic_predecessors"])
        blocker_ids = sorted({b["id"] for b in asset["blockers"]})
        blockers = ", ".join(f"`{item}`" for item in blocker_ids) if blocker_ids else "none beyond global gates"
        primary = "; ".join(f"`{p}`" for p in asset["target_files"]["create"])
        lines.append(f"| {asset['category']} | `{asset['warehouse_id']}` | {requirement} | {source} | {g7} | {blockers} | {primary} |")
    lines += [
        "",
        "## Vertical-slice file groups",
        "",
        "1. Normalize source exports into `resource_pack/models/aionbound/whisperwood/` and `resource_pack/textures/aionbound/whisperwood/`; repair or document native dispositions before shipping use.",
        "2. Add the 10 BP/RP entity pairs, role animations, spawn rules, and structurally valid entity loot tables; keep Thorn Court completion gated.",
        "3. Add 10 resource items and item-texture/localization registry entries; only warehouse IDs and ratified derived components may materialize.",
        "4. Add 10 blocks and 10 plant-blocks with block loot, models/materials, terrain bindings, and plant feature/rule pairs.",
        "5. Author 10 block-built structure files plus feature/rule pairs and conditional chest tables; use the packet prop models as design inputs, not as proof that `.mcstructure` content exists.",
        "6. Update `catalog.js`, `codex.js`, `combat.js`, `encounters.js`, `state.js`, `budgets.js`, and `structures.js` through composed services; preserve the non-suppressing router.",
        "7. Add recipes/equipment links only where every identity is ratified; hold final economy values and blocked non-warehouse ingredients.",
        "8. Run targeted static/semantic closure only. BDS belongs at the parent-owned Whisperwood checkpoint after vertical completion.",
        "",
        "## External vertical dependencies",
        "",
        "The Packet 001 exit also depends on 21 approved Packet 006 equipment IDs and five ratified derived-component IDs. Their exact item/recipe/attachable/model/animation/texture targets are enumerated in the JSON twin under `linked_packet_006_equipment` and `ratified_whisperwood_derived_components`; they are not counted among the 50 Packet 001 warehouse IDs. Final component presentation/craft homes remain gated by `W1-CREATIVE-001`.",
        "",
        "## Proof boundary",
        "",
        "This map proves source and target traceability only. It does not prove native Blockbench round-trip, Bedrock rendering, UI readability, Stable BDS loading, same-world reopen, console/controller/multiplayer behavior, candidate status, or release readiness.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
