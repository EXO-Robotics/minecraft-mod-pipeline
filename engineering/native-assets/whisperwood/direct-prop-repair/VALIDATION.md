# Direct prop native validation

Status: `PASS` for the bounded Blockbench-native source/export gate.

## Lantern Post

- Blockbench: `5.1.6`, Bedrock format, zero captured warnings and zero errors.
- Final clips: exactly `animation.aionforge_ww.lantern_post.idle_sway` and
  `animation.aionforge_ww.lantern_post.glow`.
- `idle_sway`: 4.0-second loop, `lantern` rotation only, peak 2.2 degrees.
- `glow`: 3.2-second loop, `chassis` scale only, peak scale delta 0.04.
- Native `effect` locator: parent `chassis`, transform `[0, 16, -7]`.
- Two native geometry exports are canonically equivalent:
  `da7148c14048c3895e9b15d375f135f5a8b007f9c496f5f3d0db6fe5d2e90f3c`.
- Two native animation exports are byte-identical:
  `5a1e3ce9a5cbc4cd85d92343a2cf626a739fda83e9e157298f6cbf842c7a4802`.
- Final editable source SHA-256:
  `9ca46127983a7d6a7d8a0318e19c71a6741f3bb908c7be9c7961365947266ba1`.
- Texture SHA-256 is unchanged from the packet:
  `0f3c6e9c5da8ff47991455e6186427cb7a061d356d5f496e9bd5f32f0e412cb1`.

## Moss Cairn

- Blockbench: `5.1.6`, Bedrock format, zero captured warnings and zero errors.
- Final clip set: empty, matching the brief.
- Native `effect` locator: parent `chassis`, transform `[0, 10, 0]`.
- Two native geometry exports are byte-identical:
  `62007e16ddf57f1c4dbc54cd6325050282b375ea420f775059ce437e3eb7abd5`.
- Two native empty animation exports are byte-identical:
  `7882082857fdb11e02f158ebc3a6d3f970e2ac60d54813f0e903ee97b2293749`.
- Final editable source SHA-256:
  `a4b7730537e4bbadd932a3b4aa2bb481bad502d1f6b481213c2b36401b689020`.
- Texture SHA-256 is unchanged from the packet:
  `dde2e374a189ae3e664f2c67469f4751e45057a1ac769faa544cda9df338eb7b`.

## Authority observation

Both briefs declare a 64-pixel texture target while the packet editable models,
embedded texture records, canonical geometry descriptions, and PNGs are all
32x32. This lane preserves those approved source pixels and does not silently
upscale or repaint them. The existing packet-normalization authority should
retain the mismatch until Creative ratifies a texture-size change.

## Proof boundary

The evidence proves that the exact staged editable assets survived two native
Blockbench save-close-reopen passes and produced equivalent native geometry and
animation exports. Timeline screenshots prove that both Lantern Post clips and
their keyframes were present in the final editor session.

It does not prove custom-block animation binding or playback. Bedrock client,
Stable BDS, controller, multiplayer, physical PS4, and Marketplace gates remain
untested.
