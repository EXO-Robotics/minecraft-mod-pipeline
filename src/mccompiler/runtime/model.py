from __future__ import annotations

from enum import StrEnum


class CheckClassification(StrEnum):
    HANDLER = "handler"
    ADAPTER_INTEGRATION = "adapter_integration"
    GAMEPLAY = "gameplay"
    PERSISTENCE = "persistence"
    MULTIPLAYER = "multiplayer"
    CONSOLE = "console"


class CheckStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_RUN = "NOT_RUN"
    BLOCKED = "BLOCKED"


class RuntimeEvidenceError(ValueError):
    pass
