"""Content-addressed evidence objects and logical-path Merkle manifests."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


class ObjectStoreError(RuntimeError):
    pass


class EvidenceObjectStore:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()

    def _path(self, digest: str) -> Path:
        return self.root / "sha256" / digest[:2] / digest[2:]

    def put_bytes(self, data: bytes, *, object_type: str) -> dict[str, Any]:
        digest = hashlib.sha256(data).hexdigest()
        target = self._path(digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != data:
            raise ObjectStoreError("content-address collision")
        if not target.exists():
            temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
            temporary.write_bytes(data)
            os.replace(temporary, target)
        return {"sha256": digest, "object_type": object_type, "size": len(data)}

    def put_file(self, source: str | Path, *, object_type: str) -> dict[str, Any]:
        return self.put_bytes(Path(source).read_bytes(), object_type=object_type)

    def get(self, reference: dict[str, Any]) -> bytes:
        digest = reference.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ObjectStoreError("invalid object reference")
        data = self._path(digest).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ObjectStoreError("stored object digest mismatch")
        return data

    def put_merkle_manifest(self, files: dict[str, bytes], *, object_type: str) -> dict[str, Any]:
        entries = []
        for logical_path, data in sorted(files.items()):
            if logical_path.startswith("/") or ".." in Path(logical_path).parts:
                raise ObjectStoreError("manifest paths must be logical and relative")
            reference = self.put_bytes(data, object_type="evidence-blob-v1")
            entries.append({"logical_path": logical_path, **reference})
        payload = json.dumps({"entries": entries}, sort_keys=True, separators=(",", ":")).encode()
        root = self.put_bytes(payload, object_type=object_type)
        return {**root, "entry_count": len(entries)}
