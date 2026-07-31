#!/usr/bin/env python3
"""Materialize the frozen SF intake into evidence and clean-room deliverables.

This command consumes only an already-frozen intake.  Private evidence remains
under ``analysis``; only validated abstract contracts are written beneath
``sanitized-contracts``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from mccompiler.orchestration.workload import (
    build_skyfactory4_workload_catalog,
    canonical_workload_bytes,
    validate_sanitized_workload,
    validate_sanitized_workload_catalog,
)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(value)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_json(path: Path, value: Any) -> None:
    _atomic_bytes(path, _json_bytes(value))


def _write_text(path: Path, value: str) -> None:
    _atomic_bytes(path, value.rstrip().encode("utf-8") + b"\n")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


ASSET_CONTRACTS = (
    ("assets.world", "World surfaces and environmental landmarks", "static geometry", 16, 4096),
    ("assets.blocks", "Readable placed blocks and interaction states", "world geometry", 8, 2048),
    ("assets.items", "Inventory-readable items and tools", "held and inventory geometry", 8, 2048),
    ("assets.tools", "Held tools, durability states, and action feedback", "held geometry", 8, 2048),
    ("assets.interfaces", "Controller-readable interfaces and icons", "two-dimensional interface", 4, 1024),
    ("assets.trees", "Renewable resource trees and harvest states", "world geometry", 12, 4096),
    ("assets.machines", "Processing and power machine states", "world geometry", 16, 4096),
    ("assets.storage", "Storage blocks and capacity states", "world and interface geometry", 12, 4096),
    ("assets.crops", "Crop growth and harvest states", "world geometry", 8, 2048),
    ("assets.creatures", "Creature silhouettes and action states", "animated entity geometry", 16, 4096),
    ("assets.effects", "Status and process effects", "bounded transient geometry", 8, 1024),
    ("assets.particles", "Particles and short-lived action feedback", "bounded transient geometry", 8, 1024),
    ("assets.wearables", "Armor and wearable state families", "attached entity geometry", 12, 4096),
    ("assets.structures", "Exploration structures and encounter readability", "world geometry", 16, 8192),
    ("assets.audio", "Original feedback sounds and ambient cues", "non-visual feedback", 0, 0),
    ("assets.presentation", "Original presentation identity", "interface presentation", 4, 1024),
)


RUNTIME_CONTRACTS = (
    ("runtime.state", "Versioned persistent state with explicit scope and bounded records."),
    ("runtime.identifiers", "Stable namespaced identifiers with deterministic collision handling."),
    ("runtime.recipe-registry", "Validated transformation registration with conflict and disable policy."),
    ("runtime.scheduler", "Bounded scheduling with chunk lifecycle, cancellation, and recovery rules."),
    ("runtime.power-graph", "Conserved producer, consumer, storage, and transfer accounting."),
    ("runtime.transfer-graph", "Lossless item and fluid movement with capacity and backpressure."),
    ("runtime.ownership", "World and player ownership with explicit multiplayer permissions."),
    ("runtime.interface-framework", "Controller-first interaction states with recoverable navigation."),
    ("runtime.advancement-ledger", "World and player milestone state with auditable transitions."),
    ("runtime.migrations", "Schema versioning, idempotent upgrades, and safe unsupported-version refusal."),
    ("runtime.chunk-lifecycle", "Load, unload, restart, and reconnect state transitions."),
    ("runtime.synchronization", "Authoritative multiplayer state and bounded synchronization events."),
    ("runtime.telemetry", "Bounded counters for performance, conservation, and failure diagnosis."),
    ("runtime.test-hooks", "Deterministic setup and observation contracts without production mutation."),
)


QUALIFICATION_CASES = (
    ("startup", "The packaged product starts without fatal errors and reaches a ready state."),
    ("fresh-world-bootstrap", "A fresh world reaches its first renewable-resource action."),
    ("progression-reachability", "Each required milestone has a reachable prerequisite chain."),
    ("resource-conservation", "Bounded processing neither creates nor loses undeclared resources."),
    ("automation-correctness", "Automated chains stop safely under full capacity and resume without duplication."),
    ("power-accounting", "Generation, transfer, storage, and consumption remain conserved."),
    ("restart-persistence", "Declared state survives save, stop, restart, and reconnect."),
    ("multiplayer-ownership", "Two players cannot bypass declared ownership or corrupt shared state."),
    ("chunk-lifecycle", "Unload and reload do not duplicate, lose, or orphan active work."),
    ("controller-usability", "Critical progression is navigable without pointer-only interaction."),
    ("representative-performance", "Representative factories remain inside declared workload budgets."),
    ("endgame-completion", "A fresh-world path can satisfy the declared completion contract."),
)


def _copy_evidence_deliverables(root: Path, private: Path) -> None:
    destinations = {
        "FULL_FILE_INVENTORY.json": root / "analysis" / "FULL_FILE_INVENTORY.json",
        "MOD_INVENTORY.json": root / "analysis" / "mods" / "MOD_INVENTORY.json",
        "MOD_DEPENDENCY_GRAPH.json": root / "analysis" / "mods" / "MOD_DEPENDENCY_GRAPH.json",
        "PROGRESSION_GRAPH.json": root / "analysis" / "progression" / "PROGRESSION_GRAPH.json",
        "RECIPE_REACHABILITY_GRAPH.json": root / "analysis" / "recipes" / "RECIPE_REACHABILITY_GRAPH.json",
        "ASSET_FAMILY_INVENTORY.json": root / "analysis" / "assets" / "ASSET_FAMILY_INVENTORY.json",
        "RIGHTS_LEDGER.json": root / "analysis" / "rights" / "RIGHTS_LEDGER.json",
    }
    for name, destination in destinations.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(private / name, destination)


def _write_workloads(root: Path) -> dict[str, Any]:
    catalog = build_skyfactory4_workload_catalog()
    workloads = validate_sanitized_workload_catalog(catalog["workloads"])
    workload_root = root / "sanitized-contracts" / "workloads"
    for packet in workloads:
        safe = validate_sanitized_workload(packet)
        _atomic_bytes(workload_root / f"{safe['workload_id']}.json", canonical_workload_bytes(safe))
    _write_json(workload_root / "WORKLOAD_CATALOG.json", catalog)
    _write_json(root / "sanitized-contracts" / "WORKLOAD_DEPENDENCY_GRAPH.json", catalog["dependency_graph"])
    return catalog


def _write_runtime_and_assets(root: Path, catalog: dict[str, Any]) -> None:
    consumers: dict[str, list[str]] = defaultdict(list)
    for packet in catalog["workloads"]:
        for contract in packet["inputs_produced_by_other_workloads"]:
            consumers[contract].append(packet["workload_id"])
    runtime = {
        "schema_version": "1.0.0",
        "document_id": "sf-shared-runtime-requirements-1.0.0",
        "implementation_selected": False,
        "owner_workload": "SF-T11",
        "requirements": [
            {
                "contract_id": contract_id,
                "requirement": requirement,
                "consumers": sorted(consumers.get(contract_id, [])),
                "versioned_interface_required": True,
                "failure_policy_required": True,
                "migration_policy_required": True,
                "bounded_performance_contract_required": True,
            }
            for contract_id, requirement in RUNTIME_CONTRACTS
        ],
    }
    _write_json(root / "sanitized-contracts" / "shared-runtime" / "SHARED_RUNTIME_REQUIREMENTS.json", runtime)

    assets = {
        "schema_version": "1.0.0",
        "document_id": "sf-original-asset-contract-index-1.0.0",
        "owner_workload": "SF-T10",
        "source_assets_included": False,
        "contracts": [
            {
                "asset_contract_id": contract_id,
                "gameplay_role": role,
                "geometry_class": geometry,
                "required_states": ["available", "active", "unavailable"],
                "interaction_geometry": "Use bounded product-native collision and selection geometry where interactive.",
                "animation_requirement": "Use only functional state feedback required by the product contract.",
                "attachment_points": "Declare portable attachment or connection roles when required by gameplay.",
                "material_class": "Use original product-owned materials selected for readability.",
                "readability_requirement": "Remain distinguishable at handheld distance and under controller focus.",
                "texture_resolution_max": texture,
                "geometry_units_max": geometry_units,
                "originality_requirement": "Create original expression; no identity-bearing source expression is authorized.",
                "physical_console_verified": False,
            }
            for contract_id, role, geometry, texture, geometry_units in ASSET_CONTRACTS
        ],
    }
    _write_json(root / "sanitized-contracts" / "asset-contracts" / "ASSET_CONTRACT_INDEX.json", assets)


def _write_qualification(root: Path) -> None:
    owner_for_class = {
        "WORKER_LOCAL": "feature_producer",
        "T1_MECHANICAL_PREFLIGHT": "t1_preflight_tester",
        "STABLE_BDS": "bds_tester",
        "T10_PRIVATE_AUDIT": "independent_auditor",
        "T2_SHARED_ADAPTER": "t2_adapter_owner",
        "INTEGRATION": "segment_integrator",
        "DESKTOP_CLIENT": "client_qa",
        "REALMS": "realms_qa",
        "CONTROLLER": "controller_qa",
        "SPLIT_SCREEN": "multiplayer_qa",
        "PHYSICAL_PS4": "console_qa",
    }
    routing = {
        "startup": ["WORKER_LOCAL", "T1_MECHANICAL_PREFLIGHT", "STABLE_BDS"],
        "fresh-world-bootstrap": ["STABLE_BDS", "DESKTOP_CLIENT"],
        "progression-reachability": ["T10_PRIVATE_AUDIT", "INTEGRATION", "DESKTOP_CLIENT"],
        "resource-conservation": ["WORKER_LOCAL", "STABLE_BDS", "INTEGRATION"],
        "automation-correctness": ["WORKER_LOCAL", "STABLE_BDS", "INTEGRATION"],
        "power-accounting": ["WORKER_LOCAL", "STABLE_BDS", "INTEGRATION"],
        "restart-persistence": ["STABLE_BDS", "DESKTOP_CLIENT", "REALMS"],
        "multiplayer-ownership": ["STABLE_BDS", "DESKTOP_CLIENT", "REALMS", "SPLIT_SCREEN"],
        "chunk-lifecycle": ["STABLE_BDS", "REALMS"],
        "controller-usability": ["CONTROLLER", "PHYSICAL_PS4"],
        "representative-performance": ["STABLE_BDS", "DESKTOP_CLIENT", "PHYSICAL_PS4"],
        "endgame-completion": ["INTEGRATION", "DESKTOP_CLIENT", "CONTROLLER", "PHYSICAL_PS4"],
    }
    cases = []
    for case_id, outcome in QUALIFICATION_CASES:
        gates = [
            {
                "class": gate,
                "owner": owner_for_class[gate],
                "candidate_publication_prerequisite": gate == "WORKER_LOCAL",
            }
            for gate in routing[case_id]
        ]
        cases.append({"case_id": case_id, "observable_outcome": outcome, "gates": gates})
    _write_json(
        root / "sanitized-contracts" / "test-contracts" / "QUALIFICATION_CONTRACTS.json",
        {
            "schema_version": "1.0.0",
            "document_id": "sf-qualification-contracts-1.0.0",
            "owner_workload": "SF-T12",
            "private_evidence_included": False,
            "cases": cases,
            "policy": "Only WORKER_LOCAL is a candidate publication prerequisite; every later gate is owned externally.",
        },
    )
    _write_json(
        root / "analysis" / "qualification" / "JAVA_ORACLE_OBSERVATION_PLAN.json",
        {
            "schema_version": "1.0.0",
            "scope": "PRIVATE_EVIDENCE_ONLY",
            "runtime_state": "NOT_INSTALLED",
            "observations": [
                {
                    "case_id": case_id,
                    "observation": outcome,
                    "status": "BLOCKED_PENDING_DETERMINISTIC_JAVA_ORACLE_INSTALL",
                }
                for case_id, outcome in QUALIFICATION_CASES
            ],
        },
    )


def _write_rights(root: Path, inventory: dict[str, Any], rights: dict[str, Any]) -> tuple[int, int]:
    records = rights["records"]
    _write_json(
        root / "analysis" / "rights" / "MOD_RIGHTS_LEDGER.json",
        {
            "schema_version": "1.0.0",
            "default_policy": rights["default_policy"],
            "records": records,
            "warning": rights["warning"],
        },
    )
    pack_files = [
        row
        for row in inventory["files"]
        if "MOD_JAR" not in row["categories"] and "FORGE_RUNTIME" not in row["categories"]
    ]
    pack_owned = {
        "schema_version": "1.0.0",
        "scope": "PRIVATE_EVIDENCE_ONLY",
        "artifact_count": len(pack_files),
        "records": [
            {
                "side": row["side"],
                "evidence_path": row["path"],
                "sha256": row["sha256"],
                "byte_length": row["byte_length"],
                "categories": row["categories"],
                "rights_status": "PACK_OWNED_OR_DISTRIBUTED_EXPRESSION_UNREVIEWED",
                "production_copying_allowed": False,
                "functional_observation_allowed": True,
                "private_oracle_only": True,
            }
            for row in pack_files
        ],
    }
    _write_json(root / "analysis" / "rights" / "PACK_OWNED_CONTENT.json", pack_owned)
    unknown = {
        "schema_version": "1.0.0",
        "policy": "Unknown rights are a hard block on production copying, not on private functional observation.",
        "unknown_mod_record_count": len(records),
        "unknown_pack_artifact_count": len(pack_files),
        "blocks": [
            {
                "code": "MOD_RIGHTS_UNRESOLVED",
                "count": len(records),
                "effect": "NO_CODE_ASSET_OR_BRANDING_COPYING",
            },
            {
                "code": "PACK_EXPRESSION_RIGHTS_UNRESOLVED",
                "count": len(pack_files),
                "effect": "NO_CONFIGURATION_SCRIPT_ASSET_OR_PROSE_COPYING",
            },
            {
                "code": "PACK_BRANDING_NOT_AUTHORIZED",
                "count": 1,
                "effect": "ORIGINAL_PRODUCT_IDENTITY_REQUIRED",
            },
        ],
    }
    _write_json(root / "analysis" / "rights" / "UNKNOWN_OR_BLOCKED.json", unknown)
    _write_text(
        root / "sanitized-contracts" / "blocked" / "PROHIBITED_SOURCE_EXPRESSION.md",
        """# Prohibited source expression

