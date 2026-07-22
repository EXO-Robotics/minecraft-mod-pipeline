from __future__ import annotations

import json
import uuid
import zipfile
from pathlib import Path
from typing import Any

from .bedrock import ARCHIVE_NAME, ZIP_TIME


def _json(path: Path, errors: list[str]) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid JSON {path}: {exc}")
        return None


def _result(errors: list[str], warnings: list[str], checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {"status": "passed" if not errors else "failed", "valid": not errors, "errors": errors, "warnings": warnings, "checks": checks}


def validate_output(path: str | Path, plan: dict[str, Any] | None = None, *, runtime: bool = False) -> dict[str, Any]:
    root = Path(path).expanduser().resolve()
    if root.is_file() and root.suffix == ".mcaddon": root = root.parent
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []
    if not root.is_dir():
        errors.append(f"Output does not exist: {root}")
        return {"path": str(root), "layers": {"static": _result(errors, warnings, checks), "integration": _result([], [], []), "runtime": {"status": "not-run", "reason": "output missing"}}, "errors": errors, "warnings": warnings, "valid": False}

    required = ["behavior_pack/manifest.json", "resource_pack/manifest.json", "conversion-manifest.json", "reports/provenance.json", "reports/unsupported-and-approximations.json", "tests/behavior-plan.json", ARCHIVE_NAME]
    missing = [x for x in required if not (root / x).exists()]
    if missing: errors.extend(f"Missing required output: {x}" for x in missing)
    checks.append({"name": "required-layout", "passed": not missing})

    json_files = sorted(root.rglob("*.json"))
    parsed = {p: _json(p, errors) for p in json_files}
    checks.append({"name": "json-parse", "files": len(json_files), "passed": all(v is not None for v in parsed.values())})
    manifests = [(p, parsed.get(p)) for p in (root / "behavior_pack/manifest.json", root / "resource_pack/manifest.json") if p.exists()]
    seen: dict[str, Path] = {}
    pack_ids: set[str] = set()
    for path_, data in manifests:
        if not isinstance(data, dict): continue
        header = data.get("header") or {}
        modules = data.get("modules") or []
        for label, value in [("header", header.get("uuid"))] + [("module", x.get("uuid")) for x in modules if isinstance(x, dict)]:
            try: uuid.UUID(str(value))
            except (ValueError, AttributeError): errors.append(f"Invalid {label} UUID in {path_}: {value}")
            if value in seen: errors.append(f"Duplicate UUID {value}: {path_} and {seen[value]}")
            elif value: seen[value] = path_
        if header.get("uuid"): pack_ids.add(header["uuid"])
        script_modules = [x for x in modules if x.get("type") == "script"]
        for module in script_modules:
            entry = root / "behavior_pack" / str(module.get("entry", ""))
            if not entry.is_file(): errors.append(f"Missing script module entry: {entry}")
    for path_, data in manifests:
        if not isinstance(data, dict): continue
        for dependency in data.get("dependencies", []):
            if dependency.get("uuid") and dependency["uuid"] not in pack_ids: errors.append(f"Unresolved pack dependency {dependency['uuid']} in {path_}")
    checks.append({"name": "manifest-identities-and-references", "passed": not any("UUID" in x or "dependency" in x or "script module" in x for x in errors)})

    for script in sorted((root / "behavior_pack/scripts").rglob("*.js")) if (root / "behavior_pack/scripts").exists() else []:
        text = script.read_text(encoding="utf-8")
        if text.count("{") != text.count("}") or text.count("[") != text.count("]"):
            errors.append(f"Unbalanced JavaScript delimiters: {script}")
        for rel in __import__("re").findall(r"from\s+['\"](\.[^'\"]+)['\"]", text):
            target = (script.parent / rel)
            if not target.suffix: target = target.with_suffix(".js")
            if not target.exists(): errors.append(f"Unresolved script import in {script}: {rel}")
    checks.append({"name": "script-static", "passed": not any("script" in x.lower() or "JavaScript" in x for x in errors)})

    archive = root / ARCHIVE_NAME
    if archive.exists():
        try:
            with zipfile.ZipFile(archive) as bundle:
                infos = bundle.infolist()
                names = [x.filename for x in infos]
                if names != sorted(names): errors.append("Archive members are not lexicographically ordered")
                if any(x.date_time != ZIP_TIME for x in infos): errors.append("Archive contains nondeterministic timestamps")
                if bundle.testzip() is not None: errors.append("Archive contains a corrupt member")
                disk = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p != archive)
                if names != disk: errors.append("Archive member set differs from generated output")
        except zipfile.BadZipFile: errors.append(f"Invalid mcaddon archive: {archive}")
    checks.append({"name": "archive-reproducibility-metadata", "passed": not any("Archive" in x for x in errors)})

    integration_errors: list[str] = []
    integration_warnings: list[str] = []
    integration_checks: list[dict[str, Any]] = []
    conversion = parsed.get(root / "conversion-manifest.json") or {}
    provenance = parsed.get(root / "reports/provenance.json") or {}
    behavior_plan = parsed.get(root / "tests/behavior-plan.json") or {}
    planned_ids = {str(x.get("id")) for x in (plan or {}).get("features", [])} if plan else {str(x) for x in conversion.get("plan_feature_ids", [])}
    covered = {str(x.get("id")) for x in provenance.get("features", [])} | {str(x.get("id")) for x in conversion.get("omitted", [])}
    absent = sorted(planned_ids - covered)
    if absent: integration_errors.append(f"Plan features lack generated/omitted provenance: {', '.join(absent)}")
    approved_behaviors = set(behavior_plan.get("approved", []))
    provenance_by_id = {str(x.get("id")): x for x in provenance.get("features", [])}
    unsafe = [x for x in approved_behaviors if not provenance_by_id.get(str(x), {}).get("evidence")]
    if unsafe: integration_errors.append(f"Generated behavior lacks evidence: {', '.join(sorted(map(str, unsafe)))}")
    integration_checks.append({"name": "plan-coverage", "planned": len(planned_ids), "covered": len(planned_ids - set(absent)), "passed": not absent})
    integration_checks.append({"name": "behavior-provenance", "approved": len(approved_behaviors), "passed": not unsafe})
    if not plan: integration_warnings.append("Integration validated against embedded plan feature IDs; no external plan supplied")

    runtime_result = {"status": "not-run", "reason": "No Bedrock runtime adapter was invoked; static and integration validation do not imply activation"}
    if runtime: runtime_result = {"status": "not-run", "reason": "Runtime execution is not implemented by this validator; use a configured BDS runtime harness"}
    static = _result(errors, warnings, checks)
    integration = _result(integration_errors, integration_warnings, integration_checks)
    all_errors = errors + integration_errors
    all_warnings = warnings + integration_warnings
    return {"path": str(root), "manifest_count": len(manifests), "layers": {"static": static, "integration": integration, "runtime": runtime_result}, "errors": all_errors, "warnings": all_warnings, "valid": not all_errors}
