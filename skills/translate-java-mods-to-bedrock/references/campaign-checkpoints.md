# Campaign checkpoints and classifications

Use this reference when preparing a reconstruction wave, promoting a pilot or
segment, or assigning a final readiness label.

## Prepare a wave

Group work by reusable Bedrock technical patterns and a coherent player-facing
dependency graph. Require at least one selected role for each claimed category.
Keep evidence in analysis and expose only opaque intent IDs and sanitized
contracts to production.

For this portable factory, freeze the authorized intake first:

```bash
.venv/bin/bedrock-factory \
  --db .mccompiler/factory-v1/orchestration.sqlite3 \
  factory-plan \
  --modpack ABSOLUTE_PATH_TO_AUTHORIZED_MODPACK \
  --output-root .mccompiler/factory-v1/campaigns/CAMPAIGN_ID \
  --authority RECORDED_AUTHORITY
```

Use `$make-java-to-bedrock-task-packs` to turn the hash-bound plan into evidence,
control, production, qualification, audit, and integration assignments.

Treat `PENDING_AUTHORIZED_EVIDENCE` as the honest initial state. Advance only
when the required evidence and preceding gates exist.

## Evidence progression

Use these states without inventing synonyms:

- `PENDING_AUTHORIZED_EVIDENCE`
- `EVIDENCE_RECORDED`
- `INTENT_DISTILLED`
- `CLEAN_ROOM_CONTRACTED`
- `IMPLEMENTED`
- `STATIC_QUALIFIED`
- `BDS_QUALIFIED`
- `DESKTOP_VERIFIED`
- `PS4_VERIFIED`

## Pilot checkpoints

- `AUTHORIZED_FEATURE_PACKAGE_REQUIRED`
- `JAVA_PILOT_CANDIDATE_QUALIFIED`
- `PILOT_READY_FOR_CLEANROOM_PRODUCTION`
- `CANDIDATE_READY_FOR_INDEPENDENT_AUDIT`
- `TRANSLATION_LOOP_PROVEN`
- `TRANSLATION_LOOP_PROVEN_WITH_LIMITATIONS`

Stop at readiness unless implementation is authorized. Use a limitation result
only for explicit non-material client or harness gaps. It cannot hide rights,
isolation, lineage, originality, deterministic-build, semantic, or Stable-BDS
failure.

## Segment and portfolio checkpoints

- `SEGMENT_TRANSLATION_LOOP_PROVEN_WITH_LIMITATIONS`
- `JAVA_TO_BEDROCK_PIPELINE_PROVEN_AT_SEGMENT_SCALE_WITH_PLATFORM_LIMITATIONS`
- `REAL_JAVA_MOD_SUBSYSTEM_RECONSTRUCTION_PROVEN_WITH_PLATFORM_LIMITATIONS`
- `PARTIAL_CANDIDATE_FROZEN`
- `PORTFOLIO_FREEZE_PROVEN_WITH_PLATFORM_LIMITATIONS`

Use segment-success classifications only when the exact candidate passes its
frozen semantic oracle and mutations, contamination/originality,
lineage/isolation, deterministic rebuild, and required Stable/Preview BDS
gates. Keep protocol-player, retail client, authenticated identity, controller,
Realms, split-screen, and physical PS4 pending unless their exact gates ran.

Freeze a partial candidate when useful technical evidence exists but a
non-waivable gate remains failed or unproven. Preserve the exact package and
receipts, but do not create a full-success tag.
