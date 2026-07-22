from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


METRIC_THRESHOLDS: dict[str, float] = {
    "registration_precision": 0.95,
    "registration_recall": 0.90,
    "behavior_precision": 0.90,
    "recoverable_behavior_recall": 0.70,
    "unsupported_detection": 0.95,
    "fabrication_rate": 0.0,
    "determinism": 1.0,
    "source_jar_agreement": 0.95,
}

SPLITS = ("development", "validation", "final_holdout")
TUNING_SPLITS = frozenset({"development", "validation"})


@dataclass(frozen=True)
class _Count:
    numerator: int
    denominator: int
    failures: tuple[str, ...]

    @property
    def value(self) -> float:
        return self.numerator / self.denominator


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return sha256(encoded).hexdigest()


def _nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(x, str) and x.strip() for x in value)


def _bool(value: Any) -> bool:
    return isinstance(value, bool)


def _validate_observations(
    sample_id: str,
    name: str,
    value: Any,
    errors: list[str],
    *,
    evidence_fields: Sequence[str] = ("label_evidence", "prediction_evidence"),
) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"{sample_id}: {name} observations must be a list")
        return []
    rows: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        location = f"{sample_id}: {name}[{index}]"
        if not isinstance(raw, Mapping):
            errors.append(f"{location} must be an object")
            continue
        fact_id = raw.get("id")
        if not isinstance(fact_id, str) or not fact_id.strip():
            errors.append(f"{location} requires a non-empty id")
        elif fact_id in seen:
            errors.append(f"{location} duplicates id {fact_id}")
        else:
            seen.add(fact_id)
        if not _bool(raw.get("label")):
            errors.append(f"{location} requires a boolean label")
        if not _bool(raw.get("prediction")):
            errors.append(f"{location} requires a boolean prediction")
        for field in evidence_fields:
            if not _nonempty_strings(raw.get(field)):
                errors.append(f"{location} requires non-empty {field}")
        rows.append(raw)
    return rows


def _classification_counts(rows: Sequence[tuple[str, Mapping[str, Any]]]) -> tuple[int, int, int, int]:
    tp = sum(1 for _, row in rows if row.get("label") is True and row.get("prediction") is True)
    fp = sum(1 for _, row in rows if row.get("label") is False and row.get("prediction") is True)
    fn = sum(1 for _, row in rows if row.get("label") is True and row.get("prediction") is False)
    tn = sum(1 for _, row in rows if row.get("label") is False and row.get("prediction") is False)
    return tp, fp, fn, tn


def _metric(name: str, count: _Count, *, maximum: bool = False) -> dict[str, Any]:
    threshold = METRIC_THRESHOLDS[name]
    value = count.value
    passed = value <= threshold if maximum else value >= threshold
    return {
        "value": value,
        "numerator": count.numerator,
        "denominator": count.denominator,
        "threshold": threshold,
        "comparison": "<=" if maximum else ">=",
        "passed": passed,
        "failures": list(count.failures),
        "confidence": "exact_count_over_declared_split",
        "uncertainty": "descriptive_only_no_population_inference",
    }


