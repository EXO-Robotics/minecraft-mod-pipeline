# Java-origin clean-room readiness

Use this reference for candidate acquisition, private pilot qualification,
oracle construction, sanitized transfer, and production isolation.

## 1. Separate rights by operation

Record independent states for:

- Acquisition
- Metadata and license inspection
- Static source analysis
- Bytecode inspection and decompilation
- Runtime observation
- Documentation analysis
- Abstract behavior extraction
- Independent private reimplementation
- Source-code, asset, and branding reuse
- Commercial distribution
- Marketplace submission

Use `EXPLICITLY_PERMITTED`, `PERMITTED_BY_APPLICABLE_LICENSE`,
`PERMITTED_FOR_PRIVATE_TECHNICAL_EVALUATION`, `PROHIBITED`,
`NOT_NEEDED_FOR_PILOT`, `UNRESOLVED`, `CONFLICTING_TERMS`, or
`LEGAL_REVIEW_REQUIRED`.

Do not treat `UNRESOLVED` as permission. Do not block a private,
non-distributed pilot solely because source reuse, commercial distribution, or
Marketplace submission is unresolved; those operations are not required for
the pilot.

## 2. Freeze the evidence lane

Preserve:

- Exact source origin, commit, tag, archive, license, and dependency pins
- Per-file SHA-256 records and an aggregate source-tree hash
- An unmodified read-only raw source
- A separately cloned working analysis copy
- Lane-local temporary, cache, log, and runtime directories

Do not decompile when exact source is available. Do not claim runtime evidence
when only static source was inspected.

Qualify a candidate only when the package is authentic, immutable, lawfully
acquired, technically bounded, and supported for every operation the pilot
will actually perform. Use `JAVA_PILOT_CANDIDATE_QUALIFIED`; keep distribution
and Marketplace states separate.

## 3. Normalize semantics

For each decision, preserve three explicit layers:

```text
source observation (control only)
→ abstract functional requirement
→ product-selected production requirement
```

Classify product selection as `REQUIRED`, `OPTIONAL`, `REDESIGNED`, `OMITTED`,
or `MORE_EVIDENCE_REQUIRED`.

Classify equivalence as `EXACT_INVARIANT`, `RANGE_EQUIVALENT`,
`FUNCTIONALLY_EQUIVALENT`, `INTENTIONALLY_REDESIGNED`, or
`OMITTED_WITH_APPROVAL`.

Classify unknowns as `REQUIRES_RUNTIME_EVIDENCE`,
`PRODUCT_DECISION_REQUIRED`, `SAFE_TO_OMIT`,
`BEDROCK_NATIVE_POLICY_REQUIRED`, or `OUTSIDE_PILOT_SCOPE`.

Do not reward presentation or internal similarity for intentionally redesigned
requirements. Do not present Bedrock-native restart, persistence, cleanup, or
multiplayer policy as source-equivalent evidence.

## 4. Split the oracle

Freeze the private oracle before production. Include:

- Required states, triggers, transitions, and tolerance ranges
- Public and hidden edge cases
- Duplicate-delivery and late-callback tests
- Disconnect, death, item loss, dimension change, restart, and corrupt-state
  behavior
- Two-player and four-player isolation
- Workload caps, cleanup deadlines, and endurance cases
- Mutation tests that prove the suite detects missing invariants

Give production only an oracle interface containing observable requirements,
tolerances, lifecycle policy, multiplayer ownership, and performance caps.
Never transfer hidden cases, mutation details, evidence references, or source
identity.

## 5. Sanitize the contract

Reject production-facing artifacts containing:

- Candidate, feature, author, namespace, class, method, or asset names
- Source paths, protocols, commit IDs, archive or manifest hashes
- Loader, bytecode, or implementation details
- Source prose, localization, comments, coordinates, layouts, timing constants,
  or distinctive combinations not required by product selection

Review every exact value. Permit only justified invariants, original product
selections, tolerance ranges, or Bedrock safety caps. Require
`CONTRACT_SANITIZED` before creating production.

## 6. Build an independent production repository

Do not use a normal worktree when restricted control objects share the same Git
database. Do not assume `--no-hardlinks` is sufficient: a local clone may copy
unreachable restricted objects.

Preferred sequence:

```bash
git clone --no-local --single-branch \
  --branch QUALIFIED_BASELINE_BRANCH \
  BASELINE_REPOSITORY PRODUCTION_REPOSITORY
git -C PRODUCTION_REPOSITORY remote remove origin
git -C PRODUCTION_REPOSITORY switch -c PRODUCTION_BRANCH
```

Transfer only:

- Sanitized production contract
- Production oracle interface
- Neutral infrastructure references and role instructions

Verify:

- Parent commit equals the qualified baseline
- No remotes or alternates
- No hardlinked Git objects or cross-lane symlinks
- Restricted control and source commits return `NOT_AVAILABLE`
- Production delta contains only the approved transfer files
- Contract/interface hashes match the frozen control copies
- Private oracle and implementation artifacts are absent

