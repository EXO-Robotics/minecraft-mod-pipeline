# Benchmark B: Rights-cleared Java reconstruction

Status: `TECHNICAL_CANDIDATE_REVIEW_REQUIRED`.

`vassbo/DoorLock` at commit `fe097cf9376242eb13d53dc485b61d8b33891392` is the pinned technical candidate. It has not been selected as rights-cleared, vendored into this repository, or approved for Marketplace use. The inspected repository declares CC0-1.0, but an accountable human must separately review source, assets, name, branding, trademarks, dependencies, and intended commercial/Marketplace distribution.

A future candidate must have source access, representative registrations/events/assets/state, at least one custom behavior, one reconstruction decision, and one redesigned or unsupported feature. Code, assets, names, branding, trademarks, dependencies, commercial derivatives, and Marketplace distribution are reviewed separately before any material is imported.

DoorLock is technically useful because it contains Fabric entrypoints, registrations, mixin-injected interactions, custom networking, commands, persistent lock state, recipes, textures, and controller-relevant gameplay. Those same mixins and packet/UI assumptions create meaningful redesign work. See `selection-criteria.yaml` for the pinned source and unresolved gates.

## Technical reconstruction contracts

The machine-readable Benchmark B contract set is deliberately separate from imported source or assets:

- `expected-behaviors.json` defines evidence-traceable lock, unlock, open, and break behavior.
- `contracts/state-schema.json` and `contracts/save-migration.json` define structured world state and a fail-closed legacy migration.
- `contracts/multiplayer-ownership.json` defines server authority, isolation, conflict, reconnect, and dimension rules.
- `contracts/controller-first-redesign.json` replaces command/anvil/keyboard assumptions with a proposed controller flow; it is not approved or console-tested.
- `contracts/unsupported-mixin-mapping.json` maps every observed mixin file to an explicit redesign or blocker. No mixin is portable to Bedrock.
- `expected-quality.json` records omissions and quality status with runtime `NOT_RUN` and console/Realm `UNVERIFIED`.
- `rights-blockers.json` keeps code, assets, branding, trademark, dependency, and Marketplace-distribution review open.

These files are specifications for a future reconstruction. They do not claim implementation, runtime fidelity, console compatibility, rights clearance, Marketplace eligibility, or approval. No DoorLock source or asset is vendored here.

## Clean-room technical implementation

`reconstruction/` now contains an original, partial Bedrock script written from the evidence contracts rather than copied Java or asset payloads. It proves the feasibility of stable cancellable block-interaction and break events, server-authoritative world state, controller item-use, owner isolation, universal-key access, and deferred mutations outside restricted before-event callbacks. The break policy defaults to the Java behavior of allowing a successful break and then removing the exact revisioned lock; universal-key possession exposes a controller form for switching the world to deny mode, and canceled breaks never reach the removal callback. Its API surface is checked against the stable Marketplace catalog and its JavaScript syntax is tested.

The implementation is now `PARTIAL_TECHNICAL_RECONSTRUCTION_BDS_ADAPTER_VERIFIED`. It proposes a controller-configured shared-credential redesign for normal and golden keys, with universal-key override and owner-identity compatibility records. Pinned source review confirms normal and golden keys intentionally share the same `KeyItem` behavior; their iron- and gold-nugget shaped recipes are reconstructed separately. Credential plaintext is transient; only deterministic SHA-256 gameplay identifiers are persisted, which is not a password-security boundary. Because stable Bedrock scripting cannot cancel vanilla neighbor updates, locked doors, trapdoors, and fence gates use a persisted last-authorized open state and a bounded 32-lock-per-tick reconciliation pass. This is an explicit approximation: unloaded chunks are skipped, larger lock sets add latency, and non-player state changes are also restored. The reproducible builder generates item/resource packs with original placeholder pixels. The exact `.mcaddon` passed pinned Creator Tools 0.17.6 with zero errors and warnings, and the exact `.mcworld` passed a three-cycle isolated BDS 1.26.33.2 prepared-journal recovery, pack-upgrade, and restart diagnostic. One nonempty legacy lock migrated and remained readable after restart. A bounded BDS adapter test also placed a vanilla trapdoor, forced its `open_bit`, verified that the production reconciliation restored it, and verified the restored state after restart. This is server adapter integration evidence, not player-driven redstone, gameplay, client, Realm, or console evidence. There is still no action-driven player gameplay, crafting, or form evidence, approved redesign, quality classification, rights clearance, player-created lock persistence proof, real multiplayer test, client test, Realm test, or console test. It therefore does not satisfy Benchmark B or Marketplace-candidate gates yet.

Reproduce the current technical build in a new project directory:

```sh
PYTHONPATH=src python3 tools/build_benchmark_b.py --output /private/tmp/mccompiler-benchmark-b-project
```

The builder emits deterministic `.mcaddon` and `.mcworld` artifacts, runs static/script/asset/API/performance validation, and records the intentionally failing Marketplace-candidate evaluation. It does not assign rights clearance or quality parity.
