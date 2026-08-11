# Whisperwood Plant-Class Native Gate

Status: `PASS_NATIVE_EDITABLE_AND_CODEC_GATE`.

Six assets pass the same native Blockbench 5.1.6 save/close/reopen/export gate
used by the block class:

- `briar_vine`
- `ember_thistle`
- `glow_moss`
- `hollow_lily`
- `mooncap_mushroom`
- `root_flower`

Their committed receipts bind copied input hashes, the native `effect` locator
repair, two native exports, warning count, and proof boundary.

Four assets were initially withheld before editor mutation because their briefs
require a role clip that the packet export did not contain. Engineering has now
authored only those four exact approved clips through Blockbench 5.1.6 native
animation APIs:

| Asset | Native clip | Duration | Animated bones | Native project SHA-256 | Geometry SHA-256 | Animation SHA-256 |
| --- | --- | ---: | --- | --- | --- | --- |
| `lantern_bloom` | `animation.aionforge_ww.lantern_bloom.glow_idle` | 3.2 s | `chassis` scale | `83c07c3d1d22088c9bb667cde5d500c786538ce3791e3afc67385b8e7e8083f5` | `ee39486a32ecae588eef6ef1f45a29e20e917228cc72d470cf10d7340fd56c78` | `7a8d78dd2add0ae4207fce552497f1b146130fa0a55b56c0a8f9c86282a6d8f1` |
| `pale_reed` | `animation.aionforge_ww.pale_reed.sway` | 4.0 s | `clump` rotation | `7ee29e53ec5f39cd8d464abbd7b74a8967e265fed63180957faaf0153ff47a16` | `4d05dd1e4c9121c2b4452bfe5dd9be9e215347cba32a8c629df2ff90dbfcdb92` | `46b7db929e424cf83b708c481cee6e9193c1b7d5b6b0dc15999452b10086151f` |
| `star_grass` | `animation.aionforge_ww.star_grass.wind_sway` | 3.6 s | `clump` rotation | `eff30948c124ecd4fae1c6ea1172526aeb547b2ba03b7451f39d4607b4b19878` | `b460cdc953a5a12ff2f389f38fe6aa4a9a0253e83e05e63ad734d659953926cb` | `5dda2aeed7fd4a1f67b97907b827f35215e3434fc5bc406fa96530250fd1e775` |
| `whisper_fern` | `animation.aionforge_ww.whisper_fern.gentle_sway` | 4.8 s | `frond_a`, `frond_b`, `frond_c` rotation | `77afa1712380dfc1cdf240647c3be639a44ba06b6268c7be1b8fc27c302ba558` | `70beb6fb8e6c0af91b7fabb8c0ea53e2844e27b42eb6cc92dcd21f8d7f84ee5b` | `0418c9076be6ee87056eae1def713998073a6c6bb94e2f6adae20367f22d0e8f` |

The native transaction removed the packet's generic `idle`/`action` previews,
created exactly one approved loop per asset, installed the canonical `effect`
locator on its existing source bone, and saved/closed/reopened/exported twice.
All four receipts record:

- exact two-pass geometry and animation codec equivalence;
- unchanged group/cube construction and unchanged texture bytes;
- the correct non-duplicated `geometry.aionforge_ww.*` export identifier;
- exact duration, bone, channel, loop-seam, and restrained motion limits;
- zero Blockbench warnings and errors;
- three hashed native Animate-timeline screenshots, excluded from deterministic
  equality.

The four exported geometries also pass the bundled static Bedrock asset
validator for identifier, bone/cube structure, texture dimensions, and the
required `effect` locator. Their receipts are stored at
`evidence/<asset>/plant-animation-native-receipt.json`.

This evidence is limited to native editable and codec behavior. It does not
prove Bedrock client rendering or animation playback, BDS, world generation,
harvesting, console, or shipping readiness.
