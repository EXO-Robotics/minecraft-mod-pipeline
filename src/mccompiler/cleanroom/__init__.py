"""Fail-closed clean-room rights screening and production-boundary helpers.

These helpers detect policy and provenance risks.  They do not provide legal
advice, determine ownership, or grant Marketplace clearance.
"""

from .boundary import (
    CleanRoomError,
    audit_consumer_package,
    build_gameplay_intent,
    evaluate_rights_strategy,
    export_clean_room_contract,
    reject_unknown_schema,
    screen_similarity,
    validate_material_ledger,
    validate_originality_record,
    validate_production_artifact,
)

__all__ = [
    "CleanRoomError",
    "audit_consumer_package",
    "build_gameplay_intent",
    "evaluate_rights_strategy",
    "export_clean_room_contract",
    "reject_unknown_schema",
    "screen_similarity",
    "validate_material_ledger",
    "validate_originality_record",
    "validate_production_artifact",
]
