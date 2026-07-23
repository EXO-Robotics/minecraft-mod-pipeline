from __future__ import annotations

import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


RIGHTS_MODES = frozenset({"clean_room_originalization", "authorized_adaptation"})
MATERIAL_TYPES = frozenset({
    "source_code", "compiled_binary", "model", "texture", "animation", "audio",
    "music", "writing", "localization", "logo", "trademark", "character",
    "structure_layout", "progression_design", "dependency", "documentation",
    "runtime_observation",
})
PERMISSION_STATES = frozenset({"allowed", "prohibited", "unknown", "not_applicable", "requires_review"})
CLAIM_DISPOSITIONS = frozenset({"observed", "inferred", "selected", "redesigned", "omitted", "unknown"})
RIGHTS_TRANSITIONS = frozenset({
    "RIGHTS_BLOCKED_DIRECT_RECONSTRUCTION", "ABSTRACT_PATTERN_RETAINED",
    "CLEAN_ROOM_REDESIGN_REQUIRED", "TOO_DISTINCTIVE_FOR_SAFE_REDIRECTION",
    "OMIT_PENDING_LICENSE", "AUTHORIZED_FOR_PRODUCTION",
})
TAINTS = frozenset({
    "ANALYSIS_ONLY", "RESTRICTED_EXPRESSION", "ABSTRACTED_MECHANIC",
    "AUTHORIZED_FOR_PRODUCTION", "CLEAN_ROOM_ORIGINAL", "BLOCKED",
})
PROHIBITED_PRODUCTION_TAINTS = frozenset({"ANALYSIS_ONLY", "RESTRICTED_EXPRESSION", "BLOCKED"})
SCREENING_OUTCOMES = frozenset({
    "AUTOMATED_SCREEN_LOW_RISK", "HUMAN_REVIEW_REQUIRED", "REVISION_REQUIRED",
    "OMIT_PENDING_LICENSE", "SCREENING_INSUFFICIENT",
})
_REQUIRED_ADAPTATION_TYPES = frozenset({
    "source_code", "model", "texture", "animation", "audio", "writing",
    "character", "structure_layout", "dependency",
})
_APPROVED_EXPORT_FIELDS = (
    "intent_id", "intent_type", "experience_family", "abstract_role",
    "player_fantasy", "gameplay_loop", "combat_pattern", "exploration_pattern",
    "reward_function", "progression_role", "multiplayer_requirements",
    "persistence_requirements", "cleanup_requirements",
    "performance_expectations", "dependencies",
)
_RESTRICTED_FIELD_NAMES = frozenset({
    "source_name", "source_path", "source_uri", "source_filename", "source_hash",
    "source_logo", "source_character_name", "source_weapon_name", "source_product_name",
    "source_texture", "source_model", "source_audio", "source_localization", "source_lore",
    "source_structure_layout", "source_reward_identity", "recreate_source_asset",
})
_RESTRICTED_REFERENCE = re.compile(
    r"(?:evidence://|analysis/|analysis\\|rights-ledger/|rights-ledger\\|"
    r"(?:^|[/\\])(?:source|sources|decompiled|restricted)(?:[/\\]|$))",
    re.IGNORECASE,
)
_SHA256 = re.compile(r"\b[a-fA-F0-9]{64}\b")


