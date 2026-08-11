# Ashen-facing Packet 006 native equipment gate

Status: `PASS_NATIVE_REPAIR_GATE`

Authority: G8 integration commit `f9d9735cd575761456b3db7b351facea700207f8`, tree `3d14fc72b746b63c0602e2327bdb87205f2e08bd`.

Exact scope: `basalt_hammer`, `ember_great_axe`, `ash_repeater`, `ashen_helmet`, `ashen_chest`, `ashen_legs`, `ashen_boots`, `basalt_pick`, `ember_hammer`, `ore_chisel`, `ember_totem`, `ash_drake_horn`, and `ember_forge_core`.

`briar_ring` is explicitly excluded and unchanged. It remains the existing Whisperwood base while `W1-CREATIVE-005` is deferred; no Ashen sidegrade was created.

Frozen Packet 006 originals were not edited. Exact input copies were staged, public identities normalized to `geometry.aionbound.<asset>`, texture references made portable, and `effect` locators created as true native locator elements using canonical export parents and transforms. The source textures are all exact 32×32 RGBA images and their bytes were preserved without resampling or upscale.

All 13 projects passed two Blockbench 5.1.6 save-close-reopen/native-export cycles in an isolated profile over loopback port `9266`, with extensions disabled. Aggregate evidence records:

- 13/13 passing assets;
- 18/18 brief-declared clips and no extra clips;
- 13 true native `effect` locators;
- 122 native PNG screenshots, including one timeline state per declared clip;
- canonical pass-1/pass-2 equality for geometry and animation exports;
- stable editable shape/UV signatures across both round trips;
- exact packet/staged texture byte equality;
- zero captured Blockbench warnings and zero errors.

The shared native codec has a frozen Packet 002 preflight prefix. An ephemeral, unretained identity shim was used only for that preflight; each evidence directory contains the exact original Packet 006 brief and records its `geometry.aionforge_eq.<asset>` identity and hash.

Run deterministic checks with:

```sh
python3 engineering/native-assets/ashen/equipment/build_report.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s engineering/native-assets/ashen/equipment -p 'test_*.py' -v
```

Proof boundary: this establishes only native editable, locator, clip, screenshot, texture-byte, and codec-export behavior for the scoped assets. It does not modify or prove BP/RP integration, icons, gameplay, authority, BDS, Bedrock client rendering, multiplayer, physical PS4, Marketplace, or release readiness.
