"""Production-safe workload contracts for the SF factory decomposition.

This module deliberately contains no source inventory, authority locator, or
private evidence identifier.  Its output is suitable for crossing the
clean-room boundary into task-pack construction.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA_VERSION = "1.0.0"
WORKLOAD_IDS = tuple(f"SF-T{number}" for number in range(1, 13))
ALLOWED_RECONSTRUCTION_STRATEGIES = (
    "NATIVE_MAPPING",
    "BOUNDED_REDESIGN",
    "ORIGINAL_SUBSTITUTE",
    "DEFERRED",
    "BLOCKED",
)
ACCEPTANCE_OWNERS = {
    "WORKER_LOCAL": "feature_producer",
    "T1_MECHANICAL_PREFLIGHT": "t1_preflight_tester",
    "STABLE_BDS": "bds_tester",
    "T10_PRIVATE_AUDIT": "independent_auditor",
    "T2_SHARED_ADAPTER": "t2_adapter_owner",
    "INTEGRATION": "segment_integrator",
    "DESKTOP_CLIENT": "client_qa",
    "REALMS": "realms_qa",
    "CONTROLLER": "controller_qa",
    "SPLIT_SCREEN": "multiplayer_qa",
    "PHYSICAL_PS4": "console_qa",
}
EXTERNAL_ACCEPTANCE_CLASSES = frozenset(ACCEPTANCE_OWNERS) - {"WORKER_LOCAL"}

_REQUIRED_FIELDS = (
    "workload_id",
    "title",
    "product_scope",
    "player_facing_contracts",
    "inputs_produced_by_other_workloads",
    "outputs_consumed_by_other_workloads",
    "shared_runtime_requirements",
    "asset_contract_ids",
    "behavior_contract_ids",
    "progression_nodes",
    "acceptance_tests",
    "performance_budget",
    "console_constraints",
    "multiplayer_constraints",
    "persistence_constraints",
    "known_platform_gaps",
    "allowed_reconstruction_strategies",
    "rights_constraints",
    "source_expression_included",
)
_LIST_FIELDS = (
    "product_scope",
    "player_facing_contracts",
    "inputs_produced_by_other_workloads",
    "outputs_consumed_by_other_workloads",
    "shared_runtime_requirements",
    "asset_contract_ids",
    "behavior_contract_ids",
    "progression_nodes",
    "console_constraints",
    "multiplayer_constraints",
    "persistence_constraints",
    "known_platform_gaps",
    "rights_constraints",
)
_NONEMPTY_LIST_FIELDS = frozenset(
    {
        "product_scope",
        "player_facing_contracts",
        "outputs_consumed_by_other_workloads",
        "shared_runtime_requirements",
        "behavior_contract_ids",
        "progression_nodes",
        "console_constraints",
        "multiplayer_constraints",
        "persistence_constraints",
        "rights_constraints",
    }
)
_BUDGET_FIELDS = {
    "profile",
    "script_tick_units_max",
    "active_entities_max",
    "persistent_records_max",
    "network_events_per_tick_max",
    "cleanup_ticks_max",
    "physical_console_verified",
}
_BUDGET_LIMITS = {
    "script_tick_units_max": (0, 100),
    "active_entities_max": (0, 128),
    "persistent_records_max": (0, 4096),
    "network_events_per_tick_max": (0, 256),
    "cleanup_ticks_max": (1, 1200),
}
_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
_ABSOLUTE_PATH = re.compile(
    r"(?:^|[\s='\"])(?:/(?:Users|home|private|tmp|var|Volumes|opt|etc)(?:/|$)|[A-Za-z]:[\\/])",
    re.IGNORECASE,
)
_HASH = re.compile(r"(?:\bhash(?:es|ed|ing)?\b|\bsha(?:-?256)?\b|\b[a-f0-9]{64}\b)", re.IGNORECASE)
_SOURCE_LOCATOR = re.compile(
    r"(?:(?:^|[\s/\\])(?:oracle|authority|downloads|decompiled)(?:[/\\])|"
    r"\.jar\b|\.class\b|\.zip\b|\.java\b|\.png\b|\.ogg\b|\.wav\b|"
    r"\b(?:archive|bytecode|decompil(?:e|ed|ation)|javap|classfile|coremod|forge|"
    r"curseforge|project\s+id|file\s+id|source\s+(?:tree|path|file|archive|asset|"
    r"texture|model|audio|image)|oracle\s+(?:path|file|archive)|manifest\.json)\b)",
    re.IGNORECASE,
)
_REPRODUCTION_DIRECTION = re.compile(
    r"\b(?:copy|extract|rip|trace|sample|lift|port)\b.{0,48}\b(?:source|oracle|"
    r"texture|model|sound|audio|code|asset|artwork)\b|"
    r"\b(?:pixel[- ]for[- ]pixel|source[- ]relative|match\s+the\s+original|"
    r"recreate\s+the\s+original|use\s+the\s+original)\b",
    re.IGNORECASE,
)
_JAVA_EXPRESSION = re.compile(
    r"(?:\b(?:net\.minecraft|java\.(?:lang|util)|func_[0-9]+|method_[0-9]+)\b|"
    r"\b(?:public|private|protected)\s+(?:static\s+)?(?:class|void|int|boolean)\b|"
    r"\b(?:GETFIELD|PUTFIELD|INVOKEVIRTUAL|INVOKESTATIC)\b)",
    re.IGNORECASE,
)
_BRANDING_OR_PROSE = re.compile(
    r"\b(?:sky\s*factory|darkosto|astral\s+sorcery|twilight\s+forest|"
    r"crafttweaker|modtweaker|contenttweaker|original\s+quest\s+(?:text|prose)|"
    r"quest\s+prose|logo|tagline)\b",
    re.IGNORECASE,
)


class SanitizedWorkloadError(ValueError):
    """Raised when a workload cannot cross the clean-room boundary."""

    def __init__(self, code: str, message: str, findings: Sequence[Mapping[str, str]] = ()):
        super().__init__(message)
        self.code = code
        self.findings = tuple(dict(finding) for finding in findings)


def _finding(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _walk_strings(value: Any, path: str = "$"):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, Mapping):
        for key in sorted(value):
            yield from _walk_strings(value[key], f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_strings(item, f"{path}[{index}]")


def _validate_safe_text(document: Mapping[str, Any], findings: list[dict[str, str]]) -> None:
    checks = (
        ("ABSOLUTE_PATH_PROHIBITED", _ABSOLUTE_PATH, "absolute paths are prohibited"),
        ("HASH_OR_SOURCE_LOCATOR_PROHIBITED", _HASH, "hashes and hash locators are prohibited"),
        ("SOURCE_LOCATOR_PROHIBITED", _SOURCE_LOCATOR, "source and archive locators are prohibited"),
        ("SOURCE_REPRODUCTION_DIRECTION_PROHIBITED", _REPRODUCTION_DIRECTION, "source-relative reproduction directions are prohibited"),
        ("JAVA_EXPRESSION_PROHIBITED", _JAVA_EXPRESSION, "Java or bytecode expression is prohibited"),
        ("BRANDING_OR_PROSE_PROHIBITED", _BRANDING_OR_PROSE, "branding and original prose are prohibited"),
    )
    for path, text in _walk_strings(document):
        for code, pattern, message in checks:
            if pattern.search(text):
                findings.append(_finding(code, path, message))


def validate_sanitized_workload(document: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a defensive canonical copy of one workload packet."""

    findings: list[dict[str, str]] = []
    if not isinstance(document, Mapping):
        raise SanitizedWorkloadError(
            "SANITIZED_WORKLOAD_INVALID",
            "workload packet must be an object",
            [_finding("INVALID_TYPE", "$", "object required")],
        )
    missing = sorted(set(_REQUIRED_FIELDS) - set(document))
    extra = sorted(set(document) - set(_REQUIRED_FIELDS))
    for field in missing:
        findings.append(_finding("REQUIRED_FIELD_MISSING", f"$.{field}", "required field is missing"))
    for field in extra:
        findings.append(_finding("UNKNOWN_FIELD", f"$.{field}", "unknown fields are prohibited"))

    workload_id = document.get("workload_id")
    if workload_id not in WORKLOAD_IDS:
        findings.append(_finding("INVALID_WORKLOAD_ID", "$.workload_id", "must identify SF-T1 through SF-T12"))
    title = document.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 100 or "\n" in title:
        findings.append(_finding("INVALID_TITLE", "$.title", "one concise non-empty title is required"))

    for field in _LIST_FIELDS:
        value = document.get(field)
        if not isinstance(value, list):
            findings.append(_finding("INVALID_FIELD_TYPE", f"$.{field}", "array of concise strings required"))
            continue
        if field in _NONEMPTY_LIST_FIELDS and not value:
            findings.append(_finding("EMPTY_REQUIRED_LIST", f"$.{field}", "at least one entry is required"))
        seen: set[str] = set()
        for index, item in enumerate(value):
            path = f"$.{field}[{index}]"
            if not isinstance(item, str) or not item.strip() or item != item.strip() or len(item) > 240 or "\n" in item:
                findings.append(_finding("INVALID_LIST_ENTRY", path, "concise trimmed text is required"))
                continue
            if item in seen:
                findings.append(_finding("DUPLICATE_LIST_ENTRY", path, "duplicate entries are prohibited"))
            seen.add(item)
        if field.endswith("_ids") or field in {
            "inputs_produced_by_other_workloads",
            "outputs_consumed_by_other_workloads",
            "shared_runtime_requirements",
            "progression_nodes",
        }:
            for index, item in enumerate(value):
                if isinstance(item, str) and not _ID.fullmatch(item):
                    findings.append(_finding("INVALID_OPAQUE_ID", f"$.{field}[{index}]", "portable abstract identifier required"))

    strategies = document.get("allowed_reconstruction_strategies")
    if not isinstance(strategies, list) or not strategies:
        findings.append(_finding("RECONSTRUCTION_STRATEGIES_REQUIRED", "$.allowed_reconstruction_strategies", "non-empty strategy array required"))
    elif len(strategies) != len(set(strategies)):
        findings.append(_finding("DUPLICATE_RECONSTRUCTION_STRATEGY", "$.allowed_reconstruction_strategies", "strategies must be unique"))
    else:
        unknown = [item for item in strategies if item not in ALLOWED_RECONSTRUCTION_STRATEGIES]
        if unknown:
            findings.append(_finding("UNKNOWN_RECONSTRUCTION_STRATEGY", "$.allowed_reconstruction_strategies", ", ".join(map(str, unknown))))
        expected_order = [item for item in ALLOWED_RECONSTRUCTION_STRATEGIES if item in strategies]
        if strategies != expected_order:
            findings.append(_finding("NONCANONICAL_STRATEGY_ORDER", "$.allowed_reconstruction_strategies", "use canonical strategy order"))

    if document.get("source_expression_included") is not False:
        findings.append(_finding("SOURCE_EXPRESSION_BOUNDARY_REQUIRED", "$.source_expression_included", "must be false"))

    budget = document.get("performance_budget")
    if not isinstance(budget, Mapping):
        findings.append(_finding("INVALID_PERFORMANCE_BUDGET", "$.performance_budget", "bounded performance budget object required"))
    else:
        if set(budget) != _BUDGET_FIELDS:
            findings.append(_finding("INVALID_PERFORMANCE_BUDGET_FIELDS", "$.performance_budget", "budget fields must match the canonical bounded contract"))
        if budget.get("profile") != "BEDROCK_CONSOLE_PLANNING_PROXY":
            findings.append(_finding("INVALID_PERFORMANCE_PROFILE", "$.performance_budget.profile", "planning proxy profile required"))
        if budget.get("physical_console_verified") is not False:
            findings.append(_finding("PHYSICAL_CONSOLE_OVERCLAIM", "$.performance_budget.physical_console_verified", "must remain false until the external console gate"))
        for field, (minimum, maximum) in _BUDGET_LIMITS.items():
            value = budget.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
                findings.append(_finding("UNBOUNDED_PERFORMANCE_VALUE", f"$.performance_budget.{field}", f"integer must be within {minimum}..{maximum}"))

    tests = document.get("acceptance_tests")
    seen_tests: set[str] = set()
    classes: set[str] = set()
    if not isinstance(tests, list) or not tests:
        findings.append(_finding("ACCEPTANCE_TESTS_REQUIRED", "$.acceptance_tests", "at least one acceptance contract is required"))
    else:
        for index, test in enumerate(tests):
            path = f"$.acceptance_tests[{index}]"
            if not isinstance(test, Mapping):
                findings.append(_finding("INVALID_ACCEPTANCE_TEST", path, "acceptance test must be an object"))
                continue
            required = {"test_id", "class", "owner", "candidate_publication_prerequisite", "contract"}
            if set(test) != required:
                findings.append(_finding("INVALID_ACCEPTANCE_TEST_FIELDS", path, "acceptance test fields must match the canonical contract"))
            test_id = test.get("test_id")
            if not isinstance(test_id, str) or not _ID.fullmatch(test_id):
                findings.append(_finding("INVALID_ACCEPTANCE_TEST_ID", f"{path}.test_id", "portable abstract identifier required"))
            elif test_id in seen_tests:
                findings.append(_finding("DUPLICATE_ACCEPTANCE_TEST_ID", f"{path}.test_id", "test IDs must be unique"))
            seen_tests.add(str(test_id))
            test_class = test.get("class")
            if test_class not in ACCEPTANCE_OWNERS:
                findings.append(_finding("UNKNOWN_ACCEPTANCE_CLASS", f"{path}.class", "unknown acceptance test class"))
            else:
                classes.add(str(test_class))
                if test.get("owner") != ACCEPTANCE_OWNERS[test_class]:
                    findings.append(_finding("WRONG_ACCEPTANCE_OWNER", f"{path}.owner", "gate must be delegated to its canonical owner"))
                required_for_publication = test.get("candidate_publication_prerequisite")
                if test_class == "WORKER_LOCAL":
                    if required_for_publication is not True:
                        findings.append(_finding("LOCAL_VALIDATION_REQUIRED", f"{path}.candidate_publication_prerequisite", "worker-local validation is required before publication"))
                elif required_for_publication is not False:
                    findings.append(_finding("EXTERNAL_GATE_PREREQUISITE_PROHIBITED", f"{path}.candidate_publication_prerequisite", "external gates are not worker publication prerequisites"))
            contract = test.get("contract")
            if not isinstance(contract, str) or not contract.strip() or len(contract) > 240 or "\n" in contract:
                findings.append(_finding("INVALID_ACCEPTANCE_CONTRACT", f"{path}.contract", "concise product-safe contract required"))
        if "WORKER_LOCAL" not in classes:
            findings.append(_finding("WORKER_LOCAL_TEST_MISSING", "$.acceptance_tests", "worker-local validation contract required"))
        if "T1_MECHANICAL_PREFLIGHT" not in classes:
            findings.append(_finding("T1_DELEGATION_MISSING", "$.acceptance_tests", "T1 must be delegated explicitly"))
        if "STABLE_BDS" not in classes:
            findings.append(_finding("BDS_DELEGATION_MISSING", "$.acceptance_tests", "Stable BDS must be delegated explicitly"))

    _validate_safe_text(document, findings)
    if findings:
        raise SanitizedWorkloadError("SANITIZED_WORKLOAD_INVALID", "sanitized workload failed validation", findings)
    return copy.deepcopy(dict(document))