Production packets and workers must not receive or reproduce private code, bytecode, configuration expression, scripts, artwork, models, audio, quest prose, branding, archive names, evidence hashes, or private paths.

Allowed authority is limited to validated functional contracts, observable outcomes, abstract interfaces, bounded performance requirements, and originality constraints. Unknown rights default to private observation only. A worker must stop with `RIGHTS_BOUNDARY_VIOLATION` if a required action would cross this boundary.
""",
    )
    return len(records), len(pack_files)


def _write_reports(
    root: Path,
    release_lock: dict[str, Any],
    summary: dict[str, Any],
    inventory: dict[str, Any],
    mod_inventory: dict[str, Any],
    assets: dict[str, Any],
    catalog: dict[str, Any],
    rights_counts: tuple[int, int],
) -> None:
    server_rows = [row for row in inventory["files"] if row["side"] == "server"]
    server_categories = Counter(category for row in server_rows for category in row["categories"])
    asset_counts = Counter()
    for row in assets["families"]:
        asset_counts[row["family"]] += row["member_count"]
    graph = catalog["dependency_graph"]
    report = f"""# SkyFactory 4 factory decomposition report

Status: **FACTORY_READY_WITH_BLOCKERS**

## Frozen authority

Both exact official 4.2.4 authorities are acquired, hash-verified, ZIP-verified, and frozen read-only. The server authority is `{release_lock['authorities'][0]['sha256']}` ({release_lock['authorities'][0]['byte_length']} bytes); the client authority is `{release_lock['authorities'][1]['sha256']}` ({release_lock['authorities'][1]['byte_length']} bytes). Immutable raw files remain beneath `authority/downloads/`; extracted private oracle trees remain beneath `oracle/`.

