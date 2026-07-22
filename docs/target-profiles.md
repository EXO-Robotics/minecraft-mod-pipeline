# Target profiles

Target profiles are policy contracts, not labels inferred from a successful build.

## `MARKETPLACE_ADDON_STABLE`

The default production target is intended for local Bedrock worlds on PlayStation and Xbox after consumer installation. It permits stable BP/RP formats, stable data-driven components, and independently versioned stable `@minecraft/server` and `@minecraft/server-ui` symbols when required.

It prohibits beta/preview APIs, experiments by default, `@minecraft/server-net`, `@minecraft/server-admin`, external services, filesystem/native/JVM assumptions, server plugins, BDS-only behavior, undocumented APIs, silent fallbacks, uncleared material, and debug or fixture content.

Required gates include offline operation, controller-first design, multiplayer isolation, versioned persistence, clean packaging, rights review, performance budgets, symbol-level API validation, and explicit degradation reporting. The profile is specified but not implemented in the current compiler.

## Supporting profiles

| Profile | Purpose | Production claim |
|---|---|---|
| `LOCAL_WINDOWS_DEVELOPMENT` | Fast iteration, logs, debug commands, fixture execution | None |
| `REALM_CONSOLE_BENCHMARK` | Delivery, controller, multiplayer, persistence and physical-device testing | Evidence for named tested devices only |
| `DATA_ONLY_FALLBACK` | Script-free equivalent or controlled comparison | No automatic Marketplace claim |
| `BDS_DIAGNOSTIC` | Automated server-side diagnostics | Never console or Marketplace proof |
| `UNSUPPORTED` | No honest compatible implementation | Explicit rejection |

## Compatibility resolution

Planning must evaluate target eligibility per strategy and per emitted API symbol. Module versions are resolved independently to the lowest stable versions satisfying all emitted symbols. An override can approve degradation but cannot make an unavailable API legal.

Passing a lower target does not imply a higher one. BDS, local Windows, Realm Windows, PlayStation, Xbox, and Marketplace review are independent evidence surfaces.

