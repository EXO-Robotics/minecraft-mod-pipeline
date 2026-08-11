# Ashen remaining-creature native repair gate

Status: `PASS_NATIVE_REPAIR_GATE`

Authority: G8 integration commit `4b4118869e95e9699bd1f480feca573c3e3dca9f`, tree `c42ffa9cdbc233d2acdf7cebf7f67bfc2257faa8`.

This lane covers exactly `ash_mite`, `magma_lizard`, `furnace_beetle`, `char_wolf`, `cinder_lynx`, `soot_stag`, and `basalt_tortoise`. Frozen Packet 002 originals were not edited. Exact copies were staged, their public identifiers were normalized to `geometry.aionbound.<asset>`, texture paths were made portable without changing PNG bytes, and required locators were created as true native locator elements using the canonical packet export transforms and parents.

All seven projects passed two Blockbench 5.1.6 save-close-reopen/native-export cycles in one isolated profile over loopback port `9264`, with extensions disabled. The aggregate evidence records:

- 7/7 passing assets;
- 37/37 brief-declared clips and no extra clips;
- 13 true native locators;
- 93 native PNG screenshots, including one timeline state per clip;
- canonical pass-1/pass-2 equality for geometry and animation exports;
- stable editable shape/UV signatures before and after both round trips;
- exact source/staged texture byte equality;
- zero captured Blockbench warnings and zero captured errors.

The authored motion remains creature-specific: mite skitter, lizard lunge, beetle charge/clamp, wolf run/snarl, lynx stalk/pounce, stag trot/antler shake, and tortoise slow-walk/withdraw clips use only their own Packet 002 rigs and the roles named by their briefs.

Run the deterministic local checks with:

```sh
python3 engineering/native-assets/ashen/creatures/build_report.py
python3 -m unittest discover -s engineering/native-assets/ashen/creatures -p 'test_*.py' -v
```

Proof boundary: this establishes only native editable, locator, clip, screenshot, and codec-export behavior for the scoped assets. It does not establish BP/RP integration, gameplay, BDS, Bedrock client rendering, multiplayer, physical PS4, Marketplace, or release readiness. Golden promotion remains withheld pending true-silhouette/player-scale fixed proof, independent originality comparison, and client visual review.
