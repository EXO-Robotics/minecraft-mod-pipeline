# Validation — Whisperwood entity animation repair A

Validated in an isolated Blockbench 5.1.6 process using the loopback-only CDP
endpoint `127.0.0.1:9242` and disposable profile
`/private/tmp/aionbound-wave1-entity-animation-a-blockbench-profile`.

All five assets passed native save/close/reopen/export twice with:

- exact brief clip-set closure (27 total clips; no extra clips);
- zero captured Blockbench warnings and zero captured errors;
- canonical two-pass geometry equivalence;
- canonical two-pass animation equivalence;
- unchanged group, cube, pivot, and texture identity;
- true `gaze` and `effect` locator export using canonical geometry transforms;
- timeline proof for every clip (27 distinct PNG screenshots);
- keyframe-time comparison bounded to `0.026` seconds for Blockbench's native
  20-FPS serialization grid.

| Asset | Clips | Receipt SHA-256 | Editable `.bbmodel` SHA-256 | Pass-2 geometry SHA-256 | Pass-2 animation SHA-256 |
|---|---:|---|---|---|---|
| `lantern_hare` | 5 | `8e0abc28c226242a67fedab4025af7e57f8ea04b10b8f36d37c71898b084cee4` | `b4e7f49335e6351b64815f87abcf1a9dbeebc9bc4805bf43b5dfa30db4a4c440` | `b7cb0e1aee7e7cf297089a5a56e96f07bfc20387d345eff31e0ef878d127863c` | `1559a16d4269c6b722cc6feda6c0fad0e42a3df0f2ac414fb33254d42b1bb40f` |
| `mosskip_fawn` | 5 | `7c020c5630f66d5a6387558e577b5ba2b8410a0a0c0385788f0d187703f1085c` | `c114f972fa4a72d6bb4f161f3d3cd1af9c36841f472645b64f1c5c48c938e996` | `84c3405817b2d6ffa942978468a358165347027477d2158b59689b840fe2c5e8` | `6dc4fdda1062682375e174bd640c128509e4f6b7462816fa584a3ad864aad290` |
| `mosskip_doe` | 6 | `5f4c2dbd7203ba5e957abd64773c23cd1406ce844e104401069e975554cac5fe` | `4c1c458bb8fffa51070a98c76d3e988f1e6441b71d1b2305e258122f67f53f88` | `2cf0dbec832bfa1d63ce0bd2ec9c900ce1a6a6d6547e87a14a6364e17c2ceade` | `68454f41e2b402b7ba2364758d7b688306cf4b7a72ff7d2490fe1390404ac2ba` |
| `mosskip_buck` | 6 | `314b1c1181d433cc51c398d39af7862b0d1db07cfd712e9f01f6cb2e22ed467d` | `082951772444686b46af2a905c607b46af09a37679c157b78217d75874fb3048` | `0b77565def6cd1837664f5f4866389737aa68720b990b49a5018f58dd362e548` | `307a9317eb475fda3b7f49715cfee236667648867446e83d7708f89732ee8e7d` |
| `rootback_boar` | 5 | `eccb3d94e05fc5003b3a13ffe9991d7da1bd74364c2d1a2a2595c0e6cd3b5184` | `9a4a66b0ca2f16dbafbf921d5b2ae0677a4d8a7bb96293ca31a71e197371ef3a` | `3626e60fed3b002483b66283bb2e029eae2e90a0fbdedcb801a5770105bcc13f` | `8b8aacf345c252513ef4e9c3d740469c4fde101b288c1a63d5bccfe898956e71` |

Unit contract tests: 6 passed.

Proof boundary: this lane establishes Blockbench-native editable and codec
evidence only. Bedrock client playback, animation-controller selection,
server-side behavior/pathfinding, package/BDS admission, multiplayer,
controller, split-screen, Realms, physical PS4, and Marketplace remain untested.
