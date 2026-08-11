# Whisperwood Checkpoint 1 result

Status: **PASS**

R2 commit `32991302f2aaafefd34a292caacde89275b70ee7` built twice to the exact `.mcaddon` SHA-256 `b05d0d17d379c2ef2667400360ec7a01d017e99db0c410dd6c226705a2a05096`.

Stable BDS 1.26.33.2 loaded the exact package twice, observed the shipped `runtime-ready-g8` entrypoint marker in both cycles, shut down cleanly twice, and reopened the same world. The four R1 duplicate-recipe warnings are absent. No candidate-scoped warning or error remains; the only warning line is the intentional startup marker emitted through `console.warn`.

The Whisperwood normalization and server-side implementation pattern is authorized for reuse in Ashen Highlands.

This does not prove live natural spawning, pathfinding, structure placement, harvesting, client rendering, audio, multiplayer, controller, physical console, Realm, Marketplace, or release readiness.
