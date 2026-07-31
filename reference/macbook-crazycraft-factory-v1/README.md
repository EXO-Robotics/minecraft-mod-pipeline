# MacBook Crazy Craft factory snapshot

This directory is a pinned, read-only reference import of the improved Crazy
Craft factory from the MacBook. It is not live Studio authority and must not be
started with the copied configuration files unchanged.

Source commit: `9a485501c8df628f04f87cc6ed007a0025405ca0`

Imported tracked subtrees:

- `stabilization-v1/pack-factory-v1`
- `stabilization-v1/remote-execution`

The snapshot intentionally excludes the MacBook mailbox repository, production
repositories, SQLite/WAL state, active queues, generated runtime files,
credentials, SSH material, and Docker volumes. Many committed records preserve
MacBook absolute paths as historical evidence. Studio-local configuration must
be generated separately before any service is launched.

The reusable implementation surfaces are the factory router, T1 dispatcher,
local tester, mailbox schemas and publisher, exact-package qualifier, and their
tests. The Studio's own orchestration database remains the source of truth.
