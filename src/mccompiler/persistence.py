from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


Migration = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class StateSchema:
    namespace: str
    version: int
    identifiers: tuple[str, ...]

    def validate(self) -> None:
        if not self.namespace or ":" in self.namespace:
            raise ValueError("state namespace must be a non-empty pack namespace")
        if self.version < 1:
            raise ValueError("state schema version must be positive")
        if len(set(self.identifiers)) != len(self.identifiers):
            raise ValueError("state identifiers must be unique")
        for identifier in self.identifiers:
            if not identifier.startswith(f"{self.namespace}:"):
                raise ValueError(f"state identifier is outside namespace: {identifier}")


class StateMigrationRegistry:
    def __init__(self, schema: StateSchema):
        schema.validate()
        self.schema = schema
        self._migrations: dict[int, Migration] = {}

    def register(self, source_version: int, migration: Migration) -> None:
        if source_version < 1 or source_version >= self.schema.version:
            raise ValueError("migration source version is outside the schema route")
        if source_version in self._migrations:
            raise ValueError(f"duplicate migration from version {source_version}")
        self._migrations[source_version] = migration

    def migrate(self, state: dict[str, Any]) -> dict[str, Any]:
        current = dict(state)
        version = current.get("schema_version")
        if not isinstance(version, int):
            raise ValueError("persistent state is missing integer schema_version")
        if version > self.schema.version:
            raise ValueError("persistent state was created by a newer Add-On version")
        journal = list(current.get("migration_journal") or [])
        while version < self.schema.version:
            migration = self._migrations.get(version)
            if migration is None:
                raise ValueError(f"missing persistent-state migration {version}->{version + 1}")
            before = dict(current)
            try:
                candidate = migration(dict(current))
            except Exception as exc:
                raise ValueError(f"persistent-state migration {version}->{version + 1} failed") from exc
            if not isinstance(candidate, dict):
                raise ValueError(f"persistent-state migration {version}->{version + 1} returned invalid state")
            if candidate.get("schema_version") != version + 1:
                raise ValueError(f"persistent-state migration {version}->{version + 1} did not advance exactly once")
            if before.get("world_id") != candidate.get("world_id"):
                raise ValueError("persistent-state migration changed world identity")
            journal.append({"from": version, "to": version + 1, "status": "applied"})
            current = candidate
            version += 1
        current["migration_journal"] = journal
        return current


def validate_identifier_evolution(previous: StateSchema, current: StateSchema) -> list[str]:
    previous.validate()
    current.validate()
    errors: list[str] = []
    if previous.namespace != current.namespace:
        errors.append("persistent-state namespace cannot change")
    if current.version <= previous.version:
        errors.append("persistent-state schema version must increase")
    removed = sorted(set(previous.identifiers) - set(current.identifiers))
    if removed:
        errors.append("removed identifiers require explicit safe-removal records: " + ", ".join(removed))
    return errors

