# Whisperwood Entity Runtime A Report

Status: **PASS**

Scope: five native-PASS ordinary creatures: lantern_hare, mosskip_buck, mosskip_doe, mosskip_fawn, rootback_boar.

## What this lane binds

- Exact native-export geometry, animation JSON, and 32x32 RGBA texture bytes, normalized from `aionforge_ww` to `aionbound.whisperwood` runtime identifiers.
- One server entity, client entity, animation controller, render controller, and conservative natural spawn rule per creature, with per-type surface density two, 24-96 block spawn distance, and 32-96 block standard despawn distance.
- Ambient damage-triggered panic for the hare/fawn/doe; retaliatory target acquisition and melee pursuit for the buck/boar.
- Idle, locomotion, hurt, and death clips through per-entity controllers. Remaining approved clips are registered as aliases but not assigned fabricated triggers.
- No loot component or loot table.

## Evidence-derived checks

`python3 engineering/whisperwood-intake/entity-runtime-a/test_entity_runtime_a.py` exited 0 and its captured output SHA-256 is `53f091ce6b8683a791aa321864e05c235b88a702ea3404e981db954bd800559a`.

All five static test groups passed: native byte binding, cross-file identifier and animation closure, non-statue AI structure, bounded spawn envelopes, and full PNG decode/atlas matching.

## Preserved gaps

- W1-CREATIVE-001 and W1-CREATIVE-004 still block loot identity/probability wiring.
- Declarative spawn rules approximate approved ecology with low-weight forest/night or forest/day envelopes; they do not claim proximity to a particular plant, prop, trail, or another custom species.
- Mosskip herd-defense behavior and special action triggers remain withheld instead of being invented.

## Proof boundary

This is source-tree static validation backed by existing native Blockbench receipts. It is not Creator Tools, package, Stable BDS, client rendering/animation/pathfinding/combat, persistence, multiplayer, physical-console, Marketplace, or release proof.
