# Ashen Packet 006 runtime lane

This focused lane binds the 13 newly native-qualified Ashen-facing Packet 006
base identities to BP/RP visual and stable base-role registration. It also
registers the four already-ratified derived components (`heat_core`,
`heavy_head`, `chitin_plate`, and `ember_heart`) as inventory item shells.

The native pass-2 geometry, animation, and model UV bytes are copied exactly.
Inventory icons are separately generated 32-by-32 RGBA presentation assets;
the original generated source and full-resolution alpha master are retained as
evidence. The report records the exact prompt, source/master/shipping hashes,
and the one-call-per-icon method.

No exact approved numeric damage, durability, repair, armor protection, or
mining-speed values were available, so none are invented here. Recipes,
acquisition, loot, boss/reward delivery, build, BDS, candidate work, and all
W1-CREATIVE-005 sidegrades are outside this lane. The existing Whisperwood
`briar_ring` base is byte-preserved.

Run the bounded proof with:

```sh
python3 engineering/ashen-intake/equipment-runtime-ashen/author_runtime.py
python3 -m unittest engineering/ashen-intake/equipment-runtime-ashen/test_runtime.py
```
