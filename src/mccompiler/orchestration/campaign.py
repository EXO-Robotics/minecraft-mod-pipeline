from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .store import OrchestrationStore


CAMPAIGN_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
JOB_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
KINDS = {"command", "transfer", "manual_gate"}
LANES = {"EVIDENCE", "CONTROL", "PRODUCTION", "INTEGRATION", "AUDIT", "QUALIFICATION"}
JAVA_TO_BEDROCK_STAGES = (
    "TARGET_FROZEN",
    "INVENTORY_COMPLETE",
    "CLEAN_ROOM_CONTRACTED",
    "PRODUCTION_ACTIVE",
    "STATIC_QUALIFIED",
    "GOLDEN_QUALIFIED",
    "INTEGRATED",
    "AUDITED",
    "BDS_QUALIFIED",
    "BUNDLE_FROZEN",
)
MANUAL_AUTHORITY_GATES = {
    "RIGHTS_AUTHORIZED",
    "CONTRACT_SANITIZED",
    "PRODUCTION_AUTHORIZED",
    "PUBLICATION_AUTHORIZED",
    "RELEASE_AUTHORIZED",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class CampaignDefinitionError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CampaignDefinitionError(message)


def validate_campaign_definition(definition: dict[str, Any]) -> None:
    _require(definition.get("schema_version") == "1.0.0", "schema_version must be 1.0.0")
    campaign_id = definition.get("campaign_id")
    _require(
        isinstance(campaign_id, str) and bool(CAMPAIGN_ID.fullmatch(campaign_id)),
        "campaign_id must be a portable lowercase identifier",
    )
    _require(isinstance(definition.get("name"), str) and definition["name"], "name is required")
    _require(definition.get("kind") == "JAVA_TO_BEDROCK", "kind must be JAVA_TO_BEDROCK")
    jobs = definition.get("jobs")
    _require(isinstance(jobs, list) and jobs, "jobs must be a non-empty array")
    identifiers: set[str] = set()
    for index, job in enumerate(jobs):
        prefix = f"jobs[{index}]"
        _require(isinstance(job, dict), f"{prefix} must be an object")
        job_id = job.get("id")
        _require(
            isinstance(job_id, str) and bool(JOB_ID.fullmatch(job_id)),
            f"{prefix}.id must be a portable lowercase identifier",
        )
        _require(job_id not in identifiers, f"duplicate job id: {job_id}")
        identifiers.add(job_id)
        _require(job.get("kind") in KINDS, f"{prefix}.kind is invalid")
        _require(job.get("lane") in LANES, f"{prefix}.lane is invalid")
        _require(
            job.get("stage") in JAVA_TO_BEDROCK_STAGES
            or job.get("stage") in MANUAL_AUTHORITY_GATES,
            f"{prefix}.stage is not a recognized campaign stage",
        )
        _require(isinstance(job.get("name"), str) and job["name"], f"{prefix}.name is required")
        _require(isinstance(job.get("payload", {}), dict), f"{prefix}.payload must be an object")
        if job["kind"] == "manual_gate":
            _require(
                job["stage"] in MANUAL_AUTHORITY_GATES,
                f"{prefix} manual gates must use an authority-gate stage",
            )
        if job["lane"] in {"PRODUCTION", "INTEGRATION"} and job["kind"] == "command":
            payload = job.get("payload", {})
            sandbox_profile = payload.get("sandbox_profile")
            process_receipt = payload.get("process_receipt")
            fixed_profile = (
                isinstance(sandbox_profile, dict)
                and isinstance(sandbox_profile.get("path"), str)
                and Path(sandbox_profile["path"]).is_absolute()
                and isinstance(sandbox_profile.get("sha256"), str)
                and bool(SHA256.fullmatch(sandbox_profile["sha256"]))
            )
            generated_profile = (
                isinstance(sandbox_profile, dict)
                and sandbox_profile.get("mode") == "generated_by_launcher"
                and isinstance(sandbox_profile.get("launcher_path"), str)
                and Path(sandbox_profile["launcher_path"]).is_absolute()
                and isinstance(sandbox_profile.get("launcher_sha256"), str)
                and bool(SHA256.fullmatch(sandbox_profile["launcher_sha256"]))
            )
            _require(
                fixed_profile or generated_profile,
                f"{prefix}.payload.sandbox_profile requires a hash-bound fixed "
                "profile or Studio launcher",
            )
            _require(
                payload.get("process_receipt_required") is True,
                f"{prefix} production commands require process_receipt_required=true",
            )
            _require(
                isinstance(process_receipt, dict)
                and isinstance(process_receipt.get("path"), str)
                and Path(process_receipt["path"]).is_absolute()
                and isinstance(process_receipt.get("validator_argv"), list)
                and bool(process_receipt["validator_argv"])
                and all(
                    isinstance(part, str) and part
                    for part in process_receipt["validator_argv"]
                ),
                f"{prefix} production commands require a receipt path and validator_argv",
            )
    for index, job in enumerate(jobs):
        dependencies = job.get("depends_on", [])
        _require(isinstance(dependencies, list), f"jobs[{index}].depends_on must be an array")
        for dependency in dependencies:
            _require(dependency in identifiers, f"unknown dependency {dependency!r}")
            _require(dependency != job["id"], f"job {job['id']} cannot depend on itself")

    graph = {
        job["id"]: set(job.get("depends_on", []))
        for job in jobs
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(job_id: str) -> None:
        if job_id in visiting:
            raise CampaignDefinitionError(f"dependency cycle includes {job_id}")
        if job_id in visited:
            return
        visiting.add(job_id)
        for dependency in graph[job_id]:
            visit(dependency)
        visiting.remove(job_id)
        visited.add(job_id)

    for job_id in graph:
        visit(job_id)


def load_campaign_definition(
    path: str | Path,
    store: OrchestrationStore,
) -> dict[str, Any]:
    definition_path = Path(path).expanduser().resolve()
    definition = json.loads(definition_path.read_text(encoding="utf-8"))
    if not isinstance(definition, dict):
        raise CampaignDefinitionError("campaign definition must contain an object")
    validate_campaign_definition(definition)
    store.initialize()
    store.create_campaign(
        campaign_id=definition["campaign_id"],
        name=definition["name"],
        kind=definition["kind"],
        metadata={
            **definition.get("metadata", {}),
            "definition_path": str(definition_path),
            "definition_sha256": hashlib.sha256(
                definition_path.read_bytes()
            ).hexdigest(),
        },
    )
    jobs_by_id = {job["id"]: job for job in definition["jobs"]}
    pending = set(jobs_by_id)
    created: list[dict[str, Any]] = []
    while pending:
        progress = False
        for job_id in sorted(pending):
            job = jobs_by_id[job_id]
            if not set(job.get("depends_on", [])).issubset(
                {created_job["id"] for created_job in created}
            ):
                continue
            created.append(
                store.enqueue_job(
                    campaign_id=definition["campaign_id"],
                    job_id=job_id,
                    name=job["name"],
                    stage=job["stage"],
                    lane=job["lane"],
                    kind=job["kind"],
                    payload=job.get("payload", {}),
                    dependencies=job.get("depends_on", []),
                    max_attempts=int(job.get("max_attempts", 1)),
                    priority=int(job.get("priority", 0)),
                    idempotency_key=job.get(
                        "idempotency_key",
                        f"{definition['campaign_id']}:{job_id}",
                    ),
                )
            )
            pending.remove(job_id)
            progress = True
        if not progress:
            raise CampaignDefinitionError("could not resolve campaign dependency graph")
    return {
        "campaign": store.get_campaign(definition["campaign_id"]),
        "jobs": created,
    }
