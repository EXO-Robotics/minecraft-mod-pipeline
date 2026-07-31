# Exact tester poison-intake replay

## Scope

This report covers only
`MSG-T01-APERTURE-BDS-000030`, committed at
`bd0941ed7547de4b0b1b5b999fe8a02b3cfa1beb` as
`tester_intake/aperture-foundry/MSG-T01-APERTURE-BDS-000030.json`, with raw
SHA-256
`3895ed3602c94686acb2f68b482655b54012fe6dd8dc74f339be65cec934d15a`.

The intake is preserved as invalid historical authority. It was rejected before
staging or BDS execution because its outer idempotency key was noncanonical.
The compatibility ledger does not validate or rewrite it.

## Supersession

The exact unchanged candidate was resubmitted by
`MSG-T01-APERTURE-BDS-RETRY-000031`:

- original terminal infrastructure result:
  `MSG-TESTER-APERTURE-BDS-000030-INFRASTRUCTURE`
- original terminal result commit:
  `503f1c23d442c6af7426d3998e6ca4c4d18da6df`
- original terminal result raw SHA-256:
  `0bc566dd6296af882e5b7f763851371e2c516ca9cc1f8d2592d140b5a191b082`
- commit: `9416b3b109c2f6592762ba725ca458e29d152a78`
- raw message SHA-256:
  `51a623d8901f555e5fece92fca93a2cb11f8869b870797e1663ec8667848ebaa`
- terminal result: `MSG-TESTER-000000000030-PASS`
- terminal result commit: `28caea6301495b5b3079060e054f1bed5abd9a09`
- terminal result raw SHA-256:
  `8a663b4f0e9724c670e80b041034f7486508fddca16a73707ac4a6dc16375a1c`

The original intake is therefore `INVALID_SUPERSEDED_TERMINAL` and its replay
behavior is `NEVER_EXECUTE_ADVANCE_DISCOVERY`.

## Runtime reconstruction

The tester now rebuilds terminal intake state from committed tester results
before dispatch selection. Exact compatibility dispositions remove any stale
runtime job for the invalid intake. The valid retry is reconstructed as
terminal from its committed result and cannot be selected or re-executed even
if ignored runtime state is absent.

A newly invalid intake is recorded as a pack-local runtime rejection and does
not prevent a later valid intake from being validated and dispatched. No new
invalid intake receives the historical exception.

## Proof boundary

This is tester discovery, replay, and duplicate-execution evidence only. It
does not rerun BDS, qualify another candidate, alter product authority, or
establish client, multiplayer, controller, console, rights, Marketplace,
integration, or release proof.
