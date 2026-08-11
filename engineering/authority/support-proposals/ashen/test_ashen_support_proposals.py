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
            if path == "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json":
                # The proposals are immutable historical inputs. After explicit
                # ratification, the replacement ledger must change while the
                # proposal's bound pre-ratification source hash remains fixed.
                ledger = load(REPO / path)
                approved = {row["tranche"]: row for row in ledger["ratifications"]["approved"]}
                for tranche in ("W1-001-AH", "W1-003-KILN-SKY", "W1-004-AH"):
                    proposal = REPO / approved[tranche]["proposal"]
                    self.assertEqual(hashlib.sha256(proposal.read_bytes()).hexdigest(), approved[tranche]["proposal_sha256"])
                continue
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
        semantics = selected["drake_scale_selection_semantics"]
        self.assertEqual(semantics["row_copy"], "verbatim")
        self.assertEqual(semantics["authority_granted"], "identity_only")
        self.assertIn("NONE_WHILE_W1-CREATIVE-005_IS_DEFERRED", semantics["upgrade_or_sidegrade_authority"])

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
        self.assertIn("pre_existing_Packet006", resolution["chapter_critical_seal_identity_source"])
        core = resolution["ember_forge_core"]
        self.assertIn("pre_existing_Packet006", core["identity_source"])
        roll = core["kiln_sky_optional_reward_roll"]
        self.assertEqual(roll["classification"], "E_elite")
        self.assertEqual(roll["chance"], original["probability_and_quantity_envelopes"]["E"]["chance_elite"])
        self.assertEqual(roll["quantity"], original["probability_and_quantity_envelopes"]["E"]["quantity"])
        self.assertEqual(roll["rolls"], original["probability_and_quantity_envelopes"]["E"]["rolls"])
        recovery = resolution["recovery_claim"]
        self.assertFalse(recovery["new_UI"])
        self.assertFalse(recovery["museum_claim"])
        self.assertIn("reuse_one_existing_arena_claim_interaction_hook", recovery["interaction_hook"])
        self.assertIn("supersedes", resolution["resolution_precedence"])
        self.assertIn("no claim UI or museum", resolution["resolution_precedence"])
        self.assertLess(recovery["claim_order"].index("confirm_seal_credit_true"), recovery["claim_order"].index("write_physical_horn_claimed_true_once"))
        self.assertLess(recovery["claim_order"].index("confirm_reward_entitlement_true"), recovery["claim_order"].index("write_physical_horn_claimed_true_once"))

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

    def test_health_snapshot_is_immutable_separate_and_uniquely_capped(self) -> None:
        proposal = self.proposals["W1-003-KILN-SKY"]["proposal"]
        health = proposal["health"]
        multiplayer = proposal["multiplayer"]
        self.assertEqual(health["participant_cap"], 4)
        self.assertEqual(multiplayer["hard_unique_player_cap_for_each_set"], 4)
        self.assertTrue(health["reward_participant_set_is_separate"])
        self.assertEqual(health["unique_count_definition"], "clamp(count(unique scaling_participant_snapshot player ids),1,4)")
        self.assertEqual(health["max_health_formula"], "480 * (1 + 0.30 * (N_pull - 1))")
        self.assertFalse(health["late_join_changes_max_health"])
        self.assertFalse(health["departure_or_disconnect_changes_max_health"])
        self.assertIn("immutable_at_pull", multiplayer["health_scaling_snapshot"])

    def test_pull_and_late_join_use_automatic_continuous_predicates(self) -> None:
        multiplayer = self.proposals["W1-003-KILN-SKY"]["proposal"]["multiplayer"]
        self.assertIn("same_5_second_continuous_residency", multiplayer["pull_initiator"])
        self.assertIn("initiator_then_longest_continuous_residency", multiplayer["pull_selection_when_more_than_four_qualify"])
        late = multiplayer["late_join_predicate"]
        self.assertEqual(late["workflow"], "automatic_predicate_not_manual_approval")
        self.assertEqual(late["continuous_residency_seconds"], 15)
        self.assertEqual(late["must_complete_during_phase"], ["ash_landing", "vent_choir"])
        self.assertEqual(late["timer_resets_on"], ["arena_exit", "death", "disconnect"])
        self.assertIn("cancel_all_pending_timers", late["glass_wing_entry"])
        self.assertFalse(late["health_rescale"])
        self.assertNotIn("approved_late_join", json.dumps(multiplayer, sort_keys=True))

    def test_phase_boundaries_and_cooldown_composition_are_exact(self) -> None:
        proposal = self.proposals["W1-003-KILN-SKY"]["proposal"]
        self.assertEqual(
            [row["health_fraction_interval_while_alive"] for row in proposal["phases"]],
            ["0.70 < h <= 1.00", "0.40 < h <= 0.70", "0.15 < h <= 0.40", "0.00 < h <= 0.15"],
        )
        self.assertIn("exact 0.70, 0.40, or 0.15", proposal["phase_boundary_rule"])
        cooldown = proposal["cooldown_composition"]
        self.assertIn("both_global_and_that_attack_specific", cooldown["next_attack_gate"])
        self.assertEqual(cooldown["effective_ready_time"], "max(global_cooldown_ready_time,selected_attack_cooldown_ready_time)")

    def test_mite_cap_clamps_without_queue_and_phases_down_oldest(self) -> None:
        semantics = self.proposals["W1-003-KILN-SKY"]["proposal"]["ash_mite_cap_semantics"]
        self.assertEqual(semantics["effective_cap"], "min(current_phase.active_ash_mite_cap,multiplayer.global_session_ash_mite_cap)")
        self.assertIn("min(rolled_spawn_count", semantics["spawn_accept_count"])
        self.assertIn("FORBIDDEN", semantics["overflow_queue"])
        self.assertIn("oldest_excess", semantics["phase_cap_reduction"])
        self.assertEqual(semantics["phase_down_effects"], "no_loot_no_kill_credit_no_reward_event")

    def test_terminal_eligibility_abandon_disconnect_and_reset_precedence(self) -> None:
        proposal = self.proposals["W1-003-KILN-SKY"]["proposal"]
        terminal = proposal["terminal_semantics"]
        self.assertEqual(terminal["eligible_set_source"], "reward_participant_set_only")
        self.assertEqual(len(terminal["eligible_at_terminal_if"]), 3)
        self.assertTrue(any("recorded_dead_during_current_active_session" in row for row in terminal["eligible_at_terminal_if"]))
        self.assertTrue(any("60_seconds" in row for row in terminal["eligible_at_terminal_if"]))
        self.assertIn("removed permanently", terminal["voluntary_abandon_loss_rule"])
        reset = proposal["reset"]
        self.assertIn("does not pause reset clocks", reset["disconnect_semantics"])
        self.assertEqual([row["order"] for row in reset["precedence"]], [1, 2, 3, 4, 5])
        self.assertEqual(reset["precedence"][0]["event"], "valid_arena_form_death")

    def test_completion_alias_and_ordered_claim_are_not_duplicate_semantics(self) -> None:
        proposal = self.proposals["W1-003-KILN-SKY"]["proposal"]
        persistence = proposal["persistence"]
        self.assertNotIn("player_completion_key", persistence)
        self.assertEqual(persistence["player_completion_semantic"], "alias_of_seal_credit_key_no_separate_player_completion_key")
        order = proposal["terminal_semantics"]["ordered_idempotent_player_transition"]
        claimed_index = next(i for i, row in enumerate(order) if "physical_horn_claimed" in row)
        self.assertLess(next(i for i, row in enumerate(order) if "seal_credit" in row), claimed_index)
        self.assertLess(next(i for i, row in enumerate(order) if "reward_entitlement" in row), claimed_index)
        self.assertIn("reuse_one_existing_arena_claim_interaction_hook", proposal["terminal_semantics"]["recovery_surface"])
        self.assertIn("no_new_UI_or_museum", proposal["terminal_semantics"]["recovery_surface"])

    def test_natural_drake_cannot_enter_arena_reward_or_key_paths(self) -> None:
        separation = self.proposals["W1-003-KILN-SKY"]["proposal"]["arena_vs_ecology_separation"]
        forbidden = set(separation["natural_or_ecology_ash_drake_must_not"])
        self.assertEqual(separation["tag_writer"], "active_kiln_sky_arena_session_spawn_path_only")
        self.assertIn("receive_arena_apex_tag", forbidden)
        self.assertIn("join_or_create_kiln_sky_session", forbidden)
        self.assertIn("write_world_completion_key", forbidden)
        self.assertIn("write_player_seal_credit_or_reward_entitlement", forbidden)
        self.assertIn("write_physical_horn_claimed_key", forbidden)
        self.assertIn("drop_or_deliver_ash_drake_horn", forbidden)

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
