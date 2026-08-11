# Whisperwood equipment runtime A

This lane binds exactly five Packet 006 Whisperwood weapons and three tools to
the Behavior and Resource Packs. It consumes only native Blockbench pass-2
geometry/animations and byte-identical approved 32x32 UV sheets.

The shipping inventory icons under
`resource_pack/textures/aionbound/whisperwood/equipment/<id>.png` are supplied
by the separate icon pass and hash-checked against its evidence-derived receipt.
The native UV sheets remain isolated under `equipment/models/`; no UV sheet is
used as a shipping inventory icon. Runtime-A's original atlas keys already
pointed at these exact shipping paths, so the icon handoff required no atlas
rewrite.

No recipe, loot, acquisition, repair ingredient, sidegrade, or new art is
introduced. Extended melee reach, literal attack-speed control, elite-specific
damage, lantern-hook pull/climb, and action-clip input binding are explicitly
withheld. The source report does not claim build, package, BDS, client,
multiplayer, controller, console, Marketplace, or release proof.

Run:

```sh
python3 engineering/whisperwood-intake/equipment-runtime-a/author_runtime_a.py
python3 engineering/whisperwood-intake/equipment-runtime-a/test_runtime_a.py
node --test tests/g7_runtime_semantics.test.mjs
```
