from __future__ import annotations

from typing import Final


POSITIVE_DIMENSIONS: Final[tuple[str, ...]] = (
    "identity_importance",
    "player_appeal",
    "gameplay_depth",
    "spectacle",
    "replayability",
    "progression_importance",
    "exploration_value",
    "content_reuse",
    "pattern_reuse",
    "marketing_clarity",
    "bedrock_native_improvement_opportunity",
)

FEASIBILITY_DIMENSIONS: Final[tuple[str, ...]] = (
    "java_evidence_confidence",
    "bedrock_reconstruction_feasibility",
    "existing_compiler_pattern_coverage",
    "asset_production_effort",
    "testing_effort",
    "console_performance_viability",
    "multiplayer_complexity",
    "persistence_complexity",
    "maintenance_cost",
)

RIGHTS_DIMENSIONS: Final[tuple[str, ...]] = (
    "code_license_clarity",
    "asset_license_clarity",
    "branding_trademark_risk",
    "commercial_derivative_permission",
    "marketplace_distribution_review_status",
)

NEGATIVE_DIMENSIONS: Final[tuple[str, ...]] = (
    "integration_risk",
    "dependency_chain_cost",
    "runtime_cost",
    "ui_redesign_cost",
    "unsupported_engine_reliance",
    "rights_uncertainty",
    "content_duplication",
    "low_player_impact",
)

STRATEGIES: Final[tuple[str, ...]] = (
    "DIRECT_RECONSTRUCTION",
    "BEDROCK_NATIVE_REDESIGN",
    "ORIGINAL_REPLACEMENT",
    "DEFER",
    "UNSUPPORTED",
    "RIGHTS_BLOCKED",
)

CORE_CATEGORIES: Final[tuple[str, ...]] = (
    "signature_weapons",
    "armor_or_active_powers",
    "dangerous_creatures",
    "elite_encounters",
    "major_bosses",
    "structures_and_discovery",
    "controlled_chaos",
    "clear_progression",
    "persistent_unlocks_or_transformations",
    "loot_and_crafting_integration",
)

DEFAULT_PROGRESSION_STAGES: Final[tuple[str, ...]] = (
    "early_survival",
    "first_unusual_equipment",
    "regional_creatures",
    "structure_exploration",
    "elite_encounters",
    "boss_materials",
    "advanced_armor_or_powers",
    "world_tier_bosses",
    "final_chaos_encounter",
    "postgame_modifiers",
)

PROVEN_PATTERNS: Final[dict[str, str]] = {
    "persistent_location_records": "PROVEN_DOORLOCK",
    "canonical_multi_block_locations": "PROVEN_DOORLOCK",
    "ownership_and_authorization": "PROVEN_DOORLOCK",
    "forms": "PROVEN_DOORLOCK_AND_CLOCKWORK",
    "server_authoritative_decisions": "PROVEN_DOORLOCK",
    "versioned_migrations": "PROVEN_DOORLOCK",
    "break_cleanup": "PROVEN_DOORLOCK",
    "redstone_reconciliation": "PROVEN_DOORLOCK",
    "fail_closed_state_validation": "PROVEN_DOORLOCK",
    "item_actions": "PROVEN_CLOCKWORK",
    "projectiles": "PROVEN_CLOCKWORK",
    "effects": "PROVEN_CLOCKWORK",
    "cooldowns": "STRUCTURAL_CLOCKWORK_REAL_PLAYER_PENDING",
    "event_context_contracts": "PROVEN_CLOCKWORK",
    "progression_state": "PROVEN_CLOCKWORK",
    "processing_machines": "PROVEN_CLOCKWORK",
    "form_backed_interactions": "EVENT_PROVEN_PRESENTATION_PENDING",
    "growing_entities": "PROVEN_CLOCKWORK",
    "entity_lifecycle": "PROVEN_CLOCKWORK",
    "multiphase_bosses": "PROVEN_CLOCKWORK",
    "real_action_runtime_tests": "PREVIEW_INTEGRATION_PROVEN_REAL_CLIENT_PENDING",
    "performance_budgets": "STATIC_POLICY_PROVEN_CONSOLE_MEASUREMENT_PENDING",
}
