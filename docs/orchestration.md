# Durable multi-worker orchestration

The orchestration layer turns the compiler's individual operations into a
recoverable dependency graph. It is intentionally separate from Java scanning,
Bedrock generation, clean-room production, audit, and BDS qualification.
The Studio is the production host and source of truth. Other machines may be
consulted as references, but their paths, queues, runtimes, and worker state are
never imported as authority.

## What it automates

- Transactional job claims shared by multiple threads or worker processes.
- Dependency-aware scheduling and lane filters.
- Bounded concurrency, priorities, retries, and exponential backoff.
- Worker leases, heartbeats, and dead-worker recovery.
- Quarantine after the declared attempt limit.
- Append-only event history and per-attempt receipts.
- Hash-bound inputs, output inventories, and atomic local transfers.
- Explicit human gates for rights, contract approval, publication, and release.
- External validation of clean-room production-process receipts.

It never converts a failed run into a pass, overwrites an existing transfer
destination, uses a shell to interpret commands, or treats its own queue receipt
as proof of production-process isolation.

## Queue states

```text
WAITING ──dependencies pass──> READY ──claim──> RUNNING ──success──> SUCCEEDED
                                      │             │
                                      │             ├─ retry budget ─> RETRY_WAIT
                                      │             └─ exhausted ────> QUARANTINED
                                      │
manual authority gate: WAITING ───────┴─> AWAITING_APPROVAL ──approve──> SUCCEEDED

failed prerequisite ───────────────────────────────────────────> BLOCKED
```

`retry` is an operator action for a quarantined or blocked job. It requires an
operator, reason, and explicit additional-attempt budget. It preserves the old
attempt numbers and receipts, then re-evaluates dependent jobs. Use it only
after a material repair or changed external condition:

```sh
bedrock-factory --db /absolute/queue.sqlite3 retry JOB_ID \
  --operator "$USER" \
  --reason "sandbox profile v2 frozen after denied-path repair" \
  --additional-attempts 1
```

## Start a campaign

Install or refresh the repository entry points:

```sh
python3.11 tools/bootstrap.py
```

Copy and edit
`examples/orchestration/java-to-bedrock-campaign.example.json`. Every path must
be absolute and every input or sandbox-profile hash must identify the actual
frozen bytes.

```sh
.venv/bin/bedrock-factory \
  --db .mccompiler/orchestration.sqlite3 \
  init

.venv/bin/bedrock-factory \
  --db .mccompiler/orchestration.sqlite3 \
  create --definition /absolute/path/to/campaign.json

.venv/bin/bedrock-factory \
  --db .mccompiler/orchestration.sqlite3 \
  run --concurrency 4 --runtime-root .mccompiler/runtime
```

When a manual gate becomes ready:

```sh
.venv/bin/bedrock-factory \
  --db .mccompiler/orchestration.sqlite3 \
  approve authorize-evidence \
  --operator "$USER" \
  --reason "operation-level rights ledger reviewed"
```

Inspect state and history:

```sh
.venv/bin/bedrock-factory \
  --db .mccompiler/orchestration.sqlite3 status \
  --campaign replace-me-java-to-bedrock-v1

.venv/bin/bedrock-factory \
  --db .mccompiler/orchestration.sqlite3 events \
  --campaign replace-me-java-to-bedrock-v1
```

Use `run --forever` under `launchd` for continuous processing. Run the command
from the repository's Python 3.11 environment and give each daemon a stable
`--db` and `--runtime-root`.

Render a Studio launch agent after choosing those absolute paths:

```sh
.venv/bin/python tools/render_orchestrator_launchd.py \
  --repository "$PWD" \
  --db "$PWD/.mccompiler/orchestration.sqlite3" \
  --runtime-root "$PWD/.mccompiler/runtime" \
  --concurrency 4 \
  --output "$PWD/.mccompiler/com.mccompiler.orchestrator.plist"
```

Inspect that generated plist before copying it to
`~/Library/LaunchAgents/com.mccompiler.orchestrator.plist` and loading it with
`launchctl`. The repository does not install or load a background agent
silently.

## Thread and process layout

For one Studio, start with four general workers. For heavier campaigns, use
separate long-running pools against the same database:

```sh
# Evidence/control work
bedrock-factory --db /absolute/queue.sqlite3 run --forever \
  --concurrency 6 --lane EVIDENCE --lane CONTROL \
  --runtime-root /absolute/runtime

# Evidence-blind production: intentionally bounded
bedrock-factory --db /absolute/queue.sqlite3 run --forever \
  --concurrency 2 --lane PRODUCTION --lane INTEGRATION \
  --runtime-root /absolute/runtime

# Read-only audit and qualification
bedrock-factory --db /absolute/queue.sqlite3 run --forever \
  --concurrency 3 --lane AUDIT --lane QUALIFICATION \
  --runtime-root /absolute/runtime
```

SQLite WAL mode safely coordinates multiple local processes. This is the right
first deployment for one Studio and hundreds to low thousands of campaign jobs.
Do not place the SQLite file on NFS or synchronize it with Tailscale. To scale
to several hosts, keep this job and receipt contract but replace the store with
a central PostgreSQL/API broker; transfer immutable artifacts through an object
store or a receipt-bound SSH/rsync adapter. The current built-in transfer
adapter is deliberately local-only and hash-verifies bytes before atomic
placement.

## Clean-room production rule

`PRODUCTION` and `INTEGRATION` command jobs fail closed unless their payload
contains:

- The absolute path and SHA-256 of a frozen sandbox profile, or the exact
  SHA-256 of the Studio launcher that freezes the profile before worker start.
- `process_receipt_required: true`.
- The absolute process-receipt output path.
- A validator command that must accept that receipt.

The external launcher must still create and enforce the actual deny-by-default
boundary. The queue does not manufacture isolation by itself. Evidence and
control material must never appear in a production payload, working directory,
Git object store, environment, cache, or output receipt.

The repository's Studio-native launcher is
`tools/production_sandbox/studio_launcher.py`. It is backend-neutral: its worker
command is an explicit JSON argv file, its environment is cleared, and network
access is denied. It does not assume another host's model service, paths,
credentials, repository, or runtime state.

The worker command file is a JSON argv array whose executable is absolute:

```json
[
  "/absolute/path/to/the/studio/worker",
  "--assignment",
  "inputs/01-assignment.json"
]
```

The launcher creates a fresh Studio-local repository, transfers only the
assignment, sanitized contract, and prompt, applies four required denial
classes, launches the actual worker, verifies the inputs remained unchanged,
scans for credentials and the canary, and writes
`runtime/process-receipt.json`. Because the default profile denies all network
access, the worker must be locally executable and must not depend on a cloud
API. Any future network-enabled profile is a new security boundary and must be
separately frozen, reviewed, and requalified.

## Java-to-Bedrock scheduling

Use the campaign gate order:

```text
TARGET_FROZEN → INVENTORY_COMPLETE → CLEAN_ROOM_CONTRACTED →
PRODUCTION_ACTIVE → STATIC_QUALIFIED → GOLDEN_QUALIFIED →
INTEGRATED → AUDITED → BDS_QUALIFIED → BUNDLE_FROZEN
```

Independent evidence features can run in parallel. Shared Bedrock interfaces
and integration must be dependency-ordered. Custom hero assets should normally
use no more than two concurrent production slots. A production candidate may
advance only after its exact process receipt and hashes validate. Rights,
contract sanitization, publication, Marketplace, and release remain explicit
human authority gates.
