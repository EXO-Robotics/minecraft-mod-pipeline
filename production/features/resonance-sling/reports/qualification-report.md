# Resonance Sling qualification report

Status: internal production checkpoint. Publication and physical-platform claims remain blocked.

## Gate matrix

| Gate | Status | Evidence |
|---|---|---|
| Static validation | PASS | `tests/test_resonance_sling.py`; deterministic second build produced identical hashes |
| Creator Tools / Blockbench runtime | NOT_EXECUTED_ENVIRONMENT_UNAVAILABLE | Editable sources are retained, but no Bedrock client content-log or native Blockbench export receipt was captured |
| Stable BDS pack boot and restart | PASS | Pinned BDS 1.26.33.2 booted cleanly three times and initialized Script API 2.0.0 |
| Stable BDS gameplay | BLOCKED | Stable headless BDS supplies no player actor. It cannot exercise item-use, player inventory, owner attribution, or controller input by itself |
| Desktop client | NOT_EXECUTED_ENVIRONMENT_UNAVAILABLE | No compatible Bedrock desktop-client session was connected |
| Multiplayer | NOT_EXECUTED_ENVIRONMENT_UNAVAILABLE | No real clients or feature-specific Preview SimulatedPlayer harness were executed |
| Physical PS4 | PENDING_PHYSICAL_HARDWARE | See `physical-ps4-test-plan.md` |

The stable-BDS PASS is deliberately limited to clean pack loading, script initialization, and restart behavior. It is not represented as gameplay or multiplayer proof.

## Static and architecture evidence

- One stable `itemUse` activation path.
- One projectile per valid activation.
- Owner-scoped inventory, cooldown, durability, and active-count handling.
- Entity and block impacts are separate stable events guarded by projectile ID.
- Immediate impact cleanup plus a 60-tick timeout.
- Four live projectiles per owner and sixteen globally.
- Zero dynamic properties, persistent records, full-world queries, or per-tick loops.
- Six particles per impact and one resource-pack entity geometry.

## Repairs

1. Gate: Stable BDS. Failure: both recipes were rejected because 1.20+ recipes require unlock data. Cause: missing `unlock` arrays. Repair: added amethyst-shard unlock conditions to both recipes and rebuilt. Rerun: clean content log and three successful restart cycles.
2. Gate: Stable BDS adapter. Failure: the harness did not recognize script initialization despite the feature log probe matching. Cause: the shared analyzer accepts the phrases `runtime initialized` or `script runtime initialized`. Repair: made the initialization receipt explicit. Rerun: all three cycles passed.

## Technical boundary

The pinned stable API catalog contains `world.afterEvents.itemUse`, but no portable stable start-use/release-use pair. The frozen design therefore uses tap activation. This preserves controller accessibility and avoids an experimental API.

Headless stable BDS also has no native player-generation facility. Player-owned gameplay and multiplayer claims require a Preview SimulatedPlayer diagnostic or real clients. Those claims remain unexecuted, not inferred from code.

## Stop-condition report

No stable-API stop condition blocks the selected tap-to-fire product role. A qualification boundary was approached for headless player and multiplayer evidence; the affected gates remain explicitly unexecuted.
