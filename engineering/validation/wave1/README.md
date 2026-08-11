# Wave 1 successor validator

`tools/validate_wave1.py` is the evolving G8 mechanical validator. It does not
reuse G7's frozen exact-count assertions. Instead it inventories the checked-out
packs, requires the proven G7 inventory as a minimum floor, and requires named
Wave 1 additions from `WAVE_1_VALIDATION_AUTHORITY.json`, including the ten
Whisperwood blocks, ten resource items, and four foundation recipes.

Run it with:

```text
python3 tools/validate_wave1.py
```

Use `--report PATH` to persist the JSON result. The report includes a
path-and-byte-bound aggregate SHA-256 for every BP/RP source file and is derived
from the bytes inspected in that invocation; it is not a hand-authored PASS
receipt.

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
