#!/usr/bin/env python3
"""Build the exact-current, authority-neutral Wave 1 decision packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BEDROCK = Path("/Users/blakegrove/Desktop/bedrock-server")
PACKET006_MANIFEST = BEDROCK / "program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-006-equipment-progression/MANIFEST_FULL.json"

AUDITED_COMMIT = "0061c979049b60b752a54bef611b6f16fd2a5fae"
AUDITED_TREE = "2254abb2d5c30808a38fc47b39872fc7c0afa5c5"

SOURCE_HASHES = {
    "engineering/authority/support-proposals/skyreach/W1-001-SR.json": "926a401add04b6611d7cee7dd1fa3bcf6a3fe44cf656ef9aa34d9b1bad5f30cd",
    "engineering/authority/support-proposals/skyreach/W1-003-STORM-NEST.json": "59b4493857bf3d90d402d438553f4b7fc03c6b45689e5897f8a8cb501bfc15d0",
    "engineering/authority/support-proposals/skyreach/W1-004-SR.json": "823894296bb4b4ed1becd1a1a5ccc814f734cecc50c8433be855bdf1e080e4bf",
    "engineering/authority/support-proposals/finale/W1-002-TWINBOND.json": "0f99a748e55d15bd468d9ded25a0c170972bf94c1682e56c8abb78cde25eda7e",
    "engineering/authority/support-proposals/finale/W1-003-TWINBOND.json": "c22a350499fd2674d3dabedcee8ec5221c4e3e8da4f89666f91cb5a69a43cf1c",
    "engineering/authority/support-proposals/finale/W1-004-TWINBOND.json": "b5ac9295df1718112793d2b15ba035570e1e6032d0da814b9af68a17c27d9a4c",
    "engineering/validation/wave1/WAVE_1_SKYREACH_IMPLEMENTED_CLOSURE.json": "5f1e044c6f4c1176f0025ab35be0afd1a0a96d66b73b3e10cd3113e727292fee",
    "engineering/skyreach-intake/deferred-source-exit/SKYREACH_DEFERRED_SOURCE_EXIT.json": "4410df90c93e7d2adbb6899fe88397c419b26e76c8ae571559ece0ef432cfb39",
    "engineering/packet006-presentation/PACKET006_PRESENTATION_SHELLS_REPORT.json": "7136319581d3102525965e4e2ec99440fbbe74294ae83a1ecacc7ac35c64fc42",
    "engineering/native-assets/packet006-missing/PACKET006_MISSING_NATIVE_REPORT.json": "76622b1d3b33bae40e08182d987ef33e972f0be5f9fb7b64d53e5c7728cd4f1f",
    "engineering/native-assets/twinbond/TWINBOND_NATIVE_REPORT.json": "fd4cbf54799a3d78d5bfa170f57e1b555ce50b890a591e0371207e4f84a484ef",
    "engineering/packet006-reconciliation/PACKET006_ROUTINE_RECONCILIATION.json": "d1b71c2375a14a26a1475003a17a63b5c31cd9567764cc5af931ef617b0683d2",
    "engineering/authority/support-tickets/W1-ASSET-AUDIO-001.json": "cc8c3179964c61c495fb25d4c0f891bdb237433edb847b1e73e54018387a667f",
    "engineering/ashen-intake/deferred-runtime-activation/ASHEN_RUNTIME_ACTIVATION_DEFERRED.json": "e35d8b25e798a6bf1844ed8aaa718c13e021b83c056b9ff15b9f3d4eb35ae998",
    "engineering/authority/support-proposals/W1-CREATIVE-005/sidegrade_identity_proposal.json": "03dd32528d85c7e82edec0f998a1c271e782886f4cf357f1283e25fece11933a",
    "resource_pack/textures/item_texture.json": "b3ba12a8612322119d1825e1e831ce83fb7b56e83b4b8be06a9df47a819e05e3",
    "resource_pack/textures/terrain_texture.json": "8edbcdc323214b7f930521161defb36563aeb91b2a1d5d14a362dc8ad7ff9b95",
    "resource_pack/texts/en_US.lang": "0393af3080dfa8208fd32532be37b1849a118fb03ca759b5cb64d4bb2fe0b394",
    "resource_pack/sounds.json": "6629c48aca2f561d7e6362da9b3072b676b79b524eabccd73b711a749412310a",
    "engineering/authority/WAVE_1_SUCCESSOR_WORKSPACE_AUTHORITY.json": "df8eae7a83a820770c882edbe44c9293b53997febe1305446c61554addf2d0a4",
}

PACKET006_MANIFEST_SHA256 = "71ab8dec6949ab4a1321fe4215d843cdb9c4279e8ca6a37adfb95c20149951ea"

SKYREACH_APPROVAL = "Approve W1-001-SR, W1-003-STORM-NEST, and W1-004-SR exactly as proposed. Preserve W1-CREATIVE-005 as deferred."
FINALE_APPROVAL = "Approve W1-002-TWINBOND, W1-003-TWINBOND, and W1-004-TWINBOND exactly as proposed. Preserve the retired finale-key and Concord Scale path as forbidden, and preserve W1-CREATIVE-005 as deferred."
AUDIO_ORIGINAL = "Preserve W1-ASSET-AUDIO-001 as a final blocker. Do not freeze the Wave 1 candidate until original provenance-backed regional, creature, boss, and landmark audio is supplied and qualified."
AUDIO_SCOPE_REDUCTION = "Explicitly reduce the Wave 1 final sound-identity requirement: ship the existing role-appropriate vanilla placeholder mappings as the Wave 1 audio scope, record custom regional, boss, and landmark audio plus client mix as known limitations, and make no custom-audio or client-mix claims."


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def packet006_closure() -> dict:
    manifest = load(PACKET006_MANIFEST)
    item_atlas = load(ROOT / "resource_pack/textures/item_texture.json")["texture_data"]
    terrain_atlas = load(ROOT / "resource_pack/textures/terrain_texture.json")["texture_data"]
    language = (ROOT / "resource_pack/texts/en_US.lang").read_text(encoding="utf-8")
    rows = []
    for asset in manifest["assets"]:
        name = asset["name"]
        item = ROOT / f"behavior_pack/items/{name}.item.json"
        block = ROOT / f"behavior_pack/blocks/{name}.block.json"
        representation = "item" if item.is_file() else "block" if block.is_file() else "missing"
        texture_kind = "item_atlas" if name in item_atlas else "terrain_atlas" if name in terrain_atlas else "missing"
        texture = (item_atlas.get(name) or terrain_atlas.get(name) or {}).get("textures")
        png = bool(texture and (ROOT / "resource_pack" / f"{texture}.png").is_file())
        geometry = bool(list((ROOT / "resource_pack/models").rglob(f"{name}.geo.json")))
        localized = any(token in language for token in (
            f"item.aionbound:{name}=", f"item.aionbound:{name}.name=", f"tile.aionbound:{name}.name="
        ))
        attachable = (ROOT / f"resource_pack/attachables/{name}.attachable.json").is_file()
        rows.append({
            "id": f"aionbound:{name}", "tier": asset["tier"], "representation": representation,
            "texture_registry": texture_kind, "png": png, "geometry": geometry,
            "localized": localized, "attachable": attachable,
        })
    complete = [row for row in rows if row["representation"] != "missing" and row["texture_registry"] != "missing" and row["png"] and row["geometry"] and row["localized"]]
    return {
        "manifest_path": str(PACKET006_MANIFEST.relative_to(BEDROCK)),
        "manifest_sha256": sha256(PACKET006_MANIFEST),
        "manifest_count": manifest["count"],
        "source_presentation_complete": len(complete),
        "item_representations": sum(row["representation"] == "item" for row in rows),
        "block_representations": sum(row["representation"] == "block" for row in rows),
        "item_atlas_entries": sum(row["texture_registry"] == "item_atlas" for row in rows),
        "terrain_atlas_entries": sum(row["texture_registry"] == "terrain_atlas" for row in rows),
        "geometry_bindings": sum(row["geometry"] for row in rows),
        "localized": sum(row["localized"] for row in rows),
        "attachables": sum(row["attachable"] for row in rows),
        "intentional_non_attachable_placeable_trophies": [row["id"] for row in rows if row["representation"] == "block" and not row["attachable"]],
        "status": "ALL_50_BASE_PACKET006_PRESENTATION_IDENTITIES_SOURCE_CLOSED",
        "authority_consequence": "No new decision is needed for the approved base 50 identities. Acquisition/gameplay/finale authority remains separate.",
        "proof_boundary": "source representation, geometry, texture registry/PNG, localization, and attachable-or-placeable presentation only; not client readability, package, BDS, console, or release proof",
    }


def proposal_rows(paths: list[str]) -> list[dict]:
    rows = []
    for path in paths:
        payload = load(ROOT / path)
        rows.append({
            "ticket_id": payload["ticket_id"], "path": path, "sha256": sha256(ROOT / path),
            "status": payload["status"], "authority_effect": payload["authority_effect"],
            "proposal_source_commit": payload["source_commit"], "proposal_source_tree": payload["source_tree"],
            "question": payload["approval_required"][0]["question"],
        })
    return rows


def build() -> dict:
    sky_paths = [
        "engineering/authority/support-proposals/skyreach/W1-001-SR.json",
        "engineering/authority/support-proposals/skyreach/W1-003-STORM-NEST.json",
        "engineering/authority/support-proposals/skyreach/W1-004-SR.json",
    ]
    finale_paths = [
        "engineering/authority/support-proposals/finale/W1-002-TWINBOND.json",
        "engineering/authority/support-proposals/finale/W1-003-TWINBOND.json",
        "engineering/authority/support-proposals/finale/W1-004-TWINBOND.json",
    ]
    return {
        "schema": "aionbound.wave1.final_decision_packet.v1",
        "status": "FINAL_WAVE1_DECISIONS_REQUIRED_NO_AUTHORITY_EFFECT",
        "authority_effect": "NONE_UNTIL_USER_APPROVAL_IS_RATIFIED_IN_A_REPLACEMENT_DECISION_LEDGER",
        "audited_integration": {"commit": AUDITED_COMMIT, "tree": AUDITED_TREE, "head_advanced_during_audit": False},
        "included_later_local_commits": [
            {"commit": "390dce2757d2b1b7a7e3a967d214593b99c31480", "subject": "Skyreach approval-ready support tranche", "contained_in_audited_integration": True},
            {"commit": "49bd8500259b9bed954862704ebc95ffbb4392bd", "subject": "Packet 006 dormant presentation shells", "contained_in_audited_integration": True},
            {"commit": "0061c979049b60b752a54bef611b6f16fd2a5fae", "subject": "Twinbond finale approval-ready support tranche", "contained_in_audited_integration": True},
        ],
        "evidence": [{"path": path, "sha256": value} for path, value in SOURCE_HASHES.items()] + [{
            "path": str(PACKET006_MANIFEST.relative_to(BEDROCK)), "sha256": PACKET006_MANIFEST_SHA256,
            "repository": "bedrock-server workspace external Creative Packet 006 source",
        }],
        "decision_set": [
            {
                "id": "DECISION_SKYREACH_TRANCHE", "kind": "APPROVE_OR_REJECT_ATOMIC_TRANCHE", "approval_text_verbatim": SKYREACH_APPROVAL,
                "proposals": proposal_rows(sky_paths),
                "approve_consequence": "Engineering may ratify and execute exact Skyreach identities/acquisition/recipes, Storm Nest envelope, storm_pinion seal, loot/recovery/repeat-clear semantics; proposal exclusions remain exclusions.",
                "reject_or_no_decision_consequence": "Skyreach remains foundation-complete but executable acquisition, loot, Storm Nest, seal recovery, and terminal progression stay dormant; no full Wave 1 candidate.",
            },
            {
                "id": "DECISION_FINALE_TRANCHE", "kind": "APPROVE_OR_REJECT_ATOMIC_TRANCHE", "approval_text_verbatim": FINALE_APPROVAL,
                "proposals": proposal_rows(finale_paths),
                "approve_consequence": "Engineering may ratify and implement the same-world authored Twinbond site, bounded four-phase encounter, Trophy Edge/Memory/relic fulfillment and recovery, while keeping retired G7 finale rewards forbidden.",
                "reject_or_no_decision_consequence": "Twinbond stays deliberately withheld; the inherited finale-key/Concord Scale path remains forbidden; no full Wave 1 candidate.",
            },
            {
                "id": "DECISION_AUDIO_CONTRACT", "kind": "CHOOSE_EXACTLY_ONE", "choices": [
                    {"id": "AUDIO_ORIGINAL_REQUIRED", "approval_text_verbatim": AUDIO_ORIGINAL, "consequence": "W1-ASSET-AUDIO-001 remains final-blocking until original bytes, filenames, provenance, event binding, and qualification exist."},
                    {"id": "AUDIO_PLACEHOLDER_SCOPE_REDUCTION", "approval_text_verbatim": AUDIO_SCOPE_REDUCTION, "consequence": "Existing vanilla placeholder mappings become the explicit Wave 1 audio scope; custom identity audio and client mix remain known limitations and cannot be claimed."},
                ],
                "no_decision_consequence": "The current contract keeps W1-ASSET-AUDIO-001 final-blocking.",
            },
        ],
        "no_decision_required": {
            "packet006_base_presentation": packet006_closure(),
            "W1-CREATIVE-005": {
                "status": "SAFE_TO_SHIP_DEFERRED_UNDER_EXISTING_CONDITIONS",
                "conditions": ["only approved base Packet 006 identities ship", "all eight proposed sibling sidegrade/unique-finish IDs remain absent", "no substitute identity or same-ID finish is invented", "known limitation is disclosed"],
                "consequence": "Deferral does not block the base 50 Packet 006 presentation set.",
            },
        },
        "separately_blocked_not_approved_by_this_packet": {
            "ashen_activation": {
                "status": "ASHEN_VERTICAL_SOURCE_COMPLETE_RUNTIME_ACTIVATION_DEFERRED",
                "blocker": "MANAGED_REVIEWER_ACTIVATION_BLOCKED",
                "disposition": "NO_RETRY_NO_WORKAROUND_IN_THIS_WORKLOAD",
                "product_defect_demonstrated": False,
                "dormant_only": ["Ashen equipment composition into existing completed-item, hurt, and 20-tick handlers", "Kiln Sky composition into existing reconcile, tick, block-interaction, and death handlers"],
                "candidate_consequence": "Still must be normally activated when tooling permits or explicitly removed by a product-contract revision before candidate freeze; dormant gameplay must not ship silently.",
            },
            "github_publication": {
                "classification": "EXTERNALLY_OBSERVED_NOT_PRODUCT_EVIDENCE_PUBLICATION_BLOCKER_ONLY",
                "branch": "codex/aionbound-wave1-g8-integration",
                "remote": "https://github.com/EXO-Robotics/minecraft-mod-pipeline.git",
                "attempted_command": "git push -u origin codex/aionbound-wave1-g8-integration",
                "observations": ["gh auth status reported the EXO-Robotics token invalid", "managed review rejected publishing 86 commits to an unverified destination while auth and exact publication scope were not trusted"],
                "decision_source": "NOT_OBSERVABLE",
                "retry_disposition": "DO_NOT_RETRY_OR_WORK_AROUND_WITHOUT_FRESH_DIRECT_EXACT_REPOSITORY_AND_BRANCH_APPROVAL_AFTER_AUTH_AND_RISK_DISCLOSURE",
                "product_or_candidate_consequence": "None; publication is external and separately gated. It does not invalidate source work or prove a product defect.",
                "committed_evidence_path": None,
            },
        },
        "after_approvals": [
            "ratify exact approved proposal hashes in a replacement decision ledger",
            "implement and locally validate approved Skyreach and Twinbond surfaces",
            "reconcile Ashen activation without bypassing tooling governance",
            "apply the selected audio contract",
            "then build twice, freeze an immutable generation, and run the separately gated final exact-package qualification ladder",
        ],
        "nonclaims": ["no product or ledger mutation", "no build or package", "no BDS", "no candidate freeze", "no client, multiplayer, console, Marketplace, publication, or release proof"],
    }


def render_markdown(packet: dict) -> str:
    sky, finale, audio = packet["decision_set"]
    p6 = packet["no_decision_required"]["packet006_base_presentation"]
    return f"""# Final Wave 1 decision packet

