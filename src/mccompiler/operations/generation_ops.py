from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Callable

from mccompiler.api_catalog import ApiCatalog
from mccompiler.bedrock import ARCHIVE_NAME, _zip_deterministic, compile_bedrock
from mccompiler.operations.envelope import OperationError
from mccompiler.overrides import apply_overrides
from mccompiler.planner import plan_conversion
from mccompiler.project.store import ProjectError, ProjectStore
from mccompiler.world import generate_test_world


HandlerResult = tuple[Any, ProjectStore, list[dict[str, Any]]]
_FEATURE_KINDS = {
    "generate_item": "item",
    "generate_block": "block",
    "generate_entity": "entity",
    "generate_recipe": "recipe",
    "generate_structure": "structure",
}
_DERIVED_RECORD_ROOT = "reports/generation"
_CUSTOM_ROOTS = ("scripts", "entities", "models", "assets")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact(store: ProjectStore, path: Path, kind: str) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved != store.root and store.root not in resolved.parents:
        raise ProjectError("INVALID_PATH", f"Generated artifact escapes project: {path}")
    row: dict[str, Any] = {"path": resolved.relative_to(store.root).as_posix(), "kind": kind}
    if resolved.is_file():
        row.update({"sha256": _sha256(resolved), "size": resolved.stat().st_size})
    return row


def _require_revision(store: ProjectStore, expected_revision: int | None) -> int:
    revision = store.revision
    if expected_revision is not None and expected_revision != revision:
        raise ProjectError("REVISION_CONFLICT", f"Expected project revision {expected_revision}, found {revision}")
    return revision


def _inputs(store: ProjectStore) -> tuple[dict[str, Any], dict[str, Any]]:
    source = store.read("analysis/modir.json")
    if not isinstance(source, dict):
        raise ProjectError("MISSING_MODIR", "Generate operations require analysis/modir.json")
    ir = copy.deepcopy(source)
    overrides = store.read("decisions/overrides.yaml", {"schema_version": "1.0.0", "overrides": []})
    if not isinstance(overrides, dict):
        raise ProjectError("INVALID_PROJECT_DOCUMENT", "decisions/overrides.yaml must be an object")
    try:
        apply_overrides(ir, overrides)
    except (KeyError, TypeError, ValueError) as exc:
        raise ProjectError("INVALID_OVERRIDE", str(exc)) from exc
    ir["target"] = {"profile": str(store.manifest.get("target_profile") or "MARKETPLACE_ADDON_STABLE")}
    plan = plan_conversion(ir)
    decisions = store.read("decisions/strategies.yaml", {"strategies": []}) or {"strategies": []}
    selected = {row.get("target"): row.get("strategy") for row in decisions.get("strategies", []) if isinstance(row, dict)}
    for feature in plan.get("features", []):
        if selected.get(feature.get("id")):
            feature["classification"] = selected[feature["id"]]
    return ir, plan


def _compile_staged(store: ProjectStore) -> tuple[tempfile.TemporaryDirectory[str], Path, dict[str, Any], dict[str, Any]]:
    ir, plan = _inputs(store)
    temporary = tempfile.TemporaryDirectory(prefix="mccompiler-generation-")
    stage = Path(temporary.name) / "build"
    try:
        compile_bedrock(ir, plan, stage)
        _merge_custom_implementations(store, stage)
    except BaseException:
        temporary.cleanup()
        raise
    return temporary, stage, ir, plan


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _decision_rows(store: ProjectStore, path: str, key: str) -> list[dict[str, Any]]:
    document = store.read(path, {"schema_version": "1.0.0", key: []})
    if not isinstance(document, dict) or not isinstance(document.get(key), list):
        raise ProjectError("INVALID_CUSTOM_METADATA", f"{path} must contain a {key} array")
    return [row for row in document[key] if isinstance(row, dict)]


def _safe_pack_destination(value: Any, *, prefix: str | None = None) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute() or ".." in Path(value).parts:
        raise ProjectError("INVALID_CUSTOM_MAPPING", f"Invalid custom Bedrock destination: {value!r}")
    destination = Path(value)
    if prefix is not None and (not destination.parts or destination.parts[0] != prefix):
        raise ProjectError("INVALID_CUSTOM_MAPPING", f"Custom destination must be under {prefix}/: {value}")
    if destination.as_posix() == "manifest.json":
        raise ProjectError("INVALID_CUSTOM_MAPPING", "Custom content cannot replace a pack manifest")
    return destination


