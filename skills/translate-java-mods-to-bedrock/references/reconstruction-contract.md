# Reconstruction contract

## Required separation

| Analysis-only | Production-safe |
| --- | --- |
| Source paths and URIs | Opaque intent ID |
| Java names and branding | Original product identity |
| Decompiled code and binaries | Abstract gameplay role |
| Source assets and hashes | Originality constraints |
| Runtime observation details | Selected behavior contract |
| Rights evidence documents | Rights disposition |

Reject a consumer artifact containing `analysis/`, `evidence://`,
`rights-ledger/`, source/decompiled paths, restricted hashes, or source
identities.

The production lane receives only a sanitized product contract, a
production-facing oracle interface, and approved Bedrock infrastructure
references. Keep the private oracle, hidden tests, transformation history,
rights records, evidence hashes, and candidate identity outside production.

Directory names are not isolation. A normal Git worktree shares the repository
object store and is unsuitable when the control branch contains restricted
material. A local clone may also copy unreachable restricted objects. Prefer a
single-branch clone through Git transport (`--no-local --single-branch`), remove
all remotes, prohibit alternates and hardlinks, and verify restricted commit
objects return `NOT_AVAILABLE`.

## Feature contract

Record:

- Stable lowercase feature ID and category.
- Abstract role and additive Minecraft purpose.
- Authorized evidence IDs and evidence state in analysis only.
- Gameplay Intent ID and clean-room contract.
- Expected BP, RP, script, structure, and Blockbench outputs.
- Dependencies and vanilla-compatibility constraints.
- Workload caps, cleanup, persistence, migration, and multiplayer semantics.
- Gate matrix for rights, intent, contract, assets/behavior, implementation,
  deterministic package, Creator Tools, BDS, multiplayer, persistence, cleanup,
  desktop presentation, PS4 planning, and physical PS4.

## Java-to-Bedrock redesign prompts

- What player-visible mechanic matters after removing Java code shape?
- Which implementation depends on loader hooks, mixins, custom rendering,
  packets, GUIs, or arbitrary JVM state?
- Can supported Bedrock components express the mechanic without scripts?
- If scripts are required, what is the bounded event-driven state machine?
- What controller-only interaction replaces keyboard or custom GUI behavior?
- How does the feature coexist with vanilla worlds and other add-ons?
- What is the four-player workload and cleanup failure mode?
- Which distinctive combination must be redesigned or omitted?

## Gate semantics

`PASSED` requires artifact-bound evidence. `PENDING` means work or testing has
not occurred. `BLOCKED` requires a named external or rights blocker.
`NOT_APPLICABLE` requires a rationale.

Creator Tools validates the frozen package profile. Stable BDS validates only
the exercised server-side path. Desktop testing establishes client rendering
and controls for that platform. Only a physical PS4 run establishes
`PS4_VERIFIED`.

`PILOT_READY_FOR_CLEANROOM_PRODUCTION` additionally requires:

- Explicit product selection and equivalence classes.
- Frozen private and production-facing oracle artifacts.
- `CONTRACT_SANITIZED` with a forbidden-expression scan.
- A production repository based on the recorded baseline.
- Exact transferred-file hash receipts.
- Evidence, private-oracle, source-identifier, restricted-hash, environment,
  cache, symlink, remote, alternate, and Git-object negative-access tests.
- A hidden evidence-lane canary that production cannot read.
- No implementation files in the production delta.

If process-level isolation is used, record the sandbox profile hash and require
all future production work to launch under it. Bypassing the profile invalidates
the readiness result.

Process isolation is mandatory for a clean-room success claim. Context
isolation, opaque prompts, repository separation, and a clean contamination
scan are necessary but do not prove technical prevention. Require a receipt
from the actual authoring process and every repair process. A later sandboxed
rebuild of existing implementation bytes cannot retroactively repair missing
authorship receipts.