## Inventory

- {summary['file_count']} extracted files across both authorities.
- {mod_inventory['server_mod_jar_count']} server mod archives and {summary['client_manifest_row_count']} exact client-manifest entries.
- {server_categories.get('CONFIG', 0)} server-side configuration-classified files and {server_categories.get('SCRIPT', 0)} server-side script-classified files.
- {summary['unknown_mod_metadata_count']} mod metadata rows and {summary['unknown_distribution_count']} distribution records remain unresolved.
- {summary['anomaly_count']} nested archive anomalies are recorded; nested archives were not recursively opened.

## Workload topology

The approved topology is SF-T1 through SF-T12. Its only roots are {', '.join(graph['root_workloads'])}; its deterministic order is {' -> '.join(graph['topological_order'])}. SF-T10 defines original asset requirements and SF-T11 defines shared runtime interfaces. SF-T1 through SF-T9 consume those contracts in product-progression order. SF-T12 consumes the completed progression path and test hooks.

No workload is activated by this intake. When production is separately authorized, SF-T10 and SF-T11 can begin independently. Every other workload must wait for its declared graph inputs; SF-T12 waits for SF-T9 plus shared test hooks and interface contracts.

## Shared runtime and progression bottlenecks

Critical shared interfaces are persistent state, deterministic identifiers, recipe registry, bounded scheduler, power accounting, transfer accounting, ownership, controller-first interfaces, advancement state, migrations, chunk lifecycle, multiplayer synchronization, telemetry, and test hooks. SF-T9 is the progression dependency owner; SF-T11 is the runtime dependency owner. The Java recipe and progression graphs currently preserve complete coarse evidence locations but do not claim semantic reachability, cycles, or unobtainable nodes without deterministic runtime observations.

