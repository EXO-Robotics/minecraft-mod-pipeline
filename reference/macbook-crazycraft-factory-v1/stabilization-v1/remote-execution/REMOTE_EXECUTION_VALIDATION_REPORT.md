# Crazy Craft remote execution validation

## Verdict

The bounded MacBook-to-Mac-Studio execution substrate is deployed and has
executed live synthetic T1, T10, denial, receipt, and parallel-container
tests. Campaign production remains paused because same-user credential custody,
OS-enforced evidence/oracle separation, and exact Stable/Preview BDS runtime
qualification are not established.

Classification:

`REMOTE_EXECUTION_LIVE_SUBSTRATE_ACTIVE_PRODUCTION_RESUME_BLOCKED`

Implementation authority:

- commit: `62cd0cd42403612060aedad5f5cce738529b5806`
- tree: `1e3b1ce2ec9c8b99ad8253d5372e10b1e87cd42e`
- prior report commit: `ee0c798a4c4faa354f17f5e8828ea4ab39090403`

## Installed boundary

- Studio: `BlakeStacStudio.hsd1.pa.comcast.net`, user `blakestudio`
- job root: `/Users/blakestudio/crazycraft-remote-jobs`
- runner root: `/Users/blakestudio/crazycraft-remote-runner`
- Codex: `codex-cli 0.143.0`
- Docker: `29.5.2 linux/arm64`
- pinned host key:
  `SHA256:cdHPCFE/4L0q9Fx3gTHCkzpuAi8V/I5vegAYTLlgSr4`
- T1 key:
  `SHA256:o1Ug5HPDqkzQmLqhGTXxVRwWoXFe9iL6Odbn8LOAXoE`
- T10 key:
  `SHA256:XFHOU5DWZ3IGKaRVNSgrnFyB3xn/278B+tKIm2SRbTs`

Both identities disable forwarding, require pinned host verification, and enter
role-specific forced commands. T1-as-T10 and arbitrary-shell probes both
returned 126.

The Studio’s existing Crazy Craft archive is the exact frozen authority:

- size: `286297671`
- SHA-256:
  `daaa5afdea5795bac139a3b327e268b3f11b65a3909753f2ff313adadb17cef3`

No archive content was transferred to the MacBook or read by these synthetic
tests.

## Validation

- remote protocol/security tests: `24/24 PASS`
- existing stabilization regression: `20/20 PASS`
- Python compilation: `PASS`
- diff whitespace validation: `PASS`

No campaign product, Golden, package, audit, Blockbench, client, or integration
suite was rerun.

## Live T1 return

JOB-5 executed `EVIDENCE_RECOVERY` through the dedicated T1 identity and Studio
Codex. It used only a non-sensitive synthetic missing-contract fixture.

- terminal state: `COMPLETED`
- result:
  `d33a565737ce811f96d8cb1c6b840a0c2e4c24128fcb6f5a335ba3c2680c27aa`
- receipt:
  `cc98c0b44309439c81a3b24ba816e53340a27ed8952142f830110d29e6b05b5e`
- disclosure scan: `PASS`
- raw inputs returned: `NO`

The source-neutral result correctly remained `MORE_EVIDENCE_REQUIRED`; the
synthetic fixture intentionally contained no evidence.

## Live T10 return

JOB-4 executed `PRIVATE_CANDIDATE_AUDIT` through the dedicated T10 identity and
Studio Codex. It used a deliberately invalid synthetic candidate and no
private oracle.

- terminal state: `COMPLETED`
- result:
  `68757a6d343b2323ff1a00555b47b3ccb1d971b33d04bf67b9c6b498dba5bfd5`
- receipt:
  `6d7c20fed6b59647d7d74adc5dddd3f73ff4e8a8a5f83d0537d04217a752b555`
- disclosure scan: `PASS`
- raw inputs/logs returned: `NO`

The result contained only opaque IDs, abstract defects, allowed repair scope,
regression IDs, and a proof boundary.

## Failure and denial evidence

Failed attempts remain preserved.

- JOB-1 rejected an unsupported structured-output schema keyword.
- JOB-3 timed out at the original 60-second bound. Its unreserved
  nonmonotonic attempt was preserved under runtime rejected-ingress history
  before a fresh monotonic execution.
- JOB-8 deliberately bound the wrong MCAddon hash and failed before Docker:
  `exact BDS input mismatch: candidate.mcaddon`.
- reusing JOB-8 failed as a duplicate.
- path traversal, unauthorized job type, malformed framing, missing input,
  wrong manifest hash, role confusion, agent forwarding, and unexpected
  retrieval paths remain covered by the 24-test deterministic suite.

## Studio parallel Docker

Two fixed non-sensitive containers executed concurrently on the Studio using:

`crazycraft-python-test@sha256:4203883759408bd6904fc20a974b4c16094b5c8e605a1cbbaaa87e139e8fbebe`

Result authority:

`a06286603da1070c8ea6a88339cc22cf064b4517181a0c5a6a6a08ea9eac6999`

Both used network `none`, read-only roots, distinct inputs, outputs, names, and
logical ports. Each output hash matched its own input; the synthetic evidence
canary was not mounted; both containers were removed.

This proves Studio Docker concurrency and mount isolation only. It is not
Stable or Preview BDS qualification.

## Unresolved trust boundaries

1. All MacBook Codex tasks share the OS user that owns both private keys.
   Mode 0600 cannot prevent another same-user process from reading them.
2. Both keys terminate in the same Studio OS account. Forced commands enforce
   role operation, but the account is not a strong T1/T10 filesystem boundary.
3. Studio Codex runs read-only and is instructed to limit evidence reads, but
   there is no OS sandbox restricting it to only request-declared evidence
   roots.
4. No actual private oracle was used.
5. No authoritative Stable or Preview BDS image executed an exact package.
6. Bedrock client, controller, console, Realm, split-screen, rights, branding,
   commercial, and Marketplace gates remain unrun.

## Decision

The remote substrate is usable for further bounded validation work, but it is
not a replacement production-isolation authority yet.

Keep the network paused. The next supervisor action is to place T1/T10 key
custody behind a separate MacBook service identity and provide separate or
sandboxed Studio evidence/audit execution identities. Then run one real bounded
evidence recovery, one oracle-bound audit, and exact-package Stable and Preview
BDS qualification. No campaign assignment is issued by this milestone.