def _budget(*, ticks: int, entities: int, records: int, events: int, cleanup: int) -> dict[str, Any]:
    return {
        "profile": "BEDROCK_CONSOLE_PLANNING_PROXY",
        "script_tick_units_max": ticks,
        "active_entities_max": entities,
        "persistent_records_max": records,
        "network_events_per_tick_max": events,
        "cleanup_ticks_max": cleanup,
        "physical_console_verified": False,
    }


def _tests(prefix: str, local: str, bds: str) -> list[dict[str, Any]]:
    return [
        {"test_id": f"{prefix}.local", "class": "WORKER_LOCAL", "owner": "feature_producer", "candidate_publication_prerequisite": True, "contract": local},
        {"test_id": f"{prefix}.preflight", "class": "T1_MECHANICAL_PREFLIGHT", "owner": "t1_preflight_tester", "candidate_publication_prerequisite": False, "contract": "Validate packaged structure, references, identifiers, and deterministic assembly."},
        {"test_id": f"{prefix}.server", "class": "STABLE_BDS", "owner": "bds_tester", "candidate_publication_prerequisite": False, "contract": bds},
        {"test_id": f"{prefix}.audit", "class": "T10_PRIVATE_AUDIT", "owner": "independent_auditor", "candidate_publication_prerequisite": False, "contract": "Compare observable product behavior against authorized private evidence without disclosing it."},
        {"test_id": f"{prefix}.controller", "class": "CONTROLLER", "owner": "controller_qa", "candidate_publication_prerequisite": False, "contract": "Complete representative interactions using controller-only navigation."},
        {"test_id": f"{prefix}.console", "class": "PHYSICAL_PS4", "owner": "console_qa", "candidate_publication_prerequisite": False, "contract": "Measure representative play on physical target hardware; no proxy result may satisfy this gate."},
    ]


