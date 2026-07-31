#!/usr/bin/env python3
"""Initialize empty, source-neutral factory production repositories.

This performs organization only.  It refuses to touch an existing target and
does not add gameplay, asset, package, evidence, or oracle content.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "FACTORY_REPOSITORY_ALLOCATION_REGISTRY.json"
PACK_MAP = ROOT / "CRAZY_CRAFT_FINAL_PACK_MAP.json"
RECEIPT = ROOT / "FACTORY_REPOSITORY_BOOTSTRAP_RECEIPT.json"
CREATED_AT = "2026-07-29T16:30:00Z"


def run(*argv: str, cwd: Path | None = None) -> str:
    return subprocess.check_output(argv, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    pack_map = json.loads(PACK_MAP.read_text(encoding="utf-8"))
    packs = {item["pack_id"]: item for item in pack_map["packs"]}
    results = []

    for allocation in registry["pack_repositories"]:
        if allocation["existing_authority"]:
            continue
        pack_id = allocation["pack_id"]
        target = Path(allocation["path"])
        branch = allocation["ref"].removeprefix("refs/heads/")
        if target.exists():
            if not (target / ".git").is_dir():
                raise SystemExit(f"refusing pre-existing non-repository target: {target}")
        else:
            target.mkdir(parents=True)
            run("git", "init", "-b", branch, str(target))
            (target / ".gitignore").write_text(
                ".runtime/\n.DS_Store\n*.log\n*.tmp\n", encoding="utf-8"
            )
            allocation_record = {
                "schema_version": "1.0.0",
                "record_type": "factory_production_repository_allocation",
                "pack_id": pack_id,
                "authority_id": packs[pack_id]["authority_id"],
                "original_product_name": packs[pack_id]["name"],
                "namespace": packs[pack_id]["namespace"],
                "semantic_version": packs[pack_id]["semantic_version"],
                "production_ref": allocation["ref"],
                "run_control": "PAUSED_FACTORY_ORGANIZATION",
                "permitted_future_content": [
                    "independently authored Bedrock BP/RP and editable assets",
                    "source-neutral tests and deterministic build tools",
                    "candidate-bound clean-room process receipts",
                ],
                "prohibited_content": [
                    "Java archives, bytecode, source, or decompiled text",
                    "source identifiers, source assets, source expression, or private oracle",
                    "shared Git objects, alternates, or unapproved remotes",
                ],
                "proof_boundary": "Empty source-neutral repository allocation only; no product implementation is present or authorized.",
            }
            (target / "FACTORY_ALLOCATION.json").write_text(
                json.dumps(allocation_record, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (target / "README.md").write_text(
                f"# {packs[pack_id]['name']} production authority\n\n"
                "This independent repository is an empty, paused factory allocation. "
                "A later controlled launch must provide the accepted producer-safe "
                "contract and candidate-bound isolation admission before any product "
                "implementation begins.\n",
                encoding="utf-8",
            )
            run("git", "add", ".gitignore", "FACTORY_ALLOCATION.json", "README.md", cwd=target)
            run(
                "git",
                "-c",
                "user.name=Crazy Craft Factory Controller",
                "-c",
                "user.email=factory-controller@local.invalid",
                "commit",
                "-m",
                f"chore: allocate paused {pack_id} production authority",
                cwd=target,
            )

        head = run("git", "rev-parse", "HEAD", cwd=target)
        tree = run("git", "show", "-s", "--format=%T", "HEAD", cwd=target)
        observed_branch = run("git", "branch", "--show-current", cwd=target)
        if observed_branch != branch:
            raise SystemExit(f"branch mismatch for {pack_id}: {observed_branch} != {branch}")
        remotes = run("git", "remote", cwd=target)
        alternates = target / ".git" / "objects" / "info" / "alternates"
        if remotes or alternates.exists():
            raise SystemExit(f"unapproved object sharing/remotes for {pack_id}")
        if run("git", "status", "--porcelain", cwd=target):
            raise SystemExit(f"dirty bootstrap repository: {target}")
        results.append(
            {
                "pack_id": pack_id,
                "repository": str(target),
                "ref": allocation["ref"],
                "commit": head,
                "tree": tree,
                "independent_git_object_store": True,
                "remotes": [],
                "alternates": False,
                "allocation_sha256": sha256(target / "FACTORY_ALLOCATION.json"),
                "status": "PAUSED_EMPTY_AUTHORITY_READY",
            }
        )

    receipt = {
        "schema_version": "1.0.0",
        "record_type": "factory_repository_bootstrap_receipt",
        "created_at": CREATED_AT,
        "repositories_created_or_verified": len(results),
        "results": results,
        "campaign_work_resumed": False,
        "product_files_created": False,
        "proof_boundary": "Independent empty repository initialization only.",
    }
    RECEIPT.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
