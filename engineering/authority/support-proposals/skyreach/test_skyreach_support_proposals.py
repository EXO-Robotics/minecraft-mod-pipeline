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
BEDROCK = Path("/Users/blakegrove/Desktop/bedrock-server")
SPEC = importlib.util.spec_from_file_location("skyreach_support_builder", HERE / "build_skyreach_support_proposals.py")
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class SkyreachSupportProposalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tickets = ("W1-001-SR", "W1-003-STORM-NEST", "W1-004-SR")
        self.proposals = {ticket: load(HERE / f"{ticket}.json") for ticket in self.tickets}

    def test_only_three_authority_neutral_tickets(self) -> None:
        self.assertEqual({path.stem for path in HERE.glob("W1-*.json")}, set(self.tickets))
        for ticket, payload in self.proposals.items():
            self.assertEqual(payload["ticket_id"], ticket)
            self.assertEqual(payload["status"], "PROPOSED_NOT_RATIFIED")
            self.assertEqual(payload["authority_effect"], "NONE_UNTIL_RATIFIED_IN_REPLACEMENT_DECISION_LEDGER")
            self.assertEqual(payload["source_commit"], BUILDER.BASE_COMMIT)
            self.assertEqual(payload["source_tree"], BUILDER.BASE_TREE)
            self.assertFalse(payload["scope_guard"]["decision_ledger_mutation"])
            self.assertFalse(payload["scope_guard"]["pack_implementation_authorized"])
            self.assertEqual(payload["scope_guard"]["w1_creative_005_status"], "DEFERRED_UNCHANGED")
            self.assertEqual(set(payload["scope_guard"]["w1_creative_005_sidegrades_absent"]), BUILDER.SIDEGRADES)

    def test_bound_sources_match_current_bytes(self) -> None:
        for relative, expected in BUILDER.SOURCE_HASHES.items():
            candidate = REPO / relative
            if not candidate.is_file():
                candidate = BEDROCK / relative
            self.assertTrue(candidate.is_file(), relative)
            self.assertEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(), expected, relative)

    def test_identity_proposal_is_exact_subset_and_creates_no_extra_identity(self) -> None:
        original = load(REPO / "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json")["proposal"]
        selected = self.proposals["W1-001-SR"]["proposal"]
        original_aliases = {(term, row["canonical_id"]) for row in original["aliases"] for term in row["terms"]}
        selected_aliases = {(term, row["canonical_id"]) for row in selected["aliases"] for term in row["terms"]}
        self.assertEqual({term for term, _ in selected_aliases}, BUILDER.SKY_ALIAS_TERMS)
        self.assertTrue(selected_aliases <= original_aliases)
        self.assertEqual(set(selected["narrative_codex_only"]), BUILDER.SKY_NARRATIVE_TERMS)
        self.assertEqual({row["id"] for row in selected["new_required_items"]}, BUILDER.SKY_NEW_ITEM_IDS)
        self.assertEqual(selected["additional_inventory_identities_created_by_this_tranche"], [])
        self.assertEqual(set(selected["skyreach_creative_doc_only_resolutions"]["narrative_codex_only"]), {"Sky Milk Curd", "Stolen Shiny", "Carrion Charm", "Harpy Song Flute"})
        serialized = json.dumps(selected, sort_keys=True)
        for sidegrade in BUILDER.SIDEGRADES:
            self.assertNotIn(sidegrade, serialized)

    def test_storm_nest_uses_exact_creative_phases_and_attacks(self) -> None:
        proposal = self.proposals["W1-003-STORM-NEST"]["proposal"]
        self.assertEqual([row["id"] for row in proposal["phases"]], ["nest_guard", "wind_roads", "harpy_dirge", "storm_crown"])
        attacks = {attack for phase in proposal["phases"] for attack in phase["attacks"]}
        expected = {"wing_buffet", "talon_pin", "gale_dive", "feather_knives", "call_of_the_nest", "storm_screech"}
        self.assertEqual(attacks, expected)
        self.assertEqual(set(proposal["timing_seconds"]) - {"global_attack_cooldown"}, expected)
        self.assertFalse(proposal["ecology_or_natural_form_can_complete_chapter"])
        self.assertEqual(proposal["explicit_nondecisions"]["damage_values"], "NOT_CREATED")
        self.assertEqual(proposal["explicit_nondecisions"]["attack_effect_radii"], "NOT_CREATED")
        self.assertIn("no_new_radius", proposal["reset"]["leash_boundary"])

    def test_storm_nest_state_is_bounded_and_idempotent(self) -> None:
        proposal = self.proposals["W1-003-STORM-NEST"]["proposal"]
        self.assertEqual(proposal["all_numeric_values_status"], "PROPOSED_NOT_RATIFIED")
        self.assertEqual(proposal["new_numbers_proposed_not_ratified"]["attack_timing_seconds"], proposal["timing_seconds"])
        self.assertEqual(proposal["health"]["participant_cap"], 4)
        self.assertFalse(proposal["arena_state"]["persistent_world_block_mutation"])
        self.assertTrue(proposal["arena_state"]["reset_restores_authored_arena_state"])
        self.assertEqual(proposal["add_semantics"]["overflow_queue"], "FORBIDDEN")
        self.assertEqual(proposal["persistence"]["schema"], "existing_G8_schema_only_no_new_domain")
        forbidden = set(proposal["ecology_separation"]["natural_or_command_wind_roc_must_not"])
        self.assertIn("drop_or_deliver_storm_pinion", forbidden)
        order = proposal["terminal_semantics"]["ordered_idempotent_transition"]
        self.assertLess(order.index("write_player_reward_entitlement_once"), order.index("fulfill_physical_pinion_at_most_once_or_leave_recovery_entitlement"))

    def test_loot_proposal_inherits_global_bands_and_only_pinion_progresses(self) -> None:
        original = load(REPO / "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json")["proposal"]
        selected = self.proposals["W1-004-SR"]["proposal"]
        for key in ("probability_and_quantity_envelopes", "boss_package", "structure_chest_bands", "arena_reward_guard", "tuning_rule"):
            self.assertEqual(selected[key], original[key], key)
        resolution = selected["skyreach_resolution"]
        self.assertEqual(resolution["chapter_critical_seal"], "aionbound:storm_pinion")
        self.assertEqual(resolution["chapter_critical_seal_count"], 1)
        self.assertFalse(resolution["ecology_or_natural_wind_roc_can_drop_chapter_seal"])
        for semantics in resolution["mastery_only_rewards"].values():
            self.assertFalse(semantics["inventory_identity_created"])
            self.assertFalse(semantics["progression_substitute"])
            self.assertFalse(semantics["may_fill_pilgrim_seal_slot"])
        self.assertFalse(resolution["recovery_claim"]["new_UI"])
        self.assertFalse(resolution["recovery_claim"]["museum_claim"])
        self.assertEqual(resolution["repeat_clear"]["storm_pinion_entitlement"], "not_reissued")
        self.assertEqual(resolution["repeat_clear"]["virtual_seal_credit"], "not_reissued")

    def test_generated_outputs_are_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            BUILDER.write_outputs(out)
            for ticket in self.tickets:
                for suffix in ("json", "md"):
                    self.assertEqual((out / f"{ticket}.{suffix}").read_bytes(), (HERE / f"{ticket}.{suffix}").read_bytes())


if __name__ == "__main__":
    unittest.main()
