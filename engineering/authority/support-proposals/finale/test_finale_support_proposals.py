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
BEDROCK_CANDIDATES = [*REPO.parents, Path("/Users/blakegrove/Desktop/bedrock-server")]
BEDROCK = next(parent for parent in BEDROCK_CANDIDATES if (parent / "program/crazycraft-pack-production-v1").is_dir())

SPEC = importlib.util.spec_from_file_location("finale_support_builder", HERE / "build_finale_support_proposals.py")
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class FinaleSupportProposalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.proposals = {ticket: load(HERE / f"{ticket}.json") for ticket in BUILDER.build_all()}

    def test_authority_neutral_hash_bound_and_no_product_authority(self) -> None:
        for ticket, payload in self.proposals.items():
            self.assertEqual(payload["ticket_id"], ticket)
            self.assertEqual(payload["status"], "PROPOSED_NOT_RATIFIED")
            self.assertEqual(payload["authority_effect"], "NONE_UNTIL_RATIFIED_IN_REPLACEMENT_DECISION_LEDGER")
            self.assertEqual(payload["source_commit"], BUILDER.BASE_COMMIT)
            self.assertEqual(payload["source_tree"], BUILDER.BASE_TREE)
            guard = payload["scope_guard"]
            self.assertFalse(guard["pack_or_runtime_mutation_authorized"])
            self.assertFalse(guard["decision_ledger_mutation"])
            self.assertFalse(guard["native_asset_work_authorized"])
            self.assertFalse(guard["candidate_or_runtime_proof_claimed"])
            self.assertEqual(guard["w1_creative_005_status"], "DEFERRED_UNCHANGED")

    def test_source_hashes_match_exact_current_bytes(self) -> None:
        bound = {row["path"]: row["sha256"] for payload in self.proposals.values() for row in payload["source_bindings"]}
        self.assertEqual(bound, {path: BUILDER.SOURCE_HASHES[path] for path in bound})
        for relative, expected in BUILDER.SOURCE_HASHES.items():
            candidate = REPO / relative
            if not candidate.is_file():
                candidate = BEDROCK / relative
            self.assertTrue(candidate.is_file(), relative)
            if relative == "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json":
                # The immutable proposal binds the pre-ratification ledger.
                # The current replacement ledger instead closes provenance by
                # ratifying each proposal's exact byte hash.
                approved = {
                    row["tranche"]: row
                    for row in load(candidate)["ratifications"]["approved"]
                }
                for ticket in self.proposals:
                    self.assertEqual(approved[ticket]["proposal_sha256"], hashlib.sha256((HERE / f"{ticket}.json").read_bytes()).hexdigest())
                continue
            self.assertEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(), expected, relative)

    def test_w1_002_closes_only_narrowed_identity_container_and_exit_surface(self) -> None:
        p = self.proposals["W1-002-TWINBOND"]["proposal"]
        self.assertEqual(p["finale_container"]["choice"], "SAME_WORLD_SINGLE_AUTHORED_FINALE_SITE")
        self.assertEqual(p["finale_container"]["dimension"], "minecraft:overworld")
        self.assertFalse(p["finale_container"]["new_dimension_or_portal_system"])
        self.assertFalse(p["finale_container"]["old_isolated_logical_twinbond_container_adopted"])
        self.assertEqual(p["prepared_site_binding"]["declared_size"], [128, 48, 128])
        self.assertEqual(p["prepared_site_binding"]["anchors"]["center_relic_trial"], [64, 12, 64])
        rewards = p["secondary_reward_presentation"]
        self.assertFalse(rewards["concord_spark"]["inventory_item"])
        self.assertEqual(rewards["memory_of_four_lands"]["canonical_id"], "aionbound:memory_of_four_lands")
        self.assertFalse(rewards["memory_of_four_lands"]["placeable_block_or_entity"])
        self.assertFalse(rewards["mastery_sigil"]["new_item_or_icon"])
        self.assertTrue(p["machine_exit_dependency"]["twinbond_durable_completion_required"])
        self.assertTrue(p["machine_exit_dependency"]["trophy_edge_ignition_required"])
        self.assertFalse(p["machine_exit_dependency"]["memory_of_four_lands_required"])
        self.assertFalse(p["machine_exit_dependency"]["post_clear_mastery_or_mastery_stamp_required"])

    def test_w1_003_preserves_balance_and_bounds_four_phase_execution(self) -> None:
        p = self.proposals["W1-003-TWINBOND"]["proposal"]
        self.assertEqual(p["balance_preservation"]["entity_component_health_each"], 160)
        self.assertEqual(p["balance_preservation"]["entity_component_attack_damage_each"], 8)
        self.assertFalse(p["balance_preservation"]["multiplayer_health_scaling"])
        self.assertEqual([phase["id"] for phase in p["phases"]], ["split_approach", "concord_pressure", "relic_trial", "finale_ignition"])
        self.assertEqual(p["phase_thresholds"]["split_approach_exit"], "both aspects at or below 0.70 health fraction")
        self.assertEqual(p["phase_thresholds"]["concord_pressure_exit"], "both aspects at or below 0.40 health fraction")
        self.assertEqual(p["phase_thresholds"]["individual_aspect_death_before_terminal"], "FORBIDDEN")
        self.assertEqual(p["timing_seconds"]["relic_trial_channel_required"], 12.0)
        self.assertEqual(p["timing_seconds"]["finale_ignition"], 5.0)
        self.assertEqual(p["multiplayer"]["participant_cap"], 4)
        self.assertFalse(p["multiplayer"]["late_join_after_relic_trial_begins"])
        self.assertFalse(p["reset"]["persistent_world_block_mutation"])
        self.assertEqual(p["persistence"]["schema"], "existing_G8_schema_only_no_new_domain")
        self.assertEqual(p["persistence"]["active_fight"], "not_persisted")
        self.assertFalse(p["terminal_semantics"]["individual_aspect_death_or_command_kill_completes"])
        order = p["terminal_semantics"]["ordered_transition"]
        self.assertLess(order.index("write synchronous terminal lock for encounter session"), order.index("write durable world Twinbond completion once"))
        self.assertIn("never falls through", p["terminal_semantics"]["repeat_or_recovery_entry"])

    def test_w1_004_guarantees_identity_bounded_package_and_recovery(self) -> None:
        p = self.proposals["W1-004-TWINBOND"]["proposal"]
        package = p["first_eligible_clear_package"]
        self.assertEqual(package["twinbond_relic"]["id"], "aionbound:twinbond_relic")
        self.assertEqual(package["twinbond_relic"]["chance"], 1.0)
        self.assertEqual(package["memory_completion"]["maximum_missing_credits"], 4)
        self.assertFalse(package["mastery_stamp"]["progression_required"])
        self.assertEqual(package["random_material_or_catalyst_package"], "NONE_CREATED_BY_THIS_PROPOSAL")
        self.assertFalse(p["global_envelope_relationship"]["new_loot_identity"])
        self.assertTrue(p["global_envelope_relationship"]["finale_is_not_a_repeat_grind"])
        self.assertIn("do not fall through", p["recovery"]["full_inventory"])
        self.assertIn("at-most-once", p["recovery"]["crash_boundary"])
        for key, value in p["repeat_clear"].items():
            if key.startswith("duplicate_"):
                self.assertFalse(value)
        self.assertFalse(p["repeat_clear"]["new_encounter_after_durable_completion"])

    def test_retired_path_is_only_preserved_as_forbidden(self) -> None:
        expected = set(BUILDER.FORBIDDEN_INHERITANCE)
        for payload in self.proposals.values():
            self.assertEqual(set(payload["proposal"]["forbidden_inheritance"]), expected)
            copy = json.loads(json.dumps(payload))
            del copy["proposal"]["forbidden_inheritance"]
            text = json.dumps(copy)
            for forbidden in expected:
                self.assertNotIn(forbidden, text)

    def test_generated_outputs_are_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            BUILDER.write_outputs(out)
            for ticket in self.proposals:
                for suffix in ("json", "md"):
                    self.assertEqual((out / f"{ticket}.{suffix}").read_bytes(), (HERE / f"{ticket}.{suffix}").read_bytes())


if __name__ == "__main__":
    unittest.main()
