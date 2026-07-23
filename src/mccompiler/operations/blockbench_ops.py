from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping

from mccompiler.blockbench_assets import (
    AssetContractError,
    canonical_bbmodel_hash,
    canonical_json,
    sha256_file,
    validate_animation_contract,
    validate_authoring_parameters,
    validate_geometry,
    validate_semantic_coordinates,
)
from mccompiler.operations.envelope import OperationError
from mccompiler.project.store import ProjectError, ProjectStore


HandlerResult = tuple[Any, ProjectStore, list[dict[str, Any]]]


def _artifact(store: ProjectStore, path: Path, kind: str) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved != store.root and store.root not in resolved.parents:
        raise ProjectError("INVALID_PATH", f"Asset artifact escapes project: {path}")
    row: dict[str, Any] = {"path": resolved.relative_to(store.root).as_posix(), "kind": kind}
    if resolved.is_file():
        row.update({"sha256": sha256_file(resolved), "size": resolved.stat().st_size})
    return row


def _safe_source(value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise AssetContractError("Every source_files entry must be a non-empty path")
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise AssetContractError(f"Authored source file does not exist: {path}")
    return path


def _replace_tree(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    incoming = destination.parent / f".{destination.name}.incoming"
    previous = destination.parent / f".{destination.name}.previous"
    if incoming.exists():
        shutil.rmtree(incoming)
    if previous.exists():
        shutil.rmtree(previous)
    shutil.copytree(source, incoming)
    if destination.exists():
        os.replace(destination, previous)
    try:
        os.replace(incoming, destination)
    except BaseException:
        if previous.exists():
            os.replace(previous, destination)
        raise
    if previous.exists():
        shutil.rmtree(previous)


def author_blockbench_asset(
    store: ProjectStore,
    parameters: dict[str, Any],
    expected_revision: int | None = None,
) -> HandlerResult:
    source_revision = store.revision
    if expected_revision is not None and expected_revision != source_revision:
        raise ProjectError("REVISION_CONFLICT", f"Expected project revision {expected_revision}, found {source_revision}")
    try:
        validate_authoring_parameters(parameters)
        source_files = parameters["source_files"]
        if not isinstance(source_files, Mapping):
            raise AssetContractError("source_files must be an object")
        required_files = ("bbmodel", "texture", "geometry", "animations", "animation_controller")
        missing_files = [name for name in required_files if name not in source_files]
        if missing_files:
            raise AssetContractError(f"Missing authored source files: {', '.join(missing_files)}")
        sources = {name: _safe_source(value) for name, value in source_files.items()}
        model = json.loads(sources["bbmodel"].read_text(encoding="utf-8"))
        geometry = json.loads(sources["geometry"].read_text(encoding="utf-8"))
        animations = json.loads(sources["animations"].read_text(encoding="utf-8"))
        controller = json.loads(sources["animation_controller"].read_text(encoding="utf-8"))
        manifest = parameters["asset_manifest"]
        if not isinstance(model, Mapping) or not isinstance(manifest, Mapping):
            raise AssetContractError("bbmodel and asset_manifest must be objects")
        bone_contract = parameters["bone_contract"]
        locator_contract = parameters["locator_contract"]
        animation_contract = parameters["animation_contract"]
        texture_budget = parameters["texture_budget"]
        if not all(isinstance(row, Mapping) for row in (bone_contract, locator_contract, animation_contract, texture_budget)):
            raise AssetContractError("Bone, locator, animation, and texture contracts must be objects")
        geometry_result = validate_geometry(
            geometry,
            namespace=str(manifest.get("namespace")),
            required_bones=[str(row) for row in bone_contract.get("required", [])],
            required_locators=[str(row) for row in locator_contract.get("required", [])],
            texture_size=(int(texture_budget.get("width", 0)), int(texture_budget.get("height", 0))),
        )
        animation_result = validate_animation_contract(
            animations,
            controller,
            required_clips=[str(row) for row in animation_contract.get("required_clips", [])],
            required_states=[str(row) for row in animation_contract.get("required_states", [])],
            bones=geometry_result["bones"],
        )
        coordinate_result = validate_semantic_coordinates(geometry)
        repair_history = parameters.get("repair_history", [])
        if not isinstance(repair_history, list) or len(repair_history) > 5:
            raise AssetContractError("repair_history must contain no more than five revisions")
    except (AssetContractError, json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
        raise OperationError(
            "AUTONOMOUS_AUTHORING_FAILED",
            str(exc),
            details={"status": "AUTONOMOUS_AUTHORING_FAILED", "mutated": False, "success_implied": False},
        ) from exc

    asset_id = str(parameters["asset_id"])
    safe_id = asset_id.replace(":", "__").replace("/", "_")
    with tempfile.TemporaryDirectory(prefix="mccompiler-blockbench-") as temporary:
        stage = Path(temporary) / safe_id
        source_dir, export_dir, report_dir = stage / "source", stage / "exports", stage / "reports"
        source_dir.mkdir(parents=True)
        export_dir.mkdir(parents=True)
        report_dir.mkdir(parents=True)
        shutil.copyfile(sources["bbmodel"], source_dir / f"{safe_id}.bbmodel")
        shutil.copyfile(sources["texture"], source_dir / Path(sources["texture"]).name)
        export_names = {
            "geometry": f"{safe_id}.geo.json",
            "animations": f"{safe_id}.animation.json",
            "animation_controller": f"{safe_id}.animation_controllers.json",
        }
        for key, filename in export_names.items():
            shutil.copyfile(sources[key], export_dir / filename)
        for key, source in sources.items():
            if key not in {"bbmodel", "texture", *export_names}:
                shutil.copyfile(source, export_dir / source.name)
        content_hashes = {
            key: sha256_file(path)
            for key, path in sorted(sources.items())
        }
        quality = parameters.get("quality_report")
        if not isinstance(quality, Mapping) or quality.get("disposition") != "PASSED":
            raise OperationError(
                "AUTONOMOUS_AUTHORING_FAILED",
                "A passing machine visual-quality report is required",
                details={"status": "AUTONOMOUS_AUTHORING_FAILED", "mutated": False, "success_implied": False},
            )
        authoring_report = {
            "schema_version": "1.0.0",
            "operation": "author_blockbench_asset",
            "status": "QUALIFIED",
            "asset_id": asset_id,
            "deterministic_seed": parameters["deterministic_seed"],
            "blockbench_version": parameters["blockbench_version"],
            "exporter_version": parameters["exporter_version"],
            "native_roundtrip": parameters["native_roundtrip"],
            "semantic_source_hash": canonical_bbmodel_hash(model),
            "content_hashes": content_hashes,
            "geometry": geometry_result,
            "animations": animation_result,
            "coordinate_semantics": coordinate_result,
            "repair_history": repair_history,
            "claims": {"ps4_verified": False, "marketplace_approved": False},
        }
        (report_dir / "authoring-report.json").write_bytes(canonical_json(authoring_report))
        (report_dir / "visual-quality-report.json").write_bytes(canonical_json(quality))
        (report_dir / "asset-manifest.json").write_bytes(canonical_json(manifest))
        if store.revision != source_revision:
            raise ProjectError("REVISION_CONFLICT", f"Expected project revision {source_revision}, found {store.revision}")
        destination = store.resolve(f"assets/blockbench/{safe_id}")
        _replace_tree(stage, destination)

    registry = store.read("assets/registry.json", {"schema_version": "1.0.0", "assets": []})
    if not isinstance(registry, dict) or not isinstance(registry.get("assets"), list):
        raise ProjectError("INVALID_PROJECT_DOCUMENT", "assets/registry.json must contain an assets array")
    assets = [row for row in registry["assets"] if not (isinstance(row, dict) and row.get("asset_id") == asset_id)]
    relative = destination.relative_to(store.root).as_posix()
    assets.append({
        "asset_id": asset_id,
        "status": "QUALIFIED",
        "rights_status": parameters["rights_policy"]["status"],
        "root": relative,
        "semantic_source_hash": authoring_report["semantic_source_hash"],
        "content_hashes": content_hashes,
        "bindings": parameters.get("bindings", []),
        "physical_ps4": "PENDING",
        "marketplace": "NOT_SUBMITTED",
    })
    artifacts = [
        _artifact(store, destination / "source" / f"{safe_id}.bbmodel", "blockbench_source"),
        _artifact(store, destination / "exports" / export_names["geometry"], "bedrock_geometry"),
        _artifact(store, destination / "exports" / export_names["animations"], "bedrock_animations"),
        _artifact(store, destination / "reports/authoring-report.json", "authoring_report"),
        _artifact(store, destination / "reports/visual-quality-report.json", "visual_quality_report"),
    ]
    revision = store.commit(
        {
            "assets/registry.json": {"schema_version": "1.0.0", "assets": sorted(assets, key=lambda row: str(row.get("asset_id")))},
            "reports/generation/author_blockbench_asset.json": {
                "schema_version": "1.0.0",
                "source_revision": source_revision,
                "asset_id": asset_id,
                "status": "QUALIFIED",
                "artifacts": artifacts,
                "consumer_exports_deterministic": True,
            },
        },
        expected_revision=source_revision,
    )
    return {
        "status": "QUALIFIED",
        "revision": revision,
        "asset_id": asset_id,
        "final_qualification_disposition": "MARKETPLACE_CANDIDATE_PS4_PENDING",
        "content_hashes": content_hashes,
        "repair_history": repair_history,
    }, store, artifacts
