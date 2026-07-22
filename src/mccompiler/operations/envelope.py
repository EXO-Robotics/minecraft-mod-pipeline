from __future__ import annotations

import uuid
from typing import Any


SCHEMA_VERSION = "1.0.0"


class OperationError(ValueError):
    def __init__(self, code: str, message: str, *, details: Any = None):
        super().__init__(message)
        self.code = code
        self.details = details


def success(operation: str, result: Any, *, request_id: str | None, revision: int | None, artifacts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION, "request_id": request_id or str(uuid.uuid4()),
        "operation": operation, "ok": True, "project_revision": revision,
        "result": result, "diagnostics": [], "artifacts": artifacts or [],
    }


def failure(operation: str, code: str, message: str, *, request_id: str | None, revision: int | None = None, details: Any = None) -> dict[str, Any]:
    diagnostic = {"severity": "error", "code": code, "message": message}
    if details is not None:
        diagnostic["details"] = details
    return {
        "schema_version": SCHEMA_VERSION, "request_id": request_id or str(uuid.uuid4()),
        "operation": operation, "ok": False, "project_revision": revision,
        "result": None, "diagnostics": [diagnostic], "artifacts": [],
    }
