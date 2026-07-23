from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from mccompiler.operations.envelope import OperationError
from mccompiler.project.store import ProjectStore
from mccompiler.reconstruction import ReconstructionWaveError, build_reconstruction_wave
from mccompiler.reconstruction.forest_wave_1 import render_forest_wave_1_diagnosis


_SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def prepare_reconstruction_wave(
    store: ProjectStore,
    parameters: dict[str, Any],
    expected_revision: int | None = None,
) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    try:
        analysis, production = build_reconstruction_wave(parameters)
    except ReconstructionWaveError as exc:
        raise OperationError(
            exc.code,
            str(exc),
            details={
                "findings": list(exc.findings),
                "remediation": "Record authorized evidence as opaque analysis IDs and complete every required gate.",
                "mutated": False,
            },
        ) from exc
    wave_id = str(analysis["wave_id"])
    if not _SAFE_ID.fullmatch(wave_id):
        raise OperationError("INVALID_WAVE_ID", "wave_id is not path safe")
    analysis_path = f"analysis/reconstruction-waves/{wave_id}.json"
    production_path = f"production/reconstruction-waves/{wave_id}/baseline.json"
    revision = store.commit(
        {analysis_path: analysis, production_path: production},
        expected_revision=expected_revision,
    )
    artifacts = []
    for path, kind in (
        (analysis_path, "reconstruction_analysis"),
        (production_path, "reconstruction_baseline"),
    ):
        artifacts.append({"path": path, "kind": kind, "size": store.resolve(path).stat().st_size})
    return {
        "status": "BASELINE_PREPARED",
        "wave_id": wave_id,
        "analysis_record": analysis_path,
        "consumer_safe_baseline": production_path,
        "physical_ps4_pending": production["claims"]["physical_ps4_pending"],
        "revision": revision,
    }, store, artifacts


def diagnose_reconstruction_wave_repository(
    project: str,
    parameters: dict[str, Any],
    expected_revision: int | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if expected_revision is not None:
        raise OperationError(
            "DIAGNOSTIC_REVISION_UNSUPPORTED",
            "Repository diagnostics use immutable input hashes rather than ProjectStore revisions",
            details={"mutated": False, "remediation": "Omit expected_revision and retain the reported rollback point."},
        )
    if parameters.get("dry_run") is not True:
        raise OperationError(
            "DRY_RUN_REQUIRED",
            "diagnose_reconstruction_wave requires dry_run=true",
            details={"mutated": False, "remediation": "Pass --dry-run or set parameters.dry_run to true."},
        )
    if parameters.get("execution_authorized", False) is not False:
        raise OperationError(
            "UNAUTHORIZED_EXECUTION",
            "The diagnostic operation cannot authorize execution",
            details={"mutated": False, "remediation": "Remove the authorization request; approval occurs outside diagnostics."},
        )
    unknown = sorted(set(parameters) - {"dry_run", "execution_authorized", "wave_id"})
    if unknown:
        raise OperationError(
            "INVALID_PARAMETERS",
            f"Unsupported diagnostic parameters: {', '.join(unknown)}",
            details={"mutated": False},
        )
    if parameters.get("wave_id", "forest-wave-1") != "forest-wave-1":
        raise OperationError(
            "UNSUPPORTED_DIAGNOSTIC_WAVE",
            "Only the checked-in forest-wave-1 diagnostic profile is available",
            details={"mutated": False},
        )
    root = Path(project).expanduser().resolve()
    try:
        reports, paths = render_forest_wave_1_diagnosis(root)
    except (OSError, ValueError) as exc:
        raise OperationError(
            "DIAGNOSTIC_RENDER_FAILED",
            str(exc),
            details={"mutated": False, "production_writes": 0, "runtime_mutations": 0},
        ) from exc
    readiness = reports["forest-wave-1-execution-readiness.json"]
    artifacts = [
        {
            "path": str(path.relative_to(root)),
            "kind": "diagnostic_markdown" if path.suffix == ".md" else "diagnostic_report",
            "size": path.stat().st_size,
        }
        for path in paths
    ]
    return {
        "status": "DIAGNOSTIC_COMPLETE",
        "mode": "DIAGNOSTIC_ONLY",
        "execution_status": "EXECUTION_NOT_AUTHORIZED",
        "execution_authorized": False,
        "aggregate_readiness": readiness["aggregate"]["status"],
        "blocking": readiness["aggregate"]["autonomous_production_may_proceed"] is False,
        "feature_readiness": {
            row["feature_id"]: row["status"] for row in readiness["features"]
        },
        "production_writes": 0,
        "runtime_mutations": 0,
        "asset_authoring_invocations": 0,
        "package_outputs_created": 0,
    }, artifacts
