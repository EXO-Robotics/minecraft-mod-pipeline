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
    if not isinstance(source, list):
        source = []
    severity_map = {str(k).lower(): str(v).lower() for k, v in (policy.get("severity_map") or {}).items()}
    for raw in source:
        if not isinstance(raw, Mapping):
            continue
        severity = severity_map.get(str(raw.get("severity", "warning")).lower(), str(raw.get("severity", "warning")).lower())
        findings.append({
            "suite": str(raw.get("suite") or "unknown"), "severity": severity,
            "code": str(raw.get("code") or "UNKNOWN"), "path": str(raw.get("path") or ""),
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
    command = [str(executable), *lock.get("validate_args", ["validate"]), str(Path(project).resolve())]
    for suite in selected:
        command.extend([str(lock.get("suite_flag", "--suite")), str(suite)])
    result = runner(command, capture_output=True, text=True, check=False)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Creator Tools did not return JSON") from exc
    normalized = normalize_creator_tools_output(payload, version=actual_version, suites=selected, policy=policy)
    normalized["creator_tools"]["exit_code"] = result.returncode
    normalized["creator_tools"]["command"] = command
    if result.returncode != 0 and normalized["creator_tools"]["errors"] == 0:
        normalized["creator_tools"]["errors"] = 1
        normalized["creator_tools"]["findings"].append({"suite": "tool", "severity": "error", "code": "NONZERO_EXIT", "path": "", "message": "Creator Tools exited nonzero without an error diagnostic"})
        normalized["passed"] = False
    return normalized
