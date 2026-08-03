from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bedrock_factory.eventlog import CanonicalEventLog, EventLogError, rebuild_projection, verify_projection
from bedrock_factory.metrics import compute_metrics
from bedrock_factory.objects import EvidenceObjectStore
from bedrock_factory.qualification import may_reuse_gate_evidence, next_qualification_stage


H = "a" * 64


class EventKernelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.log = CanonicalEventLog(self.root / "events.jsonl")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def append(self, event_type: str, *, at: float, candidate: str | None = "C1", activation: str | None = "A1", gate_run: str | None = None, payload: dict | None = None) -> dict:
        return self.log.append(
            campaign_id="campaign-one",
            workload_id="workload-one",
            candidate_id=candidate,
            activation_id=activation,
            gate_run_id=gate_run,
            event_type=event_type,
            authority_hash=H,
            created_at=at,
            payload=payload,
        )

    def test_delete_and_rebuild_projection_from_zero(self) -> None:
        self.append("ACTIVATION_STARTED", at=1)
        self.append("CANDIDATE_PUBLISHED", at=2)
        projection = self.root / "projection.sqlite3"
        first = rebuild_projection(self.log.read(), projection)
        projection.unlink()
        second = rebuild_projection(self.log.read(), projection)
        self.assertEqual(first["projection_sha256"], second["projection_sha256"])
        self.assertTrue(verify_projection(self.log.read(), projection)["rebuild_match"])

    def test_projection_drift_fails_closed(self) -> None:
        self.append("ACTIVATION_STARTED", at=1)
        projection = self.root / "projection.sqlite3"
        rebuild_projection(self.log.read(), projection)
        with sqlite3.connect(projection) as connection:
            connection.execute("UPDATE kernel_frontier SET last_event_type='FALSE_STATE'")
            connection.commit()
        with self.assertRaises(EventLogError):
            verify_projection(self.log.read(), projection)

    def test_event_chain_detects_mutation(self) -> None:
        self.append("ACTIVATION_STARTED", at=1)
        self.append("CANDIDATE_PUBLISHED", at=2)
        text = self.log.path.read_text(encoding="utf-8").replace("CANDIDATE_PUBLISHED", "CANDIDATE_REWRITTEN")
        self.log.path.write_text(text, encoding="utf-8")
        with self.assertRaises(EventLogError):
            self.log.read()

    def test_metrics_separate_queue_service_and_control_churn(self) -> None:
        self.append("ACTIVATION_STARTED", at=1)
        self.append("ACTIVATION_STARTED", at=2, activation="A2")
        self.append("CANDIDATE_PUBLISHED", at=3)
        self.append("INFRASTRUCTURE_BLOCKED", at=4, activation="A2")
        self.append("GATE_QUEUED", at=5, gate_run="BDS-R1", payload={"gate": "BDS"})
        self.append("GATE_RUN_STARTED", at=8, gate_run="BDS-R1", payload={"gate": "BDS"})
        self.append("GATE_RUN_FINISHED", at=13, gate_run="BDS-R1", payload={"gate": "BDS", "reused_or_repeated_unchanged": False})
        metrics = compute_metrics(self.log.read())
        self.assertEqual(metrics["activation_amplification"], 2.0)
        self.assertEqual(metrics["infrastructure_blocked_share"], 0.5)
        self.assertEqual(metrics["queue_age_by_gate_seconds"]["BDS"], 3.0)
        self.assertEqual(metrics["gate_service_time_seconds"]["BDS"], 5.0)

    def test_content_addressed_objects_deduplicate_and_use_logical_paths(self) -> None:
        store = EvidenceObjectStore(self.root / "objects")
        first = store.put_bytes(b"same", object_type="fixture-v1")
        second = store.put_bytes(b"same", object_type="fixture-v1")
        self.assertEqual(first, second)
        manifest = store.put_merkle_manifest({"logs/stable.txt": b"ok"}, object_type="bds-bundle-v1")
        self.assertEqual(manifest["entry_count"], 1)
        self.assertNotIn(str(self.root), store.get(manifest).decode())

    def test_qualification_reuse_requires_every_exact_binding(self) -> None:
        previous = {"status": "PASS", **{field: H for field in (
            "candidate_sha256", "gate_implementation_sha256", "runtime_image_sha256", "configuration_sha256", "probe_authority_sha256"
        )}}
        self.assertTrue(may_reuse_gate_evidence(previous, dict(previous)))
        changed = dict(previous, runtime_image_sha256="b" * 64)
        self.assertFalse(may_reuse_gate_evidence(previous, changed))
        self.assertEqual(next_qualification_stage({}, preview_required=False), "PRODUCER_T1_SHADOW")
        self.assertIsNone(next_qualification_stage({"PRODUCER_T1_SHADOW": "FAIL"}, preview_required=False))


if __name__ == "__main__":
    unittest.main()
