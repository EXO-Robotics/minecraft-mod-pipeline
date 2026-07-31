#!/usr/bin/env python3
"""Fixed Codex executor for bounded Studio evidence and private-audit jobs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT))

from remote_job_lib import payload_hash, validate_request, write_json  # noqa: E402

CODEX = Path("/opt/homebrew/bin/codex")
OUTPUT_SCHEMA = Path(__file__).resolve().with_name("codex-result-output.schema.json")


def _prompt(job_type: str) -> str:
    common = """
You are executing one bounded Crazy Craft clean-room remote job. Work read-only.
Read request.json, input-manifest.json, and only job-local inputs plus absolute
evidence roots explicitly listed in request.json. Installed Codex skill
instruction files may be read when the runtime requires them; they are process
instructions, never job evidence. Do not inspect other user files.
Return JSON matching the supplied schema. Never return raw Java, decompiled
text, source paths, Java or source identifiers, source assets, hidden-case
inputs or values, private-oracle values, credentials, source implementation
structure, or distinctive source expression. Use opaque IDs. Do not use
network tools, modify files, invoke other agents, or invoke local models.
"""
    if job_type == "EVIDENCE_RECOVERY":
        role = """
Answer only the bounded missing-contract question in the job inputs. Return
source-neutral state transitions, ownership, persistence, restart, multiplayer,
platform requirements, contradictions, and unresolved questions. Use outcome
MORE_EVIDENCE_REQUIRED when the allowed evidence cannot support an abstraction.
"""
    else:
        role = """
Audit only the frozen candidate identified by request.json and the permitted
private-oracle scope. Return abstract defects, severity, allowed repair scope,
and required regression IDs. Never reveal hidden cases or expected values.
"""
    return common + role + "\nJob type: " + job_type + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-root", type=Path, required=True)
    parser.add_argument(
        "--job-type",
        choices=("EVIDENCE_RECOVERY", "PRIVATE_CANDIDATE_AUDIT"),
        required=True,
    )
    args = parser.parse_args()
    root = args.job_root.resolve()
    request = json.loads((root / "request.json").read_text())
    validate_request(request)
    if request["job_type"] != args.job_type:
        raise RuntimeError("runner job-type mismatch")
    if not CODEX.is_file() or not OUTPUT_SCHEMA.is_file():
        raise RuntimeError("fixed Codex executable or output schema unavailable")

    raw_result = root / "runtime-agent-result.json"
    event_log = root / "logs" / "codex-events.jsonl"
    environment = {
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(root / "runtime-home"),
        "TMPDIR": str(root / "runtime-tmp"),
        "CODEX_HOME": os.environ.get("CODEX_HOME", "/Users/blakestudio/.codex"),
        "NO_PROXY": "*",
    }
    completed = subprocess.run(
        [
            str(CODEX),
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--cd",
            str(root),
            "--output-schema",
            str(OUTPUT_SCHEMA),
            "--output-last-message",
            str(raw_result),
            "--json",
            "-",
        ],
        input=_prompt(args.job_type),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=request["timeout_seconds"],
        check=False,
        env=environment,
    )
    event_log.write_text(completed.stdout)
    if completed.returncode != 0 or not raw_result.is_file():
        raise RuntimeError(f"Codex execution failed: {completed.returncode}")
    agent_result = json.loads(raw_result.read_text())
    result = {
        "schema_version": "crazycraft-remote-v1",
        "job_id": request["job_id"],
        "job_type": request["job_type"],
        "requesting_authority": request["requesting_authority"],
        "assignment_id": request["assignment_id"],
        "campaign_id": request["campaign_id"],
        "outcome": agent_result["outcome"],
        "abstract_results": agent_result["abstract_results"],
        "opaque_contract_ids": agent_result["opaque_contract_ids"],
        "opaque_finding_ids": agent_result["opaque_finding_ids"],
        "required_regression_ids": agent_result["required_regression_ids"],
        "qualification_references": [],
        "proof_boundary": agent_result["proof_boundary"],
        "external_gates_not_run": [
            "BEDROCK_CLIENT",
            "CONTROLLER",
            "PHYSICAL_PS4",
            "REALM",
            "SPLIT_SCREEN",
            "MARKETPLACE"
        ],
        "disclosure_scan": {"status": "PENDING", "matches": []},
        "codex_session_identifier": None,
        "result_payload_sha256": ""
    }
    for line in completed.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started":
            result["codex_session_identifier"] = event.get("thread_id")
            break
    result["result_payload_sha256"] = payload_hash(
        result, "result_payload_sha256"
    )
    write_json(root / "result.json", result)
    (root / "report.md").write_text(
        "# Remote Codex job\n\n"
        f"- Job: `{request['job_id']}`\n"
        f"- Type: `{request['job_type']}`\n"
        f"- Outcome: `{result['outcome']}`\n"
        "- Boundary: abstract, disclosure-scanned result only.\n"
    )
    raw_result.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