_COMMON_RIGHTS = [
    "Implement only abstract behavior and product requirements supplied by this packet.",
    "Create original names, visual presentation, geometry, audio, and interface language.",
    "Treat identity-bearing material and protected expression as unavailable to production.",
]
_COMMON_CONSOLE = [
    "All primary interactions must support controller-only navigation.",
    "Work must remain within the bounded planning-proxy budget until physical-console qualification.",
]
_COMMON_MULTI = [
    "State transitions must be authoritative, deterministic, and safe for concurrent players.",
    "Ownership checks must prevent one player from mutating another player's protected state.",
]
_COMMON_PERSIST = [
    "Committed state must survive save, restart, reconnect, and chunk reload.",
    "Schema upgrades must fail closed without duplicating or silently discarding player state.",
]
_STRATEGIES = list(ALLOWED_RECONSTRUCTION_STRATEGIES)


def _packet(
    number: int,
    title: str,
    *,
    scope: list[str],
    contracts: list[str],
    inputs: list[str],
    outputs: list[str],
    runtime: list[str],
    assets: list[str],
    behaviors: list[str],
    progression: list[str],
    budget: dict[str, Any],
    local_test: str,
    server_test: str,
    gaps: list[str] | None = None,
) -> dict[str, Any]:
    prefix = f"sf-t{number}"
    packet = {
        "workload_id": f"SF-T{number}",
        "title": title,
        "product_scope": scope,
        "player_facing_contracts": contracts,
        "inputs_produced_by_other_workloads": inputs,
        "outputs_consumed_by_other_workloads": outputs,
        "shared_runtime_requirements": runtime,
        "asset_contract_ids": assets,
        "behavior_contract_ids": behaviors,
        "progression_nodes": progression,
        "acceptance_tests": _tests(prefix, local_test, server_test),
        "performance_budget": budget,
        "console_constraints": list(_COMMON_CONSOLE),
        "multiplayer_constraints": list(_COMMON_MULTI),
        "persistence_constraints": list(_COMMON_PERSIST),
        "known_platform_gaps": list(gaps or []),
        "allowed_reconstruction_strategies": list(_STRATEGIES),
        "rights_constraints": list(_COMMON_RIGHTS),
        "source_expression_included": False,
    }
    return validate_sanitized_workload(packet)


