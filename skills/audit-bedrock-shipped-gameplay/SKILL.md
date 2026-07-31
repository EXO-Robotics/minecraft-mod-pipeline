---
name: audit-bedrock-shipped-gameplay
description: Audit an exact frozen Minecraft Bedrock .mcaddon for packaged-media validity, shipped main-entrypoint wiring, live event-to-observable gameplay reachability, survival progression, baseline product regression, and disposable desktop smoke-test readiness. Use before replacing a prior freeze, claiming a client-limitations portfolio freeze, beginning PS4 testing, or scaling another Java-to-Bedrock production section.
---

# Audit Bedrock Shipped Gameplay

Operate read-only against immutable package bytes. Bind the candidate commit,
BP/RP/add-on hashes, prior approved baseline, sanitized product contract, and
qualification receipts before inspecting content. Do not repair while acting as
the auditor.

## Decode the shipped package

Run:

```bash
python3 scripts/inspect_mcaddon.py \
  --mcaddon /absolute/path/candidate.mcaddon \
  --expected-sha256 EXPECTED_SHA256 \
  --cooperative
```

Require every nested pack and package member to be safe to extract. Parse all
JSON and fully decode every packaged PNG. Reject zero dimensions, CRC errors,
truncated IDAT data, invalid scanlines, unsupported interlace without an
external decoder, wrong texture-contract dimensions, and files whose extension
does not match their bytes. Validate OGG signatures and decode through an
available audio tool when audio is promotion-critical.

Bind visual proof to the runtime texture bytes inside the exact RP. A valid
`.bbmodel`, Golden score, source texture, or native geometry export does not
cure a corrupt packaged texture.

## Audit the shipped entrypoint

Read the script module entry declared by the BP manifest, then recursively trace
its imports. Tests and pure policy modules are not runtime authority.

For every custom gameplay role, prove this chain:

`normal player/native event → shipped subscription or component callback →
production adapter → state transition → Bedrock API mutation → visible result →
cleanup/restart policy`

Require tests to import the shipped entrypoint with production-equivalent
Bedrock mocks and exercise its actual registration path. Fail when:

- `main.js` installs in-memory `Set` or `Map` adapters instead of world,
  inventory, player, block, particle, sound, or persistence operations;
- a placement callback sets `event.cancel = true` but the deferred path never
  performs or restores real placement;
- recipes passed by the live adapter contain null placeholders;
- hunger, durability, inventory, rewards, particles, sounds, or movement are
  represented only by bookkeeping collections;
- exported capacity, encounter, progression, cleanup, or reward functions have
  no caller reachable from the shipped entrypoint or native JSON surface.

Call this gate `SHIPPED_ENTRYPOINT_INTEGRATION_PASS`. Unit tests for an
uninstantiated controller cannot satisfy it.

## Prove player reachability and progression

For each approved product role, require:

- survival acquisition, intended natural spawn, or explicit encounter access;
- a real activation path;
- an observable player-facing outcome;
- multiplayer authority and duplicate protection where applicable;
- cleanup and restart behavior.

Do not silently replace an approved keyed encounter or progression chain with
generic natural spawning and generic loot. Record such a change as an explicit
product redesign and rerun the semantic oracle.

Classify dead policy code, command-only fixtures, stress-only summons, spawn
eggs, and unreachable recipes as `INTEGRATED_ARTIFACT_ONLY`.

## Compare against the approved baseline

Keep comparison in the audit lane so prior production files do not enter a
clean production context. Compare product-level and quality metrics:

- approved roles and progression edges;
- survival-accessible interactions;
- behavior states and feedback;
- geometry bones, cubes, locators, and animation coverage by asset class;
- texture dimensions and successful decode;
- audio/VFX breadth;
- performance caps.

Fail promotion when the candidate loses an approved capability or materially
regresses a hero/representative asset without an approved redesign. A cleaner
lineage does not automatically supersede a stronger prior product candidate.

## Classify BDS and client gates separately

Use `BDS_PACKAGE_LOAD_AND_RESTART_PASS` for clean Stable/Preview loading,
script initialization, identifier probes, and restarts. Credit only gameplay
events actually delivered and observed by the harness.

For candidates with custom RP rendering, before-event placement, custom
interaction adapters, controller-sensitive flows, or progression encounters,
require a disposable desktop smoke test before a full portfolio promotion.
The smoke matrix must cover content logs, packaged textures, animations,
placement, interaction, nutrition/effects, equipment, projectiles, structures,
progression, save/reload, and a bounded natural-spawn soak.

Keep controller, real-player reconnect, Realm, split-screen, physical PS4,
Marketplace, distribution, and release separate.

## Decide

Full promotion requires:

- `PACKAGED_MEDIA_DECODE_PASS`
- `SHIPPED_ENTRYPOINT_INTEGRATION_PASS`
- `PLAYER_REACHABILITY_PASS`
- `BASELINE_PRODUCT_REGRESSION_PASS`
- `BDS_PACKAGE_LOAD_AND_RESTART_PASS`
- `DESKTOP_SMOKE_PASS` when client-visible/custom-interaction surfaces exist

If static/BDS evidence is useful but any required gate fails, preserve the
exact package as a partial or superseded candidate. Do not create or publish a
full-success tag.
