# Subagent orchestration

Use role skills to replace long repeated prompts. Main Codex remains responsible
for lane creation, authorization, packet construction, dependency ordering,
finding disposition, and final claims.

## Role routing

Use these tiers:

- **Tier 0 — campaign controller:** freezes targets, schedules work, promotes
  interfaces, selects candidates, and owns final classification.
- **Tier 1 — evidence/control leads:** may access evidence but never production.
- **Tier 1 — production section leads:** receive sanitized inputs only and must
  be launched by the production sandbox executor.
- **Tier 2 — feature owners:** own bounded behavior, assets, tests, provenance,
  and a local receipt. Routine work stops here.
- **Tier 3 — exceptional specialists:** visual or runtime specialists only for
  bosses, multipart creatures, complex equipment, or persistent systems. They
  inherit the same sandbox and may not spawn again.
- **Independent critics:** post-freeze, read-only semantic and
  originality/lineage/isolation roles.

| Role | Skill | May see | Must not see | Completion boundary |
|---|---|---|---|---|
| Evidence analyst | `$analyze-java-mod-evidence` | Authorized Java evidence and rights matrix | Bedrock production | Evidence claims and feature graph |
| Contract steward | `$sanitize-java-bedrock-contracts` | Claims, rights, product scope, private oracle workspace | Production implementation | Sanitized transfer package |
| Feature producer | `$produce-bedrock-cleanroom-feature` | Baseline, sanitized contract, production oracle interface | Java evidence, private oracle | Frozen feature candidate |
| Visual producer | `$produce-golden-blockbench-asset` | Typed visual contract, class profile, production asset lane | Control references, source visuals, private originality cases | Frozen visual candidate |
| Segment integrator | `$integrate-bedrock-subsystem` | Frozen production candidates and shared interfaces | Java evidence, private oracle | Frozen integrated candidate |
| Independent auditor | `$audit-java-bedrock-cleanroom` | All lanes after freeze, read-only | Write access to evidence or candidate | Final audit and BDS classification |
| Visual auditor | `$audit-golden-blockbench-asset` | Frozen visual candidate and authorized control set, read-only | Write access to production | Two-cycle critique, originality and asset qualification |

Do not assign evidence analysis and production to the same agent. Use a fresh
auditor after candidate freeze. Integration is a production role and must remain
evidence-blind.

Assign custom visual production and post-freeze visual audit to different
agents. The visual auditor returns opaque findings; the producer never receives
control-reference values, images, timings, hashes, or distinctive descriptions.

## Assignment packet

Give each subagent one JSON packet and a one-line prompt:

`Use $ROLE_SKILL with the assignment packet at /absolute/path/assignment.json.`

Validate it before dispatch:

```bash
python3 ~/.codex/skills/translate-java-mods-to-bedrock/scripts/validate_subagent_assignment.py \
  /absolute/path/assignment.json \
  --verify-files
```

Include:

```json
{
  "schema_version": "1.0.0",
  "assignment_id": "opaque-id",
  "role": "evidence_analyst",
  "lane_root": "/absolute/authorized/root",
  "allowed_read_paths": [],
  "allowed_write_paths": [],
  "prohibited_paths": [],
  "input_artifacts": [
    {"path": "/absolute/path", "sha256": "64-lowercase-hex"}
  ],
  "base_commit": null,
  "output_artifacts": [],
  "required_checks": [],
  "stop_states": [],
  "completion_state": "EXPECTED_STATE"
}
```

Visual production packets additionally include:

- Typed visual-contract and class-profile hashes.
- Fixed proof-render contract.
- Exact animation-clip and proof-view inventories.
- Tool versions, authoritative commands, output roots, and BDS target set.
- Canonical archive timestamp, entry ordering, and file-mode policy.
- Required native round-trip receipt and deterministic export manifest.
- Art and performance thresholds, without control-reference material.

Visual audit packets additionally include:

- Candidate commit, model/export/package hashes, proof inventory, and native
  receipt hashes.
- Authorized read-only control set and private originality cases.
- Audit-local writable scratch/report roots; all input lanes remain read-only.
- Tool versions, commands, mutation inventory, and frozen materiality policy.
- Two critique-cycle rubrics and exact collision checks.
- An opaque defect-output path readable by the producer.
- An outbound leak-scan rule and receipt path.

Use opaque assignment and requirement IDs in production packets. Do not place
source project names, Java identifiers, evidence hashes, private-oracle hashes,
or evidence paths in producer or integrator packets.

Every production-role packet must also bind the sandbox profile, environment
manifest, launcher hashes, lane-local `HOME`, `TMPDIR`, cache/log/index/build
roots, network policy, negative-access expectations, and process-receipt output.
Repair packets also bind the superseded candidate and parent receipt hash.

## Dispatch rules

1. Hash the packet and all declared inputs.
2. Create the lane/worktree before dispatch.
3. Validate allowed and prohibited paths from the agent's actual execution
   context.
4. Launch the actual production process through the recorded sandbox executor.
   A clean prompt without a process receipt is not isolation proof.
5. Give only the role skill and packet path; avoid retelling the full campaign.
6. Require the agent to restate its verified lane, inputs, output boundary, and
   stop conditions before mutation.
7. Require machine-readable results with checked hashes, PID, command,
   prompt/context hash, tool hashes, timestamps, and exit status.
8. Keep agents on independent dependency nodes parallel; serialize shared
   infrastructure and integration.
9. Route every repair through the same sandbox launcher, require a new receipt,
   and preserve superseded freezes.
10. Re-run isolation after every production repair.
11. Close idle agents after their bounded task completes.
12. After a package-affecting visual repair, freeze a new production commit,
    rebuild twice, re-run Creator Tools and Stable/Preview BDS, and re-audit
    affected originality and lineage gates.

## Active conversion usage

Store mutable project facts in assignment packets, not skill files. Bind every
packet to the active source commit, control checkpoint, Bedrock baseline,
worktree, contract hash, oracle-interface hash, and candidate dependency hashes
that the role is permitted to know. This lets the same role skills serve the
current subsystem and later modpack waves without stale embedded paths.
