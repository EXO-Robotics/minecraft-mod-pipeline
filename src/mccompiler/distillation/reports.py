from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .model import PROVEN_PATTERNS


REQUIRED_ARTIFACTS = (
    "quarter-scope.yaml",
    "quarter-scope.json",
    "deferred-scope.yaml",
    "identity-map.md",
    "system-clusters.json",
    "scoring-report.json",
    "progression-graph.json",
    "conversion-roadmap.md",
    "pattern-coverage.json",
    "compiler-gap-analysis.md",
    "console-performance-risk.json",
    "rights-risk.json",
    "benchmark-plan.md",
    "executive-summary.md",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _bullets(rows: list[str], empty: str = "None.") -> str:
    return "\n".join(f"- {row}" for row in rows) if rows else empty


def render_reports(result: dict[str, Any], output: Path) -> list[dict[str, Any]]:
    output_root = output.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    root = output_root / "distillation"
    if root.is_symlink():
        raise ValueError("Refusing to write through a distillation directory symlink")
    root.mkdir(parents=True, exist_ok=True)
    if output_root not in root.resolve().parents:
        raise ValueError("Distillation output escapes the requested output root")
    selected_ids = set(result["selection"]["ids"])
    systems = result["systems"]
    selected = [row for row in systems if row["id"] in selected_ids]
    deferred = [row for row in systems if row["id"] not in selected_ids]
    quarter = {
        "schema_version": "1.0.0",
        "target": result["target"],
        "effort_budget_basis_points": result["effort_budget_basis_points"],
        "selection": result["selection"],
        "systems": selected,
        "review_adjustments_applied": result["review_adjustments_applied"],
    }
    deferred_doc = {
        "schema_version": "1.0.0",
        "systems": [
            {
                **row,
                "defer_reason": result["decisions"][row["id"]]["reasons"],
                "classification": result["decisions"][row["id"]]["classification"],
            }
            for row in deferred
        ],
    }
    clusters = {
        "schema_version": "1.0.0",
        "clusters": [
            {"id": row["id"], "name": row["name"], "feature_ids": sorted(row.get("feature_ids", [])), "categories": sorted(row.get("categories", []))}
            for row in systems
        ],
    }
    progression = {
        "schema_version": "1.0.0",
        "required_stages": result["required_progression_stages"],
        "selected_stages": result["selection"]["stages"],
        "complete": result["selection"]["progression_complete"],
        "missing_stages": result["selection"]["missing_progression_stages"],
        "missing_transitions": result["selection"]["missing_progression_transitions"],
        "nodes": [{"id": row["id"], "stages": row.get("progression_stages", [])} for row in selected],
        "edges": [{"from": dep, "to": row["id"], "kind": "prerequisite"} for row in selected for dep in row.get("prerequisites", [])],
    }
    pattern_rows = []
    for row in systems:
        patterns = []
        for pattern in sorted(row.get("patterns", [])):
            patterns.append({"pattern": pattern, "coverage": PROVEN_PATTERNS.get(pattern, "NOVEL_PATTERN")})
        existing = [item["pattern"] for item in patterns if str(item["coverage"]).startswith("PROVEN_")]
        extension = [item["pattern"] for item in patterns if item["pattern"] not in existing and item["coverage"] != "NOVEL_PATTERN"]
        novel = [item["pattern"] for item in patterns if item["coverage"] == "NOVEL_PATTERN"]
        pattern_rows.append({
            "system_id": row["id"],
            "selected": row["id"] in selected_ids,
            "patterns": patterns,
            "existing_reusable_patterns": existing,
            "patterns_needing_extension": extension,
            "entirely_novel_patterns": novel,
            "bedrock_limitations": sorted(row.get("bedrock_limitations", [])),
            "required_benchmarks": sorted(row.get("benchmarks_required", [])),
        })
    pattern_doc = {"schema_version": "1.0.0", "systems": pattern_rows}
    console_doc = {
        "schema_version": "1.0.0",
        "limit_units": result["console_limit_units"],
        "selected_units": result["selection"]["console_cost_units"],
        "measurement_status": "STATIC_ESTIMATE_ONLY_CONSOLE_RUNTIME_PENDING",
        "risks": [
            {"system_id": row["id"], "cost_units": row["console_cost_units"], "risks": sorted(row.get("console_risks", []))}
            for row in systems if row.get("console_risks") or int(row["console_cost_units"]) >= 20
        ],
    }
    rights_doc = {
        "schema_version": "1.0.0",
        "approval_claimed": False,
        "records": [
            {
                "system_id": row["id"],
                "classification": result["decisions"][row["id"]]["classification"],
                "risks": sorted(row.get("rights_risks", [])),
                "review_status": "HUMAN_LEGAL_AND_MARKETPLACE_REVIEW_REQUIRED",
            }
            for row in systems
        ],
    }
    gaps = sorted(
        {
            gap
            for score in result["scores"]
            for gap in score["evidence_gaps"]
        }
    )
    selected_names = [row["name"] for row in selected]
    deferred_names = [row["name"] for row in deferred]
    identity = (
        f"# Identity map\n\n## Product identity\n\n{result['identity']['summary']}\n\n"
        f"## Load-bearing systems\n\n{_bullets([str(x) for x in result['identity']['load_bearing_systems']])}\n\n"
        f"## Evidence gaps\n\n{_bullets(sorted(set(gaps + result.get('evidence_gaps', []))))}\n\n"
        f"## Inputs required for full analysis\n\n{_bullets(result.get('required_inputs', []))}\n"
    )
    roadmap = (
        "# Conversion roadmap\n\n"
        + "\n".join(
            f"{index}. **{row['name']}** — {result['decisions'][row['id']]['classification']}; "
            f"prerequisites: {', '.join(row.get('prerequisites', [])) or 'none'}."
            for index, row in enumerate(selected, start=1)
        )
        + "\n"
    )
    compiler_gaps = [
        f"{row['name']}: {pattern}"
        for row in selected
        for pattern in sorted(row.get("patterns", []))
        if pattern not in PROVEN_PATTERNS
    ]
    gap_md = "# Compiler gap analysis\n\n" + _bullets(compiler_gaps, "No entirely novel patterns identified by current evidence.") + "\n"
    benchmark_md = (
        "# Benchmark plan\n\n"
        + _bullets(
            [
                f"{row['name']}: benchmark {', '.join(sorted(row.get('benchmarks_required', []))) or 'integration, restart, multiplayer, and console performance'}"
                for row in selected
            ]
        )
        + "\n"
    )
    selection_claim = (
        "This is a provisional constraint-feasible scope hypothesis. Because material identity and player-value evidence is missing, "
        "it does not prove that this scope maximizes Crazy Craft value."
        if result.get("analysis_status") == "PRELIMINARY_EVIDENCE_GAPS"
        else
        "The selected scope maximizes documented identity and player value within the configured effort and static console budgets."
    )
    executive = (
        "# Executive summary\n\n"
        f"## What makes the experience recognizable\n\n{result['identity']['summary']}\n\n"
        f"## Selected systems\n\n{_bullets(selected_names)}\n\n"
        f"## Deferred systems\n\n{_bullets(deferred_names)}\n\n"
        f"{selection_claim} It closes prerequisite chains and checks the requested progression stages. "
        "It is a planning estimate, not console certification.\n\n"
        f"## Original redesigns\n\n{_bullets([row['name'] for row in selected if result['decisions'][row['id']]['classification'] == 'ORIGINAL_REPLACEMENT'])}\n\n"
        f"## Highest engineering risks\n\n{_bullets([row['name'] for row in selected if row.get('console_risks') or row.get('benchmarks_required')])}\n\n"
        f"## Estimated scope\n\nSelected effort: {result['selection']['effort_units']} of {result['selection']['full_effort_units']} units "
        f"({result['selection']['effort_units'] * 100 // max(1, result['selection']['full_effort_units'])}%). "
        f"Selected static console cost: {result['selection']['console_cost_units']} of {result['console_limit_units']} units.\n\n"
        f"## Recommended build order\n\n{_bullets(selected_names)}\n\n"
        f"## Evidence gaps\n\n{_bullets(result.get('evidence_gaps', []))}\n\n"
        f"## Inputs required for full analysis\n\n{_bullets(result.get('required_inputs', []))}\n\n"
        "No third-party assets are included, no rights clearance is inferred, and Marketplace approval is not claimed.\n"
    )
    documents: dict[str, str] = {
        "quarter-scope.json": canonical_json(quarter),
        "quarter-scope.yaml": canonical_json(quarter),
        "deferred-scope.yaml": canonical_json(deferred_doc),
        "identity-map.md": identity,
        "system-clusters.json": canonical_json(clusters),
        "scoring-report.json": canonical_json({"schema_version": "1.0.0", "weights_version": result["weights_version"], "scores": result["scores"], "feature_scores": result["feature_scores"]}),
        "progression-graph.json": canonical_json(progression),
        "conversion-roadmap.md": roadmap,
        "pattern-coverage.json": canonical_json(pattern_doc),
        "compiler-gap-analysis.md": gap_md,
        "console-performance-risk.json": canonical_json(console_doc),
        "rights-risk.json": canonical_json(rights_doc),
        "benchmark-plan.md": benchmark_md,
        "executive-summary.md": executive,
    }
    artifacts = []
    for name in REQUIRED_ARTIFACTS:
        text = documents[name]
        write_text_atomic(root / name, text)
        artifacts.append({"path": f"distillation/{name}", "sha256": hashlib.sha256(text.encode()).hexdigest()})
    if result["review_adjustments_applied"]:
        review_text = canonical_json({
            "schema_version": "1.0.0",
            "authority": "ADVISORY_ONLY",
            "adjustments": result["review_adjustments"],
            "reviewed_selection": result["reviewed_selection"],
        })
        write_text_atomic(root / "review-adjustments.json", review_text)
        artifacts.append({
            "path": "distillation/review-adjustments.json",
            "sha256": hashlib.sha256(review_text.encode()).hexdigest(),
        })
    return artifacts
