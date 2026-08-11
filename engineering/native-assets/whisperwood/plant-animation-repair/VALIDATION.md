# Validation record

Authority base: integration commit
`732da734a51ee55e3cbf0fa9674ec907272e0fbe`.

Native editor: isolated Blockbench 5.1.6 renderer at loopback endpoint
`127.0.0.1:9238`.

Inputs: caller-created copies of the frozen Packet 001 `.bbmodel`, PNG, brief,
and canonical geometry files. The packet originals were not modified. Evidence
copies are retained under each asset's `evidence/<asset>/inputs/` directory.

## Results

All four receipts report `PASS`, an empty diagnostics array, zero native
warnings, zero native errors, one exact approved clip, an intact native
`effect` locator, unchanged group/cube signatures, unchanged texture bytes, and
canonical equivalence across two geometry and animation exports.

The bundled static validator reported:

```text
OK: 1 geometry definition(s), 4 bone(s), 13 cube(s), 1 locator(s)
OK: 1 geometry definition(s), 3 bone(s), 12 cube(s), 1 locator(s)
OK: 1 geometry definition(s), 3 bone(s), 11 cube(s), 1 locator(s)
OK: 1 geometry definition(s), 6 bone(s), 13 cube(s), 1 locator(s)
```

The narrow unit suite reports four passing tests covering the exact authorized
asset set, exact brief clip leaves, finite nonzero looping specifications, and
namespaced clip construction.

Native Animate screenshots at neutral, quarter, and half-cycle frames were
visually inspected. They show the exact clip selected, real timeline keys on
existing bones, and restrained role-appropriate poses. Screenshot pixels are
editor evidence only and are excluded from deterministic export equality.

No behavior pack, resource pack, package, candidate, or BDS operation occurred
in this lane. Bedrock client playback and every console/release gate remain
untested.
