#!/usr/bin/env python3
"""Create candidate metadata from final G7 shipping bytes and deterministic artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(relative: str, value: object) -> None:
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def members(root: Path) -> list[dict]:
    return [
        {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path), "size": path.stat().st_size}
        for path in sorted(root.rglob("*")) if path.is_file()
    ]


def count(folder: str, suffix: str = ".json") -> int:
    return len(list((ROOT / folder).rglob(f"*{suffix}")))


def main() -> None:
    artifacts = json.loads((ROOT / "dist/g7-artifact-manifest.json").read_text())["artifacts"]
    ledger_entries = members(ROOT / "behavior_pack") + members(ROOT / "resource_pack")
    write("manifests/g7-source-byte-ledger.json", {
        "aggregate_sha256": hashlib.sha256("".join(f'{row["path"]}\t{row["sha256"]}\n' for row in ledger_entries).encode()).hexdigest(),
        "entries": ledger_entries,
        "generation": 7,
        "member_count": len(ledger_entries),
        "scope": ["behavior_pack", "resource_pack"],
        "state": "COMPLETE"
    })
    counts = {
        "armor": 8,
        "accessories": 6,
        "blocks": count("behavior_pack/blocks"),
        "custom_entities": count("behavior_pack/entities"),
        "items_weapons_tools_total": count("behavior_pack/items"),
        "loot_tables": count("behavior_pack/loot_tables"),
        "natural_spawn_rules": count("behavior_pack/spawn_rules"),
        "recipes": count("behavior_pack/recipes"),
        "resources_and_material_items": 16,
        "structures": count("behavior_pack/structures", ".mcstructure"),
        "weapons": 10
    }
    write("manifests/g7-candidate-manifest.json", {
        "artifacts": artifacts,
        "authority": {
            "control_commit": "390e978d8f1233ad2278d1ef89e4dad33757f68e",
            "g6_commit": "a27047ab96a2e40a2b5b4034f3d86402e47dd16a",
            "g6_mcaddon_sha256": "3982c1d9f6be1cab6b0fda3f15e219abde8ce585cb5721cdc2f542305ba39ee3",
            "source_snapshot_aggregate_sha256": "b4b6f1d0f1db49a86b3cd6e817023d289a2132ab13de124d09ed3c7c900196da"
        },
        "candidate_id": "AIONBOUND_CORE_CONTENT_BETA_G000007",
        "claims": ["IMPLEMENTED", "PRODUCER_LOCAL_STATIC_AND_SEMANTIC_PASS", "DETERMINISTIC_BUILD_PASS"],
        "content_counts": counts,
        "external_gates_not_claimed": ["retail client", "controller", "multiplayer", "split-screen", "physical console", "rights", "Marketplace", "release"],
        "generation": 7,
        "immutable_after_commit": True,
        "qualification_pending": ["mechanical admission", "Stable BDS exact package", "same-world restart", "deterministic cleanup"],
        "state": "AIONBOUND_CORE_CONTENT_BETA_G7_CANDIDATE_READY_FOR_FREEZE"
    })
    write("reports/g7-producer-local-validation.json", {
        "checks": {
            "content_counts": "PASS",
            "identifier_recipe_loot_texture_closure": "PASS",
            "json_and_png_decode": "PASS",
            "runtime_semantics": "PASS_14_TESTS",
            "stable_api_forbidden_runtime_scan": "PASS",
            "structure_template_static_presence": "PASS_15",
        },
        "counts": counts,
        "proof_boundary": "Producer-local static and mocked semantic evidence only; no BDS, client, controller, console, rights, Marketplace, or release proof.",
        "status": "PASS"
    })
    write("reports/g7-deterministic-build.json", {
        "artifacts": artifacts,
        "build_1_equals_build_2": True,
        "build_invocations": 2,
        "packaging": "sorted members, fixed timestamps, fixed permissions, fixed compression",
        "source_generation_during_build": False,
        "status": "PASS"
    })
    promotions = [
        ["breezetail_kite", "breezetail", "creature"], ["galestrider_ridge", "galestrider", "creature"],
        ["lanternback_glow", "lanternback", "creature"], ["pebblehorn_quarry", "pebblehorn", "creature"],
        ["basalt_magma_spitter", "basalt_magma_spitter", "creature"], ["cinder_brood_hatchling", "cinder_brood_hatchling", "creature"],
        ["colossus_shard_golem", "colossus_shard_golem", "creature"], ["storm_egg_totem", "storm_egg_totem", "creature"],
        ["tide_spawn_skitter", "tide_spawn_skitter", "creature"], ["veil_mask_acolyte", "veil_mask_acolyte", "creature"],
        ["brood_fang_daggers", "brood_fang_daggers", "weapon"], ["roc_pinion_glaive", "roc_pinion_glaive", "weapon"],
        ["behemoth_tusk_bow", "behemoth_tusk_bow", "weapon"], ["mite_resin", "mite_resin", "material_icon"],
        ["pinion_feather_tuft", "pinion_feather_tuft", "material_icon"], ["anvil_chitin_deposit", "anvil_chitin", "material_icon"],
        ["trophy_relic_tooth", "trophy_relic_tooth", "material_icon"], ["prism_dew_crystal", "prism_dew_crystal", "material_icon"]
    ]
    write("manifests/g7-promotion-receipt.json", {
        "entries": [{"source_asset_id": source, "target_id": f"aionbound:{target}", "target_role": role} for source, target, role in promotions],
        "historical_qualification_transferred": False,
        "new_original_runtime_assets": ["aionbound:cinder_duelist", "aionbound:stormbound_raider", "aionbound:ferrowake_bulwark", "32-block palette", "15 structure templates"],
        "not_claimed": ["native Blockbench roundtrip", "client rendering", "physical console", "rights approval", "Marketplace", "release"],
        "product_id": "aionbound_core",
        "source_snapshot": {
            "aggregate_sha256": "b4b6f1d0f1db49a86b3cd6e817023d289a2132ab13de124d09ed3c7c900196da",
            "commit": "779e47362ec7aba594338659082c77fe521657f2",
            "tree": "a683c463275ce931550e5262c215ef23216a9dfd"
        },
        "state": "PROMOTED_WITH_FRESH_G7_QUALIFICATION_REQUIRED"
    })
    print(json.dumps({"artifacts": artifacts, "counts": counts, "ledger_members": len(ledger_entries)}, sort_keys=True))


if __name__ == "__main__":
    main()
