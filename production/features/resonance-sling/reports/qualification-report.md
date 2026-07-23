# Resonance Sling qualification report

Status: qualified internal production slice. Publication, Marketplace, desktop-client, and physical-platform claims remain blocked.

## Gate matrix

| Gate | Status | Evidence |
|---|---|---|
| Static validation | PASS | `UV_CACHE_DIR=/tmp/resonance-sling-uv-cache uv run --offline pytest -q tests/test_resonance_sling.py` returned `4 passed`; two consecutive builds produced identical package hashes |
| Blockbench authoring | PASS | Both editable projects were reopened and saved in Blockbench 5.1.5 and exported through its native Bedrock codec; the Sling export has 6 cubes, 4 named bones, and 2 true locators; the projectile export has 1 cube |
| Bedrock Creator Tools | NOT_EXECUTED_ENVIRONMENT_UNAVAILABLE | No compatible `addon` / `currentplatform` Creator Tools session was available |
| Stable BDS pack boot and restart | PASS | Pinned stable BDS 1.26.33.2 booted the exact `.mcworld` cleanly three times; all three Script API 2.0.0 initialization probes passed |
| Preview BDS gameplay diagnostic | PASS | Preview BDS 1.26.50.20 and the never-ship GameTest pack passed 27 cycle-1 gameplay/load checks and the cycle-2 restart check |
| Desktop client | NOT_EXECUTED_ENVIRONMENT_UNAVAILABLE | No compatible Bedrock desktop-client session was connected |
| Multiplayer | PASS | Four SimulatedPlayers verified simultaneous use, independent ammunition/cooldowns, owner attribution, disconnect, death, reconnect, rapid alternating use, and cleanup |
| Physical PS4 | PENDING_PHYSICAL_HARDWARE | See `physical-ps4-test-plan.md` |

Stable BDS PASS is limited to production-pack loading and restart. Player actions are proven separately by the Preview-only SimulatedPlayer diagnostic; its beta GameTest dependency is not present in either shipped pack.

## Qualified behavior

- Native hold/release shooter path with a 14-tick maximum draw.
- One Resonance Pebble consumed and one durability point charged per valid activation.
- Empty ammunition produces no shot, ammunition cost, or durability cost.
- Native projectile owner attribution, nominal component damage 4, bounded native knockback, six impact particles, and one damage event.
- Native entity/block impact removal plus a 60-tick timer backstop.
- Owner cap 4 and global cap 16; a 20-projectile stationary load fixture stabilized at 16.
- Four-player simultaneous activation produced four projectiles and four independent one-ammunition deltas.
- 100 endurance rounds across four SimulatedPlayers produced 400 attempts, a diagnostic scheduled-queue peak of 15, and cleanup to zero.
- Dimension transition retained no projectile beyond the 60-tick backstop, and native damage attribution resolved through the projectile-owner chain.
- Restart restored zero projectile or script records.
- Zero persistent records, dynamic properties in production, full-world per-tick queries, or per-tick loops.

## Repair record

1. Stable recipe load initially failed because modern recipes require unlock data. Added amethyst-shard unlock conditions and reran stable BDS.
2. Stable initialization recognition failed because the shared analyzer requires an explicit runtime-initialized phrase. Made the initialization receipt explicit and reran.
3. Preview rejected `random.orb` as an invalid `LevelSoundEvent`. Removed the invalid start sound and kept sound deferred.
4. Preview SimulatedPlayer did not implement the guessed `stopItemUse`; official GameTest documentation identified `stopUsingItem`. Corrected the diagnostic API.
5. Scripted post-impact mutation encountered invalidated projectile handles. Moved damage, knockback, particle, and removal behavior into native `minecraft:projectile.on_hit`; retained script only for caps and removal bookkeeping.
6. Ownerless projectiles were incorrectly sharing an artificial four-projectile owner cap. Applied the per-owner cap only when a real owner exists while retaining the global cap for every projectile.
7. Repeated stable restarts depended on repeated external BDS version lookup. Added ignored, version-specific server seeds so all restart cycles use the same fixed binary.
8. The shared 30-second BDS observation ceiling could not represent endurance. Raised the bounded ceiling to 120 seconds and executed a 100-round, four-player endurance scene.

## Technical boundaries

- Headless stable BDS cannot create player actors. Stable pack/restart evidence and Preview SimulatedPlayer gameplay evidence therefore remain separate.
- Native projectile damage is velocity-scaled. The manifest freezes component damage 4 and power multiplier 0.23; the qualification accepts the measured bounded 3.5–5.5 range rather than claiming an exact floating-point health delta.
- Blockbench round-trip is authoring evidence, not Bedrock client rendering evidence.

## Stop-condition report

No mandatory stop condition was triggered. Runtime-integrity risk was approached by invalid post-impact handles and repaired by moving impact behavior to native components. No contamination, experimental production API, dependency escape, runaway spawn, duplicate damage, persistent leakage, or world-save corruption was observed.
