# Whisperwood deterministic staging importer

`import_whisperwood.py` reads only the canonical `assets/` tree from Packet
001 and writes to an empty caller-selected staging directory. It never writes
to the shipping BP/RP.

The importer normalizes `aionforge_ww` identifiers to `aionbound`, canonical
filenames, and editable texture references when the source evidence is safe.
Its default CLI behavior is fail-closed: exit `0` means every discovered asset
was staged; exit `2` means a manifest was written but one or more assets were
withheld; exit `1` means the canonical input or destination was invalid.

Two promotion classes are deliberately separate:

- Explicitly brief-bound flat inventory icons and provable one-cube blocks are
  staged without their generated custom model. A model UV atlas is never
  inferred to be an inventory icon. Blockbench is `NOT_APPLICABLE` only for an
  explicitly bound flat representation.
- Custom geometry is staged only when the editable project contains real
  native locator elements, the exported geometry contains the same required
  locators, every brief-required role clip exists, and every related asset is
  an exact Packet 001 warehouse ID.

Anything else is listed as blocked in
`WHISPERWOOD_IMPORT_MANIFEST.json` and no potentially shippable copy is
emitted. Static staging does not prove a Blockbench round trip, native export
equivalence, client rendering, BDS behavior, console behavior, or candidate
qualification.

Example:

```sh
python3 engineering/normalization/whisperwood/import_whisperwood.py \
  --packet-root /absolute/path/to/asset-sprint-001-whisperwood \
  --staging-dir /tmp/whisperwood-stage
```
