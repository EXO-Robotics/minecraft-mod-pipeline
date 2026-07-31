# Crazy Craft bounded MacBook → Mac Studio execution

## Scope

This is a narrow file-and-command protocol for four closed job types:

- `EVIDENCE_RECOVERY`
- `PRIVATE_CANDIDATE_AUDIT`
- `BDS_QUALIFICATION`
- `COMBINED_PRIVATE_AUDIT_AND_QUALIFICATION`

It is not an API, daemon, mailbox, database, scheduler, production launcher, or
campaign controller. The MacBook remains the source of orchestration,
production, packaging, promotion, and final authority. No campaign assignment
is issued by this substrate.

The implementation binds the prior stabilization authority:

- content commit `dd77b32ec04d9290b3e3106f2eeb42681eaa793b`
- content tree `7e752728e3b7c4e49331e4d0459a0eede1175cd1`
- containing go/no-go commit `e94939c2d90fb9deda2d1edbadd49478763463a3`
- canonical state `a50b999420dc24d41807a68ed5978829d2280c5447fe7dbdfe8c9d44d1666603`

## Authority and clean-room roles

### T1

T1 may submit evidence-recovery and exact-package BDS requests. Evidence jobs
return only opaque contract IDs, abstract state transitions, persistence,
ownership, restart, multiplayer and platform-facing requirements,
contradictions, and proof boundaries. T1 retrieves the allowlisted result set;
it never recursively retrieves the job input tree.

### T10

T10 may submit private candidate audits, BDS qualification, or their combined
form after immutable candidate freeze and mechanical preflight. Results contain
only opaque finding/contract IDs, abstract defects, allowed repair scope,
required regression IDs, qualification references, and proof boundaries.

### T2–T9

Ordinary workers receive sanitized results through MacBook control authority.
They do not submit remote jobs. They must not inherit `SSH_AUTH_SOCK`, T1/T10
identity paths, Studio aliases with usable credentials, raw job inputs, private
oracle material, or result roots beyond their approved sanitized transfer.

The current Codex tasks share one MacBook OS user. Instructions and file modes
alone cannot prevent another same-user process from reading that user's SSH
keys. Hard worker denial therefore requires either:

1. T1/T10 keys held by a separate local service identity; or
2. T1/T10 job submission performed by a protected service outside worker
   process authority.

Until that exists, `WORKER_PRIVILEGED_KEY_ACCESS_DENIED` and
`MACBOOK_PRODUCTION_ISOLATION_READY` cannot pass.

## Remote layout

The installed Studio root is:

```text
~/crazycraft-remote-jobs/
├── incoming/
├── active/
├── completed/
├── failed/
├── templates/
└── runtime/
```

Each job is `JOB-` plus twelve decimal digits and contains:

```text
request.json
request.sha256
input-manifest.json
status.json
result.json
report.md
artifacts/
logs/
receipt.json
inputs/                  # never returned
```

The Studio owns the monotonic sequence. It serializes sequence acceptance under
`runtime/job-sequence.lock`, consumes each accepted ID exactly once, and
atomically renames `incoming/JOB-*` to `active/` and then to `completed/` or
`failed/`. Failed jobs retain a receipt. Terminal cleanup removes scratch
inputs/logs/runtime homes while preserving authority records.

## SSH deployment contract

The required aliases and keys are:

- `crazycraft-t1-remote` / `~/.ssh/crazycraft-t1-remote`
- `crazycraft-t10-remote` / `~/.ssh/crazycraft-t10-remote`

Both pin a dedicated known-hosts file, disable agent forwarding and all
forwardings, disallow PTY and local command execution, and use
`IdentitiesOnly=yes`. The corresponding Studio `authorized_keys` entries use
`restrict` and the fixed user-local dispatcher
`~/crazycraft-remote-runner/studio/forced_command.py`.

The forced command accepts only:

- `ingest <role> <validated-job-id>`
- `activate <role> <validated-job-id>`
- bounded status/result retrieval operations

`ingest` receives a canonical base64-framed bundle on standard input and writes
each manifest-declared regular file with exclusive, no-follow creation. It does
not run `scp`, `tar`, or an archive extractor. Request values never select an
executable, shell, image, arbitrary argv, environment, mount, or output path.
The current Studio account and keys have not been installed or verified; this
is a deployment contract, not a completed access claim.

