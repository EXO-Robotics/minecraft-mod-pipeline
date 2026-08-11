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
BEDROCK = next(parent for parent in REPO.parents if (parent / "program/crazycraft-pack-production-v1").is_dir())

SPEC = importlib.util.spec_from_file_location("crystal_support_builder", HERE / "build_crystal_marsh_support_proposals.py")
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class CrystalMarshSupportProposalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.proposals = {
            stem: load(HERE / f"{stem}.json")
            for stem in ("W1-001-CM", "W1-003-PEARL-DEPTHS", "W1-004-CM")
        }

    def test_authority_neutral_and_hash_bound(self) -> None:
        for ticket, payload in self.proposals.items():
            self.assertEqual(payload["ticket_id"], ticket)
            self.assertEqual(payload["status"], "PROPOSED_NOT_RATIFIED")
            self.assertEqual(payload["authority_effect"], "NONE_UNTIL_RATIFIED_IN_REPLACEMENT_DECISION_LEDGER")
            self.assertEqual(payload["source_commit"], BUILDER.BASE_COMMIT)
            self.assertEqual(payload["source_tree"], BUILDER.BASE_TREE)
            self.assertFalse(payload["scope_guard"]["pack_implementation_authorized"])
            self.assertFalse(payload["scope_guard"]["scope_broadening"])
            self.assertEqual(payload["scope_guard"]["w1_creative_005_status"], "DEFERRED_UNCHANGED")
            for binding in payload["source_bindings"]:
                self.assertEqual(binding["sha256"], BUILDER.SOURCE_HASHES[binding["path"]])

    def test_bound_sources_match_current_bytes(self) -> None:
        for relative, expected in BUILDER.SOURCE_HASHES.items():
            if relative == "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json":
                # The immutable proposals bind the pre-ratification ledger.
                # After explicit approval, the replacement ledger changes and
                # must instead hash-bind the three preserved proposal bytes.
                ledger = load(REPO / relative)
                approved = {row["tranche"]: row for row in ledger["ratifications"]["approved"]}
                for tranche in ("W1-001-CM", "W1-003-PEARL-DEPTHS", "W1-004-CM"):
                    proposal = REPO / approved[tranche]["proposal"]
                    self.assertEqual(hashlib.sha256(proposal.read_bytes()).hexdigest(), approved[tranche]["proposal_sha256"])
                continue
            candidate = REPO / relative
            if not candidate.is_file():
                candidate = BEDROCK / relative
            self.assertTrue(candidate.is_file(), relative)
            self.assertEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(), expected, relative)

    def test_w1_001_cm_is_exact_global_subset_plus_no_new_identity_resolutions(self) -> None:
        original = load(REPO / "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json")["proposal"]
        selected = self.proposals["W1-001-CM"]["proposal"]
        original_aliases = {(term, row["canonical_id"]) for row in original["aliases"] for term in row["terms"]}
        selected_aliases = {(term, row["canonical_id"]) for row in selected["aliases"] for term in row["terms"]}
        self.assertEqual({term for term, _ in selected_aliases}, BUILDER.CRYSTAL_ALIAS_TERMS)
        self.assertTrue(selected_aliases <= original_aliases)
        self.assertEqual(set(selected["narrative_codex_only"]), BUILDER.CRYSTAL_NARRATIVE_TERMS)
        self.assertEqual(set(selected["removed_or_context_only"]), BUILDER.CRYSTAL_REMOVED_TERMS)
        self.assertEqual({row["id"] for row in selected["new_required_items"]}, BUILDER.CRYSTAL_NEW_ITEM_IDS)
        self.assertEqual(selected["additional_inventory_identities_created_by_this_tranche"], [])
        doc = selected["crystal_creative_doc_only_resolutions"]
        self.assertEqual({row["term"] for row in doc["existing_ledger_aliases"]}, {"Glass Algae Film", "Flood Crystal Shard"})
        self.assertEqual(set(doc["narrative_codex_only"]), {"Frog Song Stone", "Dragonfly Pin", "Turtle Breath Stone", "Watcher Journal Scrap"})
        self.assertEqual(doc["alias_without_new_identity"], [{
            "term": "Claw",
            "canonical_id": "aionbound:wet_chitin",
            "reason": "bloom_crab creature-part prose used as a sickle blank; warehouse-first policy retains the authored purpose without a tenth inventory identity",
        }])
        self.assertIn("DEFERRED", selected["w1_creative_005_effect"])

    def test_pearl_depths_uses_exact_creative_phases_and_attacks(self) -> None:
        proposal = self.proposals["W1-003-PEARL-DEPTHS"]["proposal"]
        self.assertEqual([row["id"] for row in proposal["phases"]], ["fog_rise", "choir_below", "mask_unsealed", "flood_claim"])
        attacks = {attack for phase in proposal["phases"] for attack in phase["attacks"]}
        expected = {"silt_grasp", "prism_lance", "wail", "reed_serpent_call", "pearl_orbit", "drown_hymn"}
        self.assertEqual(attacks, expected)
        self.assertEqual(set(proposal["timing_seconds"]) - {"global_attack_cooldown"}, expected)
        self.assertFalse(proposal["ecology_or_natural_form_can_complete_chapter"])
        self.assertIn("NOT_CREATED", proposal["explicit_nondecisions"]["damage_values"])
        self.assertIn("NOT_CREATED", proposal["explicit_nondecisions"]["attack_effect_radii"])
        self.assertIn("no_new_radius", proposal["reset"]["leash_boundary"])

    def test_pearl_depths_numbers_are_explicitly_proposed_and_runtime_state_is_bounded(self) -> None:
        proposal = self.proposals["W1-003-PEARL-DEPTHS"]["proposal"]
        self.assertEqual(proposal["all_numeric_values_status"], "PROPOSED_NOT_RATIFIED")
        summary = proposal["new_numbers_proposed_not_ratified"]
        self.assertEqual(summary["solo_health"], proposal["health"]["solo"])
        self.assertEqual(summary["phase_exit_health_fractions"], [phase["exit_at_health_fraction"] for phase in proposal["phases"]])
        self.assertEqual(summary["global_attack_cooldown_seconds"], proposal["timing_seconds"]["global_attack_cooldown"])
        self.assertEqual(summary["attack_timing_seconds"], proposal["timing_seconds"])
        self.assertEqual(proposal["health"]["participant_cap"], 4)
        self.assertFalse(proposal["health"]["late_join_changes_max_health"])
        self.assertFalse(proposal["arena_state"]["persistent_world_block_mutation"])
        self.assertTrue(proposal["arena_state"]["reset_restores_authored_arena_state"])
        self.assertEqual(proposal["add_semantics"]["overflow_queue"], "FORBIDDEN")
        self.assertEqual(proposal["persistence"]["schema"], "existing_G8_schema_only_no_new_domain")

    def test_pearl_depths_ecology_and_terminal_guards(self) -> None:
        proposal = self.proposals["W1-003-PEARL-DEPTHS"]["proposal"]
        forbidden = set(proposal["ecology_separation"]["natural_marsh_wight_must_not"])
        self.assertIn("drop_or_deliver_marsh_wight_mask", forbidden)
        self.assertIn("write_completion_or_reward_keys", forbidden)
        order = proposal["terminal_semantics"]["ordered_idempotent_transition"]
        self.assertLess(order.index("write_player_seal_credit_once"), order.index("fulfill_physical_mask_at_most_once_or_leave_recovery_entitlement"))
        self.assertLess(order.index("write_player_reward_entitlement_once"), order.index("fulfill_physical_mask_at_most_once_or_leave_recovery_entitlement"))
        self.assertIn("do_not", proposal["terminal_semantics"]["repeat_clear"])

    def test_w1_004_cm_copies_global_bands_and_binds_only_mask_as_seal(self) -> None:
        original = load(REPO / "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json")["proposal"]
        selected = self.proposals["W1-004-CM"]["proposal"]
        for key in ("probability_and_quantity_envelopes", "boss_package", "structure_chest_bands", "arena_reward_guard", "tuning_rule"):
            self.assertEqual(selected[key], original[key], key)
        resolution = selected["crystal_marsh_resolution"]
        self.assertEqual(resolution["chapter_critical_seal"], "aionbound:marsh_wight_mask")
        self.assertEqual(resolution["chapter_critical_seal_count"], 1)
        self.assertFalse(resolution["ecology_or_natural_marsh_wight_can_drop_chapter_seal"])
        self.assertEqual(set(resolution["mastery_only_trophies"]), {
            "aionbound:moon_pearl_pedestal", "aionbound:crystal_obelisk_fragment", "aionbound:marsh_idol",
        })
        for semantics in resolution["mastery_only_trophies"].values():
            self.assertFalse(semantics["progression_substitute"])
            self.assertFalse(semantics["may_fill_pilgrim_seal_slot"])
        recovery = resolution["recovery_claim"]
        self.assertFalse(recovery["new_UI"])
        self.assertFalse(recovery["museum_claim"])
        self.assertIn("supersedes", resolution["resolution_precedence"])
        self.assertEqual(resolution["repeat_clear"]["marsh_wight_mask_entitlement"], "not_reissued")
        self.assertEqual(resolution["repeat_clear"]["virtual_seal_credit"], "not_reissued")

    def test_generated_outputs_are_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            BUILDER.write_outputs(out)
            for ticket in self.proposals:
                for suffix in ("json", "md"):
                    self.assertEqual((out / f"{ticket}.{suffix}").read_bytes(), (HERE / f"{ticket}.{suffix}").read_bytes())


if __name__ == "__main__":
    unittest.main()
