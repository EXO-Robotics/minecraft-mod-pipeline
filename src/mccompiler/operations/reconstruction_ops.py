from __future__ import annotations

import re
from typing import Any

from mccompiler.operations.envelope import OperationError
from mccompiler.project.store import ProjectStore
from mccompiler.reconstruction import ReconstructionWaveError, build_reconstruction_wave


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
