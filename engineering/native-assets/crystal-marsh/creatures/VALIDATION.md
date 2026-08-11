# Crystal Marsh remaining-creature native repair gate

Status: `PASS_NATIVE_REPAIR_GATE`

Authority: G8 integration commit `13c24ac77fe4383e0a1be52671424c0fdf82eaf0`, tree `08d0721a29192991a63be908735b447ccbef91b6`.

This lane covers exactly `crystal_newt`, `prism_frog`, `glass_heron`, `mire_turtle`, `bloom_crab`, `reed_serpent`, and `bog_watcher`. Frozen Packet 003 originals remain unchanged. The native gate stages exact copies, normalizes only public identifiers and portable texture paths, preserves PNG bytes and editable shape/UV signatures, creates true native locator elements from canonical packet export transforms, and authors exactly the clip names declared by each frozen brief.

All seven projects passed two Blockbench 5.1.6 save-close-reopen/native-export cycles in one isolated profile over loopback port `9265`, with extensions disabled. The aggregate evidence records:

- 7/7 passing assets;
- 39/39 brief-declared clips and no extra clips;
- 14 true native locators at canonical packet transforms and parents;
- 95 exact native PNG screenshots, including one timeline state per clip;
- canonical pass-1/pass-2 equality for geometry and animation exports;
- stable editable shape/UV signatures before and after both round trips;
- exact source/staged texture byte equality;
- 7/7 bundled static geometry/texture/locator validation PASS;
- zero captured Blockbench warnings and zero captured errors.

Manual inspection of all seven labeled contact sheets confirms that the fixed orthographic, three-quarter, top, wireframe, atlas-underlay, and per-clip timeline captures are present and visibly bind to the expected creature. The brief-specific motion set remains distinct: newt frill/bite, frog hop/swim, heron wade/strike/flap, turtle walk/swim/withdraw, crab scuttle/claw snap, serpent undulation/swim/lunge, and watcher crawl/eye focus/lunge.

Run the deterministic local checks with:

```sh
python3 engineering/native-assets/crystal-marsh/creatures/build_contact_sheets.py
python3 engineering/native-assets/crystal-marsh/creatures/validate_native_exports.py
python3 engineering/native-assets/crystal-marsh/creatures/build_report.py
python3 -m unittest discover -s engineering/native-assets/crystal-marsh/creatures -p 'test_*.py' -v
```

Proof boundary: this establishes only native editable, locator, clip, screenshot, and codec-export behavior for the seven scoped assets. It does not establish BP/RP integration, gameplay, Creator Tools, BDS, Bedrock client rendering, multiplayer, physical PS4, Marketplace, or release readiness. Golden promotion remains withheld pending true-silhouette/player-scale fixed proof, independent originality comparison, and client visual review.
