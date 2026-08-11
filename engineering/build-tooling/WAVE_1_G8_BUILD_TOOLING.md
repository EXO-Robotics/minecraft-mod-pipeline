# Wave 1 G8 deterministic build tooling

Status: `IMPLEMENTED_AND_SYNTHETICALLY_TESTED_NOT_CANDIDATE_BUILT`

`tools/build.py` is now a build-only successor packager. It packages committed
`behavior_pack/` and `resource_pack/` bytes with sorted members, fixed archive
timestamps, fixed permissions, and fixed compression. It does not run a source
generator, freeze a candidate, or claim qualification.

The output family is exclusively `aionbound-wave-1-living-world-g8-*`; none of
the inherited `aionbound-core-content-beta-g7-*` artifacts is a write target.
Each workspace build emits:

- behavior and resource `.mcpack` files;
- one `.mcaddon` containing those exact nested pack bytes;
- a complete per-file source-byte ledger for both source packs;
- an artifact manifest binding package hashes, ledger identity, and the exact
  nested address and SHA-256 of the manifest-declared shipped script entrypoint.

`build_twice_and_compare` writes to two caller-selected output directories and
compares all package and ledger hashes plus entrypoint binding. A later freeze
controller can use this primitive, but a passing comparison is only deterministic
workspace-build evidence. It is not an immutable candidate, BDS, client,
controller, console, multiplayer, Marketplace, or release proof.

The bounded tests use disposable synthetic packs. This change intentionally did
not build the current Wave 1 source tree and did not run BDS.
