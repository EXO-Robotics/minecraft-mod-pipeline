from __future__ import annotations

import json
import re
import shutil
import subprocess
import uuid
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .bedrock import ARCHIVE_NAME, ZIP_TIME


IDENTIFIER = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")
IMPORT = re.compile(r"(?:from\s+|import\s*)['\"]([^'\"]+)['\"]")
SUPPORTED_MODULES = {"@minecraft/server", "@minecraft/server-ui"}
EXPERIMENTAL_MODULES = {"@minecraft/server-net", "@minecraft/server-admin"}
SUPPORTED_COMPONENTS = {
    "item": {
        "minecraft:allow_off_hand", "minecraft:block_placer", "minecraft:bundle_interaction",
        "minecraft:can_destroy_in_creative", "minecraft:cooldown", "minecraft:damage",
        "minecraft:damage_absorption", "minecraft:display_name", "minecraft:durability",
        "minecraft:dyeable", "minecraft:enchantable", "minecraft:entity_placer",
        "minecraft:food", "minecraft:fuel", "minecraft:glint", "minecraft:hand_equipped",
        "minecraft:icon", "minecraft:interact_button", "minecraft:liquid_clipped",
        "minecraft:max_stack_size", "minecraft:projectile", "minecraft:rarity",
        "minecraft:record", "minecraft:repairable", "minecraft:shooter", "minecraft:should_despawn",
        "minecraft:stacked_by_data", "minecraft:storage_item", "minecraft:tags",
        "minecraft:throwable", "minecraft:use_animation", "minecraft:use_modifiers",
        "minecraft:wearable",
    },
    "block": {
        "minecraft:collision_box", "minecraft:crafting_table", "minecraft:custom_components",
        "minecraft:destructible_by_explosion", "minecraft:destructible_by_mining",
        "minecraft:display_name", "minecraft:flammable", "minecraft:friction",
        "minecraft:geometry", "minecraft:light_dampening", "minecraft:light_emission",
        "minecraft:loot", "minecraft:map_color", "minecraft:material_instances",
        "minecraft:placement_filter", "minecraft:redstone_conductivity", "minecraft:selection_box",
        "minecraft:transformation", "minecraft:unit_cube",
    },
}
SCHEMA_FILES = {
    "modir": "modir-1.0.0.json",
    "behavior_ir": "behavior-ir-1.0.0.json",
    "overrides": "overrides-1.0.0.json",
}
ARTIFACT_PATHS = {
    "modir": ("modir.json", "mod-ir.json", "ir/modir.json", "reports/modir.json", "reports/mod-ir.json"),
    "behavior_ir": ("behavior-ir.json", "behaviorir.json", "ir/behavior-ir.json", "reports/behavior-ir.json"),
    "overrides": ("overrides.json", "ir/overrides.json", "reports/overrides.json"),
}


def _json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid JSON {path}: {exc}")
        return None


def _result(errors: list[str], warnings: list[str], checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "passed" if not errors else "failed",
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }


def _check(checks: list[dict[str, Any]], name: str, errors: list[str], start: int, **details: Any) -> None:
    checks.append({"name": name, **details, "passed": len(errors) == start})


