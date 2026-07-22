from __future__ import annotations

import copy
import unittest

from mccompiler.ai_adapter import AIProposalError, authorize_with_override, build_proposal, proposal_digest, validate_proposal
from mccompiler.migrations import MigrationError, migrate_modir


def proposal():
    return build_proposal(
        proposal_id="ai:demo/use-v1", target="demo:wand/use",
        proposal={"behavior_patch": {"actions": [{"type": "apply_effect", "effect": "speed"}]}},
        evidence=[{"source_mode": "source-ast", "source_file": "Demo.java", "source_method": "use", "line_start": 12, "line_end": 15}],
        prompt_provenance={"template_id": "behavior-gap", "template_version": "1", "prompt_sha256": "a" * 64},
        model_provenance={"provider": "offline-test", "model": "fixture-model", "adapter_version": "1.0.0"},
        confidence=0.72,
    )


class AIProposalTests(unittest.TestCase):
    def test_proposal_is_deterministic_and_advisory(self):
        first = proposal()
        second = proposal()
        self.assertEqual(first, second)
        self.assertEqual(first["proposal_digest"], proposal_digest(first))
        self.assertEqual(first["authority"], "advisory-only")
        self.assertTrue(first["requires_explicit_override"])

    def test_tampering_or_missing_evidence_is_rejected(self):
        changed = proposal()
        changed["confidence"] = 0.99
        with self.assertRaisesRegex(AIProposalError, "digest"):
            validate_proposal(changed)
        no_evidence = proposal()
        no_evidence["evidence"] = []
        no_evidence["proposal_digest"] = proposal_digest(no_evidence)
        with self.assertRaisesRegex(AIProposalError, "evidence"):
            validate_proposal(no_evidence)

    def test_acceptance_still_requires_separate_human_override(self):
        accepted = proposal()
        accepted["human_acceptance"] = {"state": "accepted", "reviewer": "Alex", "reviewed_at": "2026-07-22T12:00:00Z", "reason": "Matches source"}
        accepted["proposal_digest"] = proposal_digest(accepted)
        with self.assertRaisesRegex(AIProposalError, "override"):
            authorize_with_override(accepted, {})
        override = {
            "target": accepted["target"],
            "behavior_patch": accepted["proposal"]["behavior_patch"],
            "provenance": {"author": "Alex", "reason": "Reviewed source evidence", "ai_proposal_id": accepted["proposal_id"], "ai_proposal_digest": accepted["proposal_digest"]},
        }
        self.assertEqual(authorize_with_override(accepted, override), override)


class MigrationTests(unittest.TestCase):
    def legacy(self):
        return {
            "schema_version": "0.1.0", "metadata": {"id": "demo"},
            "dependencies": [], "content": [{"kind": "item", "identifier": "demo:wand"}],
            "assets": [], "behaviors": [], "presentation": [{"id": "glow"}],
            "ui": [{"id": "menu"}], "networking": [], "unsupported": [],
        }

    def test_0_1_0_to_1_0_0_is_deterministic_and_non_mutating(self):
        source = self.legacy()
        before = copy.deepcopy(source)
        first = migrate_modir(source)
        second = migrate_modir(copy.deepcopy(source))
        self.assertEqual(first, second)
        self.assertEqual(source, before)
        self.assertEqual(first["schema_version"], "1.0.0")
        self.assertEqual(first["presentation_requirements"], [{"id": "glow"}])
        self.assertEqual(first["ui_intent"], [{"id": "menu"}])
        self.assertEqual(len(first["migration_provenance"][0]["source_sha256"]), 64)
        for field in ("registries", "state", "world_requirements", "diagnostics", "tests", "mods"):
            self.assertIn(field, first)

    def test_unknown_paths_and_unknown_legacy_fields_fail_closed(self):
        with self.assertRaisesRegex(MigrationError, "Unknown ModIR migration path"):
            migrate_modir({"schema_version": "0.2.0"})
        with self.assertRaisesRegex(MigrationError, "Unknown ModIR migration path"):
            migrate_modir(self.legacy(), "2.0.0")
        source = self.legacy()
        source["mystery"] = True
        with self.assertRaisesRegex(MigrationError, "Unknown ModIR 0.1.0 fields"):
            migrate_modir(source)


if __name__ == "__main__":
    unittest.main()
