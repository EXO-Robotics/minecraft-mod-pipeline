# Clockwork Gardens case study

Clockwork Gardens is an original integration benchmark, not a converted third-party mod. It proves that the generated/runtime architecture can compose ten bounded behaviors:

1. Verdant staff item use and cooldown/effect path.
2. Gearseed use on block.
3. Projectile creation and launch.
4. Entity and block projectile impacts plus cleanup.
5. Effects and immediate/delayed observations.
6. Progression state.
7. One bounded machine-processing cycle.
8. Form-oriented block interaction.
9. Growing-entity and lifecycle transitions.
10. Hit/hurt/death adapters and a scheduled three-phase boss with restart checkpoint.

## Evidence boundary

| Layer | Proven |
|---|---|
| Internal handlers/tests | Generated handler structure, deterministic state transitions, package/static checks |
| Event adapters | Item use/use-on-block, block interaction, projectile entity/block impacts, hit/hurt/death, spawn/lifecycle |
| Preview SimulatedPlayer/GameTest | Diagnostic item, projectile, combat and interaction actions |
| Stable BDS | Exact pack/world boot, script initialization, clean shutdown |
| Preview BDS | The richer diagnostic actions, direct effect API observations, machine/progression/growth/boss phases, diagnostic restart |
| Pending physical client | Generated launcher chain, real item/effect/cooldown/form/combat interaction |
| Pending multiplayer | Two-player isolation, attribution, contention and scaling |
| Pending console | Controller, Realm, PlayStation/Xbox, split-screen and performance |

The authoritative receipt is `benchmarks/original-marketplace-showcase/bds-diagnostic-validation.json`. Its `gameplay_verified`, broad persistence, multiplayer, Realm, and console fields remain false. `projectile_slowness_action_verified` is false, and a hostile-damage assertion conflicts with a broader test contract; the narrower primary receipt governs. Creator Tools reports zero errors/warnings for the exact archive but does not establish runtime or Marketplace approval.

Reusable patterns include stable event adapters, projectile ownership/collision/cleanup, bounded status effects and cooldowns, versioned progression flags, scheduled machine work, form-oriented interaction, entity phase state, lifecycle wiring, and three-phase boss scheduling.
