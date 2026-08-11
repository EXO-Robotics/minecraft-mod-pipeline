# Wave 1 Codex v4 foundation

Status: `TARGETED_LOCAL_SEMANTIC_PASS`

Base authority: integration commit `1c4e0feae68c9d2bd93044d581edca53fcf2be53` and `WHISPERWOOD_CODEX_IMPLEMENTATION_MAP.json` SHA-256 `d9c1f4c5ad4fbc66afa284da4d2bcc03424b22d6f43c49c5ec76d99198cbc9bf`.

## Implemented boundary

- State schema advances from v3 to v4 at new dynamic-property keys; frozen v3 values remain readable and are not deleted.
- v3 stamps, `codex.topic`, goal booleans, and other player/world domains are preserved. Recognized canonical Codex stamps are additionally translated into compact discovery state without removing the legacy stamp.
- Discovery is registry-versioned and stored as two-bit monotonic states (`0` locked, `1` partial, `2` complete) under `player.codex.discovery.<region>.<category>`.
- The fixed Wave 1 foundation admits four regions (`ww`, `ah`, `cm`, `sr`) and category caps totaling 40 entries per region. A fully populated four-region discovery object is 280 JSON bytes, below 4% of the 8,192-byte player budget.
- All 40 SAFE_NOW Whisperwood entries and all 43 exact canonical event IDs from the implementation map are bound. Unknown IDs and invalid coordinates are rejected; duplicate and lower-stage transitions do not write or downgrade state.
- The Codex service exposes silent event translation. No new chat output, server-ui dependency, event subscription, acquisition claim, or blocked guidance was added.

## Evidence

```text
node --test tests/wave1_codex_v4.test.mjs tests/g7_runtime_semantics.test.mjs
21 tests, 21 pass, 0 fail

python3 -m unittest engineering/whisperwood-intake/codex/test_whisperwood_codex_map.py -v
6 tests, 6 pass, 0 fail
```

Covered assertions include exact map/registry parity, v3-to-v4 idempotence, v4 reopen, prior world/player domain preservation, recognized legacy-stamp translation, compact byte bounds, monotonic partial-to-complete transitions, duplicate discovery, unknown IDs, and unchanged stable-API/subscription semantics.

## Proof boundary

This is source-level and Node/Python semantic evidence only. It does not prove event wiring, a Codex UI, live acquisition, BP/RP packaging, deterministic builds, Stable BDS, Bedrock client behavior, multiplayer, console behavior, or candidate readiness. Those remain owned by later integration and qualification gates.
