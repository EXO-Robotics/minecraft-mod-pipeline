from __future__ import annotations

import re
from pathlib import Path
from typing import Any


ANALYZER_VERSION = "loader-neutral-javap/1.0.0"


def _fact(kind: str, archive: Path, class_name: str, **values: Any) -> dict[str, Any]:
    return {
        "fact_type": kind,
        "archive": archive.name,
        "class": class_name,
        "source_file": f"{archive.name}!/{class_name.replace('.', '/')}.class",
        "source_mode": "bytecode-javap",
        "analyzer_version": ANALYZER_VERSION,
        "confidence": .72,
        **values,
    }


def parse_javap(archive: Path, class_name: str, output: str) -> list[dict[str, Any]]:
    """Parse conservative, loader-neutral facts from ``javap -v -c -l -s`` output.

    Facts describe only class-file structure and instructions. Loader meaning is
    deliberately assigned later by Fabric/Forge adapters.
    """
    facts: list[dict[str, Any]] = []
    class_header = re.search(r"^(?:public\s+)?(?:final\s+)?(?:class|interface|enum)\s+([\w.$]+)(?:\s+extends\s+([\w.$]+))?(?:\s+implements\s+([^\n{]+))?", output, re.MULTILINE)
    if class_header:
        facts.append(_fact(
            "class", archive, class_name,
            name=class_header.group(1), super_name=class_header.group(2),
            interfaces=sorted(x.strip() for x in (class_header.group(3) or "").split(",") if x.strip()),
        ))
    else:
        facts.append(_fact("class", archive, class_name, name=class_name, super_name=None, interfaces=[]))

    current_method: str | None = None
    current_descriptor: str | None = None
    annotation_pending = False
    for line_number, line in enumerate(output.splitlines(), 1):
        header = re.match(r"^\s{2}(?:public|protected|private|static|final|synchronized|native|abstract|strictfp).+?\s([\w$<>]+)\([^;]*\);$", line)
        if header:
            current_method = header.group(1)
            current_descriptor = None
            continue
        descriptor = re.match(r"^\s+descriptor:\s+(\S+)", line)
        if descriptor and current_method:
            current_descriptor = descriptor.group(1)
            facts.append(_fact("method", archive, class_name, name=current_method, descriptor=current_descriptor))
            continue
        if re.match(r"^\s+\d+:\s+#\d+\([^)]*\)\s*$", line):
            annotation_pending = True
            continue
        annotation_name = re.match(r"^\s+([a-zA-Z_$][\w.$]+)(?:\(|\s*$)", line)
        if annotation_pending and annotation_name:
            facts.append(_fact("annotation", archive, class_name, annotation=annotation_name.group(1), method=current_method))
            annotation_pending = False
        invoke = re.search(r"\b(invoke\w+)\s+#\d+\s+//\s+(?:InterfaceMethod|Method)\s+([^.:\s]+(?:/[^.:\s]+)*)\.([\w$<>]+):(\S+)", line)
        if invoke:
            facts.append(_fact(
                "invoke", archive, class_name, method=current_method, opcode=invoke.group(1),
                owner=invoke.group(2).replace("/", "."), name=invoke.group(3), descriptor=invoke.group(4),
                instruction_line=line_number,
            ))
        field = re.search(r"\b(getstatic|putstatic|getfield|putfield)\s+#\d+\s+//\s+Field\s+([^.:\s]+(?:/[^.:\s]+)*)\.([\w$]+):(\S+)", line)
        if field:
            facts.append(_fact(
                "field", archive, class_name, method=current_method, opcode=field.group(1),
                owner=field.group(2).replace("/", "."), name=field.group(3), descriptor=field.group(4),
                instruction_line=line_number,
            ))
        constant = re.search(r"\bldc(?:_w|2_w)?\s+#\d+\s+//\s+(?:String\s+)?(.+)$", line)
        if constant:
            value = constant.group(1).strip()
            facts.append(_fact("constant", archive, class_name, method=current_method, value=value, instruction_line=line_number))
        field_constant = re.match(r"^\s+ConstantValue:\s+(?:String\s+)?(.+)$", line)
        if field_constant:
            facts.append(_fact("constant", archive, class_name, method=None, value=field_constant.group(1).strip(), instruction_line=line_number, constant_source="field"))

    # Runtime annotations are rendered with a binary owner followed by an
    # argument block. Capture the owner; adapter-specific argument decoding is
    # intentionally separate.
    for match in re.finditer(r"^\s+(?:\d+:\s+#\d+\([^)]*\)\s*)?([a-zA-Z_$][\w.$]+)\($", output, re.MULTILINE):
        facts.append(_fact("annotation", archive, class_name, annotation=match.group(1), method=None))
    return _dedupe(facts)


def resource_facts(archive: Path, entries: list[str]) -> list[dict[str, Any]]:
    facts = []
    for entry in entries:
        if entry.endswith(".class") or entry.endswith("/"):
            continue
        facts.append({
            "fact_type": "resource", "archive": archive.name, "path": entry,
            "source_file": f"{archive.name}!/{entry}", "source_mode": "archive-resource",
            "analyzer_version": ANALYZER_VERSION, "confidence": .95,
        })
    return facts


def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []
    for row in rows:
        marker = repr(sorted(row.items()))
        if marker not in seen:
            seen.add(marker)
            result.append(row)
    return result
