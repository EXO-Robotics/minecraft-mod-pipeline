from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence, cast


Runner = Callable[..., subprocess.CompletedProcess[str]]


def load_creator_tools_lock(path: str | Path | None = None) -> dict[str, Any]:
    lock_path = Path(path) if path else Path(__file__).with_name("creator-tools.lock.json")
    return cast(dict[str, Any], json.loads(lock_path.read_text(encoding="utf-8")))


def load_creator_tools_policy(path: str | Path | None = None) -> dict[str, Any]:
    policy_path = Path(path) if path else Path(__file__).with_name("creator-tools-policy.json")
    return cast(dict[str, Any], json.loads(policy_path.read_text(encoding="utf-8")))


def discover_creator_tools(lock: Mapping[str, Any], *, search_path: str | None = None) -> Path | None:
    for executable in lock.get("executables", []):
        found = shutil.which(str(executable), path=search_path)
        if found:
            return Path(found).resolve()
    return None


def normalize_creator_tools_output(
    payload: Mapping[str, Any], *, version: str, suites: Sequence[str], policy: Mapping[str, Any]
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    source = payload.get("diagnostics", payload.get("findings", []))
    if not source and isinstance(payload.get("projects"), list):
        source = [
            {**item, "suite": item.get("generatorId", "unknown"), "severity": item.get("type", "info")}
            for project in payload["projects"] if isinstance(project, Mapping)
            for item in project.get("items", []) if isinstance(item, Mapping)
        ]
    if not isinstance(source, list):
        source = []
    severity_map = {str(k).lower(): str(v).lower() for k, v in (policy.get("severity_map") or {}).items()}
    for raw in source:
        if not isinstance(raw, Mapping):
            continue
        raw_severity = str(raw.get("severity", "warning")).lower()
        type_severity = {"error": "error", "warning": "warning", "warn": "warning"}.get(raw_severity, "info")
        severity = severity_map.get(raw_severity, type_severity)
        findings.append({
            "suite": str(raw.get("suite") or "unknown"), "severity": severity,
            "code": str(raw.get("code") or raw.get("generatorId") or "UNKNOWN"), "path": str(raw.get("path") or ""),
            "message": str(raw.get("message") or ""),
        })
    findings.sort(key=lambda row: (row["suite"], row["severity"], row["code"], row["path"], row["message"]))
    errors = sum(row["severity"] == "error" for row in findings)
    warnings = sum(row["severity"] == "warning" for row in findings)
    required = tuple(sorted(set(map(str, suites))))
    return {
        "creator_tools": {
            "version": version, "suites": list(required), "errors": errors, "warnings": warnings,
            "marketplace_approval_implied": False, "findings": findings,
        },
        "passed": errors == 0,
    }


def invoke_creator_tools(
    executable: str | Path,
    project: str | Path,
    *,
    lock: Mapping[str, Any],
    policy: Mapping[str, Any],
    suites: Sequence[str] | None = None,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    selected = tuple(suites or lock.get("required_suites", []))
    unknown = sorted(set(selected) - set(lock.get("allowed_suites", [])))
    if unknown:
        raise ValueError(f"Unsupported Creator Tools suites: {', '.join(unknown)}")
    version_result = runner([str(executable), *lock.get("version_args", ["--version"])], capture_output=True, text=True, check=False)
    actual_version = version_result.stdout.strip()
    expected_version = str(lock.get("version"))
    if version_result.returncode != 0 or actual_version != expected_version:
        raise RuntimeError(f"Creator Tools version mismatch: expected {expected_version}, got {actual_version or '<unavailable>'}")
    payloads: list[Mapping[str, Any]] = []
    commands: list[list[str]] = []
    exit_codes: list[int] = []
    for suite in selected:
        resolved_project = Path(project).resolve()
        input_flag = "--input-file" if resolved_project.is_file() else "--input-folder"
        command = [
            str(executable), input_flag, str(resolved_project),
            *map(str, lock.get("global_validate_args", ["--offline", "--json", "--yes"])),
            "validate", str(suite),
        ]
        commands.append(command)
        result = runner(command, capture_output=True, text=True, check=False)
        exit_codes.append(result.returncode)
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Creator Tools did not return JSON for suite {suite}") from exc
        if not isinstance(parsed, Mapping):
            raise RuntimeError(f"Creator Tools returned a non-object result for suite {suite}")
        payloads.append(parsed)
    combined_findings: list[Any] = []
    for payload in payloads:
        source = payload.get("diagnostics", payload.get("findings", []))
        if isinstance(source, list) and source:
            combined_findings.extend(source)
        elif isinstance(payload.get("projects"), list):
            for project_result in payload["projects"]:
                if isinstance(project_result, Mapping) and isinstance(project_result.get("items"), list):
                    combined_findings.extend(project_result["items"])
    normalized = normalize_creator_tools_output({"projects": [{"items": combined_findings}]}, version=actual_version, suites=selected, policy=policy)
    normalized["creator_tools"]["exit_codes"] = exit_codes
    normalized["creator_tools"]["commands"] = commands
    for suite, exit_code in zip(selected, exit_codes):
        if exit_code != 0 and not any(row["severity"] == "error" and row["suite"] == suite for row in normalized["creator_tools"]["findings"]):
            normalized["creator_tools"]["errors"] += 1
            normalized["creator_tools"]["findings"].append({"suite": suite, "severity": "error", "code": "NONZERO_EXIT", "path": "", "message": "Creator Tools exited nonzero without an error diagnostic"})
            normalized["passed"] = False
    return normalized
