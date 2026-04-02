from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import yaml


class RulesError(RuntimeError):
    """Raised when rule files are missing or malformed."""


RULE_SPECS = {
    "aliases": {
        "path": Path("rules/aliases.yaml"),
        "defaults": {"exports": {}},
    },
    "compact_exports": {
        "path": Path("rules/compact_exports.yaml"),
        "defaults": {"exports": []},
    },
    "compact_policy": {
        "path": Path("rules/compact_policy.yaml"),
        "defaults": {
            "design_workspace": {"scope_namespaces": [], "waves": {}, "adjacent": []},
            "planes": {},
            "sketch": {"targets": {}, "collections": {}, "methods": {}, "coercers": {}, "length_units_cm": {}},
            "text": {
                "family_id": None,
                "collection_attr": None,
                "builder_input": None,
                "builder_terminal": None,
                "input_methods": {},
                "input_attrs": {},
                "horizontal_alignments": {},
                "vertical_alignments": {},
            },
            "extrude": {"family_id": None, "extent_types": {}, "input_attrs": {}, "input_methods": {}},
            "construction": {
                "plane": {"family_id": None, "builder_input": None, "builder_terminal": None, "methods": {}},
                "axis": {"family_id": None, "builder_input": None, "builder_terminal": None, "methods": {}},
                "point": {"family_id": None, "builder_input": None, "builder_terminal": None, "methods": {}},
            },
            "revolve": {"family_id": None, "builder_input": None, "builder_terminal": None, "input_methods": {}},
            "hole": {
                "family_id": None,
                "builder_terminal": None,
                "create_methods": {},
                "input_methods": {},
                "edge_positions": {},
            },
            "fillet": {"family_id": None, "builder_input": None, "builder_terminal": None, "input_attrs": {}, "input_methods": {}},
            "chamfer": {"family_id": None, "builder_input": None, "builder_terminal": None, "input_attrs": {}, "input_methods": {}},
            "combine": {"family_id": None, "builder_input": None, "builder_terminal": None, "input_attrs": {}},
            "mirror": {"family_id": None, "builder_input": None, "builder_terminal": None},
            "circular_pattern": {"family_id": None, "builder_input": None, "builder_terminal": None, "input_attrs": {}},
            "rectangular_pattern": {
                "family_id": None,
                "builder_input": None,
                "builder_terminal": None,
                "input_methods": {},
                "input_attrs": {},
                "distance_types": {},
            },
            "sweep": {"family_id": None, "builder_input": None, "builder_terminal": None, "input_attrs": {}},
            "loft": {
                "family_id": None,
                "builder_input": None,
                "builder_terminal": None,
                "input_attrs": {},
                "input_methods": {},
            },
            "patch": {"family_id": None, "builder_input": None, "builder_terminal": None},
            "shell": {"family_id": None, "builder_input": None, "builder_terminal": None, "input_attrs": {}},
            "draft": {
                "family_id": None,
                "builder_input": None,
                "builder_terminal": None,
                "input_attrs": {},
                "input_methods": {},
            },
            "move": {"family_id": None, "builder_input": None, "builder_terminal": None, "input_methods": {}},
            "offset": {"family_id": None, "builder_input": None, "builder_terminal": None},
            "replace_face": {"family_id": None, "builder_input": None, "builder_terminal": None},
            "scale": {"family_id": None, "builder_input": None, "builder_terminal": None, "input_methods": {}},
            "split_body": {"family_id": None, "builder_input": None, "builder_terminal": None},
            "thread": {"family_id": None, "builder_input": None, "builder_terminal": None, "input_attrs": {}},
            "trim": {"family_id": None, "builder_input": None, "builder_terminal": None, "input_attrs": {}, "input_methods": {}},
        },
    },
    "compact_reference": {
        "path": Path("rules/compact_reference.yaml"),
        "defaults": {"exports": {}, "methods": {}},
    },
    "doc_overrides": {
        "path": Path("rules/doc_overrides.yaml"),
        "defaults": {"overrides": {}},
    },
    "enum_aliases": {
        "path": Path("rules/enum_aliases.yaml"),
        "defaults": {"aliases": {}},
    },
    "exclusions": {
        "path": Path("rules/exclusions.yaml"),
        "defaults": {"symbols": [], "pages": []},
    },
    "family_overrides": {
        "path": Path("rules/family_overrides.yaml"),
        "defaults": {"families": {}},
    },
    "wrapper_dispatch": {
        "path": Path("rules/wrapper_dispatch.yaml"),
        "defaults": {"wrappers": {}},
    },
}


