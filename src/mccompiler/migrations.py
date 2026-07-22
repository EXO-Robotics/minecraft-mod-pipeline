from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable, Mapping
from typing import Any


class MigrationError(ValueError):
    """Raised for unsupported or invalid schema migration requests."""


LEGACY_0_1_FIELDS = frozenset({
    "schema_version", "tool", "input", "metadata", "dependencies", "content", "assets",
    "registries", "behaviors", "state", "presentation", "presentation_requirements",
    "world_requirements", "ui", "ui_intent", "networking", "networking_intent",
    "unsupported", "unsupported_hooks", "diagnostics", "tests", "target", "modpack",
    "mods", "dependency_graph", "aggregate", "evidence_policy",
})


def _canonical_digest(document: Mapping[str, Any]) -> str:
    try:
        encoded = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise MigrationError(f"ModIR is not canonical JSON: {exc}") from exc
    return hashlib.sha256(encoded).hexdigest()


def _array(document: Mapping[str, Any], current: str, legacy: str | None = None) -> list[Any]:
    value = document.get(current, document.get(legacy, []) if legacy else [])
    if not isinstance(value, list):
        raise MigrationError(f"Legacy field {current!r} must be an array")
    return copy.deepcopy(value)


def migrate_modir_0_1_0_to_1_0_0(document: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(document, Mapping) or document.get("schema_version") != "0.1.0":
        raise MigrationError("Migration requires a ModIR 0.1.0 object")
    unknown = sorted(set(document) - LEGACY_0_1_FIELDS)
    if unknown:
        raise MigrationError(f"Unknown ModIR 0.1.0 fields: {', '.join(unknown)}")

    object_defaults = {
        "metadata": {}, "input": {}, "dependency_graph": {"nodes": [], "edges": []},
        "aggregate": {"content_counts": {}, "asset_counts": {}, "risk_flags": [], "source_signals": {}},
    }
    for name, default in object_defaults.items():
        value = document.get(name, default)
        if not isinstance(value, Mapping):
            raise MigrationError(f"Legacy field {name!r} must be an object")

    source_digest = _canonical_digest(document)
    migrated: dict[str, Any] = {
        "schema_version": "1.0.0",
        "tool": copy.deepcopy(document.get("tool", {"name": "minecraft-compiler-baseline", "version": "0.1.0"})),
        "input": copy.deepcopy(dict(document.get("input", {}))),
        "metadata": copy.deepcopy(dict(document.get("metadata", {}))),
        "dependencies": _array(document, "dependencies"),
        "content": _array(document, "content"),
        "assets": _array(document, "assets"),
        "registries": _array(document, "registries"),
        "behaviors": _array(document, "behaviors"),
        "state": _array(document, "state"),
        "presentation_requirements": _array(document, "presentation_requirements", "presentation"),
        "world_requirements": _array(document, "world_requirements"),
        "ui_intent": _array(document, "ui_intent", "ui"),
        "networking_intent": _array(document, "networking_intent", "networking"),
        "unsupported_hooks": _array(document, "unsupported_hooks", "unsupported"),
        "diagnostics": _array(document, "diagnostics"),
        "tests": _array(document, "tests"),
        "target": copy.deepcopy(document.get("target")),
        "modpack": copy.deepcopy(document.get("modpack")),
        "mods": _array(document, "mods"),
        "dependency_graph": copy.deepcopy(dict(document.get("dependency_graph", object_defaults["dependency_graph"]))),
        "aggregate": copy.deepcopy(dict(document.get("aggregate", object_defaults["aggregate"]))),
        "evidence_policy": document.get("evidence_policy", "No generated behavior without traceable evidence or explicit override."),
        "migration_provenance": [{
            "from": "0.1.0", "to": "1.0.0", "migration": "modir-0.1.0-to-1.0.0",
            "source_sha256": source_digest,
        }],
    }
    return migrated


Migration = Callable[[Mapping[str, Any]], dict[str, Any]]
MIGRATIONS: dict[tuple[str, str], Migration] = {
    ("0.1.0", "1.0.0"): migrate_modir_0_1_0_to_1_0_0,
}


def migrate_modir(document: Mapping[str, Any], target_version: str = "1.0.0") -> dict[str, Any]:
    """Migrate over an explicitly registered path; unknown paths fail closed."""
    if not isinstance(document, Mapping):
        raise MigrationError("ModIR must be an object")
    source_version = document.get("schema_version")
    if not isinstance(source_version, str):
        raise MigrationError("ModIR requires a string schema_version")
    if source_version == target_version:
        if source_version != "1.0.0":
            raise MigrationError(f"No validated identity path for ModIR {source_version}")
        return copy.deepcopy(dict(document))
    migration = MIGRATIONS.get((source_version, target_version))
    if migration is None:
        raise MigrationError(f"Unknown ModIR migration path: {source_version} -> {target_version}")
    return migration(document)
