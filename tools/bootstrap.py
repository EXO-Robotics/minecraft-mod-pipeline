#!/usr/bin/env python3
"""Validate the checkout, create its venv, and optionally install Codex skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import venv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
IGNORED = {".DS_Store", "__pycache__"}


def digest_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in IGNORED for part in path.parts):
            continue
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def skill_directories() -> list[Path]:
    return sorted(path for path in SKILLS.iterdir() if (path / "SKILL.md").is_file())


def validate() -> list[str]:
    errors: list[str] = []
    if sys.version_info < (3, 11):
        errors.append("Python 3.11 or newer is required")
    for required in (
        "pyproject.toml",
        "src/bedrock_factory",
        "schemas/mailbox",
        "skills/oversee-java-to-bedrock-factory/SKILL.md",
    ):
        if not (ROOT / required).exists():
            errors.append(f"missing repository component: {required}")
    for skill in skill_directories():
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\nname:" not in text or "\ndescription:" not in text:
            errors.append(f"invalid skill frontmatter: {skill.name}")
        if not (skill / "agents/openai.yaml").is_file():
            errors.append(f"missing agents/openai.yaml: {skill.name}")
    return errors


def ensure_venv() -> Path:
    target = ROOT / ".venv"
    if not (target / "bin/python").is_file():
        venv.EnvBuilder(with_pip=True).create(target)
    python = target / "bin/python"
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-build-isolation",
            "-e",
            str(ROOT),
        ],
        cwd=ROOT,
        check=True,
    )
    return python


def install_skills(codex_home: Path) -> list[dict[str, str]]:
    destination_root = codex_home / "skills"
    destination_root.mkdir(parents=True, exist_ok=True)
    backup_root = codex_home / "skill-backups" / datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    results: list[dict[str, str]] = []
    for source in skill_directories():
        destination = destination_root / source.name
        source_digest = digest_tree(source)
        if destination.exists() and digest_tree(destination) == source_digest:
            results.append({"skill": source.name, "status": "already-current"})
            continue
        if destination.exists():
            backup_root.mkdir(parents=True, exist_ok=True)
            shutil.move(str(destination), str(backup_root / source.name))
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns(*IGNORED))
        results.append({"skill": source.name, "status": "installed", "sha256": source_digest})
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--install-skills", action="store_true")
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")),
    )
    args = parser.parse_args()
    errors = validate()
    report: dict[str, object] = {
        "repository": str(ROOT),
        "python": sys.version.split()[0],
        "skills": len(skill_directories()),
        "errors": errors,
    }
    if errors:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1
    if args.check_only:
        report["status"] = "ready"
    else:
        report["venv_python"] = str(ensure_venv())
        if args.install_skills:
            report["skill_install"] = install_skills(args.codex_home.expanduser())
        report["status"] = "installed"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