def _objects(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


def _identifiers(value: Any) -> Iterable[str]:
    if isinstance(value, str) and IDENTIFIER.fullmatch(value):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _identifiers(child)
    elif isinstance(value, list):
        for child in value:
            yield from _identifiers(child)


def _schema_required(kind: str) -> list[str]:
    schema_path = Path(__file__).with_name("schemas") / SCHEMA_FILES[kind]
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        return list(schema.get("required", []))
    except (OSError, json.JSONDecodeError):
        return []


def _validate_schema_artifact(kind: str, document: Any, label: str, errors: list[str], warnings: list[str]) -> None:
    required = _schema_required(kind)
    documents = document if kind == "behavior_ir" and isinstance(document, list) else [document]
    if not isinstance(documents, list) or not documents:
        errors.append(f"Invalid {kind} schema artifact {label}: expected a non-empty object or array")
        return
    for index, item in enumerate(documents):
        where = f"{label}[{index}]" if len(documents) > 1 else label
        if not isinstance(item, dict):
            errors.append(f"Invalid {kind} schema artifact {where}: expected object")
            continue
        missing = [key for key in required if key not in item]
        if kind == "modir":
            # Phase-0 callers legitimately produced IR before these inventory arrays
            # were added. Keep those artifacts readable, but make the schema drift visible.
            compatibility_fields = {"registries", "world_requirements", "diagnostics"}
            legacy_missing = [key for key in missing if key in compatibility_fields]
            if legacy_missing:
                warnings.append(f"Legacy-compatible modir schema artifact {where} omits {', '.join(legacy_missing)}")
            missing = [key for key in missing if key not in compatibility_fields]
        if missing:
            errors.append(f"Invalid {kind} schema artifact {where}: missing {', '.join(missing)}")
        if kind in {"modir", "overrides"} and item.get("schema_version") != "1.0.0":
            errors.append(f"Unsupported {kind} schema version in {where}: {item.get('schema_version')}")
        if kind == "overrides" and "overrides" in item and not isinstance(item["overrides"], list):
            errors.append(f"Invalid overrides schema artifact {where}: overrides must be an array")
        if kind == "modir":
            for field in ("content", "assets", "behaviors", "state", "dependencies"):
                if field in item and not isinstance(item[field], list):
                    errors.append(f"Invalid modir schema artifact {where}: {field} must be an array")
        if kind == "behavior_ir":
            if not isinstance(item.get("trigger"), dict) or not item.get("trigger", {}).get("type"):
                errors.append(f"Invalid behavior_ir schema artifact {where}: trigger.type is required")
            for field in ("conditions", "actions", "evidence", "diagnostics"):
                if field in item and not isinstance(item[field], list):
                    errors.append(f"Invalid behavior_ir schema artifact {where}: {field} must be an array")


def _embedded_artifacts(
    root: Path,
    parsed: dict[Path, Any],
    conversion: dict[str, Any],
    supplied: dict[str, Any] | None,
) -> dict[str, list[tuple[str, Any]]]:
    found: dict[str, list[tuple[str, Any]]] = defaultdict(list)
    aliases = {"mod_ir": "modir", "behaviorir": "behavior_ir", "behavior-ir": "behavior_ir"}
    for kind, paths in ARTIFACT_PATHS.items():
        for relative in paths:
            path = root / relative
            if path in parsed:
                found[kind].append((str(path), parsed[path]))
    embedded = conversion.get("artifacts") if isinstance(conversion.get("artifacts"), dict) else conversion
    for raw_kind, document in embedded.items() if isinstance(embedded, dict) else []:
        kind = aliases.get(raw_kind, raw_kind)
        if kind in SCHEMA_FILES and isinstance(document, (dict, list)):
            found[kind].append((f"conversion-manifest.json#{raw_kind}", document))
    for raw_kind, document in (supplied or {}).items():
        kind = aliases.get(raw_kind, raw_kind)
        if kind in SCHEMA_FILES:
            found[kind].append((f"supplied:{raw_kind}", document))
    return found


def _definition(data: Any) -> tuple[str, str] | None:
    if not isinstance(data, dict):
        return None
    for key, kind in (
        ("minecraft:item", "item"), ("minecraft:block", "block"), ("minecraft:entity", "entity"),
        ("minecraft:spawn_rules", "spawn_rule"), ("minecraft:recipe_shaped", "recipe"),
        ("minecraft:recipe_shapeless", "recipe"), ("minecraft:recipe_furnace", "recipe"),
        ("minecraft:recipe_brewing_mix", "recipe"), ("minecraft:recipe_brewing_container", "recipe"),
    ):
        body = data.get(key)
        if isinstance(body, dict):
            identifier = (body.get("description") or {}).get("identifier")
            if identifier:
                return kind, str(identifier)
    return None


def _custom(identifier: str) -> bool:
    return bool(IDENTIFIER.fullmatch(identifier) and not identifier.startswith("minecraft:"))


def _script_check(root: Path, errors: list[str], warnings: list[str], checks: list[dict[str, Any]]) -> None:
    start = len(errors)
    script_root = root / "behavior_pack/scripts"
    scripts = sorted(script_root.rglob("*.js")) if script_root.exists() else []
    node = shutil.which("node")
    for script in scripts:
        try:
            text = script.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"Unreadable JavaScript {script}: {exc}")
            continue
        if text.count("{") != text.count("}") or text.count("[") != text.count("]") or text.count("(") != text.count(")"):
            errors.append(f"Unbalanced JavaScript delimiters: {script}")
        for specifier in IMPORT.findall(text):
            if specifier.startswith("."):
                target = script.parent / specifier
                candidates = [target, target.with_suffix(".js"), target / "index.js"]
                if not any(candidate.is_file() for candidate in candidates):
                    errors.append(f"Unresolved script import in {script}: {specifier}")
            elif specifier not in SUPPORTED_MODULES:
                qualifier = "experimental" if specifier in EXPERIMENTAL_MODULES else "unsupported"
                errors.append(f"Imported {qualifier} Script API module in {script}: {specifier}")
        if node:
            try:
                result = subprocess.run(
                    [node, "--check", str(script)], capture_output=True, text=True, timeout=10, check=False
                )
                if result.returncode:
                    detail = (result.stderr or result.stdout).strip().splitlines()
                    errors.append(f"JavaScript syntax error in {script}: {detail[-1] if detail else 'node --check failed'}")
            except (OSError, subprocess.TimeoutExpired) as exc:
                warnings.append(f"Node syntax check could not run for {script}: {exc}")
                node = None
    if scripts and not node:
        warnings.append("Node.js is unavailable; JavaScript validation used delimiter and import analysis only")
    _check(checks, "script-syntax-and-imports", errors, start, files=len(scripts), engine="node --check" if node else "fallback")


