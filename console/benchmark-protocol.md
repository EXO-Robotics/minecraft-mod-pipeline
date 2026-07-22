# Console benchmark protocol

## Purpose

This protocol collects platform-specific evidence without converting delivery success into a broader compatibility claim. All platform statuses begin `UNVERIFIED`.

## Status vocabulary

`LOCAL_WINDOWS_VERIFIED`, `BDS_DIAGNOSTIC_VERIFIED`, `REALM_WINDOWS_VERIFIED`, `PS4_VERIFIED`, `PS5_VERIFIED`, `XBOX_ONE_VERIFIED`, `XBOX_SERIES_VERIFIED`, `MARKETPLACE_TARGETED`, and `UNVERIFIED`.

A verified status applies only to the recorded artifact hash, game version, device/model, account/delivery route, scenario set, and date. `MARKETPLACE_TARGETED` means designed for the platform but not physically verified.

## Required evidence envelope

```yaml
schema_version: 1.0.0
status: UNVERIFIED
artifact_sha256: null
build_manifest_sha256: null
game_version: null
platform: null
device_model: null
delivery_route: realm
realm_version_or_id: null
tester: null
started_at: null
completed_at: null
checklist_revision: 1.0.0
raw_evidence: []
failures: []
external_blockers: []
```

Screenshots/video/logs must be time-correlated and content-addressed where practical. Personal Realm/account identifiers should be redacted from published reports.

## Procedure

1. Produce a clean test-world and candidate artifact; record hashes.
2. Validate the same artifact locally on Minecraft for Windows.
3. Record the local game version and complete real-action, persistence, migration, multiplayer, controller, and performance scenarios.
4. Upload that world to a Realm without rebuilding or substituting packs.
5. Join from Minecraft for Windows and repeat Realm checks.
6. Join from each available physical console and execute its checklist.
7. Leave/rejoin, restart the Realm, reconnect, and verify required state.
8. Preserve failures and raw evidence; do not rerun only passing subsets.
9. Assign only the exact platform status whose checklist passed.

## Required scenario classes

- Resource delivery, import/join, script initialization, and content availability.
- Actual item use/use-on-block, block interact/break, entity hit/hurt/spawn/death, projectile impact, scheduled behavior, and boss phases.
- Controller forms including focus, cancel/back, labels, accidental activation, and repeated use.
- Player progression, machine state, leave/rejoin, world/Realm restart, and migration.
- Two-player ownership and state isolation.
- Frame/input responsiveness, error logs, disconnects, and severe degradation.

An internal dispatcher invocation is labeled `INTERNAL_HANDLER`; it cannot satisfy `EVENT_ADAPTER`, `GAMEPLAY`, `PERSISTENCE`, `MULTIPLAYER`, or `CONSOLE` scenarios.

## Current platform state

| Surface | Status | Evidence |
|---|---|---|
| Local Windows Bedrock | `UNVERIFIED` | None recorded for Benchmark A |
| BDS diagnostic | `UNVERIFIED` | No Benchmark A artifact exists |
| Realm Windows | `UNVERIFIED` | Realm access/execution not recorded |
| PlayStation 4 | `MARKETPLACE_TARGETED`, `UNVERIFIED` | Physical test not performed |
| PlayStation 5 | `MARKETPLACE_TARGETED`, `UNVERIFIED` | Physical test not performed |
| Xbox One | `MARKETPLACE_TARGETED`, `UNVERIFIED` | Physical test not performed |
| Xbox Series | `MARKETPLACE_TARGETED`, `UNVERIFIED` | Physical test not performed |