def build_skyfactory4_workloads() -> list[dict[str, Any]]:
    """Build the canonical twelve-packet product decomposition.

    The historical product name appears only in this API name for operator
    discoverability.  It is never serialized into production-safe packets.
    """

    runtime_core = ["runtime.state", "runtime.identifiers", "runtime.migrations", "runtime.telemetry"]
    asset_core = ["assets.world", "assets.items", "assets.interfaces"]
    packets = [
        _packet(1, "Void-world bootstrap and survival", scope=["Generate bounded empty-world play spaces with selectable starter layouts.", "Initialize starting resources, recovery rules, and world options once per world."], contracts=["A fresh world always produces a playable starter area and a recoverable first-resource loop.", "Joining players cannot repeat or corrupt world initialization."], inputs=["assets.world", "runtime.state", "runtime.identifiers"], outputs=["product.bootstrap-ready", "product.world-options"], runtime=runtime_core, assets=["assets.world", "assets.interfaces"], behaviors=["behavior.bootstrap", "behavior.recovery"], progression=["progression.world-created", "progression.survival-loop-ready"], budget=_budget(ticks=18, entities=24, records=256, events=32, cleanup=200), local_test="Build fresh, existing, and interrupted initialization fixtures and prove idempotent recovery.", server_test="Create, restart, reconnect, and concurrently join representative worlds without duplicate initialization."),
        _packet(2, "Renewable arboreal resource progression", scope=["Provide tiered renewable trees and harvest products that replace inaccessible ground resources.", "Support manual growth, harvesting, replanting, and automation-facing harvest contracts."], contracts=["Each unlocked tree tier has a finite, explainable route from seed resource to renewable harvest.", "Harvest results conserve inputs and remain deterministic under repeated growth cycles."], inputs=["assets.trees", "product.bootstrap-ready", "runtime.identifiers", "runtime.scheduler"], outputs=["product.primary-materials", "product.tree-automation-interface"], runtime=runtime_core + ["runtime.scheduler"], assets=["assets.trees", "assets.items"], behaviors=["behavior.tree-growth", "behavior.tree-harvest"], progression=["progression.first-tree", "progression.primary-material-tiers"], budget=_budget(ticks=28, entities=40, records=512, events=48, cleanup=240), local_test="Prove every declared tree tier is reachable and each harvest table remains bounded and renewable.", server_test="Run simultaneous growth and harvest cycles across chunk reloads without item duplication or loss."),
        _packet(3, "Early processing and material transformation", scope=["Provide drying, crushing, heating, melting, casting, and early alloy transformations.", "Connect primitive processing to renewable primary materials and machine progression."], contracts=["Every early transformation exposes its inputs, outputs, duration, and failure behavior.", "The early path cannot dead-end before powered processing becomes reachable."], inputs=["product.primary-materials", "runtime.recipe-registry", "runtime.scheduler", "assets.machines"], outputs=["product.processed-materials", "product.primitive-processing"], runtime=runtime_core + ["runtime.recipe-registry", "runtime.scheduler"], assets=["assets.machines", "assets.items"], behaviors=["behavior.early-processing", "behavior.casting"], progression=["progression.primitive-processing", "progression.first-alloy"], budget=_budget(ticks=30, entities=32, records=768, events=48, cleanup=240), local_test="Check transformation reachability, conservation, timing bounds, and invalid-input behavior.", server_test="Operate concurrent primitive processing chains through restart and chunk unload without rollback or duplication."),
        _packet(4, "Power and machine lifecycle", scope=["Define bounded generation, storage, transfer, and consumption of a common machine-energy unit.", "Schedule machine work safely across activation, pause, unload, reload, and restart."], contracts=["Producers, storage, and consumers account for energy without creation, loss, or negative balances.", "Machine progress resumes deterministically after lifecycle interruptions."], inputs=["product.processed-materials", "runtime.power-graph", "runtime.scheduler", "runtime.state", "assets.machines"], outputs=["product.powered-processing", "product.energy-interface"], runtime=runtime_core + ["runtime.power-graph", "runtime.scheduler"], assets=["assets.machines", "assets.interfaces"], behaviors=["behavior.energy-accounting", "behavior.machine-lifecycle"], progression=["progression.first-power", "progression.powered-machine"], budget=_budget(ticks=40, entities=48, records=1024, events=64, cleanup=300), local_test="Prove conservation, transfer limits, scheduler bounds, and deterministic lifecycle transitions.", server_test="Stress representative producer-consumer networks across restart and chunk lifecycle boundaries."),
        _packet(5, "Logistics and bounded automation", scope=["Move items and fluids through filtered routes with explicit capacity and priority rules.", "Connect harvesting, processing, and inventories into observable automation chains."], contracts=["Full or unavailable destinations create backpressure without deleting or duplicating contents.", "Routing decisions remain deterministic when multiple destinations compete."], inputs=["product.powered-processing", "product.tree-automation-interface", "runtime.transfer-graph", "runtime.scheduler"], outputs=["product.automation-interface", "product.transport-ready"], runtime=runtime_core + ["runtime.transfer-graph", "runtime.scheduler"], assets=["assets.machines", "assets.interfaces"], behaviors=["behavior.item-routing", "behavior.fluid-routing", "behavior.backpressure"], progression=["progression.first-transport", "progression.automated-chain"], budget=_budget(ticks=48, entities=56, records=1536, events=96, cleanup=360), local_test="Check route priority, filters, conservation, full-destination backpressure, and bounded cycle handling.", server_test="Run competing automated routes under multiplayer load and chunk reload without loss or duplication."),
        _packet(6, "Compact and networked storage", scope=["Provide compact, bulk, and indexed storage tiers with controller-first access.", "Preserve ownership, capacity, indexing, migration, and corruption safeguards."], contracts=["Stored contents remain exact across upgrade, migration, restart, and concurrent access.", "Capacity failures are explicit and never discard accepted contents."], inputs=["product.transport-ready", "runtime.state", "runtime.ownership", "runtime.migrations", "assets.interfaces"], outputs=["product.storage-interface", "product.indexed-inventory"], runtime=runtime_core + ["runtime.ownership"], assets=["assets.storage", "assets.interfaces"], behaviors=["behavior.storage-capacity", "behavior.storage-index"], progression=["progression.bulk-storage", "progression.indexed-storage"], budget=_budget(ticks=36, entities=32, records=4096, events=72, cleanup=360), local_test="Verify capacity boundaries, indexing, ownership, migrations, and transactional write behavior.", server_test="Exercise concurrent deposits and withdrawals across restart without corruption, loss, or duplication."),
        _packet(7, "Renewable farming and creature production", scope=["Provide crops, managed creatures, containment, collection, and renewable production loops.", "Support bounded growth acceleration and automation-facing collection."], contracts=["Every required biological resource has a renewable route with explicit environmental conditions.", "Containment and collection remain bounded when production destinations are full."], inputs=["product.primary-materials", "product.automation-interface", "runtime.scheduler", "runtime.ownership", "assets.creatures"], outputs=["product.renewable-resources", "product.creature-production"], runtime=runtime_core + ["runtime.scheduler", "runtime.ownership"], assets=["assets.crops", "assets.creatures"], behaviors=["behavior.crop-growth", "behavior.creature-production"], progression=["progression.renewable-farming", "progression.creature-resources"], budget=_budget(ticks=44, entities=96, records=1024, events=72, cleanup=300), local_test="Prove renewable reachability, growth bounds, containment rules, and full-collector backpressure.", server_test="Stress representative farms with multiple players and verify bounded entities, cleanup, and persistence."),
        _packet(8, "Arcane progression, dimensions, and exploration", scope=["Provide original ritual-like progression, bounded destination travel, structures, encounters, and special resources.", "Use console-safe substitutes when a literal mechanic cannot be represented reliably."], contracts=["Travel is reversible and preserves player state across destination transitions.", "Required encounter rewards and remote resources remain reachable without hidden prerequisites."], inputs=["product.powered-processing", "product.renewable-resources", "runtime.state", "runtime.ownership", "assets.world"], outputs=["product.remote-resources", "product.special-progression"], runtime=runtime_core + ["runtime.ownership"], assets=["assets.world", "assets.creatures", "assets.effects"], behaviors=["behavior.dimension-travel", "behavior.special-encounters"], progression=["progression.first-travel", "progression.special-encounter"], budget=_budget(ticks=42, entities=96, records=1536, events=96, cleanup=480), local_test="Verify travel state machines, encounter reward reachability, return paths, and substitute contracts.", server_test="Exercise concurrent travel and encounter lifecycle through restart without stranded or duplicated players.", gaps=["Some destination-scale mechanics may require bounded original substitutes."]),
        _packet(9, "Milestones, unlocks, and endgame progression", scope=["Coordinate world and player milestones, optional unlock modes, rewards, and completion criteria.", "Expose a controller-friendly path from bootstrap through representative endgame."], contracts=["Every gated product system names a reachable prerequisite and an observable unlock result.", "World-scoped and player-scoped progress remain separate and migrate without privilege leakage."], inputs=["product.bootstrap-ready", "product.primary-materials", "product.processed-materials", "product.powered-processing", "product.automation-interface", "product.storage-interface", "product.renewable-resources", "product.remote-resources", "runtime.advancement-ledger", "runtime.migrations", "assets.interfaces"], outputs=["product.progression-ledger", "product.endgame-path"], runtime=runtime_core + ["runtime.advancement-ledger", "runtime.ownership"], assets=["assets.interfaces", "assets.items"], behaviors=["behavior.unlock-ledger", "behavior.milestone-rewards"], progression=["progression.bootstrap-to-endgame", "progression.completion"], budget=_budget(ticks=32, entities=24, records=2048, events=64, cleanup=240), local_test="Prove graph reachability, scope separation, reward idempotency, migrations, and completion calculation.", server_test="Advance multiple players through divergent milestones and restart without unlock leakage or duplicate rewards."),
        _packet(10, "Original asset requirement contracts", scope=["Specify functional visual, geometry, animation, audio, readability, and interface constraints by product role.", "Define bounded asset budgets and originality restrictions without producing assets."], contracts=["Each product feature references an abstract asset contract with states, interaction geometry, and readability needs.", "No contract directs reproduction of identity-bearing visual or audio material."], inputs=[], outputs=["assets.world", "assets.items", "assets.interfaces", "assets.trees", "assets.machines", "assets.storage", "assets.crops", "assets.creatures", "assets.effects"], runtime=["runtime.identifiers", "runtime.telemetry"], assets=["assets.world", "assets.items", "assets.interfaces", "assets.trees", "assets.machines", "assets.storage", "assets.crops", "assets.creatures", "assets.effects"], behaviors=["behavior.asset-state-contract"], progression=["progression.asset-contracts-ready"], budget=_budget(ticks=8, entities=16, records=256, events=16, cleanup=120), local_test="Validate contract completeness, originality boundaries, portable identifiers, and bounded asset budgets.", server_test="Validate packaged asset references and state transitions without asserting presentation quality."),
        _packet(11, "Shared Bedrock runtime requirements", scope=["Define interfaces for state, identifiers, recipes, scheduling, power, transfer, ownership, interfaces, milestones, migration, synchronization, telemetry, and test hooks.", "Publish bounded compatibility contracts for independent workload producers without selecting implementation."], contracts=["Each shared service has a versioned interface, ownership boundary, failure policy, and migration requirement.", "Consumers can declare compatibility without reading another producer's implementation."], inputs=[], outputs=["runtime.state", "runtime.identifiers", "runtime.recipe-registry", "runtime.scheduler", "runtime.power-graph", "runtime.transfer-graph", "runtime.ownership", "runtime.interface-framework", "runtime.advancement-ledger", "runtime.migrations", "runtime.telemetry", "runtime.test-hooks"], runtime=["runtime.state", "runtime.identifiers", "runtime.recipe-registry", "runtime.scheduler", "runtime.power-graph", "runtime.transfer-graph", "runtime.ownership", "runtime.interface-framework", "runtime.advancement-ledger", "runtime.migrations", "runtime.telemetry", "runtime.test-hooks"], assets=[], behaviors=["behavior.runtime-interface-contract"], progression=["progression.shared-contracts-ready"], budget=_budget(ticks=50, entities=32, records=4096, events=128, cleanup=360), local_test="Validate interface versions, failure policies, dependency declarations, migration rules, and budget composition.", server_test="Qualify only concrete shared-runtime candidates after admission; this requirements packet does not claim implementation."),
        _packet(12, "Qualification and observable acceptance planning", scope=["Define product-safe startup, progression, conservation, automation, persistence, multiplayer, lifecycle, controller, performance, and completion acceptance contracts.", "Classify each acceptance contract by its responsible local or external gate owner."], contracts=["Every product-critical behavior has a measurable acceptance outcome and one authoritative gate owner.", "No downstream gate is required before a feature producer freezes and submits a locally validated candidate."], inputs=["product.endgame-path", "runtime.test-hooks", "assets.interfaces"], outputs=["qualification.acceptance-index", "qualification.gate-routing"], runtime=["runtime.telemetry", "runtime.test-hooks", "runtime.identifiers"], assets=["assets.interfaces"], behaviors=["behavior.acceptance-contract"], progression=["progression.qualification-ready"], budget=_budget(ticks=24, entities=64, records=2048, events=96, cleanup=600), local_test="Validate complete gate ownership, measurable outcomes, boundary-safe fixtures, and external-gate delegation.", server_test="Execute only contracts classified for Stable BDS and publish immutable results without repairing candidates.", gaps=["Client, hosted-world, controller, split-screen, and physical-console gates require their designated environments."]),
    ]
    return copy.deepcopy(packets)