## Input rules

The request and manifest are canonical JSON with self-excluding SHA-256 payload
hashes. Inputs are regular, single-link files under safe relative paths.
Absolute paths, traversal, hidden paths, symlinks, hardlinks, special files,
duplicate paths, wrong size, and wrong hash fail before execution.

Evidence and oracle roots remain read-only Studio paths and never become BDS
mounts. The request records their permitted scope for evidence/audit execution.
Production packages are transferred by exact hash and are staged in the job's
input directory only.

## Studio entrypoints

`studio/remote_job_entrypoint.py` is the only dispatcher. It validates:

- role ↔ job type;
- request and manifest hashes;
- monotonic ID;
- safe input and output paths;
- role-local transition;
- disclosure policy;
- output allowlist;
- receipt completeness and cleanup.

Live evidence/audit jobs invoke only the fixed sibling runner:

`~/crazycraft-remote-runner/studio/crazycraft_studio_codex_runner.py`

The runner pins `/opt/homebrew/bin/codex`, ignores user configuration and
rules, uses an ephemeral session, applies a fixed structured-output schema, and
does not accept commands from the request.

Live BDS jobs use a server-generated Docker argv. Requests cannot supply a
command. Synthetic mode exists only for committed non-sensitive protocol tests
and must not be installed as a forced-command option.

## BDS container policy

Each request binds exact candidate repository, commit/tree, BP/RP/MCAddon
hashes, BDS channel/version, image digest, fixtures, gates, port, container
name, CPU and memory.

The generated container policy enforces:

- digest-pinned image;
- one package authority per container;
- `--network none`;
- read-only root;
- fixed non-root UID/GID;
- all capabilities dropped;
- `no-new-privileges`;
- PID, CPU and memory limits;
- no restart;
- isolated tmpfs;
- exactly one read-only job-input mount;
- exactly one writable job-output mount;
- no Docker socket, user home, SSH material, evidence, oracle, other jobs, or
  MacBook repository mount.

Container startup alone is not a BDS pass. Exact server probes, restart,
persistence, warnings, crash state, fixture identity, output hashes, and
cleanup must be present in the returned qualification receipt.

## Result boundary

The MacBook retrieves only:

- `result.json`
- `report.md`
- `receipt.json`
- `status.json`
- allowlisted `artifacts/`

It does not retrieve `inputs/`, `logs/`, evidence roots, oracle roots, hidden
cases, runtime homes, or arbitrary remote paths. Retrieved output is scanned
for private-key material, credential markers, private oracle values, hidden
case values, decompiled Java markers, Java source paths, and source
identifiers. A match deletes the local retrieval and fails closed.

## Receipt boundary

Every terminal job records request/manifest hashes, role, host/executor,
timestamps, fixed entrypoint, declared evidence/candidate accesses, output
inventory, disclosure scan, exit status, cleanup, container/session IDs, proof
boundary, and a deterministic local envelope.

The local envelope is tamper-evident only. A production authority requires a
verified Studio result signer or protected service identity.

## Current deployment status

Live deployment is active under the shared Studio account `blakestudio`:

- dedicated ED25519 T1 and T10 identities are installed with role-specific
  forced commands;
- the Studio ED25519 host key is pinned;
- live T1 evidence-return JOB-5 and T10 audit-return JOB-4 completed with
  disclosure-scanned results and receipts;
- role confusion and arbitrary shell probes returned 126;
- a wrong package hash failed before Docker and duplicate job reuse failed;
- two fixed network-disabled Studio containers ran concurrently with disjoint
  names, inputs, outputs, and logical ports.

The Studio contains the exact frozen Crazy Craft archive at SHA-256
`daaa5afdea5795bac139a3b327e268b3f11b65a3909753f2ff313adadb17cef3`.
No raw evidence was used by the synthetic jobs.

This is a live substrate, not a production-isolation pass. Both remote keys are
owned by the same MacBook OS user, both forced keys terminate in the same
Studio OS account, and Codex evidence reads are instruction-scoped rather than
OS-confined to declared roots. No exact Stable/Preview BDS runtime ran.
