from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".json", ".toml", ".yaml", ".yml"}


class PortableDistributionTests(unittest.TestCase):
    def repository_text(self) -> str:
        chunks: list[str] = []
        for path in sorted(ROOT.rglob("*")):
            if (
                path.is_file()
                and path.suffix in TEXT_SUFFIXES
                and ".git" not in path.parts
                and ".venv" not in path.parts
                and "__pycache__" not in path.parts
            ):
                chunks.append(path.read_text(encoding="utf-8"))
        return "\n".join(chunks)

    def test_distribution_contains_no_operator_absolute_paths(self) -> None:
        forbidden_prefix = "/" + "Users/"
        self.assertNotIn(forbidden_prefix, self.repository_text())

    def test_every_referenced_skill_is_bundled(self) -> None:
        referenced: set[str] = set()
        for skill in (ROOT / "skills").glob("*/SKILL.md"):
            referenced.update(re.findall(r"\$([a-z0-9][a-z0-9-]+)", skill.read_text()))
        missing = sorted(
            name for name in referenced if not (ROOT / "skills" / name / "SKILL.md").is_file()
        )
        self.assertEqual(missing, [])

    def test_skill_catalog_covers_every_bundled_skill(self) -> None:
        catalog = (ROOT / "JAVA_BEDROCK_CODEX_SKILLS.md").read_text(encoding="utf-8")
        missing = sorted(
            skill.name
            for skill in (ROOT / "skills").iterdir()
            if (skill / "SKILL.md").is_file() and f"`{skill.name}`" not in catalog
        )
        self.assertEqual(missing, [])

    def test_mailbox_schemas_are_distribution_owned(self) -> None:
        for schema in (ROOT / "schemas" / "mailbox").glob("*.json"):
            self.assertIn("bedrock-ai-factory.local", schema.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
