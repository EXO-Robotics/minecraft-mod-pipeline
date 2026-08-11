#!/usr/bin/env python3
"""Build the authority-neutral Ashen Creative support proposal tranche."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]

BASE_COMMIT = "faf8bab1785b3b847a70268c37ef813afd0495b4"
BASE_TREE = "3162be09bb1cb1b4ca10f1bf8132fbbf5e595282"

SOURCE_HASHES = {
    "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json": "3e2b64785da9310b098e06981ebc95777ddc7e5d2666f803b79ce374470a9561",
    "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json": "a9bc8133f8a0aacf7db258ffe76fc04dd9fcc6d07713bef630e074bd48588786",
    "engineering/authority/support-proposals/W1-CREATIVE-003/thorn_court_behavior_proposal.json": "04f7b9a75be6ac542d3488bd7563a601dcb94603905479b7c3e766c94b9d48c1",
    "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json": "4412b24ad680a30e5548c731f8acba94e8fd858e4bb94f701a16eb17141f5ab7",
    "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_ASHEN.md": "f5b2ff909a6e7b7669da561cc2659439819227f99d15d221dbea0147750d3727",
    "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md": "4d80925a113bb0cca67e2405047cd228a2df2ccd2c680e1e51ccd04b6f2d63d8",
    "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_SYSTEM.md": "6655eae0a65ed103a212f4b61d0f5c9352ddde871165b7bab9dbe014cfaaa8db",
    "program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md": "5ef85e1e0b29973a617f7dca4a8b119443c01644ba33f0e11166ef8d417d5a6f",
    "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json": "aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5",
    "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md": "3116c217e06afe1fd0cd56ee742c537f948a4c91193ec831fd1b3ec362837bfc",
}

ASHEN_ALIAS_TERMS = {
    "Ash Dust", "Mite Mandible", "Cinder Beak", "Ram Horn Curve", "Soot Antler", "Lynx Claw",
    "Ash Wool", "Char Hide", "Char Pelt", "Cinder Pelt", "Shell Plate", "Swarm Queen Scale",
    "Heat Scale", "Warm Blood Vial", "Smolder Gland", "Ember Fang", "Ember Sinew", "Stag Heart Cinder",
    "Beetle Core Fragment", "Char Feather",
}
ASHEN_NARRATIVE_TERMS = {
    "Scorched Message Tube", "Pack Cinder Mark", "Lynx Eye Gem", "Slow Stone", "Surviving Smith's Notes",
}
ASHEN_CONTEXT_TERMS = {
    "Drake Scale bundle", "resource bundle", "pattern scrap", "map scrap", "crate", "bulk", "chips", "dust",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_bindings(*paths: str) -> list[dict[str, str]]:
    return [{"path": p, "sha256": SOURCE_HASHES[p]} for p in paths]


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
            "region": "Ashen Highlands only",
            "creative_source_mutation": False,
            "existing_proposal_mutation": False,
            "decision_ledger_mutation": False,
            "pack_implementation_authorized": False,
            "scope_broadening": False,
        },
    }


def build_001() -> dict:
    source = load_json(REPO / "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json")
    proposal = source["proposal"]
    aliases = []
    for row in proposal["aliases"]:
        terms = [term for term in row["terms"] if term in ASHEN_ALIAS_TERMS]
        if terms:
            aliases.append({"terms": terms, "canonical_id": row["canonical_id"]})
    new_items = [copy.deepcopy(row) for row in proposal["new_required_items"] if row["id"] == "aionbound:drake_scale"]
    payload = common(
        "W1-001-AH",
        source_bindings(
            "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json",
            "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_ASHEN.md",
        ),
    )
    payload["proposal"] = {
        "selection_rule": "Exact Ashen subset of W1-CREATIVE-001 as written; no new identity or disposition.",
        "policy": copy.deepcopy(proposal["policy"]),
        "aliases": aliases,
        "narrative_codex_only": [term for term in proposal["narrative_codex_only"] if term in ASHEN_NARRATIVE_TERMS],
        "removed_or_context_only": [term for term in proposal["removed_or_context_only"] if term in ASHEN_CONTEXT_TERMS],
        "new_required_items": new_items,
        "new_inventory_identities_created_by_this_selection": [],
        "identity_count_after_ratification": {"selected_existing_new_required": 1, "additional": 0},
    }
    payload["approval_required"] = [{
        "decision_id": "W1-001-AH",
        "question": "Ratify only these already-written Ashen dispositions and the existing aionbound:drake_scale requirement?",
    }]
    return payload


def build_004() -> dict:
    source = load_json(REPO / "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json")
    proposal = source["proposal"]
    payload = common(
        "W1-004-AH",
        source_bindings(
            "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json",
            "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_SYSTEM.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_ASHEN.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md",
        ),
    )
    payload["proposal"] = {
        "selection_rule": "Adopt the existing W1-CREATIVE-004 global envelopes and guard semantics verbatim for Ashen, then resolve only Ashen seal roles.",
        "probability_and_quantity_envelopes": copy.deepcopy(proposal["probability_and_quantity_envelopes"]),
        "boss_package": copy.deepcopy(proposal["boss_package"]),
        "structure_chest_bands": copy.deepcopy(proposal["structure_chest_bands"]),
        "arena_reward_guard": copy.deepcopy(proposal["arena_reward_guard"]),
        "tuning_rule": proposal["tuning_rule"],
        "ashen_resolution": {
            "chapter_critical_seal": "aionbound:ash_drake_horn",
            "chapter_critical_seal_count": 1,
            "ecology_or_natural_ash_drake_can_drop_chapter_seal": False,
            "valid_seal_source": "active_kiln_sky_arena_session_plus_apex_entity_tag_plus_valid_death_event",
            "critical_progression_representation": "durable_virtual_seal_credit_not_physical_item_presence",
            "physical_horn_fulfillment": "at_most_once_best_effort_with_recovery_claim",
            "ember_forge_core": {
                "role": "optional_mastery_and_forge_reward",
                "progression_substitute_for_ash_drake_horn": False,
                "may_fill_pilgrim_seal_slot": False,
                "allowed_sources": ["ember_forge_or_ancient_kiln_structure_reward", "kiln_sky_optional_reward_roll"],
            },
            "repeat_clear": {
                "material_package_and_arena_chest": "allowed",
                "ash_drake_horn_entitlement": "not_reissued",
                "virtual_seal_credit": "not_reissued",
                "ember_forge_core_optional_roll": "allowed",
            },
        },
    }
    payload["approval_required"] = [{
        "decision_id": "W1-004-AH",
        "question": "Ratify the existing global envelope and guard model for Ashen with ash_drake_horn as the sole critical seal and ember_forge_core optional only?",
    }]
    return payload


def build_003() -> dict:
    payload = common(
        "W1-003-KILN-SKY",
        source_bindings(
            "engineering/authority/support-proposals/W1-CREATIVE-003/thorn_court_behavior_proposal.json",
            "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
            "program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md",
            "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json",
            "program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md",
        ),
    )
    payload["proposal"] = {
        "encounter_id": "aionbound:kiln_sky",
        "boss_entity_id": "aionbound:ash_drake",
        "arena_link": "aionbound:ember_forge",
        "arena_form_predicate": "encounter_session_active_and_entity_tag_aionbound.kiln_sky_apex",
        "ecology_or_natural_form_can_complete_chapter": False,
        "all_numeric_values_status": "PROPOSED_NOT_RATIFIED",
        "health": {
            "solo": 480,
            "per_additional_locked_participant_multiplier": 0.3,
            "participant_cap": 4,
            "rationale": "A longer second-chapter apex than Thorn Court while capping console-first multiplayer growth at four locked participants.",
        },
        "phases": [
            {"id": "ash_landing", "enter_at_health_fraction": 1.0, "exit_at_health_fraction": 0.7, "available_attacks": ["cinder_breath", "tail_slag"], "active_ash_mite_cap": 0},
            {"id": "vent_choir", "enter_at_health_fraction": 0.7, "exit_at_health_fraction": 0.4, "available_attacks": ["cinder_breath", "tail_slag", "thermal_dive", "mite_shake"], "active_ash_mite_cap": 4},
            {"id": "glass_wing", "enter_at_health_fraction": 0.4, "exit_at_health_fraction": 0.15, "available_attacks": ["cinder_breath", "thermal_dive", "basalt_quake", "glass_feather_storm", "mite_shake"], "active_ash_mite_cap": 4},
            {"id": "kiln_heart", "enter_at_health_fraction": 0.15, "exit_at_health_fraction": 0.0, "available_attacks": ["cinder_breath", "tail_slag", "thermal_dive", "basalt_quake", "glass_feather_storm"], "active_ash_mite_cap": 2},
        ],
        "phase_rationale": "70/40/15 creates three readable teaching bands and a short commit-burst enrage without adding a fifth Creative phase.",
        "timing_seconds": {
            "global_attack_cooldown": [2.75, 4.5],
            "cinder_breath": {"telegraph": [1.0, 1.3], "active": [1.2, 1.8], "recovery": [0.9, 1.2], "cooldown": [7.0, 10.0]},
            "tail_slag": {"telegraph": [0.7, 1.0], "active": [0.25, 0.45], "recovery": [0.8, 1.1], "cooldown": [5.0, 8.0]},
            "thermal_dive": {"telegraph": [1.4, 1.8], "active": [0.6, 1.0], "recovery": [1.3, 1.8], "cooldown": [10.0, 14.0]},
            "mite_shake": {"telegraph": [1.3, 1.7], "active": [0.3, 0.5], "recovery": [1.0, 1.4], "cooldown": [18.0, 24.0], "spawn_count": [2, 3]},
            "basalt_quake": {"telegraph": [1.3, 1.7], "active": [0.35, 0.55], "recovery": [1.0, 1.4], "cooldown": [10.0, 14.0]},
            "glass_feather_storm": {"telegraph": [1.6, 2.0], "active": [4.0, 6.0], "recovery": [1.3, 1.8], "cooldown": [14.0, 20.0]},
        },
        "timing_rationale": "All six authored attacks expose telegraph, active, recovery, and cooldown windows; add creation is slower than ordinary attacks and bounded by the active cap.",
        "reset": {
            "leash_boundary": "authored_kiln_sky_arena_volume_no_new_radius_number",
            "outside_leash_grace_seconds": 10,
            "no_eligible_player_grace_seconds": 30,
            "all_players_dead_or_outside_grace_seconds": 15,
            "world_reload_behavior": "reset_to_unpulled_full_health_and_clear_session_transients",
            "on_reset": ["despawn_session_ash_mites", "clear_session_hazards", "restore_boss_health", "clear_active_session"],
            "completion_is_not_cleared": True,
            "rationale": "Short boundary grace avoids transient flight-path resets, while dead/absent-player windows terminate abandoned sessions and reload always clears nonpersistent fight state.",
        },
        "multiplayer": {
            "participant_snapshot": "lock_at_pull",
            "eligible_at_pull": "player_inside_authored_arena_volume_for_at_least_5_seconds",
            "late_join": "eligible_only_before_glass_wing_and_after_15_seconds_inside_authored_arena_volume",
            "disconnect_grace_seconds": 60,
            "scaling_does_not_decrease_midfight": True,
            "targeting": "never_requires_damage_to_one_specific_player",
            "global_session_ash_mite_cap": 4,
            "ownership": "per_player_terminal_entitlement_for_locked_or_approved_late_join_participants",
            "rationale": "Pull locking prevents health-scale manipulation; a bounded late-join window preserves co-op access before the third phase; disconnect grace avoids punishing brief network loss.",
        },
        "persistence": {
            "active_fight": "not_persisted",
            "world_completion_key": "aionbound.encounter.kiln_sky.completed.v1",
            "player_completion_key": "aionbound.player.kiln_sky.completed.v1",
            "reward_entitlement_key": "aionbound.player.kiln_sky.reward_entitled.v1",
            "seal_credit_key": "aionbound.player.kiln_sky.seal_credit.v1",
            "physical_horn_claimed_key": "aionbound.player.kiln_sky.trophy_claimed.v1",
            "migration": "idempotent_false_default",
        },
        "terminal_semantics": {
            "complete_on": "arena_form_valid_death_event_with_active_session",
            "eligible_players": "locked_or_approved_late_join_participants_present_or_in_disconnect_grace",
            "progression_credit": "per_player_durable_once",
            "world_stamp": "durable_once",
            "reward_identity_and_fulfillment_source": "W1-004-AH_only",
            "repeat_clear": "encounter_repeatable_but_no_duplicate_chapter_progression_or_horn_entitlement",
        },
        "explicit_nondecisions": {
            "damage_values": "NOT_CREATED_BY_THIS_PROPOSAL_ENGINEERING_TUNES_ONLY_INSIDE_A_SEPARATELY_APPROVED_OR_MEASURED_ENVELOPE",
            "attack_effect_radii": "NOT_CREATED_BY_THIS_PROPOSAL_ENGINEERING_TUNES_ONLY_INSIDE_A_SEPARATELY_APPROVED_OR_MEASURED_ENVELOPE_AND_AUTHORED_ARENA",
            "arena_radius_blocks": "NOT_CREATED_USE_AUTHORED_STRUCTURE_VOLUME",
            "new_attacks": "FORBIDDEN_ONLY_THE_SIX_APPROVED_ATTACK_IDENTITIES",
            "new_phases": "FORBIDDEN_ONLY_THE_FOUR_APPROVED_PHASE_IDENTITIES",
        },
    }
    payload["approval_required"] = [{
        "decision_id": "W1-003-KILN-SKY",
        "question": "Ratify this minimal Kiln Sky state, timing, reset, ownership, persistence, and terminal envelope without approving any damage or radius values?",
    }]
    return payload


def markdown(payload: dict) -> str:
    ticket = payload["ticket_id"]
    proposal = payload["proposal"]
    lines = [
        f"# {ticket} — Ashen support proposal",
        "",
        "**Status:** `PROPOSED_NOT_RATIFIED`",
        "**Authority effect:** none until an explicit replacement decision ledger ratifies this ticket.",
        "",
        "This proposal is Ashen-only. It does not edit Creative sources, prior proposals, the decision ledger, BP, or RP.",
        "",
    ]
    if ticket == "W1-001-AH":
        lines += [
            "## Exact selection",
            "",
            f"- Existing Ashen alias rows selected: {len(proposal['aliases'])}.",
            f"- Narrative/Codex-only terms selected: {len(proposal['narrative_codex_only'])}.",
            f"- Removed/context-only terms selected: {len(proposal['removed_or_context_only'])}.",
            "- The only selected required inventory identity is the already-written `aionbound:drake_scale` row.",
            "- Additional identities created: zero.",
        ]
    elif ticket == "W1-004-AH":
        lines += [
            "## Exact selection and Ashen resolution",
            "",
            "The C/U/R/E/T/Q intervals, boss package, four chest bands, virtual seal credit, recovery-aware at-most-once physical fulfillment, and repeat-clear model are copied from W1-CREATIVE-004 without numeric alteration.",
            "",
            "`aionbound:ash_drake_horn` is the only chapter-critical seal. Ecology/natural Ash Drake forms cannot award it. `aionbound:ember_forge_core` remains an optional mastery/forge reward and never substitutes for the horn or fills the Pilgrim seal slot.",
        ]
    else:
        lines += [
            "## Minimal executable envelope",
            "",
            "The proposal binds only the approved four phase identities and six attack identities to proposed thresholds, timing ranges, reset/leash behavior, bounded adds, multiplayer ownership, persistence, and terminal/repeat semantics.",
            "",
            "Every new number remains `PROPOSED_NOT_RATIFIED`. Damage values, attack radii, and an arena-radius number are deliberately not invented; implementation uses the authored arena volume and requires separately approved/measured Engineering constraints for mechanical tuning.",
        ]
    lines += [
        "",
        "## Source binding",
        "",
        f"Base commit `{payload['source_commit']}`; base tree `{payload['source_tree']}`.",
        "",
    ]
    for row in payload["source_bindings"]:
        lines.append(f"- `{row['sha256']}` — `{row['path']}`")
    lines += ["", "The sibling JSON is canonical.", ""]
    return "\n".join(lines)


def write_outputs(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for payload in (build_001(), build_004(), build_003()):
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
