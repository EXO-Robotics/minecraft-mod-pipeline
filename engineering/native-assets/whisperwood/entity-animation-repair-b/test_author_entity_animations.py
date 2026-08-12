#!/usr/bin/env python3

import importlib.util
import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "engineering"))
from repo_paths import find_bedrock_root
MODULE_SPEC = importlib.util.spec_from_file_location("whisperwood_entity_animation_lane_b", HERE / "author_entity_animations.py")
assert MODULE_SPEC and MODULE_SPEC.loader
module = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = module
MODULE_SPEC.loader.exec_module(module)

PACKET = find_bedrock_root(ROOT) / "program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-001-whisperwood/assets"
RUNTIME_MAP = ROOT / "engineering" / "whisperwood-intake" / "entity-runtime" / "WHISPERWOOD_ENTITY_RUNTIME_IMPLEMENTATION_MAP.json"


class EntityAnimationLaneBTests(unittest.TestCase):
    def test_exact_asset_partition(self):
        self.assertEqual(
            set(module.ENTITY_SPECS),
            {"bark_wraith", "briar_elk", "hollow_widow_spider", "rot_wolf", "thorn_stalker"},
        )

    def test_specs_match_authorities_and_existing_bones(self):
        runtime = json.loads(RUNTIME_MAP.read_text())
        runtime_by_id = {item["warehouse_id"]: item for item in runtime["entities"]}
        for asset, spec in module.ENTITY_SPECS.items():
            module.lane.validate_spec(asset, spec)
            brief = json.loads((PACKET / "briefs" / f"{asset}.json").read_text())
            model = json.loads((PACKET / "editable" / f"{asset}.bbmodel").read_text())
            geometry = json.loads((PACKET / "export" / "models" / f"{asset}.geo.json").read_text())
            runtime_item = runtime_by_id[asset]
            self.assertEqual(list(spec["clips"]), brief["animations"])
            self.assertEqual(spec["brief_role"], brief["role"])
            self.assertEqual(spec["role"], runtime_item["approved_role"])
            self.assertEqual(spec["runtime_class"], runtime_item["runtime_class"])
            self.assertEqual(spec["movement_intent"], runtime_item["movement_intent"])
            bones = set(module.lane.group_names(model))
            animated = {bone for clip in spec["clips"].values() for bone in clip["bones"]}
            self.assertFalse(animated - bones)
            exported = module.lane.native.exported_locator_specs(geometry, brief["locators"])
            self.assertEqual(set(exported), set(brief["locators"]))

    def test_thorn_stalker_has_explicit_visual_only_boundary(self):
        boundary = module.ENTITY_SPECS["thorn_stalker"]["boss_motion_boundary"]
        for forbidden_authority in ("hit", "phase", "damage", "reset", "multiplayer", "persistence", "reward"):
            self.assertIn(forbidden_authority, boundary)


if __name__ == "__main__":
    unittest.main()
