# Wave 1 successor validator

`tools/validate_wave1.py` is the evolving G8 mechanical validator. It does not
reuse G7's frozen exact-count assertions. Instead it inventories the checked-out
packs, requires the proven G7 inventory as a minimum floor, and requires named
Wave 1 additions from `WAVE_1_VALIDATION_AUTHORITY.json`, including the ten
Whisperwood blocks, ten Whisperwood resource items, four foundation recipes,
the exact ten Ashen resource items, and the exact ten Ashen full-cube blocks.
The G7 inventory numbers remain minimum floors: later growth is accepted, but
none of the named successor additions may disappear.

Run it with:

```text
python3 tools/validate_wave1.py
```

Use `--report PATH` to persist the JSON result. The report includes a
path-and-byte-bound aggregate SHA-256 for every BP/RP source file and is derived
from the bytes inspected in that invocation; it is not a hand-authored PASS
receipt.

The Ashen additions also carry explicit definition, item/terrain atlas,
`en_US.lang`, and PNG closure requirements. Passing reports emit per-ID hashes
for the definition, atlas, language file, and resolved PNG, plus the exact atlas
and language bindings.
The hash-bound seven-asset Blockbench aggregate is required as native editable
asset evidence only. Its presence and declared shape do not count as BP/RP,
client, gameplay, BDS, or release proof.

The validator fails closed for malformed JSON or PNG files, duplicate or invalid
custom identifiers, broken BP/RP manifest dependencies, missing script entry or
relative imports, unresolved custom recipe/loot/entity/feature references,
missing atlas textures, unresolved entity geometry/animation/render-controller
references, unresolved custom block geometry/material texture pairs, unstable
Script API dependency declarations, and forbidden external-runtime constructs.

## Proof boundary

A PASS is source-tree mechanical evidence only. It is not an immutable-package,
archive-extracted entrypoint, Bedrock schema, Stable BDS, client rendering,
gameplay, multiplayer, console, Marketplace, or release result. Those remain
separate gates.