## Asset estimates and rights

Private evidence records {sum(asset_counts.values())} asset-family members across {len(asset_counts)} detected families. Production receives {len(ASSET_CONTRACTS)} abstract original-expression contracts with bounded geometry, texture, interaction, animation, readability, and controller requirements—not source assets. Rights review is unresolved for {rights_counts[0]} mod metadata records and {rights_counts[1]} pack-distributed loose artifacts. The pack-level All Rights Reserved notice, unknown per-component asset scope, and unauthorized branding are hard blocks on copying.

## Qualification boundary

Worker-local tests are the only candidate-publication prerequisite. T1 mechanical preflight, Stable BDS, private audit, shared-adapter repair, integration, desktop client, Realms, controller, split-screen, and physical PS4 gates remain assigned to their designated owners. Physical-console verification is not claimed.

## Remaining blockers

The supplied server archive contains an installer rather than an installed deterministic Java oracle, so source-side runtime observations remain blocked. Semantic recipe/progression reachability, unknown rights, distinctive branding, and client/controller/console behaviors remain unsuitable for autonomous reconstruction. These blockers do not prevent clean-room task planning from the validated abstract contracts; they do prevent source copying and any claim of full behavioral parity.
"""
    _write_text(root / "reports" / "SKYFACTORY4_FACTORY_DECOMPOSITION_REPORT.md", report)
    blockers = """# Open questions and blockers

