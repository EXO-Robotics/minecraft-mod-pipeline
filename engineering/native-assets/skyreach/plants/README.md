# Skyreach remaining plant native gate

This lane owns exactly eight non-representative Packet 004 plants:
`cliff_flower`, `cloud_moss`, `cloudpuff_plant`, `floating_blossom`,
`nest_thatch_tuft`, `rope_root`, `shelf_shrub`, and `skybloom`.

The already-passing `wind_reed_plant` and `hanging_sky_vine` representative
evidence is excluded and unchanged. The gate stages frozen packet copies,
normalizes only portable texture paths and public `aionbound` identifiers,
creates the true native `effect` locator from the canonical packet export,
authors exactly the brief-declared semantic clips, and runs two native
Blockbench save/reopen/export cycles. No generic `idle` or `action` aliases are
carried forward.

This is native editable-source and codec-export evidence only. It does not edit
or qualify BP/RP content, gameplay, Creator Tools, BDS, Bedrock client,
multiplayer, console, Marketplace, or release lanes.

Rebuild deterministic receipts and run local checks with:

```sh
python3 engineering/native-assets/skyreach/plants/build_plant_report.py
python3 -m unittest discover -s engineering/native-assets/skyreach/plants -p 'test_*.py' -v
```
