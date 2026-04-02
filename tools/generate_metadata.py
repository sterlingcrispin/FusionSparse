from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from pprint import pformat
import re

from tools.apply_rules import apply_rules, write_rules_summary_report
from tools.build_ir import build_ir


def generate_metadata(
    repo_root: str | Path | None = None,
    *,
    build_ir_first: bool = False,
    corpus_root: str | Path | None = None,
) -> dict[str, object]:
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parent.parent
    if build_ir_first or not (root / "build" / "ir" / "symbols.json").exists():
        build_ir(repo_root=root, corpus_root=corpus_root)

    symbols = _load_json(root / "build" / "ir" / "symbols.json")
    enums = _load_json(root / "build" / "ir" / "enums.json")
    families = _load_json(root / "build" / "ir" / "families.json")
    corpus_lock = _load_json(root / "corpus" / "corpus.lock.json")

    applied = apply_rules(symbols=symbols, enums=enums, families=families, repo_root=root)
    runtime_generated_dir = root / "src" / "fusion_sparse" / "generated"
    build_generated_dir = root / "build" / "generated"
    runtime_generated_dir.mkdir(parents=True, exist_ok=True)
    build_generated_dir.mkdir(parents=True, exist_ok=True)

    timestamp = _timestamp()
    paths = {
        "symbol_index_path": build_generated_dir / "symbol_index.py",
        "enum_index_path": runtime_generated_dir / "enum_index.py",
        "compact_policy_path": runtime_generated_dir / "compact_policy.py",
        "compact_surface_path": runtime_generated_dir / "compact_surface.py",
        "compact_reference_path": build_generated_dir / "compact_reference.py",
        "wrapper_dispatch_path": runtime_generated_dir / "wrapper_dispatch.py",
        "families_path": build_generated_dir / "families.py",
        "public_api_path": runtime_generated_dir / "public_api.py",
        "release_info_path": runtime_generated_dir / "release_info.py",
        "generated_init_path": runtime_generated_dir / "__init__.py",
        "compact_reference_doc_path": root / "docs" / "compact_reference.md",
        "raw_mapping_doc_path": root / "docs" / "raw_mapping.md",
        "update_workflow_doc_path": root / "docs" / "update_workflow.md",
        "symbol_stats_report_path": root / "build" / "reports" / "symbol_stats.md",
    }

    symbol_index = _build_symbol_index(applied["symbols"])
    enum_index = _build_enum_index(applied["enums"], applied["enum_aliases"])
    compact_policy = _build_compact_policy(applied["compact_policy"], applied["families"])
    compact_surface = _build_compact_surface(compact_policy)
    compact_reference = _build_compact_reference(
        applied["compact_reference"],
        applied["exports"],
        applied["compact_exports"],
    )
    wrapper_dispatch = _build_wrapper_dispatch(applied["symbols"], applied["wrapper_dispatch"])
    family_index = _build_family_index(applied["families"])
    public_api = _build_public_api(applied["exports"], applied["compact_exports"])
    release_info = _build_release_info(corpus_lock)
    symbol_stats = _build_symbol_stats(applied, compact_reference)

    _write_compact_data_module(
        paths["symbol_index_path"],
        "Generated symbol index. Do not edit by hand.",
        [("SYMBOL_INDEX", symbol_index)],
    )
    _write_compact_data_module(
        paths["enum_index_path"],
        "Generated enum aliases and lookup helpers. Do not edit by hand.",
        [
            ("ENUM_INDEX", enum_index["index"]),
            ("ENUM_NAME_TO_MODULE", enum_index["modules"]),
            ("ENUM_ALIASES_BY_NAME", enum_index["aliases"]),
            ("ENUM_REVERSE_ALIASES_BY_NAME", enum_index["reverse_aliases"]),
        ],
        helpers=_enum_index_helpers(),
    )
    _write_compact_policy_module(paths["compact_policy_path"], compact_policy)
    _write_compact_surface_module(paths["compact_surface_path"], compact_surface)
    _write_compact_reference_module(paths["compact_reference_path"], compact_reference)
    _write_compact_data_module(
        paths["wrapper_dispatch_path"],
        "Generated wrapper dispatch metadata. Do not edit by hand.",
        [("WRAPPER_CLASS_PATHS", wrapper_dispatch["wrapper_class_paths"])],
        helpers=_wrapper_dispatch_helpers(),
    )
    _write_compact_data_module(
        paths["families_path"],
        "Generated family metadata. Do not edit by hand.",
        [("FAMILY_INDEX", family_index)],
    )
    _write_public_api_module(paths["public_api_path"], public_api)
    _write_compact_data_module(
        paths["release_info_path"],
        "Generated corpus release metadata. Do not edit by hand.",
        [("RELEASE_INFO", release_info)],
    )
    _write_python_module(
        paths["generated_init_path"],
        "Generated runtime metadata.",
        [],
    )
    _write_compact_reference_doc(paths["compact_reference_doc_path"], compact_reference)
    _write_raw_mapping_doc(paths["raw_mapping_doc_path"], compact_reference)
    _write_update_workflow_doc(paths["update_workflow_doc_path"], corpus_lock)
    _write_symbol_stats_report(paths["symbol_stats_report_path"], symbol_stats)

    rules_report_path = write_rules_summary_report(applied, root / "build" / "reports" / "rules_summary.md")

    return {
        "generated_at": timestamp,
        "symbol_count": len(symbol_index),
        "enum_count": len(enum_index["index"]),
        "family_count": len(family_index),
        "rules_report_path": str(rules_report_path),
        **{name: str(path) for name, path in paths.items()},
    }


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _build_symbol_index(symbols: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    index = {}
    for symbol in symbols:
        index[symbol["id"]] = {
            "kind": symbol["kind"],
            "name": symbol["name"],
            "owner": symbol.get("owner"),
            "namespace": symbol.get("namespace"),
            "display_name": symbol.get("display_name"),
            "traits": {key: value for key, value in symbol.get("traits", {}).items() if value},
            "signature_count": len(symbol.get("signatures", [])),
            "doc_title": symbol.get("doc", {}).get("title") if symbol.get("doc") else None,
            "introduced_in": symbol.get("doc", {}).get("introduced_in") if symbol.get("doc") else None,
        }
    return index


def _build_enum_index(
    enums: list[dict[str, object]],
    alias_rules: dict[str, dict[str, str]],
) -> dict[str, dict[str, object]]:
    index = {}
    modules = {}
    aliases = {}
    reverse_aliases = {}
    for enum in enums:
        enum_name = enum["name"]
        alias_map = alias_rules.get(enum_name, {})
        members = {member["name"]: member.get("value") for member in enum.get("members", [])}
        index[enum["id"]] = {
            "name": enum_name,
            "namespace": enum.get("namespace"),
            "members": members,
            "aliases": alias_map,
        }
        if enum.get("namespace"):
            modules[enum_name] = enum["namespace"]
        if alias_map:
            aliases[enum_name] = alias_map
            reverse_aliases[enum_name] = {member_name: alias for alias, member_name in alias_map.items()}
    return {
        "index": index,
        "modules": modules,
        "aliases": aliases,
        "reverse_aliases": reverse_aliases,
    }


def _build_wrapper_dispatch(
    symbols: list[dict[str, object]],
    wrapper_rules: dict[str, str],
) -> dict[str, object]:
    symbol_index = {}
    for symbol in symbols:
        if symbol["kind"] != "class":
            continue
        namespace = symbol.get("namespace")
        name = symbol.get("name")
        if not namespace or not name:
            continue
        symbol_index[symbol["id"]] = symbol

    wrapper_class_paths = {}
    for symbol_id, target_path in wrapper_rules.items():
        symbol = symbol_index[symbol_id]
        module_name, class_name = _split_target_path(target_path)
        namespace = symbol["namespace"]
        name = symbol["name"]
        object_type = f"{namespace.replace('.', '::')}::{name}"
        wrapper_class_paths[object_type] = (module_name, class_name)
        wrapper_class_paths[name] = (module_name, class_name)
        wrapper_class_paths[symbol_id] = (module_name, class_name)

    return {"wrapper_class_paths": wrapper_class_paths}


def _build_family_index(families: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    index = {}
    for family in families:
        index[family["id"]] = {
            "name": family["name"],
            "namespace": family["namespace"],
            "methods": family["methods"],
            "traits": family.get("traits", {}),
            "override": family.get("override"),
        }
    return index


def _build_compact_policy(
    compact_policy_rules: dict[str, object],
    families: list[dict[str, object]],
) -> dict[str, object]:
    family_by_id = {family["id"]: family for family in families}
    extrude_policy = dict(compact_policy_rules["extrude"])
    family_id = extrude_policy["family_id"]
    family = family_by_id.get(family_id)
    if family is None:
        raise RuntimeError(f"Compact extrude policy references missing family: {family_id}")

    override = family.get("override") or {}
    required_override_keys = ("compact_method", "simple_method", "builder_input", "builder_terminal")
    missing_override_keys = [key for key in required_override_keys if key not in override]
    if missing_override_keys:
        raise RuntimeError(
            f"Family override for {family_id} is missing required keys: {', '.join(sorted(missing_override_keys))}"
        )

    extrude_policy["compact_method"] = override["compact_method"]
    extrude_policy["simple_method"] = override["simple_method"]
    extrude_policy["builder_input"] = override["builder_input"]
    extrude_policy["builder_terminal"] = override["builder_terminal"]

    construction_policy = {}
    for helper_name, section in compact_policy_rules["construction"].items():
        family_id = section["family_id"]
        if family_by_id.get(family_id) is None:
            raise RuntimeError(f"Compact construction policy references missing family: {family_id}")
        construction_policy[helper_name] = dict(section)

    revolve_policy = dict(compact_policy_rules["revolve"])
    if family_by_id.get(revolve_policy["family_id"]) is None:
        raise RuntimeError(f"Compact revolve policy references missing family: {revolve_policy['family_id']}")

    hole_policy = dict(compact_policy_rules["hole"])
    if family_by_id.get(hole_policy["family_id"]) is None:
        raise RuntimeError(f"Compact hole policy references missing family: {hole_policy['family_id']}")

    fillet_policy = dict(compact_policy_rules["fillet"])
    if family_by_id.get(fillet_policy["family_id"]) is None:
        raise RuntimeError(f"Compact fillet policy references missing family: {fillet_policy['family_id']}")

    chamfer_policy = dict(compact_policy_rules["chamfer"])
    if family_by_id.get(chamfer_policy["family_id"]) is None:
        raise RuntimeError(f"Compact chamfer policy references missing family: {chamfer_policy['family_id']}")

    combine_policy = dict(compact_policy_rules["combine"])
    if family_by_id.get(combine_policy["family_id"]) is None:
        raise RuntimeError(f"Compact combine policy references missing family: {combine_policy['family_id']}")

    mirror_policy = dict(compact_policy_rules["mirror"])
    if family_by_id.get(mirror_policy["family_id"]) is None:
        raise RuntimeError(f"Compact mirror policy references missing family: {mirror_policy['family_id']}")

    circular_pattern_policy = dict(compact_policy_rules["circular_pattern"])
    if family_by_id.get(circular_pattern_policy["family_id"]) is None:
        raise RuntimeError(
            f"Compact circular pattern policy references missing family: {circular_pattern_policy['family_id']}"
        )

    rectangular_pattern_policy = dict(compact_policy_rules["rectangular_pattern"])
    if family_by_id.get(rectangular_pattern_policy["family_id"]) is None:
        raise RuntimeError(
            f"Compact rectangular pattern policy references missing family: {rectangular_pattern_policy['family_id']}"
        )

    sweep_policy = _optional_family_policy(compact_policy_rules["sweep"], family_by_id)
    loft_policy = _optional_family_policy(compact_policy_rules["loft"], family_by_id)
    patch_policy = _optional_family_policy(compact_policy_rules["patch"], family_by_id)
    shell_policy = _optional_family_policy(compact_policy_rules["shell"], family_by_id)
    draft_policy = _optional_family_policy(compact_policy_rules["draft"], family_by_id)
    move_policy = _optional_family_policy(compact_policy_rules["move"], family_by_id)
    offset_policy = _optional_family_policy(compact_policy_rules["offset"], family_by_id)
    replace_face_policy = _optional_family_policy(compact_policy_rules["replace_face"], family_by_id)
    scale_policy = _optional_family_policy(compact_policy_rules["scale"], family_by_id)
    split_body_policy = _optional_family_policy(compact_policy_rules["split_body"], family_by_id)
    thread_policy = _optional_family_policy(compact_policy_rules["thread"], family_by_id)
    trim_policy = _optional_family_policy(compact_policy_rules["trim"], family_by_id)
    text_policy = _optional_family_policy(compact_policy_rules["text"], family_by_id)

    units = compact_policy_rules["sketch"]["length_units_cm"]
    unit_names = "|".join(sorted((re.escape(name) for name in units), key=len, reverse=True))
    sketch_length_pattern = (
        r"^\s*(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(?P<unit>"
        + unit_names
        + r")\s*$"
    )

    return {
        "design_workspace": compact_policy_rules["design_workspace"],
        "planes": compact_policy_rules["planes"],
        "sketch_targets": compact_policy_rules["sketch"].get("targets", {}),
        "sketch_collections": compact_policy_rules["sketch"]["collections"],
        "sketch_methods": compact_policy_rules["sketch"]["methods"],
        "sketch_coercers": compact_policy_rules["sketch"]["coercers"],
        "sketch_length_units_cm": units,
        "sketch_length_pattern": sketch_length_pattern,
        "text_policy": text_policy,
        "extrude_policy": extrude_policy,
        "construction_policy": construction_policy,
        "revolve_policy": revolve_policy,
        "hole_policy": hole_policy,
        "fillet_policy": fillet_policy,
        "chamfer_policy": chamfer_policy,
        "combine_policy": combine_policy,
        "mirror_policy": mirror_policy,
        "circular_pattern_policy": circular_pattern_policy,
        "rectangular_pattern_policy": rectangular_pattern_policy,
        "sweep_policy": sweep_policy,
        "loft_policy": loft_policy,
        "patch_policy": patch_policy,
        "shell_policy": shell_policy,
        "draft_policy": draft_policy,
        "move_policy": move_policy,
        "offset_policy": offset_policy,
        "replace_face_policy": replace_face_policy,
        "scale_policy": scale_policy,
        "split_body_policy": split_body_policy,
        "thread_policy": thread_policy,
        "trim_policy": trim_policy,
    }


def _optional_family_policy(section: dict[str, object], family_by_id: dict[str, dict[str, object]]) -> dict[str, object]:
    policy = dict(section)
    family_id = policy.get("family_id")
    if family_id is None:
        return policy
    if family_by_id.get(family_id) is None:
        raise RuntimeError(f"Compact policy references missing family: {family_id}")
    return policy


def _build_public_api(aliases: dict[str, str], compact_exports: list[str]) -> dict[str, object]:
    exports = []
    for public_name in compact_exports:
        target_path = aliases[public_name]
        module_name, attr_name = _split_target_path(target_path)
        exports.append(
            {
                "public_name": public_name,
                "module_name": module_name,
                "attr_name": attr_name,
            }
        )
    return {"exports": exports}


def _build_release_info(corpus_lock: dict[str, object]) -> dict[str, object]:
    return {
        "corpus_generated_at": corpus_lock.get("generated_at"),
        "git_commit": corpus_lock.get("git_commit"),
        "file_counts": corpus_lock.get("file_counts"),
    }


def _build_compact_surface(compact_policy: dict[str, object]) -> dict[str, object]:
    sketch_targets = compact_policy["sketch_targets"]
    sketch_collections = compact_policy["sketch_collections"]
    sketch_methods = compact_policy["sketch_methods"]
    sketch_coercers = compact_policy["sketch_coercers"]
    methods = {
        "ComponentRef.sketch": {
            "kind": "call",
            "target_attrs": ["sketches"],
            "method": "add",
            "coercers": ["plane"],
        },
        "SketchRef.profiles": {
            "kind": "collection_list",
            "attr_path": ["profiles"],
        },
        "SketchRef.profile": {
            "kind": "collection_item",
            "attr_path": ["profiles"],
            "default_index": 0,
        },
    }
    for method_id, raw_method in sketch_methods.items():
        collection = sketch_collections.get(method_id)
        coercers = sketch_coercers.get(method_id)
        if collection is None:
            raise RuntimeError(f"Missing sketch collection rule for compact sketch method: {method_id}")
        if coercers is None:
            raise RuntimeError(f"Missing sketch coercer rule for compact sketch method: {method_id}")
        target_attrs = sketch_targets.get(method_id)
        if target_attrs is None:
            target_attrs = ["sketchCurves", collection]
        methods[f"SketchRef.{method_id}"] = {
            "kind": "call",
            "target_attrs": target_attrs,
            "method": raw_method,
            "coercers": coercers,
        }
    return {
        "properties": {
            "DesignRef.root": {
                "kind": "property",
                "attr_path": ["rootComponent"],
            }
        },
        "methods": methods,
    }


def _build_symbol_stats(
    applied: dict[str, object],
    compact_reference: dict[str, object],
) -> dict[str, object]:
    symbols = applied["symbols"]
    enums = applied["enums"]
    families = applied["families"]
    kind_counts: dict[str, int] = {}
    namespace_counts: dict[str, int] = {}
    for symbol in symbols:
        kind = symbol["kind"]
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        namespace = symbol.get("namespace")
        if namespace:
            namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1

    top_namespaces = sorted(namespace_counts.items(), key=lambda item: (-item[1], item[0]))[:10]
    return {
        "symbol_total": len(symbols),
        "enum_total": len(enums),
        "family_total": len(families),
        "kind_counts": dict(sorted(kind_counts.items())),
        "top_namespaces": top_namespaces,
        "public_export_total": len(compact_reference["exports"]),
        "compact_method_total": len(compact_reference["methods"]),
        "wrapper_dispatch_total": len(applied["wrapper_dispatch"]),
    }


def _build_compact_reference(
    compact_reference_rules: dict[str, dict[str, dict[str, object]]],
    aliases: dict[str, str],
    compact_exports: list[str],
) -> dict[str, object]:
    export_order = list(compact_exports)
    exports = []
    for public_name in export_order:
        reference = compact_reference_rules["exports"].get(public_name)
        if reference is None:
            raise RuntimeError(f"Missing compact reference metadata for public export: {public_name}")
        exports.append(
            {
                "id": public_name,
                "kind": "export",
                "public_name": public_name,
                "implementation": _qualify_target_path(aliases[public_name]),
                "raw_mapping": reference["raw_mapping"],
                "arguments": reference["arguments"],
                "example": reference["example"].strip(),
                "escape_hatch": reference["escape_hatch"].strip(),
            }
        )

    methods = []
    for method_id, reference in compact_reference_rules["methods"].items():
        methods.append(
            {
                "id": method_id,
                "kind": "method",
                "public_name": method_id,
                "implementation": None,
                "raw_mapping": reference["raw_mapping"],
                "arguments": reference["arguments"],
                "example": reference["example"].strip(),
                "escape_hatch": reference["escape_hatch"].strip(),
            }
        )

    index = {entry["id"]: entry for entry in exports + methods}
    return {
        "exports": exports,
        "methods": methods,
        "index": index,
    }


def _write_python_module(
    path: Path,
    docstring: str,
    assignments: list[tuple[str, object]],
    *,
    helpers: str | None = None,
) -> None:
    lines = [
        '"""' + docstring + '"""',
        "",
        "from __future__ import annotations",
        "",
    ]
    for name, value in assignments:
        rendered = pformat(value, width=100, sort_dicts=True)
        lines.append(f"{name} = {rendered}")
        lines.append("")
    if helpers:
        lines.append(helpers.rstrip())
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_compact_data_module(
    path: Path,
    docstring: str,
    assignments: list[tuple[str, object]],
    *,
    helpers: str | None = None,
) -> None:
    lines = [
        '"""' + docstring + '"""',
        "",
        "from __future__ import annotations",
        "",
        "import json as _json",
        "",
    ]
    for name, value in assignments:
        payload = json.dumps(_json_ready(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        lines.append(f"{name} = _json.loads({payload!r})")
        lines.append("")
    if helpers:
        lines.append(helpers.rstrip())
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_public_api_module(path: Path, public_api: dict[str, object]) -> None:
    exports = list(public_api["exports"])
    grouped_imports: dict[str, list[tuple[str, str]]] = {}
    for export in exports:
        grouped_imports.setdefault(export["module_name"], []).append((export["attr_name"], export["public_name"]))

    lines = [
        '"""Generated package public API. Do not edit by hand."""',
        "",
        "from __future__ import annotations",
        "",
    ]
    for module_name, members in grouped_imports.items():
        rendered_members = []
        for attr_name, public_name in members:
            if attr_name == public_name:
                rendered_members.append(attr_name)
            else:
                rendered_members.append(f"{attr_name} as {public_name}")
        lines.append(f"from {module_name} import {', '.join(rendered_members)}")
    lines.extend(
        [
            "",
            f"__all__ = {pformat([export['public_name'] for export in exports], width=100)}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_compact_policy_module(path: Path, compact_policy: dict[str, object]) -> None:
    _write_compact_data_module(
        path,
        "Generated compact behavior policy. Do not edit by hand.",
        [
            ("DESIGN_WORKSPACE_POLICY", compact_policy["design_workspace"]),
            ("PLANE_ALIASES", compact_policy["planes"]),
            ("SKETCH_TARGETS", compact_policy["sketch_targets"]),
            ("SKETCH_COLLECTIONS", compact_policy["sketch_collections"]),
            ("SKETCH_METHODS", compact_policy["sketch_methods"]),
            ("SKETCH_COERCERS", compact_policy["sketch_coercers"]),
            ("SKETCH_LENGTH_UNITS_CM", compact_policy["sketch_length_units_cm"]),
            ("SKETCH_LENGTH_PATTERN", compact_policy["sketch_length_pattern"]),
            ("TEXT_POLICY", compact_policy["text_policy"]),
            ("EXTRUDE_POLICY", compact_policy["extrude_policy"]),
            ("CONSTRUCTION_POLICY", compact_policy["construction_policy"]),
            ("REVOLVE_POLICY", compact_policy["revolve_policy"]),
            ("HOLE_POLICY", compact_policy["hole_policy"]),
            ("FILLET_POLICY", compact_policy["fillet_policy"]),
            ("CHAMFER_POLICY", compact_policy["chamfer_policy"]),
            ("COMBINE_POLICY", compact_policy["combine_policy"]),
            ("MIRROR_POLICY", compact_policy["mirror_policy"]),
            ("CIRCULAR_PATTERN_POLICY", compact_policy["circular_pattern_policy"]),
            ("RECTANGULAR_PATTERN_POLICY", compact_policy["rectangular_pattern_policy"]),
            ("SWEEP_POLICY", compact_policy["sweep_policy"]),
            ("LOFT_POLICY", compact_policy["loft_policy"]),
            ("PATCH_POLICY", compact_policy["patch_policy"]),
            ("SHELL_POLICY", compact_policy["shell_policy"]),
            ("DRAFT_POLICY", compact_policy["draft_policy"]),
            ("MOVE_POLICY", compact_policy["move_policy"]),
            ("OFFSET_POLICY", compact_policy["offset_policy"]),
            ("REPLACE_FACE_POLICY", compact_policy["replace_face_policy"]),
            ("SCALE_POLICY", compact_policy["scale_policy"]),
            ("SPLIT_BODY_POLICY", compact_policy["split_body_policy"]),
            ("THREAD_POLICY", compact_policy["thread_policy"]),
            ("TRIM_POLICY", compact_policy["trim_policy"]),
        ],
    )


def _write_compact_surface_module(path: Path, compact_surface: dict[str, object]) -> None:
    _write_compact_data_module(
        path,
        "Generated compact surface metadata. Do not edit by hand.",
        [
            ("COMPACT_PROPERTIES", compact_surface["properties"]),
            ("COMPACT_METHODS", compact_surface["methods"]),
        ],
    )


def _write_compact_reference_module(path: Path, compact_reference: dict[str, object]) -> None:
    _write_compact_data_module(
        path,
        "Generated compact reference metadata. Do not edit by hand.",
        [
            ("COMPACT_REFERENCE_EXPORTS", compact_reference["exports"]),
            ("COMPACT_REFERENCE_METHODS", compact_reference["methods"]),
            ("COMPACT_REFERENCE_INDEX", compact_reference["index"]),
        ],
    )


def _write_compact_reference_doc(path: Path, compact_reference: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Compact Reference",
        "",
        "Generated from FusionSparse metadata and compact reference rules.",
        "",
    ]
    for section_title, entries in (("Public Helpers", compact_reference["exports"]), ("Compact Methods", compact_reference["methods"])):
        lines.extend([f"## {section_title}", ""])
        for entry in entries:
            lines.append(f"### `{entry['public_name']}`")
            lines.append("")
            lines.append(f"- Raw Autodesk mapping: `{entry['raw_mapping']}`")
            implementation = entry.get("implementation")
            if implementation:
                lines.append(f"- Implementation: `{implementation}`")
            arguments = entry["arguments"] or ["none"]
            rendered_args = ", ".join(f"`{arg}`" for arg in arguments)
            lines.append(f"- Arguments: {rendered_args}")
            lines.append("- Example:")
            lines.append("")
            lines.append("```python")
            lines.append(entry["example"])
            lines.append("```")
            lines.append("")
            lines.append(f"- Escape hatch: {entry['escape_hatch']}")
            lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_raw_mapping_doc(path: Path, compact_reference: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Raw Mapping",
        "",
        "Generated compact-to-Autodesk mapping table.",
        "",
        "| Compact Surface | Raw Autodesk Mapping |",
        "| --- | --- |",
    ]
    for entry in compact_reference["exports"] + compact_reference["methods"]:
        lines.append(f"| `{entry['public_name']}` | `{entry['raw_mapping']}` |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_update_workflow_doc(path: Path, corpus_lock: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    commit = corpus_lock.get("git_commit") or "unknown"
    lines = [
        "# Update Workflow",
        "",
        "Generated workflow for refreshing FusionSparse from the Autodesk corpus.",
        "",
        "## Current Corpus Snapshot",
        "",
        f"- Pinned Autodesk commit: `{commit}`",
        "",
        "## Steps",
        "",
        "1. Run `python -m tools.cli snapshot-ir` before refreshing the Autodesk corpus if you want to preserve the previous IR state.",
        "2. Update the Autodesk `corpus/FusionAPIReference` submodule to the target upstream commit.",
        "3. Run `python -m tools.cli build-ir` with the project interpreter.",
        "4. Run `python -m tools.cli diff-ir` to compare the new IR against the latest snapshot.",
        "5. Review `build/reports/corpus_summary.md`, `build/reports/merge_conflicts.md`, `build/reports/rules_summary.md`, and `build/reports/ir_diff.md`.",
        "6. Run `python -m tools.cli generate` to regenerate runtime metadata and generated docs.",
        "7. Review generated diffs under `src/fusion_sparse/generated/` and `docs/`.",
        "8. Run `python -m tools.cli sync-fusion` to stage the smoke script and the workbench add-in into Fusion's API folders.",
        "9. Run the unit test suite.",
        "10. Start `fusion/scripts/FusionSparseSmoke/` or the `FusionSparseWorkbench` add-in inside Fusion and verify the smoke summary.",
        "11. If the local Fusion MCP add-in is available, run the same smoke flows through `execute_api_script` and capture a screenshot with `get_screenshot`.",
        "12. Run `python -m tools.cli run-sample-pairs` to compare normalized Autodesk sample scripts against FusionSparse translations and capture matched screenshots.",
        "13. Review `build/reports/sample_pairs/sample_pairs_report.md` plus the paired screenshots under `build/reports/sample_pairs/`. The expected state is a growing set of exact signature matches with per-pair size reductions.",
        "14. Run `python -m tools.cli measure-sparsity` to regenerate the compact-vs-baseline benchmark report.",
        "",
        "## Outputs To Review",
        "",
        "- `build/ir/symbols.json`",
        "- `build/ir/enums.json`",
        "- `build/ir/families.json`",
        "- `build/reports/merge_conflicts.md`",
        "- `build/reports/rules_summary.md`",
        "- `build/reports/symbol_stats.md`",
        "- `build/reports/sparsity_report.md`",
        "- `build/reports/ir_diff.md`",
        "- `docs/compact_reference.md`",
        "- `docs/raw_mapping.md`",
        "- `fusion/scripts/FusionSparseSmoke/`",
        "- `fusion/addins/FusionSparseWorkbench/`",
        "- `build/reports/fusion_mcp_pre.png`",
        "- `build/reports/fusion_mcp_post.png`",
        "- `tests/integration/sample_pairs/`",
        "- `build/reports/sample_pairs/sample_pairs_report.md`",
        "",
        "## Command Reference",
        "",
        "```bash",
        "python -m tools.cli build-ir",
        "python -m tools.cli snapshot-ir",
        "python -m tools.cli diff-ir",
        "python -m tools.cli generate",
        "python -m tools.cli sync-fusion",
        "python -m tools.cli run-sample-pairs",
        "python -m tools.cli measure-sparsity",
        "python -m unittest discover -s tests/unit -p 'test_*.py'",
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_symbol_stats_report(path: Path, symbol_stats: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Symbol Stats",
        "",
        "Generated summary of the current canonical IR and compact surface.",
        "",
        "## Totals",
        "",
        f"- Symbols: `{symbol_stats['symbol_total']}`",
        f"- Enums: `{symbol_stats['enum_total']}`",
        f"- Families: `{symbol_stats['family_total']}`",
        f"- Public compact exports: `{symbol_stats['public_export_total']}`",
        f"- Compact methods documented: `{symbol_stats['compact_method_total']}`",
        f"- Wrapper dispatch rules: `{symbol_stats['wrapper_dispatch_total']}`",
        "",
        "## Symbol Kinds",
        "",
        "| Kind | Count |",
        "| --- | ---: |",
    ]
    for kind, count in symbol_stats["kind_counts"].items():
        lines.append(f"| `{kind}` | `{count}` |")
    lines.extend(
        [
            "",
            "## Top Namespaces",
            "",
            "| Namespace | Symbols |",
            "| --- | ---: |",
        ]
    )
    for namespace, count in symbol_stats["top_namespaces"]:
        lines.append(f"| `{namespace}` | `{count}` |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _split_target_path(target_path: str) -> tuple[str, str]:
    qualified = target_path if target_path.startswith("fusion_sparse.") else f"fusion_sparse.{target_path}"
    module_name, attr_name = qualified.rsplit(".", 1)
    return module_name, attr_name


def _qualify_target_path(target_path: str) -> str:
    qualified = target_path if target_path.startswith("fusion_sparse.") else f"fusion_sparse.{target_path}"
    return qualified


def _json_ready(value):
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _enum_index_helpers() -> str:
    return """
def alias_to_member(enum_name: str, alias: str) -> str:
    return ENUM_ALIASES_BY_NAME[enum_name][alias]


def member_to_alias(enum_name: str, member_name: str) -> str:
    return ENUM_REVERSE_ALIASES_BY_NAME[enum_name][member_name]
"""


def _wrapper_dispatch_helpers() -> str:
    return """
def resolve_wrapper_class(raw_obj):
    from importlib import import_module

    from fusion_sparse.runtime._adsk import class_type_name, object_type_name
    from fusion_sparse.runtime.errors import GenerationMismatchError
    from fusion_sparse.runtime.refs import Ref

    for key in filter(None, (object_type_name(raw_obj), class_type_name(raw_obj), type(raw_obj).__name__)):
        path = WRAPPER_CLASS_PATHS.get(key)
        if not path:
            continue
        module_name, class_name = path
        try:
            module = import_module(module_name)
        except ImportError as exc:
            raise GenerationMismatchError(f"Configured wrapper module could not be imported: {module_name}") from exc
        try:
            wrapper_cls = getattr(module, class_name)
        except AttributeError as exc:
            raise GenerationMismatchError(
                f"Configured wrapper class could not be resolved: {module_name}.{class_name}"
            ) from exc
        if not isinstance(wrapper_cls, type) or not issubclass(wrapper_cls, Ref):
            raise GenerationMismatchError(f"Configured wrapper is not a Ref subclass: {module_name}.{class_name}")
        return wrapper_cls
    return Ref
"""


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
