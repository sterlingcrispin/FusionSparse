from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
from typing import Any


def merge_sources(
    python_symbols: list[dict[str, Any]],
    cpp_symbols: list[dict[str, Any]],
    cpp_enums: list[dict[str, Any]],
    doc_pages: list[dict[str, Any]],
) -> dict[str, Any]:
    python_by_id = {symbol["id"]: symbol for symbol in python_symbols}
    cpp_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for symbol in cpp_symbols:
        cpp_by_id[symbol["id"]].append(symbol)
    cpp_enums_by_id = {enum["id"]: enum for enum in cpp_enums}
    doc_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in doc_pages:
        if page.get("symbol_id"):
            doc_by_id[page["symbol_id"]].append(page)

    all_ids = sorted(set(python_by_id) | set(cpp_by_id) | set(cpp_enums_by_id) | set(doc_by_id))
    conflicts: list[dict[str, str]] = []
    merged_symbols: list[dict[str, Any]] = []

    for symbol_id in all_ids:
        python_symbol = python_by_id.get(symbol_id)
        cpp_candidates = cpp_by_id.get(symbol_id, [])
        cpp_enum = cpp_enums_by_id.get(symbol_id)
        docs = sorted(doc_by_id.get(symbol_id, []), key=lambda page: str(page["source_path"]))
        merged_symbols.append(_merge_symbol(symbol_id, python_symbol, cpp_candidates, cpp_enum, docs, conflicts))

    merged_symbols.sort(key=lambda item: (str(item["id"]), str(item["kind"])))
    _apply_traits(merged_symbols)
    enums = _build_enums(merged_symbols, cpp_enums_by_id, doc_by_id)
    families = _build_families(merged_symbols)

    return {
        "symbols": merged_symbols,
        "enums": enums,
        "families": families,
        "conflicts": sorted(conflicts, key=lambda item: (item["symbol_id"], item["field"], item["source"])),
    }


