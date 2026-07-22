from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, cast


TEXTURE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".tga"})


def load_console_performance_catalog(path: str | Path | None = None) -> dict[str, Any]:
    catalog_path = Path(path) if path else Path(__file__).with_name("capabilities") / "console-performance.json"
    return cast(dict[str, Any], json.loads(catalog_path.read_text(encoding="utf-8")))


def _approved_exception(raw: Any, metric: str) -> bool:
    if not isinstance(raw, Mapping) or raw.get("metric") != metric or raw.get("approved_by_type") != "human":
        return False
    if not all(isinstance(raw.get(key), str) and raw[key].strip() for key in ("approved_by", "approver_id", "approved_at", "reason")):
        return False
    try:
        datetime.fromisoformat(str(raw["approved_at"]).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def audit_static_performance(
    pack_root: str | Path,
    *,
    catalog: Mapping[str, Any] | None = None,
    approved_exceptions: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    root = Path(pack_root).resolve()
    policy = dict(catalog or load_console_performance_catalog())
    limits = policy.get("static_budgets") or {}
    files = sorted(path for path in root.rglob("*") if path.is_file()) if root.is_dir() else []
    texture_files = [path for path in files if path.suffix.lower() in TEXTURE_SUFFIXES]
    observed = {
        "pack_bytes": sum(path.stat().st_size for path in files),
        "file_count": len(files),
        "texture_count": len(texture_files),
    }
    exceptions = list(approved_exceptions or [])
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    if not root.is_dir():
        errors.append(f"Pack root does not exist: {root}")
    for metric in ("pack_bytes", "file_count", "texture_count"):
        limit = limits.get(metric)
        if not isinstance(limit, int) or limit < 0:
            errors.append(f"Missing or invalid static performance budget: {metric}")
            checks.append({"metric": metric, "observed": observed[metric], "limit": limit, "passed": False, "exception": None})
            continue
        exceeded = observed[metric] > limit
        matching = [item for item in exceptions if isinstance(item, Mapping) and item.get("metric") == metric]
        approved = next((item for item in matching if _approved_exception(item, metric)), None)
        if exceeded and approved is None:
            errors.append(f"Static performance budget exceeded: {metric} {observed[metric]} > {limit}")
        checks.append({
            "metric": metric, "observed": observed[metric], "limit": limit,
            "passed": not exceeded or approved is not None,
            "exception": dict(approved) if approved is not None else None,
        })
    return {
        "schema_version": "1.0.0", "catalog_version": policy.get("catalog_version"),
        "target": policy.get("target"), "pack_root": str(root), "observed": observed,
        "checks": checks, "errors": sorted(errors), "passed": not errors,
    }
