# Validation — Whisperwood equipment native lane A

Validated in an isolated Blockbench 5.1.6 process using loopback endpoint
`127.0.0.1:9248` and disposable profile
`/private/tmp/aionbound-wave1-equipment-a-blockbench-profile`.

All eight exact assets passed with:

- true native `effect` locator on `chassis`, copied from each canonical Packet 006 geometry export;
- exact brief clip closure: 18 clips total, no generic preview or extra clips;
- one native timeline PNG for each of the 18 clips;
- two Blockbench save/close/reopen/native-export passes;
- canonical geometry equivalence across the two passes;
- canonical animation equivalence across the two passes;
- unchanged group/cube/pivot identity outside the intended locator addition;
- zero captured Blockbench warnings and zero captured errors;
- `geometry.aionforge_eq.<id>` / `animation.aionforge_eq.<id>` normalized to the product namespace `aionbound`;
- portable `textures/<id>.png` editable references;
- exact 32×32 packet texture bytes preserved, with no upscale or redraw.

| Asset | Clips | Receipt SHA-256 | Native `.bbmodel` SHA-256 | Pass-2 geometry SHA-256 | Pass-2 animation SHA-256 |
|---|---:|---|---|---|---|
| `briar_cleaver` | 2 | `a6c7aaec9004e7b3aaa9885556b7e0af5b04fecd7d058f1a1958894f554825cb` | `1368224d7985b65aca9902b65a91b6e14be5889ded40f3ee8443d261b9fb9cd0` | `462565a0e280c1b78a089bead2846df0c471c9d70c7855ec6763c9e9f2be2c70` | `c84ffa02d21a3cb9dfdf7ce89d91ab50a128ca84727b4311b84acdb8912fb1bd` |
| `lantern_hook` | 2 | `9e44ac62ff2ab9e0432f6ea100ccbc4548530e9ea574b939adaae1250eefff59` | `f57276bda2cf2906b09f5da2206ec0e344b6c7b5104fe6dd60706df13e02850b` | `8e199779024d829a649dc294fae215c62bd9567b1904a5e2f2fea047fe2f2634` | `51f262c4beb0e191b79e3206dd42595dcecd0e6a17e875db60f9210c208ecd88` |
| `moon_sap_staff` | 3 | `ab602c074cbee7af2a0f7b0eac4402866100a3072f27dce4a53d6ba78e94e30e` | `6e326c896eacf7a0b70ab89e0a94a9876f17a7177dbdeef964cd5fcc874b0009` | `098104c0ce6c07284fb732cc685ef96c618c00713e331302dbf4cb9338587033` | `d466a603bf7e6e70205ed518864c56b30129900447a879781c97edf4edb825c7` |
| `mossfang_spear` | 3 | `196332504547b9cbb0902c161c38ca32d4d340bf964aab41976409c146a320d6` | `84c4f750974c7f86e8c05060a0262208b4b2c85c36d93b325e87397196fec05d` | `3462b90d58da4d428a1bbbc6604b6e3438d95616c49eea5f72287c9760f40be4` | `c35e1791d99c82e43659b770bbcca2a5e2bab5a4149fb4d989c1933d3a170ecf` |
| `root_knife` | 1 | `fb32db51742229d1a4636c1f9996f8e9dcc87d18108a4da9ed47b3b7aa871fc1` | `b4e93b5114c169f3d4cdc8c826633506607dd6d3d3b453eb3480dfdbe1bed5e8` | `8f02f4d44e656fb688fa9c240ab884e6675e6f69e9009d83ea5776b25fc5f99d` | `188926089afa68b7c12d84f7c44d2a66a6dc8ee12acf78b8684f1cf6276614ed` |
| `thorn_whip` | 3 | `0ea21de880ebd53843f60c5c8c32832a3c07fe4fbfdd09f0c9c6d5ff91fcd868` | `0a5923fb25a88e30b5ef9f6312acc4f95cc75696b144ad247d182d6c7c67487e` | `bfc69a9bf8652a65a19fc7815bc19bddb9fdb4128c73107c73581d6a7d466b8f` | `59924014af444f26d74096cc9ae575727cb7e55f562fef402b8d270f1272e133` |
| `whisperwood_hatchet` | 2 | `096f337894cd02ff0fbcb221c83d0ae27cfa5c2d22ab75a32a75cb8c94c258de` | `a020a2e1df33dd8d955279a51631bb10635721dd4f0251f8f3c1d92bec240d5e` | `4c6cd373807f947ece8f2789178b9db4031c7e8e1def689b24d5d13aacd1fc1d` | `91b830060662de50f6411d331b757584e267c0582eb48eea9ba33279baefd7f2` |
| `widow_fang_dagger` | 2 | `01687dc3f37791b10ab663d2f2fdf7376c3cd4159d0ee0f3fc81127e8bc6fb8a` | `335241518d1d4f45f623684cdb44efd0a0708c1c64ae12ffe53ec5496a5acf2f` | `f8c0f73e8a4bcdb6c2da89347b8cb039a14db065005e2c62f3494db71290e099` | `6ea16b857b7a3dcf17b5b2e4ec530273add5e364b18472a7c34b6f8a45c55e5a` |

Static contract tests: **6 passed**. Evidence verifier: **8 assets / 18 clips PASS**.

Proof boundary: this lane establishes only Blockbench-native editable/source,
locator, clip, screenshot, and codec-export evidence. It does not establish
BP/RP wiring, item or attachable behavior, acquisition, recipes, loot, Bedrock
client rendering/playback, BDS, multiplayer, controller, physical PS4, or
Marketplace readiness.
