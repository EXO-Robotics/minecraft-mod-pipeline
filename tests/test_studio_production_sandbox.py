from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.production_sandbox.studio_launcher import (
    initialize_repository,
    parse_denied_path,
    postflight_isolation,
    render_profile,
    scan_forbidden_material,
    sha256,
    verify_transferred_inputs,
)


class StudioProductionSandboxTests(unittest.TestCase):
    def test_profile_is_studio_local_deny_default_and_offline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            denied = {
                denied_class: root / denied_class
                for denied_class in ("evidence", "control", "private_oracle", "canary")
            }
            profile = render_profile(
                root / "production",
                root / "runtime",
                root / "launcher",
                denied,
            )
        self.assertIn("(deny default)", profile)
        self.assertIn("(deny network*)", profile)
        self.assertNotIn("ollama", profile.lower())
        self.assertNotIn("blakegrove", profile.lower())
        self.assertNotIn("100.84.", profile)
        for target in denied.values():
            self.assertIn(str(target), profile)

    def test_denied_paths_require_explicit_class_and_absolute_path(self) -> None:
        denied_class, target = parse_denied_path("evidence=/private/tmp/evidence")
        self.assertEqual(denied_class, "evidence")
        self.assertTrue(target.is_absolute())
        with self.assertRaises(Exception):
            parse_denied_path("evidence=relative")
        with self.assertRaises(Exception):
            parse_denied_path("unknown=/private/tmp/value")

    def test_source_neutral_repository_has_independent_objects_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment = root / "assignment.json"
            contract = root / "contract.json"
            prompt = root / "prompt.txt"
            assignment.write_text('{"assignment_id":"opaque"}', encoding="utf-8")
            contract.write_text('{"requirement_id":"REQ-001"}', encoding="utf-8")
            prompt.write_text("Use the assigned production role.", encoding="utf-8")
            repository = root / "production"
            _, _, transferred = initialize_repository(
                repository,
                base_repository=None,
                inputs=[
                    ("assignment", assignment),
                    ("contract", contract),
                    ("prompt", prompt),
                ],
            )
            self.assertEqual(len(transferred), 3)
            for record in transferred:
                self.assertEqual(
                    sha256(repository / str(record["path"])),
                    record["sha256"],
                )
            isolation = postflight_isolation(repository)
            self.assertTrue(isolation["remotes_absent"])
            self.assertTrue(isolation["alternates_absent"])
            self.assertTrue(isolation["hardlinks_absent"])
            self.assertTrue(
                all(
                    row["match"]
                    for row in verify_transferred_inputs(repository, transferred)
                )
            )

    def test_forbidden_material_scan_detects_credentials_and_canary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canary = root / "outside-canary"
            canary.write_text("RESTRICTED_REHEARSAL_CANARY", encoding="utf-8")
            production = root / "production"
            production.mkdir()
            clean = scan_forbidden_material([production], canary=canary)
            self.assertTrue(clean["clean"])
            (production / "auth.json").write_text("{}", encoding="utf-8")
            (production / "copied.txt").write_bytes(canary.read_bytes())
            dirty = scan_forbidden_material([production], canary=canary)
            self.assertFalse(dirty["clean"])
            self.assertTrue(dirty["name_matches"])
            self.assertTrue(dirty["hash_matches"])

    @unittest.skipUnless(
        os.environ.get("RUN_STUDIO_SANDBOX_INTEGRATION") == "1",
        "set RUN_STUDIO_SANDBOX_INTEGRATION=1 for real sandbox-exec proof",
    )
    def test_real_studio_sandbox_launch_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            denied_paths = {}
            for denied_class in ("evidence", "control", "private_oracle"):
                target = root / f"denied-{denied_class}"
                target.mkdir()
                (target / "secret.txt").write_text("restricted", encoding="utf-8")
                denied_paths[denied_class] = target
            canary = root / "denied-canary"
            canary.write_text("RESTRICTED_REHEARSAL_CANARY", encoding="utf-8")
            denied_paths["canary"] = canary
            assignment = root / "assignment.json"
            assignment.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "assignment_id": "studio-integration-test",
                        "role": "feature_producer",
                    }
                ),
                encoding="utf-8",
            )
            contract = root / "contract.json"
            contract.write_text('{"requirement_id":"REQ-001"}', encoding="utf-8")
            prompt = root / "prompt.txt"
            prompt.write_text("Produce one original test artifact.", encoding="utf-8")
            worker_command = root / "worker-command.json"
            worker_code = (
                "import os,subprocess; from pathlib import Path; "
                "repo=Path(os.environ['STUDIO_PRODUCTION_REPOSITORY']); "
                "(repo/'studio-output.txt').write_text('studio-only'); "
                "git=os.environ['STUDIO_GIT']; "
                "subprocess.run([git,'add','studio-output.txt'],cwd=repo,check=True); "
                "subprocess.run([git,'commit','-q','-m','Studio output'],cwd=repo,check=True)"
            )
            worker_command.write_text(
                json.dumps([sys.executable, "-c", worker_code]),
                encoding="utf-8",
            )
            run_root = root / "run"
            command = [
                sys.executable,
                str(ROOT / "tools/production_sandbox/studio_launcher.py"),
                "--run-root",
                str(run_root),
                "--assignment",
                str(assignment),
                "--sanitized-contract",
                str(contract),
                "--prompt",
                str(prompt),
                "--worker-command",
                str(worker_command),
            ]
            for denied_class, target in denied_paths.items():
                command.extend(["--deny", f"{denied_class}={target}"])
            result = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            internal_stderr = run_root / "runtime/logs/stderr.log"
            failure_detail = (
                result.stderr
                + "\n"
                + result.stdout
                + "\n"
                + (
                    internal_stderr.read_text(encoding="utf-8", errors="replace")
                    if internal_stderr.is_file()
                    else "<no internal stderr>"
                )
            )
            self.assertEqual(result.returncode, 0, failure_detail)
            receipt = run_root / "runtime/process-receipt.json"
            validator = subprocess.run(
                [
                    sys.executable,
                    str(
                        ROOT
                        / "skills/translate-java-mods-to-bedrock/scripts/"
                        "validate_production_process_receipt.py"
                    ),
                    str(receipt),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validator.returncode, 0, validator.stdout)
            data = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(data["host_role"], "STUDIO_PRODUCTION_HOST")
            self.assertEqual(data["preflight"]["network"], "DENIED")


if __name__ == "__main__":
    unittest.main()
