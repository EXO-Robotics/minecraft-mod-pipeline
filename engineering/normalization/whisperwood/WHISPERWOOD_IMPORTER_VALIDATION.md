# Whisperwood importer validation

Status: `STATIC_TOOLING_PASS_PACKET_REMAINS_REPAIR_BLOCKED`

Authority base: `05aff36392d9c31cf0745ee651427d7efc87b53d`

## Automated tests

Command:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
```

Result: 13 tests passed, including five importer-specific tests for deterministic
output, namespace/path rewriting, missing locator and role-clip rejection,
ambiguous dependency rejection, simple texture-only staging, and preservation
of a nonempty caller directory.

## Canonical Packet 001 smoke

The importer was run twice against the canonical
`asset-sprint-001-whisperwood` packet into two empty temporary staging
directories. `diff -qr` reported byte-for-byte equality.

The second manifest SHA-256 was:

`52593615e8dcc92cbde527c248eb1d9b10c11f98d02a6aed1598f8829a21678f`

Observed result:

- 50 canonical assets inventoried.
- 3 promotable simple texture items: `briar_antler`, `lantern_fur`, and
  `widow_silk`.
- 47 assets withheld.
- 40 custom-geometry assets lacked required native locator elements in their
  editable `.bbmodel` projects.
- 18 assets lacked one or more brief-required role clips.
- 38 assets contained at least one non-exact `related_assets` token; these
  require an engineering binding or Creative clarification.

Counts overlap because one asset may have multiple blockers. Exported geometry
did contain the declared locator names, but that does not cure the missing
native locator elements in the editable sources.

## Proof boundary

This validates deterministic static staging and conservative rejection only.
It does not prove native Blockbench round-trip, native export equivalence,
shipping BP/RP integration, Bedrock client rendering, BDS behavior, console
behavior, or candidate qualification. No shipping pack was modified and no
candidate was declared.
