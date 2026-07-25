# Production sandbox and process receipts

Use this reference before any evidence-blind production, integration, visual
production, or repair task.

## Rehearse before a large campaign

Before a 35–55-feature campaign, run one tiny original feature through:

```text
fresh source-neutral repository
→ sandboxed authoring agent
→ one sandboxed repair
→ deterministic rebuild
→ candidate-bound isolation audit
```

Do not begin large production until the rehearsal proves the launcher and
repair path.

## Build the execution boundary

Create a fresh standalone repository and Git object store from the qualified
source-neutral baseline. Transfer only:

- Sanitized production contract
- Production oracle interface
- Approved neutral infrastructure
- Source-neutral role skill and assignment packet

Use a deny-by-default OS sandbox, container, VM, or separate filesystem user.
Set lane-local `HOME`, `TMPDIR`, `XDG_CACHE_HOME`, logs, indexes, tool state,
Blockbench projects, generated output, and build caches. Deny evidence, control,
private oracle, canary, evidence/control Git stores, shared agent indexes,
unapproved caches, unrelated user directories, and network by default.

Do not dispatch a native subagent directly when the collaboration runtime
cannot prove its process inherited the boundary. Use a launcher that starts the
actual agent process inside the boundary or stop with
`PRODUCTION_ISOLATION_INVALIDATED`.

## Preflight from the real process

Require:

```text
approved inputs readable: PASS
production/runtime/temp/cache writes: PASS
evidence/control/private oracle/canary reads: DENIED
restricted source identifiers and hashes: NO_MATCH
remotes/alternates/hardlinks/cross-lane symlinks: NONE
restricted Git objects: NOT_AVAILABLE
evidence-related environment variables: NONE
network: DENIED unless explicitly authorized and receipt-bound
```

Tool-loader repairs may add only the minimum public runtime path. Freeze each
profile revision and rerun the entire preflight.

## Record the actual process

Create one receipt per agent process and repair process. Record:

- Receipt ID, role, assignment ID, and parent receipt
- Fresh repository path and object-store identity
- Baseline commit/tree and transferred-file inventory/hashes
- Contract, oracle-interface, assignment, and prompt/context hashes
- Sandbox profile and environment-manifest hashes
- Exact command, PID, agent/thread identity, start/end time, exit status
- Executable and tool hashes or version receipts
- Allowed/denied path results and environment/network results
- Output inventory, candidate commit/tree, and package hashes
- Lane-local cache/log paths and cleanup disposition
- Any repair finding, superseded candidate, and invalidated gates

Call this hash-bound process attestation, not a legal signature.

## Repair rule

Every repair must run through the launcher. A controller editing production
outside the boundary, even for one line, invalidates continuous isolation.
Require a new process receipt, candidate commit, deterministic packages, and
affected re-audits.

## Audit rule

Verify both:

1. No prohibited expression was detected.
2. Copying was technically prevented throughout every authoring and repair
   process.

These are separate claims. A clean contamination scan cannot replace missing
process receipts. Rebuilding existing implementation bytes under a sandbox
cannot repair unsandboxed authorship; create a fresh isolated reimplementation.
