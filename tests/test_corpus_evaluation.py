from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from mccompiler.evaluation import METRIC_THRESHOLDS, evaluate_corpus, evaluate_corpus_json


ROOT = Path(__file__).resolve().parents[1]


def observation(identifier: str, label: bool, prediction: bool) -> dict[str, object]:
    return {
        "id": identifier,
        "label": label,
        "prediction": prediction,
        "label_evidence": [f"labels/{identifier}.json"],
        "prediction_evidence": [f"reports/{identifier}.json"],
    }


def valid_manifest(split: str = "validation") -> dict[str, object]:
    digest = "a" * 64
    registrations = [observation(f"registration-{i}", True, True) for i in range(20)]
    registrations.append(observation("registration-negative", False, False))
    behaviors = [
        {**observation(f"behavior-{i}", True, True), "recoverable": True, "evidence_supports_prediction": True}
        for i in range(20)
    ]
    behaviors.append({
        **observation("behavior-negative", False, False),
        "recoverable": False,
        "evidence_supports_prediction": False,
    })
    unsupported = [observation(f"unsupported-{i}", True, True) for i in range(20)]
    unsupported.append(observation("unsupported-negative", False, False))
    source_jar = [
        {
            "id": f"pair-{i}",
            "label": True,
            "prediction": True,
            "supported_pattern": True,
            "source_evidence": [f"source/{i}.json"],
            "jar_evidence": [f"jar/{i}.json"],
        }
        for i in range(20)
    ]
    return {
        "schema_version": "1.0.0",
        "corpus_revision": "fixture-v1",
        "split_policy": {
            "assignment_method": "content_hash_before_tuning",
            "frozen_at": "2026-07-22T00:00:00Z",
            "tuning_splits": ["development", "validation"],
            "final_holdout_tuning_prohibited": True,
        },
        "samples": [{
            "id": "legal-synthetic-fixture",
            "split": split,
            "content_sha256": digest,
            "legally_clean": True,
            "rights_evidence": ["original-authorship-declaration.yaml"],
            "registrations": registrations,
            "behaviors": behaviors,
            "unsupported_hooks": unsupported,
            "determinism": [{
                "id": "addon-output",
                "first_sha256": digest,
                "second_sha256": digest,
                "evidence": ["runs/one.json", "runs/two.json"],
            }],
            "source_jar": source_jar,
        }],
    }


class CorpusEvaluationTests(unittest.TestCase):
    def test_complete_labeled_fixture_computes_all_metrics(self) -> None:
        report = evaluate_corpus(valid_manifest(), split="validation")
        self.assertTrue(report["qualified"], report["errors"])
        self.assertEqual(set(report["metrics"]), set(METRIC_THRESHOLDS))
        self.assertTrue(all(metric["passed"] for metric in report["metrics"].values()))
        self.assertEqual(report["metrics"]["fabrication_rate"]["value"], 0.0)
        self.assertFalse(report["real_corpus_completion_implied"])
        for metric in report["metrics"].values():
            self.assertGreater(metric["denominator"], 0)
            self.assertIn("uncertainty", metric)
            self.assertIn("failures", metric)

    def test_output_is_deterministic_and_order_independent(self) -> None:
        manifest = valid_manifest()
        first = evaluate_corpus_json(manifest, split="validation")
        second_manifest = deepcopy(manifest)
        second_manifest["samples"] = list(reversed(second_manifest["samples"]))
        self.assertEqual(first, evaluate_corpus_json(manifest, split="validation"))
        self.assertEqual(
            json.loads(first)["metrics"],
            evaluate_corpus(second_manifest, split="validation")["metrics"],
        )

    def test_missing_labels_evidence_and_denominators_fail_closed(self) -> None:
        manifest = valid_manifest()
        sample = manifest["samples"][0]
        sample["registrations"] = []
        del sample["behaviors"][0]["label"]
        sample["unsupported_hooks"][0]["prediction_evidence"] = []
        sample["determinism"] = []
        sample["source_jar"] = []
        report = evaluate_corpus(manifest, split="validation")
        self.assertFalse(report["qualified"])
        joined = "\n".join(report["errors"])
        self.assertIn("registration_precision denominator is zero", joined)
        self.assertIn("requires a boolean label", joined)
        self.assertIn("requires non-empty prediction_evidence", joined)
        self.assertIn("determinism denominator is zero", joined)
        self.assertIn("source_jar_agreement denominator is zero", joined)
        self.assertIn("not all required metrics could be computed", joined)

    def test_metric_failures_are_exposed_without_fabrication(self) -> None:
        manifest = valid_manifest()
        sample = manifest["samples"][0]
        sample["registrations"][0]["prediction"] = False
        sample["behaviors"][0]["evidence_supports_prediction"] = False
        sample["unsupported_hooks"][0]["prediction"] = False
        sample["determinism"][0]["second_sha256"] = "b" * 64
        sample["source_jar"][0]["prediction"] = False
        sample["source_jar"][1]["prediction"] = False
        report = evaluate_corpus(manifest, split="validation")
        self.assertFalse(report["qualified"])
        self.assertIn("fabrication_rate", report["failed_metrics"])
        self.assertIn("determinism", report["failed_metrics"])
        self.assertIn("source_jar_agreement", report["failed_metrics"])
        self.assertEqual(report["metrics"]["fabrication_rate"]["numerator"], 1)

    def test_holdout_requires_one_non_tuning_release_evaluation(self) -> None:
        manifest = valid_manifest("final_holdout")
        report = evaluate_corpus(manifest, split="final_holdout")
        self.assertFalse(report["qualified"])
        self.assertIn("final_holdout requires holdout_evaluation metadata", report["errors"])

        manifest["holdout_evaluation"] = {
            "release_candidate": "0.2.0-rc1",
            "evaluation_id": "holdout-0.2.0-rc1",
            "evaluated_at": "2026-07-22T12:00:00Z",
            "used_for_tuning": False,
            "evaluation_count": 1,
        }
        self.assertTrue(evaluate_corpus(manifest, split="final_holdout")["qualified"])
        manifest["holdout_evaluation"]["used_for_tuning"] = True
        self.assertFalse(evaluate_corpus(manifest, split="final_holdout")["qualified"])

    def test_template_is_intentionally_non_qualifying(self) -> None:
        template = json.loads((ROOT / "benchmarks/corpus/manifest-template.json").read_text())
        report = evaluate_corpus(template, split="validation")
        self.assertFalse(report["qualified"])
        self.assertFalse(report["real_corpus_completion_implied"])


if __name__ == "__main__":
    unittest.main()
