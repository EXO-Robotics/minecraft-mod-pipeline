from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from mccompiler.blockbench_assets import (
    validate_animation_contract,
    validate_geometry,
    validate_semantic_coordinates,
)
from tools.build_bramblehorn_asset import ASSET, OUTPUT, build
from tools.build_server_qualification_planning import build_documents


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class BramblehornVerticalSliceTests(unittest.TestCase):
    def test_native_and_runtime_exports_preserve_contract(self) -> None:
        manifest = read(ASSET / "asset-manifest.json")
        runtime = read(ASSET / "bramblehorn.geo.json")
        native = read(ASSET / "native-export/bramblehorn.geo.json")
        for geometry in (runtime, native):
            result = validate_geometry(
                geometry,
                namespace=manifest["namespace"],
                required_bones=manifest["bone_contract"]["required"],
                required_locators=manifest["locator_contract"]["required"],
                texture_size=(64, 64),
            )
            self.assertEqual((8, 18, 3), (result["bone_count"], result["cube_count"], result["locator_count"]))
            self.assertEqual("PRESERVED", validate_semantic_coordinates(geometry)["left_right"])

    def test_required_animation_lifecycle_is_explicit(self) -> None:
        manifest = read(ASSET / "asset-manifest.json")
        geometry = read(ASSET / "bramblehorn.geo.json")
        result = validate_animation_contract(
            read(ASSET / "addon/resource_pack/animations/bramblehorn.animation.json"),
            read(ASSET / "addon/resource_pack/animation_controllers/bramblehorn.animation_controllers.json"),
            required_clips=manifest["animation_contract"]["required_clips"],
            required_states=manifest["animation_contract"]["required_states"],
            bones=[row["name"] for row in geometry["minecraft:geometry"][0]["bones"]],
        )
        self.assertGreaterEqual(result["clip_count"], 5)
        self.assertEqual(5, result["state_count"])

    def test_package_is_deterministic_and_ps4_model_keeps_physical_pending(self) -> None:
        first = build()
        first_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
        second = build()
        self.assertEqual(first_hash, hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
        self.assertEqual(first["artifact"]["sha256"], second["artifact"]["sha256"])
        proxy = build_documents(Path(__file__).resolve().parents[1])["ps4-planning-proxy.json"]
        authored = proxy["authored_asset_inputs"]["bramblehorn"]
        self.assertEqual("INCLUDED_WITHIN_CREATURES_ELITE_SYSTEM_NOT_ADDITIVE", authored["planning_treatment"])
        self.assertEqual("PENDING", authored["physical_ps4"])
        self.assertFalse(proxy["claims"]["ps4_verified"])


if __name__ == "__main__":
    unittest.main()
