#!/usr/bin/env python3
"""Build the authority-neutral Wave 1 finale/Twinbond support proposals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent

BASE_COMMIT = "1b8d35fe47906f376196ad5f049d1595e3366f27"
BASE_TREE = "83d67bd95cb5c0f067be7876967c32ca881dcdd0"

SOURCE_HASHES = {
    "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json": "b791c4b63d6ef09c2ac437fdc67065735a2363becad92b359cecb0a4e25c5172",
    "engineering/authority/twinbond/TWINBOND_EXISTING_AUTHORITY_AUDIT.json": "5af5125dea93bf488dcdcd1ce5939117329cfa803854fc8f3396638782416ebf",
    "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json": "a9bc8133f8a0aacf7db258ffe76fc04dd9fcc6d07713bef630e074bd48588786",
    "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json": "4412b24ad680a30e5548c731f8acba94e8fd858e4bb94f701a16eb17141f5ab7",
    "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json": "aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5",
    "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md": "3116c217e06afe1fd0cd56ee742c537f948a4c91193ec831fd1b3ec362837bfc",
    "program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md": "5ef85e1e0b29973a617f7dca4a8b119443c01644ba33f0e11166ef8d417d5a6f",
    "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md": "4d80925a113bb0cca67e2405047cd228a2df2ccd2c680e1e51ccd04b6f2d63d8",
    "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_SYSTEM.md": "6655eae0a65ed103a212f4b61d0f5c9352ddde871165b7bab9dbe014cfaaa8db",
    "program/crazycraft-pack-production-v1/studio-prep/creative/03_crafting/CRAFTING_TREE.md": "1f3482ba3dd9f916e08aa544153cc841871a729a2e82d9e75601715f4b5ee807",
    "program/crazycraft-pack-production-v1/studio-prep/creative/01_progression/PLAYER_JOURNEY.md": "42ba75d9518977c71397826aa9f4daa3864df942019c809b04830fef654a1fa7",
}

FORBIDDEN_INHERITANCE = [
    "aionbound:trophy_concord_scale",
    "aionbound:finale_ignition_key",
    "concord_sigil",
    "concord_dueling_ring",
    "ash_crownblade",
    "empress_tide_lance",
]


def bindings(*paths: str) -> list[dict[str, str]]:
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
            "region": "Wave 1 finale/Twinbond only",
            "creative_source_mutation": False,
            "decision_ledger_mutation": False,
            "pack_or_runtime_mutation_authorized": False,
            "scope_broadening": False,
            "w1_creative_005_status": "DEFERRED_UNCHANGED",
            "native_asset_work_authorized": False,
            "candidate_or_runtime_proof_claimed": False,
        },
    }


def build_002() -> dict:
    payload = common(
        "W1-002-TWINBOND",
        bindings(
            "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
            "engineering/authority/twinbond/TWINBOND_EXISTING_AUTHORITY_AUDIT.json",
            "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json",
            "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json",
            "program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/03_crafting/CRAFTING_TREE.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/01_progression/PLAYER_JOURNEY.md",
        ),
    )
    payload["proposal"] = {
        "selection_rule": "Close only the narrowed W1-CREATIVE-002 container, presentation, identity-disposition, and machine-exit questions using already-audited inputs.",
        "finale_container": {
            "choice": "SAME_WORLD_SINGLE_AUTHORED_FINALE_SITE",
            "dimension": "minecraft:overworld",
            "site_count": "one_durable_site_per_world",
            "placement": "existing_G8_structure_locality_and_persistence_paths_only; not ordinary random feature-rule density",
            "entry": "existing_twinbond_approach_marker_handoff_after_four_seals_edge_blank_inert_edge_and_pilgrimage",
            "new_dimension_or_portal_system": False,
            "old_isolated_logical_twinbond_container_adopted": False,
        },
        "prepared_site_binding": {
            "massing": "twinbond_slice_v1",
            "declared_size": [128, 48, 128],
            "assets": ["twin_thrones", "twinbond_obelisk_site", "ceremony_anvil_site", "twinbond_obsidian_ring", "twinbond_approach_marker"],
            "anchors": {
                "arrival": [64, 12, 22],
                "gate": [64, 12, 30],
                "ember_throne": [36, 12, 64],
                "tide_throne": [92, 12, 64],
                "center_relic_trial": [64, 12, 64],
                "completion": [64, 12, 94],
            },
            "aspect_entities": ["aionbound:ash_sovereign_wyrm", "aionbound:tide_empress_wyrm"],
        },
        "secondary_reward_presentation": {
            "concord_spark": {
                "disposition": "ABSTRACT_ENCOUNTER_TRANSITION_STATE",
                "inventory_item": False,
                "meaning": "the durable transition from completed Relic Trial to Trophy Edge ignition",
            },
            "memory_of_four_lands": {
                "canonical_id": "aionbound:memory_of_four_lands",
                "presentation": "single_inventory_backed_vanity_and_Codex_completion_item",
                "placeable_block_or_entity": False,
                "set_model": "four durable chapter-curiosity credits compose one combined item entitlement; no four new item identities",
                "shipping_icon": "one flat item icon at textures/items/memory_of_four_lands.png using the already-approved four-region memory motif",
                "art_gate": "icon must pass ordinary Asset provenance/PNG/pack-path qualification before candidate; this is not a new Creative identity decision",
                "progression_required": False,
            },
            "mastery_sigil": {
                "disposition": "NON_INVENTORY_DURABLE_CODEX_MASTERY_STAMP",
                "new_item_or_icon": False,
                "packet006_trophy_substitution": False,
                "progression_required": False,
                "meaning": "optional post-clear mastery acknowledgement only",
            },
        },
        "machine_exit_dependency": {
            "twinbond_durable_completion_required": True,
            "trophy_edge_ignition_required": True,
            "unresolved_reward_recovery_at_final_freeze_allowed": False,
            "post_clear_mastery_or_mastery_stamp_required": False,
            "memory_of_four_lands_required": False,
            "meaning": "Twinbond is mandatory for the Wave 1 machine-exit token; vanity and mastery remain optional.",
        },
        "native_dependencies_not_waived": [
            "both wyrm editable assets require native Blockbench round-trip and encounter-animation assessment",
            "twinbond_relic requires native repair/qualification for its bound dual_pulse presentation",
            "Memory of Four Lands icon requires ordinary Asset qualification",
        ],
        "forbidden_inheritance": FORBIDDEN_INHERITANCE,
        "explicit_nondecisions": {
            "boss_numbers_and_runtime_semantics": "W1-003-TWINBOND",
            "reward_probability_duplicate_and_recovery_semantics": "W1-004-TWINBOND",
            "sidegrade_or_upgrade_behavior": "W1-CREATIVE-005_REMAINS_DEFERRED",
            "new_mechanics_or_reward_identities": "NOT_CREATED",
        },
    }
    payload["approval_required"] = [{
        "decision_id": "W1-002-TWINBOND",
        "question": "Ratify the same-world single authored Twinbond site, abstract Concord Spark, combined Memory presentation, non-inventory optional mastery stamp, and mandatory Twinbond/Trophy Edge machine-exit dependency exactly as proposed?",
    }]
    return payload


def build_003() -> dict:
    timing = {
        "global_action_cooldown": [3.0, 4.5],
        "split_single_aspect_window": {"telegraph": [1.2, 1.8], "active": [0.6, 1.2], "recovery": [1.0, 1.5], "cooldown": [6.0, 9.0]},
        "concord_paired_window": {"telegraph": [1.6, 2.2], "active": [0.8, 1.6], "recovery": [1.2, 1.8], "cooldown": [9.0, 13.0]},
        "relic_trial_channel_required": 12.0,
        "relic_trial_absence_reset": 2.0,
        "finale_ignition": 5.0,
    }
    payload = common(
        "W1-003-TWINBOND",
        bindings(
            "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
            "engineering/authority/twinbond/TWINBOND_EXISTING_AUTHORITY_AUDIT.json",
            "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/01_progression/PLAYER_JOURNEY.md",
        ),
    )
    payload["proposal"] = {
        "encounter_id": "aionbound:twinbond",
        "aspect_entities": ["aionbound:ash_sovereign_wyrm", "aionbound:tide_empress_wyrm"],
        "arena": "authored_twinbond_slice_v1_structure_volume_and_exact_prepared_anchors",
        "all_numeric_values_status": "PROPOSED_NOT_RATIFIED",
        "balance_preservation": {
            "entity_component_health_each": 160,
            "entity_component_attack_damage_each": 8,
            "multiplayer_health_scaling": False,
            "damage_effect_radius_or_knockback_changes": "NOT_AUTHORIZED",
            "reason": "preserve the current G8 entity-component balance values; propose only orchestration thresholds and timing",
        },
        "phase_thresholds": {
            "split_approach_exit": "both aspects at or below 0.70 health fraction",
            "concord_pressure_exit": "both aspects at or below 0.40 health fraction",
            "threshold_hold": "an aspect reaching the current phase floor cannot lose further health until the other aspect reaches the same floor",
            "relic_trial": "at the paired 0.40 threshold both aspects become non-terminal and damage-immune until the trial resolves or resets",
            "individual_aspect_death_before_terminal": "FORBIDDEN",
        },
        "phases": [
            {"id": "split_approach", "health_gate": "start_until_both_aspects_le_0.70", "execution": "serialize one existing authored aspect action window at a time; alternate eligible aspect when both can act", "new_attack_identity": False},
            {"id": "concord_pressure", "health_gate": "both_le_0.70_until_both_le_0.40", "execution": "one telegraphed paired action window followed by full recovery; uses only each aspect's existing approved action repertoire", "new_attack_identity": False},
            {"id": "relic_trial", "health_gate": "both_held_at_0.40", "execution": "at least one eligible participant remains in the authored center relic-focus volume for 12 continuous seconds while the two aspects continue serialized pressure", "damage_resets_channel": False},
            {"id": "finale_ignition", "health_gate": "relic_trial_complete", "execution": "freeze combat, run one 5-second terminal ignition window, then commit the ordered terminal transition", "combat_damage": False},
        ],
        "timing_seconds": timing,
        "action_composition": {
            "serialization": "one telegraph-active-recovery sequence globally at a time; no overlapping double-dispatch",
            "clock_start": "global and selected window cooldowns start after recovery",
            "new_attack_names_or_effects": "FORBIDDEN",
            "phase_specific_animation_requirement": "implementation may ship only after native assessment proves existing clips sufficient or a separately qualified repair supplies the bound phase presentation",
        },
        "reset": {
            "leash_boundary": "authored structure volume only; no invented radius",
            "one_aspect_outside_grace_seconds": 10,
            "all_eligible_dead_or_outside_grace_seconds": 15,
            "no_eligible_participant_grace_seconds": 30,
            "relic_channel_no_presence_reset_seconds": 2,
            "action": "remove session aspects and transient relic-trial state; restore authored arena state; retain no reward or completion write",
            "restart_or_reconcile": "an active non-terminal fight reopens as unpulled after cleanup; durable completed/reward recovery state remains authoritative",
            "persistent_world_block_mutation": False,
        },
        "multiplayer": {
            "pull_eligibility": "unique players inside authored encounter volume continuously for 5 seconds at admission",
            "participant_cap": 4,
            "health_scaling_snapshot": "none_health_values_preserved",
            "late_join": "after 15 continuous seconds only during split_approach or concord_pressure while reward set has an open slot",
            "late_join_after_relic_trial_begins": False,
            "disconnect_grace_seconds": 60,
            "ownership": "per-player terminal entitlement for the immutable pull set plus admitted early-phase late joiners",
            "world_completion": "one durable world encounter completion shared by the valid terminal event",
            "targeting": "must not require one specific owner's damage or presence after admission",
        },
        "persistence": {
            "schema": "existing_G8_schema_only_no_new_domain",
            "active_fight": "not_persisted",
            "durable_world_key": "aionbound.encounter.twinbond.completed.v1",
            "durable_player_keys": [
                "aionbound.player.twinbond.completed.v1",
                "aionbound.player.twinbond.reward_entitled.v1",
                "aionbound.player.twinbond.relic_claimed.v1",
                "aionbound.player.twinbond.edge_ignited.v1",
                "aionbound.player.twinbond.memory_claimed.v1",
                "aionbound.player.twinbond.mastery_stamp.v1",
            ],
            "writes": "idempotent booleans or existing-schema cache fields only",
        },
        "terminal_semantics": {
            "sole_valid_terminal": "active admitted session reaches relic_trial completion and then completes the 5-second finale_ignition window",
            "individual_aspect_death_or_command_kill_completes": False,
            "ordered_transition": [
                "write synchronous terminal lock for encounter session",
                "write durable world Twinbond completion once",
                "write per-player completion and reward entitlement once for each eligible terminal participant",
                "write Concord Spark abstract transition and Trophy Edge ignition state once",
                "run W1-004-TWINBOND bounded fulfillment or retain recovery entitlement",
                "remove encounter entities and transient state without death-loot dispatch",
            ],
            "repeat_or_recovery_entry": "a completed encounter never falls through to a new pull while any eligible player has unfulfilled terminal entitlement",
        },
        "forbidden_inheritance": FORBIDDEN_INHERITANCE,
        "explicit_nondecisions": {
            "new_attack_identity_damage_radius_or_effect": "NOT_CREATED",
            "new_persistence_domain_or_schema": "FORBIDDEN",
            "new_global_subscription_or_scheduler": "FORBIDDEN",
            "native_asset_pass": "NOT_CLAIMED",
        },
    }
    payload["approval_required"] = [{
        "decision_id": "W1-003-TWINBOND",
        "question": "Ratify these four Creative phases with preserved entity balance, bounded timing, reset, multiplayer ownership, existing-schema persistence, and ignition-terminal semantics exactly as proposed?",
    }]
    return payload


def build_004() -> dict:
    payload = common(
        "W1-004-TWINBOND",
        bindings(
            "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
            "engineering/authority/twinbond/TWINBOND_EXISTING_AUTHORITY_AUDIT.json",
            "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_SYSTEM.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/03_crafting/CRAFTING_TREE.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/01_progression/PLAYER_JOURNEY.md",
        ),
    )
    payload["proposal"] = {
        "selection_rule": "Bind only already-approved finale identities to guaranteed first-clear entitlements and idempotent recovery; create no new loot identity or grind loop.",
        "valid_source": "W1-003-TWINBOND_valid_finale_ignition_terminal_only",
        "first_eligible_clear_package": {
            "twinbond_relic": {"id": "aionbound:twinbond_relic", "chance": 1.0, "quantity": 1, "ownership": "once_per_eligible_player"},
            "concord_spark": {"inventory_quantity": 0, "result": "durable_abstract_transition_state_once_per_eligible_player"},
            "trophy_edge_ignition": {"chance": 1.0, "result": "durable_per_player_ignition_credit_and_full_Trophy_Edge_fulfillment_or_recovery"},
            "memory_completion": {"chance_per_missing_chapter_curiosity_credit": 1.0, "quantity_per_missing_chapter": 1, "maximum_missing_credits": 4, "combined_item": "aionbound:memory_of_four_lands_once_when_all_four_credits_are_present"},
            "mastery_stamp": {"chance": 1.0, "inventory_quantity": 0, "result": "optional_durable_Codex_mastery_stamp", "progression_required": False},
            "random_material_or_catalyst_package": "NONE_CREATED_BY_THIS_PROPOSAL",
        },
        "global_envelope_relationship": {
            "critical_finale_rewards": "guaranteed narrative package above; no probability tuning permitted",
            "future_optional_existing_identity_material_chest": "may use only the already-ratified W1-CREATIVE-004 C/U/R/E/Q bands and remains noncritical",
            "new_loot_identity": False,
            "finale_is_not_a_repeat_grind": True,
        },
        "durable_guards": {
            "world_completed": "aionbound.encounter.twinbond.completed.v1",
            "per_player_entitled": "aionbound.player.twinbond.reward_entitled.v1",
            "per_player_relic_claimed": "aionbound.player.twinbond.relic_claimed.v1",
            "per_player_edge_ignited": "aionbound.player.twinbond.edge_ignited.v1",
            "per_player_memory_claimed": "aionbound.player.twinbond.memory_claimed.v1",
            "per_player_mastery_stamp": "aionbound.player.twinbond.mastery_stamp.v1",
            "schema": "existing_G8_schema_only_no_new_domain",
        },
        "ordered_idempotent_fulfillment": [
            "require W1-003 terminal lock and durable world completion",
            "write each eligible player's completion and reward entitlement once",
            "write Concord Spark transition and Trophy Edge ignition credit once",
            "write missing chapter-curiosity credits without duplicating existing credits",
            "write optional non-inventory mastery stamp once",
            "preflight inventory capacity independently for Twinbond Relic, full Trophy Edge, and combined Memory item",
            "for each physical item with capacity, write its claimed flag before one delivery attempt",
            "for each physical item without capacity, retain entitlement and unclaimed state for recovery",
        ],
        "recovery": {
            "hook": "existing_twinbond_obelisk_or_completion_anchor_block_interaction_path_only",
            "new_UI_or_subscription": False,
            "available_when": "durable completion and per-player entitlement are true and at least one physical fulfillment remains unclaimed",
            "full_inventory": "remain in recovery; do not write claimed; do not consume entitlement; do not fall through to new encounter admission",
            "preclear_lock": "synchronous terminal/admission lock remains authoritative until all terminal writes complete",
            "restart": "durable completion and entitlement reopen recovery; never replay terminal combat or duplicate a claimed item",
            "crash_boundary": "claimed-before-delivery retains at-most-once physical delivery while durable progression and entitlement remain exactly-once/idempotent",
        },
        "repeat_clear": {
            "new_encounter_after_durable_completion": False,
            "duplicate_twinbond_relic": False,
            "duplicate_trophy_edge_ignition": False,
            "duplicate_memory_credit_or_combined_item": False,
            "duplicate_mastery_stamp": False,
            "post_clear_mastery_loops": "outside this encounter and optional; they never gate campaign completion",
        },
        "forbidden_inheritance": FORBIDDEN_INHERITANCE,
        "explicit_nondecisions": {
            "new_reward_identity": "NOT_CREATED",
            "new_loot_probability_for_existing_materials": "NOT_CREATED",
            "new_persistence_domain_or_schema": "FORBIDDEN",
            "new_UI_subscription_or_scheduler": "FORBIDDEN",
            "runtime_or_BDS_proof": "NOT_CLAIMED",
        },
    }
    payload["approval_required"] = [{
        "decision_id": "W1-004-TWINBOND",
        "question": "Ratify the guaranteed once-per-player Twinbond Relic/Edge/Memory package, optional non-item mastery stamp, full-inventory recovery, and no-repeat-final-reward semantics exactly as proposed?",
    }]
    return payload


def render_markdown(payload: dict) -> str:
    ticket = payload["ticket_id"]
    p = payload["proposal"]
    title = {
        "W1-002-TWINBOND": "Twinbond finale container, presentation, and exit proposal",
        "W1-003-TWINBOND": "Twinbond encounter execution proposal",
        "W1-004-TWINBOND": "Twinbond terminal reward and recovery proposal",
    }[ticket]
    lines = [f"# {ticket} — {title}", "", "Status: `PROPOSED_NOT_RATIFIED`", "", "This file has no authority effect until its exact JSON sibling is ratified into a replacement Wave 1 engineering decision ledger.", ""]
    if ticket == "W1-002-TWINBOND":
        lines += [
            "## Proposed closure", "",
            "- Use one durable, same-world authored finale site in the Overworld. Reuse the prepared 128×48×128 `twinbond_slice_v1`, its exact anchors, the five audited approach/arena inputs, and the two audited wyrm IDs. Do not adopt the old isolated logical container or add a portal/dimension system.",
            "- `Concord Spark` is abstract transition state, never an item.",
            "- `aionbound:memory_of_four_lands` is one non-placeable vanity/Codex inventory item composed from four durable chapter-curiosity credits. It gets one ordinary flat item icon; no four sibling item identities are created.",
            "- Unbound mastery-sigil prose becomes an optional non-inventory Codex mastery stamp, not a new item.",
            "- Durable Twinbond completion and Trophy Edge ignition gate the Wave 1 machine exit. Memory completion and post-clear mastery do not.",
        ]
    elif ticket == "W1-003-TWINBOND":
        lines += [
            "## Proposed execution", "",
            "- Preserve current G8 entity-component balance: 160 health and 8 attack damage per aspect, with no multiplayer health scaling and no proposed damage/radius/effect changes.",
            "- Run the four Creative phases exactly: Split Approach, Concord Pressure, Relic Trial, Finale Ignition. Paired health floors are 70% and 40%; neither aspect can die before the Relic Trial resolves.",
            "- Relic Trial requires 12 continuous seconds of eligible presence at the authored center focus. Finale Ignition is a five-second terminal window.",
            "- Use only existing action repertoires, globally serialized. No new attack identity is authorized.",
            "- Reset, restart, multiplayer ownership, durable completion, existing-schema persistence, and ordered terminal semantics are fully bounded in the JSON sibling.",
        ]
    else:
        lines += [
            "## Proposed fulfillment", "",
            "- On the sole valid ignition terminal, each eligible player gets one durable entitlement to `aionbound:twinbond_relic`, Trophy Edge ignition, missing chapter-curiosity credits, the combined Memory item when complete, and an optional non-item mastery stamp.",
            "- The narrative package is guaranteed; this proposal creates no random finale grind, new material probability, or new reward identity.",
            "- Durable state is written before bounded physical fulfillment. Full inventory retains recovery entitlement and cannot fall through to a new encounter.",
            "- Claimed flags are written before one physical delivery attempt, preserving at-most-once delivery while progression/entitlement writes remain idempotent.",
            "- Completed Twinbond cannot be replayed for duplicate finale rewards. Optional mastery remains outside campaign progression.",
        ]
    lines += [
        "## Preserved prohibitions", "",
        "The retired `trophy_concord_scale`, `finale_ignition_key`, `concord_sigil`, `concord_dueling_ring`, `ash_crownblade`, and `empress_tide_lance` path is forbidden. W1-CREATIVE-005 remains deferred. This proposal does not authorize pack/runtime edits, asset qualification, candidate freeze, build, BDS, or runtime claims.", "",
        "## Exact approval surface", "",
        payload["approval_required"][0]["question"], "",
    ]
    return "\n".join(lines)


def build_all() -> dict[str, dict]:
    return {
        "W1-002-TWINBOND": build_002(),
        "W1-003-TWINBOND": build_003(),
        "W1-004-TWINBOND": build_004(),
    }


def write_outputs(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for ticket, payload in build_all().items():
        (out / f"{ticket}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out / f"{ticket}.md").write_text(render_markdown(payload), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE)
    args = parser.parse_args()
    write_outputs(args.out)


if __name__ == "__main__":
    main()
