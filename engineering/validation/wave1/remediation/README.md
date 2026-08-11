# Wave 1 source-closure remediation

This lane resolves only the ten findings emitted by `tools/validate_wave1.py`
at base commit `9064107a8df563796ffe222df506bbc58246f1f6`.

The repair deliberately reuses existing G7/packet bytes. Mosskip is rebound to
the already-present `mosskip_trail` clean-room model, texture, and idle clip.
Four material names receive atlas aliases to their already-present texture
paths. Barkling receives an empty loot table because its familiar authority
defines no loot identity.

The Burrowgate Key and Waykeeper Whistle remain ordinary icon-backed items.
Their optional attachable documents were removed because neither G7 nor the
packet evidence contains authored handheld geometry. Creating two generic
models merely to satisfy closure would invent art and overstate asset readiness.

`WAVE_1_CLOSURE_REMEDIATION.json` records each finding and its disposition.
`test_closure_remediation.py` guards those exact decisions and invokes the
successor validator against the repository source tree.

## Proof boundary

Passing these checks proves source-tree mechanical closure only. It does not
prove an immutable package, archive-extracted entrypoint, Bedrock schema, Stable
BDS load, client rendering, gameplay, multiplayer, console, Marketplace, or
release readiness.
