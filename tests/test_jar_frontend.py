from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from mccompiler.frontends.javap_analyzer import available
from mccompiler.scan import scan_path


ROOT = Path(__file__).parent / "fixtures" / "representative_mod"
JDK = Path("/opt/homebrew/opt/openjdk/bin")


class JarFrontendTests(unittest.TestCase):
    @unittest.skipUnless(available() and (JDK / "javac").is_file(), "OpenJDK javac/javap required")
    def test_compiled_jar_matches_source_semantics(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            classes, archive = temp / "classes", temp / "representative.jar"
            classes.mkdir()
            subprocess.run([
                str(JDK / "javac"), "-g", "-d", str(classes),
                str(ROOT / "src/main/java/fixture/api/FixtureApi.java"),
                str(ROOT / "src/main/java/fixture/representative/RepresentativeMod.java"),
            ], check=True)
            subprocess.run([
                str(JDK / "jar"), "--create", "--file", str(archive),
                "-C", str(classes), ".", "-C", str(ROOT), "fabric.mod.json",
                "-C", str(ROOT / "src/main/resources"), ".",
            ], check=True)
            source_ir, jar_ir = scan_path(ROOT), scan_path(archive)
            self.assertEqual(
                {(x["kind"], x["identifier"]) for x in source_ir["content"]},
                {(x["kind"], x["identifier"]) for x in jar_ir["content"]},
            )
            source_fingerprints = {x["id"]: x["fingerprint"]["sha256"] for x in source_ir["behaviors"]}
            jar_fingerprints = {x["id"]: x["fingerprint"]["sha256"] for x in jar_ir["behaviors"]}
            self.assertEqual(source_fingerprints, jar_fingerprints)
            self.assertTrue(all(e["source_mode"] == "bytecode-javap" for b in jar_ir["behaviors"] for e in b["evidence"]))
            self.assertEqual(1, len(jar_ir["unsupported_hooks"]))


if __name__ == "__main__":
    unittest.main()