def _state_check(artifacts: dict[str, list[tuple[str, Any]]], errors: list[str], checks: list[dict[str, Any]]) -> None:
    start = len(errors)
    states: dict[str, tuple[str, Any, str]] = {}
    for label, document in artifacts.get("modir", []):
        if not isinstance(document, dict):
            continue
        for state in document.get("state", []):
            if not isinstance(state, dict):
                continue
            state_id = str(state.get("id", ""))
            value_type = str(state.get("value_type", ""))
            default = state.get("default")
            expected = {"number": (int, float), "integer": (int,), "boolean": (bool,), "string": (str,), "object": (dict,), "array": (list,)}.get(value_type)
            if not state_id:
                errors.append(f"State declaration without id in {label}")
            elif state_id in states:
                prior_type, prior_default, prior_label = states[state_id]
                if (value_type, default) != (prior_type, prior_default):
                    errors.append(f"Conflicting state schema {state_id}: {prior_label} and {label}")
                elif prior_label == label:
                    errors.append(f"Duplicate state schema {state_id}: {prior_label} and {label}")
            else:
                states[state_id] = (value_type, default, label)
            wrong_type = False
            if expected:
                wrong_type = isinstance(default, bool) if value_type in {"number", "integer"} else False
                wrong_type = wrong_type or not isinstance(default, expected)
            if wrong_type:
                errors.append(f"State default does not match {value_type} for {state_id} in {label}")
            if state.get("persistence") not in {None, "persistent", "session", "transient"}:
                errors.append(f"Unsupported state persistence for {state_id} in {label}: {state.get('persistence')}")
    _check(checks, "state-schema-consistency", errors, start, declarations=len(states))