class CleanRoomError(ValueError):
    """Structured policy failure raised before production emission."""

    def __init__(self, code: str, message: str, *, findings: Sequence[Mapping[str, Any]] = ()):
        super().__init__(message)
        self.code = code
        self.findings = tuple(dict(row) for row in findings)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _finding(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def reject_unknown_schema(document: Mapping[str, Any], artifact: str) -> None:
    """Reject version drift before an artifact reaches a specialized validator."""
    if document.get("schema_version") != "1.0.0":
        raise CleanRoomError(
            "UNSUPPORTED_SCHEMA",
            f"{artifact} must use schema_version 1.0.0",
            findings=[_finding("UNSUPPORTED_SCHEMA", "$.schema_version", artifact)],
        )


def _require_text(value: Any, path: str, findings: list[dict[str, str]]) -> str:
    if not isinstance(value, str) or not value.strip():
        findings.append(_finding("REQUIRED_VALUE_MISSING", path, "non-empty text is required"))
        return ""
    return value.strip()


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, str | None, Any]]:
    if isinstance(value, Mapping):
        for key in sorted(value, key=str):
            child_path = f"{path}.{key}"
            yield child_path, str(key), value[key]
            yield from _walk(value[key], child_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, None, item
            yield from _walk(item, child_path)


def evaluate_rights_strategy(
    strategy: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    mode = strategy.get("mode")
    if strategy.get("schema_version") != "1.0.0":
        findings.append(_finding("UNSUPPORTED_SCHEMA", "$.schema_version", "rights strategy must use 1.0.0"))
    if mode not in RIGHTS_MODES:
        findings.append(_finding("INVALID_RIGHTS_MODE", "$.mode", "unsupported rights strategy mode"))

    ledger_result = validate_material_ledger(ledger)
    findings.extend(ledger_result["findings"])
    records = ledger_result["records"]
    if mode == "clean_room_originalization":
        expected = {
            "inspiration_scope": "abstract_gameplay_patterns_only",
            "direct_source_expression_reuse": "prohibited",
            "third_party_assets_allowed": False,
            "third_party_names_allowed": False,
            "third_party_branding_allowed": False,
            "distinctive_expression_allowed": False,
            "commercial_marketplace_rights_required": True,
        }
        for key, wanted in expected.items():
            if strategy.get(key) != wanted:
                findings.append(_finding("UNSAFE_CLEAN_ROOM_STRATEGY", f"$.{key}", f"must equal {wanted!r}"))
    elif mode == "authorized_adaptation":
        material_types = {row["material_type"] for row in records if row["eligible_for_authorized_adaptation"]}
        for missing in sorted(_REQUIRED_ADAPTATION_TYPES - material_types):
            findings.append(_finding("ADAPTATION_PERMISSION_INCOMPLETE", "$.ledger", f"missing eligible {missing} record"))
        brand_relevant = any(row["material_type"] in {"logo", "trademark"} for row in records)
        if brand_relevant and not all(
            row["eligible_for_authorized_adaptation"]
            for row in records if row["material_type"] in {"logo", "trademark"}
        ):
            findings.append(_finding("BRAND_PERMISSION_INCOMPLETE", "$.ledger", "brand or trademark rights are incomplete"))

    return {
        "schema_version": "1.0.0",
        "mode": mode,
        "production_allowed": not findings,
        "findings": sorted(findings, key=lambda row: (row["path"], row["code"])),
        "legal_clearance_implied": False,
        "screening_notice": "Policy screening only; not legal clearance.",
    }


def validate_material_ledger(ledger: Mapping[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    if ledger.get("schema_version") != "1.0.0":
        findings.append(_finding("UNSUPPORTED_SCHEMA", "$.schema_version", "material ledger must use 1.0.0"))
    raw_records = ledger.get("records")
    if not isinstance(raw_records, list) or not raw_records:
        findings.append(_finding("LEDGER_EMPTY", "$.records", "at least one material record is required"))
        raw_records = []
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_records):
        path = f"$.records[{index}]"
        if not isinstance(raw, Mapping):
            findings.append(_finding("INVALID_MATERIAL_RECORD", path, "record must be an object"))
            continue
        material_id = _require_text(raw.get("material_id"), f"{path}.material_id", findings)
        source_id = _require_text(raw.get("source_id"), f"{path}.source_id", findings)
        material_type = raw.get("material_type")
        if material_id in seen:
            findings.append(_finding("DUPLICATE_MATERIAL_ID", f"{path}.material_id", material_id))
        seen.add(material_id)
        if material_type not in MATERIAL_TYPES:
            findings.append(_finding("INVALID_MATERIAL_TYPE", f"{path}.material_type", str(material_type)))
        ownership = raw.get("ownership")
        permissions = raw.get("permissions")
        restrictions = raw.get("restrictions")
        disposition = raw.get("production_disposition")
        for field, section in (
            ("ownership", ownership), ("permissions", permissions),
            ("restrictions", restrictions), ("production_disposition", disposition),
        ):
            if not isinstance(section, Mapping):
                findings.append(_finding("MISSING_LEDGER_SECTION", f"{path}.{field}", "object is required"))
        permissions = permissions if isinstance(permissions, Mapping) else {}
        required_permissions = (
            "analysis", "redistribution", "commercial_use", "derivatives",
            "marketplace_distribution", "attribution_required", "source_disclosure_required",
        )
        for key in required_permissions:
            if permissions.get(key) not in PERMISSION_STATES:
                findings.append(_finding("INVALID_PERMISSION_STATE", f"{path}.permissions.{key}", str(permissions.get(key))))
        restrictions = restrictions if isinstance(restrictions, Mapping) else {}
        disposition = disposition if isinstance(disposition, Mapping) else {}
        direct = disposition.get("direct_reuse")
        reusable = all(permissions.get(key) == "allowed" for key in (
            "redistribution", "commercial_use", "derivatives", "marketplace_distribution",
        ))
        ambiguous = restrictions.get("ambiguous_ownership") is True
        noncommercial = restrictions.get("noncommercial") is True
        third_party = restrictions.get("third_party_content_present") is True
        if direct == "allowed" and (not reusable or ambiguous or noncommercial or third_party):
            if ambiguous:
                code = "UNKNOWN_OWNERSHIP_PRODUCTION_BLOCKED"
            elif noncommercial:
                code = "NONCOMMERCIAL_MARKETPLACE_REUSE_BLOCKED"
            else:
                code = "DIRECT_PRODUCTION_REUSE_BLOCKED"
            findings.append(_finding(code, f"{path}.production_disposition.direct_reuse", "commercial production permissions are incomplete or restricted"))
        eligible = (
            reusable and not ambiguous and not noncommercial and
            disposition.get("authorized_adaptation_eligible") == "allowed"
        )
        normalized.append({
            "material_id": material_id,
            "source_id": source_id,
            "material_type": material_type,
            "analysis_allowed": permissions.get("analysis") == "allowed",
            "direct_reuse_allowed": direct == "allowed" and reusable and not ambiguous and not noncommercial and not third_party,
            "eligible_for_authorized_adaptation": eligible,
            "rights_state": "unknown" if ambiguous or any(permissions.get(key) in {"unknown", "requires_review"} for key in required_permissions) else "recorded",
        })
    return {
        "schema_version": "1.0.0",
        "valid": not findings,
        "records": sorted(normalized, key=lambda row: row["material_id"]),
        "findings": sorted(findings, key=lambda row: (row["path"], row["code"])),
        "legal_clearance_implied": False,
    }


def build_gameplay_intent(
    intent: Mapping[str, Any],
    *,
    allowed_evidence_refs: Iterable[str],
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    if "schema_version" in intent and intent.get("schema_version") != "1.0.0":
        findings.append(_finding("UNSUPPORTED_SCHEMA", "$.schema_version", "Gameplay Intent input must use 1.0.0"))
    allowed = frozenset(allowed_evidence_refs)
    required = (
        "intent_id", "intent_type", "experience_family", "abstract_role",
        "player_fantasy", "gameplay_loop", "combat_pattern", "exploration_pattern",
        "reward_function", "progression_role", "multiplayer_requirements",
        "persistence_requirements", "cleanup_requirements",
        "performance_expectations", "dependencies", "claims", "rights",
    )
    for key in required:
        if key not in intent:
            findings.append(_finding("INTENT_FIELD_MISSING", f"$.{key}", "required field"))
    claims = intent.get("claims")
    if not isinstance(claims, list) or not claims:
        findings.append(_finding("INTENT_CLAIMS_MISSING", "$.claims", "at least one audited claim is required"))
        claims = []
    normalized_claims: list[dict[str, Any]] = []
    for index, claim in enumerate(claims):
        path = f"$.claims[{index}]"
        if not isinstance(claim, Mapping):
            findings.append(_finding("INVALID_INTENT_CLAIM", path, "claim must be an object"))
            continue
        disposition = claim.get("disposition")
        confidence = claim.get("confidence")
        refs = claim.get("evidence_refs")
        if disposition not in CLAIM_DISPOSITIONS:
            findings.append(_finding("INVALID_CLAIM_DISPOSITION", f"{path}.disposition", str(disposition)))
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            findings.append(_finding("INVALID_CONFIDENCE", f"{path}.confidence", "must be between 0 and 1"))
        if not isinstance(refs, list):
            findings.append(_finding("INVALID_EVIDENCE_REFS", f"{path}.evidence_refs", "array required"))
            refs = []
        for ref in refs:
            if ref not in allowed:
                findings.append(_finding("UNAUTHORIZED_EVIDENCE_REFERENCE", f"{path}.evidence_refs", str(ref)))
        _require_text(claim.get("rationale"), f"{path}.rationale", findings)
        _require_text(claim.get("source_type"), f"{path}.source_type", findings)
        if not isinstance(claim.get("rights_constraints"), list):
            findings.append(_finding("RIGHTS_CONSTRAINTS_MISSING", f"{path}.rights_constraints", "array required"))
        normalized_claims.append(dict(claim))
    rights = intent.get("rights")
    if not isinstance(rights, Mapping):
        findings.append(_finding("INTENT_RIGHTS_MISSING", "$.rights", "rights disposition object required"))
        rights = {}
    for key in (
        "source_access", "reusable_expression", "abstract_mechanic_reuse",
        "direct_reconstruction", "commercial_asset_rights", "transition",
    ):
        _require_text(rights.get(key), f"$.rights.{key}", findings)
    if rights.get("transition") not in RIGHTS_TRANSITIONS:
        findings.append(_finding("INVALID_RIGHTS_TRANSITION", "$.rights.transition", str(rights.get("transition"))))
    source_taint = intent.get("taint", ["ANALYSIS_ONLY"])
    if not isinstance(source_taint, list):
        findings.append(_finding("INVALID_TAINT", "$.taint", "array required"))
        source_taint = []
    for label in source_taint:
        if label not in TAINTS:
            findings.append(_finding("UNKNOWN_TAINT", "$.taint", str(label)))
        elif label == "BLOCKED":
            findings.append(_finding("BLOCKED_TAINT_CANNOT_BE_ABSTRACTED", "$.taint", str(label)))
    if (
        rights.get("abstract_mechanic_reuse") != "allowed"
        and any(label in {"ANALYSIS_ONLY", "RESTRICTED_EXPRESSION"} for label in source_taint)
    ):
        findings.append(_finding("TAINT_REMOVAL_NOT_AUTHORIZED", "$.taint", "approved abstract-mechanic reuse is required"))
    if findings:
        raise CleanRoomError("GAMEPLAY_INTENT_INVALID", "Gameplay Intent IR failed validation", findings=findings)
    output = {
        "schema_version": "1.0.0",
        **{key: intent[key] for key in required if key not in {"claims", "rights"}},
        "claims": normalized_claims,
        "rights": dict(rights),
        "taint": ["ABSTRACTED_MECHANIC"],
    }
    output["semantic_hash"] = _digest(output)
    return output


def export_clean_room_contract(
    intent: Mapping[str, Any],
    *,
    contract_id: str,
    blocked_names: Iterable[str] = (),
    blocked_hashes: Iterable[str] = (),
) -> dict[str, Any]:
    rights = intent.get("rights")
    transition = rights.get("transition") if isinstance(rights, Mapping) else None
    if transition in {"TOO_DISTINCTIVE_FOR_SAFE_REDIRECTION", "OMIT_PENDING_LICENSE"}:
        raise CleanRoomError(
            "OMIT_PENDING_LICENSE",
            "Distinctive source expression is not eligible for clean-room redirection",
            findings=[_finding("DISTINCTIVE_COMBINATION_BLOCKED", "$.rights.transition", str(transition))],
        )
    if transition not in {
        "ABSTRACT_PATTERN_RETAINED", "CLEAN_ROOM_REDESIGN_REQUIRED",
        "RIGHTS_BLOCKED_DIRECT_RECONSTRUCTION", "AUTHORIZED_FOR_PRODUCTION",
    }:
        raise CleanRoomError(
            "CLEAN_ROOM_EXPORT_BLOCKED", "Intent lacks an exportable rights transition",
            findings=[_finding("RIGHTS_TRANSITION_NOT_EXPORTABLE", "$.rights.transition", str(transition))],
        )
    contract: dict[str, Any] = {
        "schema_version": "1.0.0",
        "contract_id": contract_id,
        **{key: intent[key] for key in _APPROVED_EXPORT_FIELDS if key in intent},
        "design_constraints": {
            "original_name": "required",
            "original_silhouette": "required",
            "original_palette": "required",
            "original_texture": "required",
            "original_reward_identity": "required",
            "original_audio_identity": "required",
            "source_asset_access": "prohibited",
        },
        "qualification_requirements": {
            "multiplayer_safe": "required",
            "cleanup_bounded": "required",
            "ps4_planning_profile": "conservative",
        },
        "provenance": {
            "gameplay_intent_id": intent.get("intent_id"),
            "gameplay_intent_semantic_hash": intent.get("semantic_hash"),
            "taint": ["ABSTRACTED_MECHANIC", "CLEAN_ROOM_ORIGINAL"],
        },
    }
    report = validate_production_artifact(contract, blocked_names=blocked_names, blocked_hashes=blocked_hashes)
    if not report["valid"]:
        raise CleanRoomError("CLEAN_ROOM_EXPORT_BLOCKED", "Production contract failed clean-room validation", findings=report["findings"])
    contract["semantic_hash"] = _digest(contract)
    return contract


def validate_production_artifact(
    artifact: Mapping[str, Any],
    *,
    blocked_names: Iterable[str] = (),
    blocked_hashes: Iterable[str] = (),
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    names = tuple(sorted({name.casefold() for name in blocked_names if name.strip()}, key=len, reverse=True))
    hashes = frozenset(value.casefold() for value in blocked_hashes)
    for path, key, value in _walk(artifact):
        if key is not None and key.casefold() in _RESTRICTED_FIELD_NAMES:
            findings.append(_finding("PROHIBITED_PRODUCTION_FIELD", path, f"field {key} is not allowed"))
        if key == "taint" and isinstance(value, list):
            for label in value:
                if label not in TAINTS:
                    findings.append(_finding("UNKNOWN_TAINT", path, str(label)))
                elif label in PROHIBITED_PRODUCTION_TAINTS:
                    findings.append(_finding("PROHIBITED_TAINT", path, str(label)))
        if isinstance(value, str):
            if _RESTRICTED_REFERENCE.search(value):
                findings.append(_finding("RESTRICTED_REFERENCE_LEAK", path, value))
            folded = value.casefold()
            for name in names:
                if re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", folded):
                    findings.append(_finding("BLOCKED_NAME_LEAK", path, name))
            for candidate in _SHA256.findall(value):
                if candidate.casefold() in hashes:
                    findings.append(_finding("RESTRICTED_HASH_LEAK", path, candidate.casefold()))
    return {
        "schema_version": "1.0.0",
        "valid": not findings,
        "findings": sorted(findings, key=lambda row: (row["path"], row["code"], row["message"])),
        "legal_clearance_implied": False,
    }


def validate_originality_record(record: Mapping[str, Any]) -> dict[str, Any]:
    required = (
        "product_id", "contract_id", "creator_mode", "design_seed",
        "design_profile_revision", "source_restrictions",
        "independently_created_elements", "mechanics_retained_at_abstract_level",
        "expressive_elements_replaced", "name_provenance", "visual_provenance",
        "structure_provenance", "reward_provenance", "progression_provenance",
        "known_similarities", "revision_history", "screening_status",
    )
    findings: list[dict[str, str]] = []
    if record.get("schema_version") != "1.0.0":
        findings.append(_finding("UNSUPPORTED_SCHEMA", "$.schema_version", "originality record must use 1.0.0"))
    for key in required:
        if key not in record:
            findings.append(_finding("ORIGINALITY_FIELD_MISSING", f"$.{key}", "required field"))
    status = record.get("screening_status")
    if status not in SCREENING_OUTCOMES:
        findings.append(_finding("INVALID_SCREENING_STATUS", "$.screening_status", str(status)))
    if not isinstance(record.get("revision_history"), list) or not record.get("revision_history"):
        findings.append(_finding("REVISION_HISTORY_MISSING", "$.revision_history", "at least one revision is required"))
    return {
        "schema_version": "1.0.0",
        "valid": not findings,
        "record_hash": _digest(record) if not findings else None,
        "findings": sorted(findings, key=lambda row: (row["path"], row["code"])),
        "legal_clearance_implied": False,
    }


def screen_similarity(
    candidate: Mapping[str, Any],
    restricted_references: Sequence[Mapping[str, Any]],
    *,
    blocked_names: Iterable[str] = (),
    blocked_hashes: Iterable[str] = (),
) -> dict[str, Any]:
    categories = (
        "names", "aliases", "silhouette_descriptors", "palette", "texture_hashes",
        "geometry_hashes", "structure_layout", "phase_ordering", "reward_identity",
        "lore", "progression_sequence", "mechanic_combination",
    )
    findings = validate_production_artifact(candidate, blocked_names=blocked_names, blocked_hashes=blocked_hashes)["findings"]
    available: list[str] = []
    unavailable: list[str] = []
    triggered: list[str] = []
    for category in categories:
        value = candidate.get(category)
        refs = [row.get(category) for row in restricted_references if row.get(category) is not None]
        if value is None or not refs:
            unavailable.append(category)
            continue
        available.append(category)
        if _canonical(value) in {_canonical(ref) for ref in refs}:
            code = f"EXACT_{category.upper()}_MATCH"
            triggered.append(code)
            findings.append(_finding(code, f"$.{category}", "exact match to restricted comparison evidence"))
    if any(row["code"] in {"BLOCKED_NAME_LEAK", "RESTRICTED_HASH_LEAK", "RESTRICTED_REFERENCE_LEAK"} for row in findings):
        outcome = "REVISION_REQUIRED"
    elif any(row["code"].startswith("EXACT_") for row in findings):
        outcome = "HUMAN_REVIEW_REQUIRED"
    elif not available:
        outcome = "SCREENING_INSUFFICIENT"
    else:
        outcome = "AUTOMATED_SCREEN_LOW_RISK"
    return {
        "schema_version": "1.0.0",
        "product_id": candidate.get("product_id"),
        "outcome": outcome,
        "compared_categories": list(categories),
        "available_evidence": sorted(available),
        "unavailable_evidence": sorted(unavailable),
        "triggered_rules": sorted(triggered),
        "findings": sorted(findings, key=lambda row: (row["path"], row["code"])),
        "required_action": (
            "revise" if outcome == "REVISION_REQUIRED" else
            "review" if outcome == "HUMAN_REVIEW_REQUIRED" else
            "obtain_more_evidence" if outcome == "SCREENING_INSUFFICIENT" else
            "continue_policy_gates"
        ),
        "screening_limitations": [
            "Automated comparisons cover only supplied evidence.",
            "Absence of a detected match does not establish originality or rights.",
        ],
        "legal_clearance_implied": False,
        "notice": "Not legal clearance.",
    }


def audit_consumer_package(paths: Iterable[str]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    prohibited_parts = {
        "analysis", "rights", "rights-ledger", "evidence", "source", "sources",
        "decompiled", "restricted", "originality", "similarity-screening",
    }
    for index, raw in enumerate(paths):
        normalized = raw.replace("\\", "/").lstrip("/")
        parts = {part.casefold() for part in PurePosixPath(normalized).parts}
        contaminated = sorted(parts & prohibited_parts)
        if contaminated:
            findings.append(_finding("CONSUMER_PACKAGE_CONTAMINATION", f"$[{index}]", f"{normalized}: {', '.join(contaminated)}"))
    return {
        "schema_version": "1.0.0",
        "valid": not findings,
        "findings": sorted(findings, key=lambda row: row["path"]),
        "legal_clearance_implied": False,
    }
