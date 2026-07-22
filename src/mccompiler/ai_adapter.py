from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping


SCHEMA_VERSION = "1.0.0"
PROPOSAL_STATUSES = frozenset({"proposed", "withdrawn"})
HUMAN_ACCEPTANCE_STATES = frozenset({"pending", "accepted", "rejected"})


class AIProposalError(ValueError):
    """Raised when an AI proposal fails the deterministic trust boundary."""


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise AIProposalError(f"Proposal is not canonical JSON: {exc}") from exc


def proposal_digest(proposal: Mapping[str, Any]) -> str:
    """Return a stable digest, excluding the self-referential digest field."""
    document = copy.deepcopy(dict(proposal))
    document.pop("proposal_digest", None)
    return hashlib.sha256(_canonical_json(document).encode("utf-8")).hexdigest()


def build_proposal(
    *,
    proposal_id: str,
    target: str,
    proposal: Mapping[str, Any],
    evidence: list[Mapping[str, Any]],
    prompt_provenance: Mapping[str, Any],
    model_provenance: Mapping[str, Any],
    confidence: float,
) -> dict[str, Any]:
    """Create an offline proposal envelope; this function never calls a model."""
    document: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "proposal_id": proposal_id,
        "target": target,
        "status": "proposed",
        "proposal": copy.deepcopy(dict(proposal)),
        "evidence": copy.deepcopy(evidence),
        "prompt_provenance": copy.deepcopy(dict(prompt_provenance)),
        "model_provenance": copy.deepcopy(dict(model_provenance)),
        "confidence": confidence,
        "human_acceptance": {"state": "pending"},
        "authority": "advisory-only",
        "requires_explicit_override": True,
    }
    document["proposal_digest"] = proposal_digest(document)
    validate_proposal(document)
    return document


def validate_proposal(proposal: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the proposal deterministically and return a defensive copy."""
    if not isinstance(proposal, Mapping):
        raise AIProposalError("AI proposal must be an object")

    required = {
        "schema_version", "proposal_id", "target", "status", "proposal", "evidence",
        "prompt_provenance", "model_provenance", "confidence", "human_acceptance",
        "authority", "requires_explicit_override", "proposal_digest",
    }
    missing = sorted(required - set(proposal))
    unknown = sorted(set(proposal) - required)
    if missing:
        raise AIProposalError(f"Missing proposal fields: {', '.join(missing)}")
    if unknown:
        raise AIProposalError(f"Unknown proposal fields: {', '.join(unknown)}")
    if proposal["schema_version"] != SCHEMA_VERSION:
        raise AIProposalError(f"Unsupported AI proposal schema: {proposal['schema_version']!r}")
    if not isinstance(proposal["proposal_id"], str) or not proposal["proposal_id"].strip():
        raise AIProposalError("proposal_id must be a non-empty string")
    if not isinstance(proposal["target"], str) or not proposal["target"].strip():
        raise AIProposalError("target must be a non-empty string")
    if proposal["status"] not in PROPOSAL_STATUSES:
        raise AIProposalError(f"Invalid proposal status: {proposal['status']!r}")
    if not isinstance(proposal["proposal"], Mapping) or not proposal["proposal"]:
        raise AIProposalError("proposal must be a non-empty object")
    if not isinstance(proposal["evidence"], list) or not proposal["evidence"]:
        raise AIProposalError("At least one evidence record is required")
    for index, record in enumerate(proposal["evidence"]):
        if not isinstance(record, Mapping) or not record.get("source_mode"):
            raise AIProposalError(f"Evidence record {index} needs source_mode")
        if not any(record.get(key) for key in ("source_file", "source_class", "resource_path", "registration_site")):
            raise AIProposalError(f"Evidence record {index} needs a traceable source location")

    _validate_provenance("prompt_provenance", proposal["prompt_provenance"], ("template_id", "template_version", "prompt_sha256"))
    _validate_provenance("model_provenance", proposal["model_provenance"], ("provider", "model", "adapter_version"))
    confidence = proposal["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise AIProposalError("confidence must be a number from 0 through 1")

    acceptance = proposal["human_acceptance"]
    if not isinstance(acceptance, Mapping) or acceptance.get("state") not in HUMAN_ACCEPTANCE_STATES:
        raise AIProposalError("human_acceptance.state must be pending, accepted, or rejected")
    acceptance_unknown = sorted(set(acceptance) - {"state", "reviewer", "reviewed_at", "reason"})
    if acceptance_unknown:
        raise AIProposalError(f"Unknown human acceptance fields: {', '.join(acceptance_unknown)}")
    if acceptance["state"] != "pending" and (not acceptance.get("reviewer") or not acceptance.get("reviewed_at")):
        raise AIProposalError("Reviewed proposals require reviewer and reviewed_at")
    if proposal["authority"] != "advisory-only" or proposal["requires_explicit_override"] is not True:
        raise AIProposalError("AI proposals must remain advisory and require an explicit override")

    expected = proposal_digest(proposal)
    if proposal["proposal_digest"] != expected:
        raise AIProposalError("proposal_digest does not match canonical proposal content")
    return copy.deepcopy(dict(proposal))


def _validate_provenance(name: str, value: Any, fields: tuple[str, ...]) -> None:
    if not isinstance(value, Mapping):
        raise AIProposalError(f"{name} must be an object")
    missing = [field for field in fields if not isinstance(value.get(field), str) or not value[field].strip()]
    if missing:
        raise AIProposalError(f"{name} needs: {', '.join(missing)}")


def authorize_with_override(proposal: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Verify separate human authority; return the override, never an AI-authored patch."""
    checked = validate_proposal(proposal)
    if checked["human_acceptance"]["state"] != "accepted":
        raise AIProposalError("Proposal must be human-accepted before an override can reference it")
    if not isinstance(override, Mapping) or override.get("target") != checked["target"]:
        raise AIProposalError("Explicit override target must match the proposal target")
    provenance = override.get("provenance")
    if not isinstance(provenance, Mapping):
        raise AIProposalError("Explicit override requires human provenance")
    if provenance.get("ai_proposal_id") != checked["proposal_id"] or provenance.get("ai_proposal_digest") != checked["proposal_digest"]:
        raise AIProposalError("Override provenance must bind the exact AI proposal id and digest")
    if not provenance.get("author") or not provenance.get("reason"):
        raise AIProposalError("Override provenance requires a human author and reason")
    return copy.deepcopy(dict(override))