def load_rules(repo_root: str | Path | None = None) -> dict[str, object]:
    root = _repo_root(repo_root)
    loaded = {}
    for rule_name, spec in RULE_SPECS.items():
        file_path = root / spec["path"]
        if not file_path.exists():
            loaded[rule_name] = deepcopy(spec["defaults"])
            continue
        parsed = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
        if not isinstance(parsed, dict):
            raise RulesError(f"{file_path} must contain a top-level mapping.")
        normalized = deepcopy(spec["defaults"])
        normalized.update(parsed)
        loaded[rule_name] = normalized

    _validate_rules(loaded)
    return loaded


def apply_rules(
    *,
    symbols: list[dict[str, object]],
    enums: list[dict[str, object]],
    families: list[dict[str, object]],
    repo_root: str | Path | None = None,
) -> dict[str, object]:
    rules = load_rules(repo_root)
    exclusions = rules["exclusions"]
    excluded_symbol_ids = set(exclusions["symbols"])
    excluded_page_ids = set(exclusions["pages"])
    doc_overrides = rules["doc_overrides"]["overrides"]
    family_overrides = rules["family_overrides"]["families"]
    enum_aliases = rules["enum_aliases"]["aliases"]
    wrapper_rules = rules["wrapper_dispatch"]["wrappers"]
    compact_policy = deepcopy(rules["compact_policy"])
    compact_reference = deepcopy(rules["compact_reference"])

    filtered_symbols = []
    for symbol in symbols:
        if symbol["id"] in excluded_symbol_ids:
            continue
        symbol_copy = deepcopy(symbol)
        if symbol_copy.get("doc") and symbol_copy["id"] in doc_overrides:
            symbol_copy["doc"].update(doc_overrides[symbol_copy["id"]])
        if symbol_copy.get("lineage", {}).get("docs"):
            docs = [
                page
                for page in symbol_copy["lineage"]["docs"]
                if Path(str(page)).stem not in excluded_page_ids
            ]
            symbol_copy["lineage"]["docs"] = docs
        filtered_symbols.append(symbol_copy)

    filtered_enums = []
    for enum in enums:
        if enum["id"] in excluded_symbol_ids:
            continue
        enum_copy = deepcopy(enum)
        alias_map = enum_aliases.get(enum_copy["name"], {})
        if alias_map:
            enum_copy["aliases"] = alias_map
        if enum_copy.get("doc") and enum_copy["id"] in doc_overrides:
            enum_copy["doc"].update(doc_overrides[enum_copy["id"]])
        filtered_enums.append(enum_copy)

    filtered_families = []
    for family in families:
        if family["id"] in excluded_symbol_ids:
            continue
        family_copy = deepcopy(family)
        override = family_overrides.get(family_copy["name"]) or family_overrides.get(family_copy["id"])
        if override:
            family_copy["override"] = override
        filtered_families.append(family_copy)

    class_symbol_ids = {symbol["id"] for symbol in filtered_symbols if symbol.get("kind") == "class"}
    for symbol_id in wrapper_rules:
        if symbol_id not in class_symbol_ids:
            raise RulesError(f"wrapper_dispatch.wrappers references unknown class symbol: {symbol_id}")

    family_ids = {family["id"] for family in filtered_families}
    for section_name in (
        "text",
        "extrude",
        "revolve",
        "hole",
        "fillet",
        "chamfer",
        "combine",
        "mirror",
        "circular_pattern",
        "rectangular_pattern",
        "sweep",
        "loft",
        "patch",
        "shell",
        "draft",
        "move",
        "offset",
        "replace_face",
        "scale",
        "split_body",
        "thread",
        "trim",
    ):
        family_id = compact_policy[section_name]["family_id"]
        if family_id is not None and family_id not in family_ids:
            raise RulesError(f"compact_policy.{section_name}.family_id references unknown family: {family_id}")
    for section_name in ("plane", "axis", "point"):
        family_id = compact_policy["construction"][section_name]["family_id"]
        if family_id is not None and family_id not in family_ids:
            raise RulesError(f"compact_policy.construction.{section_name}.family_id references unknown family: {family_id}")
    for export_name in compact_reference["exports"]:
        if export_name not in rules["compact_exports"]["exports"]:
            raise RulesError(f"compact_reference.exports references unknown public export: {export_name}")

    return {
        "rules": rules,
        "symbols": filtered_symbols,
        "enums": filtered_enums,
        "families": filtered_families,
        "exports": rules["aliases"]["exports"],
        "compact_exports": rules["compact_exports"]["exports"],
        "compact_policy": compact_policy,
        "compact_reference": compact_reference,
        "enum_aliases": enum_aliases,
        "wrapper_dispatch": wrapper_rules,
    }


