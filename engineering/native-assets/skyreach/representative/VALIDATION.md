# Skyreach representative native repair gate

Status: `PASS_NATIVE_REPAIR_GATE`

Authority: integration commit `1810d0bb75e73be16d1c98e1d57dfe9ea485849d`, tree `11f377745f69b848396780dac1d039955fa90131`.

The bounded seven-class representative set (`wind_roc`, `gale_hawk`, `cloud_goat`, `wind_reed_plant`, `hanging_sky_vine`, `wind_shrine`, and `observation_tower`) completed two Blockbench 5.1.6 save-close-reopen/native-export cycles in an isolated extension-disabled profile over loopback-only CDP port 9268.

The staged projects preserve frozen Packet 004 editable geometry/UV signatures and exact texture bytes, normalize staged texture paths and public `aionbound` identifiers, add 10 true native locators at canonical packet-export transforms, and contain exactly the 18 animation roles declared by their frozen briefs. The aggregate receipt records 7/7 passing assets, 74 native screenshots, seven labeled contact sheets, canonical equality between both native export passes, and zero captured warnings/errors.

The packet originals were not modified. The static packet exports are used only as locator-transform authority. Whole-file equality with those generator-authored exports is informational; shape/UV preservation is bound to before/after editable-project signatures and native export determinism to pass-1/pass-2 canonical equality.

Remaining custom-geometry native repair roster:

- creatures: `sky_fox`, `cliff_ram`, `ropewing`, `stone_vulture`, `glide_drake`, `storm_gull`, `ruin_harpy`
- plants: `cliff_flower`, `cloud_moss`, `floating_blossom`, `rope_root`, `cloudpuff_plant`, `shelf_shrub`, `skybloom`, `nest_thatch_tuft`
- landmarks: `rope_bridge`, `cliff_outpost`, `floating_ruin_floor`, `nest_platform`, `broken_sky_path`, `hanging_lift_frame`, `ancient_sky_arch`, `cliff_beacon`

These 23 assets remain `NATIVE_REPAIR_REQUIRED`; this representative gate does not promote them. The 10 ordinary full-cube blocks and 10 flat resource items are Blockbench `NOT_APPLICABLE` and require their separate native block/item normalization lane.

Golden promotion remains withheld pending true silhouette-only and player-scale proof, independent originality/control comparison, and Bedrock client visual review. No BP/RP integration, gameplay, Creator Tools, BDS, client, multiplayer, physical console, Marketplace, or release claim is made.

Deterministic checks:

```sh
python3 engineering/native-assets/skyreach/intake/audit_packet_004.py \
  --json-output engineering/native-assets/skyreach/intake/SKYREACH_PACKET_004_NATIVE_READINESS.json \
  --markdown-output engineering/native-assets/skyreach/intake/SKYREACH_PACKET_004_NATIVE_READINESS.md
python3 -m unittest discover -s engineering/native-assets/skyreach/intake -p 'test_*.py' -v
python3 engineering/native-assets/skyreach/representative/build_contact_sheets.py
python3 engineering/native-assets/skyreach/representative/build_representative_report.py
python3 -m unittest discover -s engineering/native-assets/skyreach/representative -p 'test_*.py' -v
```
