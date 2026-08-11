import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REPORT_PATH = Path(__file__).with_name("ASHEN_RESOURCE_RUNTIME_REPORT.json")
AUTHORITY_PATH = ROOT / "engineering/ashen-intake/authority/ASHEN_HIGHLANDS_VERTICAL_INTAKE_MAP.json"
ATLAS_PATH = ROOT / "resource_pack/textures/item_texture.json"
LANG_PATH = ROOT / "resource_pack/texts/en_US.lang"
EXPECTED = {
    "smolder_bark", "charbone", "sulfur_cluster", "volcanic_glass_shard",
    "ember_resin", "heatstone", "furnace_chitin", "basalt_core",
    "ash_crystal", "fire_bloom_seed",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AshenResourceRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        cls.authority = json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))
        cls.atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))["texture_data"]
        cls.lang = {}
        for line in LANG_PATH.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                cls.lang[key] = value

    def test_exact_packet_002_resource_authority(self):
        authority_assets = {
            asset["warehouse_id"]: asset for asset in self.authority["assets"]
            if asset["category"] == "resources"
        }
        self.assertEqual(EXPECTED, set(authority_assets))
        self.assertEqual(EXPECTED, {entry["warehouse_id"] for entry in self.report["resources"]})
        self.assertEqual(10, len(self.report["resources"]))
        self.assertEqual(sha256(AUTHORITY_PATH), self.report["authority"]["sha256"])
        for asset, entry in authority_assets.items():
            self.assertEqual(f"aionbound:{asset}", entry["runtime_id"])

    def test_stable_inert_item_definitions(self):
        allowed_components = {"minecraft:display_name", "minecraft:icon"}
        for entry in self.report["resources"]:
            path = ROOT / entry["item_path"]
            document = json.loads(path.read_text(encoding="utf-8"))
            item = document["minecraft:item"]
            self.assertEqual("1.21.80", document["format_version"])
            self.assertEqual(entry["runtime_id"], item["description"]["identifier"])
            self.assertEqual({"category": "items"}, item["description"]["menu_category"])
            self.assertEqual(allowed_components, set(item["components"]))
            self.assertEqual(entry["display_name"], item["components"]["minecraft:display_name"]["value"])
            self.assertEqual(entry["warehouse_id"], item["components"]["minecraft:icon"]["textures"]["default"])
            self.assertEqual(entry["item_sha256"], sha256(path))

    def test_texture_localization_and_icon_byte_closure(self):
        for entry in self.report["resources"]:
            asset = entry["warehouse_id"]
            self.assertEqual(entry["texture_path"], self.atlas[asset]["textures"])
            self.assertEqual(entry["display_name"], self.lang[f"item.aionbound:{asset}"])
            icon = ROOT / entry["icon_path"]
            self.assertTrue(icon.is_file())
            self.assertEqual(entry["icon_sha256"], sha256(icon))
            self.assertEqual("NOT_APPLICABLE", entry["blockbench"]["status"])

    def test_report_preserves_narrow_proof_boundary(self):
        self.assertEqual("ten Packet 002 warehouse resource items only", self.report["scope"])
        self.assertIn("recipes and crafting relations", self.report["withheld"])
        self.assertIn("scripts and persistence", self.report["withheld"])
        self.assertIn(
            "Stable BDS, multiplayer, controller, console, Marketplace, candidate, or release qualification",
            self.report["proof_boundary"]["does_not_prove"],
        )


if __name__ == "__main__":
    unittest.main()
