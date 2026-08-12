#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RECEIPT = json.loads((HERE / "FINAL_WAVE1_RATIFICATION_RECEIPT.json").read_text(encoding="utf-8"))
LEDGER = json.loads((ROOT / "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json").read_text(encoding="utf-8"))


def sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


class FinalWave1RatificationTests(unittest.TestCase):
    def test_exact_six_proposal_bytes_are_bound_and_approved(self) -> None:
        rows = RECEIPT["approved_proposals"]
        expected = {"W1-001-SR", "W1-003-STORM-NEST", "W1-004-SR", "W1-002-TWINBOND", "W1-003-TWINBOND", "W1-004-TWINBOND"}
        self.assertEqual({row["ticket_id"] for row in rows}, expected)
        approved = {row["tranche"]: row for row in LEDGER["ratifications"]["approved"]}
        for row in rows:
            self.assertEqual(sha256(row["path"]), row["sha256"])
            self.assertEqual(approved[row["ticket_id"]]["proposal"], row["path"])
            self.assertEqual(approved[row["ticket_id"]]["proposal_sha256"], row["sha256"])

    def test_scope_guards_remain_binding(self) -> None:
        self.assertEqual(LEDGER["ratifications"]["deferred"], ["W1-CREATIVE-005"])
        self.assertEqual(RECEIPT["preserved_invariants"]["retired_finale_key_and_concord_scale_path"], "FORBIDDEN")
        forbidden = {"aionbound:trophy_concord_scale", "aionbound:finale_ignition_key", "concord_sigil", "concord_dueling_ring", "ash_crownblade", "empress_tide_lance"}
        for ticket in ("W1-002-TWINBOND", "W1-003-TWINBOND", "W1-004-TWINBOND"):
            proposal = json.loads((ROOT / f"engineering/authority/support-proposals/finale/{ticket}.json").read_text(encoding="utf-8"))["proposal"]
            self.assertEqual(set(proposal["forbidden_inheritance"]), forbidden)

    def test_audio_scope_is_reduced_without_custom_claims(self) -> None:
        audio = RECEIPT["audio_scope"]
        self.assertEqual(audio["decision"], "AUDIO_PLACEHOLDER_SCOPE_REDUCTION")
        self.assertEqual(LEDGER["audio_contract"]["decision"], audio["decision"])
        self.assertEqual(LEDGER["audio_contract"]["wave_1_scope"], audio["wave_1_scope"])
        self.assertEqual(LEDGER["audio_contract"]["claims_forbidden"], audio["claims_forbidden"])
        self.assertIn("custom_audio_complete", audio["claims_forbidden"])

    def test_ledger_receipt_hashes_and_nonproduct_boundary(self) -> None:
        ledger = RECEIPT["ledger"]
        self.assertEqual(sha256(ledger["json_path"]), ledger["json_sha256"])
        self.assertEqual(sha256(ledger["markdown_path"]), ledger["markdown_sha256"])
        self.assertEqual(RECEIPT["mutation_boundary"], {"product_pack_or_runtime_mutation": False, "build_or_bds_run": False, "candidate_or_client_proof_claimed": False})


if __name__ == "__main__":
    unittest.main()
