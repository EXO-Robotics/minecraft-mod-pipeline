# Whisperwood equipment native lane A

This lane repairs exactly eight Packet 006 Whisperwood held items:

- weapons: `mossfang_spear`, `widow_fang_dagger`, `thorn_whip`, `briar_cleaver`, `moon_sap_staff`
- tools: `root_knife`, `whisperwood_hatchet`, `lantern_hook`

The tool consumes immutable packet inputs, stages portable copies, normalizes
`geometry.aionforge_eq.<id>` to `geometry.aionbound.<id>`, creates a true
`effect` locator from the canonical geometry export on `chassis`, replaces
generic preview clips with the exact 18 brief-declared clips, and performs two
native Blockbench save/close/reopen/export passes. A timeline screenshot is
captured for every clip.

The exact 32×32 Packet 006 PNG bytes are preserved. The 64×64 brief declaration
is recorded as an unresolved source-contract mismatch; this lane does not
upscale, redraw, or reinterpret the approved pixels.

Example against an isolated Blockbench 5.1.6 loopback endpoint:

```sh
python3 author_equipment_a.py \
  --all \
  --output-root evidence \
  --cdp-endpoint http://127.0.0.1:9248 \
  --capture-timeline
```

Evidence proves native editable integrity, locator construction, native codec
export, two-pass structural equivalence, and exact clip/timeline coverage only.
It does not prove BP/RP binding, gameplay, recipes, loot, Bedrock client
rendering, BDS, multiplayer, controller behavior, PS4, or Marketplace status.
