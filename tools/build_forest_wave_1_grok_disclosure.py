#!/usr/bin/env python3
"""Build the authorized, sanitized Forest Wave 1 Batch 1 Grok disclosure."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "production/batches/forest-wave-1-parallel-batch-1"
RED_TEAM = BATCH / "red-team"
BUNDLE = RED_TEAM / "disclosure-bundle"
BASE = "e9009b70502f4e0db57986ea52cf8d4f7998cc1b"
HEAD = "01c58486030699cf65a19a4e2da30d7ddb4b7cfb"
FEATURES = (
    "signal_ruin",
    "gloamwing_stalker",
    "forest_attunement",
    "mossback_forager",
    "barkguard_charm",
)

FILES = [
    "production/batches/forest-wave-1-parallel-batch-1/batch-preflight.json",
    "production/batches/forest-wave-1-parallel-batch-1/reservations.json",
    *[
        f"production/batches/forest-wave-1-parallel-batch-1/assignments/{feature}.json"
        for feature in FEATURES
    ],
    *[
        f"production/reconstruction-waves/forest-wave-1/{feature}/original-production-manifest.json"
        for feature in FEATURES
    ],
    *[
        f"production/features/{feature.replace('_', '-')}/reports/candidate-packet.json"
        for feature in FEATURES
    ],
    "production/features/signal-ruin/reports/artifact-manifest.json",
    "production/features/signal-ruin/reports/revision-history.json",
    "production/features/gloamwing-stalker/reports/build-report.json",
    "production/features/gloamwing-stalker/reports/revision-history.json",
    "production/features/forest-attunement/reports/artifact-manifest.json",
    "production/batches/forest-wave-1-parallel-batch-1/reports/candidate-review.json",
    "production/batches/forest-wave-1-parallel-batch-1/reports/workload-measurement.json",
    "production/batches/forest-wave-1-parallel-batch-1/reports/blockbench-round-trip.json",
    "production/batches/forest-wave-1-parallel-batch-1/reports/creator-tools.json",
    "production/batches/forest-wave-1-parallel-batch-1/reports/integration-artifact-manifest.json",
    "production/batches/forest-wave-1-parallel-batch-1/reports/bds-qualification-summary.json",
    "production/batches/forest-wave-1-parallel-batch-1/reports/stable-bds-result.json",
    "production/batches/forest-wave-1-parallel-batch-1/reports/preview-simulated-player-result.json",
    "production/batches/forest-wave-1-parallel-batch-1/reports/checkpoint-manifest.json",
    "production/batches/forest-wave-1-parallel-batch-1/reports/qualification-report.md",
    "tools/build_forest_wave_1_parallel_batch_1.py",
    "tools/run_forest_wave_1_parallel_batch_1_bds.py",
    "tests/test_parallel_batch_preflight.py",
    "tests/test_forest_wave_1_parallel_batch_1_integration.py",
    *[f"tests/test_{feature}.py" for feature in FEATURES],
]

PURPOSES = {
    "original-production-manifest.json": "Original-production contract",
    "candidate-packet.json": "Candidate evidence packet",
    "revision-history.json": "Candidate revision evidence",
    "artifact-manifest.json": "Artifact hash evidence",
    "build-report.json": "Candidate build evidence",
    "batch-preflight.json": "Batch policy and immutable base",
    "reservations.json": "Shared identifier and UUID reservations",
    "candidate-review.json": "Main Codex candidate dispositions",
    "workload-measurement.json": "Concurrency and workload evidence",
    "blockbench-round-trip.json": "Serialized Blockbench GUI evidence",
    "creator-tools.json": "Creator Tools availability status",
    "integration-artifact-manifest.json": "Combined artifact hash evidence",
    "bds-qualification-summary.json": "BDS qualification summary",
    "stable-bds-result.json": "Stable BDS evidence",
    "preview-simulated-player-result.json": "Preview BDS diagnostic evidence",
    "checkpoint-manifest.json": "Pre-review checkpoint state",
    "qualification-report.md": "Human-readable qualification report",
}


def sanitized(text: str) -> str:
    text = text.replace(str(ROOT), "<WORKSPACE>")
    text = re.sub(r"/Users/[^/\s\"']+", "<USER_HOME>", text)
    text = text.replace("blakegrove", "<USER>")
    return text


def write_text(relative: str, text: str) -> None:
    target = BUNDLE / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(sanitized(text), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def purpose_for(relative: str) -> str:
    name = Path(relative).name
    if relative.startswith("assignments/"):
        return "Bounded candidate assignment"
    if relative.startswith("tests/"):
        return "Automated qualification test"
    if relative.startswith("tools/"):
        return "Minimum integration and BDS orchestration context"
    return PURPOSES.get(name, "Authorized qualification context")


def main() -> None:
    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    BUNDLE.mkdir(parents=True)

    copied: list[str] = []
    for relative in FILES:
        source = ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(relative)
        bundle_relative = relative
        write_text(bundle_relative, source.read_text(encoding="utf-8"))
        copied.append(bundle_relative)

    diff_scopes = [
        "production/features/signal-ruin/bedrock/behavior_pack/scripts/signal_ruin.js",
        "production/features/signal-ruin/bedrock/behavior_pack/entities/signal_ruin_anchor.json",
        "production/features/signal-ruin/bedrock/behavior_pack/manifest.json",
        "production/features/gloamwing-stalker/behavior_pack/entities/gloamwing_stalker.json",
        "production/features/gloamwing-stalker/behavior_pack/spawn_rules/gloamwing_stalker.json",
        "production/features/gloamwing-stalker/behavior_pack/manifest.json",
        "production/features/forest-attunement/behavior_pack/scripts/main.js",
        "production/features/forest-attunement/behavior_pack/scripts/state.js",
        "production/features/forest-attunement/behavior_pack/manifest.json",
        "production/features/mossback-forager/bedrock/behavior_pack/entities/mossback_forager.json",
        "production/features/mossback-forager/bedrock/behavior_pack/manifest.json",
        "production/features/barkguard-charm/bedrock/behavior_pack/scripts/main.js",
        "production/features/barkguard-charm/bedrock/behavior_pack/manifest.json",
    ]
    diff = subprocess.run(
        [
            "git",
            "diff",
            "--no-ext-diff",
            "--no-renames",
            "--unified=3",
            BASE,
            HEAD,
            "--",
            *diff_scopes,
            ":(exclude)**/*.png",
            ":(exclude)**/*.bbmodel",
            ":(exclude)**/*.mcstructure",
            ":(exclude)**/*.zip",
            ":(exclude)**/*.mcaddon",
            ":(exclude)**/*.mcworld",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    write_text("candidate-diffs/forest-wave-1-parallel-batch-1.patch", diff)
    copied.append("candidate-diffs/forest-wave-1-parallel-batch-1.patch")

    prompt = """\
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
"""
    write_text("REVIEW_PROMPT.md", prompt)
    copied.append("REVIEW_PROMPT.md")

    groups = {
        "CONTRACTS_AND_ASSIGNMENTS.md": [
            item
            for item in copied
            if "/original-production-manifest.json" in item
            or "/assignments/" in item
            or item.endswith("batch-preflight.json")
            or item.endswith("reservations.json")
        ],
        "FEATURE_TESTS.md": [
            item
            for item in copied
            if item.startswith("tests/") and "parallel_batch" not in item
        ],
        "INTEGRATION_TESTS_AND_ORCHESTRATION.md": [
            item
            for item in copied
            if item.startswith("tools/")
            or (item.startswith("tests/") and "parallel_batch" in item)
        ],
        "QUALIFICATION_EVIDENCE.md": [
            item
            for item in copied
            if "/reports/" in item and not item.endswith("original-production-manifest.json")
        ],
    }
    aggregate_text = {}
    for aggregate, sources in groups.items():
        sections = []
        for source in sources:
            sections.append(
                f"\n\n===== DISCLOSED SOURCE: {source} =====\n\n"
                + (BUNDLE / source).read_text(encoding="utf-8")
            )
        aggregate_text[aggregate] = "".join(sections).lstrip()

    patch_text = (BUNDLE / "candidate-diffs/forest-wave-1-parallel-batch-1.patch").read_text(
        encoding="utf-8"
    )
    shutil.rmtree(BUNDLE)
    BUNDLE.mkdir(parents=True)
    write_text("REVIEW_PROMPT.md", prompt)
    write_text("CANDIDATE_DIFF.patch", patch_text)
    for aggregate, text in aggregate_text.items():
        write_text(aggregate, text)
    copied = [
        "REVIEW_PROMPT.md",
        "CANDIDATE_DIFF.patch",
        *groups.keys(),
    ]

    entries = []
    for relative in sorted(copied):
        path = BUNDLE / relative
        provenance = groups.get(relative, [relative])
        entries.append(
            {
                "path": relative,
                "purpose": purpose_for(relative),
                "source_paths": provenance,
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    manifest = {
        "schema_version": "1.0.0",
        "authorization_scope": "FOREST_WAVE_1_PARALLEL_BATCH_1_GROK_RED_TEAM_ONLY",
        "source_commit": HEAD,
        "base_commit": BASE,
        "bundle_file_count": len(entries),
        "files": entries,
        "explicit_exclusions": [
            "Java or licensed source material",
            "Third-party assets",
            "Credentials, tokens, secrets, environment files, or personal information",
            "Unrelated repository files and Git history",
            "Textures, models, audio, structures, packaged worlds, and packaged add-ons",
        ],
    }
    RED_TEAM.mkdir(parents=True, exist_ok=True)
    (RED_TEAM / "disclosure-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
