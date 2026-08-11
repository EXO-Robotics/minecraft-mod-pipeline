# Whisperwood native Blockbench repair gate

This tool operates only on caller-supplied copied `.bbmodel`, PNG, and brief
inputs. It stages another isolated copy under a new/empty output directory; it
does not edit packet sources or shipping BP/RP files.

It is intentionally fail-closed:

- every brief-required animation must already exist in the editable project;
  missing clips produce `WITHHELD_MISSING_ROLE_ANIMATIONS` and exact
  `MISSING_REQUIRED_ROLE_CLIP:<name>` diagnostics before a native session starts;
- it never creates or renames animations;
- required locators are real Blockbench `Locator` elements, attached to the
  required existing bone (`effect` to `root`, `gaze` and `projectile` to
  `head`) or an explicit caller mapping;
- texture paths in the staged editable are normalized to its staged `textures/`
  folder;
- the editor must save/reopen twice, and the Bedrock geometry and animation
  codecs must produce canonically equivalent pass-one and pass-two exports;
- every required locator must occur in the second native geometry export.

The Blockbench instance must be launched separately with an isolated remote
debugging port. The tool accepts only a loopback CDP endpoint and never launches
or terminates Blockbench itself.

Example (illustrative only; not executed by this change):

```sh
python3 engineering/native-assets/whisperwood/repair_whisperwood_native.py \
  --bbmodel /tmp/copied-asset/model.bbmodel \
  --texture /tmp/copied-asset/model.png \
  --brief /tmp/copied-asset/brief.json \
  --output-dir /tmp/native-proof/model \
  --cdp-endpoint http://127.0.0.1:9333 \
  --capture-screenshots front three_quarter wireframe animate
```

Use `--locator-map mapping.json` only when the approved rig needs a different
existing parent bone. The map is a JSON object such as
`{"projectile":"muzzle"}`. A missing target bone or a mapping for a locator not
required by the brief is an error.

The evidence receipt binds input hashes, the staged project hash, Blockbench
version/format, locator additions, native export hashes, canonical two-pass
equivalence, exported locator coverage, and optional PNG screenshot hashes.
Screenshots are deliberately excluded from deterministic export equality.

Proof scope is limited to native Blockbench editable round-trip and codec
export. It does not establish Bedrock client rendering, Stable BDS behavior,
physical PS4 behavior, or Marketplace acceptance.
