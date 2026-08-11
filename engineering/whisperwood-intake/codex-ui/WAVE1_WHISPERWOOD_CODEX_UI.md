# Wave 1 Whisperwood Codex UI

Status: `TARGETED_LOCAL_SEMANTIC_PASS_OFFICIAL_AND_LOCAL_STABLE_API_BOUND`

Base commit: `8a92b8c822021232b74ad33771585899cf989400`.

## Stable API authority

The behavior pack pins `@minecraft/server-ui` to `2.0.0`.

- Microsoft stable module reference: <https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server-ui/minecraft-server-ui?view=minecraft-bedrock-stable>. Accessed 2026-08-11. It lists `2.0.0` as an available non-beta version and documents the manifest dependency shape. The newer `2.1.0` was not selected because it is absent from the exact local Stable server distribution.
- Microsoft stable `ActionFormData` reference: <https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server-ui/actionformdata?view=minecraft-bedrock-stable>. Accessed 2026-08-11. It documents the constructor plus `title`, `body`, `button`, and promise-returning `show(player)` used here.
- Microsoft stable add-on manifest reference: <https://learn.microsoft.com/en-us/minecraft/creator/reference/content/addonsreference/packmanifest?view=minecraft-bedrock-stable>. Accessed 2026-08-11. It documents `module_name` and exact string `version` dependencies.
- Exact local Stable BDS evidence identifies server `1.26.33.2` in `G000007-R1/output/stable-cycle-1.log` (SHA-256 `0f997e2bca628a0295a525e1a139a2b71e771f12898520e4d3d1f08a8cf46a47`).
- That server installation contains `data/behavior_packs/server_ui_library/scripts/server-ui-2.0.0.js` (SHA-256 `16ea3027fd36b0d39f35b2dd1250e6e2ffdbaea3934cefb86f1c9009abb4ff99`) and no `server-ui-2.1.0.js`.
- Its installed representative scripted BP declares `@minecraft/server-ui` `2.0.0` in `data/behavior_packs/mccompiler_representative_bp/manifest.json` (SHA-256 `9c2ed037a7c9fc6529bf3ba3e2d79370d5231a41f2be6768c603b443e3ba271f`).

The Wave 1 validator now binds approved script modules to exact versions and fails closed on `@minecraft/server-ui` `2.1.0` or another unapproved version.

## Implemented boundary

- Existing Codex item and lectern routes now open an `ActionFormData` primary surface.
- Navigation covers three approved categories and all 40 Whisperwood entries: Resources & Blocks (20), Plants (10), and Creatures (10).
- Locked entries hide identity and all answers. Partial entries expose identity and only the first question. Complete entries expose all three question slots.
- The three approved question headings are always used. Exact authored answer text is shipped only when its implementation-map `blocked_by` list is empty. Blocked answer text is absent from the runtime module and renders as a generic unavailable notice.
- A canceled form exits silently. A synchronous `show` throw or rejected `show` promise produces one bounded legacy guidance message; successful/canceled navigation produces no chat.
- The starter bookmark still records its legacy stamp before opening the UI. Codex v4 discovery state remains authoritative and unchanged.

## Evidence

```text
node --test tests/wave1_codex_ui.test.mjs tests/wave1_codex_runtime_events.test.mjs tests/wave1_codex_v4.test.mjs tests/g7_runtime_semantics.test.mjs
35 tests, 35 pass, 0 fail

python3 tests/test_wave1_validator.py
12 tests, 12 pass, 0 fail

python3 tools/validate_wave1.py --root .
PASS; source-tree mechanical validation only
```

## Proof boundary

This proves official/local stable API selection, source import and manifest binding, view-model disclosure rules, mocked form navigation, fallback behavior, and source-tree validation. It does not prove actual Bedrock form rendering or event delivery, controller ergonomics, client or console behavior, multiplayer, BP/RP packaging, deterministic build, Stable BDS module resolution for this successor, candidate readiness, Marketplace, or release.
