#!/usr/bin/env python3
"""Build the paused Crazy Craft fixed-pack factory control artifacts.

This script is deliberately control-plane only.  It does not initialize or
mutate product repositories, dispatch workers, build packs, run audits, or run
BDS.  It transforms the frozen 52-artifact accounting map into fixed product
ownership, deterministic allocations, sanitized producer contracts, durable
pack-owner assignments, and mailbox schemas.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / "stabilization-v1" / "pack-factory-v1"
SECTION_MAP = REPO / "stabilization-v1" / "ten-sections" / "CRAZY_CRAFT_TEN_SECTION_PORTFOLIO_MAP.json"
WORKSPACE = REPO.parents[1]
PRODUCTION_ROOT = WORKSPACE / "program" / "crazycraft-pack-production-v1"
MAILBOX_REPOSITORY = WORKSPACE / "program" / "crazycraft-pack-factory-mailboxes-v1"
PLATFORM_ID = "CRAZY_CRAFT_BEDROCK_PLATFORM_V1"
PLATFORM_AUTHORITY = {
    "repository": str(WORKSPACE / "minecraft-compiler-baseline"),
    "commit": "aba740f136dce5781e68d34e1c7aaa2a0a3d8671",
    "tree": "2d5c123c9cbc6d4cdaac2ff922916450b5282d08",
    "aggregate_sha256": "84e79568550d800717798858c254498e682d452ec4ab6b95e6320d1a79397f57",
    "manifest_sha256": "b7de7329fd78b451994b367e0ac226099e8d260bd21309f3f5753b3830c42630",
    "interface_classification": "FROZEN_PLATFORM_V1_CONTRACTS",
}
UUID_NAMESPACE = uuid.NAMESPACE_URL
CREATED_AT = "2026-07-29T16:00:00Z"

ACCEPTED_FOUNDATIONS = {
    "aspectweave": [
        {
            "decision_id": "D-000004",
            "repository": str(REPO),
            "decision_path": "stabilization-v1/epochs/epoch-0001/decisions/D-000004-aspectweave-foundation-admission.json",
            "content_commit": "de22c564da01ec69e6fa01143c27bd6c48cb2ea1",
            "content_tree": "54b7ebc6f543cdc0e4b39bc3b893429f9538f3d3",
            "classification": "SANITIZED_FOUNDATION_FOUNDATION_READY",
        }
    ],
    "echo-vessels": [
        {
            "decision_id": "D-000005",
            "repository": str(REPO),
            "decision_path": "stabilization-v1/epochs/epoch-0001/decisions/D-000005-echo-foundation-blocked-registration.json",
            "content_commit": "bdaed995574093c8b9149b15f5320ddcc04d1553",
            "content_tree": "916d201db3085a79ad5afea8b2d111a469cd4194",
            "classification": "SANITIZED_FOUNDATION_SHARED_RUNTIME_BLOCKED",
        }
    ],
    "hearthveil": [
        {
            "decision_id": "D-000007",
            "repository": str(REPO),
            "decision_path": "stabilization-v1/epochs/epoch-0001/decisions/D-000007-hearthveil-foundation-admission.json",
            "content_commit": "61591c961ce0dd3f9c4699e7303d6e0d71822d64",
            "content_tree": "c7591b148780609c419afdc1060f21391a4e3a09",
            "classification": "SANITIZED_FOUNDATION_FOUNDATION_READY",
        },
        {
            "decision_id": "D-000001",
            "repository": str(REPO),
            "decision_path": "stabilization-v1/decisions/D-000001-ownership-transfer.json",
            "content_commit": "1ef47f4ebde3241e3a15ffbc44f8926eb59f8d10",
            "content_tree": "356caf1424adf2168b901213c5cef76c2f62cab2",
            "classification": "SOURCE_NEUTRAL_TRAVEL_CONTROL_OWNERSHIP_TRANSFER",
        },
    ],
    "bounded-outcome-events": [
        {
            "decision_id": "D-000002",
            "repository": str(REPO),
            "decision_path": "stabilization-v1/decisions/D-000002-ownership-transfer.json",
            "content_commit": "8edf2a6904b788f981503458420ccbcd4cc338ad",
            "content_tree": "12680669664677c165293b281e50e3c6fb04d1aa",
            "classification": "SOURCE_NEUTRAL_FOUNDATION_SOLE_OWNERSHIP_TRANSFER",
        }
    ],
}

EXISTING_ASSET_CLASS_COUNTS = {
    "quietwork": {"HERO": 0, "REUSABLE_COMPLEX": 0, "ROUTINE_MODEL": 0, "ICON": 12, "PARTICLE": 0, "SOUND": 0, "NOT_REQUIRED": 1},
    "catalyst-wilds": {"HERO": 5, "REUSABLE_COMPLEX": 18, "ROUTINE_MODEL": 0, "ICON": 30, "PARTICLE": 11, "SOUND": 22, "NOT_REQUIRED": 0},
    "shatterwild-foundry": {"HERO": 8, "REUSABLE_COMPLEX": 38, "ROUTINE_MODEL": 0, "ICON": 40, "PARTICLE": 4, "SOUND": 12, "NOT_REQUIRED": 0},
    "trailbound-packs": {"HERO": 8, "REUSABLE_COMPLEX": 0, "ROUTINE_MODEL": 0, "ICON": 8, "PARTICLE": 1, "SOUND": 12, "NOT_REQUIRED": 0},
    "pocketbound-companions": {"HERO": 1, "REUSABLE_COMPLEX": 0, "ROUTINE_MODEL": 0, "ICON": 14, "PARTICLE": 0, "SOUND": 0, "NOT_REQUIRED": 0},
    "wayfarer-settlements": {"HERO": 12, "REUSABLE_COMPLEX": 25, "ROUTINE_MODEL": 0, "ICON": 74, "PARTICLE": 8, "SOUND": 12, "NOT_REQUIRED": 0},
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(canonical_bytes(value))


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def git_tree(repository: Path, commit: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repository), "show", "-s", "--format=%T", commit],
        text=True,
    ).strip()


def uuid_set(authority_id: str, namespace: str, major: int = 1) -> dict[str, str]:
    result: dict[str, str] = {}
    for role in (
        "behavior_header",
        "behavior_data_module",
        "behavior_script_module",
        "resource_header",
        "resource_resources_module",
    ):
        seed = f"{PLATFORM_ID}|{authority_id}|{namespace}|{role}|{major}"
        result[role] = str(uuid.uuid5(UUID_NAMESPACE, seed))
    return result


SOURCE_RULES = {
    "mods/Adventure Backpack.jar": ("trailbound-packs", "EXISTING_AUTHORITY"),
    "mods/Inventory Pets.jar": ("pocketbound-companions", "EXISTING_AUTHORITY"),
    "mods/Jewelrycraft 2.jar": ("reliquary-vaults", "PACK"),
    "mods/Baubles.jar": ("reliquary-vaults", "PACK_CONSOLIDATED_DEPENDENCY"),
    "mods/Iron Chest.jar": ("reliquary-vaults", "PACK_CONSOLIDATED_ROLE"),
    "mods/CustomNpcs.jar": ("wayfarer-settlements", "EXISTING_AUTHORITY"),
    "mods/BiblioCraft.jar": ("hearth-and-hall", "PACK"),
    "mods/Carpenter's Blocks.jar": ("hearth-and-hall", "PACK"),
    "mods/Chisel 2.jar": ("hearth-and-hall", "PACK"),
    "mods/Decocraft.jar": ("hearth-and-hall", "PACK"),
    "mods/MrCrayfish's Furniture Mod.jar": ("hearth-and-hall", "PACK"),
    "mods/Statues.jar": ("hearth-and-hall", "PACK"),
    "mods/Witchery.jar": ("hearthveil", "PACK"),
    "mods/Equivalent Exchange 3.jar": ("hearthveil", "PACK_CONSOLIDATED_ROLE"),
    "mods/Morph.jar": ("aspectweave", "PACK"),
    "mods/Armourer's Workshop.jar": ("aspectweave", "PACK_CONSOLIDATED_ROLE"),
    "mods/Hats.jar": ("aspectweave", "PACK_CONSOLIDATED_ROLE"),
    "mods/HatStand-4.0.0.jar": ("aspectweave", "PACK_CONSOLIDATED_ROLE"),
    "mods/iChunUtil.jar": ("aspectweave", "PACK_CONSOLIDATED_DEPENDENCY"),
    "mods/AnimationAPI.jar": ("aspectweave", "PACK_CONSOLIDATED_DEPENDENCY"),
    "mods/Superheroes Mod.jar": ("vanguard-arsenal", "PACK"),
    "mods/Mine & Blade Battlegear 2 - Bullseye.jar": ("vanguard-arsenal", "PACK_CONSOLIDATED_ROLE"),
    "mods/GravityGun.jar": ("vanguard-arsenal", "PACK_CONSOLIDATED_ROLE"),
    "mods/Mutant Creatures.jar": ("catalyst-wilds", "EXISTING_AUTHORITY"),
    "mods/Transformers Mod.jar": ("aperture-foundry", "PACK_ORIGINAL_REDESIGN"),
    "mods/PortalGun-4.0.0-beta-4.jar": ("aperture-foundry", "PACK_ORIGINAL_REDESIGN"),
    "mods/Tardis Mod.jar": ("aperture-foundry", "PACK_ORIGINAL_REDESIGN"),
    "mods/Soul Shards- The Old Ways.jar": ("echo-vessels", "PACK"),
    "mods/Weeping Angels.jar": ("echo-vessels", "PACK_ORIGINAL_REDESIGN"),
    "mods/Origin.jar": ("echo-vessels", "PACK_CONSOLIDATED_DEPENDENCY"),
    "mods/Mob Properties.jar": ("shared-platform:adaptive-creature-policy", "SHARED_PLATFORM_REQUIREMENT"),
    "mods/Pandora's Box.jar": ("bounded-outcome-events", "PACK"),
    "mods/LuckyBlocks.jar": ("bounded-outcome-events", "PACK_CONSOLIDATED_ROLE"),
    "mods/Killer Pacman.jar": ("momentum-menagerie", "PACK_ORIGINAL_REDESIGN"),
    "mods/TrailMix.jar": ("momentum-menagerie", "PACK"),
    "mods/FoodPlus.jar": ("momentum-menagerie", "PACK_CONSOLIDATED_ROLE"),
    "mods/Hardcore Ender Expansion.jar": ("no-standalone:disabled-placeholder", "NO_STANDALONE"),
    "mods/Railcraft.jar": ("latchline-infrastructure", "PACK"),
    "mods/SecurityCraft.jar": ("latchline-infrastructure", "PACK"),
    "mods/The SecretRoomsMod.jar": ("quietwork", "EXISTING_AUTHORITY"),
    "mods/Malisis' Doors.jar": ("latchline-infrastructure", "PACK_CONSOLIDATED_ROLE"),
    "mods/Malisis' Core.jar": ("latchline-infrastructure", "PACK_CONSOLIDATED_DEPENDENCY"),
    "mods/1.7.10/CodeChickenLib-1.7.10-1.1.3.138-universal.jar": ("no-standalone:dependency-library", "NO_STANDALONE"),
    "mods/CodeChickenCore.jar": ("no-standalone:dependency-library", "NO_STANDALONE"),
    "mods/asielib.jar": ("no-standalone:dependency-library", "NO_STANDALONE"),
    "mods/Dark Core.jar": ("no-standalone:dependency-library", "NO_STANDALONE"),
    "mods/MobiusCore.jar": ("no-standalone:dependency-library", "NO_STANDALONE"),
    "mods/NEI Addons.jar": ("shared-platform:recipe-reachability", "SHARED_PLATFORM_REQUIREMENT"),
    "mods/Opis.jar": ("shared-platform:diagnostics", "SHARED_PLATFORM_REQUIREMENT"),
    "mods/Saintscore.jar": ("no-standalone:dependency-library", "NO_STANDALONE"),
    "mods/Controlling.jar": ("shared-platform:controller-conventions", "SHARED_PLATFORM_REQUIREMENT"),
    "mods/CustomMenu.jar": ("shared-platform:menu-localization", "SHARED_PLATFORM_REQUIREMENT"),
}


COMMON_REQUIRED_OUTPUTS = [
    "complete_behavior_pack",
    "complete_resource_pack_when_applicable",
    "manifest_declared_scripts_main_js_when_scripted",
    "original_editable_asset_sources",
    "local_unit_and_integration_tests",
    "deterministic_builder",
    "exact_bp_rp_mcaddon_artifacts",
    "artifact_manifest",
    "candidate_bound_process_isolation_receipt",
    "immutable_candidate_submission_message",
]

COMMON_COMPLETION = {
    "terminal_success": "PACK_ACCEPTED_AND_INTEGRATED",
    "terminal_alternatives": [
        "TERMINALLY_UNAVAILABLE",
        "USER_DECISION_REQUIRED",
        "EXTERNAL_PHYSICAL_GATE_REQUIRED",
    ],
    "nonterminal_events": [
        "contract_created",
        "vertical_slice_created",
        "preliminary_candidate_published",
        "candidate_submitted_to_testing",
        "one_repair_completed",
        "waiting_for_tester",
        "standalone_test_pass",
    ],
}


def gameplay(
    loop: str,
    progression: list[str],
    items: list[str],
    blocks: list[str],
    entities: list[str],
    encounters: list[str],
    crafting_loot: list[str],
    ownership: str,
    persistence: str,
    multiplayer: str,
    recovery: str,
    presentation: str,
) -> dict[str, Any]:
    return {
        "core_gameplay_loop": loop,
        "player_progression": progression,
        "items": items,
        "blocks": blocks,
        "entities": entities,
        "encounters": encounters,
        "crafting_and_loot": crafting_loot,
        "ownership_rules": ownership,
        "persistence": persistence,
        "multiplayer_behavior": multiplayer,
        "restart_and_reconnect": "Versioned state reconstructs idempotently; stale callbacks and generations are inert.",
        "recovery_and_cleanup": recovery,
        "controller_conscious_interaction": "All primary actions use ordinary item use, block interact, inventory, dialogue forms, or bounded action forms; no keyboard-only requirement.",
        "required_original_presentation": presentation,
    }


def planned_assets(
    *,
    hero: int,
    reusable: int,
    routine: int,
    icons: int,
    particles: int,
    sounds: int,
    bbmodels: int,
    textures: int,
    animations: int,
    controllers: int,
    ui: int,
    renders: int,
) -> dict[str, Any]:
    return {
        "authority_state": "PLANNED_ORIGINAL_PRODUCTION",
        "class_counts": {
            "HERO": hero,
            "REUSABLE_COMPLEX": reusable,
            "ROUTINE_MODEL": routine,
            "ICON": icons,
            "PARTICLE": particles,
            "SOUND": sounds,
            "NOT_REQUIRED": 0,
        },
        "expected_outputs": {
            "models": hero + reusable + routine,
            "editable_bbmodel_files": bbmodels,
            "textures": textures,
            "icons": icons,
            "animations": animations,
            "animation_controllers": controllers,
            "particles": particles,
            "sounds": sounds,
            "ui_elements": ui,
            "localization_sets": 1,
            "proof_renders": renders,
        },
        "rules": [
            "Blockbench is NOT_APPLICABLE for flat icons and ordinary full-cube blocks unless custom geometry materially supports the product.",
            "Every custom geometry source must reopen natively and export twice to normalized equivalent runtime geometry.",
            "Hero and reusable-complex assets require independent Golden scoring; routine assets require originality, readability, and technical validity.",
            "Repairs update editable sources first; export-only hand edits are forbidden.",
        ],
    }


EXISTING = {
    "quietwork": {
        "classification": "FINAL_OR_REFERENCE",
        "namespace": "ccoriginal_cc",
        "semantic_version": [1, 1, 0],
        "repository": str(WORKSPACE / ".derivedData/worktrees/authorized-java-secretrooms-v1/v1.1-integration"),
        "ref": "refs/heads/codex/quietwork-v1.1-reference",
        "content_commit": "26fd00c7e00a8c3ec2f57e5bde071068d5d426e4",
        "content_tree": "fa74786c8c1b608e7c7662da2c8a33848847a21b",
        "metadata_commit": "14e74bd49d0f04e5f30dea36a336c600d38be8fe",
        "metadata_tree": "99bff707663b109cd2fcf1b0371a956c0adb3ec6",
        "artifacts": {
            "behavior_pack": {
                "path": str(WORKSPACE / ".derivedData/worktrees/authorized-java-secretrooms-v1/v1.1-integration/production/segments/quietwork-v1/dist/quietwork-v1-behavior-SERVER-TEST-CANDIDATE.mcpack"),
                "sha256": "143b0eafc948affc05f52530304ea6bf59059800f530a55444577524e3d34e3f",
            },
            "resource_pack": {
                "path": str(WORKSPACE / ".derivedData/worktrees/authorized-java-secretrooms-v1/v1.1-integration/production/segments/quietwork-v1/dist/quietwork-v1-resource-SERVER-TEST-CANDIDATE.mcpack"),
                "sha256": "66afe2812ba2d7814b33cb11348f03213cf97a00b63d5026d32b6b2ab5541000",
            },
            "mcaddon": {
                "path": str(WORKSPACE / ".derivedData/worktrees/authorized-java-secretrooms-v1/v1.1-integration/production/segments/quietwork-v1/dist/quietwork-v1-SERVER-TEST-CANDIDATE.mcaddon"),
                "sha256": "f7ad3aec771a120809b42dd82d6ad92e141ee8eecd5a0e0b4561d3b9ed42fbd5",
            },
        },
        "uuids": {
            "behavior_header": "26d31540-44f7-5fb4-9d6f-7e79d720c709",
            "behavior_data_module": "b3eaaf5e-3b66-5e8a-b892-1cf916b22ed5",
            "behavior_script_module": "9f643da5-d813-5e54-af89-28c5dcf41011",
            "resource_header": "51b31164-ae85-5370-b1a0-4d763539f7ed",
            "resource_resources_module": "5ad06e65-da09-59a7-864f-c61580bc466b",
        },
        "asset_inventory": {
            "authority_state": "PRESERVE_EXISTING",
            "editable_bbmodel_files": 0,
            "textures_png": 50,
            "custom_geometry": 0,
            "animations": 0,
            "animation_controllers": 0,
            "particles": 0,
            "sounds": 0,
            "ui_elements": 0,
            "localization_sets": 2,
            "blockbench": "NOT_APPLICABLE",
        },
    },
    "catalyst-wilds": {
        "classification": "AWAITING_TEST",
        "namespace": "exowild",
        "semantic_version": [1, 0, 0],
        "repository": str(WORKSPACE / ".derivedData/authorities/catalyst-wilds"),
        "ref": "refs/heads/main",
        "content_commit": "2a72b72002c8eedd787262c1a6c7c00862447920",
        "content_tree": "ebe24edf61491f8e598574fd3d8ba2881112cf45",
        "metadata_commit": None,
        "metadata_tree": None,
        "artifacts": {
            "behavior_pack": None,
            "resource_pack": None,
            "mcaddon": {
                "path": str(WORKSPACE / ".derivedData/authorities/catalyst-wilds/packages/catalyst-wilds-v1.mcaddon"),
                "sha256": "86e582665f7e4fa268de977e4fb7a3ff18be9c13a565e72c42f3ee586dffa787",
            },
        },
        "uuids": {
            "behavior_header": "451b2d48-282b-5c69-88e9-29fd9f2e29f4",
            "behavior_data_module": "bb81ee02-a2c9-5632-b8b2-8f92f7d1a95e",
            "behavior_script_module": "91cd2202-a58a-5272-a5e8-94f67c63cf53",
            "resource_header": "d657b69c-4671-57ef-a55f-404fcf64a625",
            "resource_resources_module": "a98dc5a5-4fa8-5592-bf0c-1b5f8a752e47",
        },
        "asset_inventory": {
            "authority_state": "PRESERVE_EXISTING",
            "editable_bbmodel_files": 23,
            "textures_png": 341,
            "custom_geometry": 1,
            "animations": 1,
            "animation_controllers": 1,
            "particles": 11,
            "sounds": 22,
            "ui_elements": 0,
            "localization_sets": 1,
        },
    },
    "shatterwild-foundry": {
        "classification": "FINAL_OR_REFERENCE",
        "namespace": "ccoriginal_sw",
        "semantic_version": [1, 0, 0],
        "repository": str(WORKSPACE / ".derivedData/cleanroom/shatterwild-closure-repair-v1/lanes/production-repair"),
        "ref": "refs/heads/codex/import-shatterwild-foundry",
        "content_commit": "11c5d7cfbb887d1f5246f85ffb34e5b340144f5f",
        "content_tree": "ce1dbafdaa04673885e755f5f9747aaf359b3eea",
        "metadata_commit": None,
        "metadata_tree": None,
        "artifacts": {
            "behavior_pack": {
                "path": str(WORKSPACE / ".derivedData/cleanroom/shatterwild-closure-repair-v1/lanes/production-repair/production/integrated/artifacts/Shatterwild_Foundry_BP.mcpack"),
                "sha256": "d3f2652738d68ef3b82f713adcf9028a81d5069ff6fc38de58e0ec2cd65ed1da",
            },
            "resource_pack": {
                "path": str(WORKSPACE / ".derivedData/cleanroom/shatterwild-closure-repair-v1/lanes/production-repair/production/integrated/artifacts/Shatterwild_Foundry_RP.mcpack"),
                "sha256": "10ffb3c6af0b02f2e23a36284ceb249d63b68f23a9fbb961b36d575855aec702",
            },
            "mcaddon": {
                "path": str(WORKSPACE / ".derivedData/cleanroom/shatterwild-closure-repair-v1/lanes/production-repair/production/integrated/artifacts/Shatterwild_Foundry.mcaddon"),
                "sha256": "80467eae5cdb4303593e725572364177d8d53f8e73c5d02538a5469d9837dd56",
            },
        },
        "uuids": {
            "behavior_header": "35b53416-a79f-4714-96e3-3520fb7a84e9",
            "behavior_data_module": "406259ff-d2af-41db-bb12-9cc938463071",
            "behavior_script_module": "f2280535-e33c-4bb0-8e02-7893ea315064",
            "resource_header": "7d2b57ba-9bbb-40e9-96a1-534c626394b0",
            "resource_resources_module": "d6cf8f8f-fb72-4e9a-bbdf-b87064a3bf07",
        },
        "asset_inventory": {
            "authority_state": "PRESERVE_EXISTING",
            "editable_bbmodel_files": 46,
            "textures_png": 384,
            "custom_geometry": 56,
            "animations": 54,
            "animation_controllers": 44,
            "particles": 4,
            "sounds": 12,
            "ui_elements": 0,
            "localization_sets": 10,
        },
    },
    "trailbound-packs": {
        "classification": "AWAITING_TEST",
        "namespace": "ccr_p07",
        "semantic_version": [1, 1, 0],
        "repository": str(WORKSPACE / "program/crazycraft-autonomous-worker-lanes-v1/thread-09"),
        "ref": "refs/heads/main",
        "content_commit": "d2d737c5b7110c1c596ce429649fb002efdf9049",
        "content_tree": "47d8d3e409b8cc1b6de49654456f6cee5ddfb201",
        "metadata_commit": "3cfcc28f7a15a8f31413b77ca0cbd6f3c137f5e5",
        "metadata_tree": "f4dfc5db028a709bc89b588b57719ad78b215d8b",
        "artifact_commit": "3cfcc28f7a15a8f31413b77ca0cbd6f3c137f5e5",
        "content_bundle": {
            "path": str(WORKSPACE / "program/crazycraft-autonomous-worker-lanes-v1/thread-09/trailbound-golden-repair-v2/candidate/trailbound-golden-repair-v2.bundle"),
            "sha256": "64ef65c1a6d5b90ac55af7f4aa05a951574e055966287ec7912eb01aa706be72",
        },
        "artifacts": {
            "behavior_pack": {
                "path": str(WORKSPACE / "program/crazycraft-autonomous-worker-lanes-v1/thread-09/trailbound-golden-repair-v2/candidate/trailbound-packs-behavior.mcpack"),
                "sha256": "f26e9daddfd7ba8893f6ccd5934b45ec0f88e1380b3e02038c13051d71fad8f3",
            },
            "resource_pack": {
                "path": str(WORKSPACE / "program/crazycraft-autonomous-worker-lanes-v1/thread-09/trailbound-golden-repair-v2/candidate/trailbound-packs-resource.mcpack"),
                "sha256": "14fcdba454ab5ca85381628d71845dadc80b9c255eb812b7aaebea84814ef7af",
            },
            "mcaddon": {
                "path": str(WORKSPACE / "program/crazycraft-autonomous-worker-lanes-v1/thread-09/trailbound-golden-repair-v2/candidate/trailbound-packs.mcaddon"),
                "sha256": "949fa581e930460a8bcc8e02f574d1bc89f848a754c57ec84907f07f27372bc4",
            },
        },
        "uuids": {
            "behavior_header": "7c428986-b20f-548d-84ae-1c56029426b2",
            "behavior_data_module": "8ebbf794-79de-5401-845b-8c8e67fb9921",
            "behavior_script_module": "2ed26f2f-0adc-594c-87db-9f0da045b472",
            "resource_header": "565a3efe-77ac-5533-8097-3098881e17d0",
            "resource_resources_module": "052be8ee-7a9d-562c-8631-cfb0f1e9d2b1",
        },
        "asset_inventory": {
            "authority_state": "PRESERVE_EXISTING",
            "editable_bbmodel_files": 8,
            "textures_png": 137,
            "custom_geometry": 8,
            "animations": 7,
            "animation_controllers": 0,
            "particles": 1,
            "sounds": 12,
            "proof_renders": 104,
            "native_export_equivalence": "PASS_8_OF_8",
        },
    },
    "pocketbound-companions": {
        "classification": "AWAITING_TEST",
        "namespace": "ccr_p08",
        "semantic_version": [1, 0, 2],
        "repository": str(WORKSPACE / "program/crazycraft-production-lanes-v1/pocketbound-companions-v1"),
        "ref": "refs/heads/codex/pocketbound-production-v1",
        "content_commit": "2ab0eba12f93bc0e7d4f1c40f94fb8268e3347fa",
        "content_tree": "2f07723236a6fff4b5859cf2b888b5a4b815f14a",
        "metadata_commit": "96857b6ca1dc80861afd940afa93456abc762bb3",
        "metadata_tree": "6c66a6525e556cfdb61d709d014eb37602ca1178",
        "artifacts": {
            "behavior_pack": {
                "path": str(WORKSPACE / "program/crazycraft-production-lanes-v1/pocketbound-companions-v1/campaigns/pocketbound-companions-v1/production/replacement-candidate/dist/pocketbound-companions-behavior.mcpack"),
                "sha256": "580a9b61e46bbe8cef2a56b7f5bf2936b3d6791651d755dfeb14d4f25d7a245c",
            },
            "resource_pack": {
                "path": str(WORKSPACE / "program/crazycraft-production-lanes-v1/pocketbound-companions-v1/campaigns/pocketbound-companions-v1/production/replacement-candidate/dist/pocketbound-companions-resources.mcpack"),
                "sha256": "88afed9bedbff89197a75c60aca8316e7909f37fd218b47d5198fcc9024cee66",
            },
            "mcaddon": {
                "path": str(WORKSPACE / "program/crazycraft-production-lanes-v1/pocketbound-companions-v1/campaigns/pocketbound-companions-v1/production/replacement-candidate/dist/pocketbound-companions.mcaddon"),
                "sha256": "69f47526337f8a6cb4975de443e7972f7ec9d08d9b9ff8259bce96d3a0dba404",
            },
        },
        "uuids": {
            "behavior_header": "fa3e39f0-f8e2-5467-981c-4474a599ed03",
            "behavior_data_module": "6e561477-fb6b-58a9-bce3-806593c483f8",
            "behavior_script_module": "50893814-1e31-50a5-8563-61354bbbfdc6",
            "resource_header": "7d5521ed-ae7c-517c-8d03-c9e5a08c07e7",
            "resource_resources_module": "e5bf7ac0-385f-5ecc-ba2e-40fc28c632cf",
        },
        "asset_inventory": {
            "authority_state": "PRESERVE_EXISTING",
            "editable_bbmodel_files": 0,
            "textures_png": 14,
            "custom_geometry": 1,
            "animations": 1,
            "animation_controllers": 1,
            "particles": 0,
            "sounds": 0,
            "ui_elements": 0,
            "localization_sets": 1,
            "editable_source_gate": "PENDING_OR_NOT_APPLICABLE_MUST_BE_RESOLVED_BY_ASSET_CLASS",
        },
    },
    "wayfarer-settlements": {
        "classification": "AWAITING_TEST",
        "namespace": "ccr_p01",
        "semantic_version": [1, 0, 0],
        "repository": str(WORKSPACE / "program/crazycraft-production-lanes-v1/wayfarer-settlements-v1"),
        "ref": "refs/heads/main",
        "content_commit": "d3096a8c9f84a651934c336914a97857de9fb8b7",
        "content_tree": "43a961a5f723c02ebb84bf8802d7a77830031d8e",
        "metadata_commit": "a31d1011ffdd7b00e9134cb33ee4a661aa305d1a",
        "metadata_tree": "3db76f8c7978d12f799f7c3af4dab55a1a954500",
        "artifacts": {
            "behavior_pack": {
                "path": str(WORKSPACE / "program/crazycraft-production-lanes-v1/wayfarer-settlements-v1/dist/wayfarer-settlements-bp.mcpack"),
                "sha256": "eb203817f0e0779f620682fda73db39592a567b3b4099f470d896c09ce9c10b9",
            },
            "resource_pack": {
                "path": str(WORKSPACE / "program/crazycraft-production-lanes-v1/wayfarer-settlements-v1/dist/wayfarer-settlements-rp.mcpack"),
                "sha256": "c99266f9e78474924875a74f4e54f0743e658bba26f00ac9ad9dd2a6e4997a39",
            },
            "mcaddon": {
                "path": str(WORKSPACE / "program/crazycraft-production-lanes-v1/wayfarer-settlements-v1/dist/wayfarer-settlements.mcaddon"),
                "sha256": "19c95a2518dd495328fca3095e7aa45d2cf9d499f636799863a7b494bd951bf4",
            },
        },
        "uuids": {
            "behavior_header": "55af1605-c3ef-50f0-809b-396f8fd8d1cb",
            "behavior_data_module": "a9fb520c-a1d0-50d2-a28a-5a20257eb01d",
            "behavior_script_module": "1323921d-ff6b-56d7-8ac3-d411a4e07f87",
            "resource_header": "036b1736-ff46-5be9-ad18-7b16e0bc1d41",
            "resource_resources_module": "4627c46a-7ffc-511d-87a7-e5c3965eae0c",
        },
        "asset_inventory": {
            "authority_state": "PRESERVE_EXISTING",
            "editable_bbmodel_files": 37,
            "textures_png": 714,
            "custom_geometry": 99,
            "animations": 95,
            "animation_controllers": 95,
            "particles": 8,
            "sounds": 12,
            "ui_elements": 0,
            "localization_sets": 12,
        },
    },
}


PACK_BLUEPRINTS = [
    {
        "pack_id": "quietwork",
        "name": "Quietwork",
        "theme": "Concealed construction, subtle controls, and player-owned hidden access.",
        "owner": "PACK-WORKER-01-QUIETWORK",
        "source_paths": ["mods/The SecretRoomsMod.jar"],
        "existing": "quietwork",
        "gameplay": gameplay(
            "Craft subtle building controls, bind them to owned structures, and maintain hidden access without replacing vanilla building.",
            ["basic concealed finishes", "owned control links", "advanced recovery tools"],
            ["finish key", "toggle peg", "pulse stud"],
            ["concealed panels", "seam doors", "seam hatches", "facet screens"],
            [],
            [],
            ["survival recipes with vanilla-reachable inputs"],
            "Owner plus explicitly shared access list.",
            "Versioned owned-block records with bounded reconciliation.",
            "Other players see the same authoritative open/closed and visible/hidden state.",
            "Administrative recovery clears or rebinds orphaned records without deleting unrelated blocks.",
            "Preserve the existing original Quietwork presentation exactly; no unrelated asset reuse.",
        ),
    },
    {
        "pack_id": "catalyst-wilds",
        "name": "Catalyst Wilds",
        "theme": "Large original mutant encounters, rewards, bonds, and recovery.",
        "owner": "PACK-WORKER-02-CATALYST",
        "source_paths": ["mods/Mutant Creatures.jar"],
        "existing": "catalyst-wilds",
        "gameplay": gameplay(
            "Track, challenge, defeat, and bond with bounded original wild catalysts.",
            ["encounter discovery", "boss mastery", "reward crafting", "bonded creature care"],
            ["sigils", "trophies", "crafting materials", "bond tools"],
            [],
            ["original elites", "bosses", "helpers", "projectiles"],
            ["bounded boss and elite encounters"],
            ["server-authoritative reward journal and survival recipes"],
            "Encounter and bonded-creature records are player-scoped and transfer only through explicit product rules.",
            "Versioned encounter, ownership, projectile, reward, and recovery state.",
            "One global boss lease; rewards deduplicate per encounter generation.",
            "Cleanup leases remove adds/projectiles and recover interrupted encounter generations.",
            "Preserve the promoted Catalyst Wilds candidate; closure repairs must not redesign the portfolio.",
        ),
    },
    {
        "pack_id": "shatterwild-foundry",
        "name": "Shatterwild Foundry",
        "theme": "Original creatures, equipment, resources, structures, and staged encounters.",
        "owner": "PACK-WORKER-03-SHATTERWILD",
        "source_paths": [],
        "existing": "shatterwild-foundry",
        "gameplay": gameplay(
            "Explore, gather, craft, encounter, and progress through the existing Shatterwild portfolio.",
            ["resource discovery", "equipment", "ambient and hostile encounters", "elite and boss mastery"],
            ["existing Shatterwild equipment and resources"],
            ["existing Shatterwild world resources"],
            ["existing Shatterwild creature portfolio"],
            ["existing staged encounters"],
            ["existing reachable recipes, loot, and structures"],
            "Existing authority rules remain unchanged.",
            "Existing authority schemas remain unchanged.",
            "Existing server-authoritative ownership and reward behavior remains unchanged.",
            "Only verified defects may alter cleanup or recovery.",
            "Preserve the exact original Shatterwild authority and quality baseline.",
        ),
    },
    {
        "pack_id": "trailbound-packs",
        "name": "Trailbound Packs",
        "theme": "Player-owned expedition storage, specialization, recovery, and cache rewards.",
        "owner": "PACK-WORKER-04-TRAILBOUND",
        "source_paths": ["mods/Adventure Backpack.jar"],
        "existing": "trailbound-packs",
        "gameplay": gameplay(
            "Craft, bind, equip, specialize, upgrade, transfer, and recover expedition packs.",
            ["9-slot tier", "18-slot tier", "27-slot tier", "four specializations"],
            ["eight pack variants", "Trailbound Clasp", "upgrade materials", "Wild Cache"],
            [],
            [],
            ["twelve exact-once cache outcomes"],
            ["survival-reachable crafting and tier upgrades"],
            "One authoritative pack identity and owner with explicit transfer.",
            "Versioned virtual storage, transaction journal, duplicate quarantine, and migration.",
            "Player identity, ownership, and cache rewards remain isolated and exact-once.",
            "Drop, death, reconnect, restart, rollback, quarantine, and administrative recovery remain supported.",
            "Preserve the repaired eight-model Golden/native authority and exact package tuple.",
        ),
    },
    {
        "pack_id": "pocketbound-companions",
        "name": "Pocketbound Companions",
        "theme": "Item-bound companions with care, energy, abilities, ownership, and recovery.",
        "owner": "PACK-WORKER-05-POCKETBOUND",
        "source_paths": ["mods/Inventory Pets.jar"],
        "existing": "pocketbound-companions",
        "gameplay": gameplay(
            "Acquire an original companion token, bond it, sustain its energy, and use passive and active abilities.",
            ["bond", "care", "energy", "three mastery tiers"],
            ["companion tokens", "care items", "upgrade materials"],
            [],
            ["bounded companion representation where required"],
            [],
            ["survival acquisition and progression recipes"],
            "One owner per physical companion identity; explicit transfer and anti-duplication.",
            "Versioned companion, bond, energy, cooldown, and pending-recovery records.",
            "Abilities and rewards are player-scoped and server authoritative.",
            "Lost, duplicated, interrupted, reconnected, and restarted companion states reconcile idempotently.",
            "Preserve the immutable replacement candidate and repair lineage.",
        ),
    },
    {
        "pack_id": "wayfarer-settlements",
        "name": "Wayfarer Settlements",
        "theme": "Original settlement roles, followers, merchants, tasks, and encounter actors.",
        "owner": "PACK-WORKER-06-WAYFARER",
        "source_paths": ["mods/CustomNpcs.jar"],
        "existing": "wayfarer-settlements",
        "gameplay": gameplay(
            "Discover or establish settlements, interact with role-driven residents, complete tasks, and recover persistent relationships.",
            ["settlement reputation", "role access", "task completion", "follower trust"],
            ["role tokens", "task items", "merchant goods"],
            ["settlement workstations"],
            ["guards", "followers", "merchants", "task-givers", "encounter actors"],
            ["bounded settlement defense and task encounters"],
            ["survival acquisition, trades, loot, and reward-journal issuance"],
            "Resident, task, and follower ownership is scoped by settlement and player identity.",
            "Versioned dialogue, role, ownership, task, reward, and recovery state.",
            "Dialogue and rewards isolate players; shared encounters use fenced generations.",
            "Restart, reconnect, death, unload, and administrative recovery preserve bounded state.",
            "Preserve Wayfarer A3; repair only candidate-bound defects.",
        ),
    },
    {
        "pack_id": "reliquary-vaults",
        "name": "Reliquary Vaults",
        "theme": "Crafted relics, equippable effects, and tiered player-owned secure vaults.",
        "owner": "PACK-WORKER-07-RELIQUARY",
        "source_paths": ["mods/Jewelrycraft 2.jar", "mods/Baubles.jar", "mods/Iron Chest.jar"],
        "namespace": "ccr_p13",
        "gameplay": gameplay(
            "Recover relic components, craft bounded relics, equip one through controller-safe use, and secure collections in owned vault tiers.",
            ["common relics", "attuned relics", "masterwork relics", "vault tier upgrades"],
            ["twelve original relics", "relic clasp", "three vault upgrades", "recovery seal"],
            ["three secure vault tiers", "relic workbench"],
            ["two optional cosmetic wisps used only as bounded feedback"],
            ["relic trials with no global boss"],
            ["vanilla-reachable recipes, bounded trial loot, exact-once upgrades"],
            "Relics use physical item identity; vaults have one owner and an explicit trusted-user list.",
            "Versioned vault inventory, relic attunement, transfer, and rollback records.",
            "Concurrent access uses revision fencing; effects and rewards are per-player and exact-once.",
            "Orphaned vaults and interrupted upgrades remain recoverable; feedback entities self-clean.",
            "Original faceted metal, cloth, glass, and carved-stone language with clear tier readability.",
        ),
        "assets": planned_assets(hero=2, reusable=4, routine=6, icons=28, particles=4, sounds=10, bbmodels=12, textures=40, animations=8, controllers=4, ui=2, renders=60),
    },
    {
        "pack_id": "hearth-and-hall",
        "name": "Hearth & Hall",
        "theme": "Original functional furnishings, material families, statuary, and settlement building craft.",
        "owner": "PACK-WORKER-08-HEARTH-HALL",
        "source_paths": [
            "mods/BiblioCraft.jar",
            "mods/Carpenter's Blocks.jar",
            "mods/Chisel 2.jar",
            "mods/Decocraft.jar",
            "mods/MrCrayfish's Furniture Mod.jar",
            "mods/Statues.jar",
        ],
        "namespace": "ccr_p11",
        "gameplay": gameplay(
            "Gather material families, craft coordinated furnishing sets, place functional pieces, and complete themed halls.",
            ["basic utility set", "material families", "decorative sets", "masterwork hall pieces"],
            ["catalog token", "finish samples", "placement tools"],
            ["storage, seating, display, light, shelf, trim, panel, table, statue, and door-adjacent pieces"],
            [],
            [],
            ["survival recipes grouped by obtainable vanilla material families"],
            "Functional storage blocks have one owner or public mode; purely decorative blocks have no ownership record.",
            "Only functional inventories and selections persist; ordinary blocks rely on world state.",
            "Concurrent storage access is revision-fenced; seating and display interactions are server authoritative.",
            "Destroyed functional blocks clear bounded records and return valid inventories according to recovery policy.",
            "Original warm workshop language with restrained voxel detail and readable material separation.",
        ),
        "assets": planned_assets(hero=0, reusable=4, routine=40, icons=24, particles=2, sounds=12, bbmodels=24, textures=96, animations=8, controllers=4, ui=4, renders=80),
    },
    {
        "pack_id": "hearthveil",
        "name": "Hearthveil",
        "theme": "Original ritual craft, transmutation, familiars, travel rites, and bounded occult encounters.",
        "owner": "PACK-WORKER-09-HEARTHVEIL",
        "source_paths": ["mods/Witchery.jar", "mods/Equivalent Exchange 3.jar"],
        "namespace": "ccr_p06",
        "gameplay": gameplay(
            "Gather original reagents, build ritual arrangements, execute server-authoritative rites, raise familiar bonds, unlock travel, and challenge one leased encounter.",
            ["reagents", "ritual craft", "transmutation mastery", "familiar bond", "travel rites", "encounter mastery"],
            ["ritual tools", "reagent set", "transmutation focus", "familiar tokens", "travel sigils", "boss key"],
            ["ritual hearth", "transmutation table", "travel anchor", "reagent plants"],
            ["four familiar archetypes", "three encounter creatures", "one global-boss-lease encounter"],
            ["ritual failures", "familiar trials", "one bounded boss encounter"],
            ["survival reagents, recipes, loot tables, and exactly-once ritual rewards"],
            "Rituals and familiars are player-owned; shared anchors expose explicit access modes.",
            "Versioned ritual, transaction, familiar, travel, encounter, and migration schemas.",
            "Per-player ritual state and reward journals; shared encounters use generation fencing and one boss lease.",
            "Interrupted rituals roll back or quarantine; entities, adds, projectiles, and anchors use bounded cleanup.",
            "Original hearth-smoke, woven bark, ceramic, brass, and moonlit mineral language; no source names or visual copying.",
        ),
        "assets": planned_assets(hero=4, reusable=8, routine=18, icons=48, particles=12, sounds=20, bbmodels=30, textures=120, animations=36, controllers=20, ui=4, renders=180),
    },
    {
        "pack_id": "aspectweave",
        "name": "Aspectweave",
        "theme": "Bedrock-native form attunement, wearable presentation, cosmetic rewards, and displays.",
        "owner": "PACK-WORKER-10-ASPECTWEAVE",
        "source_paths": [
            "mods/Morph.jar",
            "mods/Armourer's Workshop.jar",
            "mods/Hats.jar",
            "mods/HatStand-4.0.0.jar",
            "mods/iChunUtil.jar",
            "mods/AnimationAPI.jar",
        ],
        "namespace": "ccr_p02",
        "gameplay": gameplay(
            "Acquire bounded aspect attunements, switch through a controller-safe selector, reconcile health/effects, and collect original wearable presentation rewards.",
            ["four form families", "attunement mastery", "wearable collection", "display mastery"],
            ["aspect loom", "attunement tokens", "wearable rewards", "display stand"],
            ["aspect display stand"],
            ["bounded visual proxy entities only where Bedrock requires them"],
            ["attunement trials"],
            ["survival acquisition and progression recipes with explicit unlocks"],
            "Forms and wearables are bound to player identity; transfers apply only to physical reward items.",
            "Versioned form, health reconciliation, effect, wearable, and migration state.",
            "Visibility, ability bounds, death, reconnect, and dimension changes remain server authoritative per player.",
            "Invalid forms revert safely; orphaned proxy entities clean within the shared entity budget.",
            "Original woven-energy silhouettes and wearable families; no claim of unsupported arbitrary player-model replacement.",
        ),
        "assets": planned_assets(hero=4, reusable=10, routine=12, icons=36, particles=8, sounds=16, bbmodels=26, textures=100, animations=32, controllers=12, ui=5, renders=160),
    },
    {
        "pack_id": "vanguard-arsenal",
        "name": "Vanguard Arsenal",
        "theme": "Original ability loadouts, melee/ranged combat craft, force tools, and bounded trials.",
        "owner": "PACK-WORKER-11-VANGUARD",
        "source_paths": [
            "mods/Superheroes Mod.jar",
            "mods/Mine & Blade Battlegear 2 - Bullseye.jar",
            "mods/GravityGun.jar",
        ],
        "namespace": "ccr_p04",
        "gameplay": gameplay(
            "Craft one original aspect loadout, charge abilities through play, use bounded melee/ranged/force actions, and master challenge trials.",
            ["six aspect loadouts", "three mastery tiers", "combat tool upgrades", "trial mastery"],
            ["aspect cores", "weapons", "ranged tools", "bounded force tool", "armor set pieces"],
            ["training target", "aspect forge"],
            ["four trial opponents", "one lease-eligible elite"],
            ["combat and mobility trials"],
            ["survival recipes, drops, cooldown-bound rewards"],
            "Abilities are player-entitled and physical tools retain unique item identity.",
            "Versioned loadout, cooldown, projectile, entitlement, and reward state.",
            "Damage, projectiles, rewards, and cooldowns are server authoritative and duplicate-safe.",
            "Stale projectiles, interrupted charge actions, and invalid loadouts clean or roll back within fixed caps.",
            "Original practical arcane-tech armor, bold readable effects, and controller-safe feedback.",
        ),
        "assets": planned_assets(hero=4, reusable=8, routine=10, icons=40, particles=12, sounds=18, bbmodels=22, textures=96, animations=30, controllers=16, ui=5, renders=150),
    },
    {
        "pack_id": "aperture-foundry",
        "name": "Aperture Foundry",
        "theme": "Original shifting machines, paired travel gates, guardian turrets, and mobile waystations.",
        "owner": "PACK-WORKER-12-APERTURE",
        "source_paths": ["mods/Transformers Mod.jar", "mods/PortalGun-4.0.0-beta-4.jar", "mods/Tardis Mod.jar"],
        "namespace": "ccr_p16",
        "gameplay": gameplay(
            "Gather machine parts, assemble modular devices, establish a paired gate route, deploy one owned guardian, and upgrade a mobile waystation.",
            ["machine components", "guardian tier", "paired travel", "waystation upgrades"],
            ["gate tool", "guardian core", "waystation key", "modular machine components"],
            ["paired travel anchors", "waystation shell", "machine workbench"],
            ["one guardian archetype", "one mobile machine proxy when active"],
            ["bounded guardian defense events"],
            ["survival machine recipes and exact-once upgrade transactions"],
            "Devices and travel pairs have one owner plus an explicit access list.",
            "Versioned pair, destination, device, guardian, upgrade, and migration records.",
            "Travel and guardian targeting are server authoritative; each pair and device is isolated by owner/generation.",
            "Unloaded destinations retain bounded pending travel; destroyed or invalid devices reconcile without orphaned entities.",
            "Original folded brass, ceramic lens, field-coil, and modular-frame language; no protected brands or source silhouettes.",
        ),
        "assets": planned_assets(hero=3, reusable=7, routine=12, icons=30, particles=8, sounds=15, bbmodels=22, textures=80, animations=24, controllers=12, ui=4, renders=120),
    },
    {
        "pack_id": "echo-vessels",
        "name": "Echo Vessels",
        "theme": "Creature-echo capture, tiered vessels, controlled summons, and watchbound spectral encounters.",
        "owner": "PACK-WORKER-13-ECHO",
        "source_paths": ["mods/Soul Shards- The Old Ways.jar", "mods/Weeping Angels.jar", "mods/Origin.jar"],
        "namespace": "ccr_p10",
        "gameplay": gameplay(
            "Capture lawful creature echoes, grow vessel tiers, summon within entity caps, and survive original line-of-sight watchbound encounters.",
            ["empty vessel", "echo tiers", "controlled summon mastery", "watchbound encounter mastery"],
            ["vessels", "capture focus", "summon seal", "watch lantern"],
            ["vessel plinth", "watch marker"],
            ["summoned echo archetypes", "three original watchbound entities"],
            ["observation-state encounters and controlled summon challenges"],
            ["survival vessel recipes, capture progression, and bounded rewards"],
            "Vessels and summon records have one owner and explicit transfer; captures cannot duplicate credit.",
            "Versioned capture, tier, summon, encounter, ownership, and recovery state.",
            "Observation and summon state is authoritative per player and dimension; rewards deduplicate by generation.",
            "Entity admissions, unload, restart, death, and corrupt-state recovery are bounded and idempotent.",
            "Original glass-clay vessels and faceless watchbound mineral creatures; no source branding or silhouette transfer.",
        ),
        "assets": planned_assets(hero=3, reusable=7, routine=10, icons=24, particles=8, sounds=16, bbmodels=20, textures=76, animations=26, controllers=12, ui=3, renders=120),
    },
    {
        "pack_id": "bounded-outcome-events",
        "name": "Bounded Outcome Events",
        "theme": "Tiered chance relics with deterministic, capped, recoverable world and reward outcomes.",
        "owner": "PACK-WORKER-14-OUTCOMES",
        "source_paths": ["mods/Pandora's Box.jar", "mods/LuckyBlocks.jar"],
        "namespace": "ccr_p03",
        "gameplay": gameplay(
            "Craft an event reliquary, choose a risk tier, commit one server-authoritative outcome, resolve or recover it, and claim exactly-once rewards.",
            ["four risk tiers", "sixteen original outcome templates", "reliquary mastery"],
            ["four reliquary tiers", "stabilizer", "recovery seal"],
            ["event anchor"],
            ["bounded temporary event entities"],
            ["resource, puzzle, hazard, creature, and reward outcomes"],
            ["survival acquisition, exact-once consumption, exact-once reward journal"],
            "Reliquaries use physical item identity and one initiating owner; shared event rewards use explicit participation rules.",
            "Stable logical operation ID across retries plus separate fenced attempt generation; committed outcomes never rerun.",
            "One event generation is authoritative; callbacks, effects, and rewards deduplicate across reconnect and restart.",
            "Every outcome declares caps, rollback, cleanup deadline, restart recovery, and administrative cancellation.",
            "Original sealed ceramic-and-metal reliquaries with clear risk color language and bounded feedback.",
        ),
        "assets": planned_assets(hero=2, reusable=5, routine=8, icons=32, particles=12, sounds=18, bbmodels=15, textures=64, animations=18, controllers=8, ui=3, renders=90),
    },
    {
        "pack_id": "momentum-menagerie",
        "name": "Momentum Menagerie",
        "theme": "Food-linked movement effects and original roaming creature-event encounters.",
        "owner": "PACK-WORKER-15-MOMENTUM",
        "source_paths": ["mods/Killer Pacman.jar", "mods/TrailMix.jar", "mods/FoodPlus.jar"],
        "namespace": "ccr_p17",
        "gameplay": gameplay(
            "Forage and cook movement foods, use bounded momentum effects, track roaming original creatures, and resolve encounter rewards.",
            ["foraging", "food craft", "movement mastery", "five encounter families"],
            ["food ingredients", "prepared trail foods", "tracker", "encounter trophies"],
            ["forage plants", "cook station"],
            ["five original creature families including one large roaming encounter"],
            ["roaming, harvest-linked, and momentum challenge encounters"],
            ["survival forage, recipes, bounded drops, exact-once encounter rewards"],
            "Effects are player-scoped; encounter ownership is generation-fenced and does not duplicate rewards.",
            "Versioned cooldown, effect, encounter, reward, and cleanup state.",
            "Movement effects never poll inventories; encounters isolate player rewards and shared world entities.",
            "Expired effects, abandoned encounters, projectiles, and temporary terrain feedback clean within fixed deadlines.",
            "Original bright trail provisions and expressive voxel creatures with distinct, non-source silhouettes.",
        ),
        "assets": planned_assets(hero=3, reusable=8, routine=12, icons=28, particles=8, sounds=16, bbmodels=23, textures=84, animations=30, controllers=15, ui=2, renders=140),
    },
    {
        "pack_id": "latchline-infrastructure",
        "name": "Latchline Infrastructure",
        "theme": "Owned access systems, configurable doors, bounded rail dispatch, and secure infrastructure.",
        "owner": "PACK-WORKER-16-LATCHLINE",
        "source_paths": ["mods/Railcraft.jar", "mods/SecurityCraft.jar", "mods/Malisis' Doors.jar", "mods/Malisis' Core.jar"],
        "namespace": "ccr_p14",
        "gameplay": gameplay(
            "Craft access tokens, install owned doors and security devices, connect bounded rail dispatch stations, and recover infrastructure after unload or destruction.",
            ["basic access", "trusted-user control", "security devices", "rail dispatch"],
            ["access token", "recovery tool", "rail route card", "security modules"],
            ["owned doors", "alarm block", "route station", "signal marker", "secure storage"],
            ["bounded utility proxies only where required"],
            ["security alarms and rail dispatch faults, not combat bosses"],
            ["survival recipes and recoverable upgrade transactions"],
            "Every functional device has one owner, explicit trust policy, and admin recovery boundary.",
            "Versioned device, access-list, route, pending cleanup, and migration records.",
            "Access checks and route reservations are server authoritative; concurrent edits use revisions.",
            "Unloaded, blocked, destroyed, stale, and orphaned devices retain bounded cleanup records until reconciled.",
            "Original industrial wood, riveted metal, colored signal glass, and readable access-state feedback.",
        ),
        "assets": planned_assets(hero=1, reusable=6, routine=24, icons=32, particles=4, sounds=12, bbmodels=18, textures=88, animations=12, controllers=6, ui=4, renders=100),
    },
]


BUDGETS = {
    "quietwork": [0, 0, 0, 2, 1, 95, 4, 0, 96, 6144],
    "catalyst-wilds": [10, 6, 5, 4, 1, 295, 16, 1, 384, 24576],
    "shatterwild-foundry": [8, 4, 4, 4, 1, 255, 16, 1, 288, 19456],
    "trailbound-packs": [0, 0, 0, 5, 1, 235, 6, 1, 512, 36864],
    "pocketbound-companions": [2, 0, 0, 3, 1, 195, 6, 1, 352, 22528],
    "wayfarer-settlements": [8, 0, 4, 3, 1, 275, 8, 1, 352, 22528],
    "reliquary-vaults": [2, 1, 0, 3, 1, 155, 6, 1, 192, 12288],
    "hearth-and-hall": [0, 0, 0, 2, 0, 95, 4, 0, 128, 8192],
    "hearthveil": [4, 2, 2, 4, 1, 295, 14, 1, 256, 15360],
    "aspectweave": [0, 0, 0, 4, 1, 255, 8, 1, 256, 15360],
    "vanguard-arsenal": [4, 4, 1, 4, 1, 275, 14, 1, 192, 12288],
    "aperture-foundry": [2, 4, 0, 4, 1, 255, 8, 0, 128, 8192],
    "echo-vessels": [6, 0, 3, 4, 1, 275, 10, 1, 256, 15360],
    "bounded-outcome-events": [4, 4, 1, 4, 1, 275, 14, 1, 192, 11264],
    "momentum-menagerie": [4, 3, 2, 3, 1, 195, 12, 1, 128, 7168],
    "latchline-infrastructure": [0, 0, 0, 3, 0, 175, 4, 0, 128, 8192],
}


def budget_record(values: list[int]) -> dict[str, Any]:
    entities, projectiles, pathfinders, jobs, callbacks, micros, particles, voices, records, prop_bytes = values
    return {
        "combined_reservation_target": {
            "custom_entities": entities,
            "projectiles": projectiles,
            "pathfinders": pathfinders,
            "scheduler_pending": jobs,
            "callbacks_per_heartbeat": callbacks,
            "script_time_microseconds_per_tick": micros,
            "particles_per_second": particles,
            "simultaneous_audio_voices": voices,
            "persistent_records": records,
            "dynamic_property_bytes": prop_bytes,
        },
        "boss_policy": "SHARED_LEASE_ONLY_NO_GUARANTEED_CONCURRENT_BOSS",
        "adds_policy": "SHARED_ADMISSION_CONTROLLER_MAX_8_GLOBAL_MAX_4_PER_ENCOUNTER",
        "standalone_policy": "A pack may use a larger standalone test fixture only when its assignment declares that fixture; combined integration must meet this reservation target or return an integration finding.",
    }


def build() -> None:
    section = json.loads(SECTION_MAP.read_text())
    source_rows = []
    for sec in section["sections"]:
        for source in sec["source_artifacts"]:
            source_rows.append({**source, "section_id": sec["section_id"]})
    observed_paths = [row["path"] for row in source_rows]
    if len(observed_paths) != 52 or len(set(observed_paths)) != 52:
        raise SystemExit("frozen section source map is not exact 52/52")
    if set(observed_paths) != set(SOURCE_RULES):
        missing = sorted(set(observed_paths) - set(SOURCE_RULES))
        extra = sorted(set(SOURCE_RULES) - set(observed_paths))
        raise SystemExit(f"source rule mismatch missing={missing} extra={extra}")

    source_by_path = {row["path"]: row for row in source_rows}
    packs = []
    namespace_seen: set[str] = set()
    uuid_seen: set[str] = set()
    for index, raw in enumerate(PACK_BLUEPRINTS, 1):
        pack = dict(raw)
        existing_key = pack.pop("existing", None)
        if existing_key:
            authority = EXISTING[existing_key]
            pack["existing_authority"] = authority
            namespace = authority["namespace"]
            uuids = authority["uuids"]
            assets = dict(authority["asset_inventory"])
            assets["class_counts"] = EXISTING_ASSET_CLASS_COUNTS[pack["pack_id"]]
            assets["classification_status"] = "PRESERVED_AUTHORITY_FACTORY_WORKLOAD_CLASSIFICATION"
            repository = authority["repository"]
            ref = authority["ref"]
            lifecycle = authority["classification"]
        else:
            namespace = pack.pop("namespace")
            authority_id = f"{pack['pack_id']}-v1"
            uuids = uuid_set(authority_id, namespace)
            assets = pack.pop("assets")
            repository = str(PRODUCTION_ROOT / pack["pack_id"])
            ref = f"refs/heads/codex/{pack['pack_id']}-production-v1"
            lifecycle = "PLANNED_PRODUCTION"
            pack["existing_authority"] = None
        if namespace in namespace_seen:
            raise SystemExit(f"namespace collision: {namespace}")
        namespace_seen.add(namespace)
        for allocated in uuids.values():
            if allocated in uuid_seen:
                raise SystemExit(f"UUID collision: {allocated}")
            uuid_seen.add(allocated)
        pack.update(
            {
                "pack_sequence": index,
                "authority_id": f"{pack['pack_id']}-v1",
                "namespace": namespace,
                "semantic_version": authority["semantic_version"] if existing_key else [1, 0, 0],
                "production_repository": repository,
                "production_ref": ref,
                "asset_authority": {
                    "repository": repository,
                    "ref": ref,
                    "root": "assets/editable",
                    "inventory": assets,
                },
                "uuid_allocations": uuids,
                "lifecycle_classification": lifecycle,
                "shared_runtime_dependencies": [
                    "identity",
                    "persistence",
                    "ownership",
                    "scheduler",
                    "event_router",
                    "reward_journal",
                    "recovery",
                    "diagnostics",
                    "budget_admission",
                    "migration_coordinator",
                ],
                "runtime_budget": budget_record(BUDGETS[pack["pack_id"]]),
                "excluded_source_scope": [
                    "raw Java code or bytecode",
                    "decompiled text",
                    "source identifiers and paths",
                    "source models, textures, UVs, animations, audio, writing, and branding",
                    "private oracle values and hidden cases",
                ],
                "required_outputs": COMMON_REQUIRED_OUTPUTS,
                "completion_condition": COMMON_COMPLETION,
                "run_control": "PAUSED_FACTORY_ORGANIZATION",
            }
        )
        packs.append(pack)

    reconciliation = []
    for sequence, row in enumerate(sorted(source_rows, key=lambda value: value["path"]), 1):
        target, disposition = SOURCE_RULES[row["path"]]
        reconciliation.append(
            {
                "source_sequence": sequence,
                "source_artifact_id": f"CC-SRC-{sequence:03d}",
                "path": row["path"],
                "sha256": row["sha256"],
                "prior_section": row["section_id"],
                "prior_disposition": row["prior_disposition"],
                "final_target": target,
                "final_disposition": disposition,
                "exact_once": True,
            }
        )

    pack_map = {
        "schema_version": "1.0.0",
        "record_type": "crazy_craft_final_pack_map",
        "created_at": CREATED_AT,
        "run_control": "PAUSED",
        "source_authority": {
            "frozen_archive_sha256": section["source_authorities"]["frozen_archive_sha256"],
            "ten_section_map_path": str(SECTION_MAP),
            "ten_section_map_sha256": digest_file(SECTION_MAP),
            "complete_jar_disposition": section["source_authorities"]["complete_jar_disposition"],
            "campaign_registry": section["source_authorities"]["campaign_registry"],
        },
        "pack_count": len(packs),
        "source_artifact_count": len(reconciliation),
        "existing_pack_count": sum(1 for pack in packs if pack["existing_authority"]),
        "new_pack_count": sum(1 for pack in packs if not pack["existing_authority"]),
        "production_unit_rule": "One named coherent Bedrock Add-On pack with one durable owner, production repository, asset authority, deterministic package lifecycle, and mailbox repair loop.",
        "packs": packs,
        "proof_boundary": "Control-plane pack decomposition, allocation, and preserved exact authorities only. No new product implementation, test, audit, qualification, integration, or client proof.",
    }
    write_json(ROOT / "CRAZY_CRAFT_FINAL_PACK_MAP.json", pack_map)

    recon_doc = {
        "schema_version": "1.0.0",
        "record_type": "source_to_pack_reconciliation",
        "created_at": CREATED_AT,
        "source_artifact_count": 52,
        "unique_source_artifact_count": len({row["path"] for row in reconciliation}),
        "mapped_to_pack": sum(1 for row in reconciliation if not row["final_target"].startswith(("shared-platform:", "no-standalone:"))),
        "mapped_to_shared_platform": sum(1 for row in reconciliation if row["final_target"].startswith("shared-platform:")),
        "mapped_to_no_standalone": sum(1 for row in reconciliation if row["final_target"].startswith("no-standalone:")),
        "duplicates": [],
        "unassigned": [],
        "records": reconciliation,
    }
    write_json(ROOT / "CRAZY_CRAFT_SOURCE_TO_PACK_RECONCILIATION.json", recon_doc)

    namespace_registry = {
        "schema_version": "1.0.0",
        "record_type": "factory_namespace_uuid_registry",
        "created_at": CREATED_AT,
        "allocation_authority": "T1_PORTFOLIO_SUPERVISOR",
        "uuid_policy": {
            "algorithm": "UUID_V5",
            "namespace": str(UUID_NAMESPACE),
            "seed": f"{PLATFORM_ID}|<authority_id>|<namespace>|<pack_role>|<major_version>",
            "random_uuid_forbidden": True,
        },
        "supersessions": [
            {"old": "ccr_p05 section-map draft for Vanguard", "new": "ccr_p04", "reason": "Preserve prior global working identity."},
            {"old": "ccr_p14 section-map draft for portal/travel", "new": "ccr_p16", "reason": "Preserve Sentinel/Aperture prior working identity."},
            {"old": "ccr_p12 Harvestkin", "new": "ccr_p17 Momentum Menagerie", "reason": "Consolidated into one creature-event pack."},
            {"old": "ccr_p15 Chancewild Events", "new": "ccr_p03 Bounded Outcome Events", "reason": "Preserve accepted Pandora ownership and avoid duplicate chance products."},
            {"old": "ccr_p09 Wildshift Rules", "new": "shared-platform adaptive-creature-policy", "reason": "No standalone player-facing pack."},
        ],
        "allocations": [
            {
                "pack_id": pack["pack_id"],
                "authority_id": pack["authority_id"],
                "namespace": pack["namespace"],
                "semantic_version": pack["semantic_version"],
                "uuids": pack["uuid_allocations"],
                "status": "PRESERVED_EXISTING" if pack["existing_authority"] else "FACTORY_ALLOCATED_NOT_ACTIVATED",
            }
            for pack in packs
        ],
        "collision_status": "PASS",
    }
    write_json(ROOT / "FACTORY_NAMESPACE_UUID_REGISTRY.json", namespace_registry)

    bootstrap_receipt_path = ROOT / "FACTORY_REPOSITORY_BOOTSTRAP_RECEIPT.json"
    bootstrap_by_pack = {}
    if bootstrap_receipt_path.exists():
        bootstrap_by_pack = {
            row["pack_id"]: row
            for row in json.loads(bootstrap_receipt_path.read_text(encoding="utf-8"))["results"]
        }
    mailbox_receipt_path = ROOT / "SYNTHETIC_MAILBOX_ROUND_TRIP_RECEIPT.json"
    mailbox_receipt = (
        json.loads(mailbox_receipt_path.read_text(encoding="utf-8"))
        if mailbox_receipt_path.exists()
        else None
    )
    route_verification_path = ROOT / "EXISTING_CANDIDATE_DOCKER_BDS_ROUTE_VERIFICATION.json"
    route_verification = (
        json.loads(route_verification_path.read_text(encoding="utf-8"))
        if route_verification_path.exists()
        else None
    )
    mailbox_head = (
        route_verification["mailbox_result"]
        if route_verification
        else (mailbox_receipt["final_authority"] if mailbox_receipt else None)
    )

    repository_registry = {
        "schema_version": "1.0.0",
        "record_type": "factory_repository_allocation_registry",
        "created_at": CREATED_AT,
        "mailbox_repository": {
            "path": str(MAILBOX_REPOSITORY),
            "ref": "refs/heads/codex/factory-mailbox-v1",
            "status": "APPEND_ONLY_FACTORY_MAILBOX_READY" if mailbox_head else "TO_BE_INITIALIZED_BY_ORGANIZATION_MILESTONE",
            "commit": mailbox_head["commit"] if mailbox_head else None,
            "tree": mailbox_head["tree"] if mailbox_head else None,
        },
        "pack_repositories": [
            {
                "pack_id": pack["pack_id"],
                "path": pack["production_repository"],
                "ref": pack["production_ref"],
                "asset_root": pack["asset_authority"]["root"],
                "existing_authority": bool(pack["existing_authority"]),
                "status": (
                    "PRESERVE_EXISTING"
                    if pack["existing_authority"]
                    else (
                        bootstrap_by_pack[pack["pack_id"]]["status"]
                        if pack["pack_id"] in bootstrap_by_pack
                        else "ALLOCATED_FOR_FACTORY_BOOTSTRAP"
                    )
                ),
                "baseline_commit": (
                    pack["existing_authority"].get("artifact_commit", pack["existing_authority"]["content_commit"])
                    if pack["existing_authority"]
                    else bootstrap_by_pack.get(pack["pack_id"], {}).get("commit")
                ),
                "baseline_tree": (
                    (
                        pack["existing_authority"]["metadata_tree"]
                        if pack["existing_authority"].get("artifact_commit")
                        else pack["existing_authority"]["content_tree"]
                    )
                    if pack["existing_authority"]
                    else bootstrap_by_pack.get(pack["pack_id"], {}).get("tree")
                ),
                "independent_git_object_store_required": True,
                "remotes_forbidden_during_private_production": True,
            }
            for pack in packs
        ],
    }
    write_json(ROOT / "FACTORY_REPOSITORY_ALLOCATION_REGISTRY.json", repository_registry)

    ceiling = {
        "custom_entities": 64,
        "projectiles": 32,
        "pathfinders": 24,
        "scheduler_pending": 64,
        "callbacks_per_heartbeat": 16,
        "script_time_microseconds_per_tick": 4000,
        "particles_per_second": 160,
        "simultaneous_audio_voices": 12,
        "persistent_records": 4096,
        "dynamic_property_bytes": 262144,
    }
    platform_reserve = {
        "custom_entities": 10,
        "projectiles": 4,
        "pathfinders": 2,
        "scheduler_pending": 8,
        "callbacks_per_heartbeat": 2,
        "script_time_microseconds_per_tick": 400,
        "particles_per_second": 10,
        "simultaneous_audio_voices": 0,
        "persistent_records": 256,
        "dynamic_property_bytes": 16384,
    }
    combined = {key: 0 for key in ceiling}
    for pack in packs:
        for key, value in pack["runtime_budget"]["combined_reservation_target"].items():
            combined[key] += value
    allocation_check = {
        key: {
            "pack_total": combined[key],
            "platform_reserve": platform_reserve[key],
            "combined": combined[key] + platform_reserve[key],
            "ceiling": ceiling[key],
            "status": "PASS" if combined[key] + platform_reserve[key] <= ceiling[key] else "FAIL",
        }
        for key in ceiling
    }
    budget_registry = {
        "schema_version": "1.0.0",
        "record_type": "factory_runtime_performance_budget_registry",
        "created_at": CREATED_AT,
        "frozen_global_ceilings": ceiling,
        "shared_runtime_safety_reserve": platform_reserve,
        "pack_allocations": {
            pack["pack_id"]: pack["runtime_budget"] for pack in packs
        },
        "combined_target_check": allocation_check,
        "boss_and_adds": {
            "bosses_global": 1,
            "adds_global": 8,
            "policy": "Lease/admission controlled; eligibility is not a simultaneous reservation.",
        },
        "status": "PASS" if all(row["status"] == "PASS" for row in allocation_check.values()) else "FAIL",
        "proof_boundary": "Factory combined-reservation target, not proof that existing standalone implementations already meet these targets. Integration must measure and enforce actual use.",
    }
    write_json(ROOT / "FACTORY_RUNTIME_PERFORMANCE_BUDGET_REGISTRY.json", budget_registry)

    asset_ledger = {
        "schema_version": "1.0.0",
        "record_type": "factory_asset_workload_ledger",
        "created_at": CREATED_AT,
        "packs": [
            {
                "pack_id": pack["pack_id"],
                "name": pack["name"],
                "asset_authority": pack["asset_authority"],
                "production_rules": [
                    "Only source-neutral typed visual contracts enter asset production.",
                    "Original names, silhouettes, proportions, surface language, palettes, motion, audio, and lore are required.",
                    "Custom geometry requires editable source, native reopen/save/export, deterministic normalized equivalence, proof renders, and independent audit.",
                    "Exact packaged PNG/audio/media decode is separate from native source proof.",
                ],
            }
            for pack in packs
        ],
    }
    write_json(ROOT / "FACTORY_ASSET_WORKLOAD_LEDGER.json", asset_ledger)

    # Producer contracts intentionally omit Java source paths, names, hashes,
    # evidence roots, private oracle values, and transformation history.
    contract_hashes: dict[str, str] = {}
    for pack in packs:
        contract = {
            "schema_version": "1.0.0",
            "contract_id": f"PC-{pack['pack_id'].upper().replace('-', '_')}-V1",
            "pack_id": pack["pack_id"],
            "product_name": pack["name"],
            "theme": pack["theme"],
            "namespace": pack["namespace"],
            "gameplay": pack["gameplay"],
            "asset_workload": pack["asset_authority"]["inventory"],
            "technical_allocation": {
                "runtime_budget": pack["runtime_budget"],
                "platform_authority": PLATFORM_AUTHORITY,
                "shared_runtime_dependencies": pack["shared_runtime_dependencies"],
                "uuid_allocations": pack["uuid_allocations"],
                "persistence_schema": f"{pack['namespace']}:state_v1",
                "migration_version": 1,
            },
            "required_outputs": pack["required_outputs"],
            "completion_condition": pack["completion_condition"],
            "clean_room_boundary": {
                "permitted": ["this contract", "approved platform interfaces", "qualified production baseline", "original authored assets and code"],
                "prohibited": pack["excluded_source_scope"],
                "proof_rule": "Every authoring and product-affecting repair process emits a candidate-bound isolation receipt.",
            },
        }
        path = ROOT / "contracts" / f"{pack['pack_id']}.production-contract.json"
        write_json(path, contract)
        contract_hashes[pack["pack_id"]] = digest_file(path)

    map_hash = digest_file(ROOT / "CRAZY_CRAFT_FINAL_PACK_MAP.json")
    ns_hash = digest_file(ROOT / "FACTORY_NAMESPACE_UUID_REGISTRY.json")
    repo_hash = digest_file(ROOT / "FACTORY_REPOSITORY_ALLOCATION_REGISTRY.json")
    budget_hash = digest_file(ROOT / "FACTORY_RUNTIME_PERFORMANCE_BUDGET_REGISTRY.json")
    asset_hash = digest_file(ROOT / "FACTORY_ASSET_WORKLOAD_LEDGER.json")
    for pack in packs:
        assignment = {
            "schema_version": "1.0.0",
            "assignment_type": "DURABLE_PACK_OWNERSHIP",
            "assignment_id": f"PA-{pack['pack_sequence']:02d}-{pack['pack_id'].upper().replace('-', '_')}-V1",
            "pack_id": pack["pack_id"],
            "pack_name": pack["name"],
            "assigned_worker_role": pack["owner"],
            "run_control": "PAUSED_NOT_DISPATCHED",
            "identity": {
                "theme": pack["theme"],
                "namespace": pack["namespace"],
                "bp_header_uuid": pack["uuid_allocations"]["behavior_header"],
                "bp_data_uuid": pack["uuid_allocations"]["behavior_data_module"],
                "script_module_uuid": pack["uuid_allocations"]["behavior_script_module"],
                "rp_header_uuid": pack["uuid_allocations"]["resource_header"],
                "rp_module_uuid": pack["uuid_allocations"]["resource_resources_module"],
                "semantic_version": pack["semantic_version"],
                "production_repository": pack["production_repository"],
                "production_ref": pack["production_ref"],
                "asset_authority": pack["asset_authority"],
            },
            "control_source_responsibility": {
                "visibility": "CONTROL_ONLY_NOT_A_PRODUCTION_INPUT",
                "exact_source_artifacts": [
                    {
                        "source_artifact_id": next(row["source_artifact_id"] for row in reconciliation if row["path"] == path),
                        "path": path,
                        "sha256": source_by_path[path]["sha256"],
                        "final_disposition": SOURCE_RULES[path][1],
                    }
                    for path in pack["source_paths"]
                ],
                "accepted_foundations": ACCEPTED_FOUNDATIONS.get(pack["pack_id"], []),
                "existing_candidate_authority": pack["existing_authority"],
                "excluded_scope": pack["excluded_source_scope"],
            },
            "producer_safe_input": {
                "contract_path": str(ROOT / "contracts" / f"{pack['pack_id']}.production-contract.json"),
                "contract_sha256": contract_hashes[pack["pack_id"]],
                "source_names_paths_hashes_forbidden": True,
            },
            "product_scope": pack["gameplay"],
            "asset_workload": pack["asset_authority"]["inventory"],
            "technical_allocation": {
                "runtime_budget": pack["runtime_budget"],
                "platform_authority": PLATFORM_AUTHORITY,
                "dynamic_property_prefix": f"{pack['namespace']}:",
                "persistence_schema": f"{pack['namespace']}:state_v1",
                "migration_version": 1,
                "shared_runtime_interfaces": pack["shared_runtime_dependencies"],
                "integration_adapter_required": True,
            },
            "required_outputs": pack["required_outputs"],
            "mailbox_contract": {
                "repository": str(MAILBOX_REPOSITORY),
                "candidate_submission": f"candidate_submissions/{pack['pack_id']}/",
                "tester_result": f"tester_results/{pack['pack_id']}/",
                "repair_instruction": f"worker_repairs/{pack['pack_id']}/",
                "integration_intake": f"integration_intake/{pack['pack_id']}/",
                "final_decision": f"final_decisions/{pack['pack_id']}/",
            },
            "worker_mission": "Own this entire Bedrock pack. Build all assigned gameplay, runtime, assets, tests, and deterministic package outputs. Submit immutable candidates through the mailbox. Read tester and repair messages from the mailbox. Correct defects in the production repository and publish new immutable candidates. Continue until T1 registers the pack as accepted and integrated or issues an exact terminal disposition.",
            "internal_subagent_roles": [
                "gameplay_runtime",
                "behavior_pack_content",
                "resource_pack_and_assets",
                "blockbench_when_required",
                "tests",
                "package_validation",
            ],
            "publication_rules": {
                "one_durable_owner": True,
                "subagents_are_not_product_owners": True,
                "frozen_candidates_never_edited": True,
                "new_product_repair_requires_new_generation": True,
                "working_tree_packages_rejected": True,
                "candidate_publication_is_nonterminal": True,
                "tester_wait_is_nonterminal": True,
            },
            "completion_condition": pack["completion_condition"],
            "central_authority_bindings": {
                "pack_map_sha256": map_hash,
                "namespace_uuid_registry_sha256": ns_hash,
                "repository_registry_sha256": repo_hash,
                "runtime_budget_registry_sha256": budget_hash,
                "asset_workload_ledger_sha256": asset_hash,
            },
            "no_ssh_no_studio": {
                "status": "REQUIRED",
                "attempt_is_lane_clean_room_hard_stop": True,
            },
        }
        assignment["assignment_payload_sha256"] = digest_json(assignment)
        write_json(ROOT / "assignments" / f"{pack['pack_id']}.assignment.json", assignment)

    base_message_properties = {
        "schema_version": {"const": "1.0.0"},
        "message_id": {"type": "string", "pattern": "^[A-Z0-9][A-Z0-9._-]{7,127}$"},
        "message_type": {"type": "string"},
        "pack_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{2,63}$"},
        "sender_role": {"type": "string"},
        "recipient_role": {"type": "string"},
        "created_at": {"type": "string"},
        "source_authority_commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
        "source_authority_tree": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
        "candidate_generation": {"type": "integer", "minimum": 0},
        "exact_artifact_hashes": {"type": "object"},
        "parent_message_id": {"type": ["string", "null"]},
        "required_action": {"type": "string"},
        "idempotency_key": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "proof_boundary": {"type": "array", "items": {"type": "string"}},
    }
    base_required = list(base_message_properties)
    base_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://crazycraft.local/factory/mailbox-message.schema.json",
        "title": "Crazy Craft immutable mailbox message",
        "type": "object",
        "required": base_required,
        "properties": base_message_properties,
        "additionalProperties": True,
    }
    write_json(ROOT / "mailboxes" / "schemas" / "mailbox-message.schema.json", base_schema)

    candidate_schema = {
        **base_schema,
        "$id": "https://crazycraft.local/factory/candidate-submission.schema.json",
        "title": "Immutable candidate submission",
        "required": base_required + ["production_commit", "production_tree", "behavior_pack", "resource_pack", "mcaddon", "artifact_manifest", "tests"],
        "properties": {
            **base_message_properties,
            "message_type": {"const": "CANDIDATE_SUBMISSION"},
            "production_commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "production_tree": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "behavior_pack": {"type": ["object", "null"]},
            "resource_pack": {"type": ["object", "null"]},
            "mcaddon": {"type": "object"},
            "artifact_manifest": {"type": "object"},
            "tests": {"type": "object"},
        },
    }
    write_json(ROOT / "mailboxes" / "schemas" / "candidate-submission.schema.json", candidate_schema)

    tester_schema = {
        **base_schema,
        "$id": "https://crazycraft.local/factory/tester-result.schema.json",
        "title": "Immutable consolidated tester result",
        "required": base_required + ["result", "candidate_hash", "findings", "qualification_receipts"],
        "properties": {
            **base_message_properties,
            "message_type": {"enum": ["TEST_PASS", "TEST_FAIL_PRODUCT", "TEST_FAIL_INFRASTRUCTURE", "TEST_BLOCKED_CLIENT", "TEST_BLOCKED_PHYSICAL"]},
            "result": {"type": "string"},
            "candidate_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "findings": {"type": "array"},
            "qualification_receipts": {"type": "array"},
        },
    }
    write_json(ROOT / "mailboxes" / "schemas" / "tester-result.schema.json", tester_schema)

    repair_schema = {
        **base_schema,
        "$id": "https://crazycraft.local/factory/repair-instruction.schema.json",
        "title": "Immutable worker repair instruction",
        "required": base_required + ["failed_candidate_generation", "finding_ids", "allowed_repair_scope", "required_regression_gates"],
        "properties": {
            **base_message_properties,
            "message_type": {"const": "REPAIR_INSTRUCTION"},
            "failed_candidate_generation": {"type": "integer", "minimum": 1},
            "finding_ids": {"type": "array", "items": {"type": "string"}},
            "allowed_repair_scope": {"type": "array", "items": {"type": "string"}},
            "required_regression_gates": {"type": "array", "items": {"type": "string"}},
        },
    }
    write_json(ROOT / "mailboxes" / "schemas" / "repair-instruction.schema.json", repair_schema)

    final_schema = {
        **base_schema,
        "$id": "https://crazycraft.local/factory/accepted-pack-registration.schema.json",
        "title": "Immutable accepted pack registration",
        "required": base_required + ["standalone_authority", "integration_authority", "final_classification"],
        "properties": {
            **base_message_properties,
            "message_type": {"const": "PACK_ACCEPTED_AND_INTEGRATED"},
            "standalone_authority": {"type": "object"},
            "integration_authority": {"type": "object"},
            "final_classification": {"type": "string"},
        },
    }
    write_json(ROOT / "mailboxes" / "schemas" / "accepted-pack-registration.schema.json", final_schema)

    for name in (
        "candidate_submissions",
        "tester_intake",
        "tester_results",
        "worker_repairs",
        "integration_intake",
        "final_decisions",
    ):
        write_text(
            ROOT / "mailboxes" / name / "README.md",
            f"# {name}\n\nAppend-only immutable messages. Consumed state is runtime data and is never written into these message files.",
        )

    tester_assignment = {
        "schema_version": "1.0.0",
        "assignment_type": "PERSISTENT_TESTER_SERVICE",
        "assignment_id": "SA-TESTER-SERVICE-V1",
        "run_control": "PAUSED_NOT_DISPATCHED",
        "owner_role": "PERSISTENT_TESTER_SERVICE",
        "mailbox_repository": str(MAILBOX_REPOSITORY),
        "intake": "tester_intake/",
        "results": "tester_results/",
        "responsibilities": [
            "verify immutable repository commit/tree and exact artifact hashes",
            "run mechanical preflight before substantive services",
            "run deterministic clean rebuild when required",
            "run packaged-media and asset validation",
            "coordinate one private T10 semantic audit per immutable generation",
            "run exact-package Stable BDS",
            "run exact-package Preview BDS when required",
            "run restart, persistence, stress, cleanup, and automated gameplay fixtures",
            "publish one consolidated immutable result",
            "never edit product repositories",
        ],
        "result_types": ["TEST_PASS", "TEST_FAIL_PRODUCT", "TEST_FAIL_INFRASTRUCTURE", "TEST_BLOCKED_CLIENT", "TEST_BLOCKED_PHYSICAL"],
        "container_isolation": {
            "unique_container_name": True,
            "unique_world": True,
            "unique_ports": True,
            "unique_logs": True,
            "unique_output": True,
            "pinned_image_and_bds_version": True,
            "cpu_and_memory_limits": True,
            "evidence_and_oracle_mounts_forbidden": True,
            "product_repository_write_mount_forbidden": True,
        },
        "qualification_claim_boundary": "BDS package load/restart and declared fixtures only; client, audio, controller, Realm, split-screen, physical console, rights, branding, Marketplace, and release remain independent.",
        "completion": "Persistent service has no campaign terminal event; it remains available until T1 closes the factory.",
    }
    tester_assignment["assignment_payload_sha256"] = digest_json(tester_assignment)
    write_json(ROOT / "services" / "PERSISTENT_TESTER_ASSIGNMENT.json", tester_assignment)

    integration_assignment = {
        "schema_version": "1.0.0",
        "assignment_type": "PERSISTENT_SHARED_RUNTIME_INTEGRATION",
        "assignment_id": "SA-SHARED-RUNTIME-INTEGRATION-V1",
        "run_control": "PAUSED_NOT_DISPATCHED",
        "owner_role": "SHARED_RUNTIME_INTEGRATION_WORKER",
        "platform_contract_authority": PLATFORM_AUTHORITY,
        "nested_repository": {
            "path": str(WORKSPACE / "program/crazycraft-autonomous-worker-lanes-v1/thread-02/integration-repo"),
            "ref": "refs/heads/codex/autonomous-m4-semantic-repair",
            "commit": "1230f8c7bb2e7d1699373c60c34f168f5ae66bc8",
            "tree": "3b3a2b38e34f7186cf1169fd0a40a88e03522bfb",
            "classification": "REGISTERED_NESTED_AUTHORITY_NOT_PROMOTED",
        },
        "inputs": ["accepted platform requests", "exact shared-runtime changes", "accepted standalone candidate authorities", "integration failures"],
        "forbidden": ["pack production management", "Java evidence", "private oracle", "product repository edits"],
        "integration_flow": [
            "ingest exact accepted candidate",
            "resolve namespace and UUID collisions",
            "register one mod-local module with shared runtime",
            "resolve dynamic property, scheduler, persistence, migration, recipe, loot, and progression conflicts",
            "build combined package deterministically",
            "run combined BDS qualification",
            "publish combined milestone",
            "route product defects to pack owner and platform defects to this service",
        ],
        "global_budget_registry": str(ROOT / "FACTORY_RUNTIME_PERFORMANCE_BUDGET_REGISTRY.json"),
        "mailboxes": {"intake": "integration_intake/", "results": "tester_results/", "repairs": "worker_repairs/"},
    }
    integration_assignment["assignment_payload_sha256"] = digest_json(integration_assignment)
    write_json(ROOT / "services" / "SHARED_RUNTIME_INTEGRATION_ASSIGNMENT.json", integration_assignment)

    t1_assignment = {
        "schema_version": "1.0.0",
        "assignment_type": "T1_FACTORY_SUPERVISOR",
        "assignment_id": "SA-T1-FACTORY-SUPERVISOR-V1",
        "run_control": "PAUSED_ORGANIZATION_ONLY",
        "owner_role": "T1_PORTFOLIO_SUPERVISOR",
        "responsibilities": [
            "freeze pack map and complete central allocations",
            "issue one durable ownership assignment per pack",
            "monitor immutable mailbox messages",
            "validate candidate authority before tester intake",
            "route consolidated test results",
            "keep repairs with the original pack owner",
            "preserve candidate on infrastructure failure",
            "route accepted candidates to integration",
            "register accepted and integrated pack authorities",
            "replace an exited worker only when the durable pack remains incomplete and no writer collision exists",
        ],
        "forbidden": [
            "author product implementation or assets",
            "split a pack into routine microassignments",
            "repair candidate bytes",
            "count chat prose as authority",
            "turn infrastructure failures into product repairs",
        ],
        "routing": {
            "CANDIDATE_SUBMISSION": "validate then append TESTER_INTAKE",
            "TEST_PASS": "register standalone and append INTEGRATION_INTAKE",
            "TEST_FAIL_PRODUCT": "append one consolidated REPAIR_INSTRUCTION for same owner",
            "TEST_FAIL_INFRASTRUCTURE": "route to tester service owner and preserve candidate",
            "TEST_BLOCKED_CLIENT": "record proof boundary; do not infer failure",
            "TEST_BLOCKED_PHYSICAL": "record external physical gate",
            "PACK_ACCEPTED_AND_INTEGRATED": "append final authority registration",
        },
        "mailbox_repository": str(MAILBOX_REPOSITORY),
        "pack_map_sha256": map_hash,
    }
    t1_assignment["assignment_payload_sha256"] = digest_json(t1_assignment)
    write_json(ROOT / "services" / "T1_SUPERVISOR_MAILBOX_ROUTING_ASSIGNMENT.json", t1_assignment)

    md_lines = [
        "# Crazy Craft fixed Bedrock pack factory",
        "",
        "The frozen ten-section map remains the source-accounting input. The production unit is now one coherent named Bedrock Add-On pack.",
        "",
        f"- Packs: **{len(packs)}**",
        f"- Existing/reference authorities: **{sum(1 for pack in packs if pack['existing_authority'])}**",
        f"- New packs: **{sum(1 for pack in packs if not pack['existing_authority'])}**",
        "- Frozen source artifacts: **52/52 exact-once**",
        "- Run control: **PAUSED**",
        "",
        "## Pack portfolio",
        "",
        "| # | Pack | Namespace | Owner | State | Source responsibility |",
        "|---:|---|---|---|---|---|",
    ]
    for pack in packs:
        sources = ", ".join(Path(value).stem for value in pack["source_paths"]) or "reference authority only"
        md_lines.append(
            f"| {pack['pack_sequence']} | {pack['name']} | `{pack['namespace']}` | `{pack['owner']}` | `{pack['lifecycle_classification']}` | {sources} |"
        )
    md_lines.extend(
        [
            "",
            "## Factory flow",
            "",
            "```text",
            "durable pack owner",
            "→ implementation and original assets",
            "→ immutable candidate submission",
            "→ tester intake",
            "→ mechanical/static/private/BDS/media consolidation",
            "→ one PASS or consolidated repair result",
            "→ same owner replacement generation",
            "→ standalone acceptance",
            "→ incremental shared-runtime integration",
            "→ combined qualification",
            "→ PACK_ACCEPTED_AND_INTEGRATED",
            "```",
            "",
            "No product worker is launched by this organization commit.",
        ]
    )
    write_text(ROOT / "CRAZY_CRAFT_FINAL_PACK_MAP.md", "\n".join(md_lines))


if __name__ == "__main__":
    build()
