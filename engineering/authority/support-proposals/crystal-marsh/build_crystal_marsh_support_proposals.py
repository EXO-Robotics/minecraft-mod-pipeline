#!/usr/bin/env python3
"""Build the authority-neutral Crystal Marsh Creative support tranche."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]

BASE_COMMIT = "fa2960e8c68a7dde740fac421cf0ea941bbcb6e1"
BASE_TREE = "cf6d5571b8119d0655adcac0466dea54fb2f3d48"

SOURCE_HASHES = {
    "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json": "b554db9fab3fe16e59e2e3b36dfc310ff462078b170f14e1f9fe8a46999bbd0c",
    "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json": "a9bc8133f8a0aacf7db258ffe76fc04dd9fcc6d07713bef630e074bd48588786",
    "engineering/authority/support-proposals/W1-CREATIVE-003/thorn_court_behavior_proposal.json": "04f7b9a75be6ac542d3488bd7563a601dcb94603905479b7c3e766c94b9d48c1",
    "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json": "4412b24ad680a30e5548c731f8acba94e8fd858e4bb94f701a16eb17141f5ab7",
    "engineering/authority/support-proposals/ashen/W1-003-KILN-SKY.json": "1b2d5f77185a1461040d7559d0d8ecdaf803d7727e419ceac32636865be85d7c",
    "engineering/crystal-marsh-intake/authority/CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.json": "922b40aaefff220d4bd9b60fa0596b09a76fb6cf7dd181dac42e1dda856417f3",
    "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_CRYSTAL_MARSH.md": "c127203e9372683421154f3877246fe1972b445c9983d350aceda26c42584441",
    "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md": "4d80925a113bb0cca67e2405047cd228a2df2ccd2c680e1e51ccd04b6f2d63d8",
    "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_SYSTEM.md": "6655eae0a65ed103a212f4b61d0f5c9352ddde871165b7bab9dbe014cfaaa8db",
    "program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md": "5ef85e1e0b29973a617f7dca4a8b119443c01644ba33f0e11166ef8d417d5a6f",
    "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json": "aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5",
    "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md": "3116c217e06afe1fd0cd56ee742c537f948a4c91193ec831fd1b3ec362837bfc",
}

CRYSTAL_ALIAS_TERMS = {
    "Algae Scrap", "Bog Tendril", "Crab Pearl Grain", "Croc Eye Pearl", "Croc Hide",
    "Glass Feather", "Iridescent Dust", "Long Beak Shard", "Marsh Resin Blob",
    "Mire Shell Plate", "Newt Tail Crystal", "Perfect Prism Pearl", "Prism Mucus",
    "Serpent Scale", "Shed Skin Ribbon", "Silt Fang", "Tiny Prism Chip", "Venom Crystal",
}
CRYSTAL_NARRATIVE_TERMS = {"Heron Nest Token", "Drowned Choir Tablet"}
CRYSTAL_REMOVED_TERMS = {"Wight Shroud Cloth"}
CRYSTAL_NEW_ITEM_IDS = {"aionbound:prism_wing", "aionbound:watcher_lens", "aionbound:wight_shroud"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_bindings(*paths: str) -> list[dict[str, str]]:
    return [{"path": path, "sha256": SOURCE_HASHES[path]} for path in paths]


def common(ticket_id: str, sources: list[dict[str, str]]) -> dict:
    return {
        "ticket_id": ticket_id,
        "status": "PROPOSED_NOT_RATIFIED",
        "schema_version": 1,
        "authority_effect": "NONE_UNTIL_RATIFIED_IN_REPLACEMENT_DECISION_LEDGER",
        "source_commit": BASE_COMMIT,
        "source_tree": BASE_TREE,
        "source_bindings": sources,
        "scope_guard": {
            "region": "Crystal Marsh only",
            "creative_source_mutation": False,
            "existing_proposal_mutation": False,
            "decision_ledger_mutation": False,
            "pack_implementation_authorized": False,
            "scope_broadening": False,
            "w1_creative_005_status": "DEFERRED_UNCHANGED",
        },
    }


def build_001() -> dict:
    source = load_json(REPO / "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json")
    proposal = source["proposal"]
    aliases = []
    for row in proposal["aliases"]:
        terms = [term for term in row["terms"] if term in CRYSTAL_ALIAS_TERMS]
        if terms:
            aliases.append({"terms": terms, "canonical_id": row["canonical_id"]})
    payload = common(
        "W1-001-CM",
        source_bindings(
            "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json",
            "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
            "engineering/crystal-marsh-intake/authority/CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.json",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_CRYSTAL_MARSH.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md",
        ),
    )
    payload["proposal"] = {
        "selection_rule": "Exact Crystal Marsh subset of W1-CREATIVE-001 plus explicit no-new-identity resolution of Crystal-only loot prose; no other identity or disposition.",
        "policy": copy.deepcopy(proposal["policy"]),
        "aliases": aliases,
        "narrative_codex_only": [term for term in proposal["narrative_codex_only"] if term in CRYSTAL_NARRATIVE_TERMS],
        "removed_or_context_only": [term for term in proposal["removed_or_context_only"] if term in CRYSTAL_REMOVED_TERMS],
        "new_required_items": [copy.deepcopy(row) for row in proposal["new_required_items"] if row["id"] in CRYSTAL_NEW_ITEM_IDS],
        "crystal_creative_doc_only_resolutions": {
            "existing_ledger_aliases": [
                {"term": "Glass Algae Film", "canonical_id": "aionbound:glass_algae"},
                {"term": "Flood Crystal Shard", "canonical_id": "aionbound:flood_crystal"},
            ],
            "narrative_codex_only": ["Frog Song Stone", "Dragonfly Pin", "Turtle Breath Stone", "Watcher Journal Scrap"],
            "alias_without_new_identity": [
                {
                    "term": "Claw",
                    "canonical_id": "aionbound:wet_chitin",
                    "reason": "bloom_crab creature-part prose used as a sickle blank; warehouse-first policy retains the authored purpose without a tenth inventory identity",
                }
            ],
            "presentation_or_quantity_context_only": [
                "pearl dust", "pearls low", "pearls", "wet tools", "trail maps", "star charts",
                "floating ruin sketches", "marsh_idol component", "crystal_talisman fragment", "surveyor_staff lens",
            ],
        },
        "existing_derived_components_unchanged": True,
        "new_inventory_identities_selected": sorted(CRYSTAL_NEW_ITEM_IDS),
        "additional_inventory_identities_created_by_this_tranche": [],
        "identity_count_after_ratification": {"selected_existing_new_required": 3, "additional": 0},
        "w1_creative_005_effect": "NONE_DEFERRED_NO_SIDEGRADE_OR_UPGRADE_BEHAVIOR_GRANTED",
    }
    payload["approval_required"] = [{
        "decision_id": "W1-001-CM",
        "question": "Ratify only these already-written Crystal Marsh dispositions and the existing prism_wing, watcher_lens, and wight_shroud requirements?",
    }]
    return payload


def build_004() -> dict:
    source = load_json(REPO / "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json")
    proposal = source["proposal"]
    payload = common(
        "W1-004-CM",
        source_bindings(
            "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json",
            "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
            "engineering/crystal-marsh-intake/authority/CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.json",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_SYSTEM.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_CRYSTAL_MARSH.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json",
        ),
    )
    payload["proposal"] = {
        "selection_rule": "Copy the existing W1-CREATIVE-004 numeric envelopes, chest bands, and guards verbatim, then apply only the Crystal Marsh resolution below.",
        "probability_and_quantity_envelopes": copy.deepcopy(proposal["probability_and_quantity_envelopes"]),
        "boss_package": copy.deepcopy(proposal["boss_package"]),
        "structure_chest_bands": copy.deepcopy(proposal["structure_chest_bands"]),
        "arena_reward_guard": copy.deepcopy(proposal["arena_reward_guard"]),
        "tuning_rule": proposal["tuning_rule"],
        "crystal_marsh_resolution": {
            "chapter_critical_seal": "aionbound:marsh_wight_mask",
            "chapter_critical_seal_count": 1,
            "ecology_or_natural_marsh_wight_can_drop_chapter_seal": False,
            "valid_seal_source": "active_pearl_depths_arena_session_plus_apex_entity_tag_plus_valid_death_event",
            "critical_progression_representation": "durable_virtual_seal_credit_not_physical_item_presence",
            "physical_mask_fulfillment": "at_most_once_best_effort_with_recovery_claim",
            "recovery_claim": {
                "interaction_hook": "reuse_one_existing_pearl_depths_arena_claim_interaction_hook_no_new_identifier",
                "new_UI": False,
                "museum_claim": False,
                "available_only_when": "reward_entitlement_true_and_physical_mask_claimed_false",
                "claim_order": [
                    "confirm_seal_credit_true",
                    "confirm_reward_entitlement_true",
                    "confirm_inventory_capacity",
                    "write_physical_mask_claimed_true_once",
                    "attempt_one_physical_mask_delivery",
                ],
                "crash_boundary": "after_claimed_write_before_delivery_may_lose_physical_mask_but_never_progression_credit_or_entitlement_and_does_not_auto_reissue",
            },
            "resolution_precedence": "For Crystal Marsh only, recovery_claim supersedes the inherited generic arena_reward_guard.retry_policy; no claim UI or museum path is authorized.",
            "mastery_only_trophies": {
                "aionbound:moon_pearl_pedestal": {"progression_substitute": False, "may_fill_pilgrim_seal_slot": False},
                "aionbound:crystal_obelisk_fragment": {"progression_substitute": False, "may_fill_pilgrim_seal_slot": False},
                "aionbound:marsh_idol": {"progression_substitute": False, "may_fill_pilgrim_seal_slot": False},
            },
            "repeat_clear": {
                "material_package_and_arena_chest": "allowed",
                "marsh_wight_mask_entitlement": "not_reissued",
                "virtual_seal_credit": "not_reissued",
                "optional_mastery_rewards": "allowed_inside_ratified_loot_envelopes",
            },
        },
    }
    payload["approval_required"] = [{
        "decision_id": "W1-004-CM",
        "question": "Ratify the inherited global loot bands and guards for Crystal Marsh with marsh_wight_mask as the sole critical seal and all other trophies optional only?",
    }]
    return payload


def build_003() -> dict:
    timing_seconds = {
        "global_attack_cooldown": [3.0, 4.75],
        "silt_grasp": {"telegraph": [1.2, 1.6], "active": [0.6, 1.0], "recovery": [0.9, 1.3], "cooldown": [7.0, 10.0]},
        "prism_lance": {"telegraph": [1.4, 1.8], "active": [0.8, 1.2], "recovery": [1.0, 1.4], "cooldown": [8.0, 12.0]},
        "wail": {"telegraph": [1.5, 2.0], "active": [1.0, 1.5], "recovery": [1.2, 1.6], "cooldown": [12.0, 17.0]},
        "reed_serpent_call": {"telegraph": [1.6, 2.1], "active": [0.4, 0.7], "recovery": [1.1, 1.5], "cooldown": [19.0, 25.0], "spawn_count": [1, 2]},
        "pearl_orbit": {"telegraph": [1.8, 2.2], "active": [5.0, 7.0], "recovery": [1.3, 1.8], "cooldown": [15.0, 21.0]},
        "drown_hymn": {"telegraph": [2.0, 2.5], "active": [1.0, 1.5], "recovery": [1.5, 2.0], "cooldown": "once_per_phase_transition_plus_flood_claim_rotation"},
    }
    payload = common(
        "W1-003-PEARL-DEPTHS",
        source_bindings(
            "engineering/authority/support-proposals/W1-CREATIVE-003/thorn_court_behavior_proposal.json",
            "engineering/authority/support-proposals/ashen/W1-003-KILN-SKY.json",
            "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
            "engineering/crystal-marsh-intake/authority/CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.json",
            "program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json",
            "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md",
        ),
    )
    payload["proposal"] = {
        "encounter_id": "aionbound:pearl_depths",
        "boss_entity_id": "aionbound:marsh_wight",
        "arena_link": "aionbound:sunken_shrine_or_deep_pool_entrance_authored_encounter_volume",
        "arena_form_predicate": "encounter_session_active_and_entity_tag_aionbound.pearl_depths_apex",
        "ecology_or_natural_form_can_complete_chapter": False,
        "all_numeric_values_status": "PROPOSED_NOT_RATIFIED",
        "new_numbers_proposed_not_ratified": {
            "solo_health": 520,
            "additional_participant_multiplier": 0.30,
            "participant_cap": 4,
            "phase_exit_health_fractions": [0.70, 0.40, 0.15, 0.0],
            "global_attack_cooldown_seconds": [3.0, 4.75],
            "hard_enrage_seconds": 420,
            "outside_leash_grace_seconds": 10,
            "dead_or_outside_grace_seconds": 15,
            "no_eligible_player_grace_seconds": 30,
            "pull_residency_seconds": 5,
            "late_join_residency_seconds": 15,
            "disconnect_grace_seconds": 60,
            "global_session_add_cap": 4,
            "attack_timing_seconds": copy.deepcopy(timing_seconds),
        },
        "health": {
            "solo": 520,
            "per_additional_locked_participant_multiplier": 0.30,
            "participant_cap": 4,
            "scaling_participant_snapshot": "immutable_unique_eligible_pull_participants_selected_at_pull",
            "max_health_formula": "520 * (1 + 0.30 * (N_pull - 1))",
            "late_join_changes_max_health": False,
            "departure_or_disconnect_changes_max_health": False,
        },
        "phases": [
            {"id": "fog_rise", "enter_at_health_fraction": 1.0, "exit_at_health_fraction": 0.70, "health_interval": "0.70 < h <= 1.00", "attacks": ["silt_grasp", "prism_lance"], "add_cap": 0},
            {"id": "choir_below", "enter_at_health_fraction": 0.70, "exit_at_health_fraction": 0.40, "health_interval": "0.40 < h <= 0.70", "attacks": ["silt_grasp", "prism_lance", "wail", "reed_serpent_call"], "add_cap": 3},
            {"id": "mask_unsealed", "enter_at_health_fraction": 0.40, "exit_at_health_fraction": 0.15, "health_interval": "0.15 < h <= 0.40", "attacks": ["prism_lance", "wail", "pearl_orbit", "drown_hymn"], "add_cap": 4},
            {"id": "flood_claim", "enter_at_health_fraction": 0.15, "exit_at_health_fraction": 0.0, "health_interval": "0.00 < h <= 0.15", "attacks": ["silt_grasp", "prism_lance", "pearl_orbit", "drown_hymn"], "add_cap": 2},
        ],
        "phase_boundary_rule": "At exact 0.70, 0.40, or 0.15 enter the lower-health phase; h=0 is terminal death, not a live phase.",
        "timing_seconds": timing_seconds,
        "cooldown_composition": {
            "attack_serialization": "one_attack_telegraph_active_recovery_sequence_at_a_time",
            "clock_start": "global_and_selected_attack_cooldowns_start_when_selected_attack_recovery_finishes",
            "next_attack_gate": "selected_attack_starts_only_when_global_and_attack_specific_cooldowns_have_expired",
        },
        "add_semantics": {
            "allowed_authored_adds": ["aionbound:bog_watcher", "aionbound:reed_serpent"],
            "effective_cap": "min(current_phase.add_cap,multiplayer.global_session_add_cap)",
            "overflow_queue": "FORBIDDEN",
            "phase_down": "despawn_oldest_excess_session_adds_without_loot_kill_credit_or_reward_event",
            "ecology_entities_never_join_session": True,
        },
        "arena_state": {
            "water_rise_and_shrinking_islands": "session_transient_authored_arena_state_only",
            "persistent_world_block_mutation": False,
            "reset_restores_authored_arena_state": True,
            "no_new_radius": True,
        },
        "enrage": {"health_fraction": 0.15, "hard_time_seconds": 420, "hard_time_action": "enter_flood_claim_not_instant_kill"},
        "reset": {
            "leash_boundary": "authored_pearl_depths_encounter_volume_no_new_radius_number",
            "outside_leash_grace_seconds": 10,
            "all_players_dead_or_outside_grace_seconds": 15,
            "no_eligible_player_grace_seconds": 30,
            "world_reload_behavior": "reset_to_unpulled_full_health_restore_authored_arena_and_clear_session_transients",
            "on_reset": ["despawn_session_adds", "clear_session_hazards_and_orbs", "restore_authored_arena_state", "restore_boss_health", "clear_active_session"],
            "completion_is_not_cleared": True,
            "precedence": [
                "valid_arena_form_death_wins_and_cancels_reset",
                "world_unload_or_reload_resets_without_completion_or_reward",
                "outside_authored_volume_continuously_10_seconds_resets",
                "connected_participants_all_dead_or_outside_continuously_15_seconds_resets",
                "no_connected_alive_participant_inside_continuously_30_seconds_resets",
            ],
        },
        "multiplayer": {
            "health_scaling_snapshot": "immutable_at_pull",
            "reward_participant_set": "separate_set_initialized_from_pull_snapshot_then_automatic_early_phase_late_join_may_fill_open_slots",
            "hard_unique_player_cap_for_each_set": 4,
            "eligible_at_pull": "inside_authored_encounter_volume_continuously_for_5_seconds",
            "late_join": "automatic_after_15_continuous_seconds_only_in_fog_rise_or_choir_below_if_reward_set_has_open_slot; never rescales health",
            "disconnect_grace_seconds": 60,
            "targeting": "never_requires_damage_to_one_specific_player",
            "global_session_add_cap": 4,
            "ownership": "per_player_terminal_entitlement_for_terminally_eligible_reward_participant_set",
        },
        "persistence": {
            "schema": "existing_G8_schema_only_no_new_domain",
            "active_fight": "not_persisted",
            "world_completion_key": "aionbound.encounter.pearl_depths.completed.v1",
            "player_seal_credit_key": "aionbound.player.pearl_depths.seal_credit.v1",
            "reward_entitlement_key": "aionbound.player.pearl_depths.reward_entitled.v1",
            "physical_mask_claimed_key": "aionbound.player.pearl_depths.mask_claimed.v1",
            "migration": "idempotent_false_default",
        },
        "terminal_semantics": {
            "complete_on": "arena_form_valid_death_event_with_active_session",
            "eligible_set_source": "reward_participant_set_only",
            "world_stamp": "durable_once",
            "progression_credit": "per_player_durable_once",
            "reward_identity_source": "W1-004-CM_only",
            "ordered_idempotent_transition": [
                "validate_session_and_apex_tag_and_death_event",
                "write_world_completion_once",
                "write_player_seal_credit_once",
                "write_player_reward_entitlement_once",
                "fulfill_physical_mask_at_most_once_or_leave_recovery_entitlement",
            ],
            "repeat_clear": "materials_and_arena_chest_may_repeat_but_chapter_seal_credit_and_entitlement_do_not",
        },
        "ecology_separation": {
            "arena_apex_tag": "aionbound.pearl_depths_apex",
            "tag_writer": "active_pearl_depths_session_spawn_path_only",
            "natural_marsh_wight_must_not": [
                "receive_arena_apex_tag", "join_or_create_session", "complete_chapter",
                "write_completion_or_reward_keys", "drop_or_deliver_marsh_wight_mask",
            ],
        },
        "explicit_nondecisions": {
            "damage_values": "NOT_CREATED",
            "attack_effect_radii": "NOT_CREATED",
            "arena_radius_blocks": "NOT_CREATED_USE_AUTHORED_STRUCTURE_VOLUME",
            "new_attacks": "FORBIDDEN_ONLY_SIX_CREATIVE_ATTACK_IDENTITIES",
            "new_phases": "FORBIDDEN_ONLY_FOUR_CREATIVE_PHASE_IDENTITIES",
            "new_persistence_domain_or_schema": "FORBIDDEN",
        },
    }
    payload["approval_required"] = [{
        "decision_id": "W1-003-PEARL-DEPTHS",
        "question": "Ratify this Crystal-specific Pearl Depths phase, timing, reset, multiplayer, persistence, and terminal envelope without approving damage or radius values?",
    }]
    return payload


def markdown(payload: dict) -> str:
    ticket = payload["ticket_id"]
    proposal = payload["proposal"]
    lines = [
        f"# {ticket} — Crystal Marsh support proposal",
        "",
        "**Status:** `PROPOSED_NOT_RATIFIED`",
        "**Authority effect:** none until an explicit replacement decision ledger ratifies this ticket.",
        "",
        "This proposal is Crystal-Marsh-only. It edits no Creative source, prior proposal, decision ledger, BP, RP, or runtime. `W1-CREATIVE-005` remains deferred unchanged.",
        "",
    ]
    if ticket == "W1-001-CM":
        lines += [
            "## Exact identity disposition",
            "",
            f"- Existing global alias terms selected: {sum(len(row['terms']) for row in proposal['aliases'])}.",
            "- Existing global narrative/Codex terms selected: `Heron Nest Token`, `Drowned Choir Tablet`.",
            "- Existing global removed term selected: `Wight Shroud Cloth`.",
            "- Existing required identities selected: `aionbound:prism_wing`, `aionbound:watcher_lens`, `aionbound:wight_shroud`.",
            "- Crystal-doc-only prose resolves without any additional inventory identity: two already-ledgered aliases, four explicit curiosity states, one `Claw` alias to `wet_chitin`, and presentation/quantity phrases.",
            "- Additional inventory identities created: zero.",
        ]
    elif ticket == "W1-004-CM":
        lines += [
            "## Exact loot and reward resolution",
            "",
            "The global C/U/R/E/T/Q intervals, boss package, four structure-chest bands, arena guards, and tuning rule are copied without numeric alteration.",
            "",
            "`aionbound:marsh_wight_mask` is the sole chapter-critical seal. Ecology/natural Marsh Wights cannot drop it or write Pearl Depths state. Physical fulfillment is at-most-once with durable progression credit and recovery entitlement. `moon_pearl_pedestal`, `crystal_obelisk_fragment`, and `marsh_idol` are optional mastery rewards and cannot fill the pilgrim seal slot.",
        ]
    else:
        lines += [
            "## Minimal Pearl Depths envelope",
            "",
            "The four phase and six attack identities come directly from the frozen Creative boss design. The proposal adds only an executable, Crystal-specific envelope for thresholds, timing, bounded adds, reset, multiplayer ownership, existing-schema persistence, and terminal ordering.",
            "",
            "Every number in `new_numbers_proposed_not_ratified` and every literal under `timing_seconds` is proposed and has no authority until ratified. Damage, attack radii, and an arena-radius number are deliberately absent. Water rise, islands, hazards, and orbs are session-transient authored-arena state and are restored on reset/reload.",
            "",
            "Natural Marsh Wights are prohibited from all Pearl Depths completion, seal, entitlement, and mask-delivery paths.",
        ]
    lines += ["", "## Source binding", "", f"Base commit `{payload['source_commit']}`; base tree `{payload['source_tree']}`.", ""]
    lines.extend(f"- `{row['sha256']}` — `{row['path']}`" for row in payload["source_bindings"])
    lines += ["", "The sibling JSON is canonical.", ""]
    return "\n".join(lines)


def write_outputs(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for payload in (build_001(), build_003(), build_004()):
        stem = payload["ticket_id"]
        (out_dir / f"{stem}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out_dir / f"{stem}.md").write_text(markdown(payload), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE)
    args = parser.parse_args()
    write_outputs(args.out.resolve())


if __name__ == "__main__":
    main()