def evaluate_corpus(manifest: Mapping[str, Any], *, split: str) -> dict[str, Any]:
    """Evaluate labeled corpus observations without implying corpus qualification.

    The evaluator is deliberately fail-closed. A report may contain diagnostic
    metric values while ``qualified`` remains false whenever labels, evidence,
    denominators, content hashes, or split/holdout declarations are incomplete.
    """
    errors: list[str] = []
    if split not in SPLITS:
        errors.append(f"split must be one of {', '.join(SPLITS)}")
    if manifest.get("schema_version") != "1.0.0":
        errors.append("unsupported corpus schema_version")
    revision = manifest.get("corpus_revision")
    if not isinstance(revision, str) or not revision.strip():
        errors.append("corpus_revision is required")

    policy = manifest.get("split_policy")
    if not isinstance(policy, Mapping):
        errors.append("split_policy is required")
        policy = {}
    if policy.get("assignment_method") != "content_hash_before_tuning":
        errors.append("split assignment_method must be content_hash_before_tuning")
    if not isinstance(policy.get("frozen_at"), str) or not policy.get("frozen_at"):
        errors.append("split_policy.frozen_at is required")
    if policy.get("tuning_splits") != ["development", "validation"]:
        errors.append("only development and validation may be tuning_splits")
    if policy.get("final_holdout_tuning_prohibited") is not True:
        errors.append("final holdout tuning must be explicitly prohibited")

    raw_samples = manifest.get("samples")
    if not isinstance(raw_samples, list) or not raw_samples:
        errors.append("samples must be a non-empty list")
        raw_samples = []
    selected: list[Mapping[str, Any]] = []
    seen_samples: set[str] = set()
    for index, raw in enumerate(raw_samples):
        location = f"samples[{index}]"
        if not isinstance(raw, Mapping):
            errors.append(f"{location} must be an object")
            continue
        sample_id = raw.get("id")
        if not isinstance(sample_id, str) or not sample_id.strip():
            errors.append(f"{location} requires a non-empty id")
            sample_id = location
        elif sample_id in seen_samples:
            errors.append(f"duplicate sample id {sample_id}")
        seen_samples.add(str(sample_id))
        sample_split = raw.get("split")
        if sample_split not in SPLITS:
            errors.append(f"{sample_id}: invalid split {sample_split!r}")
        content_sha = raw.get("content_sha256")
        if not isinstance(content_sha, str) or len(content_sha) != 64 or any(c not in "0123456789abcdef" for c in content_sha):
            errors.append(f"{sample_id}: content_sha256 must be a lowercase SHA-256")
        if raw.get("legally_clean") is not True or not _nonempty_strings(raw.get("rights_evidence")):
            errors.append(f"{sample_id}: legally clean status and rights evidence are required")
        if sample_split == split:
            selected.append(raw)
    if not selected:
        errors.append(f"split {split!r} has no samples")

    if split == "final_holdout":
        holdout = manifest.get("holdout_evaluation")
        if not isinstance(holdout, Mapping):
            errors.append("final_holdout requires holdout_evaluation metadata")
        else:
            for field in ("release_candidate", "evaluation_id", "evaluated_at"):
                if not isinstance(holdout.get(field), str) or not holdout.get(field):
                    errors.append(f"holdout_evaluation.{field} is required")
            if holdout.get("used_for_tuning") is not False:
                errors.append("final holdout must declare used_for_tuning=false")
            if holdout.get("evaluation_count") != 1:
                errors.append("final holdout may be evaluated exactly once per release candidate")
    elif manifest.get("holdout_evaluation") is not None:
        errors.append("holdout_evaluation metadata is only valid when evaluating final_holdout")

    grouped: dict[str, list[tuple[str, Mapping[str, Any]]]] = {
        "registrations": [], "behaviors": [], "unsupported_hooks": []
    }
    deterministic: list[tuple[str, Mapping[str, Any]]] = []
    source_jar: list[tuple[str, Mapping[str, Any]]] = []
    for sample in sorted(selected, key=lambda x: str(x.get("id", ""))):
        sample_id = str(sample.get("id") or "<unknown>")
        sample_rows: dict[str, list[Mapping[str, Any]]] = {}
        for name in grouped:
            rows = _validate_observations(sample_id, name, sample.get(name), errors)
            sample_rows[name] = rows
            grouped[name].extend((sample_id, row) for row in rows)
        for row in sample_rows["behaviors"]:
            if not _bool(row.get("recoverable")):
                errors.append(f"{sample_id}: behavior {row.get('id')} requires a boolean recoverable label")
            if row.get("prediction") is True and not _bool(row.get("evidence_supports_prediction")):
                errors.append(f"{sample_id}: predicted behavior {row.get('id')} requires evidence_supports_prediction")

        raw_determinism = sample.get("determinism")
        if not isinstance(raw_determinism, list):
            errors.append(f"{sample_id}: determinism observations must be a list")
        else:
            for index, row in enumerate(raw_determinism):
                location = f"{sample_id}: determinism[{index}]"
                if not isinstance(row, Mapping):
                    errors.append(f"{location} must be an object")
                    continue
                if not isinstance(row.get("id"), str) or not row.get("id"):
                    errors.append(f"{location} requires an id")
                for field in ("first_sha256", "second_sha256"):
                    value = row.get(field)
                    if not isinstance(value, str) or len(value) != 64:
                        errors.append(f"{location} requires {field}")
                if not _nonempty_strings(row.get("evidence")):
                    errors.append(f"{location} requires evidence")
                deterministic.append((sample_id, row))

        raw_pairs = sample.get("source_jar")
        pairs = _validate_observations(
            sample_id, "source_jar", raw_pairs, errors,
            evidence_fields=("source_evidence", "jar_evidence"),
        )
        for row in pairs:
            if row.get("supported_pattern") is not True:
                errors.append(f"{sample_id}: source/JAR row {row.get('id')} must be a declared supported pattern")
            source_jar.append((sample_id, row))

    metrics: dict[str, dict[str, Any]] = {}

    def classification_metric(name: str, rows: list[tuple[str, Mapping[str, Any]]], kind: str) -> None:
        tp, fp, fn, _ = _classification_counts(rows)
        if kind == "precision":
            denominator, numerator = tp + fp, tp
            failures = tuple(f"{sid}:{row.get('id')}" for sid, row in rows if row.get("label") is False and row.get("prediction") is True)
        else:
            denominator, numerator = tp + fn, tp
            failures = tuple(f"{sid}:{row.get('id')}" for sid, row in rows if row.get("label") is True and row.get("prediction") is False)
        if denominator == 0:
            errors.append(f"{name} denominator is zero")
            return
        metrics[name] = _metric(name, _Count(numerator, denominator, failures))

    classification_metric("registration_precision", grouped["registrations"], "precision")
    classification_metric("registration_recall", grouped["registrations"], "recall")
    classification_metric("behavior_precision", grouped["behaviors"], "precision")
    recoverable_rows = [(sid, row) for sid, row in grouped["behaviors"] if row.get("recoverable") is True]
    classification_metric("recoverable_behavior_recall", recoverable_rows, "recall")
    classification_metric("unsupported_detection", grouped["unsupported_hooks"], "recall")

    predicted_behaviors = [(sid, row) for sid, row in grouped["behaviors"] if row.get("prediction") is True]
    if not predicted_behaviors:
        errors.append("fabrication_rate denominator is zero")
    else:
        fabricated = [(sid, row) for sid, row in predicted_behaviors if row.get("evidence_supports_prediction") is not True]
        metrics["fabrication_rate"] = _metric(
            "fabrication_rate",
            _Count(len(fabricated), len(predicted_behaviors), tuple(f"{sid}:{row.get('id')}" for sid, row in fabricated)),
            maximum=True,
        )

    if not deterministic:
        errors.append("determinism denominator is zero")
    else:
        failures = tuple(f"{sid}:{row.get('id')}" for sid, row in deterministic if row.get("first_sha256") != row.get("second_sha256"))
        metrics["determinism"] = _metric("determinism", _Count(len(deterministic) - len(failures), len(deterministic), failures))

    if not source_jar:
        errors.append("source_jar_agreement denominator is zero")
    else:
        failures = tuple(f"{sid}:{row.get('id')}" for sid, row in source_jar if row.get("label") != row.get("prediction"))
        metrics["source_jar_agreement"] = _metric("source_jar_agreement", _Count(len(source_jar) - len(failures), len(source_jar), failures))

    metric_failures = sorted(name for name, result in metrics.items() if not result["passed"])
    complete = set(metrics) == set(METRIC_THRESHOLDS)
    if not complete:
        errors.append("not all required metrics could be computed")
    errors = sorted(set(errors))
    return {
        "schema_version": "1.0.0",
        "corpus_revision": revision,
        "split": split,
        "sample_count": len(selected),
        "metrics": {name: metrics[name] for name in sorted(metrics)},
        "thresholds": dict(sorted(METRIC_THRESHOLDS.items())),
        "exclusion_rules": "none; ambiguous and unsupported labeled observations remain in denominators",
        "errors": errors,
        "failed_metrics": metric_failures,
        "qualified": complete and not errors and not metric_failures,
        "real_corpus_completion_implied": False,
        "evaluation_sha256": _canonical_hash({"manifest": manifest, "split": split}),
    }


def evaluate_corpus_json(manifest: Mapping[str, Any], *, split: str) -> str:
    """Return byte-stable JSON for an evaluation report."""
    return json.dumps(evaluate_corpus(manifest, split=split), sort_keys=True, separators=(",", ":")) + "\n"
