# Whisperwood foundation crafting

This bounded slice implements four evidence-bound construction recipes: Whisperwood log, stripped log, and bark-on-all-sides wood convert to planks using the ordinary four-plank timber default; four Whisperwood logs convert to three Whisperwood wood blocks using the ordinary bark-on-all-sides construction default.

The binding creative evidence is `WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md` section 1.A.3 and `03_crafting/CRAFTING_TREE.md` section 3.1. Canonical identifiers come from the checked-in Whisperwood implementation map and the registered behavior-pack blocks.

The slice deliberately withholds bark-to-plank quantity, stripping interaction, accent-block formulas, equipment, derived components, loot, boss, and progression recipes. See `WHISPERWOOD_CRAFTING_FOUNDATION.json` for the exact authority, decisions, and proof boundary.

Run the bounded static checks with:

```sh
python3 engineering/whisperwood-intake/crafting-foundation/test_whisperwood_crafting_foundation.py
```

Passing proves static JSON, identifier, uniqueness, exact-signature collision, and scope closure only. It is not BDS, client, balance, progression, or candidate evidence.