def _content_checks(
    root: Path,
    parsed: dict[Path, Any],
    errors: list[str],
    warnings: list[str],
    checks: list[dict[str, Any]],
) -> None:
    start = len(errors)
    definitions: dict[tuple[str, str], list[Path]] = defaultdict(list)
    custom_content: set[str] = set()
    for path, data in parsed.items():
        if root / "behavior_pack" not in path.parents:
            continue
        definition = _definition(data)
        if definition:
            definitions[definition].append(path)
            if _custom(definition[1]) and definition[0] in {"item", "block", "entity"}:
                custom_content.add(definition[1])
    for (kind, identifier), paths in definitions.items():
        if len(paths) > 1:
            errors.append(f"Identifier collision for {kind} {identifier}: {', '.join(map(str, paths))}")
        if not IDENTIFIER.fullmatch(identifier):
            errors.append(f"Invalid Bedrock identifier for {kind} in {paths[0]}: {identifier}")
    _check(checks, "identifier-uniqueness", errors, start, definitions=len(definitions))

    start = len(errors)
    known = {identifier for (_, identifier) in definitions}
    conversion = parsed.get(root / "conversion-manifest.json") or {}
    if isinstance(conversion, dict):
        known.update(str(row.get("id")) for row in conversion.get("generated", []) if isinstance(row, dict) and row.get("id"))
    known.update({"minecraft:" + name for name in ("air", "stone")})
    for path, data in parsed.items():
        if root / "behavior_pack" not in path.parents or not isinstance(data, dict):
            continue
        definition = _definition(data)
        if definition and definition[0] == "recipe":
            body = next((data[key] for key in data if key.startswith("minecraft:recipe_")), {})
            refs = list(_identifiers(body.get("ingredients", []))) + list(_identifiers(body.get("result", {})))
            for reference in refs:
                if _custom(reference) and reference not in known:
                    errors.append(f"Missing referenced content {reference} in recipe {path}")
        if "minecraft:spawn_rules" in data:
            identifier = (data["minecraft:spawn_rules"].get("description") or {}).get("identifier")
            if _custom(str(identifier)) and ("entity", str(identifier)) not in definitions:
                errors.append(f"Spawn rule references missing entity {identifier} in {path}")
        if "pools" in data and "loot_tables" in path.parts:
            for reference in _identifiers(data.get("pools", [])):
                if _custom(reference) and reference not in known:
                    errors.append(f"Loot table references missing content {reference} in {path}")
    modir = parsed.get(root / "reports/modir.json") or {}
    if isinstance(modir, dict):
        ui_ids = {str(row.get("id")) for row in modir.get("ui_intent", []) if isinstance(row, dict)}
        reference_fields = {
            "spawn_entity": "entity", "spawn_projectile": "entity", "set_block": "block",
            "replace_block": "block", "add_item": "item", "remove_item": "item",
            "place_structure": "structure",
        }
        for behavior in modir.get("behaviors", []):
            if not isinstance(behavior, dict):
                continue
            for action in behavior.get("actions", []):
                if not isinstance(action, dict):
                    continue
                field = reference_fields.get(str(action.get("type")))
                reference = str(action.get(field, "")) if field else ""
                if reference and _custom(reference) and reference not in known:
                    errors.append(f"Behavior {behavior.get('id')} references missing generated content {reference}")
                if action.get("type") == "open_interaction_ui" and str(action.get("ui")) not in ui_ids:
                    errors.append(f"Behavior {behavior.get('id')} references missing UI intent {action.get('ui')}")
    _check(checks, "content-cross-references", errors, start)

    start = len(errors)
    for (kind, _), paths in definitions.items():
        if kind not in SUPPORTED_COMPONENTS:
            continue
        for path in paths:
            data = parsed[path]
            components = (data.get(f"minecraft:{kind}") or {}).get("components", {})
            for component in components if isinstance(components, dict) else []:
                if component.startswith("minecraft:") and component not in SUPPORTED_COMPONENTS[kind]:
                    errors.append(f"Unsupported {kind} component {component} in {path}")
    _check(checks, "supported-components", errors, start)

    start = len(errors)
    resource_map = parsed.get(root / "resource_pack/_source_asset_map.json")
    if isinstance(resource_map, list):
        for mapping in resource_map:
            destination = mapping.get("destination") if isinstance(mapping, dict) else None
            if destination and not (root / str(destination)).is_file():
                errors.append(f"Missing referenced resource asset: {destination}")
    item_texture = parsed.get(root / "resource_pack/textures/item_texture.json") or {}
    terrain_texture = parsed.get(root / "resource_pack/textures/terrain_texture.json") or {}
    texture_keys = set((item_texture.get("texture_data") or {})) | set((terrain_texture.get("texture_data") or {}))
    for (kind, _), paths in definitions.items():
        if kind not in {"item", "block"}:
            continue
        for path in paths:
            body = parsed[path].get(f"minecraft:{kind}") or {}
            components = body.get("components") or {}
            icon = components.get("minecraft:icon")
            keys = []
            if isinstance(icon, str):
                keys.append(icon)
            elif isinstance(icon, dict):
                keys.extend(str(icon[key]) for key in ("texture", "textures") if isinstance(icon.get(key), str))
            material = components.get("minecraft:material_instances") or {}
            keys.extend(str(value.get("texture")) for value in material.values() if isinstance(value, dict) and value.get("texture"))
            for key in keys:
                if key not in texture_keys:
                    errors.append(f"Missing referenced texture key {key} for {kind} in {path}")
    _check(checks, "referenced-resources", errors, start, texture_keys=len(texture_keys))

    start = len(errors)
    client_entities: set[str] = set()
    for path, data in parsed.items():
        client = data.get("minecraft:client_entity") if isinstance(data, dict) else None
        identifier = (client.get("description") or {}).get("identifier") if isinstance(client, dict) else None
        if identifier:
            client_entities.add(str(identifier))
    for identifier in client_entities:
        if ("entity", identifier) not in definitions:
            errors.append(f"Resource client entity has no behavior entity: {identifier}")
    _check(checks, "resource-behavior-correspondence", errors, start, client_entities=len(client_entities))

    language_files = sorted((root / "resource_pack/texts").glob("*.lang")) if (root / "resource_pack/texts").exists() else []
    language_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in language_files)
    if custom_content and not language_files:
        warnings.append(f"No localization files found for {len(custom_content)} custom content identifiers")
    elif language_files:
        for identifier in sorted(custom_content):
            if not any(identifier in line.partition("=")[0] for line in language_text.splitlines()):
                warnings.append(f"No localization entry found for custom content {identifier}")
    checks.append({"name": "localization-coverage", "passed": True, "files": len(language_files), "warnings": sum("localization" in x.lower() for x in warnings)})


