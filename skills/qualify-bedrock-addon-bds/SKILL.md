---
name: qualify-bedrock-addon-bds
description: Qualify an immutable Minecraft Bedrock add-on package with deterministic rebuilds, MCTools, architecture-aware Docker controls, exact commit and SHA binding, Stable and Preview BDS restart ledgers, script or asset-only policies, packless and minimal-pack diagnostics, and narrow machine-readable receipts. Use when BDS crashes, behaves nondeterministically, runs x86-64 binaries on ARM64, or must prove that the exact frozen `.mcaddon` loads without overstating client, multiplayer, controller, Realm, split-screen, or PS4 behavior.
---

# Qualify a Bedrock add-on in BDS

Read [qualification-contract.md](references/qualification-contract.md) before
running BDS or interpreting a crash.

Use this skill as the execution harness beneath the read-only
`$qualify-bedrock-candidate` role. Validate that role's standardized assignment
before executing. Keep BDS execution separate from final portfolio
classification.

## Freeze the candidate

1. Require a clean production repository and immutable commit.
2. Read the package bytes from that commit.
3. Compare the committed bytes, working package, and expected SHA-256.
4. Rebuild twice and require byte identity.
5. Run static/schema tests and MCTools on that exact package.
6. Freeze tool versions, BDS binary hashes, image digest, host architecture, and
   Docker server architecture.

Do not qualify a mutable working-tree package.

## Check architecture first

Run:

```bash
python3 scripts/inspect_bds_architecture.py \
  --image IMAGE_DIGEST \
  --stable-binary /path/to/stable-server \
  --preview-binary /path/to/preview-server
```

Bedrock Dedicated Server Linux binaries may be x86-64 while the macOS host,
Docker server, and wrapper image are ARM64. Treat this as an emulation boundary.
If pack-loaded worlds crash silently while minimal or packless worlds boot,
test an explicit `linux/amd64` wrapper digest before degrading the candidate.
Use the public registry's platform-specific digest, not a mutable tag, for the
qualifying receipt.

If Docker credential lookup hangs for a public image, use an empty temporary
Docker config for an anonymous pull. Do not copy or expose the user's Docker
credentials.

## Run declared ledgers

1. Generate a deterministic pack-bound `.mcworld`.
2. Run Stable for the declared restart count.
3. Export the Stable-saved LevelDB world.
4. Verify embedded pack hashes.
5. Run Preview on that exact saved world.
6. Require correct version/build ID, server start, clean content log, expected
   script marker when scripts exist, and bounded console probes.
7. For asset-only packs, explicitly disable the script marker requirement.

Stop a ledger on its first disqualifying failure. Do not continue unchanged
runs until a passing streak appears.

## Diagnose without hiding failures

Preserve the failed ledger and run separately labeled controls:

- packless world
- manifest-only BP
- manifest-only RP
- candidate BP-only
- candidate RP-only
- architecture-matched wrapper

Controls do not count as qualification. A material repair or architecture
change starts a fresh ledger with a new receipt.

Treat a BDS content/schema error as a generator escape: repair the generator,
add a regression, rebuild, commit a replacement candidate, and rerun every
invalidated gate.

MCTools must report zero errors. Warnings and recommendations require review but
are not equivalent to errors. Keep the complete log and tool exit code.

Require paired BP/RP presentation bindings for promoted items and wearables:
server definitions, client textures or attachables, atlas entries, and
localized names must agree. Treat a behavior-only item or missing atlas binding
as `ARTIFACT_PRESENT`, not a player-ready feature.

## Validate and report

Run:

```bash
python3 scripts/validate_bds_receipt.py \
  --receipt /path/qualification-receipt.json \
  --metadata /path/qualification-metadata.json \
  --mct-log /path/mctools.log \
  --repository /path/production-repo \
  --package-path packages/addon.mcaddon
```

Report only:

- Exact candidate commit, tree, package SHA, world SHA, image digest, BDS
  versions, binary hashes, restart counts, and passed probes.
- Failed or superseded ledgers.
- Untested client and platform claims.

BDS load and script initialization do not prove gameplay, rendering,
persistence semantics, real multiplayer, controller input, Realm, split-screen,
or physical PS4 behavior.
