from __future__ import annotations

import unittest

from mccompiler.persistence import StateMigrationRegistry, StateSchema, validate_identifier_evolution


class PersistenceTests(unittest.TestCase):
    def test_migrations_are_ordered_and_journaled(self) -> None:
        schema = StateSchema("showcase", 3, ("showcase:rank", "showcase:machine_progress"))
        registry = StateMigrationRegistry(schema)
        registry.register(1, lambda state: {**state, "schema_version": 2, "rank": state.pop("level", 0)})
        registry.register(2, lambda state: {**state, "schema_version": 3, "machine_progress": 0})
        result = registry.migrate({"schema_version": 1, "world_id": "world-a", "level": 4})
        self.assertEqual(result["schema_version"], 3)
        self.assertEqual(result["rank"], 4)
        self.assertEqual(result["machine_progress"], 0)
        self.assertEqual(
            result["migration_journal"],
            [
                {"from": 1, "to": 2, "status": "applied"},
                {"from": 2, "to": 3, "status": "applied"},
            ],
        )

    def test_missing_route_fails_without_claiming_upgrade(self) -> None:
        registry = StateMigrationRegistry(StateSchema("showcase", 2, ("showcase:rank",)))
        with self.assertRaisesRegex(ValueError, "missing persistent-state migration"):
            registry.migrate({"schema_version": 1, "world_id": "world-a"})

    def test_migration_cannot_change_world_identity(self) -> None:
        registry = StateMigrationRegistry(StateSchema("showcase", 2, ("showcase:rank",)))
        registry.register(1, lambda state: {**state, "schema_version": 2, "world_id": "other"})
        with self.assertRaisesRegex(ValueError, "changed world identity"):
            registry.migrate({"schema_version": 1, "world_id": "world-a"})

    def test_identifier_removal_requires_explicit_handling(self) -> None:
        previous = StateSchema("showcase", 1, ("showcase:rank", "showcase:old_machine"))
        current = StateSchema("showcase", 2, ("showcase:rank",))
        errors = validate_identifier_evolution(previous, current)
        self.assertTrue(any("showcase:old_machine" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