def _manifest_checks(
    root: Path, manifests: list[tuple[Path, Any]], errors: list[str], warnings: list[str], checks: list[dict[str, Any]]
) -> None:
    start = len(errors)
    seen: dict[str, Path] = {}
    pack_ids: set[str] = set()
    module_dependencies: dict[str, str] = {}
    for path, data in manifests:
        if not isinstance(data, dict):
            continue
        header = data.get("header") or {}
        modules = data.get("modules") or []
        for label, value in [("header", header.get("uuid"))] + [("module", x.get("uuid")) for x in modules if isinstance(x, dict)]:
            try:
                uuid.UUID(str(value))
            except (ValueError, AttributeError):
                errors.append(f"Invalid {label} UUID in {path}: {value}")
            if value in seen:
                errors.append(f"Duplicate UUID {value}: {path} and {seen[value]}")
            elif value:
                seen[value] = path
        if header.get("uuid"):
            pack_ids.add(str(header["uuid"]))
        for module in modules:
            if isinstance(module, dict) and module.get("type") == "script":
                entry = root / "behavior_pack" / str(module.get("entry", ""))
                if not entry.is_file():
                    errors.append(f"Missing script module entry: {entry}")
        min_engine = header.get("min_engine_version")
        if not isinstance(min_engine, list) or len(min_engine) != 3 or not all(isinstance(x, int) for x in min_engine):
            errors.append(f"Invalid min_engine_version in {path}: {min_engine}")
    for path, data in manifests:
        if not isinstance(data, dict):
            continue
        for dependency in data.get("dependencies", []):
            if not isinstance(dependency, dict):
                errors.append(f"Invalid dependency in {path}: expected object")
                continue
            dep_uuid = dependency.get("uuid")
            module_name = dependency.get("module_name")
            if dep_uuid and str(dep_uuid) not in pack_ids:
                errors.append(f"Unresolved pack dependency {dep_uuid} in {path}")
            if module_name:
                version = dependency.get("version")
                if module_name not in SUPPORTED_MODULES:
                    qualifier = "experimental" if module_name in EXPERIMENTAL_MODULES else "unsupported"
                    errors.append(f"Manifest declares {qualifier} Script API module {module_name} in {path}")
                if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+(?:-(?:beta|stable))?", version):
                    errors.append(f"Invalid Script API dependency version for {module_name} in {path}: {version}")
                if module_name in module_dependencies and module_dependencies[module_name] != version:
                    errors.append(f"Conflicting Script API versions for {module_name}: {module_dependencies[module_name]} and {version}")
                module_dependencies[str(module_name)] = str(version)
                if isinstance(version, str) and "beta" in version:
                    warnings.append(f"Experimental Script API dependency requested: {module_name} {version}")
    _check(checks, "manifest-identities-dependencies-and-script-api", errors, start, script_modules=module_dependencies)


def _dependency_check(artifacts: dict[str, list[tuple[str, Any]]], errors: list[str], checks: list[dict[str, Any]]) -> None:
    start = len(errors)
    examined = 0
    for label, document in artifacts.get("modir", []):
        if not isinstance(document, dict):
            continue
        mod_ids = {str(mod.get("id")) for mod in document.get("mods", []) if isinstance(mod, dict) and mod.get("id")}
        for dependency in document.get("dependencies", []):
            if not isinstance(dependency, dict):
                errors.append(f"Invalid ModIR dependency in {label}: expected object")
                continue
            examined += 1
            dep_id = str(dependency.get("id") or dependency.get("mod_id") or dependency.get("to") or "")
            required = dependency.get("required", not dependency.get("optional", False))
            if required and dependency.get("resolved") is False:
                errors.append(f"Unresolved required ModIR dependency {dep_id} in {label}")
            if required and dependency.get("internal") is True and dep_id not in mod_ids:
                errors.append(f"Missing internal ModIR dependency {dep_id} in {label}")
            if not dep_id:
                errors.append(f"ModIR dependency without id in {label}")
    _check(checks, "mod-dependency-resolution", errors, start, dependencies=examined)


