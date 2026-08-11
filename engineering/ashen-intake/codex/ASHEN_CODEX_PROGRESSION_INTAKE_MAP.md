# Ashen Codex / Progression Intake Map

Status: `HASH_BOUND_INTAKE_MAP_SAFE_ROUTES_SEPARATED`

This is a deterministic intake map only. It adds no runtime, BP/RP, Creative decision, build, BDS, or candidate evidence.

## Exact coverage

| Scope | Count | Disposition |
|---|---:|---|
| Packet 002 warehouse IDs | 50 | Indexed exactly |
| Packet 006 Ashen links | 14 | 13 new pages; existing `briar_ring` page referenced |
| Kiln Sky | 1 boss page | Identity only; executable events withheld |
| Progression | 2 pages | Ashen chapter + Crystal Marsh rumor |
| Packet event routes | 49 safe / 2 withheld | Decision-separated |

## Append-only proposal

Registry version advances from 2 to 3; state schema remains v4. Existing 74 rows and all Whisperwood addresses stay byte-identical. Ashen adds 66 rows, producing 140 total. Category indices become explicitly region-local when runtime data is later appended.

No cap grows: resource 20 already covers 10 resources plus 10 blocks; equipment 21 covers the 14 links; creature/plant/structure 10, boss 1, and progression 2 already fit. The fully populated four-region discovery object remains 596 JSON bytes under the 8192-byte player budget.

## Progression invariants

- The existing Whisperwood hint remains exactly: “Heat waits east of the burned wagons.” It is an invitation only.
- Ashen chapter entry is soft and sandbox-compatible.
- `ash_drake_horn` is the primary critical Chapter 2 seal.
- `ember_forge_core` remains a secondary trophy/structure reward and approved pilgrim-part identity; it never substitutes for the chapter seal.
- The Crystal Marsh rumor is Codex/recognized-structure state only; physical teaser-map loot is withheld.

## Blocking boundary

- `W1-CREATIVE-001-AH`: no deferred non-warehouse term becomes an item or acquisition predicate.
- `W1-CREATIVE-003-KILN-SKY`: no executable boss thresholds, timing, reset, ownership, persistence, terminal, recovery, or repeat semantics.
- `W1-CREATIVE-004-AH`: no numeric loot/reward route or alternate-seal behavior.
- `W1-CREATIVE-005`: no `briar_ring` temper sidegrade identity or representation.

## Proof boundary

The tests prove roster/link coverage, authority hashes, append-only address rules, unchanged caps/budget, blocker separation, seal semantics, and deterministic regeneration. They do not prove runtime wiring, live gameplay, persistence migration, packaging, BDS, client, multiplayer, or console behavior.
