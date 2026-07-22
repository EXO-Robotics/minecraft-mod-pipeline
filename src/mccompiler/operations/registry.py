from __future__ import annotations

from typing import Any, Callable

from mccompiler.project.store import ProjectError, ProjectStore

from . import analysis_ops, planning_ops, project_ops
from .envelope import OperationError, failure, success


Handler = Callable[..., tuple[Any, ProjectStore, list[dict[str, Any]]]]


class OperationRegistry:
    def __init__(self) -> None:
        self.handlers: dict[str, Handler] = {
            "create_conversion_project": project_ops.create_conversion_project,
            "open_conversion_project": project_ops.open_conversion_project,
            "get_project_status": project_ops.get_project_status,
            "list_unresolved_work": project_ops.list_unresolved_work,
            "list_unresolved": project_ops.list_unresolved_work,
            "list_blocking_failures": project_ops.list_blocking_failures,
            "list_blocking": project_ops.list_blocking_failures,
            "get_next_recommended_task": project_ops.get_next_recommended_task,
            "get_next_task": project_ops.get_next_recommended_task,
            "scan_mod": analysis_ops.scan_mod, "list_mods": analysis_ops.list_mods,
            "list_content": analysis_ops.list_content, "inspect_behavior": analysis_ops.inspect_behavior,
            "show_evidence": analysis_ops.show_evidence, "set_strategy": planning_ops.set_strategy,
        }

    def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(request, dict):
            return failure("<invalid>", "INVALID_REQUEST", "Operation request must be a JSON object", request_id=None)
        operation = request.get("operation")
        request_id = request.get("request_id")
        unknown = sorted(set(request) - {"schema_version", "request_id", "operation", "project", "parameters", "expected_revision"})
        if unknown:
            return failure(str(operation or "<invalid>"), "INVALID_REQUEST", f"Unknown request fields: {', '.join(unknown)}", request_id=request_id)
        if request.get("schema_version") != "1.0.0":
            return failure(str(operation or "<invalid>"), "UNSUPPORTED_REQUEST_SCHEMA", "schema_version must be 1.0.0", request_id=request_id)
        if operation not in self.handlers:
            return failure(str(operation or "<missing>"), "UNKNOWN_OPERATION", f"Unknown operation: {operation}", request_id=request_id)
        project = request.get("project")
        if not isinstance(project, str) or not project:
            return failure(operation, "INVALID_REQUEST", "project must be a non-empty path", request_id=request_id)
        parameters = request.get("parameters", {})
        if not isinstance(parameters, dict):
            return failure(operation, "INVALID_REQUEST", "parameters must be an object", request_id=request_id)
        expected_revision = request.get("expected_revision")
        if expected_revision is not None and (isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 1):
            return failure(operation, "INVALID_REQUEST", "expected_revision must be a positive integer", request_id=request_id)
        try:
            if operation == "create_conversion_project":
                result, store, artifacts = self.handlers[operation](project, parameters, request.get("expected_revision"))
            elif operation == "open_conversion_project":
                result, store, artifacts = self.handlers[operation](project, parameters, request.get("expected_revision"))
            else:
                store = ProjectStore.open(project)
                result, store, artifacts = self.handlers[operation](store, parameters, request.get("expected_revision"))
            return success(operation, result, request_id=request_id, revision=store.revision, artifacts=artifacts)
        except ProjectError as exc:
            revision = None
            try:
                revision = ProjectStore.open(project).revision
            except ProjectError:
                pass
            return failure(operation, exc.code, str(exc), request_id=request_id, revision=revision)
        except OperationError as exc:
            return failure(operation, exc.code, str(exc), request_id=request_id, details=exc.details)
        except Exception as exc:
            return failure(operation, "INTERNAL_ERROR", str(exc), request_id=request_id)


def execute_request(request: dict[str, Any]) -> dict[str, Any]:
    return OperationRegistry().execute(request)
