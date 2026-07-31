# Trailbound exact-package Stable BDS qualification

## Candidate

Trailbound remained unchanged.

- Content authority: registered Git bundle commit `d2d737c5b7110c1c596ce429649fb002efdf9049`, tree `47d8d3e409b8cc1b6de49654456f6cee5ddfb201`
- Publication authority: commit `3cfcc28f7a15a8f31413b77ca0cbd6f3c137f5e5`, tree `f4dfc5db028a709bc89b588b57719ad78b215d8b`
- BP: 33,229 bytes, `f26e9daddfd7ba8893f6ccd5934b45ec0f88e1380b3e02038c13051d71fad8f3`
- RP: 65,207 bytes, `14fcdba454ab5ca85381628d71845dadc80b9c255eb812b7aaebea84814ef7af`
- MCAddon: 84,791 bytes, `949fa581e930460a8bcc8e02f574d1bc89f848a754c57ec84907f07f27372bc4`
- Bundle: 877,571 bytes, `64ef65c1a6d5b90ac55af7f4aa05a951574e055966287ec7912eb01aa706be72`

The content commit is not in Thread 9's current object database; it is preserved by the registered, complete Git bundle. `git bundle verify` passed and resolved that commit and tree. The publication commit and tree remain present in Thread 9.

## Real Stable BDS execution

JOB `JOB-000000000014` ran on local Docker Desktop using the digest-pinned qualifier v2 image and embedded Stable BDS `1.26.33.2`. This post-repair run also returned a canonical outer result accepted by the remote-result validator.

Both cycles:

- reached `Server started`;
- loaded `Trailbound Packs Behavior` UUID `7c428986-b20f-548d-84ae-1c56029426b2`, version `1.1.0`;
- installed and activated the exact RP without dependency or content errors;
- emitted `[trailbound] runtime initialized`;
- exited cleanly after `Server stop requested`;
- reused and reopened the same world.

The automated fixture `TRAILBOUND_EXACT_PACKAGE_LOAD_RESTART_V1` passed. It proves exact package load, shipped entrypoint initialization, clean shutdown, and same-world restart. No automated physical-player hook exists, so player-mutated persistence remains not run.

The container was removed, no host gameplay ports were published, no evidence or private-oracle mounts were present, and the three candidate hashes remained byte-identical.

## Classification

The selected MacBook-local Docker route returns `TEST_PASS` for the narrow exact-package Stable load/restart gate. Optional Mac Studio replication remains unavailable because the restricted T1 forced-command allowlist cannot load the new digest-pinned image, but that optional-capacity blocker does not supersede the selected local result and is not a Trailbound product defect.

The append-only mailbox result is `MSG-T09-TRAILBOUND-BDS-RESULT-000005` at commit `851c016483dc5d87329135c3d63eaa8fcd565332`, tree `8f6fdbb47ba0e5754f4980f1f670c010a58c5425`.

Unproven boundaries remain Bedrock client presentation, audio, player-mutated persistence, multiplayer, controller, Realm, split-screen, physical PS4, rights, branding, Marketplace, and release.

The independent red team accepted the narrow Stable load/restart evidence and retained two route limitations. The qualifier verifies exact artifact bytes and syntactic authority fields but does not itself resolve the Git bundle, repository ref, commit, or tree; that provenance was verified separately for JOB-14 and remains mandatory outer preflight. Its generic fatal-pattern list is conservative but cannot substitute for client qualification. These limitations narrow the result; they do not block the generic local exact-package route.