def _custom_files(store: ProjectStore, kind: str) -> list[Path]:
    root = store.resolve(f"custom/{kind}")
    return sorted((path for path in root.rglob("*") if path.is_file()), key=lambda path: path.relative_to(store.root).as_posix())


def _merge_custom_implementations(store: ProjectStore, stage: Path) -> None:
    """Copy reviewed protected implementations into a disposable staged build.

    Protected source files are never changed. Every file must have an explicit
    handler or mapping, and every custom Script API symbol is folded into the
    normal API usage report before the consumer archive is rebuilt.
    """
    handlers = _decision_rows(store, "decisions/custom-handlers.json", "handlers")
    mappings = _decision_rows(store, "decisions/mappings.json", "mappings")
    integrations: list[dict[str, Any]] = []
    custom_requirements: list[tuple[str, str]] = []
    imports: list[str] = []

    handler_by_source: dict[str, dict[str, Any]] = {}
    for row in handlers:
        source = row.get("source_path") or row.get("path")
        if isinstance(source, str):
            if source in handler_by_source:
                raise ProjectError("DUPLICATE_CUSTOM_METADATA", f"Multiple custom handlers register {source}")
            handler_by_source[source] = row
    mapping_by_source: dict[str, dict[str, Any]] = {}
    for row in mappings:
        source = row.get("source_id")
        if isinstance(source, str) and source.startswith("custom/"):
            if source in mapping_by_source:
                raise ProjectError("DUPLICATE_CUSTOM_METADATA", f"Multiple custom mappings register {source}")
            mapping_by_source[source] = row

    for source in _custom_files(store, "scripts"):
        relative = source.relative_to(store.root).as_posix()
        handler = handler_by_source.get(relative)
        if handler is None or not isinstance(handler.get("behavior_id"), str):
            raise ProjectError("UNREGISTERED_CUSTOM_IMPLEMENTATION", f"Custom script requires a registered behavior handler: {relative}")
        destination = _safe_pack_destination(handler.get("destination"), prefix="scripts")
        if len(destination.parts) < 3 or destination.parts[1] != "custom":
            raise ProjectError("INVALID_CUSTOM_MAPPING", f"Custom scripts must stage under scripts/custom/: {destination}")
        symbols = handler.get("api_symbols")
        if not isinstance(symbols, list):
            raise ProjectError("MISSING_CUSTOM_API_METADATA", f"Custom handler must declare api_symbols (an empty array is allowed): {relative}")
        normalized_symbols: list[dict[str, str]] = []
        for symbol in symbols:
            if not isinstance(symbol, dict) or not isinstance(symbol.get("module"), str) or not isinstance(symbol.get("symbol"), str):
                raise ProjectError("INVALID_CUSTOM_API_METADATA", f"Invalid API symbol declaration for {relative}")
            pair = (symbol["module"], symbol["symbol"])
            custom_requirements.append(pair)
            normalized_symbols.append({"module": pair[0], "symbol": pair[1]})
        target = stage / "behavior_pack" / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        imports.append(f"import './{destination.relative_to('scripts').as_posix()}';")
        integrations.append({"kind": "script", "source": relative, "pack": "behavior", "destination": destination.as_posix(), "behavior_id": handler["behavior_id"], "api_symbols": normalized_symbols, "sha256": _sha256(source)})

    category_rules = {"entities": ("behavior", "entities"), "models": ("resource", "models"), "assets": (None, None)}
    for kind, (required_pack, prefix) in category_rules.items():
        for source in _custom_files(store, kind):
            relative = source.relative_to(store.root).as_posix()
            mapping = mapping_by_source.get(relative)
            if mapping is None:
                raise ProjectError("UNREGISTERED_CUSTOM_IMPLEMENTATION", f"Custom {kind} file requires a registered mapping: {relative}")
            pack = mapping.get("pack")
            if pack not in {"behavior", "resource"} or (required_pack is not None and pack != required_pack):
                raise ProjectError("INVALID_CUSTOM_MAPPING", f"Custom {kind} mapping has invalid pack {pack!r}: {relative}")
            destination = _safe_pack_destination(mapping.get("destination"), prefix=prefix)
            target = stage / ("behavior_pack" if pack == "behavior" else "resource_pack") / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            integrations.append({"kind": kind[:-1] if kind.endswith("s") else kind, "source": relative, "pack": pack, "destination": destination.as_posix(), "mapping_source_id": mapping["source_id"], "sha256": _sha256(source)})

    if not integrations:
        return

    api_path = stage / "reports/api-usage.json"
    api_report = json.loads(api_path.read_text(encoding="utf-8"))
    existing = [(str(row["module"]), str(row["symbol"])) for row in api_report.get("symbols", []) if isinstance(row, dict) and row.get("module") and row.get("symbol")]
    requirements = sorted(set(existing + custom_requirements))
    try:
        versions, evidence = ApiCatalog.load_default().resolve_versions(requirements, marketplace=True)
        uncatalogued: list[dict[str, str]] = []
    except ValueError:
        catalog = ApiCatalog.load_default()
        known = [pair for pair in requirements if pair in catalog.symbols]
        versions, evidence = catalog.resolve_versions(known, marketplace=True)
        uncatalogued = [{"module": module, "symbol": symbol} for module, symbol in requirements if (module, symbol) not in catalog.symbols]
    api_report.update({"complete": not uncatalogued, "resolved_modules": versions, "symbols": evidence, "uncatalogued_symbols": uncatalogued, "custom_integrations": [row for row in integrations if row["kind"] == "script"]})
    _write_json(api_path, api_report)

    if imports:
        main = stage / "behavior_pack/scripts/main.js"
        main.parent.mkdir(parents=True, exist_ok=True)
        current = main.read_text(encoding="utf-8") if main.exists() else ""
        main.write_text("\n".join(sorted(set(imports))) + "\n" + current, encoding="utf-8")
        manifest_path = stage / "behavior_pack/manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not any(module.get("type") == "script" for module in manifest.get("modules", []) if isinstance(module, dict)):
            header_uuid = str(manifest["header"]["uuid"])
            manifest.setdefault("modules", []).append({"type": "script", "language": "javascript", "entry": "scripts/main.js", "uuid": str(uuid.uuid5(uuid.UUID(header_uuid), "custom-script-module")), "version": [1, 0, 0]})
        dependencies = [row for row in manifest.get("dependencies", []) if not (isinstance(row, dict) and row.get("module_name") in versions)]
        dependencies.extend({"module_name": module, "version": version} for module, version in sorted(versions.items()))
        manifest["dependencies"] = dependencies
        _write_json(manifest_path, manifest)

    integration_report = {"schema_version": "1.0.0", "complete": True, "integrations": sorted(integrations, key=lambda row: (row["source"], row["destination"]))}
    _write_json(stage / "reports/custom-integrations.json", integration_report)
    conversion_manifest_path = stage / "conversion-manifest.json"
    conversion_manifest = json.loads(conversion_manifest_path.read_text(encoding="utf-8"))
    conversion_manifest["custom_integrations"] = integration_report["integrations"]
    _write_json(conversion_manifest_path, conversion_manifest)
    report_path = stage / "reports/conversion-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["custom_integrations"] = integration_report["integrations"]
    report["generated_files"] = sorted(path.relative_to(stage).as_posix() for path in stage.rglob("*") if path.is_file() and path.name != ARCHIVE_NAME)
    _write_json(report_path, report)
    _zip_deterministic(stage, stage / ARCHIVE_NAME, consumer_only=True)


