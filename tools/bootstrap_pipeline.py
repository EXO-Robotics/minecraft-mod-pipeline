#!/usr/bin/env python3
"""Install the compiler and repository-tracked Codex skills from a fresh clone."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import sysconfig
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
IGNORED_NAMES = {".DS_Store", "__pycache__"}


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in IGNORED_NAMES for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def skill_directories() -> list[Path]:
    return sorted(
        path
        for path in SKILLS_ROOT.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )


def validate_repository() -> list[str]:
    errors: list[str] = []
    if sys.version_info < (3, 11):
        errors.append("Python 3.11 or newer is required")
    for required in ("pyproject.toml", "src/mccompiler", "skills"):
        if not (ROOT / required).exists():
            errors.append(f"missing repository component: {required}")
    for skill in skill_directories():
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\nname:" not in text or "\ndescription:" not in text:
            errors.append(f"invalid skill frontmatter: {skill.name}")
        if not (skill / "agents/openai.yaml").is_file():
            errors.append(f"missing agents/openai.yaml: {skill.name}")
    if not skill_directories():
        errors.append("no repository-tracked skills found")
    return errors


def install_skills(codex_home: Path, *, replace: bool) -> list[dict[str, str]]:
    destination_root = codex_home / "skills"
    destination_root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, str]] = []
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = codex_home / "skill-backups" / timestamp

    for source in skill_directories():
        destination = destination_root / source.name
        source_digest = tree_digest(source)
        if destination.exists():
            destination_digest = tree_digest(destination)
            if destination_digest == source_digest:
                results.append({"skill": source.name, "status": "already-current"})
                continue
            if not replace:
                raise RuntimeError(
                    f"installed skill differs: {destination}; rerun with --replace-skills "
                    "to preserve it in a timestamped backup and install the repository copy"
                )
            backup_root.mkdir(parents=True, exist_ok=True)
            shutil.move(str(destination), str(backup_root / source.name))
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns(*IGNORED_NAMES))
        results.append({"skill": source.name, "status": "installed", "sha256": source_digest})
    return results


def install_compiler() -> None:
    purelib = Path(sysconfig.get_path("purelib"))
    scripts = Path(sysconfig.get_path("scripts"))
    purelib.mkdir(parents=True, exist_ok=True)
    scripts.mkdir(parents=True, exist_ok=True)
    (purelib / "mccompiler-repository.pth").write_text(
        str(ROOT / "src") + "\n",
        encoding="utf-8",
    )
    launchers = {
        "mccompiler": "from mccompiler.cli import main",
        "mccompiler-agent": "from mccompiler.agent.stdio_server import main",
    }
    for name, import_line in launchers.items():
        launcher = scripts / name
        launcher.write_text(
            f"#!{sys.executable}\n{import_line}\nraise SystemExit(main())\n",
            encoding="utf-8",
        )
        launcher.chmod(0o755)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap the Java-to-Bedrock compiler and its Codex skill pack."
    )
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")),
        help="Codex configuration directory (default: CODEX_HOME or ~/.codex)",
    )
    parser.add_argument("--replace-skills", action="store_true")
    parser.add_argument("--skip-package-install", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    errors = validate_repository()
    report: dict[str, object] = {
        "repository": str(ROOT),
        "python": sys.version.split()[0],
        "skill_count": len(skill_directories()),
        "errors": errors,
    }
    if errors:
        print(json.dumps(report, indent=2) if args.json else "\n".join(errors))
        return 1
    if args.check_only:
        report["status"] = "ready"
    else:
        if not args.skip_package_install:
            install_compiler()
        report["skills"] = install_skills(args.codex_home.expanduser(), replace=args.replace_skills)
        report["compiler_installed"] = not args.skip_package_install
        report["status"] = "installed"
    print(json.dumps(report, indent=2) if args.json else f"Pipeline bootstrap: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
