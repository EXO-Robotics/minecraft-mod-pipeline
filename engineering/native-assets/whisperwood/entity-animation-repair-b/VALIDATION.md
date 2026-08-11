# Whisperwood entity animation repair B validation

## Result

All five scoped Packet 001 creatures passed the bounded Blockbench-native gate
against Blockbench 5.1.6 on an isolated loopback CDP endpoint.

| Asset | Clips | Locators | Timeline captures | Native warnings | Native errors | Two-pass geometry | Two-pass animation |
|---|---:|---:|---:|---:|---:|---|---|
| `bark_wraith` | 5 | 2 | 5 | 0 | 0 | equivalent | equivalent |
| `briar_elk` | 6 | 2 | 6 | 0 | 0 | equivalent | equivalent |
| `hollow_widow_spider` | 6 | 2 | 6 | 0 | 0 | equivalent | equivalent |
| `rot_wolf` | 6 | 2 | 6 | 0 | 0 | equivalent | equivalent |
| `thorn_stalker` | 6 | 3 | 6 | 0 | 0 | equivalent | equivalent |

Each receipt binds the exact packet inputs, native editable project, texture,
two geometry exports, two animation exports, canonical locator transforms,
per-clip motion metrics, and screenshot hashes.

## Exact final artifact hashes

| Asset | Receipt SHA-256 | Native `.bbmodel` SHA-256 | Texture SHA-256 | Pass-2 geometry SHA-256 | Pass-2 animation SHA-256 |
|---|---|---|---|---|---|
| `bark_wraith` | `180e165aad4ce424e1f86e3195a5ba6547985011259369beca3c7de1107d1e08` | `418770fc578166303f348432de6eada857ab5aed2a1b799c4c7bbb979d0895fb` | `4fbebf5dcd2ce411a66429ea18728da4d9066d2a6375174c6c2f5c6038f56868` | `e86c817b5ea853a84880697d83bf058320bf25f9f13d4632a5004396c657d198` | `5e537ff42f08eef8701479f8063299abbd2f78f9012c11ebecb9f6b2aac78264` |
| `briar_elk` | `8055b07c6b5ebc4072ecf83c454e99a0b4f498141d696bf5f5aaad0ad2f771e7` | `c52297993f3978f18cac5627e3622101d31e2b6f64a15c7c2ef33378c1037b3f` | `ec1a88f26b80399040ed8cb8a89894ecbce308a8613fd671340d28f86aa4a196` | `3ed684128872313f1423c5896d529f1f10e4c1805afd2a4429f3bfecb5de57a7` | `9955e6040615b584dc2935ce8ca6e6ffec1393f7f3e5f4c975256f17e9de3741` |
| `hollow_widow_spider` | `e8ecdc477de13d93ce6cd0e0d55503ab349f482a591d33afc027a6736f34f008` | `b412566f75b64cdfb16a26fbbd003963357cc13d3affeb30791d8315abb7c3d6` | `54becb1fac199b6dd30e27a529939bb47879539f19a462b20d8a7109836f727a` | `6e51def51c72f57a878284287c188f76eeb4b4e130db15638161a498fe8114c9` | `f74c68a21fd8a98edae7e57663747db47a04db109c196f777c04c4417ae4b9c4` |
| `rot_wolf` | `dc8d74cceb685ccacf7f7c4a5c0db6775ac62f6b9257515a6d2252b6f44c67d6` | `f47800e087eec57d5e61d1067cd3f22e7ea182dba064b3cd39052e35f5f63af2` | `f4564a9874314303668c8ea58da3f37d7686a373852cdad34f93f9e6bfd07d06` | `864c1bb44d2ce61963a7022def091fab24cfb28e52e4994ec706f00a6ffa3c0e` | `3abfa6c697d269f2a0aecccd5611c036678b1035d2337f31691f191fabc1bea3` |
| `thorn_stalker` | `c35a29da48cb3da995aa35b65845fa644c7e7495cfcce8516015e513723b1cfc` | `4544db6db3f6e1ebc97e6ec50cf8765125dfde487cfd9ecbb4615cd644af2071` | `9507b08d4b88229a82828988a894aad6dab678f63ca8edd678aa79e0cad9f802` | `cdd514a568aba8873ddb2312966cac59d08b6e1478501e89ea106227fb25634a` | `82f07e276e7710b8fa816b5104c61f2539812aad832264d0857d14c1f24c7741` |

## Targeted verification

```text
python3 -m unittest engineering/native-assets/whisperwood/entity-animation-repair-b/test_author_entity_animations.py -v
Ran 3 tests: PASS
```

All evidence JSON and `.bbmodel` files parse. All 29 timeline captures are
native PNG screenshots at 3456 by 2056 and are hash-bound in their receipts.

## Proof boundary

Status is `BLOCKBENCH_NATIVE_ENTITY_ANIMATION_AUTHORING_AND_CODEC_EXPORT_ONLY`.
This lane does not prove Bedrock client playback, server AI, navigation,
collision, hit timing, BDS behavior, controller behavior, multiplayer,
persistence, physical-console performance, or Marketplace acceptance.

Thorn Stalker animation lengths and poses are visual presentation values only.
They do not decide boss damage, hit timing, phase timing, reset rules,
multiplayer ownership, persistence, or rewards.