1. `JAVA_ORACLE_RUNTIME_NOT_INSTALLED` — install and hash-lock the exact Forge 1.12.2 runtime before source-side observations; do not run the installer during intake.
2. `SEMANTIC_REACHABILITY_UNPROVEN` — recipe and progression evidence is complete at the file/member-location level, but runtime cycles, unobtainable nodes, optional branches, and machine compatibility require deterministic observations.
3. `RIGHTS_UNKNOWN_DEFAULT_PRIVATE` — mod, configuration, script, artwork, sound, branding, and pack-expression permissions require rights review; none may cross into production by default.
4. `NESTED_ARCHIVE_ANOMALIES` — one mod archive has duplicate member names and another has a portable-name collision; keep both opaque and use the recorded evidence.
5. `CLIENT_AND_CONSOLE_GATES_PENDING` — desktop client, Realms, controller, split-screen, and physical PS4 validation require their later gate owners and environments.
6. `NO_PRODUCTION_AUTHORIZATION` — this intake does not activate workers, create candidates, enqueue private audits, or launch translation.
"""
    _write_text(root / "reports" / "OPEN_QUESTIONS_AND_BLOCKERS.md", blockers)


def _write_manifest(root: Path, release_lock: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    included_roots = [root / "authority", root / "analysis", root / "sanitized-contracts", root / "reports"]
    fixed_files = [root / "README.md", root / "SOURCE_AUTHORITY_REPORT.md"]
    files: list[Path] = []
    for base in included_roots:
        files.extend(path for path in base.rglob("*") if path.is_file() and path.name != "FACTORY_INTAKE_MANIFEST.json")
    files.extend(path for path in fixed_files if path.is_file())
    records = [
        {
            "path": path.relative_to(root).as_posix(),
            "byte_length": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in sorted(set(files), key=lambda item: item.relative_to(root).as_posix())
    ]
    manifest = {
        "schema_version": "factory-intake-manifest-v1",
        "intake_id": "skyfactory4-4.2.4-intake",
        "state": "FACTORY_READY_WITH_BLOCKERS",
        "production_activated": False,
        "immutable_authorities": [
            {
                "role": authority["role"],
                "path": f"authority/downloads/{authority['filename']}",
                "byte_length": authority["byte_length"],
                "sha256": authority["sha256"],
            }
            for authority in release_lock["authorities"]
        ],
        "workload_ids": [packet["workload_id"] for packet in catalog["workloads"]],
        "workload_roots": catalog["dependency_graph"]["root_workloads"],
        "artifact_records": records,
        "self_hash_excluded": True,
    }
    path = root / "FACTORY_INTAKE_MANIFEST.json"
    _write_json(path, manifest)
    return manifest


def build(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    private = root / "analysis" / "private-evidence"
    release_lock = _load(root / "authority" / "release-lock.json")
    summary = _load(private / "EVIDENCE_ANALYSIS_SUMMARY.json")
    inventory = _load(private / "FULL_FILE_INVENTORY.json")
    mod_inventory = _load(private / "MOD_INVENTORY.json")
    assets = _load(private / "ASSET_FAMILY_INVENTORY.json")
    rights = _load(private / "RIGHTS_LEDGER.json")
    _copy_evidence_deliverables(root, private)
    catalog = _write_workloads(root)
    _write_runtime_and_assets(root, catalog)
    _write_qualification(root)
    rights_counts = _write_rights(root, inventory, rights)
    _write_reports(root, release_lock, summary, inventory, mod_inventory, assets, catalog, rights_counts)
    manifest = _write_manifest(root, release_lock, catalog)
    return {
        "ok": True,
        "state": manifest["state"],
        "artifact_record_count": len(manifest["artifact_records"]),
        "workload_count": len(manifest["workload_ids"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intake-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.intake_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
