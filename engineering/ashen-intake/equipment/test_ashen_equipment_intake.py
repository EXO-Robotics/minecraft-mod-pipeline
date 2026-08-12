#!/usr/bin/env python3
"""Deterministic checks for the Ashen-facing Packet 006 equipment intake."""

from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MAP_PATH = HERE / "ASHEN_EQUIPMENT_INTAKE.json"


def bedrock_root() -> Path:
    common = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = (REPO / common_path).resolve()
    # <bedrock>/program/<runs>/<generation>/repo/.git
    return common_path.parents[4]


BEDROCK_ROOT = bedrock_root()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve(path: str) -> Path:
    local = REPO / path
    if local.exists():
        return local
    return BEDROCK_ROOT / path


class AshenEquipmentIntakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(MAP_PATH.read_text())
        cls.assets = cls.data["assets"]
        cls.by_id = {row["id"]: row for row in cls.assets}
        cls.packet_root = BEDROCK_ROOT / cls.data["canonical_source_contract"]["packet_root"]

    def test_exact_scope_and_categories(self) -> None:
        ids = [row["id"] for row in self.assets]
        self.assertEqual(ids, self.data["scope"]["ordered_ids"])
        self.assertEqual(len(ids), 14)
        self.assertEqual(len(set(ids)), 14)
        self.assertEqual(
            dict(Counter(row["category"] for row in self.assets)),
            self.data["scope"]["counts"],
        )

    def test_base_and_authority_hashes(self) -> None:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD^{commit}"], cwd=REPO, check=True, capture_output=True, text=True
        ).stdout.strip()
        # The intake commit descends from the exact bound base; do not require HEAD to remain the base.
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", self.data["base"]["integration_commit"], head],
            cwd=REPO,
            check=False,
        )
        self.assertEqual(ancestor.returncode, 0)
        base_tree = subprocess.run(
            ["git", "show", "-s", "--format=%T", self.data["base"]["integration_commit"]],
            cwd=REPO,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(base_tree, self.data["base"]["integration_tree"])
        for row in self.data["authority"]:
            path = resolve(row["path"])
            self.assertTrue(path.is_file(), path)
            self.assertEqual(sha256(path), row["sha256"], path)

    def test_all_six_canonical_artifacts_are_hash_bound(self) -> None:
        templates = self.data["canonical_source_contract"]["artifact_keys"]
        self.assertEqual(set(templates), {"brief", "bbmodel", "editable_texture", "geometry", "animation", "export_texture"})
        for row in self.assets:
            self.assertEqual(set(row["artifact_sha256"]), set(templates), row["id"])
            for key, template in templates.items():
                path = self.packet_root / template.format(id=row["id"])
                self.assertTrue(path.is_file(), path)
                self.assertEqual(sha256(path), row["artifact_sha256"][key], path)

    def test_native_gaps_are_evidence_derived(self) -> None:
        for row in self.assets:
            asset_id = row["id"]
            bbmodel = json.loads((self.packet_root / f"assets/editable/{asset_id}.bbmodel").read_text())
            geometry = json.loads((self.packet_root / f"assets/export/models/{asset_id}.geo.json").read_text())
            animation = json.loads((self.packet_root / f"assets/export/animations/{asset_id}.animation.json").read_text())
            brief = json.loads((self.packet_root / f"assets/briefs/{asset_id}.json").read_text())

            native_locators = [element.get("name") for element in bbmodel.get("elements", []) if element.get("type") == "locator"]
            exported_locators = {
                name
                for bone in geometry["minecraft:geometry"][0]["bones"]
                for name in bone.get("locators", {})
            }
            source_clips = {name.rsplit(".", 1)[-1] for name in animation["animations"]}
            description = geometry["minecraft:geometry"][0]["description"]

            self.assertEqual(native_locators, [], asset_id)
            self.assertEqual(exported_locators, {"effect"}, asset_id)
            self.assertEqual(row["native_locator_gap"], ["effect"], asset_id)
            self.assertEqual(source_clips, set(row["source_clips"]), asset_id)
            self.assertEqual(brief["animations"], row["brief_clips"], asset_id)
            self.assertEqual((description["texture_width"], description["texture_height"]), (32, 32), asset_id)
            self.assertTrue(description["identifier"].startswith("geometry.aionforge_eq."), asset_id)
            texture_path = bbmodel["textures"][0]["path"]
            self.assertTrue(Path(texture_path).is_absolute(), asset_id)

    def test_historical_runtime_scan_is_preserved_and_successor_ids_are_now_bound(self) -> None:
        historically_absent = set(self.data["collision_and_reuse"]["exact_runtime_id_scan"]["new_identities_absent"])
        self.assertEqual(historically_absent, set(self.by_id) - {"briar_ring"})
        for asset_id in historically_absent:
            item = REPO / f"behavior_pack/items/{asset_id}.item.json"
            block = REPO / f"behavior_pack/blocks/{asset_id}.block.json"
            self.assertNotEqual(item.exists(), block.exists(), asset_id)
            self.assertTrue((REPO / f"resource_pack/attachables/{asset_id}.attachable.json").exists(), asset_id)
        briar = self.data["collision_and_reuse"]["whisperwood_briar_ring"]
        self.assertEqual(briar["classification"], "KEEP_EXISTING_BASE_REUSE_ONLY")
        for row in briar["existing_files"]:
            path = REPO / row["path"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(sha256(path), row["sha256"], path)

    def test_functional_reuse_does_not_alias_identity(self) -> None:
        self.assertTrue((REPO / "behavior_pack/items/basalt_maul.item.json").is_file())
        self.assertTrue((REPO / "behavior_pack/items/gale_repeater.item.json").is_file())
        self.assertNotIn("basalt_hammer", (REPO / "behavior_pack/items/basalt_maul.item.json").read_text())
        self.assertNotIn("ash_repeater", (REPO / "behavior_pack/items/gale_repeater.item.json").read_text())

    def test_blockers_and_proof_boundary_fail_closed(self) -> None:
        self.assertEqual(self.by_id["briar_ring"]["blocked_by"], ["W1-CREATIVE-005"])
        self.assertEqual(set(self.by_id["ash_drake_horn"]["blocked_by"]), {"W1-003-KILN-SKY", "W1-004-AH"})
        self.assertEqual(self.by_id["ember_forge_core"]["blocked_by"], ["W1-004-AH"])
        for asset_id, row in self.by_id.items():
            if asset_id not in {"briar_ring", "ash_drake_horn", "ember_forge_core"}:
                self.assertEqual(set(row["blocked_by"]), {"W1-001-AH", "W1-004-AH"}, asset_id)
        self.assertEqual(self.data["native_readiness"]["blockbench_run"], "NOT_RUN")
        self.assertEqual(self.data["proof_boundary"]["runtime_pack_binding"], "NOT_IMPLEMENTED")
        self.assertEqual(self.data["proof_boundary"]["stable_bds"], "NOT_RUN")
        self.assertEqual(self.data["proof_boundary"]["physical_ps4"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
