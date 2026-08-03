---
name: work-bedrock-factory-pack
description: Execute one authorized Java-to-Bedrock production, continuation, repair, or interruption-recovery activation in an isolated pack repository. Use when assigned a hash-bound task pack that requires original Bedrock implementation, a minimal activation attestation, freezing, and submission of at most one immutable candidate generation.
---

# Work one Bedrock factory pack

Use `$launch-cleanroom-production-worker` for production isolation and
`$translate-java-mods-to-bedrock` for reconstruction boundaries. Read the exact
assignment and activation files and verify their hashes before writing.

## Execute

1. Verify repository identity/ref, exclusive write roots, authority precedence,
   activation type, current/next generation, and that no authority was
   superseded.
2. Read only sanitized contracts and production-safe inputs. Never read Java
   evidence, source identity, private oracle cases, another pack repository, or
   downstream private findings.
3. Implement original Bedrock behavior only within the authorized scope.
4. Do not run broad validation jobs. Enforce only cheap control invariants:
   assignment and authority hashes, repository/ref identity, path containment,
   exclusive write scope, and candidate immutability.
5. Freeze and submit at most one candidate. Emit only the bounded activation
   attestation: activation ID, assignment hash, platform-qualification hash,
   repository ref, exit code, cleanup status, and optional candidate identity.

Deterministic double builds, package inventories, schema/static suites,
restricted scans, and package-entrypoint checks belong exclusively to
`PRE_BDS_MILESTONE`. They are forbidden as routine per-worker validation.

Completion is `CANDIDATE_SUBMITTED`, not downstream acceptance. Do not run,
request, or wait for either validation milestone, Stable BDS, integration, client, Realms,
controller, split-screen, PS4, Marketplace, or release gates.

For repair, preserve rejected generation `N`, make a material change, and submit
exactly `N+1`. Stop only with an activation-allowed structured code and exact
evidence. Free-form questions, routine permission requests, and "local work is
done" are not valid stops.
