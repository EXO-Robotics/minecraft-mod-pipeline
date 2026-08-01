# Campaign state machine

## Controller ledger

Maintain one machine-readable record with:

- `campaign_id`
- `target_scope`
- `official_sources`
- `target_hashes`
- `active_gate`
- `candidate_commit`
- `candidate_tree`
- `candidate_package_sha256`
- `workers`
- `repairs`
- `superseded_candidates`
- `passed_claims`
- `failed_claims`
- `untested_claims`
- `final_classification`

## Lane permissions

| Lane | May read | Must not read |
|---|---|---|
| evidence | authorized Java evidence, configs, public docs | production secrets or unrelated private files |
| control | private oracle, evidence mappings, hidden cases | production worker credentials |
| production | sanitized contracts, approved infrastructure | Java evidence, private oracle, hidden canaries |
| audit | frozen candidate plus authorized oracle | mutable production worktree |
| qualification | committed package, public tests, BDS seeds | raw Java evidence |

## Candidate ledger

For every candidate record:

- Candidate number and parent.
- Material delta.
- Commit and tree.
- Package hash.
- Static, Golden, MCTools, Stable, Preview, and audit results.
- Declared run count and outcome sequence.
- Reason for supersession or promotion.

Never erase a failed candidate or relabel diagnostic controls as qualification
runs.

## Invalidated gates

- Runtime or BP change: static, semantic, deterministic build, MCTools, Stable,
  Preview, runtime audit.
- RP, geometry, animation, texture, or icon change: static, Golden, proof
  parity, deterministic build, MCTools, Stable, Preview, visual audit.
- Packaging-only change: deterministic build, package binding, MCTools, Stable,
  Preview.
- Receipt or report-only change: receipt schema, hashes, claim-boundary audit,
  final manifest.

## Final classifications

Use the campaign's declared classification vocabulary. A frozen-with-client-
limitations result requires all non-client release gates to pass. Do not use it
to hide rights, clean-room, semantic, originality, deterministic-build,
MCTools, Stable, or Preview failures.
