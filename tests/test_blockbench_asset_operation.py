from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from mccompiler.operations.blockbench_ops import author_blockbench_asset
from mccompiler.operations.envelope import OperationError
from mccompiler.project.store import ProjectStore


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "prototypes/blockbench/bramblehorn"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parameters() -> dict:
    manifest = read(ASSET / "asset-manifest.json")
    return {
        "project_id": "fixture",
        "asset_id": manifest["asset_id"],
        "asset_class": manifest["asset_class"],
        "asset_manifest": manifest,
        "template_family": "quadruped-regional-creature-1.0.0",
        "gameplay_role": manifest["gameplay_role"],
        "visual_intent": manifest["visual_intent"],
        "style_profile": read(ASSET.parent / "visual-style-profile-1.0.0.json"),
        "silhouette_requirements": ["readable horns", "heavy chest"],
        "geometry_budget": manifest["geometry_budget"],
        "texture_budget": manifest["texture_budget"],
        "bone_contract": manifest["bone_contract"],
        "pivot_contract": manifest["pivot_contract"],
        "locator_contract": manifest["locator_contract"],
        "animation_contract": manifest["animation_contract"],
        "collision_contract": manifest["collision_contract"],
        "visible_bounds_contract": manifest["visible_bounds_contract"],
        "bedrock_target_profile": manifest["bedrock_target_profile"],
        "rights_policy": {"status": "original_generated"},
        "deterministic_seed": manifest["deterministic_seed"],
        "reference_restrictions": ["no copied geometry", "no traced texture"],
        "source_files": {
            "bbmodel": str(ASSET / "bramblehorn.bbmodel"),
            "texture": str(ASSET / "bramblehorn_texture.png"),
            "geometry": str(ASSET / "bramblehorn.geo.json"),
            "animations": str(ASSET / "addon/resource_pack/animations/bramblehorn.animation.json"),
            "animation_controller": str(ASSET / "addon/resource_pack/animation_controllers/bramblehorn.animation_controllers.json"),
            "client_entity": str(ASSET / "addon/resource_pack/entity/bramblehorn.entity.json"),
            "behavior_entity": str(ASSET / "addon/behavior_pack/entities/bramblehorn.json"),
        },
        "blockbench_version": "5.1.5",
        "exporter_version": "Blockbench Bedrock Entity codec 5.1.5",
        "native_roundtrip": {
            "reopened": True,
            "native_save": True,
            "runtime_geometry_reexported": True,
        },
        "quality_report": read(ASSET / "visual-quality-report.json"),
        "repair_history": read(ASSET / "repair-history.json")["revisions"],
        "bindings": [{"consumer": "ccoriginal:bramblehorn", "kind": "client_and_behavior_entity"}],
    }


class BlockbenchAssetOperationTests(unittest.TestCase):
    def test_qualified_asset_is_registered_with_ps4_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ProjectStore.create(Path(temporary) / "project")
            result, _, artifacts = author_blockbench_asset(store, parameters(), store.revision)
            self.assertEqual("QUALIFIED", result["status"])
            self.assertEqual("MARKETPLACE_CANDIDATE_PS4_PENDING", result["final_qualification_disposition"])
            registry = store.read("assets/registry.json")
            self.assertEqual("PENDING", registry["assets"][0]["physical_ps4"])
            self.assertTrue(all((store.root / row["path"]).is_file() for row in artifacts))

    def test_non_releasable_rights_fail_without_mutating_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ProjectStore.create(Path(temporary) / "project")
            revision = store.revision
            request = parameters()
            request["rights_policy"] = {"status": "unknown"}
            with self.assertRaises(OperationError) as context:
                author_blockbench_asset(store, request, revision)
            self.assertEqual("AUTONOMOUS_AUTHORING_FAILED", context.exception.code)
            self.assertEqual(revision, store.revision)
            self.assertEqual([], store.read("assets/registry.json")["assets"])


if __name__ == "__main__":
    unittest.main()
