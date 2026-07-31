---
name: work-bedrock-factory-pack
description: Execute one authorized Java-to-Bedrock production, continuation, repair, or interruption-recovery activation in an isolated pack repository. Use when assigned a hash-bound task pack that requires original Bedrock implementation, worker-local validation, freezing, and submission of at most one immutable candidate generation.
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
4. Run every declared worker-local command: static/schema checks, pack-local
   tests, exact shipped-script tests, deterministic build twice, archive/media
   integrity, restricted scans, and process-receipt validation.
5. Freeze and submit at most one candidate. Bind the production commit/tree,
   artifact/manifest hashes, activation, local results, and process-isolation
   receipt.

Completion is `CANDIDATE_SUBMITTED`, not downstream acceptance. Do not run,
request, or wait for T1, Stable BDS, T10, T2, integration, client, Realms,
controller, split-screen, PS4, Marketplace, or release gates.

For repair, preserve rejected generation `N`, make a material change, and submit
exactly `N+1`. Stop only with an activation-allowed structured code and exact
evidence. Free-form questions, routine permission requests, and "local work is
done" are not valid stops.
