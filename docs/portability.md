# Portability contract

The repository is a factory template, not a frozen campaign export.

## Allowed repository content

- Factory source, generic schemas, deterministic examples, tests, docs, and
  reusable agent skills.
- Relative paths and placeholders that are resolved inside a user's checkout.
- Public tool names and narrow evidence boundaries.

## Excluded repository content

- Java mods, source evidence, decompilations, private oracles, or third-party
  game assets.
- Generated `.mcaddon` files, campaign receipts, SQLite databases, Git mailbox
  histories, worker prompts, logs, and runtime queues.
- Workstation usernames, absolute operator paths, credentials, session IDs,
  task IDs, service tokens, or another factory's compatibility ledger.
- Claims that synthetic rehearsal, static validation, BDS, or private audit
  proves client, console, Marketplace, legal, release, or universal conversion.

## New host rule

Every clone initializes a fresh `.mccompiler/factory-v1` root and independent
mailbox. The synthetic rehearsal must run on that host and bind its receipt hash
before a real campaign is activated. Cross-host scaling requires a separately
designed central broker and artifact transport; do not synchronize the SQLite
database or mailbox worktree as a substitute.

The supplied process sandbox is macOS-specific. On another operating system,
keep the queue and role contracts but replace the launcher with a fail-closed
backend that is independently reviewed and qualified before production.
