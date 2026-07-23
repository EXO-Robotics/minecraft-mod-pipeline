from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, Sequence


FEATURE_CATEGORIES = frozenset({
    "regional_creature", "ranged_item", "structure", "elite_encounter",
    "additive_unlock", "bounded_event",
})
EVIDENCE_STATES = frozenset({
    "PENDING_AUTHORIZED_EVIDENCE", "EVIDENCE_RECORDED", "INTENT_DISTILLED",
    "CLEAN_ROOM_CONTRACTED", "IMPLEMENTED", "STATIC_QUALIFIED",
    "BDS_QUALIFIED", "DESKTOP_VERIFIED", "PS4_VERIFIED",
})
GATES = (
    "rights_and_provenance", "gameplay_intent", "clean_room_contract",
    "behavior_and_asset_contracts", "implementation", "deterministic_package",
    "creator_tools", "stable_bds", "multiplayer", "persistence", "cleanup",
    "desktop_presentation", "ps4_planning", "physical_ps4",
)
_SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_RESTRICTED_REFERENCE = re.compile(
    r"(?:^|[/\\])(?:source|sources|decompiled|restricted)(?:[/\\]|$)|"
    r"(?:evidence://|analysis/|rights-ledger/)",
    re.IGNORECASE,
)


class ReconstructionWaveError(ValueError):
    def __init__(self, code: str, message: str, findings: Sequence[Mapping[str, str]] = ()):
        super().__init__(message)
        self.code = code
        self.findings = tuple(dict(row) for row in findings)


def _finding(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, path: str, findings: list[dict[str, str]]) -> str:
    if not isinstance(value, str) or not value.strip():
        findings.append(_finding("REQUIRED_VALUE_MISSING", path, "non-empty text is required"))
        return ""
    return value.strip()


