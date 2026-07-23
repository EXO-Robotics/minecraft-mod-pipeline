from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, Mapping


class EvidenceState(StrEnum):
    PLANNED = "PLANNED"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    IMPLEMENTED = "IMPLEMENTED"
    STATIC_QUALIFIED = "STATIC_QUALIFIED"
    SERVER_QUALIFIED = "SERVER_QUALIFIED"
    CLIENT_QUALIFIED = "CLIENT_QUALIFIED"
    PHYSICAL_QUALIFIED = "PHYSICAL_QUALIFIED"


@dataclass(frozen=True)
class AcceptanceNode:
    node_id: str
    weight: int
    dependencies: tuple[str, ...] = ()
    evidence: EvidenceState = EvidenceState.CONTRACT_ONLY
    required: EvidenceState = EvidenceState.SERVER_QUALIFIED
    mandatory: bool = False

    def __post_init__(self) -> None:
        if not self.node_id or self.weight <= 0:
            raise ValueError("acceptance nodes require an id and positive weight")
        if self.node_id in self.dependencies:
            raise ValueError(f"{self.node_id} cannot depend on itself")


_LEVEL = {
    EvidenceState.PLANNED: 0,
    EvidenceState.CONTRACT_ONLY: 1,
    EvidenceState.IMPLEMENTED: 2,
    EvidenceState.STATIC_QUALIFIED: 3,
    EvidenceState.SERVER_QUALIFIED: 4,
    EvidenceState.CLIENT_QUALIFIED: 5,
    EvidenceState.PHYSICAL_QUALIFIED: 6,
}


class AcceptanceGraph:
    def __init__(self, nodes: Iterable[AcceptanceNode]) -> None:
        materialized = tuple(nodes)
        self.nodes: Mapping[str, AcceptanceNode] = {
            node.node_id: node for node in materialized
        }
        if len(self.nodes) != len(materialized):
            raise ValueError("duplicate acceptance node id")
        for node in self.nodes.values():
            missing = sorted(set(node.dependencies) - set(self.nodes))
            if missing:
                raise ValueError(f"{node.node_id} has unknown dependencies: {missing}")
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visiting:
                raise ValueError("acceptance graph contains a cycle")
            if node_id in visited:
                return
            visiting.add(node_id)
            for dependency in self.nodes[node_id].dependencies:
                visit(dependency)
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in sorted(self.nodes):
            visit(node_id)

    def accepted(self, node_id: str) -> bool:
        node = self.nodes[node_id]
        return (
            _LEVEL[node.evidence] >= _LEVEL[node.required]
            and all(self.accepted(dependency) for dependency in node.dependencies)
        )

    def weighted_coverage(self) -> dict[str, int]:
        total = sum(node.weight for node in self.nodes.values())
        accepted = sum(
            node.weight for node in self.nodes.values() if self.accepted(node.node_id)
        )
        return {
            "accepted_weight": accepted,
            "total_weight": total,
            "basis_points": accepted * 10_000 // total if total else 0,
        }

    def coverage_report(self) -> dict[str, object]:
        names = (
            ("planned_coverage", EvidenceState.PLANNED),
            ("contracted_coverage", EvidenceState.CONTRACT_ONLY),
            ("implemented_coverage", EvidenceState.IMPLEMENTED),
            ("static_qualified_coverage", EvidenceState.STATIC_QUALIFIED),
            ("server_qualified_coverage", EvidenceState.SERVER_QUALIFIED),
            ("client_qualified_coverage", EvidenceState.CLIENT_QUALIFIED),
            ("physical_qualified_coverage", EvidenceState.PHYSICAL_QUALIFIED),
        )
        total = sum(node.weight for node in self.nodes.values())
        metrics: dict[str, dict[str, object]] = {}
        for name, threshold in names:
            covered = sum(
                node.weight for node in self.nodes.values()
                if _LEVEL[node.evidence] >= _LEVEL[threshold]
                and all(
                    _LEVEL[self.nodes[dependency].evidence] >= _LEVEL[threshold]
                    for dependency in node.dependencies
                )
            )
            mandatory_pending = sorted(
                node.node_id for node in self.nodes.values()
                if node.mandatory and _LEVEL[node.evidence] < _LEVEL[threshold]
            )
            metrics[name] = {
                "covered_weight": covered,
                "total_weight": total,
                "basis_points": covered * 10_000 // total if total else 0,
                "status": "BLOCKED_MANDATORY_NODES"
                if mandatory_pending else "SATISFIED",
                "mandatory_pending": mandatory_pending,
            }
        return {"schema_version": "1.0.0", "metrics": metrics}

    def blockers(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for node_id, node in sorted(self.nodes.items()):
            reasons: list[str] = []
            if _LEVEL[node.evidence] < _LEVEL[node.required]:
                reasons.append(f"requires {node.required.value}; has {node.evidence.value}")
            reasons.extend(
                f"dependency not accepted: {dependency}"
                for dependency in node.dependencies
                if not self.accepted(dependency)
            )
            if reasons:
                result[node_id] = reasons
        return result
