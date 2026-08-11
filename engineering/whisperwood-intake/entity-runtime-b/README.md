# Whisperwood Entity Runtime B

This lane integrates `bark_wraith`, `briar_elk`, `hollow_widow_spider`,
`rot_wolf`, and the non-boss `thorn_stalker` shell from the native PASS evidence
at base commit `0667d65`.

All shipping geometry and animation identifiers are normalized from
`aionforge_ww` to `aionbound`. The remaining geometry, UV, texture, and
animation content is derived from the two-pass native Blockbench exports.

The entities include movement, navigation, idle motion, target/retaliation
policy, attack behavior, hurt/death presentation, bounded spawn weights and
distance despawn. These are static integration facts, not observed runtime
proof. Numeric values are provisional engineering tuning for Checkpoint 1.

Loot is deliberately absent. Creative tickets `W1-CREATIVE-001` and
`W1-CREATIVE-004` still govern identity and probability. The regular ecology
Thorn Stalker cannot award the chapter seal.

## Thorn Stalker boundary

`aionbound:thorn_stalker` is classified as `BASE_HOSTILE_SHELL_ONLY`. Its
presence must never satisfy a boss-completion or chapter-apex check. Phases,
thresholds, timing, special attacks, adds, reset, multiplayer ownership,
persistence, and terminal rewards are withheld under `W1-CREATIVE-003` and
`W1-CREATIVE-004`.

Run the bounded validator with:

```sh
python3 engineering/whisperwood-intake/entity-runtime-b/test_entity_runtime_b.py
```

The validator does not build a package and does not run BDS.
