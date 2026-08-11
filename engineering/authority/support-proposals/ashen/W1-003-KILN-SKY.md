# W1-003-KILN-SKY — Ashen support proposal

**Status:** `PROPOSED_NOT_RATIFIED`
**Authority effect:** none until an explicit replacement decision ledger ratifies this ticket.

This proposal is Ashen-only. It does not edit Creative sources, prior proposals, the decision ledger, BP, or RP.

## Minimal executable envelope

The proposal binds only the approved four phase identities and six attack identities to proposed thresholds, timing ranges, reset/leash behavior, bounded adds, multiplayer ownership, persistence, and terminal/repeat semantics.

Pull-time health scaling and the terminal reward set are separate, hard-capped at four unique players, and late join never rescales health. Late join is an automatic 15-second continuous-residency predicate available only before Glass Wing; all pending timers are cancelled on Glass Wing entry.

Terminal eligibility, voluntary abandonment, disconnect/reset precedence, exact phase inclusivity, cooldown composition, bounded no-queue Ash Mites, ecology-form prohibitions, and ordered idempotent seal-credit/entitlement/physical-claim semantics are explicit in the canonical JSON.

Every new number remains `PROPOSED_NOT_RATIFIED`. Damage values, attack radii, and an arena-radius number are deliberately not invented; implementation uses the authored arena volume and requires separately approved/measured Engineering constraints for mechanical tuning.

## Source binding

Base commit `faf8bab1785b3b847a70268c37ef813afd0495b4`; base tree `3162be09bb1cb1b4ca10f1bf8132fbbf5e595282`.

- `04f7b9a75be6ac542d3488bd7563a601dcb94603905479b7c3e766c94b9d48c1` — `engineering/authority/support-proposals/W1-CREATIVE-003/thorn_court_behavior_proposal.json`
- `3e2b64785da9310b098e06981ebc95777ddc7e5d2666f803b79ce374470a9561` — `engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json`
- `5ef85e1e0b29973a617f7dca4a8b119443c01644ba33f0e11166ef8d417d5a6f` — `program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md`
- `4d80925a113bb0cca67e2405047cd228a2df2ccd2c680e1e51ccd04b6f2d63d8` — `program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md`
- `aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5` — `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json`
- `3116c217e06afe1fd0cd56ee742c537f948a4c91193ec831fd1b3ec362837bfc` — `program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md`

The sibling JSON is canonical.
