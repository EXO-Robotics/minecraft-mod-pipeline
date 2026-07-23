from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .acceptance import EvidenceState


DIMENSIONS = (
    "script_tick_workload", "active_entities", "pathfinding_pressure",
    "projectiles", "particles", "texture_memory", "geometry_complexity",
    "animation_controller_complexity", "persistence_growth",
    "multiplayer_multiplier", "cleanup_latency", "worst_credible_scene",
)


@dataclass(frozen=True)
class Budget:
    hard_caps: Mapping[str, int]
    reserves: Mapping[str, int]
    current_scope_units: int = 62
    hard_ceiling_units: int = 80
    planning_ceiling_units: int = 64
    protected_reserve_units: int = 18
    protected_minimum_units: int = 16

    def __post_init__(self) -> None:
        if set(self.hard_caps) != set(DIMENSIONS) or set(self.reserves) != set(DIMENSIONS):
            raise ValueError(f"budget dimensions must be exactly {DIMENSIONS}")
        if self.current_scope_units != 62 or self.hard_ceiling_units != 80:
            raise ValueError("authoritative global scope must remain 62/80")
        if self.current_scope_units > self.planning_ceiling_units:
            raise ValueError("current scope exceeds planning ceiling")
        if self.hard_ceiling_units - self.current_scope_units != self.protected_reserve_units:
            raise ValueError("18-unit reserve must remain explicit")
        if self.protected_reserve_units < self.protected_minimum_units:
            raise ValueError("reserve is below protected minimum")
        for dimension in DIMENSIONS:
            cap, reserve = self.hard_caps[dimension], self.reserves[dimension]
            if cap < 0 or reserve < 0 or reserve > cap:
                raise ValueError(f"invalid {dimension} hard cap or reserve")

    def planning_cap(self, dimension: str) -> int:
        return self.hard_caps[dimension] - self.reserves[dimension]


@dataclass(frozen=True)
class ForestElement:
    element_id: str
    priority: int
    costs: Mapping[str, int]
    scope_units: int
    dependencies: tuple[str, ...] = ()
    evidence: EvidenceState = EvidenceState.CONTRACT_ONLY
    contract_ref: str = ""
    qualification_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.element_id or self.scope_units < 0:
            raise ValueError("forest element id and nonnegative scope units required")
        if set(self.costs) != set(DIMENSIONS) or any(v < 0 for v in self.costs.values()):
            raise ValueError(f"element costs must be nonnegative and exactly {DIMENSIONS}")


class ProductionWavePlanner:
    def __init__(self, budget: Budget, *, max_waves: int = 12) -> None:
        self.budget, self.max_waves = budget, max_waves

    def plan(self, elements: Iterable[ForestElement]) -> dict[str, object]:
        rows = tuple(elements)
        by_id = {row.element_id: row for row in rows}
        if len(by_id) != len(rows):
            raise ValueError("duplicate forest element id")
        if sum(row.scope_units for row in rows) > self.budget.current_scope_units:
            raise ValueError("forest allocation exceeds authoritative 62-unit scope")
        for row in rows:
            if not set(row.dependencies) <= set(by_id):
                raise ValueError(f"{row.element_id} has unknown dependencies")
            for dimension in DIMENSIONS:
                if row.costs[dimension] > self.budget.planning_cap(dimension):
                    raise ValueError(f"{row.element_id} exceeds PS4 {dimension} planning cap")
        remaining: set[str] = set(by_id)
        completed: set[str] = set()
        waves: list[dict[str, object]] = []
        while remaining and len(waves) < self.max_waves:
            usage = {dimension: 0 for dimension in DIMENSIONS}
            selected: list[str] = []
            for row in sorted(
                (by_id[item] for item in remaining),
                key=lambda item: (
                    0 if item.evidence is EvidenceState.SERVER_QUALIFIED else 1,
                    -item.priority, item.element_id,
                ),
            ):
                if not set(row.dependencies) <= completed:
                    continue
                if all(usage[d] + row.costs[d] <= self.budget.planning_cap(d) for d in DIMENSIONS):
                    selected.append(row.element_id)
                    for dimension in DIMENSIONS:
                        usage[dimension] += row.costs[dimension]
            if not selected:
                break
            remaining.difference_update(selected)
            completed.update(selected)
            waves.append({
                "wave": len(waves) + 1, "elements": selected, "usage": usage,
                "reserve_preserved": {
                    d: self.budget.hard_caps[d] - usage[d] for d in DIMENSIONS
                },
            })
        return {
            "schema_version": "1.0.0", "target": "PS4_PLANNING_PROXY",
            "weights_label": "UNCALIBRATED_PS4_PLANNING_PROXY_INPUTS",
            "authoritative_scope": {
                "current": 62, "hard_ceiling": 80, "planning_ceiling": 64,
                "reserve": 18, "protected_minimum": 16,
                "reserve_consumed": False,
            },
            "waves": waves, "deferred": sorted(remaining),
            "hard_caps": dict(self.budget.hard_caps),
            "required_reserves": dict(self.budget.reserves),
            "physical_ps4_verified": False,
        }
