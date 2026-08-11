# Crystal Marsh remaining plant native gate

This lane owns exactly eight non-representative Packet 003 plants:
`crystal_lily`, `prism_bloom`, `glass_moss`, `marsh_fern`, `glow_kelp`,
`mire_orchid`, `pearl_grass`, and `crystal_vine`.

The already-passing `bubble_pod` and `flood_reed` representative evidence is
excluded and unchanged. The gate stages frozen packet copies, normalizes only
portable texture paths and public `aionbound` identifiers, creates the true
native `effect` locator from the canonical packet export, authors exactly the
brief-declared semantic clips, and runs two native Blockbench save/reopen/export
cycles. No generic `idle` or `action` aliases are carried forward.

This is native editable-source and codec-export evidence only. It does not edit
or qualify BP/RP content, gameplay, Creator Tools, BDS, Bedrock client,
multiplayer, console, Marketplace, or release lanes.

Rebuild deterministic receipts and run local checks with:

```sh
python3 engineering/native-assets/crystal-marsh/plants/build_plant_report.py
python3 -m unittest discover -s engineering/native-assets/crystal-marsh/plants -p 'test_*.py' -v
```
