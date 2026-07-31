from __future__ import annotations

import unittest

from validate_role_contract import validate_assignment, validate_gate_ledger


HASH = "a" * 64


def assignment(
    role: str,
    skill: str,
    lane: str,
    receipt: bool,
    gate: str = "STATIC_QUALIFIED",
) -> dict:
    return {
        "schema_version": "1.0.0",
        "assignment_id": "assignment-001",
        "role": role,
        "skill": skill,
        "lane": lane,
        "lane_root": "/lane",
        "allowed_read_paths": ["/lane/input"],
        "allowed_write_paths": [] if lane == "AUDIT" else ["/lane/output"],
        "prohibited_paths": ["/evidence-vault"],
        "input_artifacts": [{"path": "/lane/input/contract.json", "sha256": HASH}],
        "output_artifacts": ["candidate.json"],
        "required_checks": ["hashes"],
        "stop_states": ["hash mismatch"],
        "completion_state": "EXPECTED_STATE",
        "gate_authority": [gate],
        "requires_process_receipt": receipt,
    }


class RoleContractTests(unittest.TestCase):
    def test_valid_production_and_audit_assignments(self) -> None:
        self.assertEqual(
            validate_assignment(
                assignment(
                    "feature_producer",
                    "produce-bedrock-cleanroom-feature",
                    "PRODUCTION",
                    True,
                )
            ),
            [],
        )
        self.assertEqual(
            validate_assignment(
                assignment(
                    "independent_auditor",
                    "audit-java-bedrock-cleanroom",
                    "AUDIT",
                    False,
                    "SEMANTIC_AUDIT",
                )
            ),
            [],
        )

    def test_wrong_lane_skill_and_receipt_fail(self) -> None:
        errors = validate_assignment(
            assignment("feature_producer", "wrong-skill", "EVIDENCE", False)
        )
        self.assertTrue(any("requires skill" in error for error in errors))
        self.assertTrue(any("requires lane PRODUCTION" in error for error in errors))
        self.assertTrue(any("requires requires_process_receipt=true" in error for error in errors))

    def test_role_cannot_claim_another_roles_gate(self) -> None:
        packet = assignment(
            "evidence_analyst",
            "analyze-java-mod-evidence",
            "EVIDENCE",
            False,
        )
        packet["gate_authority"] = ["BDS_QUALIFIED"]
        errors = validate_assignment(packet)
        self.assertTrue(any("cannot claim gates" in error for error in errors))

    def test_gate_pass_requires_exact_evidence(self) -> None:
        valid = {
            "stable_bds": {
                "status": "PASSED",
                "authority": "qualify-bedrock-candidate",
                "artifact_sha256": HASH,
                "receipt": "receipts/stable-bds.json",
                "classification": "exact_package_bds",
            }
        }
        self.assertEqual(validate_gate_ledger(valid), [])
        invalid = {"stable_bds": {"status": "PASSED", "artifact_sha256": "bad"}}
        self.assertGreaterEqual(len(validate_gate_ledger(invalid)), 4)


if __name__ == "__main__":
    unittest.main()
