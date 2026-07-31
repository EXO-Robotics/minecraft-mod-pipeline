#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validate_bedrock_pack_hazards import validate


class BedrockPackHazardTests(unittest.TestCase):
    def fixture(self, server_version: str = "2.0.0") -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        bp = root / "bp"
        rp = root / "rp"
        (bp / "scripts").mkdir(parents=True)
        rp.mkdir()
        bp_uuid = "11111111-1111-4111-8111-111111111111"
        rp_uuid = "22222222-2222-4222-8222-222222222222"
        bp_manifest = {
            "header": {"uuid": bp_uuid},
            "dependencies": [
                {"uuid": rp_uuid},
                {"module_name": "@minecraft/server", "version": server_version},
            ],
        }
        rp_manifest = {
            "header": {"uuid": rp_uuid, "pack_scope": "world"},
            "dependencies": [{"uuid": bp_uuid}],
        }
        (bp / "manifest.json").write_text(json.dumps(bp_manifest))
        (rp / "manifest.json").write_text(json.dumps(rp_manifest))
        return temp, bp, rp

    def test_removed_event_rejected_for_server_2(self) -> None:
        temp, bp, rp = self.fixture()
        self.addCleanup(temp.cleanup)
        (bp / "scripts" / "main.js").write_text(
            "world.beforeEvents.itemUseOn.subscribe(() => {});"
        )
        result = validate(bp, rp, cooperative=False)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "REMOVED_SCRIPT_EVENT_MEMBER",
            {row["code"] for row in result["findings"]},
        )

    def test_current_interaction_event_passes(self) -> None:
        temp, bp, rp = self.fixture()
        self.addCleanup(temp.cleanup)
        (bp / "scripts" / "main.js").write_text(
            "world.beforeEvents.playerInteractWithBlock.subscribe(() => {});"
        )
        result = validate(bp, rp, cooperative=False)
        self.assertEqual(result["status"], "PASS", result)

    def test_pack_icons_are_profile_gated(self) -> None:
        temp, bp, rp = self.fixture()
        self.addCleanup(temp.cleanup)
        result = validate(bp, rp, cooperative=False, require_pack_icons=True)
        self.assertIn(
            "PACK_ICON_MISSING",
            {row["code"] for row in result["findings"]},
        )
        (bp / "pack_icon.png").write_bytes(b"png")
        (rp / "pack_icon.png").write_bytes(b"png")
        result = validate(bp, rp, cooperative=False, require_pack_icons=True)
        self.assertEqual(result["status"], "PASS", result)


if __name__ == "__main__":
    unittest.main()
