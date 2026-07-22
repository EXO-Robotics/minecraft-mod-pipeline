from __future__ import annotations

import re
from typing import Any


def class_constant_evidence(path: str, data: bytes) -> dict[str, Any]:
    """Conservative fallback: inventory readable class constants, never infer behavior."""
    strings = sorted({m.decode("utf-8", "ignore") for m in re.findall(rb"[A-Za-z_$][A-Za-z0-9_$/.:()-]{3,}", data)})
    return {"class_file": path, "source_mode": "bytecode-constants", "analyzer_version": "jar-bytecode/1.0.0", "constants": strings[:250], "semantic_claims": [], "diagnostics": [{"severity": "info", "code": "bytecode_semantics_unresolved", "message": "Install a JDK for javap-backed instruction analysis."}]}
