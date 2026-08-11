# Crystal Marsh Codex / Progression Intake

Status: `APPEND_ONLY_CM_CODEX_INTAKE_SAFE_ROUTES_SEPARATED`

Base: `b4005112cf7ad347433ec3aa42bf7a761359b95d` / tree `6a2008f2a4f68859ef330a5b984af5eb8d9692c8`.

This is a deterministic intake map only. It changes no BP, RP, runtime, decision ledger, or qualification state.

## Exact append

| Page class | Count | Address treatment |
|---|---:|---|
| Packet 003 | 50 | CM-local category indices |
| Direct Packet 006 equipment | 11 | CM equipment indices 0-10 |
| Adjacent Packet 006 references | 2 | No CM address |
| Pearl Depths | 1 | CM boss index 0 |
| Chapter + Skyreach rumor | 2 | CM progression indices 0-1 |
| Packet discovery routes | 55 safe / 2 withheld | Decision-separated |

The exact 140-entry WW/AH prefix stays unchanged. Crystal appends 64 rows at global ordinals 140-203, yielding 204 registry entries. Registry version advances 3→4; state schema remains v4; all indices are region-local.

## Budget

No cap grows. Fully populated three-region compact discovery is 449 JSON bytes; all four preallocated regions remain 596 bytes, leaving 7596 bytes inside the 8192-byte player budget. Registry append growth in compact discovery storage is zero bytes.

## Boundaries

SAFE_NOW covers page/address scaffolding, ordinary discovery identities, nonnumeric relationship text, chapter entry, and a Codex-only Skyreach pointer from the ruined observatory. Physical maps/charts, final recipes/acquisition, Pearl Depths gameplay, numeric loot, seal/recovery semantics, and mastery rewards remain withheld behind the named Crystal proposals until ratified.

`W1-CREATIVE-005` remains deferred and receives no sidegrade page or event. The two dormant Ashen services remain final-integration dependencies only; no Crystal page or event calls them.

## Proof boundary

Tests prove exact 50+11+1+2 coverage, the hash-bound 140-entry prefix, append-only CM indices, unchanged caps/schema, computed budget, blocker separation, and byte-deterministic regeneration. They do not prove runtime append/wiring, UI, acquisition, boss behavior, persistence migration, BP/RP integration, BDS, client, multiplayer, or console behavior.
