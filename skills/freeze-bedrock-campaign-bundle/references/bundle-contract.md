# Frozen bundle contract

## Candidate freeze record

Require:

- `classification`
- `product_identity`
- `source_commit`
- `qualification_commit`
- `git_tree`
- `combined_mcaddon.path`
- `combined_mcaddon.sha256`
- `target_authority`
- `qualification.status`
- `golden`
- `feature_inventory`
- `limitations`
- `exclusions`

## Required limitation fields

- `desktop_client_visual_review`
- `controller_gameplay`
- `real_multiplayer_reconnect`
- `realm`
- `split_screen`
- `physical_ps4`
- `marketplace`
- `release`

Marketplace and release must remain `NOT_AUTHORIZED` unless the user provides
separate authority.

## Manifest

Generate after every bundle change:

```bash
find . -type f ! -name MANIFEST.sha256 \
  -exec shasum -a 256 {} + | LC_ALL=C sort > MANIFEST.sha256
shasum -a 256 -c MANIFEST.sha256
```

Run both commands from the bundle root. The manifest intentionally excludes
itself to avoid a circular hash.
