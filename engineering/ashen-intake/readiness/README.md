# Ashen vertical readiness audit

This directory contains a point-in-time, audit-only reconciliation of Packet002
and the 14 Ashen Packet006 identities against immutable integration commit
`4e75503cc0597ba7e7ffe369a61e6db09212933a` and tree
`e4a94c579612030c6f853eac9d214153fb48ef95`.

The builder reads the pinned Git tree, not the mutable working tree. This keeps
the receipt historical and deterministic while later Ashen implementation
advances. It does not edit BP/RP, Creative, the decision ledger, proposals,
build tooling, validators, or qualification state.

Run the bounded checks:

```bash
python3 engineering/ashen-intake/readiness/build_ashen_vertical_readiness_audit.py
python3 -m unittest engineering/ashen-intake/readiness/test_ashen_vertical_readiness_audit.py
```

The report is source/static evidence only. No BDS, client, multiplayer,
controller, console, Marketplace, candidate, or release claim is made.
