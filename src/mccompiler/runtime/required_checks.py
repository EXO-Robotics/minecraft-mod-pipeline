from __future__ import annotations

from collections.abc import Iterable

from .model import CheckClassification


_MARKETPLACE_CHECKS: dict[str, CheckClassification] = {
    "handler.dispatch": CheckClassification.HANDLER,
    "adapter.real_action": CheckClassification.ADAPTER_INTEGRATION,
    "gameplay.expected_behavior": CheckClassification.GAMEPLAY,
    "persistence.migration": CheckClassification.PERSISTENCE,
    "persistence.reconnect": CheckClassification.PERSISTENCE,
    "multiplayer.player_isolation": CheckClassification.MULTIPLAYER,
    "console.controller_gameplay": CheckClassification.CONSOLE,
}


def required_checks(
    profile: str = "MARKETPLACE_ADDON_STABLE",
    *,
    classifications: Iterable[CheckClassification | str] | None = None,
) -> dict[str, CheckClassification]:
    if profile != "MARKETPLACE_ADDON_STABLE":
        raise ValueError(f"Unknown runtime evidence profile: {profile}")
    if classifications is None:
        return dict(_MARKETPLACE_CHECKS)
    selected = {CheckClassification(value) for value in classifications}
    return {check_id: classification for check_id, classification in _MARKETPLACE_CHECKS.items() if classification in selected}
