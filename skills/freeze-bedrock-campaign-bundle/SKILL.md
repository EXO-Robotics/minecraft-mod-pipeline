---
name: freeze-bedrock-campaign-bundle
description: Assemble and verify a slim frozen Minecraft Bedrock reconstruction campaign bundle containing BP, RP, editable assets, sanitized contracts, approved provenance manifests, qualification receipts, independent audits, deterministic packages, and a final report. Use when a campaign must exclude raw Java artifacts, credentials, hidden canaries, private control files, worker sessions, copied BDS binaries, and vanilla server data while producing an all-file SHA-256 manifest and explicit client/platform limitation record.
---

# Freeze a Bedrock campaign bundle

Read [bundle-contract.md](references/bundle-contract.md) before copying files.

## Build in a fresh staging root

Require these top-level entries:

- `behavior_pack/`
- `resource_pack/`
- `editable_assets/`
- `contracts/`
- `provenance/`
- `qualification/`
- `audits/`
- `packages/`
- `FINAL_REPORT.md`

Copy only from frozen commits and approved evidence manifests. Do not assemble
from a mutable working tree.

## Include narrowly

Include:

- Frozen BP and RP.
- Editable original `.bbmodel` files.
- Sanitized public contracts and inherited standards.
- Acquisition and target-freeze manifests without raw JARs.
- Complete feature disposition inventory when approved for the local audit
  bundle.
- MCTools log and exit status.
- Exact candidate Stable/Preview receipt, content logs, and deterministic
  `.mcworld` inputs.
- Independent final audits.
- Player-reachability records distinguishing artifact presence, server
  loadability, and normal survival reachability.
- The passing `$audit-bedrock-portfolio-freeze` result and exact candidate
  bindings.
- Clearly labeled superseded audit findings.
- Combined `.mcaddon` and SHA sidecar.
- Candidate commit, tree, package hash, tool versions, and limitation matrix.

Exclude:

- Java JARs, source textures, sounds, decompile output, or launchers.
- Authentication files, installation identifiers, tokens, or credential
  hashes.
- Hidden canaries, private controls, semantic oracles, worker prompts, or
  session history.
- BDS executables, full BDS seed directories, copied vanilla packs, Docker
  layers, node modules, caches, and temp trees.

Retain BDS `result.json`, `content.log`, qualification receipt, and exact test
worlds; do not retain hundreds of megabytes of server payload.

## Verify before destination copy

1. Parse scoped production, provenance, audit, and receipt JSON.
2. Require no symlinks.
3. Scan filenames for `auth.json`, `installation_id`, `.hidden-canary`, and
   `*.jar`.
4. Verify the `.mcaddon` hash against the candidate-freeze record.
5. Verify final Stable/Preview qualification status and independent audits.
6. Require every promoted feature to have a passing
   `PLAYER_REACHABLE_FEATURE` record or an explicit non-success disposition.
7. Require a passing independent portfolio-freeze audit. This bundle validator
   checks packaging integrity; it does not replace the auditor.
8. Generate `MANIFEST.sha256` from the staging-root working directory.
9. Run `shasum -a 256 -c MANIFEST.sha256` from that same directory.
10. Copy to a new destination path; do not overwrite an existing frozen bundle.
11. Rerun the manifest from inside the destination directory.

Run:

```bash
python3 scripts/validate_frozen_bundle.py /absolute/path/bundle
```

If the manifest uses relative paths, invoking verification from its parent will
produce false missing-file failures. Treat the current working directory as
part of the verification contract.

## Report

Lead with classification, bundle path, commit, package SHA, manifest count,
MCTools, Stable/Preview results, Golden results, size, and pending client
limits. State whether GitHub changed.
