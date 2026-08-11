# Whisperwood block runtime slice

Status: static implementation complete; runtime qualification not run in this
lane.

The ten Packet 001 block-class assets are bound from the native Blockbench
PASS evidence in `engineering/native-assets/whisperwood/evidence`. Shipping
geometry is the receipt-bound pass-2 export with one mechanical change only:
the malformed generated identifier `geometry.geometry.aionforge_ww.<id>` is
normalized to `geometry.aionbound.<id>`. Textures are byte-identical to the
native-gate inputs.

## Ordinary engineering defaults

- Stable block format `1.21.80` and construction/nature creative-menu groups.
- One custom geometry plus one opaque material instance per block. Every source
  texture is a fully opaque 32 x 32 RGBA PNG; no alpha behavior was inferred.
- Mining time is `2.0` seconds for wood/brick building blocks, `1.5` for moss
  bark, `0.8` for root understory, and `0.2` for leaves/sapling.
- Sound families are `stone` for forest brick, `wood` for timber variants, and
  `grass` for leaves, roots, and sapling.
- The sapling alone has no collision because its approved profile is a small
  plant. No growth behavior is implied by this static block registration.

These values are implementation defaults, not Creative identity decisions, and
remain tunable at the Whisperwood vertical gameplay integration checkpoint.

## Intentionally withheld

- Generic `idle` / `action` animation exports are not shipped: the asset briefs
  require no block animations and no approved runtime trigger exists.
- Recipes, block loot, rotations/states, growth, decay, placement restrictions,
  structures, world generation, progression, Script API, and audio events are
  outside this lane.
- This slice does not claim Bedrock client, Stable BDS, package, console, or
  candidate qualification.

Run the bounded validation with:

```sh
python3 engineering/whisperwood-intake/block-runtime/test_whisperwood_block_runtime.py -v
```