If any restricted object is present, discard that generated production clone
and rebuild through transport. Do not merely delete refs.

## 7. Enforce process isolation

Use a deny-by-default OS sandbox or equivalent with:

- Production repository as the only project read root
- A separate runtime root as the only write root
- Lane-local `HOME`, `TMPDIR`, and cache variables
- Evidence and control roots denied
- Network and external services denied unless separately authorized
- A clean environment rather than inherited variables

Place a hidden canary in the evidence lane. From the sandboxed production
process, verify:

- Approved contract: `READABLE`
- Evidence root, source manifest, private oracle, and canary: `DENIED`
- Candidate identifiers and restricted hashes: `NO_MATCH`
- Evidence-related environment variables: `NONE`
- Restricted Git objects: `NOT_AVAILABLE`

Record the sandbox profile hash. If sandbox application is unavailable or any
denial test does not pass, use `ISOLATION_NOT_PROVEN`. Future production work
must use the same profile; bypass invalidates readiness.

Launch the actual authoring agent inside the boundary. Do not treat
`fork_turns:none`, a source-neutral prompt, or a standalone repository as proof
that its process could not read evidence. If the native collaboration runtime
cannot inherit and attest the boundary, use a sandboxed agent launcher or stop.

Tool-loader repairs may require narrowly adding public runtime or developer
tool paths. Hash every revised profile and environment manifest. Before and
after each production repair, rerun write-allow and evidence/control/canary
denial probes from the actual execution context. Bind the receipt to:

- Production prompt hash and connected-agent/thread identifier
- Candidate and metadata-freeze commits
- Sandbox and environment-manifest hashes
- Contract and oracle-interface readability
- Evidence, private-oracle, and canary denial
- Remotes, alternates, restricted objects, symlinks, and environment checks

Remove temporary authentication copies and lane-local agent caches after the
run. Preserve a credential-free invocation receipt; a missing repair receipt
is a lineage gap even when the original readiness test passed.

Run a one-feature sandbox rehearsal before the first large campaign or after
changing the launcher. Include one repair and prove that the repair process,
not only the final rebuild, ran inside the boundary.

## 8. Implement, freeze, audit, and repair

When implementation is explicitly authorized:

1. Run a fresh production agent with only the approved transfer package.
2. Build and test deterministically at least twice.
3. Commit the implementation and generated package as an immutable candidate.
4. Add only candidate/freeze references in a metadata-only child commit.
5. Give a fresh auditor read-only access after freeze.
6. Preserve every failed candidate and its audit; never amend or overwrite it.
7. Return accepted findings to production as abstract contract defects only.
8. Create a new candidate/freeze pair for every repair and rerun affected gates.

The authoritative suite must execute the frozen candidate logic, not merely a
parallel production model. Include mutation tests. For item-use state machines,
test an identical same-type replacement in the same slot: slot/type/durability
equality is not item identity. A stable repair for non-stackable items is a
unique per-operation `ItemStack` dynamic property checked on every continuation
and completion.

Keep automatic item cooldown components out of mechanics where bind or failed
uses must not cool down. Apply cooldown explicitly only after the successful
server-authoritative outcome.

## 9. Qualify BDS evidence narrowly

Extract package bytes from the immutable candidate commit and verify their
digest before building a test world. If a generic BDS runner requires a
runtime-initialization marker the candidate does not emit, add a separate
test-only marker pack and probe the candidate's own marker independently.
Never patch the candidate merely to satisfy the harness.

Record Stable and Preview versions, server-binary hashes, image digest, world
hash, restart count, clean logs, and exact package hash. Classify pack/script
boot separately from gameplay. If SimulatedPlayer cannot deliver the
production item-use event or preserve real player identity across restart,
leave those claims pending desktop/Realm testing.

## 10. Attest and stop

Hash and connect:

- Evidence manifest
- Product selection and equivalence classification
- Private oracle and production interface
- Sanitized contract and sanitization report
- Isolation manifest and negative-access results
- Sandbox profile
- Production commit, tree, Git-object inventory, and input manifest
- Every transferred file and its receipt

Cryptographic lineage is not a legal signature or rights clearance.

Use `PILOT_READY_FOR_CLEANROOM_PRODUCTION` only when all readiness gates pass
and the production delta contains no implementation. Stop before BP, RP,
scripts, assets, tests, packages, BDS, desktop, Realm, PS4, Marketplace, or
release work unless a later task explicitly authorizes it.

After implementation, require separate passes for rights/evidence, contract,
oracle, process isolation, lineage, semantic integrity, originality,
deterministic packaging, and exact-package Stable/Preview BDS. Pending desktop,
Realm, or physical PS4 evidence must remain visible and never be inferred from
BDS.

Do not use a limitations result when any actual production or repair process
lacks a valid receipt. Use `CLEANROOM_BOUNDARY_FAILED` or
`ISOLATION_NOT_PROVEN`. Preserve a technically useful candidate separately from
the clean-room classification.
