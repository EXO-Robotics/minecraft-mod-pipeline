from __future__ import annotations

from typing import Any


def validate_ir(ir: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ("schema_version", "metadata", "dependencies", "content", "assets", "registries", "behaviors", "state", "presentation_requirements", "world_requirements", "ui_intent", "networking_intent", "unsupported_hooks", "diagnostics", "tests")
    for key in required:
        if key not in ir:
            errors.append(f"ModIR missing {key}")
    for behavior in ir.get("behaviors", []):
        for key in ("id", "owner", "trigger", "conditions", "actions", "evidence", "confidence", "diagnostics"):
            if key not in behavior:
                errors.append(f"Behavior {behavior.get('id', '<unknown>')} missing {key}")
        if not behavior.get("evidence") and not behavior.get("override_provenance"):
            errors.append(f"Behavior {behavior.get('id')} has no evidence or override provenance")
    return errors


MIGRATIONS = {("0.1.0", "1.0.0"): "scan-and-enrich"}

