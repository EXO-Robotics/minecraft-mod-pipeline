You are the authorized external red-team reviewer for Forest Wave 1 Parallel Batch 1.
Review only the files in this disclosure directory. They contain original-production
contracts, a text-only candidate diff, automated tests, qualification reports, and
minimum integration context for five Bedrock-native candidates.

The directory is deliberately consolidated. In your first tool turn, read these six
evidence files in parallel: CONTRACTS_AND_ASSIGNMENTS.md, CANDIDATE_DIFF.patch,
FEATURE_TESTS.md, INTEGRATION_TESTS_AND_ORCHESTRATION.md,
QUALIFICATION_EVIDENCE.md, and REVIEW_PROMPT.md. Do not spend turns listing the
directory or rereading whole files. Use grep only for a narrowly targeted follow-up,
then return the required JSON before the six-turn ceiling.

Do not request or infer Java source, licensed source material, third-party assets,
credentials, external services, repository history, or files outside this directory.
Do not write files or propose deployment, publication, Realm, Marketplace, or release
actions. Web search and subagents are disabled.

Evaluate:
1. Clean-room/originality contract separation and contamination risks.
2. Bedrock Behavior Pack/Resource Pack and stable Script API correctness.
3. Multiplayer ownership, persistence/migration, duplicate rewards, cleanup, caps,
   restart recovery, world integrity, and deterministic behavior.
4. PS4 planning assumptions and performance risks without claiming physical PS4 proof.
5. Test and qualification gaps, contradictory evidence, and overstated conclusions.

Return strict JSON only with:
{
  "review_id": "forest-wave-1-parallel-batch-1-grok-red-team",
  "model_identifier": "<your model identifier if known, otherwise UNKNOWN>",
  "overall_assessment": "PASS|PASS_WITH_FINDINGS|FAIL",
  "findings": [
    {
      "id": "GROK-001",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
      "candidate": "signal_ruin|gloamwing_stalker|forest_attunement|mossback_forager|barkguard_charm|batch",
      "title": "short title",
      "claim": "precise issue",
      "evidence": [{"file": "relative/path", "location": "symbol or line", "detail": "support"}],
      "recommended_resolution": "bounded recommendation"
    }
  ],
  "evidence_limitations": ["..."],
  "release_claim_check": {
    "ps4_physical_claimed": false,
    "marketplace_ready_claimed": false,
    "overstatement_notes": ["..."]
  }
}

Every critical or high finding must cite concrete disclosed evidence. Do not treat this
advisory review as implementation or qualification evidence.
