#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]

SPEC = importlib.util.spec_from_file_location("ashen_support_builder", HERE / "build_ashen_support_proposals.py")
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class AshenSupportProposalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.proposals = {stem: load(HERE / f"{stem}.json") for stem in ("W1-001-AH", "W1-004-AH", "W1-003-KILN-SKY")}

    def test_all_proposals_are_authority_neutral_and_hash_bound(self) -> None:
        for ticket, payload in self.proposals.items():
            self.assertEqual(payload["ticket_id"], ticket)
            self.assertEqual(payload["status"], "PROPOSED_NOT_RATIFIED")
            self.assertEqual(payload["authority_effect"], "NONE_UNTIL_RATIFIED_IN_REPLACEMENT_DECISION_LEDGER")
            self.assertEqual(payload["source_commit"], BUILDER.BASE_COMMIT)
            self.assertEqual(payload["source_tree"], BUILDER.BASE_TREE)
            self.assertFalse(payload["scope_guard"]["pack_implementation_authorized"])
            self.assertFalse(payload["scope_guard"]["scope_broadening"])
            for binding in payload["source_bindings"]:
                self.assertRegex(binding["sha256"], r"^[0-9a-f]{64}$")
                self.assertEqual(binding["sha256"], BUILDER.SOURCE_HASHES[binding["path"]])

    def test_repository_sources_retain_bound_hashes(self) -> None:
        for path, expected in BUILDER.SOURCE_HASHES.items():
            candidate = REPO / path
            if not candidate.is_file():
                continue
            actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
            self.assertEqual(actual, expected, path)

    def test_w1_001_ah_is_exact_existing_subset_and_adds_no_identity(self) -> None:
        original = load(REPO / "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json")["proposal"]
        selected = self.proposals["W1-001-AH"]["proposal"]
        original_alias_pairs = {(term, row["canonical_id"]) for row in original["aliases"] for term in row["terms"]}
        selected_alias_pairs = {(term, row["canonical_id"]) for row in selected["aliases"] for term in row["terms"]}
        self.assertEqual({term for term, _ in selected_alias_pairs}, BUILDER.ASHEN_ALIAS_TERMS)
        self.assertTrue(selected_alias_pairs <= original_alias_pairs)
        self.assertEqual(set(selected["narrative_codex_only"]), BUILDER.ASHEN_NARRATIVE_TERMS)
        self.assertTrue(set(selected["narrative_codex_only"]) <= set(original["narrative_codex_only"]))
        self.assertEqual(set(selected["removed_or_context_only"]), BUILDER.ASHEN_CONTEXT_TERMS)
        self.assertTrue(set(selected["removed_or_context_only"]) <= set(original["removed_or_context_only"]))
        drake = next(row for row in original["new_required_items"] if row["id"] == "aionbound:drake_scale")
        self.assertEqual(selected["new_required_items"], [drake])
        self.assertEqual(selected["new_inventory_identities_created_by_this_selection"], [])

    def test_w1_004_ah_copies_global_envelopes_and_protects_seal_semantics(self) -> None:
        original = load(REPO / "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json")["proposal"]
        selected = self.proposals["W1-004-AH"]["proposal"]
        for key in ("probability_and_quantity_envelopes", "boss_package", "structure_chest_bands", "arena_reward_guard", "tuning_rule"):
            self.assertEqual(selected[key], original[key], key)
        resolution = selected["ashen_resolution"]
        self.assertEqual(resolution["chapter_critical_seal"], "aionbound:ash_drake_horn")
        self.assertEqual(resolution["chapter_critical_seal_count"], 1)
        self.assertFalse(resolution["ecology_or_natural_ash_drake_can_drop_chapter_seal"])
        self.assertFalse(resolution["ember_forge_core"]["progression_substitute_for_ash_drake_horn"])
        self.assertFalse(resolution["ember_forge_core"]["may_fill_pilgrim_seal_slot"])
        self.assertEqual(resolution["repeat_clear"]["ash_drake_horn_entitlement"], "not_reissued")
        self.assertEqual(resolution["repeat_clear"]["virtual_seal_credit"], "not_reissued")

    def test_kiln_sky_has_exact_creative_phases_and_attacks(self) -> None:
        proposal = self.proposals["W1-003-KILN-SKY"]["proposal"]
        phases = proposal["phases"]
        self.assertEqual([row["id"] for row in phases], ["ash_landing", "vent_choir", "glass_wing", "kiln_heart"])
        attacks = {attack for row in phases for attack in row["available_attacks"]}
        expected = {"cinder_breath", "tail_slag", "thermal_dive", "mite_shake", "basalt_quake", "glass_feather_storm"}
        self.assertEqual(attacks, expected)
        self.assertEqual(set(proposal["timing_seconds"]) - {"global_attack_cooldown"}, expected)
        self.assertEqual([row["exit_at_health_fraction"] for row in phases], [0.7, 0.4, 0.15, 0.0])
        self.assertLessEqual(max(row["active_ash_mite_cap"] for row in phases), proposal["multiplayer"]["global_session_ash_mite_cap"])
        self.assertEqual(proposal["reset"]["leash_boundary"], "authored_kiln_sky_arena_volume_no_new_radius_number")
        self.assertIn("NOT_CREATED", proposal["explicit_nondecisions"]["damage_values"])
        self.assertIn("NOT_CREATED", proposal["explicit_nondecisions"]["attack_effect_radii"])
        self.assertFalse(proposal["ecology_or_natural_form_can_complete_chapter"])

    def test_generated_outputs_are_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            BUILDER.write_outputs(out)
            for ticket in self.proposals:
                for suffix in ("json", "md"):
                    expected = HERE / f"{ticket}.{suffix}"
                    actual = out / expected.name
                    self.assertEqual(actual.read_bytes(), expected.read_bytes(), expected.name)


if __name__ == "__main__":
    unittest.main()
