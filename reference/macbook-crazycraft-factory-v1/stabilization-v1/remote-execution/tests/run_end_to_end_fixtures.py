#!/usr/bin/env python3
"""Generate hash-bound summaries for the two synthetic return-path fixtures."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "macbook"))
sys.path.insert(0, str(ROOT / "tests"))

from remote_job_lib import disclosure_scan, sha256_file  # noqa: E402
from remote_jobs import local_retrieve, local_submit  # noqa: E402
from test_remote_execution import make_bundle, make_request  # noqa: E402


def run_fixture(base: Path, sequence: int, role: str, job_type: str) -> dict:
    job_id = f"JOB-{sequence:012d}"
    bundle = make_bundle(base / "local", make_request(job_id, role, job_type))
    remote = base / "remote"
    exit_status = local_submit(bundle, remote, role, True)
    terminal = remote / ("completed" if exit_status == 0 else "failed") / job_id
    retrieved = base / f"retrieved-{sequence}"
    local_retrieve(remote, job_id, retrieved, failed=exit_status != 0)
    result = json.loads((retrieved / "result.json").read_text())
    return {
        "job_id": job_id,
        "role": role,
        "job_type": job_type,
        "exit_status": exit_status,
        "result_sha256": sha256_file(retrieved / "result.json"),
        "report_sha256": sha256_file(retrieved / "report.md"),
        "receipt_sha256": sha256_file(retrieved / "receipt.json"),
        "disclosure_scan": disclosure_scan([retrieved]),
        "raw_inputs_returned": (retrieved / "inputs").exists(),
        "terminal_state": terminal.parent.name.upper(),
        "proof_boundary": "Synthetic non-sensitive protocol fixture; no Studio, private oracle, Java evidence, Codex remote thread, or BDS runtime.",
        "result_shape": {
            "opaque_contract_ids": len(result["opaque_contract_ids"]),
            "opaque_finding_ids": len(result["opaque_finding_ids"]),
            "required_regression_ids": len(result["required_regression_ids"]),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = Path(tempfile.mkdtemp(prefix="crazycraft-return-fixtures-"))
    try:
        records = [
            run_fixture(base, 1, "T1", "EVIDENCE_RECOVERY"),
            run_fixture(base, 2, "T10", "PRIVATE_CANDIDATE_AUDIT"),
        ]
        passed = all(
            record["exit_status"] == 0
            and record["disclosure_scan"]["status"] == "PASS"
            and not record["raw_inputs_returned"]
            for record in records
        )
        result = {
            "schema_version": "1.0.0",
            "classification": "SYNTHETIC_RETURN_PATHS_PASS"
            if passed
            else "SYNTHETIC_RETURN_PATHS_FAIL",
            "jobs": records,
            "proof_boundary": "Synthetic sanitized-evidence and private-audit return paths only.",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
        return 0 if passed else 1
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

