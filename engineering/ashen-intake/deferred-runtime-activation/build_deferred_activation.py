#!/usr/bin/env python3
"""Build the deterministic Ashen deferred-runtime-activation receipt."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT_JSON = HERE / "ASHEN_RUNTIME_ACTIVATION_DEFERRED.json"
OUT_MD = HERE / "ASHEN_RUNTIME_ACTIVATION_DEFERRED.md"

SOURCE_COMMIT = "bcd65076900a3688dd797d54719263d88afd501c"
SOURCE_TREE = "4d876b233e6b510687d238f1d7f6611c7c0c4ab9"
STATUS = "ASHEN_VERTICAL_SOURCE_COMPLETE_RUNTIME_ACTIVATION_DEFERRED"
BLOCKER = "MANAGED_REVIEWER_ACTIVATION_BLOCKED"

EVIDENCE = [
    "engineering/validation/wave1/WAVE_1_ASHEN_SOURCE_VALIDATION_PASS.json",
    "engineering/validation/wave1/WAVE_1_ASHEN_IMPLEMENTED_CLOSURE.json",
    "engineering/ashen-intake/equipment-functional/ASHEN_EQUIPMENT_FUNCTIONAL_EVIDENCE.json",
    "engineering/ashen-intake/equipment-functional/ACTIVATION_WITHHELD.md",
    "engineering/ashen-intake/kiln-sky-runtime/KILN_SKY_RUNTIME_EVIDENCE.json",
    "engineering/ashen-intake/kiln-sky-runtime/ACTIVATION_WITHHELD.md",
    "behavior_pack/scripts/ashen_equipment.js",
    "behavior_pack/scripts/ashen_equipment_roles.js",
    "behavior_pack/scripts/kiln_sky.js",
    "behavior_pack/scripts/ashen_rewards.js",
    "behavior_pack/scripts/runtime.js",
    "behavior_pack/scripts/catalog.js",
    "behavior_pack/scripts/state.js",
    "tests/wave1_ashen_equipment_functional.test.mjs",
    "tests/wave1_kiln_sky.test.mjs",
    "tests/wave1_ashen_rewards.test.mjs",
    "tests/wave1_ashen_structure_rewards.test.mjs",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def evidence_rows() -> list[dict[str, object]]:
    rows = []
    for relative in EVIDENCE:
        path = ROOT / relative
        rows.append({"path": relative, "sha256": sha(path), "bytes": path.stat().st_size})
    return rows


def receipt() -> dict[str, object]:
    equipment = json.loads((ROOT / EVIDENCE[2]).read_text())
    kiln = json.loads((ROOT / EVIDENCE[4]).read_text())
    source_validation = json.loads((ROOT / EVIDENCE[0]).read_text())
    runtime = (ROOT / "behavior_pack/scripts/runtime.js").read_text()
    catalog = (ROOT / "behavior_pack/scripts/catalog.js").read_text()

    subprocess.run(["git", "merge-base", "--is-ancestor", SOURCE_COMMIT, "HEAD"], cwd=ROOT, check=True)
    assert git("rev-parse", f"{SOURCE_COMMIT}^{{tree}}") == SOURCE_TREE
    changed_since_authority = git("diff", "--name-only", f"{SOURCE_COMMIT}..HEAD").splitlines()
    assert all(path.startswith("engineering/ashen-intake/deferred-runtime-activation/") for path in changed_since_authority)
    assert source_validation["status"] == "PASS"
    assert equipment["proof"]["shared_runtime_activation"] is False
    assert kiln["proof"]["shared_runtime_activation"] is False
    assert '"aionbound:ash_repeater": "ashen_ranged"' not in catalog
    assert "createAshenEquipmentService" not in runtime
    assert "createKilnSkyService" not in runtime
    assert "ashenEquipment." not in runtime
    assert "kilnSky." not in runtime

    return {
        "schema": "aionforge.wave1.ashen_deferred_runtime_activation.v1",
        "status": STATUS,
        "blocker": BLOCKER,
        "classification": "TOOLING_GOVERNANCE_BLOCKER_NOT_DEMONSTRATED_PRODUCT_DEFECT",
        "source_authority": {
            "commit": SOURCE_COMMIT,
            "tree": SOURCE_TREE,
            "subject": git("show", "-s", "--format=%s", SOURCE_COMMIT),
            "immutable_prior_generation_modified": False,
        },
        "vertical_disposition": {
            "source_complete": True,
            "runtime_complete": False,
            "deferred_only": [
                "Ashen equipment-role composition into existing completed-item, hurt, and 20-tick handlers",
                "Kiln Sky composition into existing reconcile, tick, block-interaction, and death handlers",
            ],
            "other_implemented_and_validated_ashen_work_preserved": True,
            "crystal_marsh_or_skyreach_blocked": False,
        },
        "implemented_services": [
            {
                "module": "behavior_pack/scripts/ashen_equipment.js",
                "factory": "createAshenEquipmentService",
                "exported_service_functions": ["routeMeleeHurt", "useRanged", "armorSet", "handlePlayerHurt", "tickPlayers"],
                "role_data": "behavior_pack/scripts/ashen_equipment_roles.js",
                "evidence_status": equipment["status"],
                "semantics": [
                    "bounded cooldown state in existing player cooldowns map",
                    "Ash Repeater volcanic-glass ammunition consumption and selected-item durability",
                    "bounded damage, fire, weakness, slowness, and particle effects",
                    "Ashen armor-set and Ember Totem fire-resistance roles",
                ],
            },
            {
                "module": "behavior_pack/scripts/kiln_sky.js",
                "factory": "createKilnSkyService",
                "exported_service_functions": ["begin", "tick", "bossDeath", "reconcile", "claimHorn", "recoverHorn", "flushPending", "resolveArena"],
                "reward_module": "behavior_pack/scripts/ashen_rewards.js",
                "reward_factory": "createAshenRewardHooks",
                "evidence_status": kiln["status"],
                "semantics": [
                    "bounded encounter sessions, phases, attacks, participants, resets, and cleanup",
                    "durable terminal completion and once-per-player seal/horn entitlement",
                    "offline/restart pending-credit and horn recovery",
                    "post-clear participant materials and guarded Ember Forge cache population",
                ],
            },
        ],
        "dormant_connections": [
            {
                "target": "behavior_pack/scripts/catalog.js::COMPLETED_ITEM_ROUTES",
                "intended": "route aionbound:ash_repeater to ashen_ranged",
                "observed": "ABSENT",
            },
            {
                "target": "behavior_pack/scripts/runtime.js::itemActions",
                "intended": "ashen_ranged calls only ashenEquipment.useRanged",
                "observed": "ABSENT",
            },
            {
                "target": "behavior_pack/scripts/runtime.js::existing entityHurt subscriber",
                "intended": "compose routeMeleeHurt and handlePlayerHurt without early return",
                "observed": "ABSENT",
            },
            {
                "target": "behavior_pack/scripts/runtime.js::existing 20-tick player cadence",
                "intended": "compose ashenEquipment.tickPlayers beside combat.tickPlayers",
                "observed": "ABSENT",
            },
            {
                "target": "behavior_pack/scripts/runtime.js::reconcile and existing tick callback",
                "intended": "compose kilnSky.reconcile and kilnSky.tick",
                "observed": "ABSENT",
            },
            {
                "target": "behavior_pack/scripts/runtime.js::existing synchronous/deferred block-interaction paths",
                "intended": "make durable Kiln completion authoritative for overlapping Ember Forge cache guards, retain synchronous pre-clear lock, recover pending horn entitlement before any begin path",
                "observed": "ABSENT",
            },
            {
                "target": "behavior_pack/scripts/runtime.js::existing entityDie subscriber",
                "intended": "compose kilnSky.bossDeath beside thornCourt.bossDeath",
                "observed": "ABSENT",
            },
            {
                "target": "behavior_pack/scripts/runtime.js::return object",
                "intended": "expose ashenEquipment and kilnSky for semantic testing",
                "observed": "ABSENT",
            },
        ],
        "mutation_surfaces_if_later_activated": {
            "existing_player_state": [
                "cooldowns: ashen:weapon:<itemType> and ashen:accessory:ember_totem",
                "credits: aionbound.player.kiln_sky.seal_credit.v1",
                "credits: aionbound.player.kiln_sky.reward_entitled.v1",
                "credits: aionbound.player.kiln_sky.trophy_claimed.v1",
            ],
            "existing_world_state": [
                "encounters.terminal[aionbound.encounter.kiln_sky.completed.v1]",
                "encounters.pendingKilnSky[playerId]",
            ],
            "inventory_and_item": [
                "consume one aionbound:volcanic_glass_shard per successful Ash Repeater shot",
                "damage selected Ash Repeater durability by one",
                "deliver aionbound:ash_drake_horn only after durable entitlement and available inventory capacity",
                "populate exact Ember Forge cache only after authoritative completion",
            ],
            "runtime_only": ["Kiln Sky in-memory sessions", "Ashen reward-hook opened-cache guard set"],
            "new_persistence_domain_or_schema": False,
        },
        "reviewer_rejection_history": {
            "historical_activation_attempt_refs": [
                {"ref": "codex/ashen-shared-activation", "commit": SOURCE_COMMIT},
                {"ref": "codex/ashen-shared-activation-r2", "commit": SOURCE_COMMIT},
                {"ref": "codex/ashen-shared-activation-r3", "commit": SOURCE_COMMIT},
            ],
            "standing_authority_attempt_refs": [
                {"ref": "codex/wave1-runtime-activation-authority", "commit": SOURCE_COMMIT},
                {"ref": "codex/wave1-review-and-proceed-authority", "commit": SOURCE_COMMIT},
            ],
            "observed_result": "NO_ACTIVATION_OR_AUTHORITY_COMMIT_LANDED; ALL_REFS_REMAIN_AT_SOURCE_AUTHORITY",
            "reported_reasons": [
                "broad persistent shared-runtime mutation",
                "governance-scope expansion",
                "trusted direct user approval absent or conveyed only through subagent payload",
            ],
            "decision_source_attribution": "PARTIAL_NOT_DECISIVELY_OBSERVABLE",
            "external_diagnostics": [
                {
                    "path": "/Users/blakegrove/Desktop/bedrock-server/REVIEWER_POLICY_AUDIT.md",
                    "sha256": "8b3cdcc88e2097e6bd93822a459563466005a31104d0b333264fe180258294ab",
                },
                {
                    "path": "/Users/blakegrove/Desktop/bedrock-server/REVIEWER_DECISION_SOURCE_AUDIT.md",
                    "sha256": "b773003424b2f018517244110b946aa7b2466b4630f8ce6a04918b87fccd2166",
                },
            ],
        },
        "passed_evidence": {
            "source_validation_status": source_validation["status"],
            "source_validation_checks": source_validation["checks"],
            "equipment_proof": equipment["proof"],
            "kiln_sky_proof": kiln["proof"],
            "focused_tests_to_replay_for_ticket_validation": [
                "node --test tests/wave1_ashen_equipment_functional.test.mjs",
                "node --test tests/wave1_kiln_sky.test.mjs tests/wave1_ashen_rewards.test.mjs tests/wave1_ashen_structure_rewards.test.mjs",
                "python3 engineering/ashen-intake/equipment-functional/test_ashen_equipment_evidence.py",
            ],
            "focused_validation_observed_2026_08_11": [
                {
                    "scope": "equipment, Kiln Sky, Ashen rewards, and Ashen structure-reward semantics",
                    "command": "node --test tests/wave1_ashen_equipment_functional.test.mjs tests/wave1_kiln_sky.test.mjs tests/wave1_ashen_rewards.test.mjs tests/wave1_ashen_structure_rewards.test.mjs",
                    "passed": 30,
                    "failed": 0,
                },
                {
                    "scope": "existing functional-equipment evidence closure",
                    "command": "python3 engineering/ashen-intake/equipment-functional/test_ashen_equipment_evidence.py",
                    "passed": 2,
                    "failed": 0,
                },
                {
                    "scope": "new deferred-ticket exactness, hash closure, dormancy, determinism, and final reconciliation",
                    "command": "python3 engineering/ashen-intake/deferred-runtime-activation/test_deferred_activation.py",
                    "passed": 6,
                    "failed": 0,
                },
            ],
        },
        "reconciliation_debt": {
            "id": "W1-G8-KILN-SKY-CHECKED-IN-EVIDENCE-STALE",
            "classification": "STALE_DETERMINISTIC_RECEIPT_AFTER_LATER_INTEGRATION_MOVEMENT_NOT_SERVICE_SEMANTIC_FAILURE",
            "command": "python3 engineering/ashen-intake/kiln-sky-runtime/test_kiln_sky_runtime_evidence.py",
            "observed_2026_08_11": {"tests": 2, "passed": 1, "failed": 1},
            "passing_surface": "activation-absent/source-boundary test",
            "failing_surface": "checked-in evidence equals deterministic rebuild",
            "exact_mismatch": {
                "path": "behavior_pack/scripts/state.js",
                "checked_in_receipt_sha256": "b6d5691adf70396effdb48bce08dbaa4a4ec7b63a3cdffe04b83d5108457827f",
                "current_source_sha256": "69eb00df9ce2f16dcca9794a61c4fcaf9403512f8057ecd4907b6a8f8375b7cd",
            },
            "disposition": "RECONCILE_RECEIPT_IN_LATER_INTEGRATION_PASS; DO_NOT_EDIT_PRIOR_EVIDENCE_IN_THIS_TICKET",
            "product_defect_demonstrated": False,
        },
        "deferred_integration_ticket": {
            "id": "W1-G8-ASHEN-SHARED-RUNTIME-ACTIVATION-DEFERRED",
            "design_decisions_required": False,
            "scope": "ONLY_THE_TWO_DORMANT_COMPOSITIONS_LISTED_IN_THIS_RECEIPT",
            "acceptance_criteria": [
                "Import and instantiate exactly one Ashen equipment service and one Kiln Sky service using existing dependencies.",
                "Use only existing completed-item, hurt, 20-tick, reconcile, tick, block-interaction, and death paths; add no subscription or interval class.",
                "Preserve current balance, persistence schema, ownership, encounter, reward, duplicate, replay, and recovery semantics.",
                "Make durable Kiln completion authoritative for overlapping Ember Forge cache guards while retaining synchronous pre-clear locking.",
                "When a horn-entitled player has full inventory, remain in recovery and do not fall through into a new encounter.",
                "Pass targeted shared-handler semantic tests, prove no duplicate subscription/double dispatch, and prove bounded/idempotent persistent mutations where designed.",
                "Run no BDS solely for activation; final integrated qualification remains separately gated.",
            ],
            "final_candidate_rule": "MUST_RECONCILE_BEFORE_IMMUTABLE_WAVE_1_CANDIDATE; ACTIVATE_NORMALLY_OR_EXPLICITLY_REVISE_PRODUCT_CONTRACT; DO_NOT_SHIP_DORMANT_SILENTLY",
        },
        "proof_boundary": {
            "bds": False,
            "package": False,
            "client": False,
            "shared_runtime_activation": False,
            "runtime_complete": False,
            "product_defect_demonstrated": False,
            "tooling_governance_blocker_recorded": True,
        },
        "evidence": evidence_rows(),
    }


def markdown(data: dict[str, object]) -> str:
    dormant = "\n".join(f"{i}. `{row['target']}` — {row['intended']} (`{row['observed']}`)." for i, row in enumerate(data["dormant_connections"], 1))
    criteria = "\n".join(f"- {item}" for item in data["deferred_integration_ticket"]["acceptance_criteria"])
    tests = "\n".join(f"- `{item}`" for item in data["passed_evidence"]["focused_tests_to_replay_for_ticket_validation"])
    return f"""# Ashen deferred shared-runtime activation

