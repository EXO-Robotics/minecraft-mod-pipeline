from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, NoReturn

from mccompiler.api_catalog import ApiCatalog
from mccompiler.creator_tools import invoke_creator_tools, load_creator_tools_lock, load_creator_tools_policy
from mccompiler.marketplace import evaluate_marketplace_candidate as evaluate_candidate
from mccompiler.performance import audit_archive_performance, audit_static_performance
from mccompiler.project.store import ProjectStore
from mccompiler.rights import evaluate_marketplace_rights
from mccompiler.runtime.evidence import EvidenceExpectation, validate_runtime_evidence
from mccompiler.runtime.bds import BDSDiagnosticError, BDSRunRequest, run_bds_diagnostic
from mccompiler.targets import get_target
from mccompiler.validate import validate_output

from .envelope import OperationError


HandlerResult = tuple[Any, ProjectStore, list[dict[str, Any]]]


def _unavailable(store: ProjectStore, operation: str, blocker: str) -> NoReturn:
    raise OperationError(
        "NOT_AVAILABLE",
        f"{operation} is not available from current project artifacts",
        details={
            "status": "NOT_AVAILABLE", "operation": operation, "category": "validation",
            "blocker": blocker, "project_revision": store.revision,
            "mutated": False, "success_implied": False,
        },
    )


