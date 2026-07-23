# Resonance Sling performance model

These are enforced workload bounds and BDS observations, not PS4 performance claims.

| Scene | Planned maximum | Measured / modeled observation |
|---|---:|---|
| One player, normal | 1 live projectile | One spawn and one 60-tick timeout per activation |
| One player, maximum valid rate | 4 live projectiles | Owner cap rejects the fifth |
| Four concurrent players | 16 live projectiles | Global cap rejects the seventeenth |
| Ambient entities | 16 live projectiles | No ambient-entity scan; collision events only |
| Disconnect in flight | 16 live projectiles | Invalid owner prevents damage; timeout remains |
| Repeated fire then cleanup | 0 after 60 ticks | Impact or timer removal; no persistent record |
| Restart after active use | 0 restored records | Three clean BDS restarts; persistent-record count is zero |
| Long-duration soak | Not executed | Requires player automation; pending Preview or real clients |

Per activation: one inventory traversal bounded by container size, one entity spawn, one scheduled timeout, no global query. Per impact: one event callback, at most one damage, one impulse, six particles, one sound at activation, and immediate removal.

Stable BDS 1.26.33.2 observations: three clean starts, no critical content-log lines, 83.646 seconds total harness time, and 146 normalized aggregate log lines. This does not predict PS4 frame pacing, graphics memory, or controller latency.
