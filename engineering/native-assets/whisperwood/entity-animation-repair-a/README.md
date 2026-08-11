# Whisperwood entity animation repair A

This narrow Blockbench-native lane authors the brief-approved clips for exactly:

- `lantern_hare`
- `mosskip_fawn`
- `mosskip_doe`
- `mosskip_buck`
- `rootback_boar`

The tool consumes caller-supplied copies of the frozen Packet 001 `.bbmodel`,
texture, geometry export, and brief. It removes the generic preview `idle` and
`action` clips, creates only the names declared by the brief, repairs true
native locators from the canonical geometry export, then performs two native
Blockbench save/close/reopen/export passes. Evidence is written below
`engineering/native-assets/whisperwood/evidence/<asset>/`.

Run one asset against an isolated loopback Blockbench 5.1.6 instance:

```sh
python3 author_entity_animations.py \
  --asset lantern_hare \
  --bbmodel /path/to/copied/lantern_hare.bbmodel \
  --texture /path/to/copied/lantern_hare.png \
  --geometry /path/to/copied/lantern_hare.geo.json \
  --brief /path/to/copied/lantern_hare.json \
  --output-dir ../evidence/lantern_hare \
  --cdp-endpoint http://127.0.0.1:9242 \
  --capture-timeline
```

The receipts prove only native editable integrity, native codec export,
deterministic two-pass structural equivalence, locator preservation, and
authored keyframe coverage. They do not prove Bedrock client playback, BDS
behavior, controller behavior, physical-console performance, or Marketplace
acceptance.