def build_reconstruction_wave(document: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build analysis and consumer-safe records for one Java-mod reconstruction wave."""
    findings: list[dict[str, str]] = []
    if document.get("schema_version") != "1.0.0":
        findings.append(_finding("UNSUPPORTED_SCHEMA", "$.schema_version", "must equal 1.0.0"))
    wave_id = _text(document.get("wave_id"), "$.wave_id", findings)
    if wave_id and not _SAFE_ID.fullmatch(wave_id):
        findings.append(_finding("INVALID_WAVE_ID", "$.wave_id", "use lowercase identifier characters"))
    title = _text(document.get("title"), "$.title", findings)
    target = document.get("target_profile")
    if target != "PS4_MARKETPLACE_CANDIDATE":
        findings.append(_finding("INVALID_TARGET_PROFILE", "$.target_profile", "must be PS4_MARKETPLACE_CANDIDATE"))
    if document.get("preserve_vanilla_gameplay") is not True:
        findings.append(_finding("VANILLA_PRESERVATION_REQUIRED", "$.preserve_vanilla_gameplay", "must be true"))
    if document.get("mandatory_campaign") is not False:
        findings.append(_finding("MANDATORY_CAMPAIGN_PROHIBITED", "$.mandatory_campaign", "must be false"))
    if document.get("rights_mode") not in {"clean_room_originalization", "authorized_adaptation"}:
        findings.append(_finding("INVALID_RIGHTS_MODE", "$.rights_mode", "unsupported rights mode"))

    raw_features = document.get("features")
    if not isinstance(raw_features, list) or not raw_features:
        findings.append(_finding("FEATURES_REQUIRED", "$.features", "at least one feature is required"))
        raw_features = []
    seen: set[str] = set()
    categories: set[str] = set()
    analysis_features: list[dict[str, Any]] = []
    production_features: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_features):
        path = f"$.features[{index}]"
        if not isinstance(raw, Mapping):
            findings.append(_finding("INVALID_FEATURE", path, "feature must be an object"))
            continue
        feature_id = _text(raw.get("feature_id"), f"{path}.feature_id", findings)
        if feature_id and not _SAFE_ID.fullmatch(feature_id):
            findings.append(_finding("INVALID_FEATURE_ID", f"{path}.feature_id", "use lowercase identifier characters"))
        if feature_id in seen:
            findings.append(_finding("DUPLICATE_FEATURE_ID", f"{path}.feature_id", feature_id))
        seen.add(feature_id)
        category = raw.get("category")
        if category not in FEATURE_CATEGORIES:
            findings.append(_finding("INVALID_FEATURE_CATEGORY", f"{path}.category", str(category)))
        else:
            categories.add(str(category))
        abstract_role = _text(raw.get("abstract_role"), f"{path}.abstract_role", findings)
        state = raw.get("evidence_state")
        if state not in EVIDENCE_STATES:
            findings.append(_finding("INVALID_EVIDENCE_STATE", f"{path}.evidence_state", str(state)))
        refs = raw.get("authorized_evidence_refs")
        if not isinstance(refs, list) or not all(isinstance(ref, str) and ref for ref in refs):
            findings.append(_finding("INVALID_EVIDENCE_REFS", f"{path}.authorized_evidence_refs", "must be an array of opaque IDs"))
            refs = []
        if state != "PENDING_AUTHORIZED_EVIDENCE" and not refs:
            findings.append(_finding("EVIDENCE_REQUIRED", f"{path}.authorized_evidence_refs", "record evidence before advancing state"))
        for ref in refs:
            if "/" in ref or "\\" in ref or ":" in ref or not _SAFE_ID.fullmatch(ref):
                findings.append(_finding("NON_OPAQUE_EVIDENCE_REF", f"{path}.authorized_evidence_refs", ref))
        intent_ref = _text(raw.get("gameplay_intent_ref"), f"{path}.gameplay_intent_ref", findings)
        contract_ref = _text(raw.get("clean_room_contract_ref"), f"{path}.clean_room_contract_ref", findings)
        outputs = raw.get("bedrock_outputs")
        if not isinstance(outputs, list) or not outputs or not all(isinstance(item, str) and item for item in outputs):
            findings.append(_finding("BEDROCK_OUTPUTS_REQUIRED", f"{path}.bedrock_outputs", "non-empty string array required"))
            outputs = []
        gates = raw.get("gates")
        if not isinstance(gates, Mapping) or set(gates) != set(GATES):
            findings.append(_finding("INCOMPLETE_GATE_MATRIX", f"{path}.gates", "every reconstruction gate is required"))
            gates = {}
        for gate in GATES:
            if gates.get(gate) not in {"PASSED", "PENDING", "BLOCKED", "NOT_APPLICABLE"}:
                findings.append(_finding("INVALID_GATE_STATUS", f"{path}.gates.{gate}", str(gates.get(gate))))
        if gates.get("physical_ps4") == "PASSED" and state != "PS4_VERIFIED":
            findings.append(_finding("PHYSICAL_EVIDENCE_STATE_MISMATCH", f"{path}.gates.physical_ps4", "requires PS4_VERIFIED"))
        analysis_features.append({
            "feature_id": feature_id,
            "category": category,
            "abstract_role": abstract_role,
            "authorized_evidence_refs": list(refs),
            "evidence_state": state,
            "gameplay_intent_ref": intent_ref,
            "clean_room_contract_ref": contract_ref,
            "bedrock_outputs": list(outputs),
            "gates": {gate: gates.get(gate) for gate in GATES},
        })
        production_features.append({
            "feature_id": feature_id,
            "category": category,
            "abstract_role": abstract_role,
            "evidence_state": state,
            "gameplay_intent_id": intent_ref.rsplit("/", 1)[-1].removesuffix(".json"),
            "clean_room_contract": contract_ref,
            "bedrock_outputs": list(outputs),
            "gates": {gate: gates.get(gate) for gate in GATES},
        })

    required = set(document.get("required_categories", FEATURE_CATEGORIES))
    unknown_required = required - FEATURE_CATEGORIES
    if unknown_required:
        findings.append(_finding("INVALID_REQUIRED_CATEGORY", "$.required_categories", ", ".join(sorted(unknown_required))))
    for missing in sorted(required - categories):
        findings.append(_finding("REQUIRED_CATEGORY_MISSING", "$.features", missing))
    if findings:
        raise ReconstructionWaveError("RECONSTRUCTION_WAVE_INVALID", "reconstruction wave failed validation", findings)

    analysis = {
        "schema_version": "1.0.0",
        "wave_id": wave_id,
        "title": title,
        "target_profile": target,
        "rights_mode": document["rights_mode"],
        "preserve_vanilla_gameplay": True,
        "mandatory_campaign": False,
        "features": analysis_features,
        "source_expression_boundary": {
            "analysis_only": True,
            "consumer_package_access": "prohibited",
            "opaque_evidence_ids_required": True,
        },
    }
    analysis["record_hash"] = _digest(analysis)
    production = {
        "schema_version": "1.0.0",
        "wave_id": wave_id,
        "title": title,
        "target_profile": target,
        "product_kind": "minecraft_bedrock_addon",
        "preserve_vanilla_gameplay": True,
        "mandatory_campaign": False,
        "features": production_features,
        "claims": {
            "marketplace_approved": False,
            "ps4_compatible": False,
            "physical_ps4_pending": any(row["gates"]["physical_ps4"] != "PASSED" for row in production_features),
        },
    }
    serialized = json.dumps(production, sort_keys=True)
    if _RESTRICTED_REFERENCE.search(serialized):
        raise ReconstructionWaveError(
            "CONSUMER_BOUNDARY_VIOLATION",
            "consumer-safe wave contains an analysis or source reference",
            [_finding("CONSUMER_BOUNDARY_VIOLATION", "$", "restricted reference detected")],
        )
    production["record_hash"] = _digest(production)
    return analysis, production
