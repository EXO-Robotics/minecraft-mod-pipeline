#!/usr/bin/env python3
"""Fail-closed validation for the paused fixed-pack factory."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SECTION_MAP = ROOT.parent / "ten-sections" / "CRAZY_CRAFT_TEN_SECTION_PORTFOLIO_MAP.json"
REPORT = ROOT / "FACTORY_VALIDATION_REPORT.json"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repository: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repository), *args], text=True).strip()


def check_schema(path: Path, schema: dict[str, Any]) -> list[str]:
    errors = []
    value = json.loads(path.read_text(encoding="utf-8"))
    for field in schema.get("required", []):
        if field not in value:
            errors.append(f"{path}: missing {field}")
    if schema.get("additionalProperties") is False:
        extras = set(value) - set(schema.get("properties", {}))
        if extras:
            errors.append(f"{path}: undeclared fields {sorted(extras)}")
    for field, rule in schema.get("properties", {}).items():
        if field not in value:
            continue
        expected = rule.get("const")
        if expected is not None and value[field] != expected:
            errors.append(f"{path}: {field} must equal {expected!r}")
        enum = rule.get("enum")
        if enum is not None and value[field] not in enum:
            errors.append(f"{path}: {field} outside enum")
        pattern = rule.get("pattern")
        if pattern and isinstance(value[field], str):
            import re
            if not re.fullmatch(pattern, value[field]):
                errors.append(f"{path}: {field} pattern mismatch")
    return errors


def main() -> None:
    failures: list[str] = []
    checks: list[dict[str, Any]] = []

    def record(name: str, ok: bool, detail: Any) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})
        if not ok:
            failures.append(f"{name}: {detail}")

    pack_map = json.loads((ROOT / "CRAZY_CRAFT_FINAL_PACK_MAP.json").read_text())
    reconciliation = json.loads((ROOT / "CRAZY_CRAFT_SOURCE_TO_PACK_RECONCILIATION.json").read_text())
    namespace = json.loads((ROOT / "FACTORY_NAMESPACE_UUID_REGISTRY.json").read_text())
    repositories = json.loads((ROOT / "FACTORY_REPOSITORY_ALLOCATION_REGISTRY.json").read_text())
    budgets = json.loads((ROOT / "FACTORY_RUNTIME_PERFORMANCE_BUDGET_REGISTRY.json").read_text())
    assets = json.loads((ROOT / "FACTORY_ASSET_WORKLOAD_LEDGER.json").read_text())
    section = json.loads(SECTION_MAP.read_text())
    launch_decision_path = ROOT / "FACTORY_LAUNCH_DECISION.json"
    launch_decision = (
        json.loads(launch_decision_path.read_text())
        if launch_decision_path.is_file()
        else {}
    )
    launch_active = (
        launch_decision.get("decision_type") == "FACTORY_LAUNCH"
        and launch_decision.get("run_control") == "ACTIVE"
    )

    frozen = {
        source["path"]: source["sha256"]
        for lane in section["sections"]
        for source in lane["source_artifacts"]
    }
    reconciled = {row["path"]: row["sha256"] for row in reconciliation["records"]}
    record("all_52_artifacts_exact_once", len(reconciled) == 52 and reconciled == frozen, {"count": len(reconciled)})
    record("pack_count_and_identity", len(pack_map["packs"]) == 16 and len({p["pack_id"] for p in pack_map["packs"]}) == 16, {"count": len(pack_map["packs"])})
    record("durable_owner_unique", len({p["owner"] for p in pack_map["packs"]}) == 16, [p["owner"] for p in pack_map["packs"]])

    namespaces = [row["namespace"] for row in namespace["allocations"]]
    uuids = [value for row in namespace["allocations"] for value in row["uuids"].values()]
    record("namespace_collision_free", len(namespaces) == len(set(namespaces)), namespaces)
    record("uuid_collision_free", len(uuids) == len(set(uuids)), {"count": len(uuids)})
    record("combined_budget_within_ceiling", budgets["status"] == "PASS" and all(v["status"] == "PASS" for v in budgets["combined_target_check"].values()), budgets["combined_target_check"])

    sample_assignment = json.loads(
        (ROOT / "assignments" / "quietwork.assignment.json").read_text()
    )
    platform = sample_assignment["technical_allocation"].get("platform_authority", {})
    platform_ok = False
    if platform:
        platform_repository = Path(platform["repository"])
        try:
            platform_ok = (
                git(platform_repository, "show", "-s", "--format=%T", platform["commit"])
                == platform["tree"]
            )
        except Exception:
            platform_ok = False
    record("frozen_platform_contract_authority", platform_ok, platform)

    asset_by_pack = {row["pack_id"]: row for row in assets["packs"]}
    required_classes = {"HERO", "REUSABLE_COMPLEX", "ROUTINE_MODEL", "ICON", "PARTICLE", "SOUND", "NOT_REQUIRED"}
    asset_ok = True
    asset_detail = {}
    for pack in pack_map["packs"]:
        inventory = pack["asset_authority"]["inventory"]
        if "class_counts" in inventory:
            observed = set(inventory["class_counts"])
            asset_ok &= required_classes <= observed
            asset_detail[pack["pack_id"]] = sorted(observed)
        else:
            asset_detail[pack["pack_id"]] = inventory.get("authority_state")
        asset_ok &= pack["pack_id"] in asset_by_pack
    record("every_pack_asset_manifest", asset_ok, asset_detail)

    repo_by_pack = {row["pack_id"]: row for row in repositories["pack_repositories"]}
    repo_results = {}
    repo_ok = True
    for pack in pack_map["packs"]:
        allocation = repo_by_pack.get(pack["pack_id"])
        if not allocation:
            repo_ok = False
            continue
        path = Path(allocation["path"])
        current = {
            "exists": path.is_dir(),
            "git": False,
            "baseline_commit": allocation.get("baseline_commit"),
            "baseline_tree": allocation.get("baseline_tree"),
        }
        if current["exists"]:
            try:
                current["git"] = bool(git(path, "rev-parse", "--git-dir"))
                commit = git(path, "rev-parse", allocation["baseline_commit"])
                tree = git(path, "show", "-s", "--format=%T", commit)
                current.update({"resolved_commit": commit, "resolved_tree": tree})
                repo_ok &= tree == allocation["baseline_tree"]
                if not allocation["existing_authority"]:
                    repo_ok &= git(path, "branch", "--show-current") == allocation["ref"].removeprefix("refs/heads/")
                    repo_ok &= not git(path, "remote")
                    repo_ok &= not (path / ".git" / "objects" / "info" / "alternates").exists()
                    if not launch_active:
                        repo_ok &= not git(path, "status", "--porcelain")
            except Exception as exc:
                current["error"] = str(exc)
                repo_ok = False
        else:
            repo_ok = False
        repo_results[pack["pack_id"]] = current
    record("every_pack_production_repository", repo_ok, repo_results)

    existing_results = {}
    existing_ok = True
    for pack in pack_map["packs"]:
        authority = pack.get("existing_authority")
        if not authority:
            continue
        repository = Path(authority["repository"])
        content_bundle = authority.get("content_bundle")
        if content_bundle:
            bundle_path = Path(content_bundle["path"])
            bundle_ok = bundle_path.is_file() and digest_file(bundle_path) == content_bundle["sha256"]
            if bundle_ok:
                heads = subprocess.check_output(
                    ["git", "bundle", "list-heads", str(bundle_path)], text=True
                ).splitlines()
                bundle_ok = any(line.startswith(authority["content_commit"] + " ") for line in heads)
            existing_ok &= bundle_ok
        roles = {}
        for role, artifact in authority["artifacts"].items():
            if artifact is None:
                roles[role] = "ENCAPSULATED_ONLY"
                continue
            path = Path(artifact["path"])
            observed = digest_file(path) if path.exists() else None
            roles[role] = {"expected": artifact["sha256"], "observed": observed}
            existing_ok &= observed == artifact["sha256"]
            if path.exists():
                try:
                    relative = path.relative_to(repository)
                    artifact_commit = authority.get("artifact_commit", authority["content_commit"])
                    git(repository, "cat-file", "-e", f"{artifact_commit}:{relative}")
                except Exception:
                    existing_ok = False
                    roles[role]["tracked_at_content_commit"] = False
                else:
                    roles[role]["tracked_at_content_commit"] = True
        existing_results[pack["pack_id"]] = roles
    record("existing_authorities_preserved", existing_ok, existing_results)

    assignment_ok = True
    assignment_detail = {}
    for pack in pack_map["packs"]:
        path = ROOT / "assignments" / f"{pack['pack_id']}.assignment.json"
        if not path.exists():
            assignment_ok = False
            continue
        assignment = json.loads(path.read_text())
        supplied = assignment.pop("assignment_payload_sha256")
        computed = digest_json(assignment)
        required_sections = {
            "identity",
            "control_source_responsibility",
            "producer_safe_input",
            "product_scope",
            "asset_workload",
            "technical_allocation",
            "required_outputs",
            "completion_condition",
            "worker_mission",
            "mailbox_contract",
        }
        valid = (
            supplied == computed
            and required_sections <= set(assignment)
            and assignment["run_control"] == "PAUSED_NOT_DISPATCHED"
            and assignment["completion_condition"]["terminal_success"] == "PACK_ACCEPTED_AND_INTEGRATED"
        )
        assignment_detail[pack["pack_id"]] = {"hash_match": supplied == computed, "complete": valid}
        assignment_ok &= valid
    record("durable_assignment_packets", assignment_ok, assignment_detail)

    source_markers = list(frozen) + list(frozen.values()) + ["mods/", ".jar"]
    contract_ok = True
    leaked = {}
    for path in sorted((ROOT / "contracts").glob("*.json")):
        text = path.read_text(encoding="utf-8")
        matches = [marker for marker in source_markers if marker.lower() in text.lower()]
        if matches:
            leaked[path.name] = matches[:10]
            contract_ok = False
    record("producer_contract_source_neutrality", contract_ok, leaked)

    mailbox = repositories["mailbox_repository"]
    mailbox_path = Path(mailbox["path"])
    mailbox_ok = mailbox_path.is_dir() and (mailbox_path / ".git").exists()
    mailbox_detail: dict[str, Any] = {"path": str(mailbox_path)}
    if mailbox_ok:
        mailbox_detail.update(
            {
                "commit": git(mailbox_path, "rev-parse", "HEAD"),
                "tree": git(mailbox_path, "show", "-s", "--format=%T", "HEAD"),
                "branch": git(mailbox_path, "branch", "--show-current"),
                "dirty": bool(git(mailbox_path, "status", "--porcelain")),
                "remotes": git(mailbox_path, "remote").splitlines(),
                "runtime_cursor_tracked": bool(git(mailbox_path, "ls-files", ".runtime")),
            }
        )
        mailbox_ok &= (
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(mailbox_path),
                    "merge-base",
                    "--is-ancestor",
                    mailbox["commit"],
                    mailbox_detail["commit"],
                ],
                check=False,
            ).returncode
            == 0
        )
        mailbox_ok &= (
            git(mailbox_path, "show", "-s", "--format=%T", mailbox["commit"])
            == mailbox["tree"]
        )
        mailbox_ok &= not mailbox_detail["dirty"] and not mailbox_detail["remotes"]
        mailbox_ok &= not mailbox_detail["runtime_cursor_tracked"]
    record("mailbox_repository_authority", mailbox_ok, mailbox_detail)

    schema_by_type = {
        "CANDIDATE_SUBMISSION": "candidate-submission.schema.json",
        "TEST_PASS": "tester-result.schema.json",
        "TEST_FAIL_PRODUCT": "tester-result.schema.json",
        "TEST_FAIL_INFRASTRUCTURE": "tester-result.schema.json",
        "TEST_BLOCKED_CLIENT": "tester-result.schema.json",
        "TEST_BLOCKED_PHYSICAL": "tester-result.schema.json",
        "PACK_ACCEPTED_AND_INTEGRATED": "accepted-pack-registration.schema.json",
    }
    schema_errors: list[str] = []
    messages: dict[str, dict[str, Any]] = {}
    for folder in ("candidate_submissions", "tester_intake", "tester_results", "integration_intake", "final_decisions"):
        for path in mailbox_path.glob(f"{folder}/**/*.json"):
            message = json.loads(path.read_text())
            messages[message["message_id"]] = message
            schema_name = schema_by_type.get(message["message_type"], "mailbox-message.schema.json")
            schema = json.loads((mailbox_path / "schemas" / schema_name).read_text())
            schema_errors.extend(check_schema(path, schema))
    chain = [
        "MSG-SYNTH-000001",
        "MSG-SYNTH-000002",
        "MSG-SYNTH-000003",
        "MSG-SYNTH-000004",
        "MSG-SYNTH-000005",
    ]
    chain_ok = all(item in messages for item in chain)
    if chain_ok:
        chain_ok &= messages[chain[0]]["parent_message_id"] is None
        for previous, current in zip(chain, chain[1:]):
            chain_ok &= messages[current]["parent_message_id"] == previous
        fixture = mailbox_path / messages[chain[0]]["mcaddon"]["path"]
        chain_ok &= digest_file(fixture) == messages[chain[0]]["mcaddon"]["sha256"]
    record("mailbox_round_trip_schema_and_chain", chain_ok and not schema_errors, {"schema_errors": schema_errors, "message_count": len(messages)})

    service_files = [
        ROOT / "services" / "PERSISTENT_TESTER_ASSIGNMENT.json",
        ROOT / "services" / "SHARED_RUNTIME_INTEGRATION_ASSIGNMENT.json",
        ROOT / "services" / "T1_SUPERVISOR_MAILBOX_ROUTING_ASSIGNMENT.json",
    ]
    services_ok = all(
        path.exists()
        and json.loads(path.read_text()).get("run_control")
        in {"PAUSED_NOT_DISPATCHED", "PAUSED_ORGANIZATION_ONLY"}
        for path in service_files
    ) and (not launch_decision or launch_active)
    record("persistent_service_assignments", services_ok, [str(path) for path in service_files])

    report = {
        "schema_version": "1.0.0",
        "record_type": "factory_validation_report",
        "checks": checks,
        "failure_count": len(failures),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
        "campaign_workers_started": False,
        "launchd_started": False,
        "proof_boundary": "Control-plane factory organization and synthetic mailbox mechanics only.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