def _runtime_evidence(root: Path, parsed: dict[Path, Any], requested: bool) -> tuple[dict[str, Any], list[str], list[str]]:
    candidates = (
        root / "reports/runtime-evidence.json", root / "reports/runtime-validation.json",
        root / "runtime-evidence.json", root / "runtime-validation.json",
    )
    evidence_path = next((path for path in candidates if path in parsed), None)
    if evidence_path is None:
        reason = "No runtime evidence artifact is present; static and integration validation do not imply activation"
        if requested:
            reason += "; use a configured BDS runtime harness"
            error = "Runtime validation was required but no runtime evidence artifact is present"
            return {"status": "failed", "valid": False, "reason": reason, "evidence": None, "errors": [error], "warnings": []}, [error], []
        return {"status": "not-run", "reason": reason, "evidence": None}, [], []
    evidence = parsed[evidence_path]
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(evidence, dict):
        errors.append(f"Invalid runtime evidence document: {evidence_path}")
    else:
        status = str(evidence.get("status", "")).lower()
        attempted = evidence.get("attempted", status in {"passed", "failed"})
        logs = evidence.get("logs") or evidence.get("log_excerpt") or evidence.get("runtime_log")
        checks = evidence.get("checks") or []
        critical = evidence.get("critical_errors") or []
        if not attempted:
            warnings.append(f"Runtime evidence reports no attempted run: {evidence_path}")
            return {"status": "not-run", "reason": "Runtime evidence explicitly reports no attempted run", "evidence": str(evidence_path)}, [], warnings
        if not logs:
            errors.append(f"Runtime evidence lacks runtime-log output: {evidence_path}")
        log_text = logs if isinstance(logs, str) else "\n".join(map(str, logs)) if isinstance(logs, list) else json.dumps(logs)
        detected = re.findall(
            r"(?im)^.*(?:\berror(?:\s*[:\]]|\s*$)|\bexception\b|failed to load|syntaxerror).*$",
            log_text or "",
        )
        if critical or detected:
            errors.append(f"Runtime evidence contains critical errors: {critical or detected[:3]}")
        failed_checks = [item for item in checks if isinstance(item, dict) and item.get("passed") is False]
        if failed_checks:
            errors.append("Runtime evidence contains failed checks: " + ", ".join(str(x.get("name", "unnamed")) for x in failed_checks))
        if status not in {"passed", "failed"}:
            errors.append(f"Runtime evidence has unsupported status {status or '<missing>'}: {evidence_path}")
        if status == "failed":
            errors.append(f"Runtime harness reported failure: {evidence_path}")
        if status == "passed" and not checks:
            warnings.append("Runtime evidence passed without structured behavioral checks")
    return {
        "status": "failed" if errors else "passed",
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "evidence": str(evidence_path),
    }, errors, warnings


