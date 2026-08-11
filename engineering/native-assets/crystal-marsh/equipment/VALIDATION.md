# Crystal-facing Packet 006 native equipment gate

Status: `PASS_NATIVE_REPAIR_GATE`

Authority: G8 integration commit `d6c1ab2c18ac0ec21a0218bf2c807d4177071673`, tree `52e0b9bde38158dc1287579931e0d86ce98aa4d8`.

Exact scope: `crystal_pike`, `prism_bow`, `crystal_circlet`, `explorer_cloak`, `crystal_shovel`, `marsh_sickle`, `crystal_talisman`, `marsh_idol`, `marsh_wight_mask`, `moon_pearl_pedestal`, and `crystal_obelisk_fragment`.

`surveyor_staff` and `trail_compass` are explicitly excluded and unchanged. `W1-CREATIVE-005` remains deferred; no sidegrades or substitute presentation were authored.

Frozen Packet 006 originals were not edited. Exact input copies were staged, public identities normalized to `geometry.aionbound.<asset>`, texture references made portable, and each `effect` locator was created as a true native locator element using the canonical export parent and transform. Every authoritative editable/export PNG is the same exact 32×32 RGBA byte stream. Although some briefs permit or declare up to 64×64, no source authority requests an upscale, so the 32×32 bytes were preserved without resampling.

All 11 projects passed two Blockbench 5.1.6 save-close-reopen/native-export cycles in an isolated profile over loopback port `9267`, with extensions disabled. Aggregate evidence records:

- 11/11 passing assets;
- 16/16 brief-declared clips, using their exact declared names with no generic aliases or extra clips;
- 11 true native `effect` locators derived from canonical exports;
- 104 native PNG screenshots, including one timeline state per declared clip;
- canonical pass-1/pass-2 equality for geometry and animation exports;
- stable editable shape/UV signatures across both round trips;
- exact packet/staged texture byte equality;
- zero captured Blockbench warnings and zero errors.

The shared native codec has a frozen Packet 002 preflight prefix. An ephemeral, unretained identity shim was used only for that preflight; every evidence directory contains the exact original Packet 006 brief and records its `geometry.aionforge_eq.<asset>` identity and hash.

Run deterministic checks with:

```sh
python3 engineering/native-assets/crystal-marsh/equipment/build_report.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s engineering/native-assets/crystal-marsh/equipment -p 'test_*.py' -v
```

Proof boundary: this establishes only native editable, locator, clip, screenshot, texture-byte, and codec-export behavior for the scoped assets. It does not modify or prove BP/RP integration, icons, gameplay, recipes, loot, authority, BDS, Bedrock client rendering, multiplayer, physical PS4, Marketplace, or release readiness.
