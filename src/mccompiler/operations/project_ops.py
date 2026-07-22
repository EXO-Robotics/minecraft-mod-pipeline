from __future__ import annotations

from typing import Any

from mccompiler.project.status import blocking_failures, next_task, project_status, unresolved_work
from mccompiler.project.store import ProjectStore


def create_conversion_project(project: str, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    store = ProjectStore.create(project, name=parameters.get("name"), target_profile=parameters.get("target_profile", "MARKETPLACE_ADDON_STABLE"))
    return project_status(store), store, [{"path": "project.yaml", "kind": "project_manifest"}]


def open_conversion_project(project: str, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    store = ProjectStore.open(project)
    return project_status(store), store, []


def get_project_status(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return project_status(store), store, []


def list_unresolved_work(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return {"work": unresolved_work(store)}, store, []


def list_blocking_failures(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return {"failures": blocking_failures(store)}, store, []


def get_next_recommended_task(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return {"task": next_task(store)}, store, []
