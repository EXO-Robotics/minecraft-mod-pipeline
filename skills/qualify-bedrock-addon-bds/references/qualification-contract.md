# Exact-package BDS qualification contract

## Required receipt bindings

- Candidate repository and full commit.
- Candidate Git tree.
- Package path at commit.
- Package SHA-256 and size.
- Deterministic rebuild result.
- MCTools version, command, exit code, errors, warnings, and log hash.
- Docker image by immutable platform-specific digest.
- Host, Docker server, image, and BDS binary architectures.
- Stable and Preview versions and binary hashes.
- Generated world hash and Stable-saved Preview input hash.
- Declared restart count and every cycle result.
- Script-marker policy and console/log probes.
- Explicit false claims for client, multiplayer, controller, Realm,
  split-screen, and physical console.

When the BDS harness cannot emit all fields in one receipt, freeze a
`qualification-metadata.json` beside it. The metadata must hash-bind the
original receipt and package, and the validator must require both files. Do not
silently infer missing fields from prose.

## Passed cycle

A cycle passes only when:

- The exact requested BDS version starts.
- `Server started` is observed.
- The content log has zero critical lines.
- Required script marker is observed, or asset-only policy is explicit.
- Every declared bounded console/log probe matches.
- Timeout is false.
- Shutdown behavior is recorded separately from startup.

## Nondeterminism

An unchanged-byte failure is a gate failure even if later unchanged attempts
pass. Preserve the sequence. Diagnose under a separate control ledger and
require a material candidate, runner, or architecture change before opening a
new qualification ledger.