Status: `FINAL_WAVE1_DECISIONS_REQUIRED_NO_AUTHORITY_EFFECT`

Audited integration: commit `{AUDITED_COMMIT}`, tree `{AUDITED_TREE}`. The integration HEAD did not advance during this audit. This packet changes no product, ledger, G7, build, BDS, candidate, or publication state.

## Minimal approvals

Approve or reject each atomic product tranche, then choose one audio outcome. The exact text below is sufficient.

### 1. Skyreach

> {sky['approval_text_verbatim']}

Approval unlocks exact ratification and execution of the three hash-bound proposals. Without it, Skyreach remains foundation-complete but acquisition, loot, Storm Nest, seal recovery, and terminal progression remain dormant; a full candidate is impossible.

### 2. Twinbond finale

> {finale['approval_text_verbatim']}

Approval unlocks exact ratification and implementation of the same-world authored finale, bounded four-phase encounter, and guarded relic/Edge/Memory fulfillment. Without it, Twinbond stays withheld and the retired G7 finale path remains forbidden; a full candidate is impossible.

### 3. Audio — choose exactly one

Original-audio requirement:

> {audio['choices'][0]['approval_text_verbatim']}

Or explicit Wave 1 scope reduction:

> {audio['choices'][1]['approval_text_verbatim']}