def _replace_tree(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    incoming = destination.parent / f".{destination.name}.incoming"
    if incoming.exists():
        shutil.rmtree(incoming)
    shutil.copytree(source, incoming)
    previous = destination.parent / f".{destination.name}.previous"
    if previous.exists():
        shutil.rmtree(previous)
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


def _replace_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    os.close(descriptor)
    staged = Path(temporary)
    try:
        shutil.copyfile(source, staged)
        os.replace(staged, destination)
    finally:
        staged.unlink(missing_ok=True)


def _commit_record(
    store: ProjectStore,
    operation: str,
    expected_revision: int | None,
    artifacts: list[dict[str, Any]],
    details: dict[str, Any],
) -> int:
    record = {
        "schema_version": "1.0.0",
        "operation": operation,
        "source_revision": store.revision,
        "artifacts": artifacts,
        **details,
    }
    return store.commit(
        {f"{_DERIVED_RECORD_ROOT}/{operation}.json": record},
        expected_revision=expected_revision,
    )


def generate_pack(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    source_revision = _require_revision(store, expected_revision)
    temporary, stage, _ir, plan = _compile_staged(store)
    try:
        _require_revision(store, source_revision)
        behavior = store.resolve("bedrock/behavior_pack")
        resources = store.resolve("bedrock/resource_pack")
        _replace_tree(stage / "behavior_pack", behavior)
        _replace_tree(stage / "resource_pack", resources)
        backend_reports = store.resolve("reports/backend")
        _replace_tree(stage / "reports", backend_reports)
        _replace_tree(stage / "reports", store.resolve("bedrock/reports"))
        _replace_file(stage / "conversion-manifest.json", store.resolve("bedrock/conversion-manifest.json"))
        _replace_file(stage / ARCHIVE_NAME, store.resolve(f"bedrock/{ARCHIVE_NAME}"))
        if (stage / "tests").is_dir():
            _replace_tree(stage / "tests", store.resolve("tests/generated"))
            _replace_tree(stage / "tests", store.resolve("bedrock/tests"))
        artifacts = [
            _artifact(store, behavior, "behavior_pack"),
            _artifact(store, resources, "resource_pack"),
            _artifact(store, store.resolve("bedrock/conversion-manifest.json"), "conversion_manifest"),
            _artifact(store, store.resolve(f"bedrock/{ARCHIVE_NAME}"), "generated_archive"),
            _artifact(store, backend_reports, "backend_reports"),
        ]
        revision = _commit_record(store, "generate_pack", source_revision, artifacts, {
            "target_profile": plan.get("target_profile"),
            "feature_count": len(plan.get("features", [])),
        })
    finally:
        temporary.cleanup()
    return {"status": "GENERATED", "revision": revision, "artifacts": artifacts}, store, artifacts


def package_mcaddon(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    source_revision = _require_revision(store, expected_revision)
    behavior, resources = store.resolve("bedrock/behavior_pack"), store.resolve("bedrock/resource_pack")
    if not (behavior / "manifest.json").is_file() or not (resources / "manifest.json").is_file():
        raise OperationError("PACK_NOT_GENERATED", "package_mcaddon requires generated behavior and resource packs", details={"status": "BLOCKED", "feature": "package", "blocker": "Run generate_pack first", "mutated": False})
    destination = store.resolve("dist/marketplace-candidate/converted-mod.mcaddon")
    consumer_behavior = store.resolve("dist/marketplace-candidate/behavior-pack")
    consumer_resources = store.resolve("dist/marketplace-candidate/resource-pack")
    consumer_scripts = store.resolve("dist/marketplace-candidate/scripts")
    with tempfile.TemporaryDirectory(prefix="mccompiler-package-") as temporary:
        root = Path(temporary)
        shutil.copytree(behavior, root / "behavior_pack")
        shutil.copytree(resources, root / "resource_pack")
        staged = root / ARCHIVE_NAME
        _zip_deterministic(root, staged, consumer_only=True)
        _require_revision(store, source_revision)
        _replace_file(staged, destination)
    _replace_tree(behavior, consumer_behavior)
    _replace_tree(resources, consumer_resources)
    if (behavior / "scripts").is_dir():
        _replace_tree(behavior / "scripts", consumer_scripts)
    metadata = {
        "schema_version": "1.0.0",
        "target_profile": store.manifest.get("target_profile"),
        "archive": {"name": destination.name, "sha256": _sha256(destination), "bytes": destination.stat().st_size},
        "marketplace_approval_implied": False,
        "runtime_verified": False,
        "console_verified": False,
    }
    store.write("dist/marketplace-candidate/consumer-metadata/package.json", metadata)
    artifacts = [
        _artifact(store, destination, "mcaddon"),
        _artifact(store, consumer_behavior, "consumer_behavior_pack"),
        _artifact(store, consumer_resources, "consumer_resource_pack"),
        _artifact(store, store.resolve("dist/marketplace-candidate/consumer-metadata/package.json"), "consumer_metadata"),
    ]
    if consumer_scripts.is_dir():
        artifacts.append(_artifact(store, consumer_scripts, "consumer_scripts"))
    revision = _commit_record(store, "package_mcaddon", source_revision, artifacts, {"deterministic": True})
    return {"status": "PACKAGED", "revision": revision, "archive": artifacts[0]}, store, artifacts


def generate_world(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
    source_revision = _require_revision(store, expected_revision)
    behavior, resources = store.resolve("bedrock/behavior_pack"), store.resolve("bedrock/resource_pack")
    if not (behavior / "manifest.json").is_file() or not (resources / "manifest.json").is_file():
        raise OperationError("PACK_NOT_GENERATED", "generate_world requires generated behavior and resource packs", details={"status": "BLOCKED", "feature": "world", "blocker": "Run generate_pack first", "mutated": False})
    name = parameters.get("world_name", "MCCompiler Test World")
    if not isinstance(name, str) or not name.strip():
        raise ProjectError("INVALID_PARAMETERS", "world_name must be a non-empty string")
    destination = store.resolve("dist/test-world/generated-test-world.mcworld")
    with tempfile.TemporaryDirectory(prefix="mccompiler-world-") as temporary:
        staged = Path(temporary) / destination.name
        evidence = generate_test_world(behavior, resources, staged, world_name=name.strip())
        _require_revision(store, source_revision)
        _replace_file(staged, destination)
    artifacts = [_artifact(store, destination, "mcworld")]
    evidence = {**evidence, "path": artifacts[0]["path"], "world_hash": artifacts[0]["sha256"]}
    revision = _commit_record(store, "generate_world", source_revision, artifacts, {"world": evidence})
    return {"status": "GENERATED", "revision": revision, "world": evidence}, store, artifacts


def _focused(operation: str, kind: str) -> Callable[[ProjectStore, dict[str, Any], int | None], HandlerResult]:
    def handler(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
        source_revision = _require_revision(store, expected_revision)
        identifier = parameters.get("id") or parameters.get("identifier") or parameters.get("target")
        if not isinstance(identifier, str) or not identifier:
            raise ProjectError("INVALID_PARAMETERS", f"{operation} requires id")
        ir, _plan = _inputs(store)
        row = next((item for item in ir.get("content", []) if item.get("kind") == kind and item.get("identifier") == identifier), None)
        if row is None:
            raise OperationError("FEATURE_NOT_FOUND", f"{operation} cannot find {kind} feature {identifier}", details={"status": "BLOCKED", "feature": identifier, "kind": kind, "blocker": "No matching persisted ModIR feature", "mutated": False})
        temporary, stage, _ir, plan = _compile_staged(store)
        try:
            manifest = json.loads((stage / "conversion-manifest.json").read_text(encoding="utf-8"))
            generated = next((item for item in manifest.get("generated", []) if item.get("id") == identifier and item.get("kind") == kind), None)
            if generated is None:
                feature: dict[str, Any] = next((item for item in plan.get("features", []) if item.get("id") == identifier), {})
                raise OperationError("FEATURE_GENERATION_BLOCKED", f"{operation} cannot scaffold {identifier}", details={"status": "BLOCKED", "feature": identifier, "kind": kind, "classification": feature.get("classification", "UNPLANNED"), "blocker": "Backend produced no attributable feature artifact", "mutated": False})
            source = stage / str(generated["path"])
            relative = Path(str(generated["path"]))
            destination = store.resolve(Path("bedrock") / relative)
            _require_revision(store, source_revision)
            _replace_file(source, destination)
            artifact = _artifact(store, destination, kind)
            revision = _commit_record(store, operation, source_revision, [artifact], {"feature": identifier, "kind": kind, "classification": generated.get("classification")})
        finally:
            temporary.cleanup()
        return {"status": "SCAFFOLDED", "revision": revision, "feature": identifier, "artifact": artifact}, store, [artifact]
    handler.__name__ = operation
    return handler


generate_item = _focused("generate_item", "item")
generate_block = _focused("generate_block", "block")
generate_entity = _focused("generate_entity", "entity")
generate_recipe = _focused("generate_recipe", "recipe")
generate_structure = _focused("generate_structure", "structure")


def _blocked(operation: str, feature_kind: str) -> Callable[[ProjectStore, dict[str, Any], int | None], HandlerResult]:
    def handler(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> HandlerResult:
        _require_revision(store, expected_revision)
        feature = parameters.get("id") or parameters.get("identifier") or parameters.get("target")
        raise OperationError("FEATURE_GENERATION_BLOCKED", f"{operation} has no safe focused generator", details={"status": "BLOCKED", "feature": feature, "kind": feature_kind, "blocker": "Existing Bedrock backend does not emit an attributable focused artifact for this feature kind", "mutated": False})
    handler.__name__ = operation
    return handler


generate_projectile = _blocked("generate_projectile", "projectile")
generate_loot = _blocked("generate_loot", "loot")
generate_spawn_rules = _blocked("generate_spawn_rules", "spawn_rules")
generate_animation = _blocked("generate_animation", "animation")
generate_form = _blocked("generate_form", "form")
generate_script_scaffold = _blocked("generate_script_scaffold", "script")