def _relative(store: ProjectStore, value: Any, *, parameter: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise OperationError("INVALID_PARAMETERS", f"{parameter} must be a non-empty project-relative path")
    return store.resolve(value)


def _first_existing(store: ProjectStore, parameters: Mapping[str, Any], parameter: str, candidates: tuple[str, ...]) -> Path | None:
    supplied = parameters.get(parameter)
    if supplied is not None:
        path = _relative(store, supplied, parameter=parameter)
        return path if path.exists() else None
    return next((store.resolve(candidate) for candidate in candidates if store.resolve(candidate).exists()), None)


def _build_root(store: ProjectStore, parameters: Mapping[str, Any]) -> Path | None:
    supplied = parameters.get("build_root")
    if supplied is not None:
        path = _relative(store, supplied, parameter="build_root")
        return path if path.is_dir() else None
    for candidate in ("bedrock", "dist/marketplace-candidate", "build", "out"):
        root = store.resolve(candidate)
        markers = (root / "conversion-manifest.json", root / "behavior_pack/manifest.json", root / "converted-mod.mcaddon")
        if root.is_dir() and any(marker.exists() for marker in markers):
            return root
    return None


def _validation(store: ProjectStore, parameters: Mapping[str, Any], operation: str) -> dict[str, Any]:
    root = _build_root(store, parameters)
    if root is None:
        _unavailable(store, operation, "No generated build root exists; provide build_root or generate the pack first")
    assert root is not None
    plan = store.read("reports/backend/conversion-plan.json", store.read("reports/conversion-plan.json"))
    return validate_output(root, plan if isinstance(plan, dict) else None, marketplace=bool(parameters.get("marketplace", False)))


def validate_api_symbols(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    report_path = _first_existing(store, parameters, "api_usage", (
        "reports/backend/api-usage.json", "dist/marketplace-candidate/reports/api-usage.json", "reports/api-usage.json",
    ))
    if report_path is None or not report_path.is_file():
        _unavailable(store, "validate_api_symbols", "No persisted reports/api-usage.json artifact exists")
    assert report_path is not None
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OperationError("INVALID_ARTIFACT", f"Cannot read API usage report: {exc}") from exc
    requirements: list[tuple[str, str]] = []
    rows = report.get("symbols", report.get("symbol_evidence", [])) if isinstance(report, dict) else []
    errors: list[str] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, Mapping) or not isinstance(row.get("module"), str) or not isinstance(row.get("symbol"), str):
            errors.append("API usage symbol entries require module and symbol")
        else:
            requirements.append((str(row["module"]), str(row["symbol"])))
    try:
        versions, evidence = ApiCatalog.load_default().resolve_versions(requirements, marketplace=True)
    except ValueError as exc:
        errors.append(str(exc))
        versions, evidence = {}, []
    uncatalogued = report.get("uncatalogued_symbols", []) if isinstance(report, dict) else []
    if uncatalogued:
        errors.append(f"API usage report contains {len(uncatalogued)} uncatalogued symbols")
    if report.get("complete") is not True:
        errors.append("API usage report does not claim complete symbol coverage")
    result = {"valid": not errors, "errors": errors, "resolved_modules": versions, "symbols": evidence, "artifact": str(report_path)}
    return result, store, [{"path": str(report_path.relative_to(store.root)), "kind": "api-usage"}]


def validate_marketplace_profile(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    configured = str(store.manifest.get("target_profile") or "")
    errors: list[str] = []
    try:
        profile = get_target(configured)
    except ValueError as exc:
        errors.append(str(exc))
        profile = get_target(None)
    if configured != "MARKETPLACE_ADDON_STABLE":
        errors.append(f"Marketplace validation requires MARKETPLACE_ADDON_STABLE, got {configured or '<missing>'}")
    static = _validation(store, {**parameters, "marketplace": True}, "validate_marketplace_profile") if _build_root(store, parameters) else None
    if static is not None:
        errors.extend(static.get("errors", []))
    return {
        "valid": not errors, "errors": errors, "target_profile": configured,
        "profile": profile.__dict__, "static_validation": static,
        "marketplace_approval_implied": False,
    }, store, []


def validate_rights(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    manifest = store.read(str(parameters.get("manifest", "rights/rights-manifest.yaml")))
    if not isinstance(manifest, dict):
        _unavailable(store, "validate_rights", "No readable persisted rights manifest exists")
    # Early project layouts called this array content; normalize it without weakening review rules.
    if "records" not in manifest and isinstance(manifest.get("content"), list):
        manifest = {**manifest, "records": manifest["content"]}
    result = evaluate_marketplace_rights(manifest)
    return result, store, [{"path": str(parameters.get("manifest", "rights/rights-manifest.yaml")), "kind": "rights-manifest"}]


def validate_static(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    result = _validation(store, parameters, "validate_static")
    return result, store, []


def validate_scripts(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    full = _validation(store, parameters, "validate_scripts")
    checks = [row for row in full["layers"]["static"].get("checks", []) if row.get("name") in {"script-syntax-and-imports", "target-profile-and-api-usage"}]
    errors = [error for error in full.get("errors", []) if any(token in error.lower() for token in ("script", "api", "module", "import"))]
    return {"valid": not errors and all(row.get("passed") for row in checks), "errors": errors, "checks": checks}, store, []


def validate_assets(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    full = _validation(store, parameters, "validate_assets")
    asset_names = {"json-parse", "identifier-uniqueness", "content-references", "resource-pack-references", "manifest-integrity"}
    checks = [row for row in full["layers"]["static"].get("checks", []) if row.get("name") in asset_names]
    errors = [error for error in full.get("errors", []) if any(token in error.lower() for token in ("texture", "geometry", "animation", "sound", "resource", "manifest", "identifier", "json"))]
    return {"valid": not errors and all(row.get("passed") for row in checks), "errors": errors, "checks": checks}, store, []


def validate_performance(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    exceptions = store.read("decisions/performance-exceptions.json", [])
    archive = _first_existing(store, parameters, "archive", (
        "dist/marketplace-candidate/converted-mod.mcaddon", "converted-mod.mcaddon",
    ))
    if archive is not None and archive.is_file():
        result = audit_archive_performance(archive, approved_exceptions=exceptions if isinstance(exceptions, list) else None)
    else:
        root = _build_root(store, parameters)
        if root is None:
            _unavailable(store, "validate_performance", "No generated pack or archive exists for static performance validation")
        assert root is not None
        result = audit_static_performance(root, approved_exceptions=exceptions if isinstance(exceptions, list) else None)
    result["runtime_measurement_status"] = "NOT_AVAILABLE"
    result["runtime_performance_claimed"] = False
    return result, store, []


def install_test_pack(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    _unavailable(store, "install_test_pack", "No configured installer adapter exists; external Minecraft installations are not mutated")
    raise AssertionError("unreachable")


def start_test_runtime(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    if parameters.get("adapter") != "BDS_DOCKER" or parameters.get("execute") is not True:
        _unavailable(store, "start_test_runtime", "Set adapter=BDS_DOCKER and execute=true to authorize an isolated project-scoped diagnostic run")
    world = _first_existing(store, parameters, "world", (
        "dist/test-world/converted-test-world.mcworld", "bedrock/converted-test-world.mcworld",
    ))
    if world is None or not world.is_file():
        _unavailable(store, "start_test_runtime", "Generate a .mcworld or provide a project-relative world path")
    image = parameters.get("image")
    if not isinstance(image, str) or not image.strip():
        raise OperationError("INVALID_PARAMETERS", "image must identify the BDS Docker image")
    mutable_image = "@sha256:" not in image
    if mutable_image and parameters.get("allow_mutable_image") is not True:
        raise OperationError("MUTABLE_RUNTIME_IMAGE", "Use an image digest or explicitly set allow_mutable_image=true for diagnostic-only evidence")
    network_mode = str(parameters.get("network_mode", "none"))
    if network_mode == "bridge" and parameters.get("allow_bootstrap_network") is not True:
        raise OperationError("NETWORK_NOT_AUTHORIZED", "Set allow_bootstrap_network=true to permit the pinned BDS wrapper to download the requested server version")
    if network_mode not in {"none", "bridge"}:
        raise OperationError("INVALID_PARAMETERS", "network_mode must be none or bridge")
    run_id = f"run-{store.revision}-{uuid.uuid4().hex[:12]}"
    run_root = store.resolve(f"runtime/bds/{run_id}")
    try:
        result = run_bds_diagnostic(BDSRunRequest(
            image=image,
            mcworld=world,
            run_root=run_root,
            timeout_seconds=int(parameters.get("timeout_seconds", 120)),
            boot_grace_seconds=int(parameters.get("boot_grace_seconds", 15)),
            docker_executable=str(parameters.get("docker_executable", "docker")),
            network_mode=network_mode,
            bds_version=str(parameters["bds_version"]) if parameters.get("bds_version") else None,
            restart_count=int(parameters.get("restart_count", 1)),
        ))
    except (BDSDiagnosticError, OSError, ValueError) as exc:
        raise OperationError("BDS_DIAGNOSTIC_FAILED", str(exc), details={"run_id": run_id, "success_implied": False}) from exc
    result["runtime"]["mutable_image_allowed"] = mutable_image
    result["project"] = {"revision_before_run": store.revision, "target_profile": store.manifest.get("target_profile")}
    store.write(f"runtime/bds/{run_id}/result.json", result)
    revision = store.commit({"reports/bds-diagnostic-validation.json": result}, expected_revision=expected_revision)
    return {"run": result, "revision": revision}, store, [
        {"path": str(world.relative_to(store.root)), "kind": "mcworld"},
        {"path": f"runtime/bds/{run_id}/content.log", "kind": "bds-content-log"},
        {"path": f"runtime/bds/{run_id}/result.json", "kind": "bds-run-result"},
        {"path": "reports/bds-diagnostic-validation.json", "kind": "bds-diagnostic-validation"},
    ]


def run_behavior_test(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    _unavailable(store, "run_behavior_test", "This operation cannot start a runtime; ingest independently produced runtime evidence")
    raise AssertionError("unreachable")


def run_multiplayer_test(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    _unavailable(store, "run_multiplayer_test", "No configured multiplayer runtime and clients exist")
    raise AssertionError("unreachable")


def _runtime_validation(store: ProjectStore, parameters: Mapping[str, Any], operation: str) -> tuple[dict[str, Any], Path]:
    evidence_path = _first_existing(store, parameters, "evidence", ("runtime/runtime-evidence.json", "reports/runtime-evidence.json"))
    if evidence_path is None or not evidence_path.is_file():
        _unavailable(store, operation, "No persisted runtime evidence exists")
    assert evidence_path is not None
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    identity = evidence if isinstance(evidence, dict) else {}
    try:
        expectation = EvidenceExpectation(
            pack_hash=str(identity["pack_hash"]), build_hash=str(identity["build_hash"]),
            runtime_id=str(identity["runtime_id"]), world_id=str(identity["world_id"]), test_id=str(identity["test_id"]),
            now=datetime.now(timezone.utc), max_age_seconds=int(parameters.get("max_age_seconds", 86400)),
            profile=str(store.manifest.get("target_profile") or "MARKETPLACE_ADDON_STABLE"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise OperationError("INVALID_ARTIFACT", f"Runtime evidence identity is invalid: {exc}") from exc
    log_path = _first_existing(store, parameters, "content_log", ("runtime/content.log", "runtime/content-log.txt"))
    raw_log = log_path.read_bytes() if log_path and log_path.is_file() else None
    return validate_runtime_evidence(identity, expectation, raw_log=raw_log), evidence_path


def verify_persistence(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    result, path = _runtime_validation(store, parameters, "verify_persistence")
    persistence_errors = [error for error in result["errors"] if any(word in error for word in ("persistence", "migration", "reconnect"))]
    return {**result, "persistence_valid": result["valid"] and not persistence_errors, "persistence_errors": persistence_errors}, store, [{"path": str(path.relative_to(store.root)), "kind": "runtime-evidence"}]


def inspect_content_log(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    path = _first_existing(store, parameters, "content_log", ("runtime/content.log", "runtime/content-log.txt"))
    if path is None or not path.is_file():
        _unavailable(store, "inspect_content_log", "No runtime content log has been ingested")
    assert path is not None
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    critical = [line for line in lines if any(token in line.lower() for token in ("error", "exception", "failed to load", "syntaxerror"))]
    return {"path": str(path), "sha256": hashlib.sha256(text.encode()).hexdigest(), "line_count": len(lines), "critical_lines": critical, "clean": not critical}, store, [{"path": str(path.relative_to(store.root)), "kind": "content-log"}]


def compare_expected_behavior(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    expected_path = _first_existing(store, parameters, "expected", ("tests/expected-behavior.json", "tests/behavior-plan.json"))
    actual_path = _first_existing(store, parameters, "actual", ("runtime/behavior-results.json", "runtime/runtime-evidence.json"))
    if expected_path is None or actual_path is None or not expected_path.is_file() or not actual_path.is_file():
        _unavailable(store, "compare_expected_behavior", "Persist both expected behavior and observed runtime-result artifacts")
    assert expected_path is not None and actual_path is not None
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    actual = json.loads(actual_path.read_text(encoding="utf-8"))
    expected_rows = expected.get("behaviors", expected.get("checks", [])) if isinstance(expected, dict) else []
    actual_rows = actual.get("behaviors", actual.get("checks", [])) if isinstance(actual, dict) else []
    def indexed(rows: Any) -> dict[str, Mapping[str, Any]]:
        return {str(row.get("id", row.get("check_id"))): row for row in rows if isinstance(row, Mapping) and row.get("id", row.get("check_id"))}
    wanted, observed = indexed(expected_rows), indexed(actual_rows)
    missing = sorted(set(wanted) - set(observed))
    failed = sorted(key for key in wanted.keys() & observed.keys() if observed[key].get("passed", observed[key].get("status") == "PASSED") is not True)
    return {
        "matches": not missing and not failed, "expected_count": len(wanted), "observed_count": len(observed),
        "missing": missing, "failed": failed, "unexpected": sorted(set(observed) - set(wanted)),
        "expected_artifact": str(expected_path), "actual_artifact": str(actual_path),
        "runtime_execution_implied": False,
    }, store, [
        {"path": str(expected_path.relative_to(store.root)), "kind": "expected-behavior"},
        {"path": str(actual_path.relative_to(store.root)), "kind": "observed-behavior"},
    ]


def validate_creator_tools(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    executable_value = parameters.get("executable")
    if not isinstance(executable_value, str) or not executable_value.strip():
        _unavailable(store, "validate_creator_tools", "Provide the pinned official Creator Tools executable path")
    executable = Path(executable_value).expanduser().resolve()
    if not executable.is_file():
        _unavailable(store, "validate_creator_tools", f"Creator Tools executable does not exist: {executable}")
    archive = _first_existing(store, parameters, "archive", (
        "dist/marketplace-candidate/converted-mod.mcaddon", "bedrock/converted-mod.mcaddon",
    ))
    if archive is None or not archive.is_file():
        _unavailable(store, "validate_creator_tools", "Generate and package the .mcaddon first")
    assert archive is not None
    result = invoke_creator_tools(executable, archive, lock=load_creator_tools_lock(), policy=load_creator_tools_policy())
    document = {**result, "artifact": {"path": str(archive.relative_to(store.root)), "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "bytes": archive.stat().st_size}}
    revision = store.commit({"reports/creator-tools-validation.json": document}, expected_revision=expected_revision)
    return {"validation": document, "revision": revision}, store, [
        {"path": str(archive.relative_to(store.root)), "kind": "mcaddon"},
        {"path": "reports/creator-tools-validation.json", "kind": "creator-tools-validation"},
    ]


def evaluate_marketplace_candidate(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    build_root = _build_root(store, parameters)
    if build_root is None:
        _unavailable(store, "evaluate_marketplace_candidate", "Generate the pack and archive first")
    assert build_root is not None
    plan = store.read("reports/backend/conversion-plan.json")
    if not isinstance(plan, dict):
        _unavailable(store, "evaluate_marketplace_candidate", "No persisted conversion plan exists")
    rights = store.read("rights/rights-manifest.yaml", {})
    if isinstance(rights, dict) and "records" not in rights:
        rights = {**rights, "records": rights.get("content", [])}
    fidelity = store.read("reports/fidelity.json", {"mechanics": []})
    quality = fidelity.get("mechanics", []) if isinstance(fidelity, dict) else []
    creator = store.read("reports/creator-tools-validation.json")
    report = evaluate_candidate(
        build_root,
        plan=plan,
        rights_manifest=rights if isinstance(rights, dict) else {},
        quality_records=[row for row in quality if isinstance(row, dict)],
        creator_tools_report=creator if isinstance(creator, dict) else None,
        performance_exceptions=store.read("decisions/performance-exceptions.json", []),
    )
    revision = store.commit({"dist/reports/marketplace-candidate-report.json": report}, expected_revision=expected_revision)
    return {"candidate": report, "revision": revision}, store, [{"path": "dist/reports/marketplace-candidate-report.json", "kind": "marketplace-candidate-evaluation"}]
