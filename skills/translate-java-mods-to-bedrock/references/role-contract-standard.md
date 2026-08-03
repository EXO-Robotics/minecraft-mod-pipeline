# Pipeline role contract standard

Use this standard for every delegated analysis, sanitization, production,
integration, visual, audit, repair, BDS qualification, or portfolio-freeze
assignment.

## Assignment envelope

Every assignment is one JSON object with:

- `schema_version`: exactly `1.0.0`.
- `assignment_id`: stable opaque identifier.
- `role`: stable role alias from the mapping below.
- `skill`: exact installed skill name.
- `lane`: `EVIDENCE`, `CONTROL`, `PRODUCTION`, `INTEGRATION`, or `AUDIT`.
- `lane_root`: absolute authorized execution root.
- `allowed_read_paths`, `allowed_write_paths`, and `prohibited_paths`: explicit
  absolute boundaries.
- `input_artifacts`: non-empty path/SHA-256 records.
- `output_artifacts`: non-empty output paths or receipt identifiers.
- `required_checks` and `completion_state`: bounded success contract.
- `gate_authority`: gates this role may pass, fail, or leave pending.
- `stop_states`: non-empty fail-closed conditions.
- `requires_activation_attestation`: true for every role that may mutate production
  code, assets, packages, integration state, or repairs.

Do not put mutable branch heads, unbounded directories, secrets, source
expression, private-oracle cases, or hidden mutation values in an assignment.
Bind a mutable worktree through its immutable starting commit and expected input
hashes.

| Role alias | Skill | Lane |
|---|---|---|
| `evidence_analyst` | `analyze-java-mod-evidence` | `EVIDENCE` |
| `contract_steward` | `sanitize-java-bedrock-contracts` | `CONTROL` |
| `feature_producer` | `produce-bedrock-cleanroom-feature` | `PRODUCTION` |
| `visual_producer` | `produce-golden-blockbench-asset` | `PRODUCTION` |
| `segment_integrator` | `integrate-bedrock-subsystem` | `INTEGRATION` |
| `independent_auditor` | `audit-java-bedrock-cleanroom` | `AUDIT` |
| `visual_auditor` | `audit-golden-blockbench-asset` | `AUDIT` |
| `portfolio_auditor` | `audit-bedrock-portfolio-freeze` | `AUDIT` |
| `bds_qualifier` | `qualify-bedrock-candidate` | `AUDIT` |
| `observation_tester` | `observe-bedrock-factory-pack` | `AUDIT` |

## Lane authority

| Lane | May receive | Must not receive | May establish |
|---|---|---|---|
| `EVIDENCE` | Authorized Java material, rights records, observation tools | Bedrock production candidate | Evidence claims and source-side feature graph |
| `CONTROL` | Evidence claims, product decisions, private oracle workspace | Production implementation access | Sanitized contracts and restricted oracle interface |
| `PRODUCTION` | Sanitized contracts, approved infrastructure, original asset briefs | Java evidence, private oracle, hidden mutations | Implementation, static results, candidate freeze |
| `INTEGRATION` | Frozen production candidates and public interfaces | Java evidence and private oracle | Connected candidate and integration-local checks |
| `AUDIT` | Frozen candidate, receipts, authorized oracle/control material | Candidate mutation authority | Findings and gate classification only |

Audit roles are read-only. A repair is a new `PRODUCTION` or `INTEGRATION`
assignment, never an audit continuation.

An observation tester collects calibrated evidence and may classify collection
as ready, insufficient, client-required, inconclusive, or infrastructure
blocked. It does not own semantic PASS or product repair.

## Gate ledger

Record each gate as:

```json
{
  "status": "PASSED",
  "authority": "audit-java-bedrock-cleanroom",
  "artifact_sha256": "<64 lowercase hex>",
  "receipt": "relative/path/to/receipt.json",
  "classification": "exact_package_semantic_audit"
}
```

Allowed statuses are `PASSED`, `FAILED`, `BLOCKED`, `PENDING`,
`NOT_APPLICABLE`, and `SUPERSEDED_ASSERTION`.

A `PASSED` gate requires authority, an exact artifact hash, a receipt, and a
narrow evidence classification. `PENDING` and `BLOCKED` never inherit a package
hash as proof. Metadata-only repairs may carry a gate forward only when the
package hash is unchanged and the carry-forward receipt names both metadata
commits.

## Standard terminal classifications

- `CLEANROOM_BOUNDARY_FAILED`
- `ISOLATION_NOT_PROVEN`
- `INTEGRATED_ARTIFACT_ONLY`
- `TRANSLATION_LOOP_PROVEN`
- `TRANSLATION_LOOP_PROVEN_WITH_LIMITATIONS`
- `SEGMENT_TRANSLATION_LOOP_PROVEN_WITH_LIMITATIONS`
- `PARTIAL_CANDIDATE_FROZEN`
- `PORTFOLIO_FREEZE_PROVEN_WITH_PLATFORM_LIMITATIONS`

Do not invent a success synonym. Extend this standard and its validator before
introducing a new terminal classification.

Validate assignments and gate ledgers with:

```sh
python3 ~/.codex/skills/translate-java-mods-to-bedrock/scripts/validate_subagent_assignment.py \
  assignment.json --verify-files
python3 ~/.codex/skills/translate-java-mods-to-bedrock/scripts/validate_role_contract.py \
  assignment.json --gate-ledger gate-ledger.json
```

The first validator enforces detailed filesystem, sandbox, visual-role, and
hash constraints. The second enforces cross-role identity, lane authority, and
gate-ledger consistency. Both must pass.
