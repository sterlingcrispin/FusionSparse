from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re


CLASS_RE = re.compile(
    r"^\s*class\s+(?P<name>\w+)\s*(?::\s*public\s+(?P<bases>[^{]+))?\s*\{(?P<body>.*?)^\s*};",
    re.MULTILINE | re.DOTALL,
)
ENUM_RE = re.compile(
    r"^\s*enum\s+(?P<name>\w+)\s*\{(?P<body>.*?)^\s*};",
    re.MULTILINE | re.DOTALL,
)


def parse_cpp_headers(include_root: str | Path) -> dict[str, list[dict[str, object]]]:
    root = Path(include_root)
    symbols: list[dict[str, object]] = []
    enums: list[dict[str, object]] = []

    for header_path in sorted(_iter_header_files(root)):
        relative = header_path.relative_to(root)
        source_text = header_path.read_text(encoding="utf-8", errors="ignore")
        namespace = _namespace_for_path(relative)
        enums.extend(_parse_enums(source_text, namespace, relative.as_posix()))
        symbols.extend(_parse_classes(source_text, namespace, relative.as_posix()))

    symbols.sort(key=lambda item: (str(item["id"]), int(item["line_start"]), str(item["kind"])))
    enums.sort(key=lambda item: (str(item["id"]), int(item["line_start"])))
    return {"symbols": symbols, "enums": enums}