def validate_output(
    path: str | Path,
    plan: dict[str, Any] | None = None,
    *,
    runtime: bool = False,
    artifacts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate generated output in static, integration, and evidenced-runtime layers.

    ``artifacts`` may supply ``modir``, ``behavior_ir``, or ``overrides`` documents.
    Runtime is never inferred: only a structured runtime evidence JSON can pass it.
    """
    root = Path(path).expanduser().resolve()
    if root.is_file() and root.suffix == ".mcaddon":
        root = root.parent
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []
    if not root.is_dir():
        errors.append(f"Output does not exist: {root}")
        return {
            "path": str(root),
            "layers": {
                "static": _result(errors, warnings, checks),
                "integration": _result([], [], []),
                "runtime": {"status": "not-run", "reason": "output missing"},
            },
            "errors": errors, "warnings": warnings, "valid": False,
        }

    required = [
        "behavior_pack/manifest.json", "resource_pack/manifest.json", "conversion-manifest.json",
        "reports/provenance.json", "reports/unsupported-and-approximations.json",
        "tests/behavior-plan.json", ARCHIVE_NAME,
    ]
    start = len(errors)
    missing = [item for item in required if not (root / item).exists()]
    errors.extend(f"Missing required output: {item}" for item in missing)
    _check(checks, "required-layout", errors, start)

    start = len(errors)
    json_files = sorted(root.rglob("*.json"))
    parsed = {json_path: _json(json_path, errors) for json_path in json_files}
    _check(checks, "json-parse", errors, start, files=len(json_files))
    conversion = parsed.get(root / "conversion-manifest.json") or {}
    embedded = _embedded_artifacts(root, parsed, conversion if isinstance(conversion, dict) else {}, artifacts)

    start = len(errors)
    for kind, entries in embedded.items():
        for label, document in entries:
            _validate_schema_artifact(kind, document, label, errors, warnings)
    _check(checks, "ir-and-override-schemas", errors, start, artifacts=sum(map(len, embedded.values())))
    _state_check(embedded, errors, checks)
    _dependency_check(embedded, errors, checks)

    manifest_paths = (root / "behavior_pack/manifest.json", root / "resource_pack/manifest.json")
    manifests = [(manifest, parsed.get(manifest)) for manifest in manifest_paths if manifest.exists()]
    _manifest_checks(root, manifests, errors, warnings, checks)
    _script_check(root, errors, warnings, checks)
    _content_checks(root, parsed, errors, warnings, checks)

    start = len(errors)
    archive = root / ARCHIVE_NAME
    if archive.exists():
        try:
            with zipfile.ZipFile(archive) as bundle:
                infos = bundle.infolist()
                names = [info.filename for info in infos]
                if names != sorted(names):
                    errors.append("Archive members are not lexicographically ordered")
                if any(info.date_time != ZIP_TIME for info in infos):
                    errors.append("Archive contains nondeterministic timestamps")
                if bundle.testzip() is not None:
                    errors.append("Archive contains a corrupt member")
                disk = sorted(file.relative_to(root).as_posix() for file in root.rglob("*") if file.is_file() and file != archive)
                if names != disk:
                    errors.append("Archive member set differs from generated output")
        except zipfile.BadZipFile:
            errors.append(f"Invalid mcaddon archive: {archive}")
    _check(checks, "archive-reproducibility-metadata", errors, start)

    integration_errors: list[str] = []
    integration_warnings: list[str] = []
    integration_checks: list[dict[str, Any]] = []
    provenance = parsed.get(root / "reports/provenance.json") or {}
    behavior_plan = parsed.get(root / "tests/behavior-plan.json") or {}
    planned_ids = {str(item.get("id")) for item in (plan or {}).get("features", [])} if plan else {str(item) for item in conversion.get("plan_feature_ids", [])}
    covered = {str(item.get("id")) for item in provenance.get("features", [])} | {str(item.get("id")) for item in conversion.get("omitted", [])}
    absent = sorted(planned_ids - covered)
    if absent:
        integration_errors.append(f"Plan features lack generated/omitted provenance: {', '.join(absent)}")
    approved_behaviors = set(behavior_plan.get("approved", []))
    provenance_by_id = {str(item.get("id")): item for item in provenance.get("features", [])}
    unsafe = [item for item in approved_behaviors if not provenance_by_id.get(str(item), {}).get("evidence")]
    if unsafe:
        integration_errors.append(f"Generated behavior lacks evidence: {', '.join(sorted(map(str, unsafe)))}")
    integration_checks.append({"name": "plan-coverage", "planned": len(planned_ids), "covered": len(planned_ids - set(absent)), "passed": not absent})
    integration_checks.append({"name": "behavior-provenance", "approved": len(approved_behaviors), "passed": not unsafe})
    if not plan:
        integration_warnings.append("Integration validated against embedded plan feature IDs; no external plan supplied")

    runtime_result, runtime_errors, runtime_warnings = _runtime_evidence(root, parsed, runtime)
    static = _result(errors, warnings, checks)
    integration = _result(integration_errors, integration_warnings, integration_checks)
    all_errors = errors + integration_errors + runtime_errors
    all_warnings = warnings + integration_warnings + runtime_warnings
    return {
        "path": str(root), "manifest_count": len(manifests),
        "layers": {"static": static, "integration": integration, "runtime": runtime_result},
        "errors": all_errors, "warnings": all_warnings, "valid": not all_errors,
    }
