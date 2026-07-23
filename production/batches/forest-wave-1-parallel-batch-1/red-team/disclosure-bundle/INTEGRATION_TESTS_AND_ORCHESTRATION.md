===== DISCLOSED SOURCE: tools/build_forest_wave_1_parallel_batch_1.py =====

#!/usr/bin/env python3
"""Build the deterministic six-feature Forest Wave 1 integration candidate."""
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from mccompiler.runtime.gametest import augment_mcworld_with_gametest_pack
from mccompiler.world import generate_multi_pack_test_world


ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "production/batches/forest-wave-1-parallel-batch-1"
DIST = BATCH / "dist"
REPORTS = BATCH / "reports"
RUNTIME = BATCH / "runtime"
PREVIEW_DIAGNOSTIC_PACK = BATCH / "diagnostic/preview-simulated-player"
EPOCH = (1980, 1, 1, 0, 0, 0)
LABELS = [
    "INTERNAL TEST BUILD",
    "NOT MARKETPLACE APPROVED",
    "NOT PHYSICAL PS4 CERTIFIED",
    "NOT FOR PUBLIC RELEASE",
]


@dataclass(frozen=True)
class FeaturePacks:
    feature_id: str
    behavior_pack: Path
    resource_pack: Path


PACKS = (
    FeaturePacks(
        "resonance_sling",
        ROOT / "production/features/resonance-sling/bedrock/behavior_pack",
        ROOT / "production/features/resonance-sling/bedrock/resource_pack",
    ),
    FeaturePacks(
        "signal_ruin",
        ROOT / "production/features/signal-ruin/bedrock/behavior_pack",
        ROOT / "production/features/signal-ruin/bedrock/resource_pack",
    ),
    FeaturePacks(
        "gloamwing_stalker",
        ROOT / "production/features/gloamwing-stalker/behavior_pack",
        ROOT / "production/features/gloamwing-stalker/resource_pack",
    ),
    FeaturePacks(
        "forest_attunement",
        ROOT / "production/features/forest-attunement/behavior_pack",
        ROOT / "production/features/forest-attunement/resource_pack",
    ),
    FeaturePacks(
        "mossback_forager",
        ROOT / "production/features/mossback-forager/bedrock/behavior_pack",
        ROOT / "production/features/mossback-forager/bedrock/resource_pack",
    ),
    FeaturePacks(
        "barkguard_charm",
        ROOT / "production/features/barkguard-charm/bedrock/behavior_pack",
        ROOT / "production/features/barkguard-charm/bedrock/resource_pack",
    ),
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_header(root: Path) -> dict[str, Any]:
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        header = manifest["header"]
        uuid = str(header["uuid"])
        version = [int(part) for part in header["version"]]
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid pack manifest: {root / 'manifest.json'}") from exc
    if len(version) != 3:
        raise ValueError(f"Invalid pack version in {root / 'manifest.json'}")
    return {"name": str(header["name"]), "uuid": uuid, "version": version}


def pack_entries(specs: Iterable[FeaturePacks]) -> list[tuple[str, bytes]]:
    entries: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for spec in specs:
        for kind, root in (("behavior_packs", spec.behavior_pack), ("resource_packs", spec.resource_pack)):
            if not root.is_dir():
                raise ValueError(f"Missing {kind} root for {spec.feature_id}: {root}")
            prefix = f"{kind}/{spec.feature_id}/"
            for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
                if path.is_symlink():
                    raise ValueError(f"Pack contains a symlink: {path}")
                if not path.is_file():
                    continue
                relative = prefix + path.relative_to(root).as_posix()
                if relative in seen:
                    raise ValueError(f"Duplicate integration archive entry: {relative}")
                seen.add(relative)
                entries.append((relative, path.read_bytes()))
    return entries


def write_zip(path: Path, entries: Iterable[tuple[str, bytes]]) -> dict[str, Any]:
    inventory = sorted(entries, key=lambda entry: entry[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, payload in inventory:
            info = zipfile.ZipInfo(relative, EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0
            archive.writestr(info, payload)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "files": len(inventory),
    }


def build() -> dict[str, Any]:
    behavior_packs = [spec.behavior_pack for spec in PACKS]
    resource_packs = [spec.resource_pack for spec in PACKS]
    headers = []
    all_uuids: set[str] = set()
    for spec in PACKS:
        bp = manifest_header(spec.behavior_pack)
        rp = manifest_header(spec.resource_pack)
        for header in (bp, rp):
            if header["uuid"] in all_uuids:
                raise ValueError(f"Duplicate pack UUID in integration candidate: {header['uuid']}")
            all_uuids.add(header["uuid"])
        headers.append({"feature_id": spec.feature_id, "behavior": bp, "resource": rp})

    addon_path = DIST / "forest-wave-1-parallel-batch-1-INTERNAL-TEST.mcaddon"
    world_path = DIST / "forest-wave-1-parallel-batch-1-INTERNAL-TEST.mcworld"
    addon = write_zip(addon_path, pack_entries(PACKS))
    world_result = generate_multi_pack_test_world(
        behavior_packs,
        resource_packs,
        world_path,
        world_name="Forest Wave 1 Parallel Batch 1 INTERNAL TEST",
    )
    world = {
        "path": world_path.relative_to(ROOT).as_posix(),
        "sha256": world_result["world_hash"],
        "bytes": world_path.stat().st_size,
        "pack_hash": world_result["pack_hash"],
        "behavior_pack_count": len(world_result["behavior_packs"]),
        "resource_pack_count": len(world_result["resource_packs"]),
    }
    preview_world_path = RUNTIME / "preview-simulated-player.mcworld"
    preview_result = augment_mcworld_with_gametest_pack(
        world_path,
        PREVIEW_DIAGNOSTIC_PACK,
        preview_world_path,
        diagnostic_server_version="2.10.0",
    )
    preview_world = {
        "path": preview_world_path.relative_to(ROOT).as_posix(),
        "sha256": preview_result["diagnostic_world"]["sha256"],
        "bytes": preview_world_path.stat().st_size,
        "diagnostic_pack_uuid": preview_result["diagnostic_pack"]["uuid"],
        "production_pack_module_overrides": preview_result["production_pack_module_overrides"],
        "never_ship": True,
        "preview_only": True,
    }
    resonance_addon = ROOT / "production/features/resonance-sling/dist/resonance-sling-INTERNAL-TEST.mcaddon"
    resonance_world = ROOT / "production/features/resonance-sling/dist/resonance-sling-INTERNAL-TEST.mcworld"
    report = {
        "schema_version": "1.0.0",
        "batch_id": "forest-wave-1-parallel-batch-1",
        "status": "INTEGRATION_ARTIFACT_BUILT",
        "labels": LABELS,
        "features": headers,
        "artifacts": {"mcaddon": addon, "mcworld": world},
        "preview_diagnostic": preview_world,
        "protected_resonance_sling": {
            "mcaddon_sha256": sha256(resonance_addon),
            "mcworld_sha256": sha256(resonance_world),
            "unchanged": True,
        },
        "claims": {
            "marketplace_approved": False,
            "physical_ps4_verified": False,
            "realm_deployed": False,
            "creator_tools_executed": False,
            "bds_qualified": False,
        },
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "integration-artifact-manifest.json").write_text(canonical_json(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(canonical_json(build()), end="")


===== DISCLOSED SOURCE: tools/run_forest_wave_1_parallel_batch_1_bds.py =====

#!/usr/bin/env python3
"""Run Stable and Preview BDS qualification for Forest Wave 1 parallel batch 1."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from mccompiler.runtime.bds import (
    BDSConsoleProbe,
    BDSLogProbe,
    BDSRunRequest,
    run_bds_diagnostic,
)


ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "production/batches/forest-wave-1-parallel-batch-1"
REPORTS = BATCH / "reports"
RUNTIME = BATCH / "runtime"
IMAGE = "itzg/minecraft-bedrock-server@sha256:12c7047cc149bd517d6dbc2339163cf62a4f1044c10e759c45c8b387e9784e39"
SEED_BASE = (
    Path("<USER_HOME>/Desktop/bedrock-server/minecraft-compiler-baseline")
    / "production/features/resonance-sling/runtime"
)
VERSIONS = {"stable": "1.26.33.2", "preview": "1.26.50.20"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_report(name: str, result: dict[str, Any]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / name).write_text(canonical_json(result), encoding="utf-8")


def reset_run_root(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def remove_server_payload(path: Path) -> None:
    """Keep receipts and normalized logs, never another cached BDS installation."""
    shutil.rmtree(path / "data", ignore_errors=True)


def run_stable() -> dict[str, Any]:
    run_root = RUNTIME / "stable-bds"
    reset_run_root(run_root)
    expected = (
        "[resonance-sling] script runtime initialized stable_api=2.0.0",
        "[barkguard-charm] stable_api=2.0.0",
    )
    probes = tuple(
        BDSLogProbe(
            check_id=f"stable-{name}-cycle-{cycle}",
            cycle=cycle,
            expect_output=output,
            classification="bds_restart_diagnostic",
        )
        for cycle in range(1, 4)
        for name, output in (("resonance", expected[0]), ("barkguard", expected[1]))
    )
    try:
        result = run_bds_diagnostic(
            BDSRunRequest(
                image=IMAGE,
                mcworld=BATCH / "dist/forest-wave-1-parallel-batch-1-INTERNAL-TEST.mcworld",
                run_root=run_root,
                timeout_seconds=180,
                boot_grace_seconds=20,
                network_mode="bridge",
                bds_version=VERSIONS["stable"],
                preview_channel=False,
                restart_count=3,
                log_probes=probes,
                server_seed_root=SEED_BASE / "stable-server-seed",
            )
        )
        write_report("stable-bds-result.json", result)
        return result
    finally:
        remove_server_payload(run_root)


def run_preview() -> dict[str, Any]:
    contract = json.loads(
        (BATCH / "diagnostic/preview-simulated-player/probes.json").read_text(encoding="utf-8")
    )
    run_root = RUNTIME / "preview-simulated-player"
    reset_run_root(run_root)
    console = tuple(
        BDSConsoleProbe(
            check_id=str(row["check_id"]),
            cycle=int(row["cycle"]),
            after_boot_seconds=float(row["after_boot_seconds"]),
            command=str(row["command"]),
            expect_output=str(row["expect_output"]),
        )
        for row in contract["console_probes"]
    )
    logs = tuple(
        [
            *(
                BDSLogProbe(
                    check_id=f"preview-{name.replace('_', '-')}",
                    cycle=1,
                    expect_output=f"[forest-batch-1:preview] {name}=passed",
                    classification="simulated_player_integration",
                )
                for name in contract["cycle_1_checks"]
            ),
            *(
                BDSLogProbe(
                    check_id=f"preview-restart-{name.replace('_', '-')}",
                    cycle=2,
                    expect_output=f"[forest-batch-1:preview] {name}=passed",
                    classification="simulated_player_integration",
                )
                for name in contract["cycle_2_checks"]
            ),
        ]
    )
    try:
        result = run_bds_diagnostic(
            BDSRunRequest(
                image=IMAGE,
                mcworld=RUNTIME / "preview-simulated-player.mcworld",
                run_root=run_root,
                timeout_seconds=240,
                boot_grace_seconds=90,
                network_mode="bridge",
                bds_version=VERSIONS["preview"],
                preview_channel=True,
                restart_count=2,
                console_probes=console,
                log_probes=logs,
                server_seed_root=SEED_BASE / "preview-server-seed",
            )
        )
        write_report("preview-simulated-player-result.json", result)
        return result
    finally:
        remove_server_payload(run_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("channel", choices=("stable", "preview", "all", "summary"))
    args = parser.parse_args()
    results: dict[str, Any] = {}
    if args.channel in {"stable", "all"}:
        results["stable"] = run_stable()
    if args.channel in {"preview", "all"}:
        results["preview"] = run_preview()
    if args.channel == "summary":
        integration = json.loads(
            (REPORTS / "integration-artifact-manifest.json").read_text(encoding="utf-8")
        )
        expected = {
            "stable": integration["artifacts"]["mcworld"]["sha256"],
            "preview": integration["preview_diagnostic"]["sha256"],
        }
        for channel, filename in (
            ("stable", "stable-bds-result.json"),
            ("preview", "preview-simulated-player-result.json"),
        ):
            result = json.loads((REPORTS / filename).read_text(encoding="utf-8"))
            if result["artifact"]["sha256"] != expected[channel]:
                raise ValueError(
                    f"{channel} BDS receipt does not match current artifact: "
                    f"{result['artifact']['sha256']} != {expected[channel]}"
                )
            results[channel] = result
    summary = {
        "schema_version": "1.0.0",
        "batch_id": "forest-wave-1-parallel-batch-1",
        "channels": {
            name: {
                "status": result["status"],
                "passed": result["passed"],
                "artifact_sha256": result["artifact"]["sha256"],
                "bds_version": result["runtime"]["requested_bds_version"],
            }
            for name, result in results.items()
        },
        "passed": bool(results) and all(bool(result["passed"]) for result in results.values()),
        "claims": {
            "physical_ps4_verified": False,
            "marketplace_approved": False,
            "creator_tools_executed": False,
        },
    }
    write_report("bds-qualification-summary.json", summary)
    print(canonical_json(summary), end="")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


===== DISCLOSED SOURCE: tests/test_parallel_batch_preflight.py =====

from __future__ import annotations

import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "production/batches/forest-wave-1-parallel-batch-1"
FEATURES = (
    "signal_ruin",
    "gloamwing_stalker",
    "forest_attunement",
    "mossback_forager",
    "barkguard_charm",
)


def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_preflight_is_complete_and_honest() -> None:
    preflight = read(BATCH / "batch-preflight.json")
    assert preflight["status"] == "BATCH_PREFLIGHT_READY"
    assert preflight["immutable_base_commit"] == "e9009b70502f4e0db57986ea52cf8d4f7998cc1b"
    assert preflight["production_model"] == "gpt-5.6-sol"
    assert preflight["production_reasoning_effort"] == "light"
    assert preflight["wave_policy"]["maximum_child_concurrency"] == 3
    launched = preflight["wave_policy"]["wave_a"] + preflight["wave_policy"]["wave_b"]
    assert sorted(launched) == sorted(FEATURES)
    assert preflight["acceptance"]["unavailable_gates"]["physical_ps4"] == "PENDING_PHYSICAL_HARDWARE"
    assert "NO_PUSH" in preflight["release_restrictions"]


def test_original_production_contracts_are_authorized_and_isolated() -> None:
    for feature in FEATURES:
        contract = read(
            ROOT
            / "production/reconstruction-waves/forest-wave-1"
            / feature
            / "original-production-manifest.json"
        )
        assert contract["production_lane"] == "ORIGINAL_BEDROCK_NATIVE"
        assert contract["authorship_mode"] == "ORIGINAL_AUTHORSHIP"
        assert contract["java_evidence"] == "NOT_APPLICABLE"
        assert contract["java_fidelity_claimed"] is False
        assert contract["source_expression_used"] is False
        assert contract["execution_authorized"] is True
        assert contract["required_tests"]
        assert contract["explicit_non_goals"]
        assert contract["performance_caps"]
        assert contract["release_status"]["physical_ps4_certified"] is False


def test_reservations_have_unique_valid_uuids_and_disjoint_prefixes() -> None:
    reservations = read(BATCH / "reservations.json")["features"]
    all_uuids: list[str] = []
    all_prefixes: list[str] = []
    all_identifiers: list[str] = []
    for feature in FEATURES:
        row = reservations[feature]
        all_uuids.extend(row["uuids"].values())
        all_prefixes.extend(row["identifier_prefixes"])
        all_identifiers.extend(row["reserved_identifiers"])
    assert len(all_uuids) == len(set(all_uuids)) == 25
    assert all(str(uuid.UUID(value)) == value for value in all_uuids)
    assert len(all_prefixes) == len(set(all_prefixes))
    assert len(all_identifiers) == len(set(all_identifiers))


def test_assignments_have_disjoint_write_scopes_and_required_packet() -> None:
    owned: list[str] = []
    for feature in FEATURES:
        assignment = read(BATCH / "assignments" / f"{feature}.json")
        assert assignment["feature_id"] == feature
        assert assignment["model"] == "gpt-5.6-sol"
        assert assignment["reasoning_effort"] == "light"
        assert assignment["shared_files_may_be_edited"] is False
        assert assignment["authoritative_bds_owner"] == "MAIN_CODEX"
        assert assignment["blockbench_gui_owner"] == "MAIN_CODEX"
        assert "reports/candidate-packet.json" in assignment["required_outputs"]
        owned.extend(assignment["owned_paths"])
    assert len(owned) == len(set(owned))
    assert not any("resonance-sling" in path for path in owned)
    assert not any("phase_anchor_test.bbmodel" in path for path in owned)


===== DISCLOSED SOURCE: tests/test_forest_wave_1_parallel_batch_1_integration.py =====

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/build_forest_wave_1_parallel_batch_1.py"
SPEC = importlib.util.spec_from_file_location("batch_1_builder", SCRIPT)
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = BUILDER
SPEC.loader.exec_module(BUILDER)


class ForestWave1ParallelBatch1IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = BUILDER.build()

    def test_all_six_feature_pack_pairs_are_bound(self) -> None:
        world = ROOT / self.report["artifacts"]["mcworld"]["path"]
        with zipfile.ZipFile(world) as archive:
            behavior = json.loads(archive.read("world_behavior_packs.json"))
            resource = json.loads(archive.read("world_resource_packs.json"))
            self.assertEqual(6, len(behavior))
            self.assertEqual(6, len(resource))
            self.assertEqual(12, len({entry["pack_id"] for entry in [*behavior, *resource]}))
            manifests = [name for name in archive.namelist() if name.endswith("/manifest.json")]
            self.assertEqual(12, len(manifests))

    def test_mcaddon_contains_every_feature_without_path_collisions(self) -> None:
        addon = ROOT / self.report["artifacts"]["mcaddon"]["path"]
        with zipfile.ZipFile(addon) as archive:
            names = archive.namelist()
            self.assertEqual(len(names), len(set(names)))
            for spec in BUILDER.PACKS:
                self.assertIn(f"behavior_packs/{spec.feature_id}/manifest.json", names)
                self.assertIn(f"resource_packs/{spec.feature_id}/manifest.json", names)

    def test_preview_diagnostic_is_separate_and_never_ship(self) -> None:
        production = ROOT / self.report["artifacts"]["mcworld"]["path"]
        diagnostic = ROOT / self.report["preview_diagnostic"]["path"]
        self.assertNotEqual(production, diagnostic)
        self.assertTrue(self.report["preview_diagnostic"]["never_ship"])
        self.assertTrue(self.report["preview_diagnostic"]["preview_only"])
        with zipfile.ZipFile(production) as archive:
            self.assertFalse(any("preview_simulated_player" in name for name in archive.namelist()))
        with zipfile.ZipFile(diagnostic) as archive:
            diagnostic_manifests = [
                name
                for name in archive.namelist()
                if name.startswith("behavior_packs/") and name.endswith("/manifest.json")
                and self.report["preview_diagnostic"]["diagnostic_pack_uuid"]
                in archive.read(name).decode("utf-8")
            ]
            self.assertEqual(
                1,
                len(diagnostic_manifests),
            )

    def test_preview_build_does_not_mutate_production_world(self) -> None:
        production = ROOT / self.report["artifacts"]["mcworld"]["path"]
        before = production.read_bytes()
        BUILDER.build()
        self.assertEqual(before, production.read_bytes())

    def test_build_is_byte_deterministic(self) -> None:
        first_addon = (ROOT / self.report["artifacts"]["mcaddon"]["path"]).read_bytes()
        first_world = (ROOT / self.report["artifacts"]["mcworld"]["path"]).read_bytes()
        second = BUILDER.build()
        self.assertEqual(first_addon, (ROOT / second["artifacts"]["mcaddon"]["path"]).read_bytes())
        self.assertEqual(first_world, (ROOT / second["artifacts"]["mcworld"]["path"]).read_bytes())

    def test_pack_uuids_and_archive_paths_are_unique(self) -> None:
        entries = BUILDER.pack_entries(BUILDER.PACKS)
        self.assertEqual(len(entries), len({name for name, _ in entries}))
        headers = []
        for spec in BUILDER.PACKS:
            headers.extend(
                [
                    BUILDER.manifest_header(spec.behavior_pack),
                    BUILDER.manifest_header(spec.resource_pack),
                ]
            )
        self.assertEqual(len(headers), len({header["uuid"] for header in headers}))

    def test_integration_labels_and_ps4_boundary_are_explicit(self) -> None:
        self.assertIn("NOT PHYSICAL PS4 CERTIFIED", self.report["labels"])
        self.assertFalse(self.report["claims"]["physical_ps4_verified"])
        self.assertFalse(self.report["claims"]["marketplace_approved"])
        self.assertFalse(self.report["claims"]["bds_qualified"])

    def test_resonance_sling_frozen_artifacts_remain_exact(self) -> None:
        protected = self.report["protected_resonance_sling"]
        self.assertTrue(protected["unchanged"])
        self.assertEqual(
            "0bbd00a285cb8c7ccab49cf9a246f2ad95386eeaa239631a1c6463c0c84855ec",
            protected["mcaddon_sha256"],
        )
        self.assertEqual(
            "061501b67b0886296ad2765f1b7c5246efbe38d64b9494303a05b9ee81a58d9a",
            protected["mcworld_sha256"],
        )

    def test_writer_rejects_duplicate_archive_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            duplicate = BUILDER.FeaturePacks(
                "duplicate",
                BUILDER.PACKS[0].behavior_pack,
                BUILDER.PACKS[0].resource_pack,
            )
            path = Path(directory) / "duplicate.mcaddon"
            with self.assertRaisesRegex(ValueError, "Duplicate integration archive entry"):
                BUILDER.write_zip(path, BUILDER.pack_entries([duplicate, duplicate]))


if __name__ == "__main__":
    unittest.main()
