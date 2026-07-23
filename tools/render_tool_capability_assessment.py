#!/usr/bin/env python3
"""Validate and deterministically render the planning capability matrix."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT = ROOT / "planning" / "tool-capability-assessment"
SOURCE = ASSESSMENT / "capability-matrix.json"
INDEX = ASSESSMENT / "evidence-index.json"
OUTPUT = ASSESSMENT / "capability-matrix.md"

REQUIRED = {
    "family", "feature", "java_pattern", "strategy", "evidence_level", "outcome",
    "evidence", "runtime", "fidelity", "ai", "risk", "marketplace", "console_risk",
}


def main() -> None:
    data = json.loads(SOURCE.read_text())
    evidence = json.loads(INDEX.read_text())["entries"]
    rows = data["rows"]
    for index, row in enumerate(rows):
        missing = REQUIRED - row.keys()
        if missing:
            raise ValueError(f"row {index} missing {sorted(missing)}")
        if row["evidence_level"] not in data["evidence_levels"]:
            raise ValueError(f"row {index} has invalid evidence level")
        if row["outcome"] not in data["outcomes"]:
            raise ValueError(f"row {index} has invalid outcome")
        for evidence_id in row["evidence"]:
            if evidence_id not in evidence:
                raise ValueError(f"row {index} has unknown evidence {evidence_id}")
            for path in evidence[evidence_id]:
                if not (ROOT / path).exists():
                    raise ValueError(f"missing evidence path: {path}")
        if row["evidence_level"].startswith("PROVEN_") and not row["evidence"]:
            raise ValueError(f"proven row {index} lacks evidence")

    lines = [
        "# Proven-conversion capability matrix", "",
        data["disclaimer"], "",
        "Evidence levels and outcomes are defined canonically in `capability-matrix.json`. Runtime wording is deliberately narrower than the classification.", "",
    ]
    current = None
    for row in rows:
        if row["family"] != current:
            current = row["family"]
            lines += [f"## {current}", "", "| Feature | Level / outcome | Java → Bedrock | Evidence / runtime | Fidelity / AI | Risk / suitability |", "|---|---|---|---|---|---|"]
        refs = ", ".join(f"`{item}`" for item in row["evidence"])
        lines.append(
            f"| {row['feature']} | `{row['evidence_level']}` / `{row['outcome']}` | "
            f"{row['java_pattern']} → {row['strategy']} | {refs}; {row['runtime']} | "
            f"{row['fidelity']}; {row['ai']} | {row['risk']}; Marketplace: {row['marketplace']}; console: {row['console_risk']} |"
        )
    lines += ["", "Evidence IDs resolve through `evidence-index.json`.", ""]
    OUTPUT.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
