---
name: integrate-bedrock-subsystem
description: Integrate multiple frozen clean-room Bedrock feature candidates into one connected subsystem using production-facing interfaces only. Use when an integration subagent must merge dependency waves, reconcile namespaces and shared services, repair production-local conflicts, run cross-feature tests, deterministically package the exact candidate, and freeze it for independent audit without Java evidence access.
---

# Integrate a Bedrock Subsystem

Require a standardized assignment for role `segment_integrator`, skill
`integrate-bedrock-subsystem`, and lane `INTEGRATION`. Validate it with
`$translate-java-mods-to-bedrock`'s
role-contract validator. `requires_activation_attestation` must be true.

Operate inside the integration worktree. Do not access Java evidence, analyst
notes, private oracle cases, or source-specific identifiers.

## Verify the integration packet

This is a production role. Require an actual sandboxed activation attestation, not
only context isolation. Verify lane-local runtime roots, denied evidence and
private-oracle access, launcher/profile/environment hashes, PID, command,
prompt/context hash, tool hashes, timestamps, and exit status before mutation.

Require:

- Baseline and integration branch commits.
- Ordered candidate commits and package hashes.
- Shared infrastructure and namespace contracts.
- Production-facing cross-feature requirements.
- Performance budgets, allowed paths, and supersession policy.

Verify every input commit and hash before merging. Reject mutable or dirty
candidate worktrees.

## Integrate by dependency wave

Use this order:

1. Shared identifiers, state schemas, persistence, cleanup, and event interfaces.
2. Independent native blocks, items, controls, and entities.
3. Consumers such as doors, multiblocks, visuals, machines, or encounters.
4. Cross-feature redstone, lifecycle, ownership, and migration behavior.
5. Packaging, stress, repair, and freeze.

Resolve namespace, UUID, manifest dependency, texture-path, and shared-script
conflicts centrally. Preserve feature provenance and candidate ancestry. Do not
silently rewrite product behavior to make a merge easier.

For cooperative Resource Packs, require one immediate creator-project texture
root and keep each feature's entity and item textures below its game/asset
directory. Update client bindings after moves. Re-run the current Creator Tools
profile instead of assuming that a locally resolving loose texture layout is
cooperative-pack compliant.

## Test the connected system

Test more than the sum of feature-local suites:

- At least one required cross-feature interaction.
- Shared persistence and migration.
- Restart during active states and pending cleanup.
- Unloaded or blocked cleanup targets.
- Two/four-player ownership and duplicate prevention.
- Redstone/event propagation and stale revision rejection.
- Worst-credible entity, callback, record, and particle budgets.
- Pack/script loading with zero content-log errors.
- Player-reachability traces from survival acquisition or spawn through the
  public event/component, authoritative handler, state transition, reward, and
  cleanup.
- Pack icons, localized pack metadata/messages, audio/particle bindings, and
  removal of stale section-facing integration residue.

Do not count a definition, exported service, stress-only summon helper, or
recipe with unobtainable dependencies as a completed player-facing feature.
Classify it `INTEGRATED_ARTIFACT_ONLY` until a current-candidate public-edge
test passes.

Run static, Creator Tools, pack-hazard, deterministic-build, and
production-local BDS checks on the exact integrated package.

For the pinned Script API version, reject removed event members and direct
restricted-mode mutation. Require module registration to survive Stable and
Preview startup, and turn every BDS-only escape into a regression plus mutation.

For asset-only candidates, explicitly set the harness to not require Script API
initialization. Do not add a marker script. Still require clean load, bounded
fixture probes, stress, cleanup, and restart in Stable and Preview where the
qualification packet requires them.

## Repair without crossing lanes

Run every repair through the same sandbox executor and require a repair
receipt. Classify tests by current candidate, superseded candidate, historical
section, cross-section integration, and authoritative semantic authority. Use
`SUPERSEDED_ASSERTION` for immutable historical expectations invalidated by a
later promoted repair.

Record defects with opaque product requirement IDs. Route feature-local repairs
back to the owning production lane without private-oracle or source details.
Every repair creates a new candidate commit and invalidates affected integration
and audit gates. Preserve superseded commits and hashes.

After a production repair, copy or merge the exact new commit, rebuild from
clean outputs twice, and ensure audit reports refer to the replacement package
hash. Do not carry forward post-freeze reports that still name a superseded
candidate.

## Freeze the integrated candidate

Extract packages from the immutable integration commit, build twice, and require
matching hashes. Freeze a candidate manifest, dependency graph, performance
budget, provenance inventory, and qualification packet. Return
`CANDIDATE_READY_FOR_INDEPENDENT_AUDIT` only for a clean, deterministic,
production-locally qualified candidate. Do not claim authoritative semantic,
originality, Stable/Preview BDS, desktop, Realm, or PS4 proof.
