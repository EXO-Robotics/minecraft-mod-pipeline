# Whisperwood ratified economy

Status: **STATIC CLOSURE PASS — CHECKPOINT 1 NOT CLAIMED**

This lane consumes `W1-001-WW` and `W1-004-WW-CH1` exactly as ratified. It
authors nine inventory identities, 26 recipes, ten natural entity tables,
seven structure chest tables, a protected Thorn Court material table, a
separate trophy-free arena chest, explicit plant/block harvest tables, and
eight repair bindings.

Chosen loot values remain inside the closed approved intervals:

- common: `1.00`, quantities `1–2`;
- uncommon: `0.40`, `0.50`, or `0.55`, quantities `1–2`;
- normal rare: `0.12`;
- elite rare: `0.50`;
- elite epic: `0.12`;
- minor/standard/landmark chests: `2`, `4`, and `5–6` total rolls;
- Thorn Court arena chest: `5` rolls and no trophy.

The natural `thorn_stalker` table contains only briar vine, thorn barb, and
stalker claw. No creature, chest, encounter-material table, or recipe contains
`aionbound:thorn_stalker_skull`. The runtime/persistence owner alone may create
the ratified per-player entitlement and fulfill/recover its physical display.
`briar_elk_trophy` and `mosskip_trophy` are optional crafts and never chapter
progression inputs.

`W1-CREATIVE-005` remains deferred. No sibling/sidegrade IDs or hidden upgrade
state are implemented. Curiosity prose remains Codex state, not inventory.

Run the bounded closure checks:

```sh
python3 engineering/whisperwood-intake/economy/author_whisperwood_economy.py --check
python3 engineering/whisperwood-intake/economy/test_whisperwood_economy.py
python3 -m unittest tests.test_whisperwood_economy_icons -v
python3 engineering/whisperwood-intake/structure-assemblies/author_whisperwood_structures.py --check
python3 engineering/whisperwood-intake/structure-assemblies/test_whisperwood_structure_assemblies.py
python3 tools/validate_wave1.py --root .
```

These checks prove source identity/reference closure, deterministic authored
bytes, exact icon decode/alpha properties, and the natural-stalker seal
prohibition. They do not prove Bedrock schema acceptance, chest population,
runtime entitlement/recovery, BDS startup, client gameplay, balance, console,
or Checkpoint 1.
