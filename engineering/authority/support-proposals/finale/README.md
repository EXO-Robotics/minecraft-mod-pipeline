# Wave 1 finale/Twinbond support proposals

This directory contains the minimum approval-ready authority closure for the remaining finale decisions:

- `W1-002-TWINBOND`: same-world authored container, exact prepared inputs, Concord Spark/Memory/mastery presentation, and machine-exit dependency;
- `W1-003-TWINBOND`: four-phase behavior, timing, reset, multiplayer ownership, existing-schema persistence, and valid terminal semantics;
- `W1-004-TWINBOND`: guaranteed first-clear package, duplicate guards, full-inventory recovery, and repeat-clear disposition.

All three are `PROPOSED_NOT_RATIFIED`. Their exact JSON bytes have no authority effect until explicitly ratified into a replacement Wave 1 engineering decision ledger. They do not modify Creative, G7/G8 product bytes, runtime, packs, assets, builds, or qualification evidence.

The builder deterministically regenerates the JSON and Markdown siblings:

```sh
python3 engineering/authority/support-proposals/finale/build_finale_support_proposals.py
python3 engineering/authority/support-proposals/finale/test_finale_support_proposals.py
```

W1-CREATIVE-005 remains deferred. Native repair/qualification for both wyrms and `twinbond_relic`, plus the ordinary Asset qualification for the Memory icon, remain separate execution gates.
