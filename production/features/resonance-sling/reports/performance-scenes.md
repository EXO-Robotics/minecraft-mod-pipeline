# Resonance Sling performance model

These are BDS observations and enforced workload bounds, not PS4 frame-rate or memory claims.

| Named scene | Bound | Evidence |
|---|---:|---|
| One player firing normally | 1 projectile / activation | Native use, ammunition, durability, owner, damage, knockback, and cleanup probes passed |
| One player at maximum valid rate | 4 live projectiles / owner | Production owner map rejects a fifth owned projectile; no unbounded collection |
| Four players firing concurrently | 4 simultaneous activations | Four spawns and ammunition deltas `1,1,1,1` |
| Ordinary ambient entities | 24 pigs + bounded projectiles | Worst-credible fixture passed with 24 ambient entities and 16 live projectiles |
| Disconnect during flight | 60-tick backstop | Disconnect cleanup and reconnect-with-no-state probes passed |
| Repeated firing then cleanup | 0 remaining | Rapid alternating use and repeated-use cleanup passed |
| Restart after active use | 0 restored | Preview cycle 2 found no persistent projectiles; stable BDS started cleanly three times |
| Long-duration repeated-use soak | 100 rounds / 400 attempts | Four-player endurance passed; queue peak 15; final projectile count 0 |

## Frozen workload values

- Projectile lifetime: 60 ticks.
- Maximum live projectiles: 4 per real owner, 16 globally.
- Production callbacks: one `entitySpawn` callback and one `entityRemove` callback per projectile, plus one scheduled timeout backstop.
- Global queries per activation or tick: 0.
- Scheduled production work per accepted activation: 1 bounded timeout.
- Impact particles: 6.
- Animation controllers: 1.
- Persistent records: 0.
- Diagnostic scheduled-queue peak: 15.
- Cleanup latency: immediate on impact, otherwise at most 60 ticks.

## Runtime observations

- Stable BDS 1.26.33.2: 3 clean cycles, 63.574 seconds total, 144 normalized log lines, 0 critical lines.
- Preview BDS 1.26.50.20: 2 clean cycles, 193.037 seconds total, 144 normalized log lines, 31 passed probes, 0 failed probes, and 0 critical lines.
- Worst-credible scene: 4 SimulatedPlayers present, 24 ambient entities, 20 stationary projectile attempts, 16 retained by the production cap.
- Endurance scene: 100 rounds, 400 use attempts, queue peak 15, cleanup to zero, then restart with zero restored projectiles.

BDS did not provide trustworthy PS4 graphics memory, frame pacing, controller latency, split-screen, or television-readability measurements. Those remain physical-hardware work.
