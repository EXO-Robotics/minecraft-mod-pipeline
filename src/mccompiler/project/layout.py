from __future__ import annotations

from pathlib import Path


PROJECT_DIRECTORIES = (
    "input/source", "input/jars", "input/mods", "input/configuration",
    "analysis/evidence", "analysis/diagnostics", "analysis/source-index", "analysis/proposals",
    "ir", "decisions", "rights/evidence",
    "bedrock/behavior_pack", "bedrock/resource_pack", "bedrock/scripts",
    "custom/scripts", "custom/entities", "custom/models", "custom/assets",
    "assets/blockbench", "assets/previews", "assets/revisions",
    "tests", "runtime", "console", "dist/marketplace-candidate", "dist/test-world",
    "dist/reports", "reports", "analysis/distillation", "decisions/distillation", "distillation",
)

PROTECTED_DIRECTORIES = (
    "custom/scripts", "custom/entities", "custom/models", "custom/assets",
)

INITIAL_DOCUMENTS = {
    "analysis/inventory.json": {"schema_version": "1.0.0", "mods": [], "content": []},
    "analysis/dependency-graph.json": {"schema_version": "1.0.0", "nodes": [], "edges": []},
    "analysis/registrations.json": {"schema_version": "1.0.0", "registrations": []},
    "analysis/evidence/index.json": {"schema_version": "1.0.0", "evidence": []},
    "analysis/diagnostics/index.json": {"schema_version": "1.0.0", "diagnostics": []},
    "analysis/source-index/files.json": {"schema_version": "1.0.0", "files": []},
    "analysis/source-index/symbols.json": {"schema_version": "1.0.0", "symbols": []},
    "analysis/source-index/calls.json": {"schema_version": "1.0.0", "calls": []},
    "ir/content.json": {"schema_version": "1.0.0", "content": []},
    "ir/behaviors.json": {"schema_version": "1.0.0", "behaviors": []},
    "ir/state.json": {"schema_version": "1.0.0", "state": []},
    "ir/presentation.json": {"schema_version": "1.0.0", "presentation": []},
    "ir/ui-intent.json": {"schema_version": "1.0.0", "ui_intent": []},
    "ir/networking-intent.json": {"schema_version": "1.0.0", "networking_intent": []},
    "decisions/strategies.yaml": {"schema_version": "1.0.0", "strategies": []},
    "decisions/overrides.yaml": {"schema_version": "1.0.0", "overrides": []},
    "decisions/redesigns.yaml": {"schema_version": "1.0.0", "redesigns": []},
    "decisions/omissions.yaml": {"schema_version": "1.0.0", "omissions": []},
    "decisions/approvals.yaml": {"schema_version": "1.0.0", "approvals": []},
    "rights/rights-manifest.yaml": {"schema_version": "1.0.0", "content": []},
    "rights/review.yaml": {"schema_version": "1.0.0", "status": "REVIEW_REQUIRED", "reviews": []},
    "assets/registry.json": {"schema_version": "1.0.0", "assets": []},
    "assets/visual-style-profile.json": {"schema_version": "1.0.0", "status": "UNCONFIGURED"},
    "decisions/distillation/review-adjustments.json": {"schema_version": "1.0.0", "adjustments": []},
}


def ensure_layout(root: Path) -> None:
    for relative in PROJECT_DIRECTORIES:
        (root / relative).mkdir(parents=True, exist_ok=True)
