from __future__ import annotations

import ast
from collections import Counter
import json
from pathlib import Path
import warnings


def parse_python_defs(defs_root: str | Path) -> list[dict[str, object]]:
    root = Path(defs_root)
    symbols: list[dict[str, object]] = []
    for source_path in sorted(_iter_python_files(root)):
        relative = source_path.relative_to(root)
        module_name = _module_name(relative)
        source_text = source_path.read_text(encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            module = ast.parse(source_text, filename=str(source_path))
        symbols.extend(_parse_module(module, module_name, relative.as_posix(), source_text))

    return sorted(symbols, key=lambda item: (str(item["id"]), int(item["line_start"]), str(item["kind"])))


def write_python_symbols(symbols: list[dict[str, object]], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(symbols, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def write_python_summary_report(symbols: list[dict[str, object]], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    kinds = Counter(symbol["kind"] for symbol in symbols)
    modules = Counter(symbol["module"] for symbol in symbols if symbol["kind"] != "module")
    lines = [
        "# Python Symbols Summary",
        "",
        f"- Total symbols: `{len(symbols)}`",
        "",
        "## By kind",
        "",
    ]
    for kind, count in sorted(kinds.items()):
        lines.append(f"- `{kind}`: `{count}`")

    lines.extend(["", "## Top modules", ""])
    for module_name, count in modules.most_common(10):
        lines.append(f"- `{module_name}`: `{count}`")

    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def _iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        relative_parts = path.relative_to(root).parts
        if any(part.startswith(".") for part in relative_parts):
            continue
        yield path
    for path in root.rglob("*.pyi"):
        relative_parts = path.relative_to(root).parts
        if any(part.startswith(".") for part in relative_parts):
            continue
        yield path


def _module_name(relative_path: Path) -> str:
    parts = list(relative_path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _parse_module(module: ast.Module, module_name: str, relative_path: str, source_text: str) -> list[dict[str, object]]:
    module_line_count = len(source_text.splitlines()) or 1
    records = [
        _base_record(
            symbol_id=module_name,
            kind="module",
            name=module_name.rsplit(".", 1)[-1],
            owner=None,
            namespace=module_name,
            display_name=module_name,
            module=module_name,
            class_name=None,
            decorators=[],
            parameters=[],
            return_annotation=None,
            docstring=ast.get_docstring(module, clean=False),
            bases=[],
            source_path=relative_path,
            line_start=1,
            line_end=module_line_count,
            flags={},
            value=None,
        )
    ]

    for node in module.body:
        if _is_docstring_node(node):
            continue
        if isinstance(node, ast.ClassDef):
            records.extend(_parse_class(node, module_name, relative_path))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            records.append(_function_record(node, module_name, relative_path, owner=None, class_name=None))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            records.extend(
                _assignment_records(
                    node,
                    module_name=module_name,
                    relative_path=relative_path,
                    owner=module_name,
                    namespace=module_name,
                    class_name=None,
                    enum_member=False,
                )
            )

    return records


def _parse_class(node: ast.ClassDef, module_name: str, relative_path: str) -> list[dict[str, object]]:
    fqcn = f"{module_name}.{node.name}"
    enum_like = _is_enum_like(node)
    records = [
        _base_record(
            symbol_id=fqcn,
            kind="enum" if enum_like else "class",
            name=node.name,
            owner=module_name,
            namespace=module_name,
            display_name=node.name,
            module=module_name,
            class_name=node.name,
            decorators=[_expr_text(decorator) for decorator in node.decorator_list],
            parameters=[],
            return_annotation=None,
            docstring=ast.get_docstring(node, clean=False),
            bases=[_expr_text(base) for base in node.bases],
            source_path=relative_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            flags={"enum_like": enum_like},
            value=None,
        )
    ]

    property_setters = {
        method.name
        for method in node.body
        if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(_expr_text(decorator).endswith(".setter") for decorator in method.decorator_list)
    }

    for child in node.body:
        if _is_docstring_node(child):
            continue
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(_expr_text(decorator).endswith(".setter") for decorator in child.decorator_list):
                continue
            records.append(
                _function_record(
                    child,
                    module_name,
                    relative_path,
                    owner=fqcn,
                    class_name=node.name,
                    has_setter=child.name in property_setters,
                )
            )
        elif isinstance(child, (ast.Assign, ast.AnnAssign)):
            records.extend(
                _assignment_records(
                    child,
                    module_name=module_name,
                    relative_path=relative_path,
                    owner=fqcn,
                    namespace=module_name,
                    class_name=node.name,
                    enum_member=enum_like,
                )
            )

    return records


def _function_record(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module_name: str,
    relative_path: str,
    owner: str | None,
    class_name: str | None,
    has_setter: bool = False,
) -> dict[str, object]:
    decorators = [_expr_text(decorator) for decorator in node.decorator_list]
    is_property = "property" in decorators
    kind = "property" if is_property else "method" if owner else "function"
    display_name = f"{owner.rsplit('.', 1)[-1]}.{node.name}" if owner and class_name else node.name
    symbol_id = f"{owner}.{node.name}" if owner else f"{module_name}.{node.name}"
    flags = {
        "staticmethod": "staticmethod" in decorators,
        "classmethod": "classmethod" in decorators,
        "property": is_property,
        "has_setter": has_setter,
        "async": isinstance(node, ast.AsyncFunctionDef),
    }

    return _base_record(
        symbol_id=symbol_id,
        kind=kind,
        name=node.name,
        owner=owner,
        namespace=module_name,
        display_name=display_name,
        module=module_name,
        class_name=class_name,
        decorators=decorators,
        parameters=_parameter_records(node),
        return_annotation=_expr_text(node.returns),
        docstring=ast.get_docstring(node, clean=False),
        bases=[],
        source_path=relative_path,
        line_start=node.lineno,
        line_end=node.end_lineno or node.lineno,
        flags=flags,
        value=None,
    )


def _assignment_records(
    node: ast.Assign | ast.AnnAssign,
    module_name: str,
    relative_path: str,
    owner: str,
    namespace: str,
    class_name: str | None,
    enum_member: bool,
) -> list[dict[str, object]]:
    records = []
    if isinstance(node, ast.Assign):
        targets = [target for target in node.targets if isinstance(target, ast.Name)]
        value = _expr_text(node.value)
        annotation = None
    else:
        targets = [node.target] if isinstance(node.target, ast.Name) else []
        value = _expr_text(node.value)
        annotation = _expr_text(node.annotation)

    for target in targets:
        symbol_id = f"{owner}.{target.id}"
        records.append(
            _base_record(
                symbol_id=symbol_id,
                kind="constant",
                name=target.id,
                owner=owner,
                namespace=namespace,
                display_name=f"{owner.rsplit('.', 1)[-1]}.{target.id}",
                module=module_name,
                class_name=class_name,
                decorators=[],
                parameters=[],
                return_annotation=annotation,
                docstring=None,
                bases=[],
                source_path=relative_path,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                flags={"enum_member": enum_member},
                value=value,
            )
        )

    return records


def _parameter_records(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict[str, object]]:
    args = node.args
    positional = list(args.posonlyargs) + list(args.args)
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)

    parameters = []
    for index, argument in enumerate(args.posonlyargs):
        parameters.append(
            _parameter_record(argument, "positional_only", defaults[index])
        )

    offset = len(args.posonlyargs)
    for index, argument in enumerate(args.args):
        parameters.append(
            _parameter_record(argument, "positional_or_keyword", defaults[offset + index])
        )

    if args.vararg:
        parameters.append(_parameter_record(args.vararg, "vararg", None))

    for index, argument in enumerate(args.kwonlyargs):
        parameters.append(
            _parameter_record(argument, "keyword_only", args.kw_defaults[index])
        )

    if args.kwarg:
        parameters.append(_parameter_record(args.kwarg, "kwarg", None))

    return parameters


def _parameter_record(argument: ast.arg, kind: str, default: ast.AST | None) -> dict[str, object]:
    return {
        "name": argument.arg,
        "kind": kind,
        "annotation": _expr_text(argument.annotation),
        "default": _expr_text(default),
    }


def _is_enum_like(node: ast.ClassDef) -> bool:
    saw_assignment = False
    for child in node.body:
        if _is_docstring_node(child) or isinstance(child, ast.Pass):
            continue
        if isinstance(child, (ast.Assign, ast.AnnAssign)):
            saw_assignment = True
            continue
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == "__init__":
            if _function_is_pass_only(child):
                continue
        return False
    return saw_assignment


def _function_is_pass_only(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    meaningful = [child for child in node.body if not _is_docstring_node(child)]
    return len(meaningful) == 1 and isinstance(meaningful[0], ast.Pass)


def _base_record(
    *,
    symbol_id: str,
    kind: str,
    name: str,
    owner: str | None,
    namespace: str,
    display_name: str,
    module: str,
    class_name: str | None,
    decorators: list[str],
    parameters: list[dict[str, object]],
    return_annotation: str | None,
    docstring: str | None,
    bases: list[str],
    source_path: str,
    line_start: int,
    line_end: int,
    flags: dict[str, object],
    value: str | None,
) -> dict[str, object]:
    return {
        "id": symbol_id,
        "kind": kind,
        "name": name,
        "owner": owner,
        "namespace": namespace,
        "display_name": display_name,
        "python_path": symbol_id,
        "module": module,
        "class_name": class_name,
        "decorators": decorators,
        "parameters": parameters,
        "return_annotation": return_annotation,
        "docstring": docstring,
        "bases": bases,
        "source_path": source_path,
        "line_start": line_start,
        "line_end": line_end,
        "flags": flags,
        "value": value,
    }


def _expr_text(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    return ast.unparse(node)


def _is_docstring_node(node: ast.AST) -> bool:
    return isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) and isinstance(node.value.value, str)