Status: `{STATUS}`  
Blocker: `{BLOCKER}`  
Classification: tooling/governance blocker, not a demonstrated Ashen product defect

## Exact source authority

- Commit: `{SOURCE_COMMIT}`
- Tree: `{SOURCE_TREE}`
- Subject: `{data['source_authority']['subject']}`
- G7 and prior immutable generations modified: no

This receipt preserves the clean G8 source authority unchanged. Ashen is source-complete but is **not** fully runtime-complete.

## Deferred scope only

1. Ashen equipment-role composition into the existing completed-item, hurt, and 20-tick live handlers.
2. Kiln Sky composition into the existing reconcile, tick, block-interaction, and death live handlers.

All other Ashen work already implemented and validated outside those two compositions remains valid engineering work. This ticket does not block Crystal Marsh or Skyreach source development.

## Implemented services

- `behavior_pack/scripts/ashen_equipment.js::createAshenEquipmentService` implements `routeMeleeHurt`, `useRanged`, `armorSet`, `handlePlayerHurt`, and `tickPlayers` against the ratified role data.
- `behavior_pack/scripts/kiln_sky.js::createKilnSkyService` implements `begin`, `tick`, `bossDeath`, `reconcile`, `claimHorn`, `recoverHorn`, `flushPending`, and `resolveArena`.
- `behavior_pack/scripts/ashen_rewards.js::createAshenRewardHooks` implements horn delivery, participant materials, guarded cache population, and the synchronous cache guard.

