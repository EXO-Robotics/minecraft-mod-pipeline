from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "tools/bootstrap_pipeline.py"


class PipelineBootstrapTests(unittest.TestCase):
    def test_check_only_reports_repository_ready(self) -> None:
        result = subprocess.run(
            [sys.executable, str(BOOTSTRAP), "--check-only", "--json"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "ready")
        self.assertGreaterEqual(report["skill_count"], 8)
        self.assertEqual(report["errors"], [])

    def test_installs_every_vendored_skill_into_fresh_codex_home(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary) / "codex"
            result = subprocess.run(
                [
                    sys.executable,
                    str(BOOTSTRAP),
                    "--codex-home",
                    str(codex_home),
                    "--skip-package-install",
                    "--json",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(result.stdout)
            installed = {row["skill"] for row in report["skills"]}
            expected = {
                path.name
                for path in (ROOT / "skills").iterdir()
                if path.is_dir() and (path / "SKILL.md").is_file()
            }
            self.assertEqual(installed, expected)
            for skill in expected:
                self.assertTrue((codex_home / "skills" / skill / "SKILL.md").is_file())

    def test_portable_entrypoints_do_not_embed_the_original_checkout(self) -> None:
        checked = [
            ROOT / "README.md",
            ROOT / "docs/bootstrap.md",
            ROOT / "skills/README.md",
            ROOT / "tools/bootstrap_pipeline.py",
            ROOT / "tools/run_forest_wave_1_parallel_batch_1_bds.py",
        ]
        forbidden = "/Users/blakegrove/Desktop/bedrock-server"
        for path in checked:
            self.assertNotIn(forbidden, path.read_text(encoding="utf-8"), path)


if __name__ == "__main__":
    unittest.main()
