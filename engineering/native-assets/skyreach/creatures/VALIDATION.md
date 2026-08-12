# Skyreach remaining-creature native validation

This lane is bound to G8 source commit `b65424610976a76ee6507917235d68f048ae249b` and tree `3f21de0ea75e4fe3344a1bac86e7d3c521129647`.

It stages frozen Packet 004 inputs for `cliff_ram`, `glide_drake`, `ropewing`, `ruin_harpy`, `sky_fox`, `stone_vulture`, and `storm_gull`; preserves exact texture bytes and editable geometry/UV signatures; authors exactly the 36 brief-declared clips; converts `effect` and `gaze` to true native locators from canonical packet transforms; and records two native Blockbench 5.1.6 save/reopen/export cycles plus fixed native screenshots.

Run from this directory with the isolated Blockbench endpoint already active:

```text
python3 run_all.py
python3 validate_native_exports.py
python3 build_contact_sheets.py
python3 build_report.py
python3 -m unittest -v test_author_creatures.py
```

The evidence is native editable/codec/static validation only. It does not claim BP/RP integration, gameplay, BDS, Bedrock client, multiplayer, physical PS4, Marketplace, or release proof. Golden promotion remains withheld pending true-silhouette, player-scale, independent-originality, and client visual review.