## Dormant shared connections

{dormant}

## Existing persistence/cache surfaces

No new persistence schema is required. Later activation is bounded to existing player `cooldowns` and `credits`, existing world `encounters.terminal` and `encounters.pendingKilnSky`, selected-item ammunition/durability mutation, the in-memory encounter session map, and the in-memory opened-cache guard.

The exact durable keys are recorded in the JSON twin. A full-inventory horn-entitled player must remain on the recovery path and must not fall through into a new encounter.

## Passed evidence and proof boundary

The bound source receipt reports `PASS` for its source/mechanical checks. Dedicated equipment semantics, declarative item components, Kiln Sky source-semantic tests, and state migration are proven by their existing receipts. Shared runtime activation is explicitly false in both dedicated receipts.

Focused tests bound to this ticket:

{tests}

No BDS, package, client, or live shared-runtime proof is claimed for the dormant compositions.

## Known receipt reconciliation debt

`engineering/ashen-intake/kiln-sky-runtime/test_kiln_sky_runtime_evidence.py` currently runs two checks: the activation-absent/source-boundary check passes, while the checked-in deterministic evidence comparison fails because the receipt binds the earlier `state.js` hash `b6d569...` and the integrated source now hashes to `69eb00...`. The dedicated service semantics remain 30/30 PASS in the focused Node run. This is recorded as stale receipt debt after later integration movement, not as a Kiln Sky semantic failure or a demonstrated product defect. The prior evidence is intentionally untouched here.

## Reviewer rejection history

The exact refs `codex/ashen-shared-activation`, `-r2`, and `-r3`, plus the two standing-authority refs, all remained at `{SOURCE_COMMIT}`. No activation or authority commit landed. Historical reviewer reports described the requested work as a broad persistent shared-runtime mutation or governance-scope expansion and did not accept delegated authority as trusted direct approval. The separate decision-source audit classified decisive attribution as partial; this receipt therefore records the blocker without claiming which hidden component authored the denial.

## Deferred integration ticket

Ticket: `W1-G8-ASHEN-SHARED-RUNTIME-ACTIVATION-DEFERRED`

No new Creative or gameplay-design decision is required. Acceptance criteria:

{criteria}

Before the final immutable Wave 1 candidate, this ticket must either activate normally or the product contract must be explicitly revised. Dormant gameplay must not ship silently.
"""


def main() -> None:
    data = receipt()
    OUT_JSON.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(markdown(data))


if __name__ == "__main__":
    main()
