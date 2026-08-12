#!/usr/bin/env python3
"""Build the authority-neutral Skyreach Creative support tranche."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BASE_COMMIT = "9cfb798b22216cc73d477ee315861ccb2089d232"
BASE_TREE = "d090311ad9a4578c53b613989a9a48a39e51b883"

SOURCE_HASHES = {
    "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json": "b791c4b63d6ef09c2ac437fdc67065735a2363becad92b359cecb0a4e25c5172",
    "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json": "a9bc8133f8a0aacf7db258ffe76fc04dd9fcc6d07713bef630e074bd48588786",
    "engineering/authority/support-proposals/W1-CREATIVE-003/thorn_court_behavior_proposal.json": "04f7b9a75be6ac542d3488bd7563a601dcb94603905479b7c3e766c94b9d48c1",
    "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json": "4412b24ad680a30e5548c731f8acba94e8fd858e4bb94f701a16eb17141f5ab7",
    "engineering/authority/support-proposals/crystal-marsh/W1-003-PEARL-DEPTHS.json": "b445cdc251eea6a79b03816b7ea0cf2bab0c6545a91946874e877f114a3e7098",
    "engineering/skyreach-intake/authority/SKYREACH_VERTICAL_INTAKE_MAP.json": "42d0d94ea55d8dd1306345caf014cac08c770cf88adb241f70e9c5bcee4807b5",
    "program/crazycraft-pack-production-v1/studio-prep/creative/01_progression/PLAYER_JOURNEY.md": "42ba75d9518977c71397826aa9f4daa3864df942019c809b04830fef654a1fa7",
    "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_SKYREACH.md": "586922ff3a4d74285e31fed4f11818e7dc70ba4d35ed97f3143f6c5b869080b4",
    "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md": "4d80925a113bb0cca67e2405047cd228a2df2ccd2c680e1e51ccd04b6f2d63d8",
    "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_SYSTEM.md": "6655eae0a65ed103a212f4b61d0f5c9352ddde871165b7bab9dbe014cfaaa8db",
    "program/crazycraft-pack-production-v1/studio-prep/creative/03_crafting/CRAFTING_TREE.md": "1f3482ba3dd9f916e08aa544153cc841871a729a2e82d9e75601715f4b5ee807",
    "program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md": "5ef85e1e0b29973a617f7dca4a8b119443c01644ba33f0e11166ef8d417d5a6f",
    "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json": "aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5",
    "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md": "3116c217e06afe1fd0cd56ee742c537f948a4c91193ec831fd1b3ec362837bfc",
}

SKY_ALIAS_TERMS = {
    "Cliff Hoof Keratin", "Dense Muscle Strip", "Drake Membrane", "Fox Whisker Cord",
    "Gale Membrane", "Glide Scale", "Hawk Talon", "Navigation Oil", "Nest Crown Plume",
    "Nest Twig", "Ram Horn Spiral", "Roc Primary Feather", "Ropewing Membrane", "Ruin Talon",
    "Soft Sky Fur", "Stone Beak", "Storm Salt", "Vulture Crop Stone",
}
SKY_NARRATIVE_TERMS = {"Sky Ruin Key Fragment", "Sky Ruin Master Key", "Twinbond-scented down"}
SKY_NEW_ITEM_IDS = {"aionbound:wing_bone_stay"}
SIDEGRADES = {"summit_hammer", "skywidow_whip", "gale_prism_bow", "nest_talon_dagger", "stormcloak"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def bindings(*paths: str) -> list[dict[str, str]]:
    return [{"path": path, "sha256": SOURCE_HASHES[path]} for path in paths]


def common(ticket: str, source_bindings: list[dict[str, str]]) -> dict:
    return {
        "ticket_id": ticket,
        "status": "PROPOSED_NOT_RATIFIED",
        "schema_version": 1,
        "authority_effect": "NONE_UNTIL_RATIFIED_IN_REPLACEMENT_DECISION_LEDGER",
        "source_commit": BASE_COMMIT,
        "source_tree": BASE_TREE,
        "source_bindings": source_bindings,
        "scope_guard": {
            "region": "Skyreach only",
            "creative_source_mutation": False,
            "existing_proposal_mutation": False,
            "decision_ledger_mutation": False,
            "pack_implementation_authorized": False,
            "scope_broadening": False,
            "w1_creative_005_status": "DEFERRED_UNCHANGED",
            "w1_creative_005_sidegrades_absent": sorted(SIDEGRADES),
        },
    }


def build_001() -> dict:
    original = load_json(REPO / "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json")["proposal"]
    aliases = []
    for row in original["aliases"]:
        terms = [term for term in row["terms"] if term in SKY_ALIAS_TERMS]
        if terms:
            aliases.append({"terms": terms, "canonical_id": row["canonical_id"]})
    payload = common("W1-001-SR", bindings(
        "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json",
        "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
        "engineering/skyreach-intake/authority/SKYREACH_VERTICAL_INTAKE_MAP.json",
        "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_SKYREACH.md",
        "program/crazycraft-pack-production-v1/studio-prep/creative/03_crafting/CRAFTING_TREE.md",
    ))
    payload["proposal"] = {
        "selection_rule": "Exact Skyreach subset of W1-CREATIVE-001 plus no-new-identity resolution of Skyreach-only prose; no other identity or disposition.",
        "policy": copy.deepcopy(original["policy"]),
        "aliases": aliases,
        "narrative_codex_only": [term for term in original["narrative_codex_only"] if term in SKY_NARRATIVE_TERMS],
        "removed_or_context_only": [],
        "new_required_items": [copy.deepcopy(row) for row in original["new_required_items"] if row["id"] in SKY_NEW_ITEM_IDS],
        "skyreach_creative_doc_only_resolutions": {
            "narrative_codex_only": ["Sky Milk Curd", "Stolen Shiny", "Carrion Charm", "Harpy Song Flute"],
            "presentation_or_quantity_context_only": [
                "sky_feather x2", "sky_feather xn", "wind_silk strand", "Wind Silk Bundle",
                "cliff_crystal chip", "aether_stone chip", "sky_feather bulk", "Roc Primary Feathers",
                "Nest glory display", "aether mark",
            ],
            "existing_identity_relationships_only": [
                "Climbing Rope", "Climbing Hook Head", "Glider Panel", "Glider Frame",
                "Soft Landing Pad", "Lift Tonic precursor", "Aether Bind",
            ],
        },
        "existing_derived_components_unchanged": True,
        "new_inventory_identities_selected": ["aionbound:wing_bone_stay"],
        "additional_inventory_identities_created_by_this_tranche": [],
        "identity_count_after_ratification": {"selected_existing_new_required": 1, "additional": 0},
        "executable_acquisition_and_recipe_scope": "only_selected_and_existing_Skyreach_inventory_ids_and_existing_derived_components",
        "w1_creative_005_effect": "NONE_DEFERRED_NO_SIDEGRADE_OR_UPGRADE_BEHAVIOR_GRANTED",
    }
    payload["approval_required"] = [{"decision_id": "W1-001-SR", "question": "Ratify only these already-written Skyreach dispositions and the existing wing_bone_stay requirement?"}]
    return payload


def build_004() -> dict:
    original = load_json(REPO / "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json")["proposal"]
    payload = common("W1-004-SR", bindings(
        "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json",
        "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
        "engineering/skyreach-intake/authority/SKYREACH_VERTICAL_INTAKE_MAP.json",
        "program/crazycraft-pack-production-v1/studio-prep/creative/01_progression/PLAYER_JOURNEY.md",
        "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_SYSTEM.md",
        "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_SKYREACH.md",
        "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md",
        "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json",
    ))
    payload["proposal"] = {
        "selection_rule": "Copy W1-CREATIVE-004 numeric envelopes, chest bands, and guards verbatim, then apply only the Skyreach resolution below.",
        "probability_and_quantity_envelopes": copy.deepcopy(original["probability_and_quantity_envelopes"]),
        "boss_package": copy.deepcopy(original["boss_package"]),
        "structure_chest_bands": copy.deepcopy(original["structure_chest_bands"]),
        "arena_reward_guard": copy.deepcopy(original["arena_reward_guard"]),
        "tuning_rule": original["tuning_rule"],
        "skyreach_resolution": {
            "chapter_critical_seal": "aionbound:storm_pinion",
            "chapter_critical_seal_count": 1,
            "ecology_or_natural_wind_roc_can_drop_chapter_seal": False,
            "valid_seal_source": "active_storm_nest_arena_session_plus_apex_entity_tag_plus_valid_death_event",
            "critical_progression_representation": "durable_virtual_seal_credit_not_physical_item_presence",
            "physical_pinion_fulfillment": "at_most_once_best_effort_with_recovery_claim",
            "recovery_claim": {
                "interaction_hook": "reuse_one_existing_storm_nest_arena_claim_interaction_hook_no_new_identifier",
                "new_UI": False,
                "museum_claim": False,
                "available_only_when": "reward_entitlement_true_and_physical_pinion_claimed_false",
                "claim_order": ["confirm_seal_credit_true", "confirm_reward_entitlement_true", "confirm_inventory_capacity", "write_physical_pinion_claimed_true_once", "attempt_one_physical_pinion_delivery"],
                "crash_boundary": "after_claimed_write_before_delivery_may_lose_physical_pinion_but_never_progression_credit_or_entitlement_and_does_not_auto_reissue",
            },
            "resolution_precedence": "For Skyreach only, recovery_claim supersedes the inherited generic arena_reward_guard.retry_policy; no claim UI or museum path is authorized.",
            "mastery_only_rewards": {
                "Nest Crown Plume display": {"inventory_identity_created": False, "progression_substitute": False, "may_fill_pilgrim_seal_slot": False},
                "Nest glory display": {"inventory_identity_created": False, "progression_substitute": False, "may_fill_pilgrim_seal_slot": False},
                "aether mark": {"inventory_identity_created": False, "progression_substitute": False, "may_fill_pilgrim_seal_slot": False},
            },
            "repeat_clear": {
                "material_package_and_arena_chest": "allowed",
                "storm_pinion_entitlement": "not_reissued",
                "virtual_seal_credit": "not_reissued",
                "optional_mastery_rewards": "allowed_inside_ratified_loot_envelopes",
            },
        },
    }
    payload["approval_required"] = [{"decision_id": "W1-004-SR", "question": "Ratify the inherited global loot bands and guards for Skyreach with storm_pinion as the sole critical seal and all other rewards optional only?"}]
    return payload


def build_003() -> dict:
    timing = {
        "global_attack_cooldown": [3.0, 4.5],
        "wing_buffet": {"telegraph": [1.1, 1.5], "active": [0.5, 0.9], "recovery": [0.9, 1.3], "cooldown": [7.0, 10.0]},
        "talon_pin": {"telegraph": [1.4, 1.9], "active": [0.7, 1.1], "recovery": [1.2, 1.6], "cooldown": [11.0, 15.0]},
        "gale_dive": {"telegraph": [1.8, 2.4], "active": [0.8, 1.3], "recovery": [1.4, 1.9], "cooldown": [13.0, 18.0]},
        "feather_knives": {"telegraph": [1.3, 1.8], "active": [1.0, 1.5], "recovery": [1.0, 1.4], "cooldown": [9.0, 13.0]},
        "call_of_the_nest": {"telegraph": [1.8, 2.4], "active": [0.5, 0.8], "recovery": [1.3, 1.8], "cooldown": [20.0, 27.0], "spawn_count": [1, 2]},
        "storm_screech": {"telegraph": [1.7, 2.2], "active": [0.8, 1.2], "recovery": [1.3, 1.8], "cooldown": [14.0, 19.0]},
    }
    payload = common("W1-003-STORM-NEST", bindings(
        "engineering/authority/support-proposals/W1-CREATIVE-003/thorn_court_behavior_proposal.json",
        "engineering/authority/support-proposals/crystal-marsh/W1-003-PEARL-DEPTHS.json",
        "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
        "engineering/skyreach-intake/authority/SKYREACH_VERTICAL_INTAKE_MAP.json",
        "program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md",
        "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md",
        "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json",
        "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md",
    ))
    phases = [
        {"id": "nest_guard", "enter_at_health_fraction": 1.0, "exit_at_health_fraction": .70, "health_interval": "0.70 < h <= 1.00", "attacks": ["wing_buffet", "talon_pin"], "add_cap": 0},
        {"id": "wind_roads", "enter_at_health_fraction": .70, "exit_at_health_fraction": .40, "health_interval": "0.40 < h <= 0.70", "attacks": ["wing_buffet", "talon_pin", "gale_dive", "feather_knives"], "add_cap": 0},
        {"id": "harpy_dirge", "enter_at_health_fraction": .40, "exit_at_health_fraction": .15, "health_interval": "0.15 < h <= 0.40", "attacks": ["gale_dive", "feather_knives", "call_of_the_nest", "storm_screech"], "add_cap": 4},
        {"id": "storm_crown", "enter_at_health_fraction": .15, "exit_at_health_fraction": 0.0, "health_interval": "0.00 < h <= 0.15", "attacks": ["wing_buffet", "gale_dive", "feather_knives", "storm_screech"], "add_cap": 2},
    ]
    payload["proposal"] = {
        "encounter_id": "aionbound:storm_nest",
        "boss_entity_id": "aionbound:wind_roc",
        "arena_link": "aionbound:nest_platform_authored_encounter_volume",
        "arena_form_predicate": "encounter_session_active_and_entity_tag_aionbound.storm_nest_apex",
        "ecology_or_natural_form_can_complete_chapter": False,
        "all_numeric_values_status": "PROPOSED_NOT_RATIFIED",
        "new_numbers_proposed_not_ratified": {
            "solo_health": 560, "additional_participant_multiplier": .30, "participant_cap": 4,
            "phase_exit_health_fractions": [.70, .40, .15, 0.0], "global_attack_cooldown_seconds": [3.0, 4.5],
            "hard_enrage_seconds": 420, "outside_leash_grace_seconds": 10, "dead_or_outside_grace_seconds": 15,
            "no_eligible_player_grace_seconds": 30, "pull_residency_seconds": 5, "late_join_residency_seconds": 15,
            "disconnect_grace_seconds": 60, "global_session_add_cap": 4, "attack_timing_seconds": copy.deepcopy(timing),
        },
        "health": {"solo": 560, "per_additional_locked_participant_multiplier": .30, "participant_cap": 4, "scaling_participant_snapshot": "immutable_unique_eligible_pull_participants_selected_at_pull", "max_health_formula": "560 * (1 + 0.30 * (N_pull - 1))", "late_join_changes_max_health": False, "departure_or_disconnect_changes_max_health": False},
        "phases": phases,
        "phase_boundary_rule": "At exact 0.70, 0.40, or 0.15 enter the lower-health phase; h=0 is terminal death, not a live phase.",
        "timing_seconds": timing,
        "cooldown_composition": {"attack_serialization": "one_attack_telegraph_active_recovery_sequence_at_a_time", "clock_start": "global_and_selected_attack_cooldowns_start_when_selected_attack_recovery_finishes", "next_attack_gate": "selected_attack_starts_only_when_global_and_attack_specific_cooldowns_have_expired"},
        "add_semantics": {"allowed_authored_adds": ["aionbound:ruin_harpy", "aionbound:gale_hawk"], "effective_cap": "min(current_phase.add_cap,multiplayer.global_session_add_cap)", "overflow_queue": "FORBIDDEN", "phase_down": "despawn_oldest_excess_session_adds_without_loot_kill_credit_or_reward_event", "ecology_entities_never_join_session": True},
        "arena_state": {"updraft_pillars_and_recovery_ledges": "session_transient_authored_arena_state_only", "persistent_world_block_mutation": False, "reset_restores_authored_arena_state": True, "no_new_radius": True},
        "enrage": {"health_fraction": .15, "hard_time_seconds": 420, "hard_time_action": "enter_storm_crown_not_instant_kill"},
        "reset": {"leash_boundary": "authored_storm_nest_encounter_volume_no_new_radius_number", "outside_leash_grace_seconds": 10, "all_players_dead_or_outside_grace_seconds": 15, "no_eligible_player_grace_seconds": 30, "world_reload_behavior": "reset_to_unpulled_full_health_restore_authored_arena_and_clear_session_transients", "on_reset": ["despawn_session_adds", "clear_session_hazards_and_updrafts", "restore_authored_arena_state", "restore_boss_health", "clear_active_session"], "completion_is_not_cleared": True, "precedence": ["valid_arena_form_death_wins_and_cancels_reset", "world_unload_or_reload_resets_without_completion_or_reward", "outside_authored_volume_continuously_10_seconds_resets", "connected_participants_all_dead_or_outside_continuously_15_seconds_resets", "no_connected_alive_participant_inside_continuously_30_seconds_resets"]},
        "multiplayer": {"health_scaling_snapshot": "immutable_at_pull", "reward_participant_set": "separate_set_initialized_from_pull_snapshot_then_automatic_early_phase_late_join_may_fill_open_slots", "hard_unique_player_cap_for_each_set": 4, "eligible_at_pull": "inside_authored_encounter_volume_continuously_for_5_seconds", "late_join": "automatic_after_15_continuous_seconds_only_in_nest_guard_or_wind_roads_if_reward_set_has_open_slot; never rescales health", "disconnect_grace_seconds": 60, "targeting": "never_requires_damage_to_one_specific_player", "global_session_add_cap": 4, "ownership": "per_player_terminal_entitlement_for_terminally_eligible_reward_participant_set"},
        "persistence": {"schema": "existing_G8_schema_only_no_new_domain", "active_fight": "not_persisted", "world_completion_key": "aionbound.encounter.storm_nest.completed.v1", "player_seal_credit_key": "aionbound.player.storm_nest.seal_credit.v1", "reward_entitlement_key": "aionbound.player.storm_nest.reward_entitled.v1", "physical_pinion_claimed_key": "aionbound.player.storm_nest.pinion_claimed.v1", "migration": "idempotent_false_default"},
        "terminal_semantics": {"complete_on": "arena_form_valid_death_event_with_active_session", "eligible_set_source": "reward_participant_set_only", "world_stamp": "durable_once", "progression_credit": "per_player_durable_once", "reward_identity_source": "W1-004-SR_only", "ordered_idempotent_transition": ["validate_session_and_apex_tag_and_death_event", "write_world_completion_once", "write_player_seal_credit_once", "write_player_reward_entitlement_once", "fulfill_physical_pinion_at_most_once_or_leave_recovery_entitlement"], "repeat_clear": "materials_and_arena_chest_may_repeat_but_chapter_seal_credit_and_entitlement_do_not"},
        "ecology_separation": {"arena_apex_tag": "aionbound.storm_nest_apex", "tag_writer": "active_storm_nest_session_spawn_path_only", "natural_or_command_wind_roc_must_not": ["receive_arena_apex_tag", "join_or_create_session", "complete_chapter", "write_completion_or_reward_keys", "drop_or_deliver_storm_pinion"]},
        "explicit_nondecisions": {"damage_values": "NOT_CREATED", "attack_effect_radii": "NOT_CREATED", "arena_radius_blocks": "NOT_CREATED_USE_AUTHORED_STRUCTURE_VOLUME", "new_attacks": "FORBIDDEN_ONLY_SIX_CREATIVE_ATTACK_IDENTITIES", "new_phases": "FORBIDDEN_ONLY_FOUR_CREATIVE_PHASE_IDENTITIES", "new_persistence_domain_or_schema": "FORBIDDEN"},
    }
    payload["approval_required"] = [{"decision_id": "W1-003-STORM-NEST", "question": "Ratify this Skyreach-specific Storm Nest phase, timing, reset, multiplayer, persistence, and terminal envelope without approving damage or radius values?"}]
    return payload


def markdown(payload: dict) -> str:
    ticket = payload["ticket_id"]
    lines = [f"# {ticket} — Skyreach support proposal", "", "**Status:** `PROPOSED_NOT_RATIFIED`", "**Authority effect:** none until an explicit replacement decision ledger ratifies this ticket.", "", "This proposal is Skyreach-only. It edits no Creative source, prior proposal, decision ledger, BP, RP, catalog, or runtime. `W1-CREATIVE-005` remains deferred unchanged.", ""]
    if ticket == "W1-001-SR":
        lines += ["## Exact identity disposition", "", "- Existing global alias terms selected: 18.", "- Existing global narrative/Codex terms selected: `Sky Ruin Key Fragment`, `Sky Ruin Master Key`, `Twinbond-scented down`.", "- Existing required identity selected: `aionbound:wing_bone_stay`.", "- Four Skyreach-only curiosities become Codex narrative state; quantity, presentation, and derived-craft phrases create no item identity.", "- Additional inventory identities created: zero.", "- All five `W1-CREATIVE-005` sidegrades remain absent."]
    elif ticket == "W1-004-SR":
        lines += ["## Exact loot and reward resolution", "", "The global C/U/R/E/T/Q intervals, boss package, structure-chest bands, arena guards, and tuning rule are copied without numeric alteration.", "", "`aionbound:storm_pinion` is the sole chapter-critical seal. Natural or command-spawned Wind Rocs cannot grant it or write Storm Nest state. Physical fulfillment is at-most-once with durable progression credit and recovery entitlement. Named mastery/display rewards are optional, create no new identity, and cannot fill the pilgrim seal slot."]
    else:
        lines += ["## Minimal Storm Nest envelope", "", "The four phase and six attack identities come directly from the frozen Creative boss design. This proposal adds only a Skyreach-specific envelope for thresholds, timing, bounded adds, authored-arena reset, multiplayer ownership, existing-schema persistence, and terminal ordering.", "", "Every number is proposed and carries no authority until ratified. Damage, attack-effect radii, and an arena-radius number are deliberately absent. Updrafts and recovery ledges remain session-transient authored-arena state.", "", "Natural or command-spawned Wind Rocs are prohibited from all Storm Nest completion, seal, entitlement, and pinion-delivery paths."]
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
