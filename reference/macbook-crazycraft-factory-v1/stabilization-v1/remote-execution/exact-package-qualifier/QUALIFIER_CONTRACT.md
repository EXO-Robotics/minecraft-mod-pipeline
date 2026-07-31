# Exact-package qualifier contract

This image qualifies one immutable, profile-bound Bedrock candidate against
Stable Bedrock Dedicated Server `1.26.33.2`.

Invocation is fixed:

```text
/opt/crazycraft/bin/qualify-exact-package \
  --request /control/request.json \
  --output /output
```

The container receives:

- `/control/request.json`: read-only canonical request;
- the three exact request-bound BP, RP, and MCAddon paths below `/input`;
- `/work`: isolated writable tmpfs;
- `/output`: isolated job-local bind, made write-only to the fixed nonroot
  container user for the run and restored to owner-only immediately afterward.

No Java evidence, private oracle, Docker socket, home directory, product
repository, network, or host port is mounted. The image directly supervises its
embedded, hash-bound x86-64 Stable BDS binary. On an ARM64 Docker Desktop host
this is an emulated diagnostic and cannot establish native performance.

New requests include `crazycraft-bds-candidate-profile-v1`. The profile binds
both manifest UUIDs and versions, both add-on member names, install-directory
names, one expected pack-stack marker, a world and fixture identity, and either
no script or one exact script entry with an optional runtime marker. The frozen
JOB-12 Trailbound tuple has one exact legacy-profile mapping; every other
profile-less request fails closed.

The qualifier proves exact artifact hashing, safe archive traversal, MCAddon
constituent identity, manifest/dependency/entrypoint bindings, two clean BDS
load cycles against one world, any required runtime marker on each cycle,
candidate-scoped fatal-log absence, and cleanup. It does not prove player-driven
gameplay persistence, client presentation, audio, controller, multiplayer,
Realm, split-screen, physical console, rights, branding, Marketplace, or
release readiness.
