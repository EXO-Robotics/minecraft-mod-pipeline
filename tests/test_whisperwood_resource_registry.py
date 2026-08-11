import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = (
    ROOT
    / "engineering"
    / "whisperwood-intake"
    / "resource-registry"
    / "WHISPERWOOD_RESOURCE_REGISTRY.json"
)
ATLAS_PATH = ROOT / "resource_pack" / "textures" / "item_texture.json"
LANG_PATH = ROOT / "resource_pack" / "texts" / "en_US.lang"


class WhisperwoodResourceRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
        cls.lang = {}
        for line in LANG_PATH.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                cls.lang[key] = value

    def test_exact_packet_resource_set(self):
        expected = {
            "whisper_bark",
            "moss_resin",
            "glow_spore",
            "hollow_amber",
            "lantern_fur",
            "moon_sap",
            "root_heart",
            "briar_antler",
            "widow_silk",
            "ancient_acorn",
        }
        actual = {entry["id"] for entry in self.registry["resources"]}
        self.assertEqual(expected, actual)
        self.assertEqual(10, len(self.registry["resources"]))

    def test_item_identifier_display_and_stack_policy(self):
        stack_policy = self.registry["stack_policy"]
        for entry in self.registry["resources"]:
            item_path = ROOT / "behavior_pack" / "items" / f"{entry['id']}.item.json"
            item = json.loads(item_path.read_text(encoding="utf-8"))["minecraft:item"]
            self.assertEqual("1.21.80", json.loads(item_path.read_text(encoding="utf-8"))["format_version"])
            self.assertEqual(f"aionbound:{entry['id']}", item["description"]["identifier"])
            self.assertEqual("items", item["description"]["menu_category"]["category"])
            self.assertEqual(entry["display_name"], item["components"]["minecraft:display_name"]["value"])
            self.assertEqual(entry["id"], item["components"]["minecraft:icon"]["textures"]["default"])
            self.assertEqual(
                stack_policy[entry["stack_category"]],
                item["components"]["minecraft:max_stack_size"],
            )

    def test_texture_atlas_and_localization_closure(self):
        texture_data = self.atlas["texture_data"]
        for entry in self.registry["resources"]:
            expected_texture = f"textures/aionbound/whisperwood/items/{entry['id']}"
            self.assertEqual(expected_texture, texture_data[entry["id"]]["textures"])
            self.assertEqual(
                entry["display_name"],
                self.lang[f"item.aionbound:{entry['id']}"],
            )

    def test_expected_icon_bytes_are_present(self):
        missing_or_empty = []
        for entry in self.registry["resources"]:
            icon_path = ROOT / entry["expected_icon"]
            if not icon_path.is_file() or icon_path.stat().st_size == 0:
                missing_or_empty.append(entry["expected_icon"])
        self.assertEqual([], missing_or_empty, "missing or empty icon bytes: " + ", ".join(missing_or_empty))


if __name__ == "__main__":
    unittest.main()
