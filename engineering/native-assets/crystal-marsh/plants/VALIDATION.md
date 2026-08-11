# Crystal Marsh remaining plant native validation

Status: `PASS_NATIVE_REPAIR_GATE`

Authority: integration commit
`75b773c6330a3dceb48841c1bebd3b8e1c58da76`, tree
`a5dfbf0b9b3b36dcb9e293264d2a1165cfcad221`.

All eight assigned plants completed two native Blockbench 5.1.6
save/close/reopen/export cycles through an isolated loopback-only CDP session.
The staged projects preserve exact Packet 003 texture bytes and editable
geometry/UV signatures, use portable texture paths, export
`geometry.aionbound.<asset>` identifiers, and retain one true native `effect`
locator per plant at its canonical packet-export transform.

The exact brief-declared clip set is five clips total: `glow_idle` for
`crystal_lily` and `prism_bloom`, `sway` for `marsh_fern` and `pearl_grass`,
and `bob` for `glow_kelp`. `glass_moss`, `mire_orchid`, and `crystal_vine`
correctly retain empty clip sets. No generic `idle` or `action` aliases were
authored. Each declared clip has a native timeline capture.

The aggregate receipt records 8/8 passing assets, 5 semantic clips, 8 true
native locators, 69 fixed-view/atlas/timeline PNG captures, and zero captured
warnings or errors. Pass-1 and pass-2 native geometry and animation exports are
canonically equivalent for every asset. The deterministic aggregate was built
twice with identical SHA-256
`ac7b3472057bde906f239c835e84ebd20647d90e86db00574a4c70ca1690e5c9`.
All eight bounded local tests pass.

This proves native editable-source round-trip, exact semantic clip authoring,
canonical locator retention, texture-byte preservation, stable native exports,
and captured fixed views. It does not prove BP/RP integration, gameplay,
Creator Tools, BDS, Bedrock client rendering or playback, multiplayer,
physical PS4, Marketplace, or release readiness. Golden promotion remains
withheld pending true silhouette/player-scale proof, independent originality
review, and client visual review.