def write_cpp_symbols(symbols: list[dict[str, object]], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(symbols, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def write_cpp_enums(enums: list[dict[str, object]], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(enums, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def write_cpp_summary_report(
    symbols: list[dict[str, object]],
    enums: list[dict[str, object]],
    output_path: str | Path,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    kinds = Counter(symbol["kind"] for symbol in symbols)
    namespaces = Counter(symbol["namespace"] for symbol in symbols)
    lines = [
        "# C++ Symbols Summary",
        "",
        f"- Total symbols: `{len(symbols)}`",
        f"- Total enums: `{len(enums)}`",
        "",
        "## By kind",
        "",
    ]
    for kind, count in sorted(kinds.items()):
        lines.append(f"- `{kind}`: `{count}`")

    lines.extend(["", "## Top namespaces", ""])
    for namespace, count in namespaces.most_common(10):
        lines.append(f"- `{namespace}`: `{count}`")

    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def _iter_header_files(root: Path):
    for path in root.rglob("*.h"):
        parts = path.relative_to(root).parts
        if any(part.startswith(".") for part in parts):
            continue
        yield path


def _parse_enums(source_text: str, namespace: str, source_path: str) -> list[dict[str, object]]:
    enums = []
    for match in ENUM_RE.finditer(source_text):
        name = match.group("name")
        members = _parse_enum_members(match.group("body"))
        line_start, line_end = _line_span(source_text, match.start(), match.end())
        enums.append(
            {
                "id": f"{namespace}.{name}",
                "kind": "enum",
                "name": name,
                "namespace": namespace,
                "cpp_qualified_name": f"{namespace.replace('.', '::')}::{name}",
                "members": members,
                "source_path": source_path,
                "line_start": line_start,
                "line_end": line_end,
            }
        )
    return enums


def _parse_classes(source_text: str, namespace: str, source_path: str) -> list[dict[str, object]]:
    symbols = []
    for match in CLASS_RE.finditer(source_text):
        name = match.group("name")
        bases = _split_bases(match.group("bases"))
        class_id = f"{namespace}.{name}"
        line_start, line_end = _line_span(source_text, match.start(), match.end())
        symbols.append(
            {
                "id": class_id,
                "kind": "class",
                "name": name,
                "owner": None,
                "namespace": namespace,
                "display_name": name,
                "cpp_qualified_name": f"{namespace.replace('.', '::')}::{name}",
                "bases": bases,
                "parameters": [],
                "return_type": None,
                "source_path": source_path,
                "line_start": line_start,
                "line_end": line_end,
                "flags": {},
            }
        )

        for method in _parse_public_methods(match.group("body")):
            method_name = method["name"]
            method["id"] = f"{class_id}.{method_name}"
            method["owner"] = class_id
            method["namespace"] = namespace
            method["display_name"] = f"{name}.{method_name}"
            method["cpp_qualified_name"] = f"{namespace.replace('.', '::')}::{name}::{method_name}"
            method["source_path"] = source_path
            method["line_start"] = line_start
            method["line_end"] = line_end
            symbols.append(method)

    return symbols


def _parse_public_methods(class_body: str) -> list[dict[str, object]]:
    methods = []
    visibility = "private"
    declaration_lines: list[str] = []
    skip_template = False

    for raw_line in class_body.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped in {"public:", "protected:", "private:"}:
            visibility = stripped[:-1]
            declaration_lines = []
            skip_template = False
            continue
        if visibility != "public":
            continue
        if stripped.startswith("//"):
            continue
        if stripped.startswith("template "):
            skip_template = True
            continue
        if skip_template:
            if ";" in stripped:
                skip_template = False
            continue
        declaration_lines.append(stripped)
        if ";" not in stripped:
            continue

        declaration = " ".join(declaration_lines)
        declaration_lines = []
        method = _parse_method_declaration(declaration)
        if method:
            methods.append(method)

    return methods


def _parse_method_declaration(declaration: str) -> dict[str, object] | None:
    if not declaration.endswith(";"):
        return None
    if declaration.startswith(("typedef ", "using ", "friend ")):
        return None

    declaration = declaration[:-1].strip()
    while declaration and declaration.split(" ", 1)[0].isupper():
        head, _, rest = declaration.partition(" ")
        if not rest:
            break
        declaration = rest.strip()

    is_static = declaration.startswith("static ")
    if is_static:
        declaration = declaration[len("static "):].strip()

    is_virtual = declaration.startswith("virtual ")
    if is_virtual:
        declaration = declaration[len("virtual "):].strip()

    if "(" not in declaration or ")" not in declaration:
        return None

    head, remainder = declaration.split("(", 1)
    params_text, tail = remainder.rsplit(")", 1)
    head = head.strip()
    tail = tail.strip()

    tokens = head.split()
    if len(tokens) < 2:
        return None

    name = tokens[-1]
    if name.startswith("~"):
        return None

    return_type = " ".join(tokens[:-1]).strip()
    if not return_type:
        return None

    return {
        "kind": "method",
        "name": name,
        "parameters": _parse_parameters(params_text),
        "return_type": return_type,
        "flags": {
            "static": is_static,
            "virtual": is_virtual,
            "const": "const" in tail.split(),
            "pure_virtual": "= 0" in tail,
            "override": "override" in tail.split(),
        },
        "bases": [],
    }


def _parse_parameters(params_text: str) -> list[dict[str, object]]:
    params_text = params_text.strip()
    if not params_text or params_text == "void":
        return []

    parameters = []
    for raw_param in _split_top_level(params_text):
        parameter = raw_param.strip()
        parameter = _strip_default(parameter)
        if not parameter:
            continue
        name, type_name = _split_parameter(parameter)
        parameters.append({"name": name, "type": type_name, "raw": raw_param.strip()})
    return parameters


def _parse_enum_members(body: str) -> list[dict[str, object]]:
    members = []
    next_implicit_value = 0
    declaration_lines: list[str] = []
    for raw_line in body.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("///"):
            continue
        if "//" in stripped:
            stripped = stripped.split("//", 1)[0].strip()
        declaration_lines.append(stripped)
        if not stripped.endswith(","):
            member = " ".join(declaration_lines).strip().strip(",")
            declaration_lines = []
        else:
            member = " ".join(declaration_lines).strip().strip(",")
            declaration_lines = []
        if not member:
            continue
        if "=" in member:
            name, raw_value = [part.strip() for part in member.split("=", 1)]
            value = _parse_int(raw_value)
            next_implicit_value = value + 1 if value is not None else next_implicit_value + 1
            members.append({"name": name, "value": raw_value, "numeric_value": value})
        else:
            members.append({"name": member, "value": str(next_implicit_value), "numeric_value": next_implicit_value})
            next_implicit_value += 1
    return members


def _split_bases(bases: str | None) -> list[str]:
    if not bases:
        return []
    return [base.strip().removeprefix("public ").strip() for base in bases.split(",") if base.strip()]


def _strip_default(parameter: str) -> str:
    depth = 0
    for index, char in enumerate(parameter):
        if char in "<([{":
            depth += 1
        elif char in ">)]}":
            depth = max(depth - 1, 0)
        elif char == "=" and depth == 0:
            return parameter[:index].strip()
    return parameter


def _split_parameter(parameter: str) -> tuple[str | None, str]:
    match = re.match(r"(?P<type>.+?)(?P<name>[A-Za-z_]\w*)$", parameter)
    if not match:
        return None, parameter
    type_name = match.group("type").strip()
    name = match.group("name")
    return name, type_name


def _split_top_level(text: str) -> list[str]:
    parts = []
    current = []
    depth = 0
    for char in text:
        if char in "<([{":
            depth += 1
        elif char in ">)]}":
            depth = max(depth - 1, 0)
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    if current:
        parts.append("".join(current))
    return parts


def _parse_int(raw_value: str) -> int | None:
    try:
        return int(raw_value, 0)
    except ValueError:
        return None


def _line_span(source_text: str, start: int, end: int) -> tuple[int, int]:
    return source_text.count("\n", 0, start) + 1, source_text.count("\n", 0, end) + 1


def _namespace_for_path(relative_path: Path) -> str:
    module = relative_path.parts[0].lower()
    return f"adsk.{module}"
