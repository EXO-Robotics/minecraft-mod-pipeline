from __future__ import annotations

import copy
from typing import Any, Mapping

from mccompiler.ai_adapter import AIProposalError, build_proposal, proposal_digest, validate_proposal
from mccompiler.project.store import ProjectStore

from .envelope import OperationError


def _required(parameters: Mapping[str, Any], name: str, expected: type[Any]) -> Any:
    value = parameters.get(name)
    if not isinstance(value, expected) or (expected is str and not value.strip()):
        raise OperationError("INVALID_PARAMETERS", f"{name} must be a non-empty {expected.__name__}")
    return value


def propose_behavior_intent(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    proposal_id = _required(parameters, "proposal_id", str)
    evidence = _required(parameters, "evidence", list)
    confidence = parameters.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise OperationError("INVALID_PARAMETERS", "confidence must be a number from 0 through 1")
    document = build_proposal(
        proposal_id=proposal_id,
        target=_required(parameters, "target", str),
        proposal=_required(parameters, "proposal", dict),
        evidence=evidence,
        prompt_provenance=_required(parameters, "prompt_provenance", dict),
        model_provenance=_required(parameters, "model_provenance", dict),
        confidence=float(confidence),
    )
    relative = f"analysis/proposals/{proposal_id}.json"
    if store.resolve(relative).exists():
        raise OperationError("PROPOSAL_EXISTS", f"Proposal already exists: {proposal_id}")
    revision = store.commit({relative: document}, expected_revision=expected_revision)
    return {"proposal": document, "revision": revision}, store, [{"path": relative, "kind": "intent_proposal"}]


def _review(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None, state: str) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    proposal_id = _required(parameters, "proposal_id", str)
    relative = f"analysis/proposals/{proposal_id}.json"
    proposal = store.read(relative)
    if not isinstance(proposal, dict):
        raise OperationError("PROPOSAL_NOT_FOUND", f"Proposal not found: {proposal_id}")
    checked = validate_proposal(proposal)
    if checked["human_acceptance"]["state"] != "pending":
        raise OperationError("PROPOSAL_ALREADY_REVIEWED", f"Proposal is already {checked['human_acceptance']['state']}")
    reviewer = _required(parameters, "reviewer", str)
    reviewed_at = _required(parameters, "reviewed_at", str)
    reason = _required(parameters, "reason", str)
    checked["human_acceptance"] = {"state": state, "reviewer": reviewer, "reviewed_at": reviewed_at, "reason": reason}
    if state == "rejected":
        checked["status"] = "withdrawn"
    checked["proposal_digest"] = proposal_digest(checked)
    validate_proposal(checked)
    documents: dict[str, Any] = {relative: checked}
    if state == "accepted":
        accepted = store.read("decisions/intent-reviews.json", {"schema_version": "1.0.0", "reviews": []})
        reviews = list(accepted.get("reviews", [])) if isinstance(accepted, dict) else []
        reviews.append({"proposal_id": proposal_id, "proposal_digest": checked["proposal_digest"], "target": checked["target"], "reviewer": reviewer, "reviewed_at": reviewed_at, "reason": reason, "status": "accepted"})
        documents["decisions/intent-reviews.json"] = {"schema_version": "1.0.0", "reviews": reviews}
    revision = store.commit(documents, expected_revision=expected_revision)
    return {"proposal": checked, "revision": revision}, store, [{"path": path, "kind": "intent_review"} for path in documents]


def accept_behavior_intent(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _review(store, parameters, expected_revision, "accepted")


def reject_behavior_intent(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _review(store, parameters, expected_revision, "rejected")


def edit_behavior_intent(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    proposal_id = _required(parameters, "proposal_id", str)
    relative = f"analysis/proposals/{proposal_id}.json"
    current = store.read(relative)
    if not isinstance(current, dict):
        raise OperationError("PROPOSAL_NOT_FOUND", f"Proposal not found: {proposal_id}")
    checked = validate_proposal(current)
    if checked["human_acceptance"]["state"] != "pending":
        raise OperationError("PROPOSAL_ALREADY_REVIEWED", "Reviewed proposals are immutable")
    replacement = _required(parameters, "proposal", dict)
    edited = copy.deepcopy(checked)
    edited["proposal"] = replacement
    if "confidence" in parameters:
        edited["confidence"] = parameters["confidence"]
    edited["proposal_digest"] = proposal_digest(edited)
    try:
        validate_proposal(edited)
    except AIProposalError as exc:
        raise OperationError("INVALID_PROPOSAL", str(exc)) from exc
    revision = store.commit({relative: edited}, expected_revision=expected_revision)
    return {"proposal": edited, "revision": revision}, store, [{"path": relative, "kind": "intent_proposal"}]