def write_symbols(symbols: list[dict[str, Any]], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(symbols, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def write_enums(enums: list[dict[str, Any]], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(enums, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def write_families(families: list[dict[str, Any]], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(families, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def write_merge_conflicts(conflicts: list[dict[str, str]], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Merge Conflicts",
        "",
        f"- Total conflicts: `{len(conflicts)}`",
        "",
    ]
    if not conflicts:
        lines.append("No conflicts detected in this merge pass.")
    else:
        for conflict in conflicts:
            lines.append(
                f"- `{conflict['symbol_id']}` `{conflict['field']}`: "
                f"canonical=`{conflict['canonical']}` vs {conflict['source']}=`{conflict['value']}`"
            )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def _merge_symbol(
    symbol_id: str,
    python_symbol: dict[str, Any] | None,
    cpp_candidates: list[dict[str, Any]],
    cpp_enum: dict[str, Any] | None,
    docs: list[dict[str, Any]],
    conflicts: list[dict[str, str]],
) -> dict[str, Any]:
    cpp_symbol = _select_cpp_symbol(python_symbol, cpp_candidates)
    primary_kind = (
        python_symbol.get("kind") if python_symbol else None
    ) or (
        cpp_symbol.get("kind") if cpp_symbol else None
    ) or (
        "enum" if cpp_enum else None
    ) or (
        _doc_kind(docs[0]) if docs else None
    )

    name = (
        python_symbol.get("name") if python_symbol else None
    ) or (
        cpp_symbol.get("name") if cpp_symbol else None
    ) or (
        cpp_enum.get("name") if cpp_enum else None
    ) or _name_from_symbol_id(symbol_id)
    owner = (
        python_symbol.get("owner") if python_symbol else None
    ) or (
        cpp_symbol.get("owner") if cpp_symbol else None
    ) or _owner_from_symbol_id(symbol_id)
    namespace = (
        python_symbol.get("namespace") if python_symbol else None
    ) or (
        cpp_symbol.get("namespace") if cpp_symbol else None
    ) or (
        docs[0]["namespace"].replace("::", ".") if docs and docs[0].get("namespace") else None
    ) or _namespace_from_symbol_id(symbol_id)

    if docs and not _expected_doc_property_bridge(primary_kind, _doc_kind(docs[0]), name):
        _record_if_mismatch(conflicts, symbol_id, "kind", primary_kind, _doc_kind(docs[0]), "docs")
    if cpp_symbol and not _expected_cpp_property_bridge(python_symbol, cpp_symbol):
        _record_if_mismatch(conflicts, symbol_id, "kind", primary_kind, cpp_symbol.get("kind"), "cpp")
    if cpp_enum:
        _record_if_mismatch(conflicts, symbol_id, "kind", primary_kind, "enum", "cpp_enum")

    signatures = []
    if python_symbol and python_symbol["kind"] in {"function", "method", "property"}:
        signatures.append(
            {
                "language": "python",
                "params": python_symbol.get("parameters", []),
                "returns": python_symbol.get("return_annotation"),
                "static": bool(python_symbol.get("flags", {}).get("staticmethod")),
                "classmethod": bool(python_symbol.get("flags", {}).get("classmethod")),
                "property": bool(python_symbol.get("flags", {}).get("property")),
            }
        )
    cpp_signature_candidates = _signature_candidates(python_symbol, cpp_candidates)
    for candidate in cpp_signature_candidates:
        signatures.append(
            {
                "language": "cpp",
                "params": candidate.get("parameters", []),
                "returns": candidate.get("return_type"),
                "static": bool(candidate.get("flags", {}).get("static")),
                "classmethod": False,
                "property": bool(python_symbol and python_symbol.get("kind") == "property"),
            }
        )
    if python_symbol and python_symbol["kind"] in {"function", "method", "property"} and cpp_symbol:
        _compare_signatures(conflicts, symbol_id, python_symbol, cpp_symbol)

    source_paths = sorted(
        set(
            _prefixed_source_path("Fusion_API_Python_Reference/defs", python_symbol.get("source_path") if python_symbol else None)
            + [
                f"Fusion_API_CPP_Reference/include/{candidate['source_path']}"
                for candidate in cpp_candidates
                if candidate.get("source_path")
            ]
            + _prefixed_source_path("Fusion_API_CPP_Reference/include", cpp_enum.get("source_path") if cpp_enum else None)
            + [
                f"Fusion_API_Documentation/files/{page['source_path']}"
                for page in docs
            ]
        )
    )

    doc_record = _merge_docs(docs)
    display_name = (
        python_symbol.get("display_name") if python_symbol else None
    ) or (
        cpp_symbol.get("display_name") if cpp_symbol else None
    ) or (
        docs[0]["symbol_key"] if docs and docs[0].get("symbol_key") else None
    ) or name

    return {
        "id": symbol_id,
        "kind": primary_kind,
        "name": name,
        "owner": owner,
        "namespace": namespace,
        "display_name": display_name,
        "python_path": python_symbol.get("python_path") if python_symbol else None,
        "cpp_qualified_name": (
            cpp_symbol.get("cpp_qualified_name") if cpp_symbol else None
        ) or (
            cpp_enum.get("cpp_qualified_name") if cpp_enum else None
        ),
        "source_paths": source_paths,
        "signatures": signatures,
        "value": python_symbol.get("value") if python_symbol else None,
        "doc": doc_record,
        "traits": {},
        "provenance": {
            "signature_source": "python_defs" if python_symbol else "cpp_headers" if cpp_symbol else None,
            "doc_source": "html" if docs else None,
            "kind_source": "python_defs" if python_symbol else "cpp_headers" if cpp_symbol or cpp_enum else "docs" if docs else None,
        },
        "lineage": {
            "python": bool(python_symbol),
            "cpp": bool(cpp_symbol),
            "cpp_enum": bool(cpp_enum),
            "docs": [page["source_path"] for page in docs],
        },
    }


def _merge_docs(docs: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not docs:
        return None
    primary = docs[0]
    return {
        "title": primary.get("title"),
        "description": primary.get("description"),
        "remarks": primary.get("remarks"),
        "parameters": primary.get("parameters", []),
        "return_value": primary.get("return_value"),
        "samples": primary.get("samples", []),
        "introduced_in": primary.get("version"),
        "headings": primary.get("headings", []),
        "related_links": primary.get("related_links", []),
        "header_file": primary.get("header_file"),
        "page_kind": primary.get("page_kind"),
    }


def _build_enums(
    merged_symbols: list[dict[str, Any]],
    cpp_enums_by_id: dict[str, dict[str, Any]],
    doc_by_id: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    merged_by_id = {symbol["id"]: symbol for symbol in merged_symbols}
    members_by_owner: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for symbol in merged_symbols:
        if symbol["kind"] == "constant" and symbol.get("owner"):
            members_by_owner[symbol["owner"]].append(symbol)

    enums = []
    enum_ids = sorted(
        {
            symbol["id"]
            for symbol in merged_symbols
            if symbol["kind"] == "enum"
        }
        | set(cpp_enums_by_id)
    )
    for enum_id in enum_ids:
        enum_symbol = merged_by_id.get(enum_id)
        cpp_enum = cpp_enums_by_id.get(enum_id)
        docs = doc_by_id.get(enum_id, [])
        members = {}
        for member in members_by_owner.get(enum_id, []):
            members[member["name"]] = {
                "name": member["name"],
                "value": member.get("doc", {}).get("value") if member.get("doc") else None,
                "python_value": _python_constant_value(member),
                "cpp_value": None,
                "doc_description": None,
            }
        if cpp_enum:
            for member in cpp_enum.get("members", []):
                entry = members.setdefault(
                    member["name"],
                    {
                        "name": member["name"],
                        "value": None,
                        "python_value": None,
                        "cpp_value": None,
                        "doc_description": None,
                    },
                )
                entry["value"] = member.get("value")
                entry["cpp_value"] = member.get("numeric_value")
        if docs:
            methods_tables = docs[0].get("tables", {}).get("Methods", [])
            if methods_tables:
                for row in methods_tables[0]:
                    mapped = {cell["key"]: cell["text"] for cell in row}
                    entry = members.setdefault(
                        mapped.get("Name"),
                        {
                            "name": mapped.get("Name"),
                            "value": None,
                            "python_value": None,
                            "cpp_value": None,
                            "doc_description": None,
                        },
                    )
                    if mapped.get("Value"):
                        entry["value"] = mapped["Value"]
                    if mapped.get("Description"):
                        entry["doc_description"] = mapped["Description"]
        enums.append(
            {
                "id": enum_id,
                "name": enum_symbol["name"] if enum_symbol else _name_from_symbol_id(enum_id),
                "namespace": enum_symbol["namespace"] if enum_symbol else _namespace_from_symbol_id(enum_id),
                "source_paths": enum_symbol["source_paths"] if enum_symbol else [],
                "members": sorted(members.values(), key=lambda item: item["name"] or ""),
                "doc": enum_symbol.get("doc") if enum_symbol else _merge_docs(docs),
            }
        )

    return enums


def _build_families(merged_symbols: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_owner: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for symbol in merged_symbols:
        if symbol.get("owner"):
            by_owner[symbol["owner"]].append(symbol)

    families = []
    for symbol in merged_symbols:
        if symbol["kind"] not in {"class", "enum"}:
            continue
        methods = {child["name"] for child in by_owner.get(symbol["id"], []) if child["kind"] in {"method", "property"}}
        if not ({"item", "count"} <= methods or "add" in methods or "createInput" in methods or "addSimple" in methods):
            continue
        families.append(
            {
                "id": symbol["id"],
                "name": symbol["name"],
                "namespace": symbol["namespace"],
                "methods": sorted(methods),
                "traits": symbol["traits"],
            }
        )
    families.sort(key=lambda item: item["id"])
    return families


def _apply_traits(merged_symbols: list[dict[str, Any]]) -> None:
    by_owner: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for symbol in merged_symbols:
        if symbol.get("owner"):
            by_owner[symbol["owner"]].append(symbol)

    for symbol in merged_symbols:
        methods = {child["name"] for child in by_owner.get(symbol["id"], []) if child["kind"] in {"method", "property", "constant"}}
        traits = {
            "collection_like": bool({"item", "count"} <= methods),
            "has_add": "add" in methods,
            "has_create_input": "createInput" in methods,
            "has_add_simple": "addSimple" in methods,
            "supports_samples": bool(symbol.get("doc", {}).get("samples")) if symbol.get("doc") else False,
            "is_enum": symbol["kind"] == "enum",
            "is_input_object": bool(symbol["name"].endswith("Input")) if symbol.get("name") else False,
            "returns_base_product": any(_normalized_type(signature.get("returns")) == "Product" for signature in symbol.get("signatures", [])),
            "is_static_constructor": symbol["kind"] == "method" and any(signature.get("static") for signature in symbol.get("signatures", [])) and (symbol["name"] == "get" or symbol["name"].startswith("create")),
            "is_cast_helper": symbol["name"] == "cast",
            "compact_candidate": symbol["kind"] in {"class", "method"} and (
                symbol["name"] in {"Design", "Component", "Sketch", "ExtrudeFeatures", "ValueInput", "Application", "Documents"}
                or {"add", "createInput", "addSimple", "get"}.__contains__(symbol["name"])
            ),
        }
        symbol["traits"] = traits


def _compare_signatures(
    conflicts: list[dict[str, str]],
    symbol_id: str,
    python_symbol: dict[str, Any],
    cpp_symbol: dict[str, Any],
) -> None:
    if _expected_cpp_property_bridge(python_symbol, cpp_symbol):
        return
    python_return = _normalized_type(python_symbol.get("return_annotation"))
    cpp_return = _normalized_type(cpp_symbol.get("return_type"))
    if python_return and cpp_return and not _equivalent_types(python_return, cpp_return):
        conflicts.append(
            {
                "symbol_id": symbol_id,
                "field": "return_type",
                "canonical": python_return,
                "value": cpp_return,
                "source": "cpp",
            }
        )


def _record_if_mismatch(
    conflicts: list[dict[str, str]],
    symbol_id: str,
    field: str,
    canonical: str | None,
    value: str | None,
    source: str,
) -> None:
    if canonical and value and canonical != value:
        conflicts.append(
            {
                "symbol_id": symbol_id,
                "field": field,
                "canonical": canonical,
                "value": value,
                "source": source,
            }
        )


def _expected_doc_property_bridge(canonical_kind: str | None, doc_kind: str | None, name: str | None) -> bool:
    return canonical_kind == "method" and doc_kind == "property" and name in {"objectType", "classType"}


def _equivalent_types(left: str, right: str) -> bool:
    return _canonical_type_name(left) == _canonical_type_name(right)


def _doc_kind(page: dict[str, Any]) -> str | None:
    page_kind = page.get("page_kind")
    if page_kind == "object":
        return "class"
    if page_kind == "property":
        return "property"
    if page_kind == "method":
        return "method"
    if page_kind == "event":
        return "event"
    if page_kind == "enum":
        return "enum"
    return page_kind


def _select_cpp_symbol(
    python_symbol: dict[str, Any] | None,
    cpp_candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not cpp_candidates:
        return None
    if python_symbol and python_symbol.get("kind") == "property":
        getter_like = [
            candidate
            for candidate in cpp_candidates
            if len(candidate.get("parameters", [])) == 0
            and _normalized_type(candidate.get("return_type")) not in {"bool", "void"}
        ]
        if getter_like:
            return getter_like[0]
    if python_symbol and python_symbol.get("kind") == "method":
        python_param_count = len(python_symbol.get("parameters", []))
        exact = [candidate for candidate in cpp_candidates if len(candidate.get("parameters", [])) == python_param_count]
        if exact:
            return exact[0]
    return cpp_candidates[0]


def _signature_candidates(
    python_symbol: dict[str, Any] | None,
    cpp_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not cpp_candidates:
        return []
    if python_symbol and python_symbol.get("kind") == "property":
        getter_like = [
            candidate
            for candidate in cpp_candidates
            if len(candidate.get("parameters", [])) == 0
            and _normalized_type(candidate.get("return_type")) not in {"bool", "void"}
        ]
        return getter_like or [cpp_candidates[0]]
    return cpp_candidates


def _expected_cpp_property_bridge(
    python_symbol: dict[str, Any] | None,
    cpp_symbol: dict[str, Any] | None,
) -> bool:
    return bool(
        python_symbol
        and cpp_symbol
        and python_symbol.get("kind") == "property"
        and cpp_symbol.get("kind") == "method"
    )


def _normalized_type(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = _strip_type_qualifiers(value)
    if not cleaned:
        return None
    generic_argument = _last_generic_argument(cleaned)
    if generic_argument is not None:
        normalized = _normalized_type(generic_argument)
        if normalized:
            return normalized
    return _canonical_type_name(_strip_type_namespace(cleaned))


def _strip_type_qualifiers(value: str) -> str:
    cleaned = value.strip()
    while True:
        updated = cleaned
        for prefix in ("const ", "volatile ", "typename "):
            if updated.startswith(prefix):
                updated = updated[len(prefix) :].strip()
        for suffix in (" const", " volatile", "&", "*"):
            if updated.endswith(suffix):
                updated = updated[: -len(suffix)].strip()
        if updated == cleaned:
            return updated
        cleaned = updated


def _last_generic_argument(value: str) -> str | None:
    for opener, closer in (("<", ">"), ("[", "]")):
        if not value.endswith(closer):
            continue
        start = _matching_generic_start(value, opener, closer)
        if start == -1:
            continue
        arguments = _split_top_level_arguments(value[start + 1 : -1])
        if arguments:
            return arguments[-1]
    return None


def _matching_generic_start(value: str, opener: str, closer: str) -> int:
    depth = 0
    for index in range(len(value) - 1, -1, -1):
        char = value[index]
        if char == closer:
            depth += 1
            continue
        if char == opener:
            depth -= 1
            if depth == 0:
                return index
    return -1


def _split_top_level_arguments(value: str) -> list[str]:
    arguments: list[str] = []
    start = 0
    angle_depth = 0
    bracket_depth = 0
    paren_depth = 0
    for index, char in enumerate(value):
        if char == "<":
            angle_depth += 1
        elif char == ">":
            angle_depth -= 1
        elif char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth -= 1
        elif char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth -= 1
        elif char == "," and angle_depth == 0 and bracket_depth == 0 and paren_depth == 0:
            arguments.append(value[start:index].strip())
            start = index + 1
    tail = value[start:].strip()
    if tail:
        arguments.append(tail)
    return arguments


def _strip_type_namespace(value: str) -> str:
    cleaned = value
    if "::" in cleaned:
        cleaned = cleaned.split("::")[-1]
    if "." in cleaned:
        cleaned = cleaned.split(".")[-1]
    return cleaned


def _canonical_type_name(value: str) -> str:
    aliases = {
        "None": "void",
        "NoneType": "void",
        "str": "string",
        "std::string": "string",
        "float": "double",
    }
    return aliases.get(value, value)


def _prefixed_source_path(prefix: str, value: str | None) -> list[str]:
    if not value:
        return []
    return [f"{prefix}/{value}"]


def _name_from_symbol_id(symbol_id: str) -> str:
    return symbol_id.rsplit(".", 1)[-1]


def _owner_from_symbol_id(symbol_id: str) -> str | None:
    parts = symbol_id.split(".")
    return ".".join(parts[:-1]) if len(parts) > 2 else None


def _namespace_from_symbol_id(symbol_id: str) -> str | None:
    parts = symbol_id.split(".")
    if len(parts) >= 2:
        return ".".join(parts[:2])
    return None


def _python_constant_value(symbol: dict[str, Any]) -> str | None:
    return symbol.get("value")
