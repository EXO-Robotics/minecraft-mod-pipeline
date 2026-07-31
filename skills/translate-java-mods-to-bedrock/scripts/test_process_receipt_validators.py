#!/usr/bin/env python3
"""Regression tests for production assignment and process-receipt gates."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
H = "a" * 64


class ReceiptValidatorTests(unittest.TestCase):
    def run_validator(self, script: str, data: dict) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / "packet.json"
            packet.write_text(json.dumps(data))
            return subprocess.run(
                ["python3", str(ROOT / script), str(packet)],
                text=True, capture_output=True, check=False,
            )

    def valid_receipt(self) -> dict:
        return {
            "schema_version": "1.0.0", "receipt_id": "r1",
            "assignment_id": "a1", "role": "feature_producer",
            "repo_root": "/lane/repo", "object_store_identity": "standalone",
            "baseline_commit": H, "transferred_inputs": [],
            "sandbox_profile_sha256": H, "environment_manifest_sha256": H,
            "launcher_sha256": H, "prompt_context_sha256": H,
            "process": {
                "pid": 42, "command": ["sandbox-launch", "agent"],
                "agent_identity": "opaque", "tool_hashes": {"agent": H},
                "started_at_utc": "2026-07-25T00:00:00Z",
                "ended_at_utc": "2026-07-25T00:01:00Z", "exit_status": 0,
            },
            "preflight": {
                "approved_inputs_readable": "YES", "production_write": "ALLOWED",
                "runtime_write": "ALLOWED", "temp_write": "ALLOWED",
                "cache_write": "ALLOWED", "evidence_denied": "YES",
                "control_denied": "YES", "private_oracle_denied": "YES",
                "canary_denied": "YES", "restricted_identifiers": "NO_MATCH",
                "restricted_hashes": "NO_MATCH", "remotes": "NONE",
                "alternates": "NONE", "hardlinks": "NONE",
                "cross_lane_symlinks": "NONE",
                "restricted_git_objects": "UNAVAILABLE",
                "restricted_env": "NONE", "network": "DENIED",
            },
            "outputs": [], "candidate_commit": H, "candidate_tree": H,
            "package_hashes": {}, "cleanup": {"status": "PASS"},
        }

    def test_valid_receipt_passes(self) -> None:
        result = self.run_validator("validate_production_process_receipt.py", self.valid_receipt())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_process_proof_fails(self) -> None:
        receipt = self.valid_receipt()
        del receipt["process"]["pid"]
        result = self.run_validator("validate_production_process_receipt.py", receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PROCESS_FIELDS_MISSING", result.stdout)

    def test_failed_denial_fails(self) -> None:
        receipt = self.valid_receipt()
        receipt["preflight"]["evidence_denied"] = "NO"
        result = self.run_validator("validate_production_process_receipt.py", receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PREFLIGHT_FAILED", result.stdout)


if __name__ == "__main__":
    unittest.main()
