# Exact-package qualifier repair

The exact-package qualifier was generalized and rebuilt without changing Trailbound.

Authority:

- Source commit: `bca89f51b10f06a145a8b02928448b98ef5ae5f8`
- Source tree: `7bd65a75a0730d8818f43a202abda2905feb62ea`
- Qualifier implementation commit: `260e2562ee190ba64385387de9f93ab1e5cda09f`
- Qualifier SHA-256: `d1af68f59307d5624352acb2c11f1b24feb66bf1e6351190eb950ff705d56880`
- Tester image: `crazycraft-exact-package-qualifier@sha256:c3adfe3f7cad7c174d23db52dd14da6937901b1df7f9be853c65167086ed811f`
- Image archive SHA-256: `23bcb3b94d8f9fd0c70797ad906b27f8026f2cddc8a1412340fb548fc0bd0894`
- Stable BDS seed: `itzg/minecraft-bedrock-server@sha256:2944da377164a7cc8bcf29c1d2fd50d0d863c6476e23923384ec55dc7dc4627a`
- Stable BDS version: `1.26.33.2`

The image contains executable `/opt/crazycraft/bin/qualify-exact-package`, and its embedded bytes match the committed qualifier SHA-256. The embedded BDS binary SHA-256 is `978ea655c418f112a33b80043d676712ad080724382fafda9509825910fa4043`.

The v2 request contract binds exact BP/RP/MCAddon paths, sizes, hashes, manifest UUIDs and versions, add-on member names, install directories, pack marker, script entrypoint and marker, world identity, fixture identity, image digest, BDS binary, ports, CPU, and memory. Unknown fields, paths, profiles, images, channels, archives, and inputs fail closed.

Targeted validation:

- Qualifier tests: `16/16 PASS`
- Remote-route regression tests: `25/25 PASS`
- Image executable and `--help`: `PASS`
- Hash, traversal, hidden-member, symlink, missing-field, unexpected-field, image-platform, evidence-mount, duplicate-ID, and sequence checks: `PASS`
- Real Stable BDS execution with the unchanged Trailbound tuple: `PASS` locally
- Canonical outer result and receipt validation after the host-wrapper repair: `PASS` on `JOB-000000000014`

The first local JOB-13 staging attempt correctly failed before Docker because a new scratch root expected sequence 1. Reusing the existing append-only root whose accepted sequence ended at JOB-12 allowed JOB-13 to execute. This was a job-journal diagnostic, not a candidate defect.

Mac Studio replication remains optional unavailable capacity. The dedicated T1 forced-command key authenticates, but its allowlist has no image-load or runner-deployment operation and direct administrative SSH is not authenticated. The selected MacBook-local Docker route is authoritative for the initial factory, so this optional Studio limitation does not block `DOCKER_BDS_ROUTE_PROVEN` or `FACTORY_TEST_GATE_READY`. No product repair is authorized or required.

Independent red-team verdict: `PASS_NARROW_WITH_REQUIRED_ROUTE_HARDENING`. The JOB-13 Trailbound authority was independently reconciled through its registered bundle and metadata commit, but qualifier v2 does not itself resolve Git provenance and its generic fatal-pattern list is not exhaustive. These are factory-route hardening items, not defects in the unchanged Trailbound candidate or its observed Stable BDS load/restart run.
