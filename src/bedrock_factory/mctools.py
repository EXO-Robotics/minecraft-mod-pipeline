"""Fail-closed parsing for exact MCTools validation summaries."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any


COUNT_FIELDS = ("errors", "warnings", "recommendations")
PLAIN_SUMMARY = re.compile(
    r"^\s*errors?\s*[:=]\s*(?P<errors>\d+)\s*[,;]?\s+"
    r"warnings?\s*[:=]\s*(?P<warnings>\d+)\s*[,;]?\s+"
    r"recommendations?\s*[:=]\s*(?P<recommendations>\d+)\s*$",
    re.IGNORECASE,
)


class MCToolsError(ValueError):
    pass


def _mappings(value: Any) -> list[Mapping[str, Any]]:
    found: list[Mapping[str, Any]] = []
    pending = [value]
    visited = 0
    while pending:
        current = pending.pop()
        visited += 1
        if visited > 100_000:
            raise MCToolsError("structured MCTools output is too large")
        if isinstance(current, Mapping):
            found.append(current)
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)
    return found


def _counts(summary: Mapping[str, Any]) -> dict[str, int]:
    missing = [field for field in COUNT_FIELDS if field not in summary]
    if missing:
        raise MCToolsError("validation summary is missing: " + ", ".join(missing))
    values = {}
    for field in COUNT_FIELDS:
        value = summary[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise MCToolsError(f"{field} must be a nonnegative integer")
        values[field] = value
    return values


def parse_mctools_counts(log: str) -> dict[str, int]:
    decoded: list[Any] = []
    stripped = log.strip()
    if stripped:
        try:
            decoded.append(json.loads(stripped))
        except json.JSONDecodeError:
            for line in log.splitlines():
                candidate = line.strip()
                if not candidate or candidate[0] not in "[{":
                    continue
                try:
                    decoded.append(json.loads(candidate))
                except json.JSONDecodeError as exc:
                    if re.search(r'"(?:errors|warnings|recommendations)"\s*:', candidate, re.IGNORECASE):
                        raise MCToolsError("malformed structured count authority") from exc
    mappings = [mapping for value in decoded for mapping in _mappings(value)]
    summaries = [
        value for value in mappings
        if value.get("command") == "validate" and any(field in value for field in COUNT_FIELDS)
    ]
    if not summaries:
        summaries = [value for value in mappings if all(field in value for field in COUNT_FIELDS)]
    if len(summaries) > 1:
        raise MCToolsError("multiple structured validation summaries are ambiguous")
    if len(summaries) == 1:
        values = _counts(summaries[0])
        return {"error_count": values["errors"], "warning_count": values["warnings"], "recommendation_count": values["recommendations"]}
    if any("errors" in value for value in mappings):
        _counts(next(value for value in mappings if "errors" in value))
    plain = [match for line in log.splitlines() if (match := PLAIN_SUMMARY.fullmatch(line))]
    if len(plain) != 1:
        raise MCToolsError("output contains no single exact validation summary")
    return {"error_count": int(plain[0].group("errors")), "warning_count": int(plain[0].group("warnings")), "recommendation_count": int(plain[0].group("recommendations"))}


def validate_mctools_result(result: Mapping[str, Any], *, required_version: str = "0.17.6") -> None:
    if result.get("version") != required_version:
        raise MCToolsError("MCTools version mismatch")
    if result.get("exit_code") != 0:
        raise MCToolsError("MCTools exited nonzero")
    if result.get("error_count") != 0:
        raise MCToolsError("MCTools reported validation errors")
    if not re.fullmatch(r"[0-9a-f]{64}", str(result.get("log_sha256", ""))):
        raise MCToolsError("MCTools log is not hash-bound")