def write_rules_summary_report(applied: dict[str, object], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    rules = applied["rules"]
    lines = [
        "# Rules Summary",
        "",
        f"- Export aliases: `{len(applied['exports'])}`",
        f"- Compact exports: `{len(applied['compact_exports'])}`",
        f"- Plane aliases: `{len(applied['compact_policy']['planes'])}`",
        f"- Sketch policy methods: `{len(applied['compact_policy']['sketch']['methods'])}`",
        f"- Sketch target overrides: `{len(applied['compact_policy']['sketch'].get('targets', {}))}`",
        f"- Sketch text modes: `{len(applied['compact_policy']['text']['input_methods'])}`",
        f"- Design workspace waves: `{len(applied['compact_policy']['design_workspace']['waves'])}`",
        f"- Construction helpers: `{len(applied['compact_policy']['construction'])}`",
        f"- Compact reference exports: `{len(applied['compact_reference']['exports'])}`",
        f"- Compact reference methods: `{len(applied['compact_reference']['methods'])}`",
        f"- Enum alias groups: `{len(applied['enum_aliases'])}`",
        f"- Wrapper dispatch entries: `{len(applied['wrapper_dispatch'])}`",
        f"- Excluded symbols: `{len(rules['exclusions']['symbols'])}`",
        f"- Excluded pages: `{len(rules['exclusions']['pages'])}`",
        f"- Family overrides: `{len(rules['family_overrides']['families'])}`",
        "",
        "## Export aliases",
        "",
    ]
    for alias, target in sorted(applied["exports"].items()):
        lines.append(f"- `{alias}` -> `{target}`")

    lines.extend(["", "## Compact policy", ""])
    for alias, attr_name in sorted(applied["compact_policy"]["planes"].items()):
        lines.append(f"- plane `{alias}` -> `{attr_name}`")
    for wave_name, families in sorted(applied["compact_policy"]["design_workspace"]["waves"].items()):
        lines.append(f"- {wave_name}: `{', '.join(families)}`")
    for helper_name, section in sorted(applied["compact_policy"]["construction"].items()):
        lines.append(f"- construction helper `{helper_name}` -> `{section['family_id']}`")

    if applied["compact_reference"]["exports"] or applied["compact_reference"]["methods"]:
        lines.extend(["", "## Compact reference", ""])
        for section_name in ("exports", "methods"):
            for entry_name, entry in applied["compact_reference"][section_name].items():
                lines.append(f"- `{entry_name}` -> `{entry['raw_mapping']}`")

    if applied["enum_aliases"]:
        lines.extend(["", "## Enum aliases", ""])
        for enum_name, aliases in sorted(applied["enum_aliases"].items()):
            lines.append(f"- `{enum_name}`: `{json.dumps(aliases, sort_keys=True)}`")

    if applied["wrapper_dispatch"]:
        lines.extend(["", "## Wrapper dispatch", ""])
        for symbol_id, target in sorted(applied["wrapper_dispatch"].items()):
            lines.append(f"- `{symbol_id}` -> `{target}`")

    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def _repo_root(repo_root: str | Path | None) -> Path:
    return Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parent.parent


def _validate_rules(rules: dict[str, object]) -> None:
    _ensure_mapping(rules["aliases"], "aliases")
    _ensure_mapping(rules["aliases"]["exports"], "aliases.exports")
    _ensure_list_of_strings(rules["compact_exports"]["exports"], "compact_exports.exports")
    _ensure_mapping(rules["compact_policy"]["design_workspace"], "compact_policy.design_workspace")
    _ensure_list_of_strings(
        rules["compact_policy"]["design_workspace"]["scope_namespaces"],
        "compact_policy.design_workspace.scope_namespaces",
    )
    _ensure_mapping(rules["compact_policy"]["design_workspace"]["waves"], "compact_policy.design_workspace.waves")
    _ensure_list_of_strings(rules["compact_policy"]["design_workspace"]["adjacent"], "compact_policy.design_workspace.adjacent")
    for wave_name, families in rules["compact_policy"]["design_workspace"]["waves"].items():
        if not isinstance(wave_name, str):
            raise RulesError("compact_policy.design_workspace.waves keys must be strings.")
        _ensure_list_of_strings(families, f"compact_policy.design_workspace.waves.{wave_name}")
    _ensure_mapping(rules["compact_policy"]["planes"], "compact_policy.planes")
    _ensure_mapping(rules["compact_policy"]["sketch"], "compact_policy.sketch")
    _ensure_mapping(rules["compact_policy"]["sketch"]["targets"], "compact_policy.sketch.targets")
    _ensure_mapping(rules["compact_policy"]["sketch"]["collections"], "compact_policy.sketch.collections")
    _ensure_mapping(rules["compact_policy"]["sketch"]["methods"], "compact_policy.sketch.methods")
    _ensure_mapping(rules["compact_policy"]["sketch"]["coercers"], "compact_policy.sketch.coercers")
    _ensure_mapping(rules["compact_policy"]["sketch"]["length_units_cm"], "compact_policy.sketch.length_units_cm")
    _ensure_mapping(rules["compact_policy"]["text"], "compact_policy.text")
    _ensure_mapping(rules["compact_policy"]["text"]["input_methods"], "compact_policy.text.input_methods")
    _ensure_mapping(rules["compact_policy"]["text"]["input_attrs"], "compact_policy.text.input_attrs")
    _ensure_mapping(rules["compact_policy"]["text"]["horizontal_alignments"], "compact_policy.text.horizontal_alignments")
    _ensure_mapping(rules["compact_policy"]["text"]["vertical_alignments"], "compact_policy.text.vertical_alignments")
    _ensure_mapping(rules["compact_policy"]["extrude"], "compact_policy.extrude")
    _ensure_mapping(rules["compact_policy"]["extrude"]["extent_types"], "compact_policy.extrude.extent_types")
    _ensure_mapping(rules["compact_policy"]["extrude"]["input_attrs"], "compact_policy.extrude.input_attrs")
    _ensure_mapping(rules["compact_policy"]["extrude"]["input_methods"], "compact_policy.extrude.input_methods")
    _ensure_mapping(rules["compact_policy"]["construction"], "compact_policy.construction")
    for helper_name in ("plane", "axis", "point"):
        _ensure_mapping(rules["compact_policy"]["construction"][helper_name], f"compact_policy.construction.{helper_name}")
        _ensure_mapping(
            rules["compact_policy"]["construction"][helper_name]["methods"],
            f"compact_policy.construction.{helper_name}.methods",
        )
    _ensure_mapping(rules["compact_policy"]["revolve"], "compact_policy.revolve")
    _ensure_mapping(rules["compact_policy"]["revolve"]["input_methods"], "compact_policy.revolve.input_methods")
    _ensure_mapping(rules["compact_policy"]["hole"], "compact_policy.hole")
    _ensure_mapping(rules["compact_policy"]["hole"]["create_methods"], "compact_policy.hole.create_methods")
    _ensure_mapping(rules["compact_policy"]["hole"]["input_methods"], "compact_policy.hole.input_methods")
    _ensure_mapping(rules["compact_policy"]["hole"]["edge_positions"], "compact_policy.hole.edge_positions")
    _ensure_mapping(rules["compact_policy"]["fillet"], "compact_policy.fillet")
    _ensure_mapping(rules["compact_policy"]["fillet"]["input_attrs"], "compact_policy.fillet.input_attrs")
    _ensure_mapping(rules["compact_policy"]["fillet"]["input_methods"], "compact_policy.fillet.input_methods")
    _ensure_mapping(rules["compact_policy"]["chamfer"], "compact_policy.chamfer")
    _ensure_mapping(rules["compact_policy"]["chamfer"]["input_attrs"], "compact_policy.chamfer.input_attrs")
    _ensure_mapping(rules["compact_policy"]["chamfer"]["input_methods"], "compact_policy.chamfer.input_methods")
    _ensure_mapping(rules["compact_policy"]["combine"], "compact_policy.combine")
    _ensure_mapping(rules["compact_policy"]["combine"]["input_attrs"], "compact_policy.combine.input_attrs")
    _ensure_mapping(rules["compact_policy"]["mirror"], "compact_policy.mirror")
    _ensure_mapping(rules["compact_policy"]["circular_pattern"], "compact_policy.circular_pattern")
    _ensure_mapping(rules["compact_policy"]["circular_pattern"]["input_attrs"], "compact_policy.circular_pattern.input_attrs")
    _ensure_mapping(rules["compact_policy"]["rectangular_pattern"], "compact_policy.rectangular_pattern")
    _ensure_mapping(
        rules["compact_policy"]["rectangular_pattern"]["input_methods"],
        "compact_policy.rectangular_pattern.input_methods",
    )
    _ensure_mapping(
        rules["compact_policy"]["rectangular_pattern"]["input_attrs"],
        "compact_policy.rectangular_pattern.input_attrs",
    )
    _ensure_mapping(
        rules["compact_policy"]["rectangular_pattern"]["distance_types"],
        "compact_policy.rectangular_pattern.distance_types",
    )
    _ensure_mapping(rules["compact_reference"], "compact_reference")
    _ensure_mapping(rules["compact_reference"]["exports"], "compact_reference.exports")
    _ensure_mapping(rules["compact_reference"]["methods"], "compact_reference.methods")
    for label, mapping in (
        ("compact_policy.planes", rules["compact_policy"]["planes"]),
        ("compact_policy.sketch.targets", rules["compact_policy"]["sketch"]["targets"]),
        ("compact_policy.sketch.collections", rules["compact_policy"]["sketch"]["collections"]),
        ("compact_policy.sketch.methods", rules["compact_policy"]["sketch"]["methods"]),
        ("compact_policy.text.input_methods", rules["compact_policy"]["text"]["input_methods"]),
        ("compact_policy.text.input_attrs", rules["compact_policy"]["text"]["input_attrs"]),
        ("compact_policy.text.horizontal_alignments", rules["compact_policy"]["text"]["horizontal_alignments"]),
        ("compact_policy.text.vertical_alignments", rules["compact_policy"]["text"]["vertical_alignments"]),
        ("compact_policy.extrude.extent_types", rules["compact_policy"]["extrude"]["extent_types"]),
        ("compact_policy.extrude.input_attrs", rules["compact_policy"]["extrude"]["input_attrs"]),
        ("compact_policy.extrude.input_methods", rules["compact_policy"]["extrude"]["input_methods"]),
        ("compact_policy.hole.create_methods", rules["compact_policy"]["hole"]["create_methods"]),
        ("compact_policy.hole.input_methods", rules["compact_policy"]["hole"]["input_methods"]),
        ("compact_policy.hole.edge_positions", rules["compact_policy"]["hole"]["edge_positions"]),
        ("compact_policy.revolve.input_methods", rules["compact_policy"]["revolve"]["input_methods"]),
        ("compact_policy.fillet.input_attrs", rules["compact_policy"]["fillet"]["input_attrs"]),
        ("compact_policy.fillet.input_methods", rules["compact_policy"]["fillet"]["input_methods"]),
        ("compact_policy.chamfer.input_attrs", rules["compact_policy"]["chamfer"]["input_attrs"]),
        ("compact_policy.chamfer.input_methods", rules["compact_policy"]["chamfer"]["input_methods"]),
        ("compact_policy.combine.input_attrs", rules["compact_policy"]["combine"]["input_attrs"]),
        ("compact_policy.circular_pattern.input_attrs", rules["compact_policy"]["circular_pattern"]["input_attrs"]),
        ("compact_policy.rectangular_pattern.input_methods", rules["compact_policy"]["rectangular_pattern"]["input_methods"]),
        ("compact_policy.rectangular_pattern.input_attrs", rules["compact_policy"]["rectangular_pattern"]["input_attrs"]),
        ("compact_policy.rectangular_pattern.distance_types", rules["compact_policy"]["rectangular_pattern"]["distance_types"]),
    ):
        for key, value in mapping.items():
            if label == "compact_policy.sketch.targets":
                if not isinstance(key, str) or not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                    raise RulesError(f"{label} must map strings to lists of strings.")
                continue
            if not isinstance(key, str) or not isinstance(value, str):
                raise RulesError(f"{label} must map strings to strings.")
    for helper_name in ("plane", "axis", "point"):
        for key, value in rules["compact_policy"]["construction"][helper_name]["methods"].items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise RulesError(f"compact_policy.construction.{helper_name}.methods must map strings to strings.")
    for key, value in rules["compact_policy"]["sketch"]["coercers"].items():
        if not isinstance(key, str) or not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise RulesError("compact_policy.sketch.coercers must map strings to lists of strings.")
    for key, value in rules["compact_policy"]["sketch"]["length_units_cm"].items():
        if not isinstance(key, str) or not isinstance(value, (int, float)):
            raise RulesError("compact_policy.sketch.length_units_cm must map strings to numbers.")
    for section_name in (
        "text",
        "extrude",
        "revolve",
        "hole",
        "fillet",
        "chamfer",
        "combine",
        "mirror",
        "circular_pattern",
        "rectangular_pattern",
    ):
        family_id = rules["compact_policy"][section_name]["family_id"]
        if family_id is not None and not isinstance(family_id, str):
            raise RulesError(f"compact_policy.{section_name}.family_id must be a string.")
    for helper_name in ("plane", "axis", "point"):
        family_id = rules["compact_policy"]["construction"][helper_name]["family_id"]
        if family_id is not None and not isinstance(family_id, str):
            raise RulesError(f"compact_policy.construction.{helper_name}.family_id must be a string.")
    for section_name in ("exports", "methods"):
        for entry_name, entry in rules["compact_reference"][section_name].items():
            if not isinstance(entry_name, str):
                raise RulesError(f"compact_reference.{section_name} keys must be strings.")
            _ensure_mapping(entry, f"compact_reference.{section_name}.{entry_name}")
            raw_mapping = entry.get("raw_mapping")
            arguments = entry.get("arguments")
            example = entry.get("example")
            escape_hatch = entry.get("escape_hatch")
            if not isinstance(raw_mapping, str) or not raw_mapping:
                raise RulesError(f"compact_reference.{section_name}.{entry_name}.raw_mapping must be a non-empty string.")
            if not isinstance(arguments, list) or not all(isinstance(item, str) for item in arguments):
                raise RulesError(f"compact_reference.{section_name}.{entry_name}.arguments must be a list of strings.")
            if not isinstance(example, str) or not example.strip():
                raise RulesError(f"compact_reference.{section_name}.{entry_name}.example must be a non-empty string.")
            if not isinstance(escape_hatch, str) or not escape_hatch.strip():
                raise RulesError(
                    f"compact_reference.{section_name}.{entry_name}.escape_hatch must be a non-empty string."
                )
    _ensure_mapping(rules["doc_overrides"]["overrides"], "doc_overrides.overrides")
    _ensure_mapping(rules["enum_aliases"]["aliases"], "enum_aliases.aliases")
    for enum_name, aliases in rules["enum_aliases"]["aliases"].items():
        if not isinstance(enum_name, str):
            raise RulesError("enum_aliases.aliases keys must be strings.")
        _ensure_mapping(aliases, f"enum_aliases.aliases.{enum_name}")
    _ensure_list_of_strings(rules["exclusions"]["symbols"], "exclusions.symbols")
    _ensure_list_of_strings(rules["exclusions"]["pages"], "exclusions.pages")
    _ensure_mapping(rules["family_overrides"]["families"], "family_overrides.families")
    for family_name, override in rules["family_overrides"]["families"].items():
        if not isinstance(family_name, str):
            raise RulesError("family_overrides.families keys must be strings.")
        _ensure_mapping(override, f"family_overrides.families.{family_name}")
    _ensure_mapping(rules["wrapper_dispatch"]["wrappers"], "wrapper_dispatch.wrappers")
    for symbol_id, target in rules["wrapper_dispatch"]["wrappers"].items():
        if not isinstance(symbol_id, str):
            raise RulesError("wrapper_dispatch.wrappers keys must be strings.")
        if not isinstance(target, str) or "." not in target:
            raise RulesError(f"wrapper_dispatch.wrappers.{symbol_id} must be a dotted import path.")
    for export_name in rules["compact_exports"]["exports"]:
        if export_name not in rules["aliases"]["exports"]:
            raise RulesError(f"compact_exports.exports references missing alias: {export_name}")


def _ensure_mapping(value: object, label: str) -> None:
    if not isinstance(value, dict):
        raise RulesError(f"{label} must be a mapping.")


def _ensure_list_of_strings(value: object, label: str) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RulesError(f"{label} must be a list of strings.")