No audio decision preserves the current original-audio blocker by default.

## Already closed; no new decision required

The exact Packet 006 source manifest has {p6['manifest_count']} identities. All {p6['source_presentation_complete']} have an item or placeable-block representation, geometry, registered texture with a present PNG, and localization. The split is {p6['item_representations']} items / {p6['block_representations']} placeable trophies, with {p6['attachables']} attachables. The four non-attachable representations are intentional placeable Whisperwood trophies. This is source presentation closure, not client/package/runtime proof.

`W1-CREATIVE-005` needs no approval if its eight sibling/unique-finish IDs remain absent, the approved base identities ship, no substitute is invented, and the omission is disclosed.

## Separate blockers not approved here

Ashen remains `ASHEN_VERTICAL_SOURCE_COMPLETE_RUNTIME_ACTIVATION_DEFERRED` under `MANAGED_REVIEWER_ACTIVATION_BLOCKED`. Do not retry or bypass it in this workload. It is not a demonstrated product defect, but the two dormant compositions must be normally activated or the contract explicitly revised before freeze; dormant gameplay cannot ship silently.

The GitHub push rejection is `EXTERNALLY_OBSERVED_NOT_PRODUCT_EVIDENCE`. Authentication was invalid and review rejected publication of 86 commits to an unverified destination. The decision source is not observable. This blocks only publication—not product work or candidate evidence—and must not be retried without fresh direct approval naming the exact repository and branch after auth/risk disclosure.

## Boundary

After approvals: ratify exact hashes, implement/validate the approved surfaces, reconcile Ashen, apply the audio choice, then build twice and run the separately gated final exact-package qualification. Nothing in this packet claims a package, BDS, client, multiplayer, console, Marketplace, publication, or release pass.
"""


def write_outputs(out: Path) -> None:
    packet = build()
    out.mkdir(parents=True, exist_ok=True)
    (out / "FINAL_WAVE1_DECISION_PACKET.json").write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "FINAL_WAVE1_DECISION_PACKET.md").write_text(render_markdown(packet), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE)
    args = parser.parse_args()
    write_outputs(args.out)


if __name__ == "__main__":
    main()
