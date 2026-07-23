# Physical PS4 certification plan

Status: `PENDING_PHYSICAL_HARDWARE`.

Use only the frozen unchanged `.mcworld` hash recorded in `artifact-manifest.json`.

- Import through the supported Realm transfer path and confirm both packs download.
- Use controller only to craft the Sling and Pebbles, fire, observe empty-ammo and cooldown feedback, and deplete durability.
- Inspect inventory icon, first-person and third-person silhouette, projectile visibility, particles, clipping, and television-distance readability.
- Exercise single-player, online multiplayer, and split-screen where supported.
- Fire at entities and blocks; verify one damage event, bounded knockback, correct ownership, and no friendly-fire surprise.
- Fire at the maximum valid rate for each player; record frame pacing, input latency, projectile visibility, and cleanup.
- Disconnect, die, change dimension, reconnect, save/reload, and restart while projectiles are active.
- Run sustained repeated use, then verify no leftover projectiles, state, or save growth.
- Uninstall/reinstall the package and confirm the frozen test world remains recoverable.

Record console model, system version, Minecraft version, artifact SHA-256, player count, duration, observed entity counts, video/screenshots, content errors, and a pass/fail decision for every row.
