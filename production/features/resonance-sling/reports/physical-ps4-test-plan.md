# Physical PS4 certification plan

Status: `PENDING_PHYSICAL_HARDWARE`.

Use only the frozen unchanged `.mcworld`:

- File: `production/features/resonance-sling/dist/resonance-sling-INTERNAL-TEST.mcworld`
- SHA-256: `061501b67b0886296ad2765f1b7c5246efbe38d64b9494303a05b9ee81a58d9a`
- Manifest revision: 3
- Pack version: `1.0.0`

- Import through the supported Realm transfer path and confirm both packs download.
- Use controller only to craft the Sling and Pebbles, fire, observe empty-ammo and cooldown feedback, and deplete durability.
- Inspect inventory icon, first-person and third-person silhouette, projectile visibility, particles, clipping, and television-distance readability.
- Exercise single-player, online multiplayer, and split-screen where supported.
- Fire at entities and blocks; verify one damage event, bounded knockback, correct ownership, and no friendly-fire surprise.
- Fire at the maximum valid rate for each player; record frame pacing, input latency, projectile visibility, and cleanup.
- Exercise the worst-credible scene with four players, 24 ordinary mobs, and up to 16 live projectiles; record frame pacing and particle readability.
- Disconnect, die, change dimension, reconnect, save/reload, and restart while projectiles are active.
- Run sustained repeated use, then verify no leftover projectiles, state, or save growth.
- Uninstall/reinstall the package and confirm the frozen test world remains recoverable.

Record console model, system version, Minecraft version, artifact SHA-256, player count, duration, observed entity counts, video/screenshots, content errors, and a pass/fail decision for every row.
