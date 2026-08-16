from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "engineering/structure-playtest/STRUCTURE_PLAYTEST_HANDOFF.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StructurePlaytestBundleTests(unittest.TestCase):
    def test_manifest_versions_are_reciprocal(self) -> None:
        behavior = json.loads((ROOT / "behavior_pack/manifest.json").read_text())
        resources = json.loads((ROOT / "resource_pack/manifest.json").read_text())
        expected = [1, 3, 1]
        self.assertEqual(behavior["header"]["version"], expected)
        self.assertEqual(resources["header"]["version"], expected)
        self.assertEqual(behavior["dependencies"][0]["version"], expected)
        self.assertEqual(resources["dependencies"][0]["version"], expected)
        for module in behavior["modules"] + resources["modules"]:
            self.assertEqual(module["version"], expected)

    def test_exact_structures_are_bound(self) -> None:
        handoff = json.loads(HANDOFF.read_text())
        self.assertEqual(handoff["status"], "STRUCTURE_PLAYTEST_SOURCE_BOUND")
        self.assertEqual(len(handoff["structures"]), 2)
        for structure in handoff["structures"]:
            path = ROOT / structure["path"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(sha256(path), structure["sha256"])

    def test_structure_ids_are_flat_and_distinct(self) -> None:
        handoff = json.loads(HANDOFF.read_text())
        identifiers = [row["identifier"] for row in handoff["structures"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertTrue(all(value.startswith("aionbound:") for value in identifiers))
        self.assertTrue(all("/" not in value for value in identifiers))

    def test_no_worldgen_was_added_for_review_structures(self) -> None:
        for identifier in ("hunter_lodge_g2", "grand_stone_castle"):
            self.assertFalse((ROOT / f"behavior_pack/features/{identifier}.structure_feature.json").exists())
            self.assertFalse((ROOT / f"behavior_pack/feature_rules/{identifier}.structure_feature_rule.json").exists())


if __name__ == "__main__":
    unittest.main()
