from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, cast

from .layout import INITIAL_DOCUMENTS, ensure_layout


class ProjectError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ProjectStore:
    SCHEMA_VERSION = "1.0.0"

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()

    @classmethod
    def create(cls, root: str | Path, *, name: str | None = None, target_profile: str = "MARKETPLACE_ADDON_STABLE") -> "ProjectStore":
        store = cls(root)
        manifest_path = store.root / "project.yaml"
        if manifest_path.exists():
            raise ProjectError("PROJECT_EXISTS", f"Conversion project already exists: {store.root}")
        store.root.mkdir(parents=True, exist_ok=True)
        ensure_layout(store.root)
        manifest = {
            "schema_version": cls.SCHEMA_VERSION,
            "name": name or store.root.name,
            "target_profile": target_profile,
            "revision": 1,
            "analysis_revision": 0,
            "input": None,
        }
        for relative, document in INITIAL_DOCUMENTS.items():
            store.write(relative, document)
        store.write("project.yaml", manifest)
        return store

    @classmethod
    def open(cls, root: str | Path) -> "ProjectStore":
        store = cls(root)
        if not store.root.is_dir() or not (store.root / "project.yaml").is_file():
            raise ProjectError("PROJECT_NOT_FOUND", f"Conversion project not found: {store.root}")
        manifest = store.read("project.yaml")
        if not isinstance(manifest, dict) or manifest.get("schema_version") != cls.SCHEMA_VERSION:
            raise ProjectError("INVALID_PROJECT", "project.yaml is missing or has an unsupported schema")
        ensure_layout(store.root)
        return store

    def resolve(self, relative: str | Path) -> Path:
        candidate = (self.root / relative).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ProjectError("INVALID_PATH", f"Project path escapes root: {relative}")
        return candidate

    def read(self, relative: str | Path, default: Any = None) -> Any:
        path = self.resolve(relative)
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return default
        except (OSError, json.JSONDecodeError) as exc:
            raise ProjectError("INVALID_PROJECT_DOCUMENT", f"Cannot read {relative}: {exc}") from exc

    def write(self, relative: str | Path, value: Any) -> None:
        path = self.resolve(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def write_text(self, relative: str | Path, value: str) -> None:
        path = self.resolve(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(value)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    @property
    def manifest(self) -> dict[str, Any]:
        return cast(dict[str, Any], self.read("project.yaml"))

    @property
    def revision(self) -> int:
        return int(self.manifest.get("revision", 0))

    def commit(self, documents: Mapping[str, Any], *, expected_revision: int | None = None, manifest_updates: Mapping[str, Any] | None = None) -> int:
        manifest = self.manifest
        current = int(manifest.get("revision", 0))
        if expected_revision is not None and expected_revision != current:
            raise ProjectError("REVISION_CONFLICT", f"Expected project revision {expected_revision}, found {current}")
        for relative, value in documents.items():
            if str(relative).startswith("custom/"):
                raise ProjectError("PROTECTED_PATH", f"Operations cannot overwrite protected path: {relative}")
            self.write(relative, value)
        manifest.update(dict(manifest_updates or {}))
        manifest["revision"] = current + 1
        self.write("project.yaml", manifest)
        return current + 1

    def commit_protected(self, relative: str | Path, value: Any, *, expected_revision: int, author: str, reason: str) -> int:
        """Write one explicitly user-owned custom artifact with revision provenance.

        Ordinary generated commits remain forbidden from touching ``custom/``.
        This separate entry point exists only for deliberate safe-edit operations.
        """
        path_text = str(relative)
        allowed = ("custom/scripts/", "custom/entities/", "custom/models/", "custom/assets/")
        if not path_text.startswith(allowed) or path_text.endswith("/"):
            raise ProjectError("INVALID_PROTECTED_PATH", f"Protected edits require a file under an allowed custom directory: {relative}")
        if not author.strip() or not reason.strip():
            raise ProjectError("MISSING_PROVENANCE", "Protected edits require author and reason")
        current = self.revision
        if expected_revision != current:
            raise ProjectError("REVISION_CONFLICT", f"Expected project revision {expected_revision}, found {current}")
        if isinstance(value, str):
            self.write_text(relative, value)
        else:
            self.write(relative, value)
        audit = self.read("decisions/protected-edits.json", {"schema_version": "1.0.0", "edits": []})
        edits = list(audit.get("edits", [])) if isinstance(audit, dict) else []
        edits.append({"path": path_text, "author": author, "reason": reason, "revision": current + 1})
        self.write("decisions/protected-edits.json", {"schema_version": "1.0.0", "edits": edits})
        manifest = self.manifest
        manifest["revision"] = current + 1
        self.write("project.yaml", manifest)
        return current + 1
