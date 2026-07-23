# Forest Wave 1 Parallel Batch 1 — Local Qualification

Status: `INTERNAL_BATCH_CHECKPOINT_FROZEN_CLIENT_AND_PS4_GATES_PENDING`

Five isolated `gpt-5.6-sol` production agents were launched across two maximum-concurrency waves, with up to three production agents active simultaneously. The requested child effort label `light` was not supported by the runtime; the closest available level, `low`, was used and recorded. No child was escalated, accepted its own work, or integrated its own candidate.

Main Codex independently reviewed every candidate, serialized the authoritative Blockbench GUI inspection, repaired generator-level defects, assembled six Behavior/Resource Pack pairs including the protected Resonance Sling, and ran the authoritative servers.

## Evidence

- Repository suite: 366 passed, 1 skipped, and 107 subtests passed.
- Stable BDS 1.26.33.2: three clean restart cycles, 79.925 seconds total, classified as boot/restart diagnostic evidence.
- Preview BDS 1.26.50.20: two clean cycles, 193.518 seconds total, classified as diagnostic SimulatedPlayer evidence.
- Preview load: four SimulatedPlayers, 20 Gloamwings, 20 Mossbacks, two Signal Ruin anchors, 16 capped Resonance projectiles, and 24 ambient entities.
- Cleanup: all diagnostic custom entities, encounter entities, projectiles, and ambient proxies removed.
- Restart: world checkpoint and zero-stale-entity state recovered.
- Blockbench 5.1.5: Gloamwing, Mossback, and Barkguard native projects opened and round-tripped with matching identifiers, bone names, cube counts, and zero remaining warnings.

## SimulatedPlayer boundaries

Preview BDS verified creation, four-player isolation, bounded load, projectile caps, cleanup, and world restart state. It also reproduced documented GameTest limitations:

- Simulated item use was accepted but did not deliver a normal production item-use event payload.
- Simulated damage was accepted but did not deliver a normal production damage event payload.
- Simulated entity interaction was accepted but did not deliver the production interaction event.
- Recreating a SimulatedPlayer after server restart did not recover the prior player identity record.

These are recorded as harness limitations, not as gameplay passes. Real item activation, damage activation, interaction activation, player reconnect persistence, desktop rendering, controller behavior, split screen, Realm behavior, and physical PS4 performance remain pending.

## External red-team disposition

The explicitly authorized Grok 4.5 review completed against a sanitized six-file, text-only disclosure bundle. The bundle manifest, exact configuration, two incomplete six-turn attempts, successful raw output, model/usage metadata, and all 16 finding dispositions are retained under `red-team/`.

Grok reported five high, seven medium, two low, and two informational findings. Main Codex independently verified each. The stale-digest, Signal Ruin periodic scan, and reward crash-window high findings were accepted and repaired; the activation-race claim was rejected because the synchronous callback contains no yield, with an immediate reservation added as defense in depth; the BDS overstatement claim was rejected because the existing report already labels those gates as diagnostic and lists the missing production events. No accepted critical or high finding remains unresolved.

Medium/lower findings that require real client evidence remain explicit limitations rather than passes, including Mossback simultaneous interaction, Gloamwing combat transitions, Barkguard partial API failure behavior, exact-minimum engine compatibility, and Forest biome/reset client behavior.

Creator Tools was unavailable and is recorded as `NOT_EXECUTED_ENVIRONMENT_UNAVAILABLE`.

The internal batch checkpoint is accepted for integration. This is not gameplay certification, Marketplace readiness, or PS4 compatibility. No push, tag, release, Realm deployment, Marketplace submission, or physical PS4 claim occurred.