def build_workload_dependency_graph(workloads: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Build a deterministic graph from declared producer/consumer contracts."""

    packets = validate_sanitized_workload_catalog(workloads or build_skyfactory4_workloads())
    producers: dict[str, str] = {}
    for packet in packets:
        for output in packet["outputs_consumed_by_other_workloads"]:
            if output in producers:
                raise SanitizedWorkloadError(
                    "SANITIZED_WORKLOAD_CATALOG_INVALID",
                    "output contract has multiple producers",
                    [_finding("DUPLICATE_OUTPUT_PROVIDER", "$.outputs_consumed_by_other_workloads", output)],
                )
            producers[output] = packet["workload_id"]
    edges: set[tuple[str, str, str]] = set()
    missing: list[dict[str, str]] = []
    for packet in packets:
        for contract in packet["inputs_produced_by_other_workloads"]:
            provider = producers.get(contract)
            if provider is None:
                missing.append(_finding("INPUT_PROVIDER_MISSING", f"$.{packet['workload_id']}.inputs_produced_by_other_workloads", contract))
            elif provider == packet["workload_id"]:
                missing.append(_finding("SELF_DEPENDENCY", f"$.{packet['workload_id']}.inputs_produced_by_other_workloads", contract))
            else:
                edges.add((provider, packet["workload_id"], contract))
    if missing:
        raise SanitizedWorkloadError("SANITIZED_WORKLOAD_CATALOG_INVALID", "workload dependency graph is incomplete", missing)
    ordered_edges = [
        {"from": provider, "to": consumer, "contract_id": contract}
        for provider, consumer, contract in sorted(edges, key=lambda row: (int(row[0][4:]), int(row[1][4:]), row[2]))
    ]
    incoming = {workload_id: 0 for workload_id in WORKLOAD_IDS}
    outgoing: dict[str, list[str]] = {workload_id: [] for workload_id in WORKLOAD_IDS}
    for edge in ordered_edges:
        incoming[edge["to"]] += 1
        outgoing[edge["from"]].append(edge["to"])
    ready = sorted((node for node, degree in incoming.items() if degree == 0), key=lambda item: int(item[4:]))
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for child in sorted(set(outgoing[node]), key=lambda item: int(item[4:])):
            incoming[child] -= sum(1 for edge in ordered_edges if edge["from"] == node and edge["to"] == child)
            if incoming[child] == 0:
                ready.append(child)
                ready.sort(key=lambda item: int(item[4:]))
    if len(order) != len(WORKLOAD_IDS):
        raise SanitizedWorkloadError(
            "SANITIZED_WORKLOAD_CATALOG_INVALID",
            "workload dependency graph contains a cycle",
            [_finding("DEPENDENCY_CYCLE", "$", "dependency graph must be acyclic")],
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "graph_id": "sf-workload-dependencies-1.0.0",
        "nodes": list(WORKLOAD_IDS),
        "edges": ordered_edges,
        "root_workloads": [node for node in WORKLOAD_IDS if not any(edge["to"] == node for edge in ordered_edges)],
        "topological_order": order,
    }


def validate_sanitized_workload_catalog(workloads: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(workloads, (str, bytes)) or not isinstance(workloads, Sequence):
        raise SanitizedWorkloadError("SANITIZED_WORKLOAD_CATALOG_INVALID", "workload catalog must be an array")
    packets = [validate_sanitized_workload(packet) for packet in workloads]
    ids = [packet["workload_id"] for packet in packets]
    if len(ids) != len(set(ids)):
        raise SanitizedWorkloadError("SANITIZED_WORKLOAD_CATALOG_INVALID", "duplicate workload IDs")
    if set(ids) != set(WORKLOAD_IDS):
        raise SanitizedWorkloadError(
            "SANITIZED_WORKLOAD_CATALOG_INVALID",
            "catalog must contain exactly SF-T1 through SF-T12",
            [_finding("INCOMPLETE_WORKLOAD_CATALOG", "$", "all twelve workloads are required")],
        )
    return sorted(packets, key=lambda packet: int(packet["workload_id"][4:]))


def build_skyfactory4_workload_catalog() -> dict[str, Any]:
    workloads = build_skyfactory4_workloads()
    return {
        "schema_version": SCHEMA_VERSION,
        "catalog_id": "sf-product-workloads-1.0.0",
        "workloads": workloads,
        "dependency_graph": build_workload_dependency_graph(workloads),
    }


def canonical_workload_bytes(value: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> bytes:
    """Return the stable serialization used by intake manifests and tests."""

    if isinstance(value, Mapping) and "workload_id" in value:
        safe: Any = validate_sanitized_workload(value)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        safe = validate_sanitized_workload_catalog(value)
    else:
        safe = copy.deepcopy(value)
    return (json.dumps(safe, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
