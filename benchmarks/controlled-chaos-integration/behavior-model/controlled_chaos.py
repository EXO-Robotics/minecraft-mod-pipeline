"""Pure qualification model for the Controlled Chaos integration slice.

This module deliberately models invariants, not Bedrock APIs. Runtime adapters
must independently prove that the same transitions occur in Minecraft.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
import random
from typing import Any, Mapping


STATE_VERSION = 2


class BossPhase(IntEnum):
    LOCKED = 0
    ONE = 1
    TWO = 2
    THREE = 3
    COMPLETE = 4


@dataclass(frozen=True)
class HostileDamageReceipt:
    execution: int
    attacker_id: str
    target_id: str
    health_before: int
    health_after: int
    expected_damage: int
    actual_damage: int
    damage_source: str
    event_adapter_observed: bool
    internal_handler_observed: bool
    entity_hurt_observed: bool
    entity_death_observed: bool
    timed_out: bool
    cleanup_succeeded: bool

    @property
    def passed(self) -> bool:
        return (
            self.actual_damage == self.expected_damage
            and self.event_adapter_observed
            and self.internal_handler_observed
            and self.entity_hurt_observed
            and not self.timed_out
            and self.cleanup_succeeded
        )


@dataclass
class PlayerState:
    unlock: bool = False
    elite_reward: bool = False
    boss_reward: bool = False
    cooldown_until: int = 0


@dataclass
class WorldState:
    version: int = STATE_VERSION
    boss_phase: BossPhase = BossPhase.LOCKED
    structure_complete: bool = False
    chaos_count: int = 0
    active_entities: set[str] = field(default_factory=set)
    players: dict[str, PlayerState] = field(default_factory=dict)


class ControlledChaosModel:
    """Deterministic state machine with bounded objects and idempotent rewards."""

    CHAOS_OUTCOMES = ("fireflies", "low_gravity", "loot_rain")
    MAX_CHAOS_OCCURRENCES = 3

    def __init__(self, *, seed: int, active_entity_limit: int = 8) -> None:
        if active_entity_limit < 1:
            raise ValueError("active_entity_limit must be positive")
        self.state = WorldState()
        self._random = random.Random(seed)
        self._active_entity_limit = active_entity_limit

    def player(self, player_id: str) -> PlayerState:
        if not player_id:
            raise ValueError("player_id cannot be empty")
        return self.state.players.setdefault(player_id, PlayerState())

    def award_elite(self, player_id: str) -> bool:
        player = self.player(player_id)
        if player.elite_reward:
            return False
        player.elite_reward = True
        if self.state.boss_phase is BossPhase.LOCKED:
            self.state.boss_phase = BossPhase.ONE
        return True

    def advance_boss(self, phase: BossPhase) -> bool:
        expected = BossPhase(int(self.state.boss_phase) + 1)
        if phase is not expected:
            return False
        self.state.boss_phase = phase
        return True

    def complete_boss(self, participant_ids: list[str]) -> dict[str, bool]:
        if self.state.boss_phase is not BossPhase.THREE:
            return {player_id: False for player_id in participant_ids}
        self.state.boss_phase = BossPhase.COMPLETE
        awarded: dict[str, bool] = {}
        for player_id in dict.fromkeys(participant_ids):
            player = self.player(player_id)
            awarded[player_id] = not player.boss_reward
            player.boss_reward = True
            player.unlock = True
        return awarded

    def use_weapon(self, player_id: str, *, tick: int, cooldown_ticks: int = 20) -> bool:
        player = self.player(player_id)
        if tick < player.cooldown_until:
            return False
        player.cooldown_until = tick + cooldown_ticks
        return True

    def select_chaos(self) -> str | None:
        if self.state.chaos_count >= self.MAX_CHAOS_OCCURRENCES:
            return None
        self.state.chaos_count += 1
        return self.CHAOS_OUTCOMES[self._random.randrange(len(self.CHAOS_OUTCOMES))]

    def spawn_bounded(self, entity_id: str) -> bool:
        if entity_id in self.state.active_entities:
            return False
        if len(self.state.active_entities) >= self._active_entity_limit:
            return False
        self.state.active_entities.add(entity_id)
        return True

    def cleanup(self) -> int:
        removed = len(self.state.active_entities)
        self.state.active_entities.clear()
        return removed

    def snapshot(self) -> dict[str, Any]:
        return {
            "version": STATE_VERSION,
            "boss_phase": int(self.state.boss_phase),
            "structure_complete": self.state.structure_complete,
            "chaos_count": self.state.chaos_count,
            "players": {
                player_id: {
                    "unlock": player.unlock,
                    "elite_reward": player.elite_reward,
                    "boss_reward": player.boss_reward,
                    "cooldown_until": player.cooldown_until,
                }
                for player_id, player in sorted(self.state.players.items())
            },
        }

    @classmethod
    def restore(cls, raw: object, *, seed: int) -> ControlledChaosModel:
        model = cls(seed=seed)
        if not isinstance(raw, Mapping):
            return model
        try:
            version = int(raw.get("version", 1))
            if version not in (1, STATE_VERSION):
                return model
            model.state.boss_phase = BossPhase(int(raw.get("boss_phase", 0)))
            model.state.structure_complete = bool(raw.get("structure_complete", False))
            model.state.chaos_count = max(0, int(raw.get("chaos_count", 0)))
            players = raw.get("players", {})
            if not isinstance(players, Mapping):
                return cls(seed=seed)
            for player_id, state in players.items():
                if not isinstance(player_id, str) or not isinstance(state, Mapping):
                    return cls(seed=seed)
                # V1 stored the unlock under ``power`` and had no reward flags.
                unlock = bool(state.get("unlock", state.get("power", False)))
                model.state.players[player_id] = PlayerState(
                    unlock=unlock,
                    elite_reward=bool(state.get("elite_reward", False)),
                    boss_reward=bool(state.get("boss_reward", unlock)),
                    cooldown_until=max(0, int(state.get("cooldown_until", 0))),
                )
        except (TypeError, ValueError):
            return cls(seed=seed)
        return model


def run_hostile_damage(execution: int, *, health: int = 20, damage: int = 4) -> HostileDamageReceipt:
    """Run one deterministic hostile-damage model execution."""
    after = max(0, health - damage)
    return HostileDamageReceipt(
        execution=execution,
        attacker_id="controlled_chaos:regional_hostile",
        target_id="qualification:player_a",
        health_before=health,
        health_after=after,
        expected_damage=damage,
        actual_damage=health - after,
        damage_source="entity_attack",
        event_adapter_observed=True,
        internal_handler_observed=True,
        entity_hurt_observed=True,
        entity_death_observed=after == 0,
        timed_out=False,
        cleanup_succeeded=True,
    )
